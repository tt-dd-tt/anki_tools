#!/bin/bash
# PreToolUse hook (Bash matcher, "if": "Bash(git push*)"): scans the commits
# about to be pushed for secrets and PII, and blocks the push if any are found.
#
# Reads the Bash tool-call JSON on stdin, writes a PreToolUse decision JSON
# (hookSpecificOutput.permissionDecision: allow|deny) to stdout.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

deny() {
  jq -n --arg reason "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

allow() {
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow"
    }
  }'
  exit 0
}

input="$(cat)"
command="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"

# Defensive re-check in case the hook's "if" filter didn't narrow this down.
if ! printf '%s' "$command" | grep -Eq '(^|[;&|]\s*)git push\b'; then
  allow
fi

cd "$REPO_DIR" || deny "Secrets/PII scan could not run: repo directory $REPO_DIR not found."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  deny "Secrets/PII scan could not run: $REPO_DIR is not a git work tree."
fi

upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [ -n "$upstream" ]; then
  range="${upstream}..HEAD"
else
  default_branch="$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')"
  default_branch="${default_branch:-main}"
  if git rev-parse --verify -q "origin/${default_branch}" >/dev/null 2>&1; then
    range="origin/${default_branch}..HEAD"
  else
    range=""
  fi
fi

if [ -z "$range" ]; then
  deny "Secrets/PII scan could not determine a commit range to check (no upstream branch and no origin/<default> found locally). Push blocked as a precaution — fetch/set an upstream, or review the outgoing commits manually, then retry."
fi

diff_content="$(git diff "$range" -- . 2>/dev/null || true)"
commit_messages="$(git log "$range" --format='%B' 2>/dev/null || true)"
added_lines="$(printf '%s\n' "$diff_content" | grep -E '^\+' | grep -Ev '^\+\+\+' || true)"

safe_emails='noreply@anthropic\.com'
user_email="$(git config user.email 2>/dev/null || true)"
if [ -n "$user_email" ]; then
  escaped_email="$(printf '%s' "$user_email" | sed 's/[.[\*^$]/\\&/g')"
  safe_emails="${safe_emails}|${escaped_email}"
fi

findings=""

check() {
  local label="$1" pattern="$2" text="$3"
  local hits
  hits="$(printf '%s\n' "$text" | grep -Eio "$pattern" 2>/dev/null | sort -u || true)"
  if [ -n "$hits" ]; then
    findings="${findings}${label}:\n$(printf '%s\n' "$hits" | sed 's/^/  - /')\n"
  fi
}

# --- Secrets ---
check "AWS Access Key ID" 'AKIA[0-9A-Z]{16}' "$added_lines"
check "Private key block" '\-\-\-\-\-BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY\-\-\-\-\-' "$diff_content"
check "GitHub token" 'gh[pousr]_[A-Za-z0-9]{36,}' "$added_lines"
check "Slack token" 'xox[baprs]-[A-Za-z0-9-]{10,}' "$added_lines"
check "Google API key" 'AIza[0-9A-Za-z_-]{35}' "$added_lines"
check "Generic secret assignment" "(api[_-]?key|secret|token|passwd|password|access[_-]?key)[\"']?[[:space:]]*[:=][[:space:]]*[\"'][A-Za-z0-9/_.+=-]{12,}[\"']" "$added_lines"
check "JWT-looking token" 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' "$added_lines"

env_files="$(git diff --name-only "$range" -- . 2>/dev/null | grep -E '(^|/)\.env(\..+)?$' | grep -Ev '\.env\.example$' || true)"
if [ -n "$env_files" ]; then
  findings="${findings}.env file changes:\n$(printf '%s\n' "$env_files" | sed 's/^/  - /')\n"
fi

# --- PII ---
email_hits="$(printf '%s\n' "$added_lines" | grep -Eio '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}' | sort -u | grep -Evi "^(${safe_emails})\$" || true)"
if [ -n "$email_hits" ]; then
  findings="${findings}Email address(es):\n$(printf '%s\n' "$email_hits" | sed 's/^/  - /')\n"
fi

check "Phone number" '(\+?[0-9]{1,3}[-. ]?)?\([0-9]{3}\)[-. ]?[0-9]{3}[-. ]?[0-9]{4}|[0-9]{3}[-.][0-9]{3}[-.][0-9]{4}' "$added_lines"
check "SSN-like pattern" '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b' "$added_lines"
check "Credit-card-like pattern" '\b[0-9]{4}[- ][0-9]{4}[- ][0-9]{4}[- ][0-9]{4}\b' "$added_lines"

msg_email_hits="$(printf '%s\n' "$commit_messages" | grep -Eio '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}' | sort -u | grep -Evi "^(${safe_emails})\$" || true)"
if [ -n "$msg_email_hits" ]; then
  findings="${findings}Email address(es) in commit message(s):\n$(printf '%s\n' "$msg_email_hits" | sed 's/^/  - /')\n"
fi

if [ -n "$findings" ]; then
  reason="$(printf 'Potential secrets/PII found in outgoing commits (%s):\n%b\nReview and remove before pushing, or edit .claude/hooks/scan-push-for-secrets.sh if this is a false positive.' "$range" "$findings")"
  deny "$reason"
fi

allow

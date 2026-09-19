# Anki Tools - German Vocabulary Helper

Tools for managing German/Slovak vocabulary in an Anki deck via the AnkiConnect API. Both tools default to a deck named `German_lessons`, but that's just a default — see below for how to point them at your own deck.

- **`add.sh` / `add_word.py`** — day-to-day tool: add a new word to the deck. This is the primary workflow.
- **`repair_notes.sh` / `edit_german_notes.py`** — occasional maintenance tool: sweeps every note in the deck and repairs formatting. Optional, run manually when needed.

## Prerequisites

1. **Anki** must be installed (`add.sh` will auto-launch it if it's not already running)
2. **AnkiConnect add-on** must be installed:
   - In Anki, go to: `Tools` → `Add-ons` → `Get Add-ons...`
   - Enter code: `2055492159`
   - Restart Anki
3. **Python 3.6+** installed

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Adding Vocabulary (`add.sh`)

Add words in **Slovak** or **German** directly to your Anki deck (defaults to `German_lessons`, override with `-d/--deck`).

Features:
- **Auto Language Detection**: Automatically detects whether input is in Slovak or German.
- **Wiktionary Article Lookup**: Determines German noun gender (`der`, `die`, `das`) and capitalizes German nouns properly.
- **Plural / Perfekt**: Adds a second line under the word with a noun's plural (`die Türen`) or a verb's Perfekt (`ist gegangen`) — the forms you can't derive from the headword.
- **Duplicate Checking**: Checks your Anki deck before adding to avoid duplicate notes. If a duplicate is found, it displays the existing note and asks whether to skip, force add, or update fields.
- **Auto Translation**: Translates word and optional example sentences between Slovak, German, and English.
- **Auto-starts Anki**: if AnkiConnect isn't reachable, `add.sh` launches Anki and waits for it to come up.

### Quick Start

```bash
# Interactive mode:
./add.sh

# Single word mode:
./add.sh pes
./add.sh "der Hund"
./add.sh mačka

# Word with a custom example sentence:
./add.sh "pes" -s "Pes breše na dvore."
```

### Options

`add.sh` forwards all arguments to `add_word.py`, whose full flag set is:

- `word` — word in German or Slovak to add (omit for interactive REPL mode)
- `-l, --lang {auto,sk,de}` — force the input language instead of auto-detecting (default: `auto`)
- `-d, --deck DECK` — target a different Anki deck (default: `German_lessons`)
- `-s, --sentence SENTENCE` — optional example sentence for the word
- `-f, --force` — add the note even if a duplicate is detected
- `-i, --interactive` — after processing the word given on the command line, stay open in interactive mode for more words

## Maintenance: Bulk-Repairing Existing Notes (`repair_notes.sh`)

`repair_notes.sh` runs `edit_german_notes.py`, which sweeps **every note** in a deck and automatically fixes formatting. It targets `German_lessons` by default — to point it at a different deck, edit the `deck_name` variable near the top of `main()` in `edit_german_notes.py` (there's no `-d` flag for this script, unlike `add_word.py`).

- Adds a missing `der`/`die`/`das` article and bolds `de_word`, using the same Wiktionary gender lookup as `add_word.py`
- Adds a noun's plural or a verb's Perfekt on a second line beneath the headword (see below)
- Strips leftover Etymology `<details>` sections from `en_word`
- Extracts the first glossary translation and injects/corrects a bold translation header at the top of `en_word`
- Strips glossary category-tag noise (e.g. `mil`) from `en_word`
- Backfills `en_sentence` by translating `de_sentence` when `en_sentence` is empty

Running it without flags mutates every matching note in place, so preview first with `--dry-run`. It's meant for occasional cleanup (e.g. after importing notes from elsewhere), not part of the regular add-word workflow.

```bash
./repair_notes.sh --dry-run   # print what would change, write nothing
./repair_notes.sh             # apply the changes
```

Re-running is safe: the sweep rebuilds `de_word` from the headword each time, so a second run reports 0 notes modified.

## Plural and Perfekt

Both tools add the form you can't guess from the headword, on its own line beneath it:

| Word type | Second line | Example |
| --- | --- | --- |
| Noun | Nominative plural | `die Tür` → `die Türen` |
| Verb | Perfekt (auxiliary + Partizip II) | `gehen` → `ist gegangen` |

```html
<b>die Tür</b><div data-anki-forms="1" style="…">die Türen</div>
```

The `data-anki-forms="1"` marker is how the tools recognise and rebuild their own output. Verbs taking either auxiliary render as `hat/ist gefahren`. Nothing is added where there's nothing to add: nouns with no plural (`das Erbrechen`), words that are already plural (`die Bücher`), and anything without a German Wiktionary entry.

### Caches

Lookups are cached on disk so repeat runs do no network work. Both files are committed:

- `gender_cache.json` — noun genders
- `forms_cache.json` — plurals and Perfekt forms

Failed requests are deliberately **not** cached, so a network blip can't permanently record a word as having no forms. Delete a word's entry to force a fresh lookup.

### Checking individual words

```bash
python check_forms.py            # a sample covering each case
python check_forms.py Tür gehen  # specific words
```

Prints the gender, plural and Perfekt found for each word. Only talks to Wiktionary — Anki doesn't need to be running.

### Tests

```bash
python -m unittest test_forms_parsing
```

Offline: the wikitext parsing, the `de_word` rendering and the duplicate-check behaviour are covered with fixtures and a stubbed network, so neither Wiktionary nor Anki access is needed.

## AnkiConnect API Reference

`edit_german_notes.py` provides an `AnkiConnect` class (also used by `add_word.py`) with these methods:

- `invoke(action, **params)` — low-level call to any AnkiConnect action
- `find_notes_in_deck(deck_name)` - Find all note IDs in a deck
- `get_notes_info(note_ids)` - Get detailed information about notes
- `update_note_fields(note_id, fields)` - Update specific fields
- `add_tags(note_ids, tags)` - Add tags to notes
- `remove_tags(note_ids, tags)` - Remove tags from notes

## Troubleshooting

### "Failed to connect to AnkiConnect"
- `add.sh` will try to launch Anki automatically; if that fails, start Anki manually
- Verify AnkiConnect is installed (check in `Tools` → `Add-ons`)
- Check that AnkiConnect is listening on `http://localhost:8765`

### "No notes found in the specified deck"
- Verify the deck name is spelled correctly (case-sensitive) — pass `-d` for `add_word.py`, or edit `deck_name` in `edit_german_notes.py` for `repair_notes.sh`
- Check that the deck exists and contains notes

### Changes not visible in Anki Browser
- If you have the note open in Anki's browser while editing, close and reopen it
- The changes are saved but may not refresh automatically


## Safety Tips

⚠️ **Important**: Back up your Anki collection before running `repair_notes.sh`, since it mutates every note in the deck!

1. In Anki: `File` → `Export` → Export your collection
2. Preview with `./repair_notes.sh --dry-run` before writing anything
3. Review the printed summary (notes modified vs. unchanged) after each run
4. You can always restore from backup if needed

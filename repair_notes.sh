#!/bin/bash
# Wrapper to run the deck-wide note repair sweep with the virtual environment.
# Optional/occasional maintenance tool — separate from add.sh's day-to-day add-word workflow.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/edit_german_notes.py"

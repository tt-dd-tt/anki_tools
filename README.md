# Anki Tools - German Vocabulary Helper

Tools for managing German/Slovak vocabulary in the `German_lessons` Anki deck via the AnkiConnect API.

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

Add words in **Slovak** or **German** directly to your `German_lessons` Anki deck.

Features:
- **Auto Language Detection**: Automatically detects whether input is in Slovak or German.
- **Wiktionary Article Lookup**: Determines German noun gender (`der`, `die`, `das`) and capitalizes German nouns properly.
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

`repair_notes.sh` runs `edit_german_notes.py`, which sweeps **every note** in the `German_lessons` deck and automatically fixes formatting:

- Adds a missing `der`/`die`/`das` article and bolds `de_word`, using the same Wiktionary gender lookup as `add_word.py`
- Strips leftover Etymology `<details>` sections from `en_word`
- Extracts the first glossary translation and injects/corrects a bold translation header at the top of `en_word`
- Strips glossary category-tag noise (e.g. `mil`) from `en_word`
- Backfills `en_sentence` by translating `de_sentence` when `en_sentence` is empty

This is **not** a dry-run or inspection tool — running it mutates every matching note in place. It's meant for occasional cleanup (e.g. after importing notes from elsewhere), not part of the regular add-word workflow.

```bash
./repair_notes.sh
```

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
- Verify the deck name is exactly `German_lessons` (case-sensitive), or pass `-d` to target a different deck
- Check that the deck exists and contains notes

### Changes not visible in Anki Browser
- If you have the note open in Anki's browser while editing, close and reopen it
- The changes are saved but may not refresh automatically

## Safety Tips

⚠️ **Important**: Back up your Anki collection before running `repair_notes.sh`, since it mutates every note in the deck!

1. In Anki: `File` → `Export` → Export your collection
2. Review the printed summary (notes modified vs. unchanged) after each run
3. You can always restore from backup if needed

# Anki Tools - German Mine Deck Editor

This tool allows you to programmatically edit notes in your "german mine" Anki deck using the AnkiConnect API.

## Prerequisites

1. **Anki** must be running
2. **AnkiConnect add-on** must be installed:
   - In Anki, go to: `Tools` → `Add-ons` → `Get Add-ons...`
   - Enter code: `2055492159`
   - Restart Anki
3. **Python 3.6+** installed
4. **requests** library: `pip install requests`

## Installation

```bash
# Install the required Python package
pip install requests
```

## Usage

### 1. Basic Usage (Inspect Notes)

Run the script to see all notes in your "german mine" deck:

```bash
python edit_german_notes.py
```

This will display information about each note including:
- Note ID
- Model (note type)
- Tags
- All fields and their values

### 2. Customize Editing Logic

Open `edit_german_notes.py` and modify the `edit_note()` function to implement your specific editing requirements.

#### Example 1: Update a specific field

```python
def edit_note(note_info: Dict[str, Any], anki: AnkiConnect) -> bool:
    note_id = note_info["noteId"]
    fields = note_info["fields"]
    
    # Update the "Back" field with additional information
    if "Back" in fields:
        current_value = fields["Back"]["value"]
        new_fields = {"Back": current_value + "<br><i>Updated on 2025-12-08</i>"}
        anki.update_note_fields(note_id, new_fields)
        return True
    
    return False
```

#### Example 2: Find and replace text

```python
def edit_note(note_info: Dict[str, Any], anki: AnkiConnect) -> bool:
    note_id = note_info["noteId"]
    fields = note_info["fields"]
    
    # Replace text in the "Front" field
    if "Front" in fields:
        old_text = "der"
        new_text = "<b>der</b>"
        current_value = fields["Front"]["value"]
        
        if old_text in current_value:
            new_fields = {"Front": current_value.replace(old_text, new_text)}
            anki.update_note_fields(note_id, new_fields)
            return True
    
    return False
```

#### Example 3: Add tags based on content

```python
def edit_note(note_info: Dict[str, Any], anki: AnkiConnect) -> bool:
    note_id = note_info["noteId"]
    fields = note_info["fields"]
    
    # Add a tag if the note contains certain words
    if "Front" in fields:
        content = fields["Front"]["value"].lower()
        
        if "verb" in content:
            anki.add_tags([note_id], "grammar::verb")
            return True
        elif "noun" in content:
            anki.add_tags([note_id], "grammar::noun")
            return True
    
    return False
```

#### Example 4: Conditional field updates

```python
def edit_note(note_info: Dict[str, Any], anki: AnkiConnect) -> bool:
    note_id = note_info["noteId"]
    fields = note_info["fields"]
    
    # Only update notes that have a specific tag
    if "needs-review" in note_info["tags"]:
        if "Back" in fields:
            new_fields = {"Back": fields["Back"]["value"] + " [REVIEWED]"}
            anki.update_note_fields(note_id, new_fields)
            anki.remove_tags([note_id], "needs-review")
            anki.add_tags([note_id], "reviewed")
            return True
    
    return False
```

## AnkiConnect API Reference

The script provides these main methods:

- `find_notes_in_deck(deck_name)` - Find all note IDs in a deck
- `get_notes_info(note_ids)` - Get detailed information about notes
- `update_note_fields(note_id, fields)` - Update specific fields
- `add_tags(note_ids, tags)` - Add tags to notes
- `remove_tags(note_ids, tags)` - Remove tags from notes

## Troubleshooting

### "Failed to connect to AnkiConnect"
- Make sure Anki is running
- Verify AnkiConnect is installed (check in `Tools` → `Add-ons`)
- Check that AnkiConnect is listening on `http://localhost:8765`

### "No notes found in the specified deck"
- Verify the deck name is exactly "german mine" (case-sensitive)
- Check that the deck exists and contains notes

### Changes not visible in Anki Browser
- If you have the note open in Anki's browser while editing, close and reopen it
- The changes are saved but may not refresh automatically


## Safety Tips

⚠️ **Important**: Always backup your Anki collection before running bulk edits!

1. In Anki: `File` → `Export` → Export your collection
2. Test your editing logic on a few notes first
3. Review the output to ensure changes are correct
4. You can always restore from backup if needed


#!/usr/bin/env python3
"""Script to find the mildrone note."""

import json
import requests

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Find notes containing "mildrone"
note_ids = invoke("findNotes", query='deck:"german mine" de_word:*mildrone*')
print(f"Found {len(note_ids)} notes with 'mildrone'")
print(f"Note IDs: {note_ids}")

if note_ids:
    # Get the note info
    notes_info = invoke("notesInfo", notes=note_ids)
    for note_info in notes_info:
        print(f"\nNote ID: {note_info['noteId']}")
        print(f"de_word: {note_info['fields']['de_word']['value']}")
        print(f"\nen_word (first 500 chars):")
        print(note_info['fields']['en_word']['value'][:500])

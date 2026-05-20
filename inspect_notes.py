#!/usr/bin/env python3
"""Script to inspect note structure."""

import json
import requests

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Find notes in german mine deck
note_ids = invoke("findNotes", query='deck:"german mine"')
print(f"Found {len(note_ids)} notes")

if note_ids:
    # Get first note
    notes_info = invoke("notesInfo", notes=[note_ids[0]])
    if notes_info:
        note_info = notes_info[0]
        print("\nFields in note:")
        for field_name, field_data in note_info["fields"].items():
            print(f"\n{field_name}:")
            print(f"  {field_data['value'][:200]}...")

#!/usr/bin/env python3
"""Debug script to inspect a specific note's HTML structure."""

import json
import requests

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Get the problematic note (mildrone strike)
note_id = 1765212023828
notes_info = invoke("notesInfo", notes=[note_id])

if notes_info:
    note_info = notes_info[0]
    print(json.dumps(note_info, indent=2))
else:
    print("Note not found")

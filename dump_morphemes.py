#!/usr/bin/env python3
"""Dump the Morphemes section HTML to see its structure."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Get the note with mildrone
note_id = 1765213071954
notes_info = invoke("notesInfo", notes=[note_id])

print(f"Response: {notes_info}")
print(f"Type: {type(notes_info)}")

if notes_info and len(notes_info) > 0:
    note_info = notes_info[0]
    print(f"Note info keys: {note_info.keys()}")
    
    if 'fields' in note_info:
        en_word = note_info['fields']['en_word']['value']
        
        # Find the Morphemes section
        morpheme_pattern = r'<details\s+data-sc-content="details-entry-Morphemes"[^>]*>.*?</details>'
        morpheme_match = re.search(morpheme_pattern, en_word, re.DOTALL)
        
        if morpheme_match:
            print("\nMORPHEMES SECTION HTML:")
            print("=" * 80)
            print(morpheme_match.group(0))
            print("=" * 80)
        else:
            print("No Morphemes section found")
    else:
        print("No 'fields' key in note_info")
else:
    print("Note not found or empty response")

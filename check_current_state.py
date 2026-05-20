#!/usr/bin/env python3
"""Check the current state of the Drohnenangriff note after cleanup."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Get the Drohnenangriff note
note_id = 1765213200778
notes_info = invoke("notesInfo", notes=[note_id])

if notes_info and len(notes_info) > 0 and 'fields' in notes_info[0]:
    note_info = notes_info[0]
    en_word = note_info['fields']['en_word']['value']
    
    print("CURRENT en_word content:")
    print("=" * 80)
    print(en_word)
    print("=" * 80)
    
    # Check for 'mil' anywhere
    if 'mil' in en_word.lower():
        print("\n⚠️  'mil' still found in en_word!")
        
        # Find all occurrences
        import re
        for match in re.finditer(r'.{0,50}mil.{0,50}', en_word, re.IGNORECASE):
            print(f"Context: ...{match.group()}...")
    else:
        print("\n✓ 'mil' not found in en_word")
else:
    print("Note not found or has no fields")

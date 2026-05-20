#!/usr/bin/env python3
"""Find notes containing 'mil' in the en_word field."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Get all notes from german mine
note_ids = invoke("findNotes", query='deck:"german mine"')
notes_info = invoke("notesInfo", notes=note_ids)

print(f"Searching for 'mil' in {len(notes_info)} notes\n")

for note_info in notes_info:
    if not note_info or 'fields' not in note_info:
        continue
        
    fields = note_info['fields']
    if 'en_word' not in fields:
        continue
        
    en_word = fields['en_word']['value']
    
    # Check if 'mil' appears in en_word
    if 'mil' in en_word.lower():
        de_word = fields.get('de_word', {}).get('value', '')
        de_word_clean = re.sub(r'<[^>]+>', '', de_word).strip()
        
        print(f"Note ID: {note_info['noteId']}")
        print(f"German word: {de_word_clean}")
        print(f"\nen_word content (first 1000 chars):")
        print(en_word[:1000])
        print("\n" + "=" * 80 + "\n")

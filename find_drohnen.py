#!/usr/bin/env python3
"""Find the current Drohnenangriff note."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Search for Drohnenangriff
note_ids = invoke("findNotes", query='deck:"german mine" de_word:*drohnen*')
print(f"Found {len(note_ids)} notes with 'drohnen'")
print(f"Note IDs: {note_ids}")

if note_ids:
    notes_info = invoke("notesInfo", notes=note_ids)
    for note_info in notes_info:
        if not note_info or 'fields' not in note_info:
            continue
            
        de_word = note_info['fields'].get('de_word', {}).get('value', '')
        de_word_clean = re.sub(r'<[^>]+>', '', de_word).strip()
        
        print(f"\nNote ID: {note_info['noteId']}")
        print(f"German word: {de_word_clean}")
        
        en_word = note_info['fields']['en_word']['value']
        
        # Check for 'mil'
        if 'mil' in en_word.lower():
            print("⚠️  Contains 'mil'")
            print("\nFull en_word content:")
            print(en_word)
        else:
            print("✓ Does NOT contain 'mil'")

#!/usr/bin/env python3
"""Find all notes with Morphemes sections."""

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

print(f"Found {len(notes_info)} notes\n")

for note_info in notes_info:
    if not note_info or 'fields' not in note_info:
        continue
        
    fields = note_info['fields']
    if 'en_word' not in fields:
        continue
        
    en_word = fields['en_word']['value']
    
    # Check for Morphemes section
    if 'Morphemes' in en_word:
        de_word = fields.get('de_word', {}).get('value', '')
        de_word_clean = re.sub(r'<[^>]+>', '', de_word).strip()
        
        print(f"Note ID: {note_info['noteId']}")
        print(f"German word: {de_word_clean}")
        
        # Find the Morphemes section
        morpheme_pattern = r'<details\s+data-sc-content="details-entry-Morphemes"[^>]*>(.*?)</details>'
        morpheme_match = re.search(morpheme_pattern, en_word, re.DOTALL)
        
        if morpheme_match:
            morpheme_html = morpheme_match.group(1)
            print(f"Morphemes HTML (first 300 chars):")
            print(morpheme_html[:300])
            print("-" * 80)

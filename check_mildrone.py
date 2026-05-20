#!/usr/bin/env python3
"""Script to check the mildrone note structure."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Find all notes in german mine
note_ids = invoke("findNotes", query='deck:"german mine"')
notes_info = invoke("notesInfo", notes=note_ids)

for note_info in notes_info:
    de_word_raw = note_info['fields']['de_word']['value']
    de_word_clean = re.sub(r'<[^>]+>', '', de_word_raw).strip()
    
    # Check if this note has morphemes
    en_word = note_info['fields']['en_word']['value']
    if 'Morphemes' in en_word and 'mil' in en_word:
        print(f"\nNote ID: {note_info['noteId']}")
        print(f"de_word (raw): {de_word_raw}")
        print(f"de_word (clean): {de_word_clean}")
        print(f"\nChecking morpheme section...")
        
        # Extract morpheme items
        morpheme_items = re.findall(r'<li>.*?</li>', en_word, re.DOTALL)
        for item in morpheme_items:
            morpheme_match = re.search(r'<li>\s*<div[^>]*>([^<]+)</div>', item)
            if morpheme_match:
                morpheme_text = morpheme_match.group(1).strip()
                print(f"  Morpheme: '{morpheme_text}'")
                print(f"    Is '{morpheme_text}' in '{de_word_clean}'? {morpheme_text.lower() in de_word_clean.lower()}")

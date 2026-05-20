#!/usr/bin/env python3
"""Script to inspect the mildrone note in detail."""

import json
import requests
import re

def invoke(action, **params):
    """Send a request to AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post("http://localhost:8765", json=payload)
    return response.json()["result"]

# Get the specific note
note_id = 1765212863181
notes_info = invoke("notesInfo", notes=[note_id])

if notes_info:
    note_info = notes_info[0]
    
    de_word_raw = note_info['fields']['de_word']['value']
    de_word_clean = re.sub(r'<[^>]+>', '', de_word_raw).strip().lower()
    
    print(f"Note ID: {note_id}")
    print(f"\nde_word (raw): {de_word_raw}")
    print(f"de_word (clean): '{de_word_clean}'")
    
    en_word = note_info['fields']['en_word']['value']
    
    # Check for Morphemes section
    morpheme_pattern = r'<details\s+data-sc-content="details-entry-Morphemes"[^>]*>.*?</details>'
    morpheme_match = re.search(morpheme_pattern, en_word, re.DOTALL)
    
    print(f"\nMorphemes section found: {morpheme_match is not None}")
    
    if morpheme_match:
        print(f"\nMorphemes section content:")
        print(morpheme_match.group(0)[:500])
        
        # Extract morpheme items
        morpheme_items = re.findall(r'<li>.*?</li>', morpheme_match.group(0), re.DOTALL)
        print(f"\nFound {len(morpheme_items)} morpheme items:")
        
        for item in morpheme_items:
            morpheme_text_match = re.search(r'<li>\s*<div[^>]*>([^<]+)</div>', item)
            if morpheme_text_match:
                morpheme_text = morpheme_text_match.group(1).strip().lower()
                in_word = morpheme_text in de_word_clean
                print(f"  - '{morpheme_text}' -> in '{de_word_clean}': {in_word}")
else:
    print("Note not found")

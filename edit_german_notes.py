#!/usr/bin/env python3
"""
Script to edit Anki notes in the "german mine" deck using AnkiConnect.

Prerequisites:
1. Anki must be running
2. AnkiConnect add-on must be installed (code: 2055492159)
3. Install required packages: pip install requests deep-translator
"""

import json
import requests
from typing import List, Dict, Any, Optional
from deep_translator import GoogleTranslator
import os
import re

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gender_cache.json")
GENDER_CACHE = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            GENDER_CACHE = json.load(f)
    except Exception:
        pass

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(GENDER_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_gender_from_wiktionary(word, original_word=None):
    if not word:
        return None
        
    if original_word is None:
        original_word = word
        # Check cache first
        if original_word in GENDER_CACHE:
            return GENDER_CACHE[original_word]
            
    url = "https://de.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": word,
        "rvprop": "content",
        "format": "json",
        "utf8": 1
    }
    headers = {
        "User-Agent": "AnkiGermanNotesEditor/1.0 (anki-tools@example.com)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return None
            
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                # Try hyphen fallback
                if "-" in word:
                    parts = [p.strip() for p in word.split("-") if p.strip()]
                    if len(parts) > 1:
                        res = get_gender_from_wiktionary(parts[-1], original_word)
                        if res:
                            GENDER_CACHE[original_word] = res
                            save_cache()
                            return res
                return None
            
            revisions = page_data.get("revisions", [])
            if not revisions:
                return None
            
            content = revisions[0].get("*", "")
            
            # Check if this page is a plural form
            is_plural = False
            if word == original_word:
                if re.search(r'\*\s*(?:Nominativ|Genitiv|Dativ|Akkusativ)\s+Plural', content, re.IGNORECASE):
                    is_plural = True
            
            # 1. Search for direct noun gender
            substantiv_matches = list(re.finditer(r'Substantiv\|Deutsch', content))
            if substantiv_matches:
                for match in substantiv_matches:
                    context_after = content[match.end():match.end() + 200]
                    gender_match = re.search(r'\{\{([mfnpl]+)\}\}', context_after)
                    if gender_match:
                        val = gender_match.group(1)
                        if val in ('m', 'f', 'n', 'pl'):
                            res = 'pl' if is_plural or val == 'pl' else val
                            GENDER_CACHE[original_word] = res
                            save_cache()
                            return res
            
            # 2. Check for inflected form with Grundformverweis
            base_form_match = re.search(r'\{\{Grundformverweis(?: Dekl)?\|([^|}]+)\}\}', content)
            if base_form_match:
                base_word = base_form_match.group(1).strip()
                gender_res = get_gender_from_wiktionary(base_word, original_word)
                if is_plural and gender_res in ('m', 'f', 'n'):
                    gender_res = 'pl'
                if gender_res:
                    GENDER_CACHE[original_word] = gender_res
                    save_cache()
                    return gender_res
                
            # Fallback 3: look for noun link in Plural des Substantivs
            base_form_match2 = re.search(r'Plural des Substantivs\s+\'\'\'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\'\'\'', content)
            if base_form_match2:
                base_word = base_form_match2.group(1).strip()
                gender_res = get_gender_from_wiktionary(base_word, original_word)
                res = 'pl'
                GENDER_CACHE[original_word] = res
                save_cache()
                return res
            
            # Fallback 4: Try a global search for Substantiv gender
            gender_match = re.search(r'\{\{Wortart\|Substantiv\|Deutsch\}\}.*?\{\{([mfnpl]+)\}\}', content, re.DOTALL)
            if gender_match:
                val = gender_match.group(1)
                res = 'pl' if is_plural or val == 'pl' else val
                GENDER_CACHE[original_word] = res
                save_cache()
                return res
            
    except Exception as e:
        print(f"Error fetching from Wiktionary for '{word}': {e}")
        
    return None



class AnkiConnect:
    """Interface to communicate with Anki via AnkiConnect API."""
    
    def __init__(self, url: str = "http://localhost:8765"):
        self.url = url
    
    def invoke(self, action: str, **params) -> Any:
        """Send a request to AnkiConnect."""
        payload = {
            "action": action,
            "version": 6,
            "params": params
        }
        
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if len(result) != 2:
                raise Exception("Response has unexpected number of fields")
            if "error" not in result:
                raise Exception("Response is missing required error field")
            if "result" not in result:
                raise Exception("Response is missing required result field")
            if result["error"] is not None:
                raise Exception(result["error"])
            
            return result["result"]
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Failed to connect to AnkiConnect. "
                "Make sure Anki is running and AnkiConnect is installed."
            )
    
    def find_notes_in_deck(self, deck_name: str) -> List[int]:
        """Find all note IDs in a specific deck."""
        query = f'deck:"{deck_name}"'
        return self.invoke("findNotes", query=query)
    
    def get_notes_info(self, note_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information about notes."""
        return self.invoke("notesInfo", notes=note_ids)
    
    def update_note_fields(self, note_id: int, fields: Dict[str, str]) -> None:
        """Update specific fields of a note."""
        note = {
            "id": note_id,
            "fields": fields
        }
        self.invoke("updateNoteFields", note=note)
    
    def add_tags(self, note_ids: List[int], tags: str) -> None:
        """Add tags to notes."""
        self.invoke("addTags", notes=note_ids, tags=tags)
    
    def remove_tags(self, note_ids: List[int], tags: str) -> None:
        """Remove tags from notes."""
        self.invoke("removeTags", notes=note_ids, tags=tags)


def edit_note(note_info: Dict[str, Any], anki: AnkiConnect) -> bool:
    """
    Edit a single note. Customize this function based on your needs.
    
    Args:
        note_info: Dictionary containing note information
        anki: AnkiConnect instance
    
    Returns:
        True if the note was modified, False otherwise
    """
    import re
    from html.parser import HTMLParser
    
    note_id = note_info["noteId"]
    fields = note_info["fields"]
    tags = note_info["tags"]
    
    # Print note information for inspection
    print(f"\n{'='*60}")
    print(f"Note ID: {note_id}")
    print(f"Model: {note_info['modelName']}")
    print(f"Tags: {', '.join(tags) if tags else 'None'}")
    
    modified = False
    updates = {}
    
    # Process de_word field to make it bold
    if "de_word" in fields:
        de_word_raw = fields["de_word"]["value"].strip()
        de_word_clean = re.sub(r'<[^>]+>', '', de_word_raw).strip()
        
        # Check if de_word is a German noun (capitalized in German)
        is_noun = de_word_clean and de_word_clean[0].isupper()
        
        # Check if it already starts with an article (der/die/das/die(pl))
        starts_with_article = False
        if de_word_clean:
            article_match = re.match(r'^(der|die|das)\s+', de_word_clean, re.IGNORECASE)
            if article_match:
                starts_with_article = True
                
        # Try to determine gender from Wiktionary to add an article to German nouns
        article_to_add = None
        if is_noun and not starts_with_article:
            gender = get_gender_from_wiktionary(de_word_clean)
            if gender == 'm':
                article_to_add = 'der'
            elif gender == 'f':
                article_to_add = 'die'
            elif gender == 'n':
                article_to_add = 'das'
            elif gender == 'pl':
                article_to_add = 'die'
                
        # Determine if we should add an article
        should_add_article = is_noun and not starts_with_article and article_to_add is not None
        
        if should_add_article:
            new_word = f"{article_to_add} {de_word_clean}"
            new_de_word = f"<b>{new_word}</b>"
            updates["de_word"] = new_de_word
            print(f"\n  ✓ Added article '{article_to_add}' and made German word bold: '{new_word}'")
            modified = True
        else:
            # Check if it is not already bold or styled
            if de_word_raw and not re.search(r'<b>|<strong>|font-weight:\s*bold', de_word_raw, re.IGNORECASE):
                new_de_word = f"<b>{de_word_clean}</b>"
                updates["de_word"] = new_de_word
                print(f"\n  ✓ Made German word bold: '{de_word_clean}'")
                modified = True
            else:
                print(f"\n  - German word is already bold/styled or has article")
    
    # Check if en_word field exists
    if "en_word" in fields:
        en_word_content = fields["en_word"]["value"]
        new_content = en_word_content
        
        # 1. Remove Etymology section if it exists
        etymology_pattern = r'<details\s+data-sc-content="details-entry-Etymology"[^>]*>.*?</details>'
        if re.search(etymology_pattern, new_content, re.DOTALL):
            print(f"\n  ✓ Found Etymology section")
            new_content = re.sub(etymology_pattern, '', new_content, flags=re.DOTALL)
            print(f"  ✓ Removed Etymology section")
            modified = True
        
        # 2. Extract first translation and add it at the beginning
        # Try multiple patterns to find the first translation
        first_translation = None
        
        # Pattern 1: Look for the first <li> item in the glossary list
        # Pattern: <li><div>translation text...
        pattern1 = r'<ol[^>]*data-sc-content="glosses"[^>]*>.*?<li><div>([^<]+)'
        match = re.search(pattern1, new_content, re.DOTALL)
        
        if match:
            raw_text = match.group(1).strip()
            # Remove anything in parentheses
            first_translation = re.split(r'[\(\[]', raw_text)[0].strip()
        else:
            # Pattern 2: Try to find any text in the first <li> tag
            pattern2 = r'<ol[^>]*data-sc-content="glosses"[^>]*>.*?<li[^>]*>(.*?)</li>'
            match = re.search(pattern2, new_content, re.DOTALL)
            if match:
                # Extract text content
                li_content = match.group(1)
                
                # Remove grammatical tag badges (e.g., <span>vi</span>, <span>vr</span>)
                # These appear as HTML elements, not plain text
                li_content = re.sub(r'<span[^>]*>\s*(?:vi|vr|vt|adj|adv|prep|conj|pron|interj|aux|det|num|art|m|f|n|pl|sg)\s*</span>', '', li_content, flags=re.IGNORECASE)
                
                # Remove all remaining HTML tags
                text_only = re.sub(r'<[^>]+>', '', li_content)
                
                # Get first line and clean it up
                first_translation = text_only.strip().split('\n')[0].strip()
                # Remove anything in parentheses or brackets
                first_translation = re.split(r'[\(\[]', first_translation)[0].strip()
            else:
                # Pattern 3: Fallback to en_sentence if it exists
                if "en_sentence" in fields:
                    en_sentence = fields["en_sentence"]["value"].strip()
                    if en_sentence:
                        first_translation = en_sentence
                        print(f"\n  ℹ Using en_sentence as fallback translation")
        
        # Final cleanup: remove any remaining grammatical tags that might be in plain text
        if first_translation:
            # Remove grammatical markers at the beginning (in case they're plain text)
            grammatical_pattern = r'^(?:vi|vr|vt|adj|adv|prep|conj|pron|interj|aux|det|num|art|m|f|n|pl|sg)(?:\s+(?:vi|vr|vt|adj|adv|prep|conj|pron|interj|aux|det|num|art|m|f|n|pl|sg))*\s+'
            first_translation = re.sub(grammatical_pattern, '', first_translation, flags=re.IGNORECASE).strip()
        
        if first_translation:
            print(f"\n  ✓ Found first translation: '{first_translation}'")
            
            # Check if translation header already exists at the beginning
            translation_header_pattern = r'^<div\s+style="[^"]*font-size:\s*1\.8em[^"]*"[^>]*>(.*?)</div>'
            existing_header_match = re.match(translation_header_pattern, new_content, re.DOTALL)
            
            if existing_header_match:
                existing_translation = existing_header_match.group(1).strip()
                # Check if the existing header has the correct translation
                if existing_translation != first_translation:
                    print(f"  ⚠ Translation header exists but is incorrect: '{existing_translation}'")
                    print(f"  ✓ Updating translation header to: '{first_translation}'")
                    # Replace the existing header with the correct one
                    translation_header = f'<div style="font-size: 1.8em; font-weight: bold; margin-bottom: 0.5em; color: #2196F3;">{first_translation}</div>'
                    new_content = re.sub(translation_header_pattern, translation_header, new_content, count=1)
                    modified = True
                else:
                    print(f"  - Translation header already correct")
            else:
                # Add translation as a prominent header at the very beginning
                translation_header = f'<div style="font-size: 1.8em; font-weight: bold; margin-bottom: 0.5em; color: #2196F3;">{first_translation}</div>'
                new_content = translation_header + new_content
                print(f"  ✓ Added translation header at the beginning")
                modified = True
        else:
            print(f"\n  - Could not extract first translation from any source")
        
        # 4. Clean up category tags in glossary (like "mil" for military)
        # These tags appear in the glossary list items and add visual noise
        # Pattern: <span data-sc-content="tag" ...>tag_text</span>
        tag_pattern = r'<div data-sc-content="tags">.*?</div>'
        tags_found = re.findall(tag_pattern, new_content, re.DOTALL)
        
        if tags_found:
            print(f"\n  ✓ Found {len(tags_found)} category tag(s) in glossary")
            for tag_html in tags_found:
                # Extract the tag text to show what we're removing
                tag_text_match = re.search(r'<span[^>]*>([^<]+)</span>', tag_html)
                if tag_text_match:
                    tag_text = tag_text_match.group(1).strip()
                    print(f"    - Removing tag: '{tag_text}'")
            
            # Remove all tag divs
            new_content = re.sub(tag_pattern, '', new_content, flags=re.DOTALL)
            print(f"  ✓ Removed category tags from glossary")
            modified = True
        
        # Store en_word updates if modified or content changed
        if new_content != en_word_content:
            updates["en_word"] = new_content
            modified = True
    else:
        print(f"\n  - en_word field not found")
    
    # 3. Translate de_sentence to en_sentence if en_sentence is empty
    if "de_sentence" in fields and "en_sentence" in fields:
        de_sentence = fields["de_sentence"]["value"].strip()
        en_sentence = fields["en_sentence"]["value"].strip()
        
        if de_sentence and not en_sentence:
            print(f"\n  ✓ Found German sentence to translate")
            print(f"    DE: {de_sentence[:80]}{'...' if len(de_sentence) > 80 else ''}")
            
            try:
                # Translate using Google Translate
                translator = GoogleTranslator(source='de', target='en')
                translated = translator.translate(de_sentence)
                
                print(f"    EN: {translated[:80]}{'...' if len(translated) > 80 else ''}")
                print(f"  ✓ Translation successful")
                
                updates["en_sentence"] = translated
                modified = True
            except Exception as e:
                print(f"  ✗ Translation failed: {e}")
        elif de_sentence and en_sentence:
            print(f"\n  - en_sentence already has content, skipping translation")
        elif not de_sentence:
            print(f"\n  - de_sentence is empty, nothing to translate")
    
    # Update the note if modified
    if modified and updates:
        anki.update_note_fields(note_id, updates)
        return True
    
    return False


def main():
    """Main function to process notes in the 'german mine' deck."""
    deck_name = "german mine"
    
    print(f"Connecting to Anki...")
    anki = AnkiConnect()
    
    # Test connection
    try:
        version = anki.invoke("version")
        print(f"✓ Connected to AnkiConnect (version {version})")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Find notes in the deck
    print(f"\nSearching for notes in deck '{deck_name}'...")
    try:
        note_ids = anki.find_notes_in_deck(deck_name)
        print(f"✓ Found {len(note_ids)} notes")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    if not note_ids:
        print("No notes found in the specified deck.")
        return
    
    # Get detailed information about the notes
    print(f"\nFetching note details...")
    try:
        notes_info = anki.get_notes_info(note_ids)
        print(f"✓ Retrieved information for {len(notes_info)} notes")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Process each note
    print(f"\nProcessing notes...")
    modified_count = 0
    
    for i, note_info in enumerate(notes_info, 1):
        print(f"\n[{i}/{len(notes_info)}]", end="")
        try:
            if edit_note(note_info, anki):
                modified_count += 1
                print("  ✓ Modified")
            else:
                print("  - No changes")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total notes processed: {len(notes_info)}")
    print(f"  Notes modified: {modified_count}")
    print(f"  Notes unchanged: {len(notes_info) - modified_count}")


if __name__ == "__main__":
    main()

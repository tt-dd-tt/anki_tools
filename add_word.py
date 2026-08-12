#!/usr/bin/env python3
"""
Anki Terminal Utility for German & Slovak Vocabulary

Adds words (in Slovak or German) to the Anki deck 'German_lessons'.
- Automatically detects input language (Slovak or German).
- Translates between Slovak, German, and English.
- Fetches noun gender/article from Wiktionary (der, die, das).
- Checks for duplicate notes in the deck before adding.
- Formats fields matching the 'Goethe Vocab List' note model.
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edit_german_notes import (
    get_gender_from_wiktionary,
    AnkiConnect,
    gender_to_article,
    build_translation_header,
    translate_text,
)

# Terminal Color Codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_GRAY = "\033[90m"

DECK_NAME = "German_lessons"
MODEL_NAME = "Goethe Vocab List"


def print_banner():
    print(f"{COLOR_CYAN}{COLOR_BOLD}============================================================{COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}         Anki Vocabulary Tool (German / Slovak)           {COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}============================================================{COLOR_RESET}")


def detect_language(text: str) -> str:
    """
    Detect whether the input text is German ('de') or Slovak ('sk').
    """
    text_clean = text.strip()
    
    # 1. Starts with German article
    if re.match(r'^(der|die|das)\s+', text_clean, re.IGNORECASE):
        return 'de'
        
    # 2. Slovak specific characters
    if re.search(r'[čďĺľňôŕšťýžČĎĹĽŇÔŔŠŤÝŽ]', text_clean):
        return 'sk'
        
    # 3. Check Wiktionary gender (exact or capitalized)
    if get_gender_from_wiktionary(text_clean) or get_gender_from_wiktionary(text_clean.capitalize()):
        return 'de'
        
    # 4. Translation heuristic
    tr_de_en = translate_text(text_clean, 'de', 'en')
    tr_sk_en = translate_text(text_clean, 'sk', 'en')
    if tr_de_en and tr_sk_en:
        if tr_de_en.lower() != text_clean.lower() and tr_sk_en.lower() == text_clean.lower():
            return 'de'
        if tr_sk_en.lower() != text_clean.lower() and tr_de_en.lower() == text_clean.lower():
            return 'sk'
        
    # Default fallback to German if capitalized, Slovak otherwise
    if text_clean and text_clean[0].isupper():
        return 'de'
    return 'sk'


def clean_word(word: str) -> str:
    """Strip HTML tags and trim whitespace."""
    return re.sub(r'<[^>]+>', '', word).strip()


def extract_base_word(word: str) -> Tuple[str, Optional[str]]:
    """
    Extract base word and existing article if present.
    Returns: (base_word, article_or_None)
    """
    word_clean = clean_word(word)
    article_match = re.match(r'^(der|die|das)\s+(.*)', word_clean, re.IGNORECASE)
    if article_match:
        return article_match.group(2).strip(), article_match.group(1).lower()
    return word_clean, None


def get_formatted_german_word(raw_word: str) -> Tuple[str, str, Optional[str]]:
    """
    Get (de_word_formatted, base_german_word, article).
    Example: ("<b>der Hund</b>", "Hund", "der")
    """
    base_word, existing_article = extract_base_word(raw_word)
    article = existing_article
    
    if existing_article:
        base_word = base_word.capitalize()
    else:
        # Check gender for exact casing first, then capitalized
        gender = get_gender_from_wiktionary(base_word)
        if not gender:
            gender = get_gender_from_wiktionary(base_word.capitalize())
            if gender:
                base_word = base_word.capitalize()
            
        if gender:
            article = gender_to_article(gender)
            if base_word and base_word[0].isupper():
                base_word = base_word.capitalize()
                
    if article:
        full_word = f"{article} {base_word}"
    else:
        full_word = base_word
        
    formatted_de_word = f"<b>{full_word}</b>"
    return formatted_de_word, base_word, article


def find_duplicates(anki: AnkiConnect, deck: str, base_de_word: str, full_de_word: str) -> List[Dict[str, Any]]:
    """
    Search deck for existing notes matching base_de_word or full_de_word.
    """
    try:
        note_ids = anki.find_notes_in_deck(deck)
        if not note_ids:
            return []
        notes = anki.get_notes_info(note_ids)
    except Exception as e:
        print(f"{COLOR_RED}Error fetching notes for duplicate check: {e}{COLOR_RESET}")
        return []
        
    target_base = base_de_word.strip().lower()
    target_full = full_de_word.strip().lower()
    
    duplicates = []
    for n in notes:
        fields = n.get("fields", {})
        note_id_val = clean_word(fields.get("Note ID", {}).get("value", "")).strip().lower()
        de_word_val = clean_word(fields.get("de_word", {}).get("value", "")).strip().lower()
        
        # Remove leading articles for comparison
        de_word_clean = re.sub(r'^(der|die|das)\s+', '', de_word_val, flags=re.IGNORECASE)
        
        if (target_base == note_id_val or 
            target_base == de_word_clean or 
            target_full == de_word_val or 
            target_base == de_word_val):
            duplicates.append(n)
            
    return duplicates


def print_note_preview(fields: Dict[str, str]):
    print(f"\n{COLOR_CYAN}┌────────────────────────────────────────────────────────────┐{COLOR_RESET}")
    print(f"{COLOR_CYAN}│ {COLOR_BOLD}PROPOSED NOTE PREVIEW{COLOR_RESET}                                      │")
    print(f"{COLOR_CYAN}├────────────────────────────────────────────────────────────┤{COLOR_RESET}")
    for k, v in fields.items():
        v_clean = v.replace('\n', ' ')
        if len(v_clean) > 55:
            v_clean = v_clean[:52] + "..."
        print(f"{COLOR_CYAN}│{COLOR_RESET} {COLOR_BOLD}{k:<12}:{COLOR_RESET} {v_clean:<44} {COLOR_CYAN}│{COLOR_RESET}")
    print(f"{COLOR_CYAN}└────────────────────────────────────────────────────────────┘{COLOR_RESET}")


def process_and_add_word(
    anki: AnkiConnect,
    input_word: str,
    input_lang: str = "auto",
    custom_sentence: Optional[str] = None,
    deck_name: str = DECK_NAME,
    force: bool = False,
    interactive: bool = True
) -> bool:
    """
    Processes word input, translates, checks duplicates, and adds note to Anki.
    """
    input_word = input_word.strip()
    if not input_word:
        return False
        
    print(f"\n{COLOR_BOLD}Processing input:{COLOR_RESET} '{input_word}'")
    
    # 1. Determine Language
    if input_lang == "auto" or input_lang not in ("sk", "de"):
        lang = detect_language(input_word)
    else:
        lang = input_lang
        
    lang_name = "Slovak" if lang == "sk" else "German"
    print(f"  ➜ Detected Language: {COLOR_GREEN}{lang_name}{COLOR_RESET}")
    
    # 2. Translations & Article Lookup
    slovak_word = ""
    german_raw = ""
    english_word = ""
    
    if lang == "sk":
        slovak_word = input_word
        print(f"  ➜ Translating Slovak to German & English...")
        german_raw = translate_text(slovak_word, 'sk', 'de')
        if german_raw is None:
            print(f"  {COLOR_RED}Translation SK->DE error{COLOR_RESET}")
            german_raw = slovak_word
        elif german_raw.lower().startswith("zu ") and len(german_raw.split()) == 2:
            # Remove leading 'zu ' if verb translation added it
            german_raw = german_raw[3:]

        english_word = translate_text(slovak_word, 'sk', 'en')
        if english_word is None:
            print(f"  {COLOR_RED}Translation SK->EN error{COLOR_RESET}")
            english_word = german_raw
    else:
        german_raw = input_word
        print(f"  ➜ Translating German to English & Slovak...")
        english_word = translate_text(german_raw, 'de', 'en')
        if english_word is None:
            print(f"  {COLOR_RED}Translation DE->EN error{COLOR_RESET}")
            english_word = german_raw

        slovak_word = translate_text(german_raw, 'de', 'sk')
        if slovak_word is None:
            slovak_word = ""
            
    # Format German Word & Article
    de_word_formatted, base_german_word, article = get_formatted_german_word(german_raw)
    
    print(f"  ➜ German Word: {COLOR_GREEN}{base_german_word}{COLOR_RESET}")
    if article:
        print(f"  ➜ Article:     {COLOR_GREEN}{article}{COLOR_RESET} -> {COLOR_BOLD}{article} {base_german_word}{COLOR_RESET}")
    else:
        print(f"  ➜ Article:     {COLOR_GRAY}None (not a noun or article unknown){COLOR_RESET}")
    print(f"  ➜ English:     {COLOR_GREEN}{english_word}{COLOR_RESET}")
    if slovak_word:
        print(f"  ➜ Slovak:      {COLOR_GREEN}{slovak_word}{COLOR_RESET}")
        
    # Handle Example Sentence
    de_sentence = ""
    en_sentence = ""
    if custom_sentence:
        custom_sentence = custom_sentence.strip()
        print(f"  ➜ Translating provided sentence...")
        if lang == "sk":
            de_sentence = translate_text(custom_sentence, 'sk', 'de')
            en_sentence = translate_text(custom_sentence, 'sk', 'en')
            if de_sentence is None:
                de_sentence = custom_sentence
            if en_sentence is None:
                en_sentence = custom_sentence
        elif lang == "de":
            de_sentence = custom_sentence
            en_sentence = translate_text(custom_sentence, 'de', 'en')
            if en_sentence is None:
                en_sentence = custom_sentence
    else:
        de_sentence = base_german_word
        en_sentence = english_word
        
    # Format en_word field HTML
    sk_note_html = f'<div style="color: #666; font-size: 1.0em; margin-top: 0.2em;"><i>SK: {slovak_word}</i></div>' if slovak_word else ''
    en_word_html = build_translation_header(english_word) + sk_note_html
    
    fields = {
        "Note ID": base_german_word,
        "de_word": de_word_formatted,
        "de_sentence": de_sentence,
        "en_word": en_word_html,
        "en_sentence": en_sentence,
        "en_note": "",
        "de_audio": ""
    }
    
    # 3. Duplicate Checking
    print(f"\n  ➜ Checking for duplicates in deck '{deck_name}'...")
    full_de_word_text = f"{article} {base_german_word}" if article else base_german_word
    duplicates = find_duplicates(anki, deck_name, base_german_word, full_de_word_text)
    
    if duplicates:
        print(f"\n{COLOR_YELLOW}{COLOR_BOLD}⚠️  DUPLICATE FOUND! ({len(duplicates)} matching note(s)){COLOR_RESET}")
        for idx, dup in enumerate(duplicates, 1):
            dup_fields = dup.get("fields", {})
            print(f"   Note ID #{dup.get('noteId')}:")
            print(f"     Note ID:     {dup_fields.get('Note ID', {}).get('value')}")
            print(f"     de_word:     {dup_fields.get('de_word', {}).get('value')}")
            print(f"     en_word:     {clean_word(dup_fields.get('en_word', {}).get('value'))[:60]}")
            
        if not force:
            if interactive:
                print(f"\n{COLOR_YELLOW}Options: [s]kip (default), [f]orce add, [u]pdate existing fields{COLOR_RESET}")
                choice = input("Select option [s/f/u]: ").strip().lower()
                if choice == 'u':
                    dup_id = duplicates[0]["noteId"]
                    print(f"Updating note ID {dup_id}...")
                    anki.update_note_fields(dup_id, {
                        "de_word": de_word_formatted,
                        "en_word": en_word_html,
                        "en_sentence": en_sentence,
                        "de_sentence": de_sentence,
                        "en_note": ""
                    })
                    print(f"{COLOR_GREEN}✓ Updated existing note successfully!{COLOR_RESET}")
                    return True
                elif choice != 'f':
                    print(f"{COLOR_GRAY}Skipped adding duplicate note.{COLOR_RESET}")
                    return False
            else:
                print(f"{COLOR_YELLOW}Skipping addition of duplicate note (use --force to override).{COLOR_RESET}")
                return False
    else:
        print(f"  {COLOR_GREEN}✓ No duplicate found.{COLOR_RESET}")
        
    # 4. Preview (No prompt required, auto-add directly)
    print_note_preview(fields)
            
    # 5. Add Note to Anki
    note_payload = {
        "deckName": deck_name,
        "modelName": MODEL_NAME,
        "fields": fields,
        "options": {
            "allowDuplicate": True if force else False,
            "duplicateScope": "deck"
        },
        "tags": ["terminal_added"]
    }
    
    try:
        note_id = anki.invoke("addNote", note=note_payload)
        print(f"\n{COLOR_GREEN}{COLOR_BOLD}✓ SUCCESS! Added note ID {note_id} to '{deck_name}'.{COLOR_RESET}")
        return True
    except Exception as e:
        print(f"\n{COLOR_RED}{COLOR_BOLD}✗ Failed to add note: {e}{COLOR_RESET}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Terminal utility to add German / Slovak vocabulary to Anki."
    )
    parser.add_argument("word", nargs="?", help="Word in German or Slovak to add")
    parser.add_argument("-l", "--lang", choices=["auto", "sk", "de"], default="auto", help="Specify input language (default: auto)")
    parser.add_argument("-d", "--deck", default=DECK_NAME, help=f"Target Anki deck (default: {DECK_NAME})")
    parser.add_argument("-s", "--sentence", help="Optional example sentence for initial word")
    parser.add_argument("-f", "--force", action="store_true", help="Force add note even if duplicate detected")
    parser.add_argument("-i", "--interactive", action="store_true", help="Stay open in interactive mode after processing initial word")
    
    args = parser.parse_args()
    
    print_banner()
    
    print("Connecting to AnkiConnect...")
    anki = AnkiConnect()
    try:
        ver = anki.invoke("version")
        print(f"{COLOR_GREEN}✓ Connected to AnkiConnect (v{ver}){COLOR_RESET}\n")
    except Exception as e:
        print(f"{COLOR_RED}✗ Error connecting to Anki: {e}{COLOR_RESET}")
        print("Please ensure Anki is running and AnkiConnect add-on is enabled.")
        sys.exit(1)
        
    # If a word was passed on command line:
    if args.word:
        process_and_add_word(
            anki,
            input_word=args.word,
            input_lang=args.lang,
            custom_sentence=args.sentence,
            deck_name=args.deck,
            force=args.force,
            interactive=True
        )
        # Exit directly unless explicit -i / --interactive flag was given
        if not args.interactive:
            return
        print("\n" + "=" * 60 + "\n")
        
    # Interactive REPL mode (when run without arguments or with -i)
    print(f"{COLOR_CYAN}Interactive Mode. Enter words in Slovak or German.{COLOR_RESET}")
    print(f"{COLOR_GRAY}Type 'q' or press Ctrl+C to exit.{COLOR_RESET}\n")
    
    try:
        while True:
            try:
                user_input = input(f"{COLOR_BOLD}Enter word (SK/DE) > {COLOR_RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{COLOR_GRAY}Exiting... Goodbye!{COLOR_RESET}")
                break
                
            if not user_input:
                continue
            if user_input.lower() in ('q', 'quit', 'exit'):
                print(f"{COLOR_GRAY}Goodbye!{COLOR_RESET}")
                break
                
            process_and_add_word(
                anki,
                input_word=user_input,
                input_lang=args.lang,
                custom_sentence=None,
                deck_name=args.deck,
                force=args.force,
                interactive=True
            )
            print("\n" + "-" * 60 + "\n")
    except KeyboardInterrupt:
        print(f"\n{COLOR_GRAY}Exiting... Goodbye!{COLOR_RESET}")


if __name__ == "__main__":
    main()

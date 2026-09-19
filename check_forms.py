#!/usr/bin/env python3
"""Spot-check the Wiktionary plural/Perfekt lookups without touching the deck.

Anki does not need to be running - this only talks to de.wiktionary.org. Use it to
confirm the lookups behave before running edit_german_notes.py against your notes.

    python check_forms.py            # check the default sample
    python check_forms.py Tür gehen  # check specific words
"""

import sys

from edit_german_notes import (
    fetch_german_wikitext,
    get_gender_from_wiktionary,
    get_word_forms,
    guess_part_of_speech,
    parse_headword,
)

# Words chosen to exercise each branch: regular noun, compound, neuter, plural-only,
# no-plural, sein-verb, haben-verb, separable verb, reflexive entry
SAMPLE = [
    "Tür",
    "Drohnenangriff",
    "Mädchen",
    "Bücher",
    "Erbrechen",
    "gehen",
    "arbeiten",
    "aufstehen",
    "sich freuen",
]


def main(words):
    for entry in words:
        article, headword = parse_headword(entry)
        part_of_speech = guess_part_of_speech(headword)

        print(f"\n{entry!r} -> headword {headword!r}, guessed {part_of_speech}")

        if fetch_german_wikitext(headword) is None:
            print("  ✗ no German Wiktionary entry (or the request failed)")
            continue

        if part_of_speech == "noun":
            gender = get_gender_from_wiktionary(headword)
            print(f"  gender:  {gender}")

        forms = get_word_forms(headword)
        print(f"  plural:  {forms.get('plural')}")
        print(f"  perfekt: {forms.get('perfekt')}")


if __name__ == "__main__":
    main(sys.argv[1:] or SAMPLE)

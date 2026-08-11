#!/usr/bin/env python3
"""Offline tests for the plural/Perfekt parsing helpers.

No network access is required - every test runs against fixture wikitext.

    python -m unittest test_forms_parsing
"""

import unittest
from unittest import mock

import edit_german_notes
from edit_german_notes import (
    build_forms_html,
    clean_wikitext_value,
    extract_german_section,
    get_noun_plural,
    get_verb_perfekt,
    guess_part_of_speech,
    parse_headword,
    parse_overview_template,
    strip_forms_block,
)

TUER = """
== Tür ({{Sprache|Deutsch}}) ==
=== {{Wortart|Substantiv|Deutsch}}, {{f}} ===

{{Deutsch Substantiv Übersicht
|Genus=f
|Nominativ Singular=Tür
|Nominativ Plural=Türen
|Genitiv Singular=Tür
|Genitiv Plural=Türen
|Dativ Singular=Tür
|Dativ Plural=Türen
|Akkusativ Singular=Tür
|Akkusativ Plural=Türen
}}
"""

# Two plurals, and a value carrying a footnote template and a link
BAND = """
== Band ({{Sprache|Deutsch}}) ==
=== {{Wortart|Substantiv|Deutsch}}, {{n}} ===

{{Deutsch Substantiv Übersicht
|Genus=n
|Nominativ Singular=Band
|Nominativ Plural 1=Bänder{{Anm.|meist [[Stoff]]}}
|Nominativ Plural 2=Bande
}}
"""

# Singularetantum: the plural parameter is present but empty
ERBRECHEN = """
== Erbrechen ({{Sprache|Deutsch}}) ==
=== {{Wortart|Substantiv|Deutsch}}, {{n}} ===

{{Deutsch Substantiv Übersicht
|Genus=n
|Nominativ Singular=Erbrechen
|Nominativ Plural=
}}
"""

GEHEN = """
== gehen ({{Sprache|Deutsch}}) ==
=== {{Wortart|Verb|Deutsch}} ===

{{Deutsch Verb Übersicht
|Präsens_ich=gehe
|Präsens_du=gehst
|Präsens_er, sie, es=geht
|Präteritum_ich=ging
|Partizip II=gegangen
|Konjunktiv II_ich=ginge
|Imperativ Singular=geh
|Imperativ Plural=geht
|Hilfsverb=sein
}}
"""

ARBEITEN = """
== arbeiten ({{Sprache|Deutsch}}) ==
=== {{Wortart|Verb|Deutsch}} ===

{{Deutsch Verb Übersicht
|Präsens_ich=arbeite
|Präteritum_ich=arbeitete
|Partizip II=gearbeitet
|Hilfsverb=haben
}}
"""

AUFSTEHEN = """
== aufstehen ({{Sprache|Deutsch}}) ==
=== {{Wortart|Verb|Deutsch}} ===

{{Deutsch Verb Übersicht
|Präsens_ich=stehe auf
|Präteritum_ich=stand auf
|Partizip II=aufgestanden
|Hilfsverb=sein
}}
"""

FAHREN = """
== fahren ({{Sprache|Deutsch}}) ==
=== {{Wortart|Verb|Deutsch}} ===

{{Deutsch Verb Übersicht
|Präsens_ich=fahre
|Präteritum_ich=fuhr
|Partizip II=gefahren
|Hilfsverb=haben
|Hilfsverb2=sein
}}
"""


class TestParseOverviewTemplate(unittest.TestCase):
    def test_reads_every_parameter(self):
        params = parse_overview_template(TUER, "Deutsch Substantiv Übersicht")
        self.assertEqual(params["Genus"], "f")
        self.assertEqual(params["Nominativ Singular"], "Tür")
        self.assertEqual(params["Nominativ Plural"], "Türen")
        self.assertEqual(params["Akkusativ Plural"], "Türen")

    def test_keeps_nested_templates_and_links_in_one_value(self):
        """A nested {{...}} must not be mistaken for the end of the template."""
        params = parse_overview_template(BAND, "Deutsch Substantiv Übersicht")
        self.assertEqual(params["Nominativ Plural 1"], "Bänder{{Anm.|meist [[Stoff]]}}")
        self.assertEqual(params["Nominativ Plural 2"], "Bande")

    def test_missing_template_gives_empty_dict(self):
        self.assertEqual(parse_overview_template(GEHEN, "Deutsch Substantiv Übersicht"), {})
        self.assertEqual(parse_overview_template("", "Deutsch Substantiv Übersicht"), {})

    def test_unterminated_template_gives_empty_dict(self):
        self.assertEqual(
            parse_overview_template("{{Deutsch Verb Übersicht|Partizip II=x", "Deutsch Verb Übersicht"),
            {},
        )


class TestCleanWikitextValue(unittest.TestCase):
    def test_strips_markup(self):
        self.assertEqual(clean_wikitext_value("Bänder{{Anm.|meist [[Stoff]]}}"), "Bänder")
        self.assertEqual(clean_wikitext_value("[[Tür|Türen]]"), "Türen")
        self.assertEqual(clean_wikitext_value("'''Türen'''"), "Türen")
        self.assertEqual(clean_wikitext_value("Türen <!-- comment -->"), "Türen")


class TestNounPlural(unittest.TestCase):
    def test_regular_plural_gets_die(self):
        self.assertEqual(get_noun_plural(TUER), "die Türen")

    def test_first_of_several_plurals_is_used(self):
        self.assertEqual(get_noun_plural(BAND), "die Bänder")

    def test_singularetantum_has_no_plural(self):
        self.assertIsNone(get_noun_plural(ERBRECHEN))

    def test_verbs_are_not_given_a_plural(self):
        self.assertIsNone(get_noun_plural(GEHEN))


class TestVerbPerfekt(unittest.TestCase):
    def test_auxiliary_sein(self):
        self.assertEqual(get_verb_perfekt(GEHEN), "ist gegangen")

    def test_auxiliary_haben(self):
        self.assertEqual(get_verb_perfekt(ARBEITEN), "hat gearbeitet")

    def test_separable_verb_keeps_its_prefix(self):
        self.assertEqual(get_verb_perfekt(AUFSTEHEN), "ist aufgestanden")

    def test_both_auxiliaries_are_shown(self):
        self.assertEqual(get_verb_perfekt(FAHREN), "hat/ist gefahren")

    def test_nouns_are_not_given_a_perfekt(self):
        self.assertIsNone(get_verb_perfekt(TUER))


class TestParseHeadword(unittest.TestCase):
    def test_bare_noun(self):
        self.assertEqual(parse_headword("Tür"), (None, "Tür"))

    def test_article_added_by_an_earlier_run_is_stripped(self):
        self.assertEqual(parse_headword("der Drohnenangriff"), ("der", "Drohnenangriff"))

    def test_reflexive_particle_is_stripped(self):
        self.assertEqual(parse_headword("sich freuen"), (None, "freuen"))

    def test_placeholder_particle_is_stripped(self):
        self.assertEqual(parse_headword("jdn. sehen"), (None, "sehen"))

    def test_empty_input(self):
        self.assertEqual(parse_headword(""), (None, ""))


class TestGuessPartOfSpeech(unittest.TestCase):
    def test_capitalised_is_a_noun(self):
        self.assertEqual(guess_part_of_speech("Tür"), "noun")

    def test_infinitive_is_a_verb(self):
        self.assertEqual(guess_part_of_speech("gehen"), "verb")
        self.assertEqual(guess_part_of_speech("sammeln"), "verb")

    def test_other_lowercase_words_are_skipped(self):
        self.assertIsNone(guess_part_of_speech("schnell"))
        self.assertIsNone(guess_part_of_speech(""))


class TestFormsBlock(unittest.TestCase):
    def test_round_trip_leaves_the_bare_headword(self):
        """Re-running must see the headword alone, never headword+forms fused together."""
        rendered = "<b>die Tür</b>" + build_forms_html("die Türen")
        self.assertEqual(strip_forms_block(rendered), "<b>die Tür</b>")

    def test_stripping_is_idempotent(self):
        self.assertEqual(strip_forms_block("<b>die Tür</b>"), "<b>die Tür</b>")

    def test_a_field_without_a_block_is_untouched(self):
        self.assertEqual(strip_forms_block("<b>gehen</b>"), "<b>gehen</b>")


class TestExtractGermanSection(unittest.TestCase):
    def test_other_languages_are_excluded(self):
        page = (
            "== Tür ({{Sprache|Deutsch}}) ==\n{{Deutsch Substantiv Übersicht|Nominativ Plural=Türen}}\n"
            "== Tür ({{Sprache|Englisch}}) ==\n{{Deutsch Substantiv Übersicht|Nominativ Plural=WRONG}}\n"
        )
        german = extract_german_section(page)
        self.assertIn("Türen", german)
        self.assertNotIn("WRONG", german)


GENDER_PAGES = {
    "Tisch": "=== {{Wortart|Substantiv|Deutsch}}, {{m}} ===\n{{Deutsch Substantiv Übersicht|Genus=m}}",
    # A plural page that points at its base form
    "Bücher": "* Nominativ Plural des Substantivs\n{{Grundformverweis Dekl|Buch}}",
    "Buch": "=== {{Wortart|Substantiv|Deutsch}}, {{n}} ===",
    # The 'Plural des Substantivs' wording, which uses a link instead of a template
    "Weise": "Plural des Substantivs '''[[Weiser]]'''",
    "Weiser": "=== {{Wortart|Substantiv|Deutsch}}, {{m}} ===",
    # Compound with no page of its own: resolved from the part after the hyphen
    "Corona-Krise": None,
    "Krise": "=== {{Wortart|Substantiv|Deutsch}}, {{f}} ===",
}


class TestGenderLookup(unittest.TestCase):
    """Guards the fallback chain in get_gender_from_wiktionary, which shares its page
    fetch with the forms lookup. Expected values match gender_cache.json."""

    def setUp(self):
        patches = [
            mock.patch.dict(edit_german_notes.GENDER_CACHE, {}, clear=True),
            mock.patch.object(edit_german_notes, "save_cache", lambda: None),
            mock.patch.object(edit_german_notes, "fetch_german_wikitext", GENDER_PAGES.get),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_direct_gender(self):
        self.assertEqual(edit_german_notes.get_gender_from_wiktionary("Tisch"), "m")

    def test_plural_via_grundformverweis(self):
        self.assertEqual(edit_german_notes.get_gender_from_wiktionary("Bücher"), "pl")

    def test_plural_via_plural_des_substantivs(self):
        self.assertEqual(edit_german_notes.get_gender_from_wiktionary("Weise"), "pl")

    def test_hyphen_fallback(self):
        self.assertEqual(edit_german_notes.get_gender_from_wiktionary("Corona-Krise"), "f")

    def test_unknown_word(self):
        self.assertIsNone(edit_german_notes.get_gender_from_wiktionary("Unbekannt"))


class FakeAnki:
    """Stands in for AnkiConnect, recording writes instead of performing them."""

    def __init__(self):
        self.updates = []

    def update_note_fields(self, note_id, fields):
        self.updates.append((note_id, fields))


PAGES = {
    "Tür": TUER,
    "gehen": GEHEN,
    "Erbrechen": ERBRECHEN,
    "Bücher": TUER,  # content is irrelevant: the gender stub reports it as plural
}

GENDERS = {"Tür": "f", "Erbrechen": "n", "Bücher": "pl"}


class TestEditNoteDeWord(unittest.TestCase):
    """End-to-end cover of the de_word rendering with the network stubbed out."""

    def setUp(self):
        # Neutralise the on-disk caches so tests neither read nor write real data
        patches = [
            mock.patch.dict(edit_german_notes.FORMS_CACHE, {}, clear=True),
            mock.patch.object(edit_german_notes, "save_forms_cache", lambda: None),
            mock.patch.object(edit_german_notes, "save_cache", lambda: None),
            mock.patch.object(edit_german_notes, "fetch_german_wikitext", PAGES.get),
            mock.patch.object(edit_german_notes, "get_gender_from_wiktionary", GENDERS.get),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def render(self, de_word):
        """Run edit_note once and return the resulting de_word value."""
        anki = FakeAnki()
        note = {
            "noteId": 1,
            "modelName": "german",
            "tags": [],
            "fields": {"de_word": {"value": de_word}},
        }
        edit_german_notes.edit_note(note, anki)
        if not anki.updates:
            return de_word
        return anki.updates[-1][1]["de_word"]

    def test_noun_gains_article_and_plural(self):
        self.assertEqual(
            self.render("Tür"),
            '<b>die Tür</b>' + build_forms_html("die Türen"),
        )

    def test_verb_gains_perfekt_but_no_article(self):
        self.assertEqual(
            self.render("gehen"),
            '<b>gehen</b>' + build_forms_html("ist gegangen"),
        )

    def test_noun_already_carrying_an_article_still_gains_its_plural(self):
        """The 73 notes processed before this change must pick up a plural."""
        self.assertEqual(
            self.render("<b>die Tür</b>"),
            '<b>die Tür</b>' + build_forms_html("die Türen"),
        )

    def test_plural_only_noun_gets_no_second_line(self):
        self.assertEqual(self.render("Bücher"), "<b>die Bücher</b>")

    def test_noun_without_a_plural_gets_no_second_line(self):
        self.assertEqual(self.render("Erbrechen"), "<b>das Erbrechen</b>")

    def test_unknown_word_is_left_alone_apart_from_bolding(self):
        self.assertEqual(self.render("Xyzzy"), "<b>Xyzzy</b>")

    def test_rendering_is_idempotent(self):
        """A second run must be a no-op - the headword must not absorb the forms line."""
        for word in ("Tür", "gehen", "Bücher", "Erbrechen"):
            with self.subTest(word=word):
                once = self.render(word)
                twice = self.render(once)
                self.assertEqual(once, twice)

    def test_second_run_writes_nothing(self):
        anki = FakeAnki()
        note = {
            "noteId": 1,
            "modelName": "german",
            "tags": [],
            "fields": {"de_word": {"value": self.render("Tür")}},
        }
        self.assertFalse(edit_german_notes.edit_note(note, anki))
        self.assertEqual(anki.updates, [])

    def test_dry_run_does_not_write(self):
        anki = FakeAnki()
        note = {
            "noteId": 1,
            "modelName": "german",
            "tags": [],
            "fields": {"de_word": {"value": "Tür"}},
        }
        self.assertTrue(edit_german_notes.edit_note(note, anki, dry_run=True))
        self.assertEqual(anki.updates, [])


if __name__ == "__main__":
    unittest.main()

"""
Plover "python dictionary" for Russian noun case/number modifiers.

Plover natively supports dictionaries written as a .py file exposing
LONGEST_KEY and a lookup(key) function - no plugin registration needed,
just add this file to Plover's dictionary list. `key` is a tuple of
stroke strings (in RTF/CRE text form); lookup() returns the translation
or raises KeyError.

Mechanism (see THEORY.md sections 3-4 for the full design):
  - `key[:-1]` (joined with "/") is looked up as a root outline in
    roots.json - the same file Plover's own JSON dictionary loads for
    plain single-stroke nominative forms.
  - `key[-1]` is parsed as a grammar modifier stroke: "#" + a
    case-mnemonic consonant + "*" for singular, "#" + "*" + the
    consonant for plural, with an optional trailing "н" (the -н key)
    marking the masculine gender override.
  - The root's declension/gender is inferred from its own spelling
    (nominative singular text), not stored anywhere - see
    _infer_paradigm below. This mirrors classify_stem in grammar/nouns.py
    but works one level up: classify_stem determines spelling-rule
    behavior (velar/husher/sibilant/soft) from a stem, while this
    infers which DECLENSION (1/2/3) and GENDER a whole nominative-
    singular word belongs to before handing off to decline_noun.

Only genitive (Р) and instrumental (Т) are wired up so far, matching
the only two cases worked out in THEORY.md section 4. Extend
_CASE_LETTERS as more cases are assigned mnemonic consonants.
"""

import json
from pathlib import Path

from plover_russian_firebird.grammar.nouns import decline_noun

_ROOTS_PATH = Path(__file__).with_name("roots.json")
with open(_ROOTS_PATH, encoding="utf-8") as _f:
    _ROOTS = json.load(_f)

LONGEST_KEY = 4  # supports up to a 3-stroke root (e.g. "болото") + 1 modifier stroke

_CASE_LETTERS = {"Р": "gen", "Т": "ins"}


def _parse_modifier(stroke):
    """Return (case, number, masc_override) or None if not a modifier stroke."""
    if not stroke.startswith("#"):
        return None
    body = stroke[1:]
    if "*" not in body:
        return None
    star_index = body.index("*")
    before, after = body[:star_index], body[star_index + 1:]
    masc_override = "н" in after
    after_letters = after.replace("н", "")
    if before and not after_letters:
        case, number = _CASE_LETTERS.get(before), "sg"
    elif after_letters and not before:
        case, number = _CASE_LETTERS.get(after_letters), "pl"
    else:
        return None
    if case is None:
        return None
    return case, number, masc_override


def _infer_paradigm(word, masc_override):
    """
    Infer (stem, declension, gender, soft) from a nominative-singular
    word's own spelling. The one case spelling can't resolve - gender of
    a ь-final noun (гвоздь vs мышь) - takes the masc_override flag from
    the modifier stroke; everything else follows deterministically from
    the final letter(s), per THEORY.md section 4.
    """
    last = word[-1]
    if last == "а":
        return word[:-1], 1, "f", False
    if last == "я":
        return word[:-1], 1, "f", True
    if last == "о":
        return word[:-1], 2, "n", False
    if last == "е":
        return word[:-1], 2, "n", True
    if last == "й":
        return word, 2, "m", True
    if last == "ь":
        if masc_override:
            return word, 2, "m", True
        return word, 3, "f", True
    return word, 2, "m", False


def lookup(key):
    if len(key) < 2:
        raise KeyError(key)

    root_stroke = "/".join(key[:-1])
    word = _ROOTS.get(root_stroke)
    if word is None:
        raise KeyError(key)

    parsed = _parse_modifier(key[-1])
    if parsed is None:
        raise KeyError(key)
    case, number, masc_override = parsed

    stem, declension, gender, soft = _infer_paradigm(word, masc_override)
    return decline_noun(stem, declension, case, number, gender=gender, animate=False, soft=soft)

"""
Russian noun declension engine.

Given a bare stem and a target (case, number), produces the inflected
form by table lookup plus the standard Russian spelling rules:

  Rule A - never write "ы" after г,к,х,ж,ш,ч,щ; write "и" instead.
  Rule B - after ж,ш,ч,щ,ц an ending "о" is written only when stressed,
           otherwise "е" (e.g. ножом vs мужем, отцов vs месяцев).
  Rule C - never write "я"/"ю" after ж,ш,ч,щ,ц; write "а"/"у" instead.

`stem` is the dictionary-form stem the caller supplies, e.g. "стол" or
"конь" (masculine, trailing ь/й kept to signal a soft stem) or "стен"
(the -а stripped from "стена"). This module does not derive a stem from
a full word - that is the caller's job (or, later, the root list's).

Known limitations, deliberately out of scope for this first pass:
  - Fleeting vowels (окно -> окон, отец -> отца) are lexical, not
    derivable from spelling rules, and are not handled.
  - Nouns in -ий/-ие/-ия (санаторий, здание, армия) take -ии instead of
    -е in dative/prepositional singular, and -ий instead of -ей in
    genitive plural. Not handled yet.
  - е/ё are treated as the same letter (ё is never produced), since we
    have no stress dictionary to know when it applies.
  - Indeclinable nouns, suppletive plurals (like человек/люди), and
    stem-extending nouns (мать/матери, время/времени) are not handled.
  - "stressed" must be supplied by the caller; there's no stress
    dictionary here yet.
"""

CASES = ("nom", "gen", "dat", "acc", "ins", "pre")

VELARS = set("гкх")
HUSHERS = set("жшчщ")
SIBILANT = "ц"
SOFT_MARKERS = set("ьй")

NOUN_ENDINGS = {
    1: {  # a-stems (папа, стена, земля...) - endings don't depend on gender
        "hard": {
            "sg": {"nom": "а", "gen": "ы", "dat": "е", "acc": "у", "ins": "ой", "pre": "е"},
            "pl": {"nom": "ы", "gen": "", "dat": "ам", "ins": "ами", "pre": "ах"},
        },
        "soft": {
            "sg": {"nom": "я", "gen": "и", "dat": "е", "acc": "ю", "ins": "ей", "pre": "е"},
            "pl": {"nom": "и", "gen": "ь", "dat": "ям", "ins": "ями", "pre": "ях"},
        },
    },
    2: {  # стол/конь (masculine), окно/поле (neuter)
        "m": {
            "hard": {
                "sg": {"nom": "", "gen": "а", "dat": "у", "ins": "ом", "pre": "е"},
                "pl": {"nom": "ы", "gen": "ов", "dat": "ам", "ins": "ами", "pre": "ах"},
            },
            "soft": {
                "sg": {"nom": "", "gen": "я", "dat": "ю", "ins": "ем", "pre": "е"},
                "pl": {"nom": "и", "gen": "ей", "dat": "ям", "ins": "ями", "pre": "ях"},
            },
        },
        "n": {
            "hard": {
                "sg": {"nom": "о", "gen": "а", "dat": "у", "ins": "ом", "pre": "е"},
                "pl": {"nom": "а", "gen": "", "dat": "ам", "ins": "ами", "pre": "ах"},
            },
            "soft": {
                "sg": {"nom": "е", "gen": "я", "dat": "ю", "ins": "ем", "pre": "е"},
                "pl": {"nom": "я", "gen": "ей", "dat": "ям", "ins": "ями", "pre": "ях"},
            },
        },
    },
    3: {  # мышь/ночь - feminine ь-stems, single paradigm
        "sg": {"nom": "", "gen": "и", "dat": "и", "ins": "ью", "pre": "и"},
        "pl": {"nom": "и", "gen": "ей", "dat": "ям", "ins": "ями", "pre": "ях"},
    },
}


def classify_stem(stem, soft=False):
    """Classify a stem's final sound for spelling-rule purposes."""
    last = stem[-1]
    if last in SOFT_MARKERS:
        # The consonant the marker softens is what actually matters for
        # the husher spelling rules (e.g. "мышь" is a husher stem
        # even though the literal last character is "ь").
        if len(stem) >= 2 and stem[-2] in HUSHERS:
            return "husher"
        return "soft"
    if last in VELARS:
        return "velar"
    if last in HUSHERS:
        return "husher"
    if last == SIBILANT:
        return "sibilant"
    return "soft" if soft else "hard"


def _apply_spelling_rules(ending, stem_type, stressed):
    if not ending:
        return ending
    first = ending[0]
    if stem_type in ("velar", "husher") and first == "ы":
        return "и" + ending[1:]
    if stem_type in ("husher", "sibilant"):
        if first == "о" and not stressed:
            return "е" + ending[1:]
        if first == "я":
            return "а" + ending[1:]
        if first == "ю":
            return "у" + ending[1:]
    return ending


def _resolve_case(case, declension, number, gender, animate):
    """Accusative is almost always an alias of nominative or genitive."""
    if case != "acc":
        return case
    if number == "pl":
        return "gen" if animate else "nom"
    if declension == 1:
        return "acc"  # decl.1 singular has its own real accusative ending
    if declension == 2 and gender == "m":
        return "gen" if animate else "nom"
    return "nom"  # decl.2 neuter singular, decl.3 singular


def decline_noun(stem, declension, case, number, gender="f", animate=False, soft=False, stressed=False):
    """
    stem:       dictionary-form stem, e.g. "стол", "конь", "стен" (from стена)
    declension: 1 (стена-type), 2 (стол/окно-type), or 3 (мышь-type)
    case:       one of CASES
    number:     "sg" or "pl"
    gender:     "m"/"f"/"n" - only affects declension 2
    animate:    affects accusative syncretism
    soft:       set True for a soft stem ending in a plain consonant
                that isn't inherently hard or soft (бвдзлмнпрстф).
                Ignored (auto-detected) when the stem already ends in
                ь/й or a velar/husher/sibilant.
    stressed:   whether the ending itself carries stress (affects the
                о/е alternation after hushers and ц). Defaults to
                unstressed since that's the more common case; the
                caller must supply this - there's no stress dictionary.
    """
    if declension not in (1, 2, 3):
        raise ValueError(f"unknown declension {declension!r}")
    if case not in CASES:
        raise ValueError(f"unknown case {case!r}")
    if number not in ("sg", "pl"):
        raise ValueError(f"unknown number {number!r}")

    stem_type = classify_stem(stem, soft=soft)
    table_variant = "soft" if stem_type == "soft" else "hard"
    base = stem[:-1] if stem[-1] in SOFT_MARKERS else stem

    resolved_case = _resolve_case(case, declension, number, gender, animate)

    if declension == 1:
        ending = NOUN_ENDINGS[1][table_variant][number][resolved_case]
    elif declension == 2:
        ending = NOUN_ENDINGS[2][gender][table_variant][number][resolved_case]
    else:
        ending = NOUN_ENDINGS[3][number][resolved_case]

    # Masculine genitive plural has two lexicalized exceptions that
    # don't follow from the general spelling rules: husher stems borrow
    # the soft ending outright (ножей, ключей), and й-stems take -ев
    # instead of -ей (музей -> музеев, not музеей).
    if declension == 2 and gender == "m" and resolved_case == "gen" and number == "pl":
        if stem_type == "husher":
            ending = "ей"
        elif stem_type == "soft" and stem[-1] == "й":
            ending = "ев"
        else:
            ending = _apply_spelling_rules(ending, stem_type, stressed)
    else:
        ending = _apply_spelling_rules(ending, stem_type, stressed)

    # A zero ending on a soft-marked stem (e.g. "конь", "музей", "мышь")
    # means the ь/й itself IS the ending - it only drops when a real
    # vowel ending is appended, so the stem is returned unstripped.
    if not ending:
        return stem

    return base + ending

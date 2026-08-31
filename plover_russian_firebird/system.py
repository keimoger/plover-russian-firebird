"""
Firebird - a Russian steno theory for Plover.

This module is registered under the "plover.system" entry point in
pyproject.toml, which is how Plover discovers it as a selectable system
(Preferences > System).

This is still a skeleton: the physical KEYS layout below is accurate
(taken from the Plover wiki's diagram of this 22-key Stenograph/Stentura
machine, which documents the raw hardware only - no theory has been
built for it before this one). Everything theory-specific (orthography
rules, dictionaries, number layout, suffix folding) is still TODO.

Physical layout, read column by column (top key, then bottom key), the
same way English steno order reads STKPWHRAO*EUFRPBLGTSDZ:

    left hand:    С (single key)  Т/П  В/К  М/Р
    left thumb:   Н  Е
    star:         *
    right thumb:  О  А
    right hand:   И/С  Т/Л  В/К  М/Р  ь/н (last column)
    number bar:   #

Capital "Н" (the left thumb key) and lowercase "н" (the last
right-hand column) are genuinely different physical keys that happen
to reuse the same base letter - not a duplicate or a typo. Cyrillic
upper/lower case are distinct Unicode characters, and combined with
the "-" hyphen placement below, every key name is unique. The last
column's other key is dedicated directly to "ь" (soft sign) - it has
no capital-vs-lowercase counterpart elsewhere on the board, since it
isn't reused for anything but this one letter.
"""

KEYS = (
    "#",
    "С-", "Т-", "П-", "В-", "К-", "М-", "Р-",
    "Н-", "Е-",
    "*",
    "-О", "-А",
    "-И", "-С", "-Т", "-Л", "-В", "-К", "-М", "-Р",
    "-ь", "-н",
)

IMPLICIT_HYPHEN_KEYS = ("Н-", "Е-", "*", "-О", "-А")

SUFFIX_KEYS = ()

NUMBER_KEY = None
NUMBERS = {}

UNDO_STROKE_STENO = "*"

ORTHOGRAPHY_RULES = [
    # Present/future tense conjugation stems. Verb roots store the
    # infinitive (THEORY.md section 1), and Russian's two conjugation
    # classes strip DIFFERENT amounts of it before adding a person
    # ending: 2nd conjugation (-ить infinitives, e.g. говорить) drops
    # the whole "-ить", not just "-ть" - "говорить"+"ю" must give
    # "говорю", not "говорию". This has to be tried BEFORE the general
    # vowel-replacement rule below, since any -ить infinitive also ends
    # in "ь" and would otherwise match that rule first and only strip
    # the trailing ь ("читатю"-style wrong result). Covers the regular
    # majority; genuine exceptions (брить/стелить are 1st conjugation
    # despite ending in -ить; most 1st-person-singular consonant
    # mutations like видеть->вижу, любить->люблю) need explicit root
    # overrides, same as -ти/-чь infinitives already do for past tense.
    (r"^(.+)ить \^ ([аеёиоуыэюя].*)$", r"\1\2"),
    # 1st conjugation (most other infinitives, e.g. читать, делать):
    # strip only "-ть", keeping the thematic vowel - "читать"+"ю" gives
    # "читаю". Tried after the -ить rule above (more specific first),
    # but still before the general vowel-replacement rule, for the same
    # reason: an infinitive ending in "ь" would otherwise only get its
    # trailing ь stripped instead of the full "-ть".
    (r"^(.+)ть \^ ([аеёиоуыэюя].*)$", r"\1\2"),
    # Root nominatives stored in firebird-main.json often end in a vowel, ь, or
    # й (поле, база, царь, музей) - gluing a new vowel-initial case
    # ending onto those needs to REPLACE that trailing letter, not
    # append after it ("поле" + "я" must give "поля", not "полея").
    # Applies uniformly regardless of which vowel/ь/й precedes or which
    # vowel-initial suffix follows.
    (r"^(.+)[ьйаеёиоуыэюя] \^ ([аеёиоуыэюяь].*)$", r"\1\2"),
    # ы -> и after velars/hushers (г,к,х,ж,ш,ч,щ) - the "7-letter rule",
    # never stress-dependent, always applies. Used by the manual
    # letter-glue suffixes (dictionaries/firebird-suffixes.json) so a speaker
    # can press the ordinary ы stroke and get the correct spelling
    # regardless of the preceding root's final consonant.
    (r"^(.*[гкхжшчщ]) \^ ы$", r"\1и"),
    # я/ю -> а/у after hushers+ц (ж,ш,ч,щ,ц) - the "5-letter rule",
    # likewise never stress-dependent.
    (r"^(.*[жшчщц]) \^ я$", r"\1а"),
    (r"^(.*[жшчщц]) \^ ю$", r"\1у"),
    # Deliberately NOT automating о -> е after ж/ш/ч/щ/ц (THEORY.md
    # section 5): that rule depends on stress, which this system has
    # no way to know. The speaker presses о or е directly instead.
    # Verb roots store the infinitive (читать, говорить - THEORY.md
    # section 1's "infinitive for verbs later"), which ends in -ть for
    # the regular conjugation classes. Past tense needs that -ть
    # stripped before gluing the -л/-ла/-ло/-ли endings (section 10):
    # "читать" + "л" must give "читал", not "читатьл". Only covers the
    # regular -ть infinitive class - -ти (нести->нёс) and -чь
    # (мочь->мог) infinitives are genuinely irregular/suppletive and
    # need explicit root overrides regardless, same as any other
    # exception in this theory.
    (r"^(.+)ть \^ (л.*)$", r"\1\2"),
]
ORTHOGRAPHY_RULES_ALIASES = {}
ORTHOGRAPHY_WORDLIST = None

KEYMAPS = {
    # Plover HID protocol positions (merged into Plover core), taken
    # verbatim from https://github.com/dnaq/plover-machine-hid#the-keys.
    # Both layouts are 22-key Stenotype-shaped boards, so the mapping is
    # purely positional: tall single key, three split columns, thumb
    # vowels, star, thumb vowels, split columns, number bar.
    #
    # This specific keymap is tuned for a Polyglot keyboard, which wires
    # S1-/S2- and the star positions differently from the generic
    # reference layout: S1- is physically the number bar, S2- is the
    # tall left-pinky key, and all four star positions (*1-*4) fire for
    # a single physical star key.
    "Plover HID": {
        "#": ["S1-"],
        "С-": ["S2-"],
        "Т-": ["T-"],
        "П-": ["K-"],
        "В-": ["P-"],
        "К-": ["W-"],
        "М-": ["H-"],
        "Р-": ["R-"],
        "Н-": ["A-"],
        "Е-": ["O-"],
        "*": ["*1", "*2", "*3", "*4"],
        "-О": ["-E"],
        "-А": ["-U"],
        "-И": ["-F"],
        "-С": ["-R"],
        "-Т": ["-P"],
        "-Л": ["-B"],
        "-В": ["-L"],
        "-К": ["-G"],
        "-М": ["-T"],
        "-Р": ["-S"],
        "-ь": ["-D"],
        "-н": ["-Z"],
    },
}

DICTIONARIES_ROOT = "asset:plover_russian_firebird:dictionaries"
DEFAULT_DICTIONARIES = [
    "firebird-user.json",
    "firebird-commands.json",
    "firebird-main.json",
    "firebird-prefixes.json",
    "firebird-suffixes.json",
    "firebird-fingerspelling.json",
]

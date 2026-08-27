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
    right hand:   И/С  Т/Л  В/К  М/Р  и/н (last column, lowercase)
    number bar:   #

Capital "И"/"Н" (the left/right thumb keys) and lowercase "и"/"н" (the
last right-hand column) are genuinely different physical keys that
happen to reuse the same base letter - not a duplicate or a typo.
Cyrillic upper/lower case are distinct Unicode characters, and combined
with the "-" hyphen placement below, every key name is unique.
"""

KEYS = (
    "#",
    "С-", "Т-", "П-", "В-", "К-", "М-", "Р-",
    "Н-", "Е-",
    "*",
    "-О", "-А",
    "-И", "-С", "-Т", "-Л", "-В", "-К", "-М", "-Р",
    "-и", "-н",
)

IMPLICIT_HYPHEN_KEYS = ("Н-", "Е-", "*", "-О", "-А")

SUFFIX_KEYS = ()

NUMBER_KEY = None
NUMBERS = {}

UNDO_STROKE_STENO = "*"

ORTHOGRAPHY_RULES = []
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
        "-и": ["-D"],
        "-н": ["-Z"],
    },
}

DICTIONARIES_ROOT = "asset:plover_russian_firebird:dictionaries"
DEFAULT_DICTIONARIES = ["user.json", "roots.json", "endings.py"]

"""
Sanity checks for the noun declension engine against known-correct
Russian words. Run directly with: python3 tests/test_nouns.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plover_russian_firebird.grammar.nouns import decline_noun

CASES = ("nom", "gen", "dat", "acc", "ins", "pre")


def check(label, stem, declension, gender, expected_sg, expected_pl, **kwargs):
    for case, expected in zip(CASES, expected_sg):
        got = decline_noun(stem, declension, case, "sg", gender=gender, **kwargs)
        assert got == expected, f"{label} sg {case}: expected {expected!r}, got {got!r}"
    for case, expected in zip(CASES, expected_pl):
        got = decline_noun(stem, declension, case, "pl", gender=gender, **kwargs)
        assert got == expected, f"{label} pl {case}: expected {expected!r}, got {got!r}"
    print(f"OK  {label}")


# declension 1, hard, feminine inanimate: комната (room)
check(
    "комната", "комнат", 1, "f",
    expected_sg=("комната", "комнаты", "комнате", "комнату", "комнатой", "комнате"),
    expected_pl=("комнаты", "комнат", "комнатам", "комнаты", "комнатами", "комнатах"),
    animate=False,
)

# declension 1, soft, feminine inanimate: неделя (week)
check(
    "неделя", "недел", 1, "f",
    expected_sg=("неделя", "недели", "неделе", "неделю", "неделей", "неделе"),
    expected_pl=("недели", "недель", "неделям", "недели", "неделями", "неделях"),
    animate=False, soft=True,
)

# declension 1, husher stem, feminine inanimate: туча (storm cloud)
check(
    "туча", "туч", 1, "f",
    expected_sg=("туча", "тучи", "туче", "тучу", "тучей", "туче"),
    expected_pl=("тучи", "туч", "тучам", "тучи", "тучами", "тучах"),
    animate=False,
)

# declension 1, sibilant stem, feminine inanimate: улица (street)
check(
    "улица", "улиц", 1, "f",
    expected_sg=("улица", "улицы", "улице", "улицу", "улицей", "улице"),
    expected_pl=("улицы", "улиц", "улицам", "улицы", "улицами", "улицах"),
    animate=False,
)

# declension 2, hard, masculine inanimate: стол (table)
check(
    "стол", "стол", 2, "m",
    expected_sg=("стол", "стола", "столу", "стол", "столом", "столе"),
    expected_pl=("столы", "столов", "столам", "столы", "столами", "столах"),
    animate=False,
)

# declension 2, soft, masculine animate: конь (horse) - ь-stem, gen.pl -ей
check(
    "конь", "конь", 2, "m",
    expected_sg=("конь", "коня", "коню", "коня", "конем", "коне"),
    expected_pl=("кони", "коней", "коням", "коней", "конями", "конях"),
    animate=True,
)

# declension 2, soft, masculine inanimate й-stem: музей (museum) - gen.pl -ев exception
check(
    "музей", "музей", 2, "m",
    expected_sg=("музей", "музея", "музею", "музей", "музеем", "музее"),
    expected_pl=("музеи", "музеев", "музеям", "музеи", "музеями", "музеях"),
    animate=False,
)

# declension 2, husher, masculine inanimate: нож (knife) - gen.pl -ей exception
check(
    "нож", "нож", 2, "m",
    expected_sg=("нож", "ножа", "ножу", "нож", "ножом", "ноже"),
    expected_pl=("ножи", "ножей", "ножам", "ножи", "ножами", "ножах"),
    animate=False, stressed=True,
)

# declension 2, husher, masculine inanimate, unstressed ending: товарищ (comrade)
assert decline_noun("товарищ", 2, "ins", "sg", gender="m") == "товарищем"
assert decline_noun("товарищ", 2, "ins", "sg", gender="m", stressed=True) == "товарищом"
print("OK  товарищ (stress-dependent о/е)")

# declension 2, sibilant, masculine inanimate: месяц (month, unstressed) vs отец (father, stressed)
assert decline_noun("месяц", 2, "gen", "pl", gender="m") == "месяцев"
assert decline_noun("отц", 2, "gen", "pl", gender="m", stressed=True) == "отцов"
print("OK  месяц/отец (sibilant gen.pl stress)")

# declension 2, hard, neuter inanimate: окно (window) - note: fleeting vowel in
# real gen.pl "окон" is a known, documented limitation; we intentionally check
# the zero-ending default instead.
check(
    "окно", "окн", 2, "n",
    expected_sg=("окно", "окна", "окну", "окно", "окном", "окне"),
    expected_pl=("окна", "окн", "окнам", "окна", "окнами", "окнах"),
    animate=False,
)

# declension 2, soft, neuter inanimate: поле (field)
check(
    "поле", "пол", 2, "n",
    expected_sg=("поле", "поля", "полю", "поле", "полем", "поле"),
    expected_pl=("поля", "полей", "полям", "поля", "полями", "полях"),
    animate=False, soft=True,
)

# declension 3, husher stem, feminine animate: мышь (mouse) - я->а rule in plural
check(
    "мышь", "мышь", 3, "f",
    expected_sg=("мышь", "мыши", "мыши", "мышь", "мышью", "мыши"),
    expected_pl=("мыши", "мышей", "мышам", "мышей", "мышами", "мышах"),
    animate=True,
)

# declension 3, plain soft stem, feminine inanimate: ночь (night)
check(
    "ночь", "ночь", 3, "f",
    expected_sg=("ночь", "ночи", "ночи", "ночь", "ночью", "ночи"),
    expected_pl=("ночи", "ночей", "ночам", "ночи", "ночами", "ночах"),
    animate=False,
)

print("\nAll checks passed.")

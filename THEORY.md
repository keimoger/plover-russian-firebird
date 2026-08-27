# Firebird theory design notes

Working design reference for the Firebird Russian steno theory. This is a
living document — update it as design decisions change. Where something
is implemented, the code is the source of truth for exact behavior; this
file explains the *why* and the *plan*.

## 1. Philosophy

Existing Russian steno options force a choice: type every inflected form
by hand in a static dictionary (huge, unmaintainable), or type bare word
roots with no grammar at all (Trillo). Firebird instead treats inflection
as a small rule system applied on demand:

1. One stroke for a word's root produces its **full dictionary form**
   (nominative singular for nouns, infinitive for verbs later) — a
   complete, correct word, not a fragment.
2. A small set of **modifier strokes**, shared across every word of a
   given part of speech, transform that word's case/number/etc. Nothing
   about a specific word's inflected forms is ever stored — only the
   rule that produces them.

This means the dictionary only ever holds one entry per root word. Every
other form is computed.

## 2. Hardware

22-key Stenograph/Stentura layout. Physical layout (see
`plover_russian_firebird/system.py` for the authoritative `KEYS` tuple):

```
left hand:    С (single key)  Т/П  В/К  М/Р
left thumb:   Н  Е
star:         *
right thumb:  О  А
right hand:   И/С  Т/Л  В/К  М/Р  и/н (last column, lowercase)
number bar:   #
```

Capital "И"/"Н" (thumb keys) and lowercase "и"/"н" (last right-hand
column) are genuinely different physical keys that happen to share a
base letter — confirmed against the Plover wiki's diagram of this
machine. Not a duplicate, not a typo.

`KEYMAPS` is filled in for the **Plover HID** protocol (merged into
Plover core; see
[dnaq/plover-machine-hid](https://github.com/dnaq/plover-machine-hid#the-keys)
for the canonical position names), for testing on a keyboard that
identifies as a PloverHID device. The mapping is purely positional —
both layouts are 22-key Stenotype-shaped boards (tall single key, three
split columns, thumb vowels, star, thumb vowels, split columns, number
bar) — not based on the English letters the HID position names reuse.
No keymap for a plain "Keyboard" (regular QWERTY passthrough) or for
real Stenograph/Stentura serial hardware yet.

## 3. Dictionary architecture

- **`dictionaries/roots.json`** — the only user-facing, user-editable
  dictionary. Maps a root stroke to its nominative-singular (or
  infinitive) text, exactly like any normal Plover dictionary. Edited
  through Plover's own Dictionary Editor — no special tooling. This is
  deliberately the *only* place word-specific data lives.
- **`dictionaries/endings.py`** — a native Plover "python dictionary"
  (`LONGEST_KEY = 4` + `lookup(key)`, a Plover core feature, no plugin
  registration needed), **implemented and tested, not just planned**.
  `key[:-1]` (joined with "/") is looked up as a root outline directly in
  `roots.json`; `key[-1]` is parsed as a grammar modifier (§4's
  `#`+letter+`*` convention, including the trailing `-н` override).
  `_infer_paradigm()` determines the root's declension number and gender
  from its own nominative-singular spelling (a level above
  `grammar/nouns.py:classify_stem`, which only handles the
  velar/husher/sibilant/soft spelling-rule axis, not declension/gender),
  then calls `decline_noun`. `LONGEST_KEY = 4` supports roots up to 3
  strokes long (the longest current root, "болото").
- **`grammar/nouns.py`** — the tested declension engine (`decline_noun`).
  Handles all 3 noun declensions × 6 cases × sg/pl, including the real
  spelling rules (ы blocked after г/к/х/ж/ш/ч/щ; unstressed о blocked
  after ж/ш/ч/щ/ц; я/ю blocked after ж/ш/ч/щ/ц) and the masculine
  genitive-plural lexical exceptions (husher stems → "-ей", й-stems →
  "-ев"). Verified against 13 known words in `tests/test_nouns.py`.

**Why not one JSON dictionary with every inflected form spelled out?**
Combinatorial explosion — 12 forms per noun × every root. **Why not
Plover's regex-based `ORTHOGRAPHY_RULES`?** They can only look at the
*spelling* of the previous word, and some spellings are genuinely
ambiguous (see gender override below) — the metadata table sidesteps
that by not needing to guess.

**Exceptions / wrong guesses:** resolved the standard Plover way. Since
dictionaries stack by priority, a normal JSON entry for a specific
`(root_stroke, modifier_stroke)` pair overrides the computed guess with
zero code changes.

## 4. Grammar modifier strokes

**A note on notation, used from here on throughout this file:** every
outline below is written in strict board order — the order keys actually
appear in the `KEYS` tuple: `#` first, then the left bank in its tuple
order, then `*`, then the right bank in its tuple order. A trailing `-`
marks a left/initial-bank key, a leading `-` marks a right/final-bank
key, shown explicitly wherever a letter exists on both sides (С, Т, В,
К, М, Р, Н) so it's never ambiguous which physical key is meant. `*` has
a **fixed physical position** between the two banks — in a combo that
mixes a left key and a right key, the star in written notation lands
literally between them, not at either end.

Convention: every modifier stroke includes `*`, paired with a consonant
that abbreviates the case (Cyrillic case-abbreviation letters: Р =
родительный/genitive, Т = творительный/instrumental, etc.). Which hand
the consonant is on marks singular vs. plural. `#` is the very first key
on the board (before even С-), so it's written first, not last:

```
# + Р- + *     →  "#Р*"   genitive singular
# + * + -Р     →  "#*Р"   genitive plural
# + Т- + *     →  "#Т*"   instrumental singular
# + * + -Т     →  "#*Т"   instrumental plural
```

The `#` (number bar, otherwise unused) is required: several case-mnemonic
consonants (Р, Т, and whichever end up meaning accusative/prepositional)
are also plain alphabet letters, and once fingerspelling assigns every
letter a `* + combo` chord (§5), a bare `{case-letter, *}` stroke would
be ambiguous with fingerspelling that letter. Since no fingerspelling
chord ever includes `#`, adding it here makes grammar modifiers
structurally impossible to confuse with fingerspelling, on top of never
colliding with real word strokes (which always carry a vowel and never
carry `#`).

Full case/number chord table: **not yet finalized** — only genitive and
instrumental have worked examples so far. TODO before the theory is
usable.

**Gender-override key:** spelling alone can't distinguish the gender of
ь-final nouns (masculine "гвоздь" vs. feminine "мышь" are spelled
identically at the point of inflection — this is memorized information
in Russian, not derivable). Default guess: feminine, declension 3
(larger/more regular ь-final class). Override: add `-н` (the lowercase
final-column key, sorted last in the right bank) to the modifier stroke
to force masculine, declension 2 soft. Example:

```
гвоздь, then "#Т*"   →  "гвоздью"    ✗ wrong (default feminine guess)
гвоздь, then "#Т*н"  →  "гвоздем"    ✓ correct (masculine override, -н added last)
```

## 5. Alphabet / fingerspelling chart

Every Cyrillic letter has its own **combo** (the key or keys that
represent it phonetically within a word outline). Fingerspelling a
letter standalone is always `* + that letter's combo` — following
Lapwing's convention of using star to mark "produce this literal
character," distinct from using the same combo as part of building a
real word.

This split matters because plain combos (no star) are needed for real,
extremely common one-letter Russian words (и, а, в, к, о, с are all real
prepositions/conjunctions) — those need the bare combo to stay available
for that word, so fingerspelling the same letter *must* look different
(hence the star). Every combo below is verified pairwise-unique, so
adding `*` to each produces 33 distinct fingerspelling chords with no
collisions — including Й, which used to be treated as identical to И for
word-building but now gets its own combo so it can be fingerspelled
independently.

**Design principle for the combos:** derive missing letters from
Russian's own phonological structure rather than assigning arbitrary
chords — voiced/voiceless consonant pairs, hard/soft vowel pairs, and
one affricate fusion account for most of the alphabet. A handful of
consonants with no anchor in either pairing (Ж, Ш, Ч, Щ, Х) get dedicated
same-side key combinations instead. No missing-letter combo itself uses
`*` — that's reserved for the fingerspelling marker and for the
distinct in-word use in §5's notes below (the -ый ending), which never
collides with fingerspelling because it always includes a consonant
alongside the star, never a bare single combo. Softening/separative ь
used to also live on `*`; that's been moved to the dedicated `-и` key
(see the Ь note above) so `*` has one job, not three.

**Known tradeoff:** Russian's word-initial consonant clusters are far
richer than English's (ст-, ск-, пр-, тр-, св- etc. are all common), so
unlike Lapwing's PW/TK/etc. (which work because English barely has those
clusters), no choice of companion keys is fully collision-free here.
Resolved the standard way: the rare colliding real word gets an explicit
dictionary entry, same as any other exception.

| Letter | Combo (explicit sides) | Written | Fingerspell | Notes |
|---|---|---|---|---|
| А | -А | А | *А | direct key, right bank only |
| Б | П- + В- | ПВ | ПВ* | voicing pair of П |
| В | В- | В | В* | direct key |
| Г | П- + К- | ПК | ПК* | voicing pair of К |
| Д | Т- + М- | ТМ | ТМ* | voicing pair of Т |
| Е | Е- | Е | Е* | direct key, left bank only |
| Ё | Е- + -О | ЕО | Е*О | "y-glide + o", not merged with Е |
| Ж | Т- + П- | ТП | ТП* | no anchor, dedicated combo |
| З | С- + Р- | СР | СР* | voicing pair of С |
| И | -И | И | *И | direct key |
| Й | Е- + -И | ЕИ | Е*И | own combo — no longer shares with И (see below) |
| К | К- | К | К* | direct key |
| Л | -Л | Л | *Л | direct key, right bank only |
| М | М- | М | М* | direct key |
| Н | Н- | Н | Н* | direct key |
| О | -О | О | *О | direct key, right bank only |
| П | П- | П | П* | direct key, left bank only |
| Р | Р- | Р | Р* | direct key |
| С | С- | С | С* | direct key |
| Т | Т- | Т | Т* | direct key |
| У | -О + -А | ОА | *ОА | hard partner of Ю |
| Ф | В- + М- | ВМ | ВМ* | voicing pair of В |
| Х | К- + Н- | КН | КН* | no anchor, dedicated combo |
| Ц | С- + Т- | СТ | СТ* | affricate fusion ("т+с" phonetically, but С- sorts before Т- on this board) |
| Ч | Р- + Н- | РН | РН* | no anchor, dedicated combo |
| Ш | М- + Р- | МР | МР* | no anchor, dedicated combo |
| Щ | П- + Н- | ПН | ПН* | no anchor, dedicated combo |
| Ъ | Т- + К- | ТК | ТК* | standalone fingerspelling only — see note below |
| Ы | -О + -И | ОИ | *ОИ | hard partner of И |
| Ь | -и | и | *и | the lowercase duplicate key, dedicated to ь directly — see note below |
| Э | Е- + -А | ЕА | Е*А | hard partner of Е |
| Ю | -О + -А + -И | ОАИ | *ОАИ | soft partner of У |
| Я | -А + -И | АИ | *АИ | soft partner of А |

For dual-bank consonants used as a bare "direct key" (В, К, М, Н, Р, С,
Т above), the left instance is the canonical choice unless a specific
rule says otherwise (e.g. grammar modifiers explicitly use the right
instance for plural, gender-override explicitly uses `-н`).

**Й's combo changed from "same as И" to its own `Е+И`.** In continuous
word-building the two are phonetically close enough that reusing И's
combo was harmless (the dictionary stores the correct spelling either
way), but fingerspelling needs to select one specific character
deliberately, so every letter — Й included — needs a combo no other
letter uses. `Е+И` reuses the one vowel-pair combination freed up when we
decided Ъ needed no in-word marker (see below).

**Ъ's combo (Т+К) is arbitrary**, chosen only to be unclaimed — there's
no phonological pairing to derive it from, since it isn't a sound in its
own right, and real word-building never needs it (see below). **Ь is
different: it's assigned directly to `-и`**, the lowercase duplicate key
from the physical layout (distinct from `-И`, the regular vowel, at a
different board position). This isn't arbitrary — ь isn't a sound
either, but unlike ъ it *is* needed constantly in real word-building
(softening, and occasionally the separative case below), so it earns a
real dedicated key rather than a fingerspelling-only afterthought. This
also replaces an earlier design that used `*` for softening — moved off
`*` once it became clear `-и` (freed up when the devoicing-override key
moved to `-н`; see the final-position note below) was sitting unused
and gave `*` a single, consistent job (grammar/endings) instead of
three.

**Final position (word-building, not fingerspelling):** Russian's own
final-devoicing rule does the work for Б/Г/Д/З/Ф — a plain final
consonant (-П/-К/-Т/-С/-В) already matches the actual pronunciation.
Spend the `-н` override key only on the minority of words where the true
*spelling* is voiced and matters for declension (е.g. "хлеб" needs to be
stored as "хлеб", not "хлеп", to correctly decline to "хлеба").

**Why `-н`, and not `-и` as originally used:** и is a vowel, so it can
always be misread as "the next syllable starts here" — appending it to
an already-final consonant risks colliding with a genuinely different
word that happens to have that consonant + и as its own next syllable
(found in practice: "газ" as -С+override collided in principle with
"гаси", a real word). A consonant override doesn't have that failure
mode — appending one to an already-final consonant reads structurally
as "one more consonant in the final cluster," a far rarer shape to
collide with. `-н` is reused here from the gender-override key, but
safely: that usage is on a separate modifier stroke, this one is
root-internal, so the two contexts never overlap in the same stroke.
This reduces the collision risk, it doesn't eliminate it — a genuine
survivor gets an explicit dictionary override, same as any other
exception in this theory.

Final chords for Ж/Ш/Ч/Щ/Х (right-bank only):

| Letter | Final combo |
|---|---|
| Ж | -Т + -Л |
| Ш | -М + -Р |
| Ч | -В + -Р |
| Щ | -Л + -К |
| Х | -К + -М |

These aren't a direct mirror of the initial chords — П (used in the
initial chords for Ж and Щ) has no right-bank counterpart at all, so
those two needed a fresh right-bank pair instead. Verified pairwise
distinct from each other, from the vowel compounds, and from final Ц
(-С + -Т).

**Ъ in real word-building needs no marker at all.** It doesn't create a
genuine minimal-pair collision in the vast majority of cases —
"обявление" and "подем" aren't words, so "объявление" and "подъём" can
just use the plain я / ё chords and the dictionary supplies the correct
spelling. The `*ТК` fingerspelling chord exists only so Ъ can be typed
as a standalone character (fingerspelling an unfamiliar word, spelling
an acronym, etc.) — it's not used in normal word outlines.

**Ь is different: it's typed directly, as `-и`, wherever it's actually
needed.** Ordinary softening (день, мышь, конь) presses `-и` alongside
the final consonant within the word's own stroke, in its actual board
position: день = Д(Т-+М-) + Е- + -н + `-и` → `ТМЕин` (Т-, М-, Е- all
left-bank, precede the star position; -н and -и, both right-bank,
follow — no star involved at all anymore). The *separative* case (ь
before an iotated vowel, only when it creates a real minimal pair — e.g.
"семья" vs. "семя," which really are different words) presses `-и`
alongside the vowel compound instead. Note семья can't fit in one
stroke: С- (pos 1) and М- (pos 6) don't sort next to Е- (pos 9) in the
order the word is actually pronounced, so — same as any other
multi-syllable word — it splits across two strokes, one per syllable:
семья = `СЕ` / `МАИи` (stroke 1 "се", stroke 2 "мья" = М- + Я-combo +
`-и`).

**The common "-ый" ending** (novый, старый — virtually every hard-stem
adjective) gets its own efficient chord rather than trying to compose
Ы+Й from scratch: consonant + `*` + И. Example: "новый" = `НО` / `В*И`
(stroke 1 "но" = Н- + -О, stroke 2 "вый" = В- + `*` + -И).

## 6. Known limitations (deliberately deferred)

- Fleeting vowels (окно → окон, отец → отца) are lexical, not derivable
  from spelling rules — not handled by `decline_noun`.
- Nouns in -ий/-ие/-ия (санаторий, здание, армия) take -ии instead of -е
  in dative/prepositional singular, and -ий instead of -ей in genitive
  plural — not handled yet.
- е/ё are usually treated as the same letter in running text (ё is
  rarely typed in practice), but the theory now gives Ё its own chord
  (Е+О) for when it's needed.
- Indeclinable nouns, suppletive plurals (человек/люди), and
  stem-extending nouns (мать/матери, время/времени) — not handled.
- `stressed` must be supplied by the caller in `decline_noun`; there's no
  stress dictionary yet.
- Adjectives and verbs: not designed yet. The case/number modifier
  convention (§4) should extend naturally to adjective agreement; verb
  conjugation (aspect, tense, person) needs its own design pass.
- Full case/number chord table: only genitive and instrumental have
  worked examples. Needs the remaining four cases (nominative is the
  bare root; dative, accusative, prepositional) assigned consonants and
  verified against real words.
- **Л has no left-bank key**, so any word whose onset cluster needs Л
  alongside another consonant (e.g. "бл-" in блюдо, блин, близко) can't
  fit that cluster into a single stroke the way "бр-", "ст-", etc. can.
  Surfaced while hand-building the starter root list (§8) — no fix
  designed yet; these words likely need a different syllable split or a
  dedicated workaround.
- Number mode is disabled: `NUMBER_KEY = None`, `NUMBERS = {}` (empty
  dict, deliberately *not* `None` — `plover/system/__init__.py`'s
  `_key_order()` calls `.get()` on `NUMBERS` unconditionally regardless
  of `NUMBER_KEY`, so it must always be a real dict; separately,
  `plover_stroke`'s validator rejects a *non-empty* `NUMBER_KEY` paired
  with an empty `NUMBERS`, and further rejects a `NUMBERS` mapping that
  doesn't cover all ten digits 0-9 exactly once — confirmed by testing
  `plover_stroke`/`plover.steno.Stroke.setup` directly rather than
  guessing). `#` itself still works fine as an ordinary key for the
  grammar modifiers in §4 regardless (that's just normal stroke
  formatting, unrelated to Plover's built-in digit-conversion feature);
  what's missing is a real 10-digit-per-key design, not yet started.

## 7. Source data and vocabulary extraction

`Russian_roots_UTF.txt` (project root, gitignored) is an Eclipse/Total
Eclipse RTF-CRE steno dictionary export (`{\*\cxs STENO}translation`
entries) from an unrelated theory on a different, larger machine layout.
Its outlines don't transfer to this layout and are not reused — only the
translation text was extracted as vocabulary source material.

That file is a *morpheme-briefing* dictionary: most entries are bare
root fragments meant to be extended by further strokes in the source
theory (e.g. "ровн", "изг", "осцилл" — not valid standalone Russian
words), mixed with some entries that already are complete words.
Extraction pipeline (not currently checked into the repo as a script,
run once): parse out the `{\*\cxs ...}` translation text, drop phrases
(contain a space or hyphen), drop the small number of Eclipse
formatting/boilerplate entries (`\cxfing`, `\cxstit`, `\cxa`, and the
`"=TAG"`-style court-reporting placeholders at the end of the file),
then run every remaining single-token candidate through `pymorphy3`
(`pip install pymorphy3 pymorphy3-dicts-ru`). Keep only tokens
`pymorphy3` recognizes (`is_known`), which reliably separates real word
forms from the source theory's fragments, and take `normal_form` as the
lemma — this is the "convert to infinitive/nominative form" step,
handled automatically rather than guessed.

Of 14,451 single-token candidates: 8,173 recognized, 6,278 rejected as
fragments. Recognized tokens broke down by part of speech as 4,490 noun
occurrences (3,745 unique lemmas), 1,876 verb forms, plus smaller counts
of adjectives/adverbs/etc. Only the noun lemmas were kept for now, since
`grammar/nouns.py` is the only part of speech with a working declension
engine — saved to
`plover_russian_firebird/dictionaries/vocabulary_nouns.json` as a plain
sorted list (not yet mapped to outlines).

## 8. Root dictionary — starter set

`dictionaries/roots.json` currently holds a small, **hand-crafted**
starter set (21 words) built directly from the vocabulary list, chosen
to exercise as much of §5's alphabet chart and §4's grammar modifiers as
possible in one pass: every derived initial consonant (Б,Г,Д,Ж,Щ,Х,Ц),
final-devoicing with the `-н` override (газ), softening via the
dedicated `-и` key (боль, щель, бровь, мышь, конь, царь), a husher
final consonant (мышь, using the newly-assigned final-Ш chord),
the gender-override case (царь — defaults to the wrong feminine guess
without it), and multi-syllable words split across strokes (база, вино,
болото, поле). All 21 outlines were generated and order-checked with a
script against the real `KEYS` positions, not by hand, and verified
pairwise-unique. `царь`, `боль`, `бровь`, and `щель` were additionally
checked against `decline_noun` and match real Russian inflected forms.

Turning the rest of `vocabulary_nouns.json` (3,745 words) into outlines
is a separate, larger task — the user chose to validate the approach
with this hand-built set first before deciding whether/how to automate
outline generation for the full list.

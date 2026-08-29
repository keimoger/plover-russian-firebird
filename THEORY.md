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
right hand:   И/С  Т/Л  В/К  М/Р  ь/н (last column)
number bar:   #
```

Capital "Н" (thumb key) and lowercase "н" (last right-hand column)
are genuinely different physical keys that happen to share a base
letter — confirmed against the Plover wiki's diagram of this machine.
Not a duplicate, not a typo. The other last-column key is dedicated
directly to "ь" (soft sign) — it has no capital counterpart anywhere
else on the board, since it isn't reused for any other letter.

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

- **`dictionaries/firebird-main.json`** — the only user-facing, user-editable
  word dictionary, exactly like any normal Plover dictionary. Named
  `firebird-main.json` (not `roots.json`, an earlier name) because it isn't
  citation forms only: most entries map a root outline to its
  nominative-singular/infinitive text, but common words also get
  additional entries for compressed (§13) or fully-inflected outlines
  when they're common enough to be worth it (говоришь, alongside
  говорить's own two outlines) — still just words in a normal
  dictionary, not a different mechanism, the same way говоришь and
  говорить sit side by side rather than in a separate file. A genuine
  brief (an *arbitrary*, non-resembling short outline, the way English
  `SKP` means "and" rather than compressing its own sounds) would
  still get its own file if one comes up — none exist yet. Edited
  through Plover's own Dictionary Editor — no special tooling.
- **`dictionaries/firebird-suffixes.json`** — a static utility dictionary,
  separate from `firebird-main.json` since its entries aren't words: the
  traditional/manual ending strokes (§9), each the fixed `П-К-Р-`
  prefix plus an ending's own letters, glued via `{^text}` — except
  the standalone `ь` entry, which never needed the prefix since a bare
  `-ь` was never a collision risk to begin with (§5's Ь note).
- **`dictionaries/firebird-prefixes.json`** (§11) — verbal aspect prefixes
  (с-, в-, по-, про-, ...), each a prefix-attach stroke (the mirror
  image of the suffix mechanism: glues the *next* word onto itself
  instead of gluing onto the previous one), marked with `*` on the
  preposition's own spelling.
- **`dictionaries/firebird-fingerspelling.json`** (§5) — all 33 Cyrillic letters,
  each `* + that letter's combo`, glued via `{&letter}` so consecutive
  fingerspelled letters concatenate without spaces.
**A computed grammar engine used to live here** — `dictionaries/endings.py`,
a Plover "python dictionary" that inferred a noun's declension/gender
from its own spelling and called a tested `grammar/nouns.py:decline_noun`
engine to produce case/number forms automatically. Removed by
deliberate choice, not because it stopped working: manual mode (§9)
already covered verbs, prefixes (§11), and — once added — nouns too,
and running two fundamentally different inflection mechanisms side by
side (one guessing from spelling, one fully manual) for no consistent
reason was judged not worth keeping. §9's manual ending-stroke system
now handles every part of speech uniformly; nothing is lost except the
automatic guessing itself, which was always the one part of this
theory with no real precedent in existing steno practice.

## 4. Notation conventions

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

This notation is used for every kind of stroke in this theory — plain
words, the manual ending/prefix strokes (§9/§11), fingerspelling
(§5) — not just one mechanism. `#` itself is currently unclaimed: the
computed system that used to need it (see §3) is gone, and the manual
system deliberately uses `П-К-Р-` instead (§9), for an unrelated
reason (avoiding a future conflict with Plover's number-bar
convention, still undesigned — §6). That leaves `#` free for whatever
that eventual number design turns out to need.

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
collisions — including Й, which used to be treated as identical to И
for word-building but now gets its own combo so it can be
fingerspelled independently.

**Implemented, not just planned:** `dictionaries/firebird-fingerspelling.json`
wires up all 33 chords below to `{&letter}` — Plover's glue syntax,
which concatenates consecutive fingerspelled letters without spaces
between them (the standard mechanism for spelling out a word
letter-by-letter, same as English theories use `{&P}{&L}{&O}...` for
this). Output is lowercase by default, matching every other stored
word in this theory; capitalization is a separate concern, not
fingerspelling's job. All 33 rendered outlines were computed against
Plover's actual stroke encoder (not hand-derived) and verified
collision-free against every other dictionary in the project.

**Every consonant fingerspells on the left bank, matching Lapwing's own
convention** (Lapwing fingerspells with the left-bank instance of a
letter whenever one exists, for one consistent hand position rather
than switching per letter). This was already true for every dual-bank
direct key (В,К,М,Н,Р,С,Т) and every combo-based letter (Б,Г,Д,Ж,З,Ф,
Х,Ц,Ч,Ш,Щ,Ъ — all built from left-bank keys already) without needing
any change. Л was the one holdout — its only key used to be `-Л`,
right-bank — resolved for free by §12's onset combo: fingerspelling Л
is now `Т-+Н-+*` (`ТН*`), left-bank like everything else, with no new
design needed since the combo already existed for word-building. Ь
stays right-bank regardless (`*ь`) — it's not a consonant, has no
other key at all, and nothing else to move it to.

**Capitalization during fingerspelling uses `-Т`, matching Lapwing's
own convention exactly** — checked directly against Lapwing's guide
([Chapter 17](https://lapwing.aerick.ca/Chapter-17.html)) rather than
assumed: Lapwing fingerspells a capital letter as `[letter]* + -P`, a
dedicated right-bank key added on top of the normal lowercase chord.
Checking `KEYMAPS`, that exact physical position (`-P` in Plover HID's
naming) is where `-Т` already sits in this layout — so `-Т` isn't an
arbitrary pick, it's the same physical key Lapwing uses, under this
board's own name for it. Every one of the 33 letters gets a capital
variant this way (`[combo] + * + -Т`), e.g. с → `С*`/{&с},
С → `С*Т`/{&С}; л → `ТН*`/{&л}, Л → `ТН*Т`/{&Л}. Safe for all 33: none
of their base combos use `-Т` (right-bank) themselves — only the
left-bank `Т-` appears in any combo (Д, Ж, Ц, Ъ, Т itself, and now Л's
onset) — so adding `-Т` never risks pressing the same key twice.
Verified against Plover's actual stroke encoder and checked
collision-free against all 33 lowercase entries and every other
dictionary: 66 total fingerspelling entries, all pairwise-unique.

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
used to also live on `*`; that's been moved to the dedicated `-ь` key
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
| Л | -Л (coda) / Т-+Н- (onset) | Л | ТН* | position-dependent — see §12; fingerspells via the onset combo, kept left-bank like every other consonant |
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
| Ь | -ь | ь | *ь | its own dedicated key — see note below |
| Э | Е- + -А | ЕА | Е*А | hard partner of Е |
| Ю | -О + -А + -И | ОАИ | *ОАИ | soft partner of У |
| Я | -А + -И | АИ | *АИ | soft partner of А |

For dual-bank consonants used as a bare "direct key" (В, К, М, Н, Р, С,
Т above), the left instance is the canonical choice unless a specific
rule says otherwise (e.g. the manual ending strokes, §9, explicitly
use the right instance for some endings).

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
different: it's assigned directly to its own key, `-ь`** — the last
right-hand column, distinct from `-И`, the regular vowel, at a
different board position. This isn't arbitrary — ь isn't a sound
either, but unlike ъ it *is* needed constantly in real word-building
(softening, and occasionally the separative case below), so it earns a
real dedicated key rather than a fingerspelling-only afterthought. This
also replaces an earlier design that used `*` for softening — moved off
`*` once it became clear that board position (freed up when the
devoicing-override key moved to `-н`; see the final-position note
below) was sitting unused and gave `*` a single, consistent job
(grammar/endings) instead of three. That same board position used to
be labeled `-и` (a leftover from when it doubled as a generic
"append-и" marker); it's now named `-ь` directly, since ь is the only
thing it's ever used for.

**Final position (word-building, not fingerspelling):** Russian's own
final-devoicing rule does the work for Г/Д/З — a plain final consonant
(-К/-Т/-С) already matches the actual pronunciation, and the dictionary
supplies the correctly-spelled voiced letter regardless of which
"sounds like" key produced it. Ж is handled the same way but through
its own final combo (below), since Ш has no direct key either. Б used
to be the one exception — no direct `-П` key existed at all, so
final-б words had no way to be spelled — fixed by the new final-П
combo below (`-С + -В`). Spend the `-н` override key only on the minority
of words where the true *spelling* is voiced and matters for
declension (е.g. "хлеб" needs to be stored as "хлеб", not "хлеп", to
correctly decline to "хлеба").

**Why `-н`, and not appending и as originally used:** и is a vowel, so
it can always be misread as "the next syllable starts here" —
appending it to an already-final consonant risks colliding with a
genuinely different word that happens to have that consonant + и as
its own next syllable (found in practice: "газ" as -С+override
collided in principle with "гаси", a real word). A consonant override
doesn't have that failure mode — appending one to an already-final
consonant reads structurally as "one more consonant in the final
cluster," a far rarer shape to collide with. `-н` gets reused again
elsewhere in this theory (е.g. as a distinguishing marker in the
present-tense `ете` ending, §10), but always safely: those usages are
on separate strokes from this root-internal one, so the contexts never
overlap within the same stroke. This reduces the collision risk, it
doesn't eliminate it — a genuine
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

**Final combo for П** (-С + -В): unlike Ж/Ш/Ч/Щ/Х, П *does* have a
direct key — but only on the left bank (`П-`), used for onset spelling
(бак, поле). Nothing stood in for it in final position at all until
now: б devoices to a п sound word-finally, and with no `-П` key,
final-б words (е.g. "хлеб") had no plain key to press. `-С + -В` fills
that gap, verified pairwise distinct from every combo above, the vowel
compounds, and final Ц.

**Ъ in real word-building needs no marker at all.** It doesn't create a
genuine minimal-pair collision in the vast majority of cases —
"обявление" and "подем" aren't words, so "объявление" and "подъём" can
just use the plain я / ё chords and the dictionary supplies the correct
spelling. The `*ТК` fingerspelling chord exists only so Ъ can be typed
as a standalone character (fingerspelling an unfamiliar word, spelling
an acronym, etc.) — it's not used in normal word outlines.

**Ь used to be typed directly wherever it was linguistically "needed,"
but live hardware testing found `-ь` physically awkward to fit into a
chord alongside other final consonants.** The fix follows the exact
same logic already used for Ъ just above: the dictionary stores the
correctly-spelled text regardless of which keys produced the outline,
so a dropped `-ь` costs nothing *unless* the bare consonant-stem left
behind collides with a different, real word. So the policy is:
**omit `-ь` by default; only press it when dropping it would create a
genuine collision.** Checked against the current root list (§8):
боль, бровь, мышь, щель, and день all drop it safely (бол, бров, мыш,
щел, and ден aren't words) — day = Д(Т-+М-) + Е- + -н → `ТМЕн`, no `-ь`
at all. царь and конь are the exceptions and must keep it: dropping ь
from царь gives "стар" (a real short-form adjective — "он стар"), and
from конь gives "кон" (a real word, the stake/round in a card game) —
`СТАРь`, `КОьн`.

**For collision cases, there's now a second way to reach the ь-final
word, alongside the direct one-stroke outline.** `dictionaries/firebird-suffixes.json`
maps bare `ь` to `{^ь}` — Plover's native "glue this onto the previous
word, no space" syntax (the same mechanism English theories use for a
separate `-S` plural stroke; §9 covers the fuller set of ending
strokes this belongs to). No `П-К-Р-` prefix needed here, unlike the
vowel endings: a bare `-ь` was never a collision risk (no real word is
just "ь"), so it's the one entry in the set that stays unprefixed.
Both firebird-main.json entries stay as before (`СТАРь` → царь, `КОьн` →
конь); what's new is that their collision partners are now real root
entries too (`СТАР` → стар, `КОн` → кон), so a plain, undecorated
stroke has somewhere to go instead of translating nothing.

This only *rescues* a collision pair — gives you a second path to the
ь-word — when the non-ь word's spelling is the ь-word's spelling minus
its final ь, letter for letter. конь qualifies: "конь" minus its last
letter is exactly "кон", so `КОн` then `ь` correctly glues
"кон" → "конь". царь doesn't: "царь" minus its last letter is "цар",
not "стар" — the outline `СТАР` only *looks* related to "царь" because
Ц happens to be spelled with the same two keys (С-+Т-) as literal с+т
(§5's Ц combo), a steno-level coincidence with no bearing on the
actual spelling. Gluing `ь` onto "стар" correctly gives "старь",
not "царь" — so for царь, `СТАРь` remains the only way to type it; the
two-stroke path just gives you "стар" and, for what it's worth,
"старь" too. The suffix stroke is still broadly useful beyond
collisions — any plain word can have `ь` glued onto it afterward —
it just doesn't universally solve every collision pair on its own.

The *separative* case (ь before an iotated vowel) is the one place `-ь`
is never optional, because it only ever gets used when it creates a
real minimal pair in the first place — e.g. "семья" vs. "семя," which
really are different words, so there's nothing to drop it against.
Note семья can't fit in one stroke: С- (pos 1) and М- (pos 6) don't
sort next to Е- (pos 9) in the order the word is actually pronounced,
so — same as any other multi-syllable word — it splits across two
strokes, one per syllable: семья = `СЕ` / `МАИь` (stroke 1 "се",
stroke 2 "мья" = М- + Я-combo + `-ь`).

**The common "-ый" ending** (novый, старый — virtually every hard-stem
adjective) gets its own efficient chord rather than trying to compose
Ы+Й from scratch: consonant + `*` + И. Example: "новый" = `НО` / `В*И`
(stroke 1 "но" = Н- + -О, stroke 2 "вый" = В- + `*` + -И).

## 6. Known limitations (deliberately deferred)

- Fleeting vowels (окно → окон, отец → отца) are lexical — the manual
  system (§9) doesn't derive them either; a word whose stem genuinely
  changes shape between forms would need its own additional root
  outline for that shape (§13-style), not something automatic.
- Nouns in -ий/-ие/-ия (санаторий, здание, армия) take -ии instead of -е
  in dative/prepositional singular, and -ий instead of -ей in genitive
  plural — no dedicated ending strokes for these yet.
- е/ё are usually treated as the same letter in running text (ё is
  rarely typed in practice), but the theory now gives Ё its own chord
  (Е+О) for when it's needed.
- Indeclinable nouns, suppletive plurals (человек/люди), and
  stem-extending nouns (мать/матери, время/времени) — not handled.
- Adjectives: not designed yet. The manual ending-stroke convention
  (§9) should extend naturally to adjective agreement, but the
  specific endings haven't been worked out.
- **Л has no left-bank key** — resolved for onset clusters, see §12.
  Plain л-initial syllables with no cluster (ла, ло, etc.) were never
  actually blocked; they just use the right-bank `-Л` plus the vowel,
  same as any other syllable ending in л (see "болото"'s second
  syllable, already built this way from the start).
- Number mode is disabled: `NUMBER_KEY = None`, `NUMBERS = {}` (empty
  dict, deliberately *not* `None` — `plover/system/__init__.py`'s
  `_key_order()` calls `.get()` on `NUMBERS` unconditionally regardless
  of `NUMBER_KEY`, so it must always be a real dict; separately,
  `plover_stroke`'s validator rejects a *non-empty* `NUMBER_KEY` paired
  with an empty `NUMBERS`, and further rejects a `NUMBERS` mapping that
  doesn't cover all ten digits 0-9 exactly once — confirmed by testing
  `plover_stroke`/`plover.steno.Stroke.setup` directly rather than
  guessing). `#` is currently completely unclaimed (§3, §4) — the
  computed system that used to need it is gone, and the manual system
  deliberately avoids it (§9) — so it's free for whatever a real
  10-digit-per-key design eventually needs; that design itself hasn't
  been started.

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
of adjectives/adverbs/etc. Only the noun lemmas were kept for now — at
the time, nouns were the only part of speech with any inflection
mechanism at all; verbs (§10/§11) and a general-purpose manual system
(§9) came later and apply just as well regardless of part of speech,
so this split is now more historical than a hard boundary — saved to
`plover_russian_firebird/dictionaries/vocabulary_nouns.json` as a plain
sorted list (not yet mapped to outlines).

## 8. Root dictionary — starter set

`dictionaries/firebird-main.json` currently holds a small, **hand-crafted**
starter set (23 words) built directly from the vocabulary list, chosen
to exercise as much of §5's alphabet chart as possible in one pass:
every derived initial consonant (Б,Г,Д,Ж,Щ,Х,Ц), final-devoicing with
the `-н` override (газ), softening (боль, щель, бровь, мышь, конь,
царь) — most of which turned out to drop the `-ь`
key entirely per the updated policy above, with конь and царь keeping
it as the two genuine-collision exceptions (and now also anchoring
кон and стар as real roots in their own right, exercising the §5
suffix-stroke rescue), a husher final consonant (мышь, using the
newly-assigned final-Ш chord), and multi-syllable words split across
strokes (база, вино, болото, поле). All outlines were generated and
order-checked with a script against the real `KEYS` positions, not by
hand, and verified pairwise-unique. `царь`, `боль`, `бровь`, and
`щель` were additionally checked against real Russian inflected forms
using the manual ending strokes (§9).

Turning the rest of `vocabulary_nouns.json` (3,745 words) into outlines
is a separate, larger task — the user chose to validate the approach
with this hand-built set first before deciding whether/how to automate
outline generation for the full list.

## 9. Manual ending mode (traditional ending strokes)

**This theory used to also have a computed system that guessed
declension, gender, and spelling rules from a stored nominative
form** (§3) — powerful, but it was still a guess (a documented gender
ambiguity needed an explicit override key), it hid the grammar behind
machinery, and running it alongside a fully manual system for other
parts of speech had no real justification once verbs (§10), prefixes
(§11), and eventually nouns too all needed the same manual approach
anyway. Removed. A native speaker who already knows Russian inflection
cold just types a root and spells out whatever ending they intend, the
traditional way — one JSON dictionary, no computation, full manual
control, for every part of speech uniformly.

**Mechanism:** `dictionaries/firebird-suffixes.json` gives each real noun ending
its own **ending stroke** — the fixed left-bank prefix `П-К-Р-`,
combined with that ending's own letters spelled the ordinary
word-building way (direct keys, board order), with `{^text}` — Plover's
"attach this to the previous word, no space" syntax — as the
translation. `{^text}` isn't just a display trick: confirmed directly
from Plover's source (`plover/meta/attach.py`) rather than assumed, it
already runs every attach through `orthography.add_suffix()`
automatically, which is what makes the rules below apply for free.

`П-К-Р-` was chosen the way Lapwing picks its own connecting stroke:
a fixed chord that's simply unclaimed for standalone use (no real
Russian word is spelled with a bare Ц-К-Р-shaped consonant cluster
and nothing else), so it's always safe as a prefix. The current set:

| Ending | Outline | Ending | Outline | Ending | Outline |
|---|---|---|---|---|---|
| а | `ПКРА` | ам | `ПКРАМ` | ах | `ПКРНА` |
| я | `ПКРАИ` | ям | `ПКРАИМ` | ях | `ПКРНАИ` |
| и | `ПКРИ` | ом | `ПКРОМ` | ей | `ПКРЕИ` |
| у | `ПКРОА` | ем | `ПКРЕМ` | ев | `ПКРЕВ` |
| ю | `ПКРОАИ` | ами | `ПКРАМь` | ов | `ПКРОВ` |
| е | `ПКРЕ` | ями | `ПКРАИМь` | ью | `ПКРОАИь` |
| ы | `ПКРОИ` | ь | `ь` *(no prefix — see below)* | | |

Example: стол + `ПКРА` (а) → "стола"; поле + `ПКРАИ` (я) → "поля" (see
the vowel-replacement rule below for why поле's trailing е doesn't
linger); конь's collision partner (§5) кон + `ь` → "конь". The
speaker picks whichever ending they intend; the system only guarantees
the *spelling* comes out right, not the grammar itself.

**ями and ами both use `-ь` as a marker, not as part of either
ending's actual spelling.** "ями" is я+м+и — а, и, м, и — the same и
twice, once inside я's own -А+-И combo and once again as the ending's
own trailing letter, which is physically impossible to press as one
stroke (a key can't fire twice in a single chord). `-ь` stands in for
that second, unpressable и. "ами" (а+м+и) would naively use the exact
same three keys as "ям" (я+м = а,и,м — steno strokes are unordered key
*sets*, so grouping doesn't matter), so rather than spell it out with
и and add a second, different disambiguator, it's simpler to just drop
the и entirely and mark it with `-ь` too: `ами` = а+м+ь. Neither
`ями`'s nor `ами`'s `-ь` is semantically part of the ending; both are
pure disambiguators, the same "arbitrary but unclaimed" precedent §5
already uses for Ъ's combo — the key difference between them is simply
whether и is spelled out (ями) or dropped (ами), which is enough on
its own to keep the two outlines distinct.

**Vowel-final, ь-final, and й-final roots need their trailing letter
*replaced*, not appended to.** `firebird-main.json` stores full nominative
forms, and several of them already end in a vowel, ь, or й (поле,
база, царь, музей) — gluing a new ending straight onto that would
double up ("поле" + "я" naively gives "полея"). A dedicated rule fixes
this generally, regardless of which vowel/ь/й precedes or which
vowel/ь-initial ending follows: `r"^(.+)[ьйаеёиоуыэюя] \^
([аеёиоуыэюяь].*)$"` → `r"\1\2"`. The trailing `ь` was added to the
*right*-hand class specifically because `-ью` (мышь's instrumental
singular) itself starts with ь — found by testing, not assumed: an
earlier version without it produced "мышьью" instead of "мышью".
Verified end-to-end (not just the regex in isolation) against every
relevant root in the starter set: стол+а→стола, поле+я→поля,
поле+ям→полям, полям+и→полями (no drop — "полям" ends in a consonant,
so this second glue just appends), база+ы→базы, царь+я→царя,
царь+ями→царями, мышь+и→мыши, мышь+ью→мышью, музей+я→музея,
музей+ев→музеев, кон+ь→конь. 37 checks total, all passing.

**Two more spelling rules are automated, on top of the vowel-replacement
one above** — both purely mechanical and never stress-dependent,
matching real Plover mechanics (`system.py`'s `ORTHOGRAPHY_RULES`, a
list of `(pattern, replacement)` string pairs Plover compiles and
matches against `word + " ^ " + suffix` — verified against Plover's
actual `orthography.py` and the English system's own rules, not
guessed):

- **ы → и after г/к/х/ж/ш/ч/щ** (the "7-letter rule"): `рук` +`ПКРОИ`
  (ы) → "руки", not "рукы". Always applies, never stress-dependent.
- **я/ю → а/у after ж/ш/ч/щ/ц** (the "5-letter rule"): `дач` + `ПКРАИ`
  (я) → "дача", not "дачя". Also never stress-dependent.

**Deliberately not automated: о → е after ж/ш/ч/щ/ц.** Unlike the two
rules above, this one genuinely depends on stress — "ножом" keeps о
(stressed) but "мужем" needs е (unstressed), and this system has no
stress information to decide with. Automating it with a default would
silently produce the wrong spelling in whichever direction wasn't
guessed. Left fully manual instead: the speaker presses the о or е
ending directly, whichever they know is correct — the entire point of
this mode is trusting that knowledge rather than guessing around it.

**Why not `#`:** `#` is Plover's conventional number-bar key, and
while `NUMBER_KEY` is currently `None` (§6 — number mode isn't designed
yet), §4's grammar modifiers already use `#`. Once a real digit layout
exists, any stroke combining `#` with letter-keys risks being
swallowed by Plover's built-in digit conversion instead of reaching
our dictionaries. `П-К-Р-` sidesteps that entirely, at the cost of
needing per-ending verification (above) rather than a single
structural guarantee — a deliberate, checked trade-off, not an
oversight.

Only these three rules (vowel-replacement, ы/и, я/ю) and this set of
endings are implemented so far; broader coverage (fleeting vowels, the
-ий/-ие/-ия exceptions from §6, adjective/verb endings) is future
work, same as for the computed system.

## 10. Verbs — past and present/future tense (manual mode only)

**Verbs were manual-only from the start, by deliberate choice.** The
computed system nouns used to have (§3, now removed entirely) relied
on inferring declension/gender from a stored spelling — already an
imperfect guess even there (a documented gender ambiguity needed an
override key). Verb conjugation-class inference would have been worse:
1st vs 2nd conjugation has more common exceptions (лежать *looks*
1st-conjugation by its -ать ending but is actually 2nd; хотеть is
irregular/mixed), so a computed verb system would have meant building
real exception machinery before it was trustworthy. Verbs use only the
§9-style manual ending-stroke mechanism: type the infinitive, then
glue the ending yourself — the same mechanism nouns now use too, since
the questions above about whether to keep two different systems side
by side resolved in favor of one manual approach for everything.

**Root text is the infinitive**, per §1's original plan ("infinitive
for verbs later") — `firebird-main.json` already documented this, unchanged.
Two test roots: `РНИ/ТАТь` → читать, `ПКО/ВО/РИТь` → говорить (one
each of the two regular conjugation classes, -ать and -ить).

**First slice: past tense only** (person/tense/mood, aspect pairs,
reflexive -ся/-сь, and participles/gerunds are all future work).
Chosen over present/future as the starting point specifically because
past tense has no conjugation-class split at all — masculine/
feminine/neuter/plural agreement is identical for every regular verb
regardless of type, unlike present/future's six person forms across
two different conjugation patterns the speaker would need to get
right themselves.

**Four ending strokes**, same `П-К-Р-` prefix and mechanism as §9:

| Ending | Outline | Example |
|---|---|---|
| -л (masc.) | `ПКРЛ` | читать → читал |
| -ла (fem.) | `ПКРАЛ` | читать → читала |
| -ло (neut.) | `ПКРОЛ` | читать → читало |
| -ли (pl.) | `ПКРИЛ` | читать → читали |

**The infinitive-strip rule** is the one genuinely new piece, and it's
not optional the way it might look — without it, gluing any of the
above onto a stored infinitive would double up the ending
("читать" + "л" → "читатьл"). New `ORTHOGRAPHY_RULES` entry:
`r"^(.+)ть \^ (л.*)$"` → `r"\1\2"` — when the previous word ends in
-ть and the glued suffix starts with л, drop the -ть first. Verified
against both test verbs and all four endings, plus a regression pass
confirming it doesn't interfere with any existing noun rule (their
patterns never overlap: this one requires a literal trailing "ть" and
a suffix starting with "л", neither of which any noun-ending rule
touches). 16 checks total, 0 failures.

**What past tense deliberately does not cover, and why:** infinitives
ending in **-ти** (нести → нёс) or **-чь** (мочь → мог) are genuinely
irregular — often suppletive stems, sometimes a dropped masculine
"-л" after a consonant-final stem, sometimes a consonant alternation
in the stem itself. No general rule captures these correctly; they'd
need explicit root-level overrides regardless of mechanism, same as
any other exception in this theory (Ъ's arbitrary combo, the gender
override, the ами/ями disambiguators — this project's standard way of
handling the minority case that a rule can't reach).

**Second slice: present/future tense**, covering both conjugation
classes for the verbs already on hand. Unlike past tense, this needed
a genuinely new stripping rule, not just more endings — the two
conjugations drop *different amounts* of the infinitive:

- **1st conjugation** (читать, делать — most infinitives): strip only
  `-ть`, keeping the thematic vowel — читать + ю → читаю.
- **2nd conjugation** (говорить — most `-ить` infinitives): strip the
  *whole* `-ить`, not just `-ть` — говорить + ю → говорю. Reusing the
  1st-conjugation rule here would wrongly leave the и in place
  ("говорию"), so this needed its own rule, tried first (more specific
  pattern), before the general one falls through to it.

Both new rules also had to be placed *before* the existing
vowel-replacement rule (§9): a `-ить` infinitive also ends in "ь", so
without ordering, that rule would fire first and only strip the
trailing ь, giving "читатю"-style wrong results instead of "читаю".

Six person/number endings per conjugation, same `П-К-Р-` mechanism,
sharing `ю`/`ем` with the noun-ending set where the spelling is
identical:

| Person | 1st conj. (читать) | Outline | 2nd conj. (говорить) | Outline |
|---|---|---|---|---|
| 1sg | читаю | `ПКРОАИ` (existing `ю`) | говорю | `ПКРОАИ` (same) |
| 2sg | читаешь | `ПКРЕ*Сь` | говоришь | `ПКР*ИСь` |
| 3sg | читает | `ПКРЕТ` | говорит | `ПКРИТ` |
| 1pl | читаем | `ПКРЕМ` (existing `ем`) | говорим | `ПКМРИ` |
| 2pl | читаете | `ПКРЕТн` | говорите | `ПКРЕИТ` |
| 3pl | читают | `ПКРОАИТ` | говорят | `ПКРАИТ` |

`ете` needed a distinguishing extra key (`-н`) for the same reason
`ями`/`ами` did in §9 — "ете" contains е twice (once at the start,
once at the end), which is physically impossible to press as one
stroke, so the second е is stood in for with an otherwise-unused key
rather than repeated. `ешь`/`ишь` use `-С` + `*` as a stand-in for the
"ш" sound rather than ш's full onset combo (`М-+Р-`) — a deliberate
simplification local to these two endings specifically, not a change
to ш's general alphabet entry (§5), which stays `МР`/`-М+-Р` for
actual word-building. The `*` was added after catching a real
collision: a bare `-С` stand-in would be indistinguishable from a
genuine `с` sound in some other ending that happens to need the same
shape (e.g. a reflexive `-ись`) — confirmed empirically, not just
reasoned about: `ишь` (starred) renders as `ПКР*ИСь`, while a plain,
unstarred `-ись` (genuine с, no ш involved) renders as `ПКР-ИСь` — a
star versus a literal hyphen, genuinely different strings. Same
technique as the aspect prefixes (§11): `*` distinguishes "this
letter's normal meaning" from "this key stands in for something else
here." Verified end-to-end against real conjugated
forms for both verbs, all 6 persons each, plus a full regression pass
confirming the two new rules don't interfere with past tense or any
noun ending (their patterns are mutually exclusive: past tense
requires a л-initial suffix, present/future requires a vowel-initial
one) — 29 checks total, 0 failures.

**Not yet covered:** conjugation-class exceptions (лежать *looks*
1st-conjugation by its `-ать` ending but is actually 2nd; брить/
стелить are 1st despite ending in `-ить`) and 1st-person-singular
consonant mutations (видеть→вижу, любить→люблю) — all need explicit
root-level overrides, same category as -ти/-чь infinitives above.
Imperative mood, aspect as a grammatical category (§11 only covers the
*prefix* mechanism, not aspect pairing itself), reflexive `-ся/-сь`,
and participles/gerunds are separate, larger design passes, still
deliberately deferred.

## 11. Verbal prefixes (aspect pairs)

**Aspect (perfective/imperfective) is often formed by prefixing an
imperfective verb** — делать/**с**делать, читать/**про**читать — a
lexical pair, not an inflection, and not something either the computed
or manual ending systems touch. `dictionaries/firebird-prefixes.json` adds a
third, independent mechanism: a **prefix-attach** stroke, the mirror
image of §9's suffix-attach — instead of gluing text onto the
*previous* word, it glues the *next* word onto itself.

**Mechanism, confirmed against Plover's actual source rather than
assumed:** a translation ending in `^` with no leading `^` (`{с^}`,
not `{^с}`) sets only `next_attach` on itself, leaving `prev_attach`
alone (`plover/meta/attach.py`). Critically, a following *plain*
translation — an ordinary root like "делать", with no special syntax
of its own — still inherits that `prev_attach` automatically, because
`_Action.new_state()` always carries `prev_attach=self.next_attach`
forward (`plover/formatting.py`). So `-С` (→ `{с^}`) then a plain
`делать` stroke glues to "сделать" with no further work — confirmed by
reading the actual formatter, not by guessing that it would.

**One consistent rule for every prefix, single-letter or not: `*` on
the word's normal spelling.** с (preposition) → `С` (the canonical
left `С-`, bare); с^ (prefix) → `*С` — the *right* `-С` plus `*`, not
the left one. по (preposition) → `ПО`; по^ (prefix) → `П*О`, `*`
rendered in its actual physical position between the banks (confirmed
empirically, not just written as a trailing symbol) rather than
appended after the letters.

**Why the single-letter case still needs the right-bank instance, even
with `*` involved:** fingerspelling с is *already* `С*` — that letter's
own combo (canonical left `С-`) plus `*` (§5). If с^ tried to reuse the
same left instance plus `*`, it would be the exact same stroke as
fingerspelling с — genuinely ambiguous, not just superficially similar.
Using the right `-С` instead keeps the same "spelling + `*`" pattern
uniform across every prefix while landing on a different stroke:
verified empirically that `['С-', '*']` renders as `"С*"` (fingerspelling,
already claimed) while `['-С', '*']` renders as `"*С"` (genuinely
different string, confirmed against `plover_stroke` directly — not
assumed from the left/right notation rules in §4). Multi-letter
prefixes never hit this problem in the first place, since
fingerspelling chords are always exactly *one* letter's own combo —
`по` isn't any single letter's combo, so `П*О` was never at risk of
collision regardless of which bank anything used.

**Mechanism, confirmed against Plover's actual source rather than
assumed:** a translation ending in `^` with no leading `^` (`{с^}`,
not `{^с}`) sets only `next_attach` on itself, leaving `prev_attach`
alone (`plover/meta/attach.py`). Critically, a following *plain*
translation — an ordinary root like "делать", with no special syntax
of its own — still inherits that `prev_attach` automatically, because
`_Action.new_state()` always carries `prev_attach=self.next_attach`
forward (`plover/formatting.py`). So `*С` (→ `{с^}`) then a plain
`делать` stroke glues to "сделать" with no further work.

**Current test set:** `С`→с / `*С`→с^, `В`→в / `*В`→в^, `ПО`→по /
`П*О`→по^, `ПРО`→про / `ПР*О`→про^, alongside `делать` and the
existing `читать`. All four prefix outlines verified pairwise-unique
against each other and against every existing root/suffix outline —
zero collisions. Extending to more prefixes (пере-, за-, вы-, до-,
от-, под-, etc.) follows the same rule directly; the only open case is
a single-letter prefix built from a letter with no left/right
dual-bank key at all (у-, a vowel spelled `-О+-А`, both right-bank) —
no solution designed yet, deferred until it's actually needed.

## 12. Multi-stroke word splitting, and Л's onset combo

**Syllable boundaries follow Lapwing's own splitting rule, not a
rule invented for this theory**: checked directly against Lapwing's
guide ([Chapter 15](https://lapwing.aerick.ca/Chapter-15.html)) rather
than assumed, since this theory has leaned on Lapwing as precedent
throughout (the suffix/prefix connecting-stroke technique, §9/§11).
Lapwing's rule: "split each remaining part by its syllables so that
every stroke after the first begins with a consonant" — a consonant
between two vowels attaches to the *following* syllable (maximal
onset), not the preceding one. An earlier version of this theory tried
the opposite (maximal coda: де-лать → дел-ать) reasoning that ANY one
consistent rule beats picking per-word — true, but Lapwing's own rule
already *is* that one consistent rule, and matching real precedent
beats inventing a new one. Reverted every multi-stroke root back to
maximal onset: делать (д-е-л-а-т-ь) → `ТМЕ/ТНАТь` (де-лать); читать →
`РНИ/ТАТь` (чи-тать); говорить → `ПКО/ВО/РИТь` (го-во-рить); вино
(в-и-н-о) → `ВИ/НО` (ви-но); база (б-а-з-а) → `ПВА/СРА` (ба-за);
болото (б-о-л-о-т-о) → `ПВО/ТНО/ТО` (бо-ло-то); чайка (ч-а-й-к-а, й
treated as a consonant-like glide, not a vowel) → `РНАИ/КА` (чай-ка);
щука (щ-у-к-а) → `ПНОА/КА` (щу-ка). Every stroke after the first now
genuinely starts with a consonant, matching Lapwing's rule exactly.

**Л gets a dedicated left-bank onset combo, `Т-+Н-`, used whenever л
starts a syllable — plain (ла, ле) or clustered (бл-, кл-, etc.) —
with `-Л` reserved purely for coda/final position.** This mirrors
standard English steno directly: checked against Lapwing's own
material rather than assumed, word-initial "L" there is `HR` (lay =
`HRAEU`, lure = `HRAOUR`) — a dedicated onset combo, not a direct key,
because standard English steno *also* has no left-bank "L" (it's
right-bank only, same gap as here). Giving Л the same treatment
replaces two separate mechanisms from an earlier pass — the right-bank
cross-bank workaround for plain л-words (rejected: it broke the
left=onset/right=coda principle even for plain words, not just
clusters) and eight independently-memorized arbitrary cluster chords
— with one rule applied everywhere, the same way `HR` covers all of L
for Lapwing regardless of what follows it.

**Verified systematically, not just for the one candidate that
worked:** checked `Т-Н-` (the only free 2-key combo drawn from keys
none of the eight relevant base consonants — б,в,г,к,п,ф,з,с — use in
their own combos, so it can never conflict with what it's clustering
with) against every existing letter, the full natural-cluster
inventory from the earlier (rejected) 8-chord attempt, and each of the
eight б/в/г/к/п/ф/з/с combinations. Seven of eight are fully clean;
one is a documented rare exception: пл- (`ТНП`) coincides with a
hypothetical жн- cluster (жнец, жнивьё) — genuinely rare words, so
this is treated as an acceptable minority collision (same category as
Ц/З's own combos coinciding with ст-/ст- and ср- clusters, already
accepted from the original alphabet design), not a blocker.

Applied concretely: "ло" in болото is now `ТНО` (was the cross-bank
`ОЛ`); "ле" in поле is now `ТНЕ`, entirely left-bank since е is also a
left-bank vowel (was `ЕЛ`); "лать" in делать is `ТНАТь` (т's own key
gets reused as the second, distinct т sound in "лать", not the one
inside the л-combo — different position in the same stroke, no
conflict); блин (a genuine бл- cluster) is `ТПВНИн` (б=`П-`+`В-`,
л-onset=`Т-`+`Н-`, и=`-И`, final н=`-н` — a *different* key from the
`Н-` used inside the л-combo, confirmed distinct in §2). `-Л` still
handles coda position unchanged: боль (`ПВОЛ`), щель (`ПНЕЛ`), стол
(`СТОЛ`) are untouched.

**One exception carries over unchanged: жаба (ж-а-б-а) stays
`ТПА/ПВА` (жа-ба)**, not folded into the maximal-onset reasoning
differently — pulling б into a stroke with ж would still require
pressing `П-` twice (ж=`Т-+П-`, б=`П-+В-`), a hardware impossibility
regardless of which splitting rule is in effect. Same category as the
пл-/жн- collision above: the rule applies everywhere it *can*, and
where it genuinely can't, that's an explicit, documented carve-out
rather than a silently inconsistent one. Extending this combo to
heavier clusters (е.g. близко, where з and к would also need to fit
alongside the бл- cluster in one stroke) is future work — see §6.

## 13. Compressed roots and briefs

**Multi-stroke roots can have more than one valid outline — the full
syllable-split version (§12) alongside a shorter, compressed one —
the same way Lapwing keeps both for English words.** These are
additions, not replacements: every existing root keeps its original
outline, and a compressed alternative gets added as a second
`firebird-main.json` entry mapping to the identical word text. Since Plover
dictionaries stack and orthography rules (§9/§10) operate on the
*resulting text* rather than which outline produced it, every ending
and prefix already built works identically on a compressed root with
zero additional changes — verified by construction, not by re-testing
each rule again.

**Adapted from Lapwing's own shortening techniques** (checked directly
against [Chapter 17](https://lapwing.aerick.ca/Chapter-17.html) rather
than invented from scratch — folding, dropping unstressed vowels,
inversions, left-hand compound clusters, arbitrary sound-dropping, and
shortened prefix strokes). Two map onto Russian well enough to start
with:

- **Dropping unstressed vowels** — arguably a *better* fit for Russian
  than English, given how strongly unstressed о/а/е reduce in real
  speech (акание/иканье). говорить is stressed on the last syllable
  (говор**и́**ть), so both **о**'s in го- and -во- are unstressed and
  droppable.
- **Folding** — squeezing a trailing consonant into an existing stroke
  via a dedicated key, rather than giving it a whole separate stroke.
  говорить's third syllable "рить" folds its onset р into the previous
  stroke, leaving only "-ить" needing its own.

**Worked example: говорить, 3 strokes → 2.** Original: `ПКО/ВО/РИТь`
(го-во-рить, one syllable per stroke). Compressed: `ПВКР/-ИТь` — drop
both unstressed о's (го, во → г, в), fold р forward into that same
stroke (`П-+К-+В-+Р-`, rendering as `ПВКР` — note В sorts *before* К
on this board, not after, confirmed against the real stroke encoder
rather than assumed), leaving just `-ить` (rendering as `-ИТь` *with*
a leading hyphen — a stroke with zero left-bank keys and none of them
in `IMPLICIT_HYPHEN_KEYS`, a case that never came up before since
every suffix stroke always has left-bank content from its `ПКР-`
prefix). Verified collision-free against every existing root; both
outlines now resolve to "говорить" in `firebird-main.json`.

**говоришь (fused root+ending in one stroke) is not actually a brief
— it's just a common word, still resembling its own sounds, so it
lives in `firebird-main.json` like any other word, not a separate file.**
`ПВКР*ИСь` fuses the compressed root (`ПВКР`, above) directly with the
`*ИСь`-shaped ending pattern (§10) into a single stroke — worth doing
because говоришь ("you say/speak") is common enough in conversation to
justify it without waiting for frequency data, but it's still a
compressed *spelling* of the word, not an arbitrary shorthand for it.
Verified against the real stroke encoder and collision-free.

**A genuine brief — Lapwing's "dropping other sounds arbitrarily" and
"shortened prefix strokes," the English `SKP`-for-"and" style — is
*arbitrary*: it doesn't resemble the word's own sounds at all, unlike
every compression technique above.** None exist in this theory yet.
When one does, it gets its own file (`dictionaries/briefs.json`),
separate from `firebird-main.json` for exactly the reason `firebird-main.json` holds
говоришь and not a true brief: one is still a spelling of the word,
the other deliberately isn't, and conflating them was a mistake this
theory already made once and corrected.

**Scaling any of this to more words still needs a frequency-ranked
word list**, and that part remains future work: `vocabulary_nouns.json`
(§7) is a plain alphabetical list extracted from a court-reporting
dictionary, with no frequency data at all, so it can't yet answer
"which 100 words are common enough to deserve this treatment."
говоришь was a judgment call, not the product of that ranking —
finding or building it is a prerequisite for doing this systematically
rather than one word at a time.

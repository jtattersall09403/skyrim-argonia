# Vocabulary for place records

## Bureaucratic words

Measured 2026-11-09 over every `summary` and note text in `places/*.json` and `regions/*.json` (2,868 texts), before
the batch edits:

| Word | Count | Word | Count |
|---|---|---|---|
| ledger(s) | 19 | clerk(s) | 21 |
| tally / tallies | 7 | licence, licensed | 20 |
| roll (noun: "toll roll") | 1 | record(s) as a noun | 15 |
| register | 1 | seal(s), stamp(s) | 10 |
| census | 2 | paperwork | 5 |
| tithe | 1 | count-book, record-book, tithe-roll, book-keeping, toll-book | 0 |

What UESP uses. The Lore extracts for Black Marsh, Kingdom of Black Marsh, An-Xileel, Argonian, Hist, Lilmothiit,
Kothringi, the nine cities, Murkmire, Shadowfen, Thornmarsh, Blackwood, Xanmeer, Nisswo, Naga, Archein, Shadowscale,
Umbriel and Deepmire (445,000 characters) contain **ledger 0, tally 0, register 0, tithe 0, clerk 0, tax 0, roll as a
noun 0**. **Census** appears once, and only for the Imperial "Census and Excise office", the Empire's own customs
office. A namespace search for `<word> "Black Marsh"` finds ledger only on Telvanni, Orc and Hammerfell pages; clerk
only in *The Argonian Account*, about an Imperial Commission clerk; tally and tally-stick nowhere. What the Black Marsh
pages do use is **toll** (6, and "held passers-by for tribute to cross" for the Tum-Taleel), **licensed foreigners**
(An-Xileel Lilmoth), **records** (only as "the most ancient records", the outside world's), and above all Argonian
terms: Hist (477), tribe (386), egg (146), sap (86), memory and memories (27), carving on the **grave-stake**
(*xul-vaat*, 18: "the deceased's story is carved upon their stake").

## The rule

Argonians keep their past in the Hist and on grave-stakes, not on paper; paper belongs to the Empire, and in 4E 201
to Gideon and the Archwardens' customs at the ports.

- **Kept, and where:**
  - **toll**, the normal word for what a crossing's owner takes (state §3).
  - **licence** / **licensed**, for foreigners in a city and for salvage and port rights (canon, Lilmoth).
  - **customs**, only at the recognised ports and the Warden forts.
  - **records** / **ledger**, **clerk**, **seal** and **census**: only for an Imperial ruin, Gideon's courthouse and
    council, or the Archwardens' customs house. At most one such word in a record, and never in a tribal place.
- **Cut** everywhere: tally, roll as a noun, register, tithe, paperwork, count-book, record-book, book-keeping.
- **Black Marsh replacements**, by what the sentence means:

| Instead of | Write |
|---|---|
| a ledger of debts, owed tolls | what is **owed**: "the crossing's owner remembers who has not paid"; a **debt** between families or tribes |
| a roll of names, the dead, members | the names **carved on the grave-stakes**; "the tree-minder knows every egg laid there" |
| a tally of eggs or hatchlings | the **egg-tender**'s count at the Hist; "hatched under the same Hist" |
| a register of who belongs | the **tribe**, the **Hist** a person was hatched under, being *saxhleel* of that tree |
| tithe to a temple or chief | a gift of **Hist-sap**, food or work at the Root Talk; tribute at a crossing (Tum-Taleel) |
| a manifest, bills, cargo papers | "the cargo it carried"; for an Imperial or Company ship, its **bills of lading** may stay |
| recorded history of a place | what the **root-herald** or **grave-singer** tells, or what the stakes say |
| an Archein estate's books | the **Archein** family's claim, its seal kept from Imperial days (one word, once) |

A record that needs to say that something is known or owed says who knows it or who is owed, a person or a tribe,
never a document.

## Documents as a theme

The owner's rule goes past wording: Black Marsh is not a bureaucratic place, and the player's play must not turn on
ledgers, papers and counts. Measured 2026-11-09, before the batch edits: notes whose text turns on a document, a
record, a map, a seal, a licence, a count or a survey (one regex over ledger, register, record, document, paper,
letter, logbook, map, chart, deed, bill, manifest, book, scroll, journal, account, census, count, survey, clerk,
seal, stamp, writ, charter, licence, list, note, written, archive), **207 of 2,586 notes**:

| Aspect | Hits | Aspect | Hits |
|---|---|---|---|
| hooks | **71 / 258** | economy | 16 / 282 |
| history | 32 / 282 | faith | 13 / 282 |
| people | 27 / 282 | overview | 12 / 282 |
| present | 24 / 282 | look | 10 / 282 |
| dangers | 2 / 282 | landscape, ecology, climate | 0 / 24 each |

The count over-reads a little (a "book" sold by the Agaceph, a "map" as a word), so it is the ceiling to work down
from, not the exact number of bad notes. Hooks are the worst: more than a quarter fetch, read or forge a paper.

**The concept rule.** Rework most of these into Argonian 4E 201 life. A document stays only where it is natural:
an outsider's papers (an Imperial or Company wreck's bills, a Dunmer slaver's log, a privateer's letter of marque,
Gideon's courthouse, a Warden customs house). Target: **no more than about one hook in ten** carries a document,
and none in a tribal place.

Replacement concept families for the batch editors:

1. **The Hist** — a tree's sickness or silence, sap to carry or steal, a hatchling's naming, the Root Talk.
2. **Eggs and hatching** — a stolen or lost clutch, an egg-tender's vigil, a hatching gone wrong.
3. **Kin and clan** — a feud, a debt between families, an exile, a marriage across tribes, a returning lost one.
4. **Memory in speech and song** — what the grave-singer or root-herald tells, a song with a place in it, a story
   that points somewhere.
5. **Carvings and the dead** — grave-stakes to read or re-stake, totems, the unstaked dead risen in the flood.
6. **River and swamp trade** — a toll quarrel, a raft that did not arrive, a crossing someone has seized.
7. **Raiding and danger** — Naga brigands, Sul-Xan raiders, a warband to drive off or join.
8. **Beasts** — a wamasu in the fishing pond, a leviathan, a hunt for hide or luminous organs.
9. **Ruins** — a xanmeer's working defences, an Ayleid hall's sick ground, a Kothringi house's chimes.
10. **Objects** — a blade, a mask, a chime, a jasper piece, a seed doll: a thing, not a paper about a thing.

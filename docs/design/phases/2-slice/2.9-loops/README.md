<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9 loop surveys

One checklist per loop of [2.9 § Loops](../2.9-magic.md#loops), written
by the lane that runs it before its first measure: one row per
measurement (the harness command, the number, its bar) with the capture
that goes beside it and the reader's checklist for that capture. The
re-measure runs the same file. Each row's elapsed time is recorded so the
planner can see a slow step.

## The slice set

Chosen at kickoff from Morrowind's spell list (UESP, authored by the
catalogue lane; the lane confirms each id against the dossier and
replaces a name here only when Morrowind has no such spell). One spell
per school, one per visual family, every cast style cast once. Ids, names and ranges are Morrowind's
(`packages/magic/src/types.ts` `SLICE_SPELL_IDS`; dossier `world/sources/lore/topics/magic-effects.md`).

| Slice spell (id) | School | Range | Cast style | Visual family | Why this one |
|---|---|---|---|---|---|
| Fireball (`fireball`) | Destruction | target | aimed | projectile + hit flash | the plain damage proof; fire resist separate |
| Frostbite (`frostbite`; frost damage, touch) | Destruction | touch | stream | stream | the one stream spell; held, drains per second |
| Hearth Heal (`hearth-heal`) | Restoration | self | self | self glow | the healing tiers of `magic.json` |
| Cure Common Disease (`cure-common-disease`) | Restoration | self | self | self glow | answers the bite |
| Shield (`shield`) | Alteration | self | ward | area ring (held) | the one ward: held while the key is down |
| Levitate (`levitate`) | Alteration | self | self | self glow | the movement mode |
| Light (`light`) | Illusion | target | aimed | light orb | the light family |
| Soul Trap (`soul-trap`; the Soultrap effect) | Mysticism | touch | stream | area ring on the target | fills the gem on death |
| Bound Dagger (`bound-dagger`) | Conjuration | self | self | summon flash | the bound item through equipment |
| dual: any of the above in both hands | | | dual | the family at dual scale | |

Powers: the birthsign powers named in `stats/data/birthsigns.json`
(Blood of the North, Mara's Gift, Lover's Kiss, Moonshadow, Tower Key,
Beggar's Nose, Star-Curse, Blessed Word, Blessed Touch) are authored
rows; only Mara's Gift is cast in the slice (the Ritual sign on the
sandbox mage).

The disease: `swamp fever` on the giant leech's bite (bog-dog if the
leech has no bite hook), staged as world/30 §26 states.

## Survey files

| Loop | File | Lane |
|---|---|---|
| the catalogue | catalogue.md | a1 |
| each slice spell, the disease, Soultrap and the bound dagger, powers | effects.md | a2 |
| the verb, the hands and belt | casting.md | b1 |
| levitation | levitation.md | b2 |
| the enemy caster, sellers and teacher | people.md | d |
| each visual family | families.md | c1 |
| each cast style | clips.md | c2 |
| each screen | screens.md | e |
| seams | seams.md | s |

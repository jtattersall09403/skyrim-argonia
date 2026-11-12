---
name: talk-write
description: Give every BM&V person in one settlement a name, a light backstory, a personality, true topics and written lines. Use per settlement, before its build.
---

# Talk for one settlement

Design: `docs/design/talk.md` (the tables, the topic catalogue). `talk_check` enforces each rule. `S` is the settlement id (`bmv.lilmoth`).

**Who is covered.** Everyone the player can walk up to in the settlement: the census's people, and every person a
quest places there. A quest's person gets their lines from the quest record (quest-write, Topics); this loop checks
that none is left without one (`plugin.sh inspect silent` reads 0) and that a census person who is also in a
quest's cast says nothing in their own topics that the quest's lines contradict at any stage.

## The rules

1. **Directions are routes, told the Morrowind way.** Every `talk.directions` fact is made by `talk_route` from
   the speaker's ref: legs (walk, follow the path, follow the shore, cross the bridge, along the boards, swim, climb)
   ending at real landmarks, each with its form key in `source`. The claim tells each leg by its way, its compass
   point, its landmark and side and a word for how far (`talk_route.BANDS`: "just" under 60 m and in sight, "a short
   way" under 200 m, "a fair way" under 600 m, "a long walk" under 2 km, "far" beyond), never a count; the measured
   legs stay in `source` for the check. A place in sight is "just" and a compass point. The writer retells the
   route in the person's voice; never adds a landmark. Any distance in another fact's claim reaches the writer as
   its band's words too.
2. **Address follows standing.** Topic replies are said to a stranger: neutral or cool by temperament. Two
   greetings a person, `talk.greet-stranger` and `talk.greet-friend` (Talk.cs gates them on GetRelationshipRank
   with the player, < 1 and >= 1, Skyrim's Hello way). At most two warm address terms in all of a person's lines,
   none to a stranger (lint B11). A `manner` never says the person calls strangers "friend".
3. **Facts are BM&V's.** A fact cites a ref (form key) in the loaded world, or is a lore line making no physical
   claim (ship, dock, wall, tree, ruin, beast, crop...) the world does not show or contradicts; where they
   disagree the world wins and the lore line is dropped. Places by the names the player sees (`world_edit`
   `name_place`: the Docks are Soulrest).
4. **Names** (`story/design/quests/35-cast.md` §54, `86-never-reuse-names.md`): the five forms by who carries them
   (Jel for the marsh-born, translated for city and outward-facing work, nickname for the notorious, chosen,
   foreign); at most a third of a settlement Verb-the-Noun; an image (water, reed, root, stone, shadow, sky,
   boat, blade, eye, hand) once a settlement; no canon or lore name unless BM&V's base carries it; nothing Nordic.
5. **Rumours are retold, never copied.** A rumour fact holds who, where and what is wanted as fields (giver, place,
   want), never a sentence. At most two people in a settlement carry one rumour; each says it from where they stand
   and what they would know of it, in their own words, and no sentence of it is shared. A rumour is gated to the
   stages in which the quest can start.
6. **No shared formula.** No opening or closing phrase is used by more than two people in a settlement (the friend
   greeting most of all); a trade or company is named in a self-description by two people at most.

## The loop

1. **Rows.** `python3 -m tools.argonia_world.db query "SELECT * FROM bmv_talker WHERE settlement='S' AND status IN
   ('silent','service')"`. Drop clean-up targets that are Nord, Thalmor, Imperial officials or undead (a kept
   talker leaves the clean-up list); mark the hostile-in-game ones hostile.
2. **Ref scan.** `python3 -m tools.argonia_world.talk_route cache` once (out/talk_route/); landmarks and refs near
   each speaker come from the same cache (`talk_route.World().refs`, each with `lm`). Place, danger, loot,
   harvest and someone facts: one row each, `source` the form key and position.
3. **Routes.** Write each directions fact with `source` naming `speaker <ref6>` and `target <key6>` (a map marker,
   a talker or a ref), then `python3 -m tools.argonia_world.talk_route facts --settlement S --write` (the
   settlement's own worldspace). Check a route by hand with `talk_route route --from REF --to KEY`. The legs it
   makes keep these rules, and `source` carries each measured leg (`legs: kind paces@degrees (why)`) for talk_check,
   which reads the told wording back against it (compass points, landmark order, distance words):
   - a leg under 50 paces joins its neighbour, unless it meets a swim or a bridge or the whole route is under 150;
   - a leg over 350 paces is cut at a landmark near its middle (the search widens along the leg and out from it);
     a long leg with no landmark at all names what it follows (along the shore, along the path, over open ground);
   - a first leg more than 90 degrees off the target is re-planned from the next-best start; when the world forces
     it, the leg says why (round the inlet, round the cliffs);
   - at most four legs: a longer route tells its first three landmarked legs, then "from there, ask again" with the
     target's bearing (an `ask` leg);
   - never the speaker's own place as a waypoint (the map marker nearest the speaker within one cell).
   A leg that breaks a rule without its reason fails talk_check. When a route changes, rewrite only the
   directions lines that tell it.
4. **Lore facts**: from `story/lore`, rule 3; cite a ref where the claim is physical.
5. **Talkers.** One author pass for the settlement (so opinions agree): `talker` rows (name by rule 4, trade,
   spot, two-to-three-sentence backstory citing lore, the seven personality columns) and `talker_topic` rows:
   `talk.self`, both greetings, three to five place or trade topics drawn from facts near the person's own spot;
   each fact has one holder in the settlement, the person whose work or story it belongs to. A fact's `claim` gives
   its parts (who, where, what, wants), never a finished sentence a writer would copy; a quest rumour (two people at most) is one fact each retells in their own words.
6. **One holder.** `python3 -m tools.argonia_world.echoes assign --settlement S` prints, and `--write` applies:
   a fact several people cite stays with one (`--owner FACT=REF`, else the first by ref) and each other person
   cites a pointer fact instead ("Ask <holder> about it", source `echo: owner <ref> holds <fact>`), so their reply
   names the holder and the subject and tells nothing more. A quest rumour named in
   `../dialogue-write/echoes.yaml` stays with every teller.
7. **Data check.** `python3 -m tools.argonia_world.talk_check --lines-only --settlement S`: facts and names 0.
8. **Briefs.** `python3 .claude/skills/dialogue-write/talk_brief.py brief --talker REF --out BRIEF.md` per person.
   Each brief ends with **Already said near you**: the settlement's other people (and the quest speakers of any
   quest stage there) on the topics this person answers, with the facts each holds.
9. **Lines.** `export ARGONIA_PRIVATE=/home/ubuntu/argonia-private` (the Morrowind corpus, for corpus-find; dotnet
   is ~/.dotnet, plugin.sh sets PATH). One `dialogue-writer` agent per person, in parallel (at most 20 at once), each given its brief and an output path
   (TSV `<topic>\t<text>`); each runs its own find step (dialogue-write section 3) and lint with `--race`. Then
   `talk_brief.py load LINES.tsv --talker REF` (it refuses a person with no finds).
10. **Echoes.** `python3 -m tools.argonia_world.echoes check --window S`: 0 clusters (no two people of the
    settlement share a fact, a seven-word run or a greeting's opening) and the shared-phrase check (`talk_check`
    repeats); reword the later person's line and reload.
11. **Reader.** One `reader` pass over all the settlement's lines (style guide, bans, personification B01 by name:
    no thing, place or institution doing a person's act, and neighbours who sound alike); fix and reload.
12. **Build.** `tools/ArgoniaPlugin/plugin.sh seed`, `plugin.sh check`, then `python3 -m
    tools.argonia_world.talk_check` (lines, facts, names, the ESP read-back) to 0 problems; set the talkers
    `built`; commit the story data (never `plugin/Argonia/`; the integrator re-seeds).

# Talk: every BM&V person has something to say

Owner, 2026-11-07: "I want to be able to talk to everyone", with a light backstory per person, their own topics,
and every fact in them real and true. This file is the design the talk pipeline runs from. Status: Lilmoth built
(Phase 3 block W-talk); the rest of BM&V is [Phase 4a](../phases/4a-talk-to-everyone.md).

## Why "E to talk" opens nothing (measured 2026-11-07)

`python3 -m tools.argonia_world.talk_census measure` reads the load order (Skyrim.esm to Valenwood.esp):

- Skyrim opens the dialogue menu only when a **top-level player topic** has an INFO whose conditions pass for the
  speaker. Of Skyrim.esm and Update.esm's 3,868 top-level player INFOs, **3,612 (93%) are gated to one speaker**
  (GetIsID or a quest alias), 205 to a job or role faction (JobMerchantFaction and the like), 51 to quest or
  follower state. **None is generic.** Bethesda's way is that every person who talks has lines of their own;
  vanilla's generic townsfolk only bark a Hello too.
- **BM&V ships no dialogue for its people:** Black Marsh.esm has 0 DIAL and 0 INFO; Black Marsh North.esp one
  branch; Valenwood.esp 3 INFOs. Its people use vanilla voice types (MaleArgonian 89 refs, MaleSoldier 69, ...), so
  they bark vanilla Hellos at most; **90 placed people have no voice type at all** and say nothing.
- So the fix is Bethesda's: lines per person. **Voice:** none recorded. Our lines are subtitles; Fuz Ro D'oh 2.6 is
  already in the stack (`mods/dependencies.json` row `fuz-ro-doh`) and holds a silent line on screen for its
  length. A talker with no voice type gets our `ARG_TalkSilentVoice` (a VTYP no vanilla line matches, so it gains
  no Skyrim bark; decision 0006).

## The records (block W-talk, `tools/ArgoniaPlugin/Talk.cs`)

One quest `ARG_Talk` (Start Game Enabled, priority 20) holds one top-level player topic per topic kind (DLBR +
DIAL, the prompt is the menu choice). Each talker's reply is one INFO under it, conditioned
**GetIsReference == the talker's placed ref** (BM&V bases are shared: `02A1EE` stands in 16 places), its lines
the INFO's responses. A no-voice talker's base gets an override with `ARG_TalkSilentVoice`. Built from the story
data by `plugin.sh seed`, allocated last so earlier form ids never move. (Adding talkers re-allocates the talk
INFOs' ids: harmless, as no save holds an INFO by id.)

## The data (story/data, through `tools/argonia_world/db.py`)

| Table | What | Made by |
|---|---|---|
| `bmv_talker` | the census: every enabled placed person, race, sex, class, factions, voice, settlement, cell, sub-location (interior name or nearest map marker), position, status (`silent`, `service`, `vanilla-lines`, `hostile`, `corpse`) | `talk_census build` (regenerated) |
| `talk_topic` | the catalogue below | by hand, once |
| `talk_fact` | one true thing, its topic, and `source`: the form key, position or lore line that proves it | per settlement, from the plugins and story/lore |
| `talker` | the light backstory: name used, trade, spot, backstory, lore cited | per person |
| `talker_topic` | a talker's topics and the facts each may state | per person |
| `talk_line` | the written replies | the dialogue writer, loaded by `talk_brief.py load` |

The brief is generated (`.claude/skills/dialogue-write/talk_brief.py brief --talker <ref> --out ...`); the
`dialogue-writer` agent writes from it alone (one context per person); `talk_brief.py load LINES.tsv --talker`
loads the lines; `plugin.sh seed` then `plugin.sh check` builds and reads back.

## The topic catalogue (Morrowind's, extended)

| Topic | Prompt | Scope | Source a fact must cite |
|---|---|---|---|
| `talk.self` | Yourself | personal | the talker row (backstory) |
| `talk.trade` | My trade | trade | census class and faction, the talker row |
| `talk.services` | Services | trade | a Job* faction, vendor or trainer data on the base |
| `talk.here` | This place | place | settlement cells, map markers, story/lore |
| `talk.directions` | Directions | place | map-marker positions: compass and metres from the speaker's spot |
| `talk.danger` | Dangers nearby | place | hostile placed actors, corpses, traps, by ref |
| `talk.rumours` | Latest rumours | place | a QUST that can start (its giver, its stage) or a placed thing worth finding |
| `talk.loot` | Anything worth finding | place | CONT refs, treasure corpses, books (`bmv_book`) |
| `talk.harvest` | Plants and ingredients | place | flora (FLOR/TREE with an ingredient) and loose INGR refs, ingredient barrels |
| `talk.someone` | Someone in particular | place | `bmv_talker` rows of the settlement |
| `talk.advice` | Little advice | trade | a mechanic true in the loaded game |
| `talk.secret` | Little secret | personal | a hidden ref, locked container or out-of-the-way spot |
| `talk.lore` | Black Marsh | place | story/lore (decision 0032) |

Proposed next, same rule: **Where to sleep** (beds and inns by ref), **Who buys what** (vendor factions' buy lists),
**Trainers** (trainer data), **Getting across the water** (boats and doors by ref), **The weather and the marsh**
(region weather records). Quest rumours wait for Phase 4's quests: a rumour names only a quest that can start.

**Assignment.** Every talker has `talk.self`. Place topics (directions, harvest, loot, danger, rumours, someone,
here, lore) are drawn from the settlement's facts; each talker gets three to five, the facts measured from **their
own spot** (directions and distances differ per person), so neighbours overlap but never repeat word for word.
Trade topics follow class and faction: a vendor gets services, a thief loot and secrets, a mage lore, a child only
self, someone and harvest. Hostile and corpse rows get none.

**Backstory format.** Two to three sentences: who they are in this place, what they do there, where exactly they
stand and why, grounded in the census (race, class, faction, spot) and citing a story/lore line (decision 0032).
No Nordic element (0006); nothing levelled (0035). The backstory may invent a person's motive, never a fact about
the world: anything the player could check is a `talk_fact` with a source.

## Truth rules

- A fact is written only from a record in the load order (form key and position) or a lore line; the source is
  kept in `talk_fact.source` and the writer states no other fact (the dialogue-write skill's rule).
- Directions: compass and metres from the speaker's position to a map marker (70 units a metre); the writer may
  say "a short walk" but keeps the order and the bearing.
- A fact that our own plugin changes (Lilmoth's five Naga, disabled by ARG_BlockTest and later `we.clean.lilmoth`)
  is not stated until the change is permanent.

## Cost (measured 2026-11-07)

One dialogue-writer run (Sonnet, high effort) with its corpus-find children: about 36,000 tokens, under two
minutes, 4 to 5 topics. At list price that is about $0.40 a person; the facts for a settlement (a scripted scan
plus an agent's backstories) about $4 a settlement. All 603 talkable people (553 silent, 50 service) in 45 groups:
about $240 + $180 ≈ **$420, about 22% of a week's allowance**, spread over the phase. Build: `plugin.sh seed` and
`check` take under 3 minutes for the whole set.

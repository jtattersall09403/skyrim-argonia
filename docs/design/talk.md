# Talk: every BM&V person has something to say

Owner, 2026-11-07: "I want to be able to talk to everyone", with a light backstory per person, their own topics,
and every fact in them real and true. This file is the design the talk pipeline runs from. Status: Lilmoth's 30 built
(Phase 3 block W-talk; personality, names and the bookseller's stock after the owner's walk of 2026-11-07); the rest of BM&V is [Phase 4a](../phases/4a-talk-to-everyone.md).

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
| `talker` | the light backstory and personality: the name the player sees (`known_as`), trade, spot, backstory, lore cited; temperament, manner, wants, grudge, notices, opinions, secret | per settlement, one author pass over all its people |
| `talker_topic` | a talker's topics and the facts each may state | per person |
| `talk_line` | the written replies | the dialogue writer, loaded by `talk_brief.py load` |

The brief is generated (`.claude/skills/dialogue-write/talk_brief.py brief --talker <ref> --out ...`); the
`dialogue-writer` agent writes from it alone (one context per person); `talk_brief.py load LINES.tsv --talker`
loads the lines; `plugin.sh seed` then `plugin.sh check` builds, and `python3 -m tools.argonia_world.talk_check`
reads the ESP back: each talker's topics gated to their ref, each renamed ref placing its own base with the name,
each restocked vendor's chest.

## Personality (owner walk 2026-11-07)

The first twelve had a backstory and their trade only, and every one was given the same directions, the same leeks
and the same three dead Dunmer: the owner found them "all much the same". So a talker row also carries seven short
personality columns, and the brief passes them to the writer under **Personality**, with the instruction that every
reply carries them and that two people given one topic must not sound alike:

| Column | What it holds | Example (Lilmoth) |
|---|---|---|
| `temperament` | how the person is | suspicious of anyone off a boat |
| `manner` | how they talk: a verbal habit, sentence length, what they call a stranger (within the race's voice card) | short answers, ends on a question |
| `wants` | what they want now | a berth on a lighter |
| `grudge` | whom or what they resent, and why | the stall-keeper who undersells her |
| `notices` | what their trade makes them see in a stranger or the place | boots: who walked the marsh, who came by boat |
| `opinions` | of two or three named neighbours (by `known_as`) and of a place | |
| `secret` | a small private thing, said only if a topic draws it out | |

None of it is a world fact: anything the player could check is a `talk_fact`. **Local knowledge differs per
person:** each person's facts are what is near their own spot and what their trade would know (the fisher knows
the slaughterfish, the soldier the dead walking by the walls, the trader her stock); neighbours may share a fact
but say it from their own position, nobody knows every fact, and each has at least one fact no one else has. A
settlement's people and facts are written in **one author pass** (one agent with the census rows, a ref scan of
the area and the lore), so opinions of each other agree; then one writer per person, as before.

## Names and bases

A placed ref's base is shared, so a name needs a base of its own. A talker whose `known_as` differs from the base's
name gets `ARG_Talker_<ref>` (Talk.cs): templated on the old base with W-npc's look flags (Traits, Factions, Spell
List, AI Data, AI Packages, Model/Animation, Inventory, Script, Def Pack List, Attack Data, Keywords), so face,
race, voice, outfit and behaviour stay BM&V's. **Use Traits carries the face:** the engine draws a templated NPC
with its template's FaceGen, as `ARG_BT_Keeper` (templated on `00FF4D`) showed on the dock in the owner's walk.
**Use Base Data is off**, so the name is ours; **Use Stats is off**, so the level is the old base's fixed level, or 5
where the old base levels with the player (decision 0035). The placed ref is overridden (in its cell, or the
worldspace's persistent cell for a persistent ref) to place the new base. Names are Argonian (Jel or translated),
the race's own for others, unique, no Nordic element (decision 0006).

## A trader's stock

A vendor's goods are their vendor faction's chest. BM&V's traders mostly use vanilla's shared factions (Looks-At-Books
had `WEServiceMiscMerchant`, whose chest's levelled lists stock any misc merchant in Skyrim). A trader whose stock does
not fit them gets a vendor faction of their own (a copy of the old one: buy list, hours) and a chest with a fixed
stock that fits who they are, vanilla or BM&V items only, nothing levelled (decision 0035); their base takes the old
factions with the vendor faction swapped. Her `talk.services` facts list the same stock.

## The topic catalogue (Morrowind's, extended)

| Topic | Prompt | Scope | Source a fact must cite |
|---|---|---|---|
| `talk.self` | Yourself | personal | the talker row (backstory) |
| `talk.trade` | My trade | trade | census class and faction, the talker row |
| `talk.services` | Services | trade | a Job* faction, vendor or trainer data on the base |
| `talk.here` | This place | place | settlement cells, map markers, story/lore |
| `talk.directions` | Directions | place | a `talk_route` route from the speaker's ref, every waypoint a ref |
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
own spot** (directions and distances differ per person), so neighbours overlap but never repeat word for word. The
mix varies too: not everyone gives directions or knows the plants, and each fact has one holder in the settlement;
anyone else who would know it (a corpse, a wreck, a piece of lore) points to the holder (`echoes assign`), save a quest
rumour, which two or three tell in their own words.
Trade topics follow class and faction: a vendor gets services, a thief loot and secrets, a mage lore, a child only
self, someone and harvest. Hostile and corpse rows get none.

**Backstory format.** Two to three sentences: who they are in this place, what they do there, where exactly they
stand and why, grounded in the census (race, class, faction, spot) and citing a story/lore line (decision 0032).
No Nordic element (0006); nothing levelled (0035). The backstory may invent a person's motive, never a fact about
the world: anything the player could check is a `talk_fact` with a source.

## Truth rules

- A fact is written only from a record in the load order (form key and position) or a lore line; the source is
  kept in `talk_fact.source` and the writer states no other fact (the dialogue-write skill's rule).
- Recipe v2 (owner walk 3, 2026-11-08): directions are `talk_route` routes with landmarks, address follows
  standing (two greetings gated on GetRelationshipRank), a lore line never makes a physical claim the world does
  not show, names follow §54. The rules and the loop are the skill `.claude/skills/talk-write`; `talk_check`
  enforces them.
- A fact that our own plugin changes (Lilmoth's five Naga, disabled by ARG_BlockTest and later `we.clean.lilmoth`)
  is not stated until the change is permanent.

## Cost (measured on Lilmoth's 30, 2026-11-08)

The author pass (one Opus agent: census rows, ref scan, lore, 30 people's rows and 134 facts): about 160,000
tokens, nine minutes. Thirty Sonnet writers without corpus-find children: 25,000 to 30,000 tokens each, under a
minute each, in parallel (about 830,000 in all). One reader pass over the 166 lines: 57,000. About $0.45 a person
all in. The other 573 talkable people: about **$260, about 14% of a week's allowance**, spread over Phase 4a. Build:
`plugin.sh seed` and `check` under 3 minutes each.

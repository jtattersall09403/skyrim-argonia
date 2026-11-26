# A more Argonian magic: the decision

Written on 26 November 2026 to answer your request in issue #104. It is an options paper: the problem, why it matters,
where we stand, four options from "do nothing" to "do most", and a recommendation. The decision is yours.

The evidence is in three research notes beside this page: [stack-inventory.md](stack-inventory.md) (every spell the
game has today and what can be reused), [lore-of-marsh-magic.md](lore-of-marsh-magic.md) (what the lore says, and what
each of our 18 cultures would have developed) and [how-magic-mods-are-built.md](how-magic-mods-are-built.md) (how
spell mods are made and what each technique costs).

## 1. The decision in five lines

1. **You are choosing** how far to go in making magic feel like Black Marsh and not like Skyrim: nothing, words and
   sellers only, a small native layer on top, or a full marsh spell list.
2. **I recommend "Sap and Song"** (the "do more" option): the renaming and the sellers of the minimum option, plus
   about ten Hist gifts that sit in the button Skyrim used for shouts, plus about twenty native spells made only from
   records the game already holds.
3. **Cost:** no fees in any option. No new visual effects in any option. The cost is agent time, which I can only
   rank: small, medium, large (section 6).
4. **The schools stay Skyrim's five** in every option, as you proposed. The lore supports that. What changes is which
   spells are native, which are foreign, who teaches them and what they are called.
5. **What you would see first:** three things to try in game before the rest is built: one renamed spell bought from a
   marsh seller, one Hist gift, and one recoloured effect.

**Words used below.** A record: one entry in the game's data (a spell, an effect, a book). Record-only: a change made
by editing records, with no script and no new art file. A tome: the book that teaches a spell. Magic Expanded: the mod
in our list that adds 139 Morrowind-style spells. A power: a spell-like ability used with the shout button, usually
once a day (the Argonian "Histskin" is one). Hist: the great thinking trees of Black Marsh. Sap: what a Hist bleeds.
A tree-minder: the Argonian who tends a village's Hist. The quest form: our one way of writing quests as data, which
can already teach the player a spell or power under a name of ours. King of the Murkmire, HTBM and the Mihail
creature mods: mods we hold for the new world's creatures, which also contain finished spells.

## 2. The problem

Magic in our game is Skyrim's magic with Morrowind's added. The player has 258 spells that a tome teaches: 91 from
Skyrim, 27 from its add-ons and 139 from Magic Expanded, plus Levitate. None of them is from Black Marsh. They are
named and described for Nords, Imperials and Dunmer, sold (in Skyrim) by court wizards and a college, and they look
the same in a mangrove as on a glacier. Skyrim gave its own province a magic of its own, the shouts. We removed the
shouts (decision 0012) and put nothing in their place.

Three things are also simply broken today, whatever you decide:

- **Nobody in our world sells a spell.** All ten kinds of trader in Black Marsh & Valenwood stock smith's or
  apothecary's goods, and our own one trader sells books but no tomes. The player has the two starting spells and a
  test kit that is due to be removed.
- **The Argonian power, Histskin, probably does nothing.** It speeds up natural healing, and our soulslike rule turns
  natural healing off. This is read from the records, not yet tried in game.
- **Mark and Recall do not know our world.** Their list of places where they may be used has to be extended to it.

## 3. Why it matters

- **It is the cheapest large gain in feel still open to us.** Places, people, quests and music are being made
  Argonian at real cost. Magic is on screen every minute a mage plays, and most of the change is words and records.
- **The lore is unusually clear, and it is not Skyrim's.** Across five games Argonians are good at the same things:
  Illusion, Mysticism (souls, memory, detection), Alchemy, healing and water. Never Destruction or Conjuration. Hist
  magic is said to work "by different rules": it is given by the tree and carried in the body, not studied from books.
  Argonians have no words for Daedra. Fire is the province's scar (the whole marsh burned in the First Era).
  Robed college mages do not exist within 400 miles of Lilmoth.
- **Our stories already assume it.** The Sisei-Xul line (the healers, makers and grave-singers) calls itself "the
  province's one native order of magic" and teaches a spell in most quests. The main quest turns on Hist sap and
  visions. House Cardruhn is a house of foreign necromancers. A world where magic has a native side and a foreign
  side gives those stories their ground.
- **It has to earn its place in play.** Every spell below is there because it does a job in our game: getting through
  a soulslike fight, reaching something under water, surviving the marsh's diseases and poisons, or passing a
  person without killing them.

## 4. The shape all the options share

**Five schools, two traditions.** The schools and their skill trees stay exactly as Skyrim has them. Within each
school a spell is either *given* (native: from the Hist, the tribe, the water) or *learned* (foreign: bought as a tome
from an Imperial, Dunmer or pirate hand). The same spell list serves both; the difference is name, look, seller and
place.

| School | The marsh's own (given) | Foreign (learned) | What it does for the player |
|---|---|---|---|
| Alteration | water (breathing, swimming, walking on it), clay and stone skin, shedding and slowing | Mark and Recall, telekinesis, time spells, the fire and frost shields | reaching wrecks, drowned ruins and the drowned Hist; armour for a caster |
| Illusion | stillness, hush, false lights, dream-sight (the Agaceph are the province's illusionists) | Fury, Frenzy, Command | the quiet way past a guard or a beast; theft; scouting |
| Restoration | sap healing, curing disease and poison, laying the dead (the grave-singers) | Divine healing, wards, Sun Fire | staying alive with no natural healing; the marsh's sicknesses; undead in ruins |
| Destruction | poison, spores, acid, lightning (the wamasu, the marsh's lightning lizard) | fire and frost | damage that fits the place; fire is sold only by foreigners and is feared |
| Conjuration | calling what the marsh already holds: a swarm, a wisp, a root guardian | atronachs, Daedra, raising the dead, soul trap | an ally in a hard fight; necromancy stays a foreign crime, which is what House Cardruhn's line needs |

**Balance.** No spell is made stronger than Skyrim's own spell at the same level; a native spell is a Skyrim or Magic
Expanded spell's numbers under another name and colour, so the five levels (Novice to Master) keep Skyrim's costs.
Each school gets one native line with a spell at each level, so a player can stay native from start to end. Sellers
carry a short sheet of 12 to 20 spells (Morrowind's median is 15), never the whole catalogue, which also hides Magic
Expanded's padding (nine Command spells, seventeen Weakness spells) without deleting anything. Nothing is levelled
against the player.

**Deliverability.** Nothing below goes past the scripting of the spells we already hold. Of Magic Expanded's 145
spells, 84 use only Skyrim's stock effect types and no script; every new spell proposed is of that kind. Colour
changes are made in the effect's record where the colour is stored there (108 of the game's effect looks are like
that); the others, whose colour is in a picture file, are left alone. Spells and powers reach the player by seller,
by tome in the world, or by the quest form's existing "teach a spell" step.

**Lore calls I have made, for you to overrule if you wish.** The player of any race can be given Hist gifts once a
tribe trusts them (the lore lets outsiders speak with a Hist at Hissmir). Fire and frost stay in the game as foreign
magic. Atronachs, raising the dead and soul trap stay too, sold only by foreigners and treated by Argonians as
abominations. Spell names are plain English, as Skyrim and the online game name Argonian abilities ("Histskin");
Argonian words are kept for people, offices and places.

## 5. The options

### Option 0. "As shipped" (do nothing)

**The point:** spend nothing; accept that magic is the one part of the game that is still plain Skyrim.

**In game:** a mage's play is Skyrim's and Morrowind's spells under their own names. But as things stand there is no
one to buy them from, so even this option needs the three repairs of section 2 (sellers of some kind, Histskin, Mark
and Recall). Small effort; sure.

**Why you might choose it:** magic is not what the game is sold on, and the soulslike fighting carries most players.

### Option 1. "Marsh Names, Marsh Hands" (do minimum)

**The point:** change no mechanics at all. Change the words and the hands the magic passes through, so the world
itself tells the player where magic comes from. This is how Morrowind made magic feel local: by who sold what, where.

**What is built:**

- **Sellers with a character.** A tree-minder or sap-gatherer sells healing, cures and poison. An Agaceph raft-trader
  sells Illusion. Harbour pilots at Archon sell the water spells. The grave-singers sell the laying of the dead. Fire,
  frost, atronachs and Mark and Recall are sold only by the foreign mages our records already place (the hedge-mages
  at Alten Corimont and Archon, the Dunmer mage at Stormhold, Soulrest, Gideon). About 15 to 20 sellers across the 24
  regions, each with a sheet of 12 to 20 spells.
- **New names and descriptions for about 50 spells** that are native in spirit but foreign in name. Stoneflesh becomes
  Clay-Skin, Calm becomes a hush of the Chime-Keepers, Turn Undead becomes a grave-song, and Magic Expanded's
  poison, wind, swimming and jumping spells get marsh names. Spells that stay foreign keep their names.
- **The three repairs**, and the test kit of spells removed with the opening as already planned.

**In game:** the first spell you buy is from an Argonian who tells you it was her mother's. Fire comes from a nervous
Imperial in Gideon. The spells behave exactly as before.

**Cost and confidence:** small. Records and writing only. Renaming was proven in game before the change of plan (11
spells); it is redone the current way, in our plugin. Sure.

**What it does not do:** nothing new to cast, nothing that looks different, nothing in place of the shouts.

### Option 2. "Sap and Song" (do more) - recommended

**The point:** give the marsh a magic of its own in the place Skyrim kept its shouts, and a short list of spells no
other province has, using only what the game already holds.

**What is built, on top of option 1:**

- **About ten Hist gifts.** These are powers, used with the shout button, usually once a day, given by a tribe's
  tree-minder when the player has earned that tribe's trust (a quest stage, through the quest form's existing step:
  no new script). One or two per culture that has a strong magic of its own, so travelling and helping people is how a
  player grows a native magic, as finding word walls was in Skyrim. A first list, each from a stock effect:

  | Gift | Given by | What it does | Its job in play |
  |---|---|---|---|
  | Spore Cloud | the Root-Folk of Helstrom | everyone close is held still for a few seconds | breathing room when surrounded |
  | Sap-Mend | any tree-minder | a strong heal over a minute (Histskin, made to work with our no-healing rule) | the emergency heal |
  | Drowned Root | the Island of Blackrose | breathe water and see the living through it | wrecks, drowned ruins, the drowned Hist |
  | Stillstare | the Agaceph | one person who has not yet attacked stands frozen | past a guard without a fight |
  | Chime-Hush | the Chime-Keepers | your steps are silent and nearby beasts calm | the quiet road through a den |
  | Wamasu's Answer | the Stone-Sleepers of Tsonac | lightning wraps you and bites whoever strikes you | punishing close attackers |
  | Root-Call | the Root-Folk, late | a root guardian fights beside you for a minute | an ally for a boss |
  | Grave-Song | the Sisei-Xul grave-singers | the walking dead near you flee or fall | Ayleid ruins and bog blights |
  | Clay-Skin of the Mound | the Clay-Mound People | heavy armour for a minute | a caster who must stand and fight |
  | Sea-Memory | the Spray-Folk of Seafalls | shows the way to what you seek | finding the next step in open marsh |

- **About twenty native spells**, one line per school at every level, made as copies of Skyrim and Magic Expanded
  spells with marsh names and, where the record allows it, marsh colours (sap amber, spore green, peat brown). For
  example a spore burst that weakens to poison, a root-bind that slows, a lightning line named for the wamasu, a
  swarm in place of the first atronach (Skyrim's own spriggan swarm), a false lantern that draws a guard away.
- **Sellers and quests teach these first**, so a new player meets the native list before the foreign one.

**In game:** you help the reed-cutters of a village and their tree-minder lets you lick the scar. You come away with
a gift no book holds. By the middle of the game a mage has five or six gifts on the shout button and a spell list
that reads as Black Marsh. A warrior who never opens the magic menu still collects gifts.

**Cost and confidence:** medium. About ten power records, about twenty spell copies with tomes, a handful of
recoloured effects, the sellers' sheets, and one line in each giving quest. All record-only; the teaching step is
proven. Two things are unproven here and are what the pilot is for: a record-only recolour (never done in this
project), and how once-a-day powers sit in soulslike fighting (it may want a shorter wait, which a record can set).

**Why this one:** the gifts are the single change that most separates us from Skyrim for the least work, they cost
about the same as ten spells, and they give every faction and culture a reward to hand out that is not gold or gear.

### Option 3. "The Deep Marsh" (do most)

**The point:** make native magic the main magic of the game: a full list, used by the people and creatures you fight
as well as by you.

**What is built, on top of option 2:**

- **The finished spell sets inside the creature mods we hold**, brought in whole: a water school of 20 spells
  (waterball, torrent, geyser, rain cloak and more), the wamasu's chain lightning and lightning cloak, a spore cloak,
  acid sap and poison bomb, and summons of a fleshfly swarm, a miregaunt and a spectral wamasu. About 40 more spells,
  set into the five schools and levels, with tomes and sellers.
- **Enemies and locals cast marsh magic**, handed out by the distribution mod we already run: a tribe's hunters use
  poison and hush, its minders heal with sap, foreign mages throw fire. This is what makes the difference felt by a
  player who never casts.
- **A signature for all 18 cultures** (the lore note has three to six ideas for each).
- **Sap as fuel:** Hist sap, which exists as an item in those mods (great strength, but slowed and drugged), sold by
  sap-gatherers and made part of a caster's kit.
- **Spells that answer the place:** stronger in rain, in water or at night. The game has the conditions, but reports
  on two of them conflict, so each is tried first.

**In game:** a fight with marsh hunters is poison, spores and silence; a fight with Dunmer slavers is fire. Water is
a weapon. The foreign spell list is the exception.

**Cost and confidence:** large, and the least sure. Our plugin would depend on four more mods for their spell
records (not yet checked in the built game), about 60 spells must be balanced against soulslike fighting, and enemy
casters change how hard fights are, which means your in-game checks. I would not approve it as a block: I would pick
from it after option 2, starting with enemies casting what option 2 already made.

## 6. Comparison

| | 0. As shipped | 1. Marsh Names, Marsh Hands | 2. Sap and Song | 3. The Deep Marsh |
|---|---|---|---|---|
| New to cast | nothing | nothing | 10 gifts, 20 spells | 10 gifts, about 60 spells |
| Looks different | no | no | a few recolours | recolours and the creature mods' own effects |
| In place of shouts | nothing | nothing | Hist gifts | Hist gifts |
| Enemies use it | no | no | no | yes |
| Scripts | none | none | none | none |
| Fees | none | none | none | none |
| Agent effort | small | small | medium | large |
| Your checks in game | Histskin | one seller | the three-item pilot, then a walk | several, for balance |
| Main risk | magic stays Skyrim's | modest gain | once-a-day powers may need tuning | balance, four more mods to depend on |

Agent effort is a ranking, not a figure: I cannot estimate it reliably. The pilot in option 2 is where it gets
measured, as with the new-art pilot.

## 7. Recommendation and next step

Choose **option 2, "Sap and Song"**, begun with a pilot of three things for you to try in game: a renamed spell
bought from a marsh seller, the Spore Cloud gift, and one recoloured effect. If the pilot pleases you the rest of
option 2 follows, and option 3 stays a list to pick from later.

If you choose option 1, nothing is lost: option 2 is built on it.

Whatever you choose, the three repairs of section 2 are done, and the lore's stance on magic
(`story/lore/topics/magic-practice.md`) is rewritten to match your choice, so quests and dialogue speak of magic the
same way everywhere.

## 8. What I could not check

- Whether Histskin is really dead under our no-healing rule (read from records; one look in game settles it).
- The permissions pages of other authors' spell mods: Nexus refused automated reading. No option above copies from
  them; they were read as examples only.
- Whether the creature mods' spell records can be used from our plugin in the built game (option 3 only).
- Nothing here was tried in game.

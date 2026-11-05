<!-- imported unchanged from elder-souls-argonia docs/quests/57-glossary.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 57. Glossary — the slice's load-bearing nouns

Machine table: `world/sources/dialogue/glossary.json` (rows `{id, forms,
topicId, actOne, opaque}` and the `loadBearing` noun list), read by
`worldgen.dialogue_lines` and the glossary gate in `dialogue_gates.py`. A
row changed here changes there in the same commit.

The lore-onboarding validator reads this file
([80 §59b](80-technical-architecture.md), conditions
[85 §A3](85-condition-vocabulary.md)). One row per term: the term and its
aliases (split on ` / `), a one-line gloss for a newcomer, the dialogue
topic a newcomer can ask, whether the topic is open in Act I, and `opaque`
where the topic returns folk speculation, never the truth.

Scope: the proper nouns in the published slice place records, the faction
names, and the lore the slice touches. Any change that introduces or
retires a load-bearing noun updates this file in the same change. A
person's own name is not an entry: it resolves through the NPC registry
(`world/sources/registries/npcs.json`).

Argonian name forms, for reading every name below: a **verb-clause name**
(*Bones-And-Tools*, *Kaska-Meen*) is a translated Jel phrase and is the
usual form for people and small places; a **Jel name** (*Hissmir*,
*Haynekhtnamet*) is untranslated; an **exonym** (*Chasepoint*, *Alten
Meerhleel*) is the name a foreign clerk wrote down. Places often carry two.

## Peoples and belief

| Term | Newcomer gloss | Newcomer topic | Act I | Opaque |
|---|---|---|---|---|
| Argonian / Argonians / Saxhleel | The lizard-folk native to Black Marsh. *Saxhleel* is their own word for themselves. | Who are the Saxhleel? | yes | |
| Argonia / Black Marsh | The province: a marsh country ruled from within since the Empire left. | What is Argonia? | yes | |
| Hist | Great sentient trees. Argonians hatch near them, drink their sap and listen to them. | What is the Hist? | yes | |
| hist-sap / sap | The Hist's sap, drunk in rites of hatching and coming of age. | What does the sap do? | yes | |
| tree-minder / Tree-Minder | The person who tends a village's Hist and speaks for it. | Who is the tree-minder? | yes | |
| egg-tender / clutch | A clutch is a family's eggs; the egg-tender keeps them until hatching. | Why guard the clutch? | yes | |
| naheesh | A tribe's elder or headman, beside the tree-minder. | Who leads here? | yes | |
| ojel | The Argonian word for outsiders. It is neutral, not an insult. | What does ojel mean? | yes | |
| lukiul | The nativists' slur for an assimilated Argonian. | What is a lukiul? | yes | |
| Sithis | The void god of change. Argonian priests teach that death and loss are its work and not a wrong. | Who is Sithis? | yes | |
| Nisswo / Clutch of Nisswo | Argonian priests of Sithis. | Who are the Nisswo? | no | |
| Shadowscale / Shadowscales | Assassins born under the Shadow and trained for Sithis. | What is a Shadowscale? | no | |
| Naga | A tall adder-like Argonian breed. Most of the marsh's brigands are tribeless Naga. | Who are the Naga? | yes | |
| xanmeer | A stepped stone pyramid of the old Argonians, mostly ruined. | What are the stone pyramids? | yes | |
| Dunmer / Dres | Dark elves of Morrowind; House Dres was the great slaving house. | Who were the Dres? | no | |
| Imperial / Imperials / Imperial-built | People and works of the Cyrodiil's Empire, which ruled here until it withdrew. | What did the Empire leave? | yes | |
| Bretic | Of the Bretons, a human people of the west. | Who are the Bretons? | no | |
| Owing | Debt that binds a person to labour until it is paid. It is the marsh's law where there is no court. | What is the Owing? | yes | |
| Archein | Argonian families who served the slavers and kept serf villages. | Who were the Archeins? | no | |
| Umbriel | The flying city that destroyed Lilmoth and killed much of the south in 4E 48. | What happened in 4E 48? | no | |
| Battle of Argonia | The battle whose survivors withdrew to Helstrom. | What was the Battle of Argonia? | no | |
| Haynekhtnamet | A wamasu of Shadowfen said to live in a pond. Villages make offerings to it against flood. | Is there a creature in the pond? | no | opaque |

## Factions

| Term | Newcomer gloss | Newcomer topic | Act I | Opaque |
|---|---|---|---|---|
| An-Xileel | The nativist government of Argonia, heirs to the movement that drove out the Empire. | Who rules Argonia? | yes | |
| Veiled Reed | The An-Xileel's covert office; its factors travel the interior. | Who are the Veiled Reed? | no | |
| Unbound Root | A movement that holds the Hist above every law; some are victims, some fanatics. | Who are the Unbound Root? | no | |
| Many-Root Conclave / Conclave | The order of Hist stewards who keep the trees and oversee consent. | What is the Conclave? | yes | |
| Reed-Sail Compact / Compact | The guild of boat crews, routes and ferries. | Who runs the boats? | yes | |
| Salt-Teeth | Pirates inside the Compact. | Who are the Salt-Teeth? | no | |
| Chainbreakers / Blackrose Chainbreakers | Abolitionists who audit the Owing and burn false debts. | Who are the Chainbreakers? | no | |
| Nisswo of the Turning Path / Turning Path | The Nisswo order that holds the Teeth of Sithis. | What is the Turning Path? | no | |
| The Empty Cradle | The Shadowscale order. The masters who gave it orders are gone. | Who sends the Shadowscales? | no | |
| Naga-Kur | The Naga people who rule the inner swamps of Murkmire. | Who are the Naga-Kur? | no | |
| Tribeless Naga / Cut-Rope | Naga outside any tribe; Cut-Rope's raiders are one band. | Who raids the tracks? | no | |
| Sul-Xan | A Naga cult that takes souls; feared by every tribe. | Who are the Sul-Xan? | no | |
| Rootworm Waykeepers / Waykeepers | Keepers of the rootworm routes and the air pockets. | Who keeps the worm-roads? | no | |
| League of Open Water | People who argue citizenship and property on the water. | What is the League? | no | |
| Marsh Charter | A fighters' guild tradition that opposes a foreign charter. | Who hires fighters? | no | |
| Night-Reed Chapter | The thieves' guild. | Who are the thieves here? | no | |
| Sunken Archive | Scholars who contest who owns knowledge. | What is the Sunken Archive? | no | |
| College of Whispers | Discreet mages, interested in the Hist and Umbriel. | Who are the College? | no | |
| Synod | Chartered mages, rivals of the College. | Who are the Synod? | no | |
| Cyrodilic Collections | An antiquities society that digs and argues over returning finds. | Who digs the ruins? | no | |
| Imperial Legion remnant / Legion | Legion garrisons and their heirs, left behind when the Empire withdrew. | Why are there legionaries here? | yes | |
| Morrowind veterans | Dunmer soldiers of the old war who never went home. | Why are there Dunmer soldiers? | no | |
| House Dres remnant | The slaving house's surviving claimants. | Are the Dres still here? | no | |
| Thorn Ash-Reed Accord | The body arguing saltrice title on the northern border. | Who owns the fields? | no | |
| Umbriel Witness Society | People who argue over the memory of 4E 48. | Who remembers Umbriel? | no | |
| Blackguards | Argonian pirate-brigands of the south coast. | Who are the Blackguards? | no | |
| Bright-Throat tribe | A Murkmire tribe that breeds horse-lizards and welcomes outsiders. | Who are the Bright-Throats? | no | |
| Murkwater / Murkwater tribe | A Murkmire tribe of hunters and trainers; also their village. | Who are the Murkwater? | no | |
| Root-Whisper tribe | A tribe whose Hist withdrew after a plague. | What happened to Root-Whisper? | no | |
| Xit-Xaht | A Murkmire tribe that its Hist directs. Other tribes fear it. | Who are the Xit-Xaht? | no | |
| Stillrise | The undead village of Shadowfen. | What is Stillrise? | no | opaque |

## Offices and institutions

| Term | Newcomer gloss | Newcomer topic | Act I | Opaque |
|---|---|---|---|---|
| Root Talk / Helstrom Assembly / Assembly | The convocation of tree-minders and naheesh that governs Helstrom by consensus. | Who governs Helstrom? | no | |
| Scalded Throne | Helstrom's empty throne. It has been empty for longer than any living person remembers. | Is there a king? | no | opaque |
| Unbound Root cutting | A cutting taken from a Hist by the Unbound Root. | What is a cutting? | no | |
| Shells and Stones | A gambling game played at ferry stages. | What game is that? | yes | |
| Fish-Eye Rye | A Hissmir liquor, drunk with the nostrils plugged. | What is Fish-Eye Rye? | yes | |

## Places named in the slice records

| Term | Newcomer gloss | Newcomer topic | Act I | Opaque |
|---|---|---|---|---|
| Helstrom | The interior capital, a city grown into a Hist grove. | What is Helstrom? | yes | |
| Greenspring | A spring village on the way to Helstrom. | Where is Greenspring? | no | |
| Cut Circle | The Unbound Root's sermon hall: a long stilt hall over still water at a lagoon's edge within a day of Helstrom, where the cult preaches in the open to anyone who comes. | What is the Cut Circle? | no | |
| Gideon | The western frontier city, where the courts still work. | What is Gideon? | yes | |
| Lilmoth | The southern port, destroyed in 4E 48 and rebuilt smaller. | What happened at Lilmoth? | no | |
| Archon | The eastern port and the province's legal harbour. | What is Archon? | no | |
| Thorn | The northern border city of saltrice fields. | What is Thorn? | no | |
| Blackrose / the Rose | Blackrose is a lake city. The Rose is its old prison, now inhabited. | What is the Rose? | no | |
| Soulrest | The old Imperial capital, now contested. | What is Soulrest? | no | |
| Alten Corimont | A neutral river port that will take anyone. | What is Alten Corimont? | yes | |
| Alten Meerhleel | A trade port and floating village north-west of Lilmoth. | What is Alten Meerhleel? | no | |
| Murkmire | The southern region of tribes and the Naga-Kur. | What is Murkmire? | no | |
| Shadowfen | The north-western region around Stormhold. | What is Shadowfen? | no | |
| Blackwood / Blackwood Road | The western hills and the road to Cyrodiil through them. | Where does the road go? | yes | |
| Morrowind | The Dunmer province to the north. | What is north of the marsh? | no | |
| Hissmir | A pilgrimage xanmeer where outsiders may touch the Hist. | What is at Hissmir? | no | |
| Rimfield | A grain village on the rim shelf above the pass, the nearest of the villages to the wamasu shrine. | Where is Rimfield? | no | |
| Tear | A Dunmer border town; the Tear road runs there from Thorn. | Where does the Tear road go? | no | |
| Padomaic / Padomaic Ocean | The eastern sea. | What is the eastern sea? | no | |
| Southern Sea | The sea south of the marsh. | What is south? | no | |
| Onkobra | A river that runs east past Gideon into the interior. | What river is that? | no | |
| Panther Race / Panther River | The river from Cyrodiil that forks by Greenspring and Helstrom. | What river is that? | no | |
| Portdun-Mont | A coastal settlement near the pearl lots. | Where is Portdun-Mont? | no | |
| Long-Water Hold | A settled hold in the deeps. | What is Long-Water Hold? | no | |
| Prison road / Border road / Mile House | Old Imperial roads and a waystation, still called by their old names. | Where does this road go? | yes | |
| Teeth of Sithis | The largest Sithis temple in Murkmire. Its original purpose is disputed. | What was the temple built to do? | no | opaque |
| Riverwalk / Chasepoint / Claywater / Nine Bends / Gang Ground / Bones-And-Tools / Counted Lots / Lighter Flotilla / Tag House / Sealed Vault / Broke Column / Bog Iron Workings / North Cut | The slice's own places; each answers its own name topic. | What is this place? | yes | |

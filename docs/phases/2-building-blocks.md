# Phase 2: the building blocks (the proving kit)

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

Each block is one small, real example built in our plugin on top of BM&V, proven off game by the agent, then
verified in game by the owner. A block's record and script shapes become the template every later use copies.
The first block also settles **the authoring route**: records are written as Spriggit YAML in `plugin/` and
built to the ESP on the build VM (`spriggit` is installed at `~/.argonia/spriggit`); xEdit on the play machine is
the checker; the Creation Kit is used only where nothing else can (FaceGen for a new face; the Papyrus
compiler). If Spriggit proves awkward for a record type, a Mutagen script replaces it for that type.

| Block | The example | What it proves for later |
|---|---|---|
| B1 Dialogue | a new greeting and one new topic on an existing BM&V NPC, conditioned on a global | changing anyone's lines, Fuz Ro D-oh silent voice, conditions |
| B2 NPC | a new NPC (template from a BM&V or vanilla actor, so no FaceGen) placed on existing navmesh with sandbox and sleep packages and a bed | placing people anywhere, schedules, ownership |
| B3 Creature and boss | one creature at a fixed level in a marsh spot; one named boss with a unique inventory | encounters, bosses, [0035](../decisions/0035-nothing-is-levelled-against-the-player.md) |
| B4 Quest starts | one quest started three ways: a dialogue topic, entering a trigger volume, reading a note | every quest trigger we will need |
| B5 Scripting | a stage fragment, an alias script (OnDeath), a trigger script, a global-driven condition; compiled on the machine | the script shapes, the compile job, where logic lives |
| B6 Items | one weapon with our stats, placed in a container and given as a reward | items and loot without levelled lists |
| B7 Faction | a faction with two ranks, an NPC in it, a line that changes with rank | faction lines |
| B8 Remove or change | a BM&V NPC disabled; a BM&V reference moved; a BM&V quest's stage changed | editing what BM&V built |
| B9 Journal | a quest with directions written in the journal, no marker | directions, not markers |

**Owner test:** one session through the nine examples, from an issue that says where each one is and what to
do. A block the owner finds broken is fixed and re-posted; a block that passes is never re-tested.

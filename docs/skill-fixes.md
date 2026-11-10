# Skill fixes owed

The one list of owner feedback whose lesson must land in a recipe: a skill in `.claude/skills/`, or the design
doc that is a pipeline's recipe (e.g. `docs/design/quests-on-a-world.md`). The system (CLAUDE.md, Agents):

1. **Record at once.** When the owner reports something wrong in output that a skill or recipe produced, add a row
   here in the commit that acknowledges it: the recipe, the fault in the owner's words (with the issue link), and
   the walk or check that will verify the fix.
2. **Fix the root cause, then verify.** Fill in the root cause and the fix commit when they land. The recipe is not
   touched yet, unless the owner asks for it now (then say so in the row and do it).
3. **Generalise and update on verification.** When the owner's walk or check confirms the fix, the agent who acts
   on that reply names the shape of the fault (the class of mistake, not this instance) and rewrites the recipe so
   the whole class is got right first time. The recipe still reads as a clean recipe, never as history or feedback.
   Then the row is deleted, in the same commit.
4. **Session start and walk replies.** Read this list at session start. Every owner walk reply is checked against
   it before the issue is closed.

| Recipe | Fault (owner's words, link) | Root cause | Fix | Verified by |
|---|---|---|---|---|
| new-world water (tools/newworld/water_kinds.py; no skill yet: a recipe goes in docs/design/ when verified) | Closed small bodies classed as stream; one closed body split marsh/stream; river classed as blackwater swamp; flow directions wrong, and northern streams flowing inland; fringe stream bits on marsh/swamp; channels with no water link to the sea classed as flowing (owner-rulings 2026-11-08 and 2026-11-09) | Kind and flow decided per pixel or blob, not from the channel graph's shape and connection to the sea | nw-02 lane W (round 2) | the owner's nw-02 walk (#56, checks G, H) and the atlas |
| new-world ground texturing (tools/newworld/landcover.py and textures) | Hard texture edges were never fully fixed by the old pipeline (owner-rulings 2026-11-08) | Edges assumed fixed from old code, never measured | nw-02 step 5: blends measured and looked at in crops | the owner's nw-02 walk (#56, check B) |
| place-research skill | Places promise mechanics Skyrim lacks (a "strong current"); no hard gameplay field; invented places; too many ledgers, rolls and tallies (owner-rulings 2026-11-09) | The recipe asks for local colour and lets a researcher invent where the lore is silent | nw-02 lane P (round 2); the recipe itself updated at the owner's ask (owner-rulings 2026-11-10, "the skills are brought up to date"): gives as hard gameplay, only what Skyrim delivers, no place invented from nothing, no life built on ledgers | the owner's read of the updated atlas |
| dialogue-write, talk-write, quest-write (briefs) and docs/design/quests-on-a-world.md parts 6 and 7 | "Dialogue - too many people early on repeating each other (e.g. about adding to the owing for food). Every single person in the hold (plus owes the months) all mention it! Dialogue writer skill - needs to be context aware - so it writes first time in a way that makes multiple conversations in the same space not repetitive (especially during the opening act flow)." (walk, 2026-11-10) | Each speaker's brief was built alone: every speaker who knew a fact got it to state, and each writer wrote one person without seeing who else the player hears in the same place and stage; no check compared speakers | Echo windows (tools/argonia_world/echoes.py): one owner per fact per window, "Already said near you" in every brief, pointer facts for talkers, the `echoes check` gate; the repeated lines rewritten (this commit) | the owner's walk check on the opening's dialogue |
| docs/design/blocks.md and docs/design/quests-on-a-world.md (people who walk), quest-write | "the gang never starts moving! So I can't go on to the next bit. Something wrong with the building blocks or how they are applied" (walk 5); in session: "they were already standing at the dock's landward end when I came out. Then I walked up to them and nothing else happened" | The march package became eligible at a stage set from another cell, so the walk happened unloaded and unseen; the route to the camp crossed navmesh islands BM&V never joined; the read-backs checked records, not whether a walk can be walked or seen | The opening re-hosted on one island, the walk started in the player's sight by a hidden stage, the same rules applied to every package of the act, `plugin.sh questcheck` (the recipe text was rewritten in those commits, as the owner asked) | walk check 10.1 |
| docs/design/blocks.md (a line heard without talking) | A new block not yet seen in game: the shout at MQ01's strike is a `Say` from the stage fragment | - | - | walk check 10.1 (the shout is heard or subtitled) |


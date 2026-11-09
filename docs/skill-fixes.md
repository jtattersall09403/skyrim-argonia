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
| place-research skill | Places promise mechanics Skyrim lacks (a "strong current"); no hard gameplay field; invented places; too many ledgers, rolls and tallies (owner-rulings 2026-11-09) | The recipe asks for local colour and lets a researcher invent where the lore is silent | nw-02 lane P (round 2) | the owner's read of the updated atlas |
| quest-write (stages) and docs/design/quests-on-a-world.md | "opening didn't actually tell me to talk to Wuleen Sei with a quest stage ... I think we should have quest stages for talking to her and then going out of the door and then what to do next. More quest stages generally" (walk 4) | The record gave the opening's steps (talk, answer, leave, follow) no stage, journal entry or objective each; the answers were topics behind a global that set no stage | MQ01 stages 10/20/30/35/40 with objectives and markers, answers as choices (37b31eab; blocks.md: answers as choices, objective markers) | walk check 9.2 (#57) |
| talk-write (who it covers) | "There were some people in the opening barge who I couldn't talk to - I said I want everyone to have dialogue in all the places the slice quests touch" (walk 4) | The recipe covered the census's settlement people only, not the people the quests themselves place; a voiceless BM&V template left three with no dialogue at all | Quest people's lines (quest_people.json, 8f3450d2, 11af4604); voiceless template given a voice (37b31eab) | walk check 9.4 (#57) |
| dialogue-write (asks the player for what they cannot give) | "Buys-the-months seemed to ask me for a name but then there was no opportunity to give one" (walk 4) | A line asked the player a question with no reply topic or choice behind it | The line rewritten to tell, not ask (37b31eab) | walk check 9.5 (#57) |
| docs/design/quests-on-a-world.md (doors and new-game start) | "The door up the stairs did nothing ... another door ... looked like it should be a door that doesn't teleport you anywhere ... but then it did teleport me out"; "Loads of people who used to have dialogue no longer do" (walk 4) | A load-door model with no teleport, and a teleport on a door with a room behind it; quests that start with a new game had no SEQ file, so their dialogue ran only after a save was loaded | Doors paired or plain, 12 audited; Argonia.seq built and laid (37b31eab); the recipe text was updated in that commit | walk checks 9.1 and 9.3 (#57) |

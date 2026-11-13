# Finish the stories and write the roster

Split out of [nw-05](nw-05-story-quest-adapt-1.md) on 2026-11-13 at the owner's ask, to stop that session's usage:
"aiming for having a smaller amount of high quality output completed if possible rather than a large amount
partially completed, and split out whatever is left into a new phase with its own brief". Written by the lead; the
owner has not edited it yet, and his words go above this line when he does.

## Where nw-05 left things

- **Done and on main:** the province digest (`story/design/world/`); the province plan and the consistency ledger
  (`story/design/quests/lines/province-plan.md`, `consistency.md`); all fourteen line stories written by Fable and
  read once on paper (`story/design/quests/lines/`); the story skill's "designing a quest that can be built" and the
  sketch check; the research on choices and what a quest can give, with thirteen new results a quest can use; the
  studio's story panel, batch notes and machine start; Helstrom's rooms named and its needs loaded.
- **Second round done** (the ledger applied, an outcome table on every ending, sketches passing, three readers who
  value different things on three models): the main quest, the Marsh Charter, the Lamp-Bearers, the Sunken Archive,
  Many-Root. In none of them was the stop rule met: each lists what a third round must check.
- **Second round not started:** the Chainbreakers (new world), the League, the Night-Reed, the Nisswo, the Reed-Sail,
  the Shadowscales, the Thorn Ash-Reed, the Umbriel Witness, the Waykeepers. Their stories stand as read once, and do
  not yet carry the ledger's rulings: names, places and seven finales will change.

## What this phase delivers

1. **The second round for the nine lines above**, by the brief already written
   ([nw-05-round-two-brief](nw-05-round-two-brief.md)), each by Fable.
2. **A third, narrow round where the second did not meet the stop rule**: a fresh deliverability reader on the full
   outlines, and players only on the choices that did not split. One set of changes; then stop, whatever the result,
   and say what remains.
3. **The skill learns from the readers**: every new class of fault the deliverability readers found in the second
   round (each story's "Read on paper" section lists them) becomes a check in `sketch` or an instruction in
   `buildable.md`, so that the next line written needs fewer rounds. The measure: a fresh writer's first outline
   draws at most one blocking fault.
4. **The database, by one lane** (nw-05's step 6): every person the stories name and every person of the slice
   places, in third normal form; each line's quests as rows; the peoples with no culture row; the stories' changes to
   places' notes; every story's needs loaded onto its places as promises; the digest regenerated.
5. **Minor quests, lightly** (nw-05's step 7): two or three local premises re-homed to each slice place.
6. **For the owner to read**: one private page that sets the fourteen stories side by side with what their readers
   made of each, and the handful of calls the ledger left for him (`consistency.md`, "For the owner").
7. **Owed from nw-05**: the generic script's thirteen new steps compiled on the play machine when no stream is live
   (`tooling/job_guard.sh run --gpu papyrus -- bash infra/gpu-box/records_jobs.sh papyrus papyrus/ARG_Effects.psc`).

## How to run it cheaply

- One line at a time is a whole Fable context (about 400,000 tokens with its readers). Run few at once and stop when
  a line meets the stop rule; do not start a round to polish.
- Lanes return at most a dozen lines; the detail is in the story's own "Read on paper" section.
- Do item 3 before items 1 and 2, so that later rounds find less.
- The slice comes first: the main quest's Act I and the second slice's openings (Many-Root, the Waykeepers, the
  Chainbreakers, the Lamp-Bearers) matter before any later quest of any line.

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
- **The main quest's plot is done** (`story/design/quests/lines/main-plot.md`): three rounds with four Sonnet
  readers each and a plot-level deliverability reader; in the last two every reader could retell it and wanted to go
  on, and the last raised nothing new the writer agreed with. Of twelve players nine chose MEND, three CLAIM and
  none CUT, which stands (readers splitting is weighed, not a bar). It withdrew the old eleventh quest, so the main
  quest is fourteen quests. Owed because of it: one line each in `province-plan.md` section 2 and the main quest's
  rows of `consistency.md`, which still name Aunike Crown and the retired Shadowscale. The Act I outlines were not
  re-tested by this.
- **Second round done** (the ledger applied, an outcome table on every ending, sketches passing, three readers who
  value different things on three models): the main quest, the Marsh Charter, the Lamp-Bearers, the Sunken Archive,
  Many-Root. In none of them was the stop rule met: each lists what a third round must check.
- **Second round not started:** the Chainbreakers (new world), the League, the Night-Reed, the Nisswo, the Reed-Sail,
  the Shadowscales, the Thorn Ash-Reed, the Umbriel Witness, the Waykeepers. Their stories stand as read once, and do
  not yet carry the ledger's rulings: names, places and seven finales will change.

## The main plot rewritten to the owner's overhaul (2026-11-13)

The owner overhauled the main quest in the story explorer (23 notes, left as drafts) and asked for the overall plot
alone to be rewritten, with no review round and no faction changes. Done: `main-plot.md` is the new plot (nineteen
quests; a long treasure hunt as Act II; the Reed's dream cellars as the twist; three endings with play effects),
written to every writing rule and run through the prose linter; its section 9 lists what it needs of the world,
five calls for the owner on the ceiling, and every knock-on effect found by checking (the built first-act quests
mq01, mq03 to mq05, Helstrom's studio needs and place files, place hooks, the roster, the province plan, about forty
ledger rows, six faction lines, four lore extrapolations). The owner's rulings from the notes are in owner-bar and
owner-rulings. Each note has a reply in the explorer, shown under the draft (collection `draftReplies`). Owed: `main.md`
written again from the plot before any main quest is written; the rounds below for `main` are void until then.

## The plot's knock-ons settled (2026-11-13, the owner's rulings)

The owner ruled on the knock-ons: "Studio story panels mist be made to update automatically / First act in old
world - leave it / Ledger, part of province plan, roster - update then / Six faction stories - mark them as needing
to be rewritten. But don't rewrite yet". And on #71 he approved the plot's six ceiling calls, each narrowly.

- **The first act built in the old world (mq01, mq03 to mq05) is left entirely as it is.**
- The studio's story panel is made from the stories each time it opens (`tools/places/needs.py`): the plot's new
  needs table, the line stories' tables, the people they name, each linked to its story and marked when that story
  is to be rewritten. Helstrom shows the plot's two needs (the handler's quiet house, the go-between's lodging) as
  not yet judged; what was placed for the earlier plot (the Sealed Spring urn, the locked chest, Ruxa-Neel's and
  Wujeel's parts) stands and is listed as placed for a story that has changed, for the owner to decide.
- The consistency ledger, the province plan (section 2 whole and every line the plot made untrue) and the cast
  roster follow the plot; the root-herald of Jal-Veesa is Vosh-Leera; the plot's four extrapolations are in
  `story/lore/extrapolation/argonia-4e201-state.md` section 11.
- Marked "to be rewritten", each with what in it is untrue by section, not rewritten: the Reed-Sail, the Sunken
  Archive, the Waykeepers, Many-Root, the Chainbreakers (new world), the Umbriel Witness. `main.md` is marked
  replaced by the plot. Item 1's rounds for these six wait for their rewrite.
- The six ceiling additions are in quest-form, blocks ("Blocks owed") and quest-system; each is a new block proven
  once before the plot's quests use it. In the finale Cuts-the-Old-Knot is already in the cavern when the player
  arrives; nobody follows the player.

## What this phase delivers

1. **The second round for the nine lines above**, by the brief already written
   ([nw-05-round-two-brief](nw-05-round-two-brief.md)), each by Fable.
2. **A third, narrow round where the second did not meet the stop rule**: a fresh deliverability reader on the full
   outlines, and players only where an option had no honest case or nothing of its own to give (readers choosing alike is not
   by itself a reason for a round: owner, 2026-11-13). One set of changes; then stop, whatever the result,
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
7. **Done, 2026-11-13**: the generic script's thirteen new steps were compiled on the play machine once the stream
   ended (1 succeeded, 0 failed); they reach the game with the next deploy.

## How to run it cheaply

- One line at a time is a whole Fable context (about 400,000 tokens with its readers). Run few at once and stop when
  a line meets the stop rule; do not start a round to polish.
- Lanes return at most a dozen lines; the detail is in the story's own "Read on paper" section.
- Do item 3 before items 1 and 2, so that later rounds find less.
- The slice comes first: the main quest's Act I and the second slice's openings (Many-Root, the Waykeepers, the
  Chainbreakers, the Lamp-Bearers) matter before any later quest of any line.

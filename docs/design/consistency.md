# One world, told the same everywhere

Every statement about the new world agrees with every other, at all times: the place records (every table that
holds a fact about a place), the lore (canon and our extrapolation), the story, the quests and their dialogue, the
people, and the drafted places as built. The checker (`python -m tools.newworld.consistency`, a stage of the gate)
fails a commit that breaks this; it is the floor, not the method. The method is below, and every agent works by it
from the first hour of a piece of work, never as a clean-up at the end.

## Every fact has one home

A fact is stored once, and everything else refers to it by id or is derived from it: a quest names a place, a room
or a person by id; a place's population is the count of its people; whether it stands on water is read from the
ground. When you find the same fact stored twice, the fix is to stop storing one of them, not to keep the two in
step. What cannot be reduced this way is prose and the built place itself: for those, the ladder below.

Every checker rule, what it compares, where each side lives and why it stays a check is in
[consistency-rules](consistency-rules.md). To add a fact, find its home first (the column, table or source a build
derives it from), store it there once and derive any copy; a new rule is only for a judgement or a sentence that
restates the fact.

## When two things disagree, which one changes

Change the thing that matters least and costs least, so that what matters most is delivered as authored. In order,
from what is kept to what gives way:

1. **The main quest's structure**: its sequence, plot, key events, who does what and why, and whatever of the lore
   those rest on. Kept as the owner authored it. A faction's line has the same standing within itself, below the
   main quest.
2. **The lore**, canon first, then our extrapolation. Kept; we deviate only where a place or a quest cannot be
   delivered otherwise, as slightly as will do, and the extrapolation is rewritten to say what is now true.
3. **What can be delivered well**: what the source place and our pieces give with easy, reliable hand work. A
   drafted place that reads as built on purpose is hard to get and is worth more than a detail of wording.
4. **Cosmetic and incidental detail** in the story, a quest, dialogue or a record: colours, materials, counts,
   where a thing hangs or stands, a name of no consequence. This gives way first: the prose is changed to match
   what is built. A record that says "light hide tents" over a source whose tents are dark becomes "dark hide
   tents".

Place-record prose is the cheapest thing to change; a quest's stage order, a key event or a person's part in the
plot is the dearest. If the cheapest change touches rung 1 or 2, it is not cheap: find another, and if there is none
that is a call for the owner.

## How an agent works by it

- **Before** changing a place, a quest, a person or a record, read what the others say about it: the place's record
  rows, the story and quest text that names it (`python -m tools.places needs <place>`; grep the quest records and
  the story pages for the place and its people), the lore page for its region.
- **As you go**, each time what you build or write differs from what another source says, settle it then: decide
  by the ladder which side changes, change it in the same piece of work, and change it EVERYWHERE it is said (the
  database tables are generated from their sources: change the source and regenerate; the checker finds the rest).
  Record the change and why in the place's notes or the quest's record.
- Changed prose that a player or the owner reads goes through the skill `text-review`.
- Never leave a known disagreement for later, and never hand over a place, quest or record with one.

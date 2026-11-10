---
name: place-lessons
description: Turn the owner's finalised studio edits of one place into better place recipes. Reads the save's fault edits and the owner's notes with the changes they cover, finds the patterns behind them, and rewrites place-build (place-people for edits to who a person is, place-stock for edits to what a place holds) so the next place gets each class right first time; taste edits stay that place's preferences. Run headless by the finalise chain, one run per finalised save.
---

# Place lessons

The owner edits an agent's draft of a place in the studio and finalises the save. Every edit is marked `fault`
(the builder got it wrong) or `taste` (a preference). Your job is to find what the fault edits say about the
recipe that produced them, and change the recipe so a fresh agent working on any place gets that whole class of
thing right first time. The recipe for where things stand, the streets, the lights and people's placement is
`place-build`; the recipe for who a person is (name, household, trade, wealth, backstory) is `place-people`; the
recipe for what a container, a person or a trader holds is `place-stock`. The prompt names every input and the files you may edit; beside them you may add rows to the skill-fixes list.

The place itself is already right: the owner's edit is in its files. You change recipes for the next place. You
never change this place, and no lesson asks for it to be drafted again.

## Inputs

- The fault edits (`faults.jsonl`), one op per line, each with `n`, `op`, `space`, `call`, and its `before` and
  `after` (the op table is in `docs/design/place-studio.md`, Edits). An op carries `note`, the words of the
  owner's note that covers it, when one does. The whole save, taste ops included, is `edits/<save_id>.json`.
- The owner's notes (`notes.json`): each note's words with exactly the edits it covers, each edit said as what
  changed, from what to what, and where. One note is one statement about all of its edits: "these three stalls
  moved off the boardwalk: stalls must never block a walkway".
- The place files before and after the save (`before.json`, `after.json`): every ref with its base, kind,
  position, rotation and seat; clearance; land patches; paths; people with routines; and, under `identities` and
  `stock`, the place's people source and stock source. Both files are large: search them for the ids and
  positions you need.
- The build and check results, when there are any.
- Every place's `place.json`, for the preferences recorded at other places.
- The current `place-build` skill, and the `place-people` or `place-stock` skill when the prompt names content
  edits for it.
- The skill-fixes list (`docs/skill-fixes.md`), for changes owed that you may not make yourself.

## Method

1. **Read the recipe first.** Read `place-build` whole, so you know what a builder following it would do. When
   the prompt names content edits, read each recipe it names for them whole as well: `place-people` for
   `identity.edit`, `place-stock` for `stock.*`.
2. **Take only the faults.** Set aside every `taste` op. Number the fault ops you will reason about. Read the
   owner's notes next: a note names the cause the owner sees in its edits, in the owner's words.
3. **Reconstruct each fault.** For each fault op, say what the builder placed and what the owner did instead,
   in the place's terms: what kind of thing it is, what it stands on or near (bank, water, slope, street, door,
   another building), which way it faces, how far it moved and in which direction relative to those features.
   Look up neighbours in `before.json`: the nearest water, street, building and door, the ground's slope.
4. **Group into patterns.** Ops that share a cause are one fault: twenty houses each nudged off a slope is one
   pattern, not twenty. Group by what the moved things have in common (kind, setting, direction of the change
   relative to the feature) rather than by op type. The edits one note covers are one group the owner has made
   already: start from it, and test the note's words against each of its edits. A pattern needs at least two ops,
   or one op the owner's note says is general.
5. **Find the cause in the recipe.** For each pattern, find the step of its recipe that led the builder there:
   a rule that was wrong, a rule that was missing, an order of steps that decided too early, a measure taken at
   the wrong point. Quote the text to yourself; if no text led there, the recipe is silent on it.
6. **Name the lesson as a class.** State the general mistake and its correction, true for any place: "footprints
   were fitted by their centre point, so long buildings overhang the bank; fit by the whole footprint", never
   "house 12 was 3 m too far north". Test it: would it have prevented every op in the pattern, and would it be
   right at a place with a different layout?
7. **Decide where it belongs.**
   - The builder's **judgement** (what to look at, which way to turn, what to keep clear, when to patch land):
     the text of `place-build`. Rewrite it (below).
   - The stocker's **judgement** (what a holder holds, at what tier, behind what lock, whose it is): the text of
     `place-stock`. Rewrite it the same way, and mark the lesson `"skill": "place-stock"`.
   - A **tool's fixed rule** (a number or a computation in `tools/places/draft`, `seat` or `stock`): do not edit
     code. Add one row to the skill-fixes list for the skill that describes the tool, naming the tool, the rule
     and the fault, with "lessons run" as who reported it, and list it in the lessons file as a tool change owed.
   - **Who a person is** (a name, a household, a trade, a wealth band, a backstory: `identity.edit`): the text
     of `place-people`. Rewrite it the same way, and mark the lesson `"skill": "place-people"`.
8. **One-off faults** (no pattern, no general cause): they are already fixed in this place by the owner's edit.
   List them; do not touch the recipe for them.
9. **Taste.** Taste ops never become rules. They are already recorded as this place's preferences. Look across
   every place's `preferences`: a preference of the same kind made at three or more places is a candidate rule.
   List it as a candidate only; never apply it.

## Rewriting a recipe

- Change the step that caused the pattern, in place. Sharpen or replace the sentence that led the builder
  wrong; add a sentence only where the recipe was silent, and put it in the step where a builder needs it.
- Write the corrected rule as the plain way to do the thing: what to do, what to measure, in what order. Never a
  list of mistakes, never "do not do X as before", never the owner, an edit, a save, a place's name or a date given as the reason for a rule. A recipe's own steps about the owner's studio edits and notes stand.
- Keep the skill from growing. Where your lesson makes an existing sentence redundant, remove it. A run usually
  changes a few sentences; a run that adds more than it removes needs every added line to carry a rule.
- Keep the skill's own shape, headings and voice. Change nothing a lesson does not touch. The order of work at
  the top of `place-build` and each skill's narrow-change section stay.
- Where a rule belongs to another skill, the skill you are rewriting points to it and does not repeat it.
- Write each whole rewritten skill to the path the prompt names for it; the finalise chain puts it in place. When
  no lesson belongs in a recipe, write nothing there.

## Check your rewrite

Reread each skill you rewrote whole as a newcomer would, from the top:

- It reads as one recipe for doing its work correctly; nothing in it refers to past drafts, feedback or
  history; no patch-like "also" or "note" bolted on to a step.
- Every command, path and check name it gives is one the skill gave before or one you have read in the inputs.
- No two sentences contradict each other; the step order still works.
- Each lesson is there in general form, in the step where it applies.
- Nothing from a taste op or a one-off is in it.

Fix anything that fails, then reread once more.

## The lessons file

Write it last, to the path the prompt gives, as JSON. Every text field is plain English for the owner: full
sentences, no jargon, no op numbers or ids in the prose, distances in metres (70 game units is about a metre).

```
{"lessons": [{"ops": [n...], "where": "recipe" | "tool", "skill": "place-build" | "place-stock" | "place-people",
              "lesson": "the general rule, one sentence",
              "why": "why the recipe led the builder to the mistake, one or two sentences",
              "change": "what the recipe says differently (recipe), or the tool change owed (tool)"}],
 "one_offs": [{"ops": [n...], "what": "what was wrong, fixed in this place only"}],
 "taste_candidates": [{"what": "the preference", "places": [place_id...]}],
 "checked": "one sentence: the rewrite was reread whole and reads as a clean recipe"}
```

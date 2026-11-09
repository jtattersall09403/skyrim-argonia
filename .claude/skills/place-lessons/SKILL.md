---
name: place-lessons
description: Turn the owner's finalised studio edits of one place into a better place-build recipe. Reads the save's fault edits, finds the patterns behind them, and rewrites place-build so the next draft gets each class right first time; taste edits stay that place's preferences. Run headless by the finalise chain, one run per finalised save.
---

# Place lessons

The owner edits an agent's draft of a place in the studio and finalises the save. Every edit is marked `fault`
(the builder got it wrong) or `taste` (a preference). Your job is to find what the fault edits say about the
recipe in `place-build`, and change the recipe so a fresh agent drafting any place gets that whole class of
thing right first time. The prompt names every input and the only files you may edit.

## Inputs

- The save (`edits/<save_id>.json`): ordered ops, each with `op`, `space`, `call`, an optional `note` in the
  owner's words, and its `before` and `after` (the op table is in `docs/design/place-studio.md`, Edits).
- The place files before and after the save (`before.json`, `after.json`): every ref with its base, kind,
  position, rotation and seat; clearance; land patches; paths; people with routines.
- The build and check results, when there are any.
- Every place's `place.json`, for the preferences recorded at other places.
- The current `place-build` skill.

## Method

1. **Read the recipe first.** Read `place-build` whole, so you know what a builder following it would do.
2. **Take only the faults.** Set aside every `taste` op. Number the fault ops you will reason about.
3. **Reconstruct each fault.** For each fault op, say what the builder placed and what the owner did instead,
   in the place's terms: what kind of thing it is, what it stands on or near (bank, water, slope, street, door,
   another building), which way it faces, how far it moved and in which direction relative to those features.
   Look up neighbours in `before.json`: the nearest water, street, building and door, the ground's slope.
4. **Group into patterns.** Ops that share a cause are one fault: twenty houses each nudged off a slope is one
   pattern, not twenty. Group by what the moved things have in common (kind, setting, direction of the change
   relative to the feature) rather than by op type. A pattern needs at least two ops, or one op the owner's note
   says is general.
5. **Find the cause in the recipe.** For each pattern, find the step of `place-build` that led the builder there:
   a rule that was wrong, a rule that was missing, an order of steps that decided too early, a measure taken at
   the wrong point. Quote the text to yourself; if no text led there, the recipe is silent on it.
6. **Name the lesson as a class.** State the general mistake and its correction, true for any place: "footprints
   were fitted by their centre point, so long buildings overhang the bank; fit by the whole footprint", never
   "house 12 was 3 m too far north". Test it: would it have prevented every op in the pattern, and would it be
   right at a place with a different layout?
7. **Decide where it belongs.**
   - The builder's **judgement** (what to look at, which way to turn, what to keep clear, when to patch land):
     the skill text. Rewrite it (below).
   - A **tool's fixed rule** (a number or a computation in `tools/places/draft` or `seat`): do not edit code.
     Add one row to the skill-fixes list for `place-build` naming the tool, the rule and the fault, with
     "lessons run" as who reported it, and list it in the lessons file as a tool change owed.
8. **One-off faults** (no pattern, no general cause): they are already fixed in this place by the owner's edit.
   List them; do not touch the recipe for them.
9. **Taste.** Taste ops never become rules. They are already recorded as this place's preferences. Look across
   every place's `preferences`: a preference of the same kind made at three or more places is a candidate rule.
   List it as a candidate only; never apply it.

## Rewriting place-build

- Change the step that caused the pattern, in place. Sharpen or replace the sentence that led the builder
  wrong; add a sentence only where the recipe was silent, and put it in the step where a builder needs it.
- Write the corrected rule as the plain way to do the thing: what to do, what to measure, in what order. Never a
  list of mistakes, never "do not do X as before", never a mention of the owner, an edit, a save, a place's
  name as the example of a fault, or a date.
- Keep the skill from growing. Where your lesson makes an existing sentence redundant, remove it. A run usually
  changes a few sentences; a run that adds more than it removes needs every added line to carry a rule.
- Keep the skill's own shape, headings and voice. Change nothing a lesson does not touch.

## Check your rewrite

Reread `place-build` whole as a newcomer would, from the top:

- It reads as one recipe for drafting a place correctly; nothing in it refers to past drafts, feedback or
  history; no patch-like "also" or "note" bolted on to a step.
- No two sentences contradict each other; the step order still works.
- Each lesson is there in general form, in the step where it applies.
- Nothing from a taste op or a one-off is in it.

Fix anything that fails, then reread once more.

## The lessons file

Write it last, to the path the prompt gives, as JSON. Every text field is plain English for the owner: full
sentences, no jargon, no op numbers or ids in the prose, distances in metres (70 game units is about a metre).

```
{"lessons": [{"ops": [n...], "where": "recipe" | "tool",
              "lesson": "the general rule, one sentence",
              "why": "why the recipe led the builder to the mistake, one or two sentences",
              "change": "what the recipe now says differently (recipe), or the tool change owed (tool)"}],
 "one_offs": [{"ops": [n...], "what": "what was wrong, fixed in this place only"}],
 "taste_candidates": [{"what": "the preference", "places": [place_id...]}],
 "checked": "one sentence: the rewrite was reread whole and reads as a clean recipe"}
```

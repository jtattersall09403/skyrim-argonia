---
name: place-plan
description: Start a place draft of the new world - read the place record as the brief, choose the source place by looking at candidates as places and testing them against the record, pin it, and write draft.plan (look, gives, structures kept, relabelled or pruned). Use before a place's first draft, and again when its source or plan changes.
---

# The record and the source

Step 2 of the place path ([place-system](../place-system/SKILL.md)). Before: the record (`place-research`). After:
the ground and the baseline (`place-site`).

## 1. Read the record as the brief

`python3 -m tools.newworld.place_card <place_id>`, read whole: what the place is, its kind and size (the footprint
radius), where it sits (water, banks, slope), its people, its promises (`gives`), dangers, and what the stories need
of it (the quests' rooms, things and persons at the place). In the database (`db.open("newworld")`): `place`,
`place_give`, `place_source` (rank 0 the allocated source, 1 to 3 the next most similar), `source_place`. Skyrim's
town rules: `docs/research/skyrim/town-life.md`.

## 2. Choose the source by looking

The record's `source` note and the allocated source are a first idea. Candidates: the card's `source 0..3`, the
committed match (`newworld/sources/source_match/place_source.jsonl`), the catalogue search
(`python3 -m tools.places search query "<kind of place>"`), and sources of the same kind and culture.

1. Get each candidate's bundle (`python3 -m tools.places extract <source_id>`) and **look at it as a place**:
   `python -m tools.places look --source <source_id> survey --ring <radius_m>` (the whole-place sheet), `section`
   through its relief and `units --ring <radius_m>` for what it holds inside the ring. Name what stands inside the ring: its structures, its water, its ground, its rooms.
2. Test each against the record: **within the footprint, over half of the source's pieces would be kept as built**
   against the record's look and promises, and **the quests' rooms are present or come cheaply from one other
   source**. A place the main quest uses gets its closest match.
3. A source another place already uses is allowed and never counted against a candidate. The place laid later
   (by `place.json` `wholesale.laid`, which `draft wholesale` stamps; a baseline with no stamp counts as earliest)
   writes, first, a `differs` entry in `draft.plan` for each earlier place: `{place, takes, turn_and_approach,
   landmark, prunes, adds, dressing_and_people}`, a sentence each, after looking at the other place (`look <other> at
   <middle> --top` and eye-level views) and at the source (`look --source`). The baseline is laid to it (`pivot` and
   turn chosen by it): `draft wholesale` refuses without it, and `draft check` and the build's `promises` check fail a
   missing entry or the same part of the source at the same turn (`tools/places/draft/differs.py`).
4. Where too little of every candidate is useful, build from the asset pool round the nearest thing: carry the closest
   source with `--carry-radius` round the one structure or layout worth keeping, prune the rest, and add everything
   else (`place-adapt`). Say so in the plan.
5. When something must change to fit, change the cheapest thing with the fewest knock-on effects: a source note,
   then a minor record, before a main-quest text or a drafted place. Where the record clashes with the ground, the
   record changes; the place is not moved.
6. Pin it: add the place to the JUDGED table in `tools/places/sources_match.py` with the reason, then
   `python -m tools.places sources-match --pin <place_id>`; set `place.json` `source_id` to it. Never edit the match
   files by hand.
7. A place whose `place.json` carries a `redraft` mark (its source was re-chosen after it was drafted) is redrafted
   fresh from the new source: `source_id` set to the mark's, the mark removed, then this skill and `place-site` from
   the start; nothing of the old draft is carried over. Its `differs` duty is reckoned from the new source.

## 3. Write draft.plan

`draft.plan` (`tools/places/draft/plan.py`) is the record of the judgement:

```
{source, differs?: [{place, takes, turn_and_approach, landmark, prunes, adds, dressing_and_people}], look: [{line, by}], gives: [{kind, by}],
 structures: [{cluster | structure, what, verdict: kept|dropped, why}]}
```

- `source`: which source, why, and how this place differs from others on it.
- `look`: a row for each thing the record's look names, with the source or added pieces that deliver it.
- `gives`: a row for each promise of the record, by its kind.
- `structures`: a row for each major source structure (`python -m tools.places draft structures <place_id>`) and each
  source group with a standing building: `kept` (as built, relabelled or moved: the `why` says which and to what) or
  `dropped` (pruned). What is added is a `draft.add` row or a hand placement; `look` names it.

`python -m tools.places draft plan <place_id>` prints the plan's faults; `draft check` and the consistency checker
fail on the same ones. The plan is updated whenever the adaptation changes a verdict.

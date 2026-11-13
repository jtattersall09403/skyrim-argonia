# Adapt Story and Quest System and NPC roster

First pass. broad brush strokes. Choose the slice places. NPC roster in 3NF in database, including backstories, linked to whatever other existing tables they should be linked to. Use the Skills (think critically about them - how suitable to this point in the project; edit if sensible; use the relevant ones). Don't implement the actual quests or factions in-game yet.

Backstory and dialogue for non-quest NPCs in Helstrom?

Do not rebuild LOD at this point.
---

## The plan (the lead's, 2026-11-13; the owner's words above are kept as written)

Status: [PROGRESS.md](../../PROGRESS.md). Owned by the walk 6 session at the owner's ask (owner-rulings 2026-11-12).
The owner's bar for this phase is in [owner-bar](../../../story/design/owner-bar.md) and binds every step: the story is
"really naturally and deeply integrated" with the new world, never "patched or shoehorned"; the factions and the
spirit of the original are kept and everything else may be rewritten; it reads as "a really nicely written exciting
story throughout that any elder scrolls fan would fall in love with"; every quest is played with the game's own
skills, any build can finish the main quest, each faction leans on its own skills and has drama and tension of its
own; paperwork is rare; everything stays inside the Morrowind-level ceiling so that it can be built; the overall story
of the main quest and of each major faction is written by Fable. The method is the quest skills, entered at
`quest-system`; this phase uses `story-line` for every line and stops before `quest-write`.

### What this phase delivers

Broad brush strokes, a first pass, nothing built in game, no LOD.

1. **The province as the story sees it.** One generated digest of the new world for writers (per region and for the
   whole province): its 24 regions, 18 cultures and 258 places with what each gives the player, its danger bands,
   its travel network, its law, and who lives where, straight from the new world's database. Writers read this, not
   memory, so the story grows from what is there.
2. **The province plan.** Before any line is written: where each line lives in the new world and why that ground
   suits it (its seat, its hubs, the regions its quests range over), how the main quest travels the province act by
   act, where lines touch each other on purpose and where they must not collide, the opening region, and the slice
   places (the opening act's places plus one of each kind in the opening region, for nw-06 and nw-07). One document,
   written by Fable, read by a deliverability reader and by a reader who knows the world's digest and asks of each
   allocation "would this faction have grown here?".
3. **The main quest's story**, written by Fable with the `story-line` skill: the line in a page, the arc across its
   acts, every quest as an outline a quest writer can build without inventing, the skills each step uses. Read on
   paper by fresh readers, quest by quest, in rounds that converge.
4. **Each major faction's story** the same way, thirteen lines: the Chainbreakers (re-homed from tonight's story),
   the detectives, the League of Open Water, Many-Root, the Marsh Charter, the Night-Reed, the Nisswo, the Reed-Sail,
   the Rootworm Waykeepers, the Shadowscales, the Sunken Archive, the Thorn Ash-Reed and the Umbriel Witness. Each
   writer has the province plan and the main quest's outline, so the lines fit one world and one timeline.
   **Every story ends with what each quest needs of its places** (owner, 2026-11-13: truth of the world is built
   into how quests are made, and the places are not built yet). A story names a place by what the digest says it is;
   anything physical it relies on that the place's data does not hold is a row in the story's needs table, in words
   that place's source could be built to. No story describes surroundings or writes lines about a place: that is
   done on the built place, in nw-07, nw-08 and nw-10.
5. **One consistency pass over all fourteen** (Fable): shared people, places and events agree; no two lines use a
   person or a place in ways that cannot both be true; the timeline is one; then one coherent set of changes.
6. **The roster, in the database, in third normal form**: every person the stories name and every person the slice
   places hold, each with a name by the naming rules, a place, a household or post, a trade they can be seen to do,
   a faction and rank where they have one, and a backstory of a few lines; linked to the place, culture, faction and
   quest tables that exist. The quests of every line get their rows (premise, host places in the new world, the
   skills they use, their place in the line). The old Black Marsh & Valenwood rows stay as they are, marked as that
   world's.
   **The needs become promises of the places**: every row of every story's needs table is written onto its place's
   record as a promise (the place records already carry promises that `place-build` and `place-stock` must keep), so
   nw-06, nw-08 and nw-09 build each place knowing what the quests will ask of it, and a need a place cannot meet
   comes back to the story before any quest is written.
7. **Minor quests, lightly**: the roughly 560 local quest premises are not rewritten now; each slice place gets the
   two or three local premises that suit what it is, re-homed, as rows. The rest wait for nw-12.
8. **Helstrom's people**: backstories for everyone in built Helstrom go into the roster now; their talk is written
   in nw-06 with the rest of the slice's general dialogue, by `talk-write` with the surroundings sheet, once the
   owner's studio edits of Helstrom are in. (The owner's question above: this is the lead's answer; say if the talk
   is wanted now.)
9. **The skills, kept current**: what this phase teaches goes into `story-line` and `quest-system` as clean recipe;
   `place-people` and `talk-write` are checked against the roster's new shape.
10. **For the owner to read**: each line's story as its own document under `story/design/quests/lines/`, and one
    private page that sets them side by side with what the fresh readers made of each. No in-game check: this phase
    is read, not played.

### How it runs

- Fable writes; Opus builds tools and data. A story lane writes only its own document, so story lanes never collide.
  The database is written by one lane at the end (step 6), from the finished documents.
- Order: 1, then 2, then 3, then 4 in parallel (four at a time), then 5, then 6 and 7, with 8 to 10 alongside.
- Each story is read on paper as `story-line` says: fresh readers every round, all reading one version; a separate
  deliverability reader with the ceiling; one coherent set of changes per round; stop when a round can retell it,
  wants the next chapter, splits on the conflicts meant to be ambiguous, and raises nothing new the author agrees
  with. Readers are honest and a little hard to please, and are evidence, not votes.
- Nothing is built, seeded or deployed. The build machine stops when the lanes are done.

### The lead's rulings on the province plan's open calls (2026-11-13)

The province plan ([province-plan](../../../story/design/quests/lines/province-plan.md), section 6) asked for these
before the lines are written. They bind every line's writer; the first and the last go to the owner as a call when
the stories are posted, and nothing waits on the answer.

1. **The main quest ends at a place the world already has.** No place is invented for it: Act V goes down to the
   sealed spire at the bottom of Echo Deep, which the data holds. A "Lost City" as a new place is the owner's to
   add if wanted.
2. **Peoples with no culture row** (the tribeless Naga, the Sarpa, the Sul-Xan, the Paatru, the Tumnatu): a writer
   takes them from the lore, marks what is extrapolated, and lists what the roster lane must add as rows.
3. **No fighting in deep water.** A drowned place a quest fights in has floors behind its dive and its guardians on
   them; the swim is passable without a fight; breath is had by any race.
4. **A place hostile on sight that a story must speak in** gets one person who can be spoken to, as a need of that
   place (the Rose's gate, Ushaan Camp's edge, Nenria's approach). The Rose has no lower levels: what the main quest
   wants there is in the old warden's office its record already promises. Thorn and Giovesse keep their seats and
   their thin sources are a need (another source allotted in nw-08 or nw-09).
5. **Lilmoth's drowned quarter**: the Umbriel Witness sit at its edge on dry ground; a dive is into one drowned
   building, listed as a need.
6. **The settlements with a tree** are those the plan lists from the gives.
7. **Water has only the names the notes give**; otherwise it is the water by a named place.
8. **Helstrom has the 58 people its roster names.**
9. **The second slice** (four faction openings; Stormhold's source is Markarth, a large build) stands as proposed
   and is the owner's to cut when nw-08 is planned.

### Measured

- The digest: 258 places, 24 regions, 18 cultures, 645 hooks, 58 named people (`story/design/world/`).
- The province plan: read once on paper by three readers (one who knows the digest, one Elder Scrolls fan, one for
  deliverability); nothing merged or dropped; two lines re-scoped and four given work that is done, not heard.

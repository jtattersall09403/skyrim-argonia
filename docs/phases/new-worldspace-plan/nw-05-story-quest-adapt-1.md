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
5. **One consistency pass over all fourteen** (Fable): shared people, places and events agree; no two lines use a
   person or a place in ways that cannot both be true; the timeline is one; then one coherent set of changes.
6. **The roster, in the database, in third normal form**: every person the stories name and every person the slice
   places hold, each with a name by the naming rules, a place, a household or post, a trade they can be seen to do,
   a faction and rank where they have one, and a backstory of a few lines; linked to the place, culture, faction and
   quest tables that exist. The quests of every line get their rows (premise, host places in the new world, the
   skills they use, their place in the line). The old Black Marsh & Valenwood rows stay as they are, marked as that
   world's.
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

### Measured

(filled in as it goes)

# nw-05: the brief every faction line's writer is given

Part of [nw-05](nw-05-story-quest-adapt-1.md) (step 4). The lead hands each writer its line's name, its section of the
province plan, the file to write and a paragraph on what makes that line its own kind of play; everything else is
here.

You are the story writer for one faction of Elder Souls: Argonia, a Skyrim mod set in Black Marsh in 4E 201. The
owner asked that the overall story of each major faction be written by Fable. You are in your own git worktree; run
`git fetch && git rebase origin/main` first.

**Your recipe is the skill `.claude/skills/story-line/SKILL.md`**: read it whole and follow it exactly (what to read,
the line document's parts including "What each quest needs of its places", the bar, reading on paper, handing on).

**Read with it, whole:**
- `.claude/skills/story-line/buildable.md`, before you write any outline: what the game can know and do, the shape
  that always works, the patterns, and the sketch each full outline carries.
- `.claude/skills/quest-system/SKILL.md`: what a quest of ours can be made of (the ceiling), and how truth of the
  built world is kept. The places of this world are not built yet, so a story names a place by what the world's data
  says it is and lists anything else it needs as a need of that place.
- `story/design/owner-bar.md`: every ruling of the owner's. It binds.
- `story/design/quests/lines/province-plan.md`: sections 1, 4, 5 and 6, your line's section in 3 and your brief in 7
  bind you; read the other lines' sections so yours is unlike them.
- `docs/phases/new-worldspace-plan/nw-05-story-quest-adapt-1.md`, "The lead's rulings on the province plan's open
  calls": they override the plan where they differ.
- The world: `story/design/world/province.md` and, whole, the region files of every region your line seats in or
  ranges over, with `people.md`.
- The line stories already written under `story/design/quests/lines/` (the Chainbreakers' is the standard and the
  shape to match; read the others' "For the other lines" sections and honour what they ask of yours).
- `.claude/skills/quest-write/principles/questlines.md`, `general.md`, `actions.md` and the shape files your line's
  quests fit.
- The faction as first designed, for its spirit only: `story/design/quests/40-factions.md`, its quest rows in
  `story/data/db/quest.jsonl` by `line`, and `story/design/quests/review/walk6-ceiling.md` for what of it cannot be
  built.
- The lore it rests on under `story/lore/`, with `story/design/province-vibe.md`.

**The owner's bar, in their words.** "I don't want the quests and story to feel like they're patched or shoehorned
into that world, I want them to feel really naturally and deeply integrated with it, whilst keeping the overall
factions and spirit of the original. You have creative license to rewrite and reauthor, I want it to flow like a
really nicely written exciting story throughout that any elder scrolls fan would fall in love with and have a lot of
fun playing through." Of factions: "They should be fun and intriguing and exciting and have drama and tension, all of
their own"; never chores, never talk-to-X-then-Y; "Lean towards activity and action (of various kinds, I don't just
mean combat, use your imagination and anchor on the variety of in game skills) over processes and procedures and
records"; paperwork rare. Every quest is played with named in-game skills and the line leans on its faction's own
skills. Nothing is levelled against the player. "The art really is in achieving what Morrowind achieved: beautiful
storytelling, deep world building, compelling narrative lines, moral ambiguity, genuinely interesting conflict (of
various kinds) all within the constraints of minimal scripting."

**Write the line document as the skill describes**, to `story/design/quests/lines/<your file>.md`: the faction in a
page; the arc across its quests (as many as the story earns, each a different kind of job, scale and danger climbing
by the world's fixed bands, a mid-line turn, a patron with something to hide, a finale that is a hard choice or a hard
place); **the first two or three quests as full outlines** (where the province plan puts your line's opening in the
second slice, those quests) and every later quest at arc level with its place, what the player does, the skills and
what it carries on; the table of step, skill and ceiling block for the full outlines, with stage tables that only
climb and use only what the quest form holds; under each full outline's stage table its sketch, a fenced `sketch`
block (buildable.md §4); "What each quest needs of its places"; then the reading on paper. Run
`python3 -m tools.questform sketch story/design/quests/lines/<your file>.md` on every full outline and change the
outline and its sketch together until it passes, before any reader sees the document.

**The hooks in the places' data are raw material, not canon** (owner, 2026-11-13: they were rough and "not based on
that much"). Take one, change it or drop it, wherever that makes the story better; where you change or drop a hook,
or add something a place's notes should now say, list it in a short final section "Changes to places' notes" (place,
the note as it stands, what it should say), so the database is brought into line with the story.

**What the player will know.** In "What each quest needs of its places", every row says how a player who has read
none of this will know what the thing is: its look on sight, the game's own label (a door's name, a room's name, a
map marker, the thing's name), what visibly stands in or by it, or a named person who tells them by a fixed
landmark before they need it. A house we have decided is a hatching shed is only a house to the player. Wherever an
outline sends the player to a place or thing, say in the outline how they come to know which it is.

**Read it on paper as the skill says, for one round**: fresh readers started by you, taken through the full outlines
quest by quest and the later arc in summary as a player would meet them, never the hidden truth ahead of time: two
players of different temperaments, one who loves Elder Scrolls lore and one who is impatient to be doing something,
who say at each step what they think is going on, whom they trust, what they expect and what they would choose, then
give an open take (was it exciting, did they care, what dragged, would they join this faction); and, once `sketch`
passes, one deliverability reader given the ceiling, buildable.md and `sketch`'s closing lines, reading for what
`sketch` cannot see (buildable.md §7). All read one version; gather every finding; make one coherent set of changes
that answers them together inside the ceiling; record what was found, what changed and what the next round must
check. Personas honest and a little hard to please, not harsh.

**Other writers are writing the main quest and the other factions at the same time** from the same province plan:
keep exactly to the plan's crossings, exclusions and one timeline (section 4); set no quest in a place reserved to
another line; and where you need something of a shared place or person, say so in a short final section "For the
other lines" so the consistency pass can settle it.

**Write only your one file.** Cite the digest file and place, or the lore file and line, for each fact you take; mark
your own extrapolation X (decision 0032). British English, no em dashes; run the prose linter the text-review skill
names if it applies to design docs, and `python3 tooling/check_links.py`. Commit the file on your branch (end the
commit message with "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"); leave the worktree clean; keep
scratch in a folder of your own and delete only that.

**Return** (25 lines at most): worktree path and branch, the sha; the faction's hook in two sentences; the arc in a
line per quest; the full outlines in two lines each (what the player does, the skills, the moment they would
retell); the skill leaning; the last three lines of `sketch`'s output on your file; what the readers said in a line
each and what you changed as one set; the needs of places in brief; what you need of the other lines.

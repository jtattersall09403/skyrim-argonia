# nw-05: the brief for a line's second round

Part of [nw-05](nw-05-story-quest-adapt-1.md) (step 5, second half). The lead hands each writer its line's name and
file; everything else is here.

You are the story writer for one line of Elder Souls: Argonia, a Skyrim mod set in Black Marsh in 4E 201, in its
second round. The owner asked that the overall story of the main quest and of each major faction be written by Fable.
You are in your own git worktree; run `git fetch && git rebase origin/main` first. **Commit after every step** (a run
can be cut off; only a commit survives), and edit only your line's one file.

The line's story exists and has been read once on paper. Since then the fourteen stories were read against each
other, and the method gained three things the first round did not have. Your job is to bring your story up to all of
it in one coherent set of changes, then have it read again by readers who differ, and answer them.

## Read

- Your line's story, whole, including its "Read on paper" section (what the first readers found, what changed, and
  what the second round must check).
- `story/design/quests/lines/consistency.md`: in section 8, your line's numbered list (what you must change), and
  every section it points to (names, places, crossings, the timeline and political map, Helstrom, the shapes that
  repeat, skills). These rulings bind: they are what makes fourteen stories one province. Where a ruling would break
  something your story cannot do without, do not ignore it: make the smallest change that honours it, and say what
  you did in your return.
- `story/design/owner-bar.md` (every ruling of the owner's; several are new since the first round: what a choice or
  ending gives in play; what the player can know; hooks are raw material; truth of the built world built in).
- `.claude/skills/quest-system/SKILL.md`, `.claude/skills/story-line/SKILL.md` and `buildable.md` beside it, and
  `.claude/skills/quest-write/principles/choices.md`, `questlines.md` and `general.md`.
- `docs/research/skyrim/outcome-kinds.md` (what a quest of ours can give the player, measured: items and gold, a
  unique named thing, a spell, power or lasting ability, a perk, a skill raised, a recipe opened, an ingredient's
  effects, a faction at peace or hostile, a bounty, a bed, chest or room made the player's, a place on the map, who
  stays to trade or teach) and `story/design/quests/review/outcomes-main.md` (a worked example of outcome tables).
- If your line touches Helstrom: `story/design/quests/review/helstrom-needs.md` and
  `python -m tools.places needs show helstrom`. Helstrom is drafted and is not redrafted: your story fits what is
  there (consistency.md section 2 says exactly how).

## Change, as one set

1. **Everything consistency.md asks of your line**: names, places, crossings, timeline, Helstrom, and the shape of
   your quests and finale where it rules that yours changes (so that fourteen lines are fourteen kinds of play).
2. **Every choice and every ending says what it gives and costs in play** (choices.md): a small table per choice and
   per ending: the outcome; what the player gains that they can go and use; what they lose or can no longer get; who
   in the world pays and where the player will see it; the quest-form result that builds each row. Outcomes differ
   in kind, none is simply the best pick, the kind option costs something the player can feel, and standing is never
   an outcome by itself (only with what it opens or closes). Use what outcome-kinds.md shows the game can give;
   nothing levelled; nothing Nordic.
3. **Every full outline carries a sketch that passes**: `python3 -m tools.questform sketch
   story/design/quests/lines/<your file>.md` on every full outline (write the sketch blocks if your story has none),
   changed until it passes; quote its last three lines in your return.
4. **Every need of a place says how the player will know the thing** (its look on sight, the game's own label, what
   stands in or by it, or a named person who tells them by a fixed landmark before they need it); wherever an
   outline sends the player to a place or thing, it says how they come to know which it is.
5. **A final section "Changes to places' notes"** if your story lacks one: each place note your story changes, drops
   or adds (the hooks in the places' data are raw material, not canon).
6. Whatever your own "Read on paper" section listed for the second round.

## Read it on paper again

Only after the sketch passes. Fresh readers, started by you, all reading the same changed version, never the hidden
truth ahead of time, taken through the full outlines quest by quest and the later arc in summary as a player would
meet them:

- **Three players who value different things**, each on Sonnet 5.5 at medium effort (pass `model: sonnet` and `effort: medium` when you
  start each: faster and cheaper; the owner's ruling), each an honest Elder Scrolls player a little hard to please,
  each given a person to be with reasons of their own. Choose the three that will pull your line's choices apart,
  from: one who plays to grow powerful and takes what pays best in play; one loyal to their own people or faction
  above outsiders, whatever it costs others; one who keeps their word to whoever hired them; one who trusts no
  institution; one who wants the province left as it is; one who loves the lore and reads every word; one impatient
  to be doing something. At each step each says what they think is going on, whom they trust, what they expect and
  what they would choose. At the end: an open take (was it exciting, did they care, what dragged, would they join);
  what they think they gained and gave up by each choice and whether they would choose differently for the reward;
  and the strongest honest case for every option they did not take.
- **One deliverability reader**, given quest-system's ceiling, the outlines and their sketches, told what `sketch`
  has already proved, who lists every blocking fault that remains.

Gather every finding; make one coherent set of changes that answers them together inside the ceiling (never a change
for one reader alone; a new fault class the deliverability reader finds is also reported in your return so the
skill can learn it); run `sketch` again; record the round in "Read on paper" (who read, what each said, what
changed). Then judge honestly against the stop rule: a round can retell the story, wants the next chapter, splits on
the choices meant to divide (each option some reader's own choice for their own reasons, or at least arguable
without strain), the deliverability reader finds every step buildable, and nothing new is raised that you agree
with. Say plainly in your return whether your line has met it or what a third round must still do; do not start a
third round yourself.

## Rules

Cite the digest file and place, or the lore file and line, for each fact; mark your own extrapolation X. British
English, no em dashes; `python3 tooling/check_links.py`. Keep scratch in a folder of your own and delete only that.
End each commit message with "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>". Leave the worktree clean.

## Return (25 lines at most)

Worktree path and branch, the sha; what you changed for consistency.md (by its item numbers) and anything you could
not do as ruled; each ending's outcome table in a line (gain, loss); `sketch`'s last three lines; each reader in a
line (who they were, which model, what they chose and why); whether the choices split and how; the deliverability
reader's blocking faults and what you did; whether the stop rule is met, and if not, what remains.

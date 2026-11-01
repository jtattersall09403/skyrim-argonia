<!-- imported unchanged from elder-souls-argonia docs/research/archive/agent-process-reviews/instruction-and-agent-tree-review-2026-10-14.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Instruction corpus and agent tree review, 2026-10-14

A critical review of CLAUDE.md, `.claude/agents/`, `.claude/skills/`, the
standards, the hook set and the agent-policy decisions (0079, 0106, 0118,
0131). It covers conflicts, bloat, cost and wall-time traps, how a mixed
round gets delegated, and the place-build skill and workbench. Ends with a
phased change set and the owner calls it needs.

## 1. What the numbers say

From `session_tokens.py --days 7` (5 sessions in the last 7 days, 13 in the
7 days before, 73 older):

| per session | last 7 d | prev 7 d | older |
|---|---|---|---|
| cost units (M) | 205.9 | 107.0 | 16.0 |
| planner cached (M) | 118 | 58 | 27 |
| sub Opus / Sonnet / Haiku tokens (M) | 356 / 334 / 158 | 399 / 35 / 36 | 55 / 4 / 2 |
| units: deliver / place-builder / deliver-small / find / lead | 68 / 39 / 29 / 26 / 15 | 29 / 27 / 5 / 8 / 19 | 9 / 0 / 0 / 0.6 / 0.4 |
| planner context from Agent results / docs read | 51 % / 32 % | 28 % / 39 % | 5 % / 15 % |

- Cost per session has risen about 13 times since the delegation controls
  went in. The work also grew (cities, interiors), so this does not prove the
  controls cost money. It does prove they have not held cost down.
- **The cost unit does not weight by model** (`session_tokens.py:36`, one
  `WEIGHT` table for every model). A Haiku token counts the same as an
  Opus or Fable token. Every tier and effort decision tuned against this
  number has been tuned blind. `find` shows 26 units, a third of
  `deliver`'s. Because Haiku costs less per token, its real share is
  smaller, but 158M Haiku tokens a session is still large. Fix this first.
- Where the planner's context goes: child reports (51 %) and docs (32 %).
  Shell exploration is now 1 %, so the look-up guard has done its job on the
  planner. The next levers are shorter reports, fewer wakes and a lighter
  orientation read.
- One city session (Helstrom, 11f4f0ed) ran 984 turns, 496M cached and 837
  units, with 82 place-builder, 55 lead and 52 deliver-small launches. There
  were 75 lead launches in a week, although the rule says a lead is "only for
  two or more large parallel lanes". Leads are relaunched at the 150k
  marker, so each lane pays repeated cold starts.

## 2. Conflicts (each is a coin-flip for an agent)

| # | Rule A | Rule B | Resolve to |
|---|---|---|---|
| C1 images | CLAUDE.md § GPU: "Every image goes to a `reader`" | `place-builder.md:15-17` look at the session renders yourself; `deliver-small.md:24` read images yourself | The designer looks at its own design-loop renders. `reader` is for bulk checklist sweeps and the blind feel check, where independent eyes are the point. |
| C2 waiting | CLAUDE.md: end the turn with `waiting: <labels>` | 0118 d8: never end the turn, loop `lane_wait.py --timeout 540`; `lead.md:50` "the result arrives as a wake"; `deliver.md:18` never end a turn while a reader runs | Test once which one the harness does today, then keep one rule. If children wake the parent, polling is pure cost: each 540 s return is a full turn of a lead's context. |
| C3 background | CLAUDE.md, `run.md`, 0118 8a: foreground up to 600 s | 0106 d20: "jobs over 60 s run in the background" | Foreground up to 600 s. Delete 0106 d20's first clause. |
| C4 lead edits | `lead.md:65` "fix small deficiencies yourself" | `lead.md:17` and `agent_guard.py` refuse a lead's Edit outside reports | Choose one. Recommendation: allow small edits (see § 4). |
| C5 caps | CLAUDE.md "Never set an arbitrary cap on a count, time…" | pod `--max-minutes <=30`, fifth builder refusal, "four rounds → escalate", "a fourth part, never a fifth", 1,500-line `Split:`, 400-line Read range, 80-turn review cap | Reword the rule: "A count or time is a **diagnosis trigger**, never a silent stop." Keep the triggers that earn their place and drop the rest. |
| C6 lessons | `place-builder.md:95` write the lesson into the skill as you go; `lead.md:98` a place ruling is an in-place skill edit | `place-build/SKILL.md:14` a rule needed mid-round is a tooling task, never written in a round; CLAUDE.md fix in the tool first | Builders and leads **propose** skill edits under `Recommendations`. The planner applies them once, at slice close. Twenty writers editing one skill is how it reached 16k words. |
| C7 tests | `deliver.md:18` test suites go to `run` agents; place-builder sends place pytest to `run` | CLAUDE.md § Working as a subagent: "Run the tests beside your change" | The implementer runs its own tests. rtk condenses the output. A Haiku relay inside a test-fix loop costs a spawn and two wakes per iteration, and the failure detail is lost. |
| C8 roles | 0079: planner "finds root causes" | `investigate` (Opus) exists to find root causes; deliver may not spawn it | Investigate is the planner's tool, and only for a class of defects spanning systems. |
| C9 description | `reader` description: "reader-and-rewriter" | body: read-only, the caller rewrites | Fix the description. |

Stale pointers, each a wasted read or a wrong step:
- `place-builder.md:35` "step 4b": no such step (the feel check is step 9).
- `place-builder.md:59` "§ How the builder works": the section is "How the work splits".
- `placement-workbench/SKILL.md:82` "Steps 5 and 6 of place-build": publish is 10, the packet is 12.
- `reader-checklist.md` "step 3/4", "SKILL § 5 read-back": stale numbering.
- 0106 d8: the "rulings R1–R55" table and `lessons/` store no longer exist (the skills README forbids row stores).
- 0106 and 0118 § Where each lives name `preflight.mjs`, which is no longer in `tooling/repo-standards/` (0131 replaced it with `check.mjs`).

## 3. Bloat and duplication

Corpus: agents 7.5k words, skills 26.4k (place-build 16.3k), CLAUDE.md
2.1k, standards 16.7k, decisions 150k across 131 files.

- **The same rule in five to eight places.** Some examples: "a missing asset
  is never a gap" (CLAUDE.md, lead, place-builder, deliver, place-build ×2);
  `--place` scoping (CLAUDE.md, lead, place-builder, deliver, place-build,
  place-edit, hooks.md, by-task); survey then fix once (CLAUDE.md, lead,
  place-builder, deliver, procedure, place-edit); the pod-deletion rule
  (lead, place-builder, deliver); the deploy barrier (CLAUDE.md, lead,
  place-builder); no `run_in_background` (deliver-small, run, research,
  investigate, 0118). **A rule a hook already enforces needs no prose
  beyond its hooks.md row.** The scope guard, miner guard, heredoc ban and
  Acceptance check are all enforced. Each copy costs tokens in every
  context that loads it, and copies drift apart (C3 and C6 above).
- **Incident history in a recipe file.** `reader-checklist.md` (2.9k words)
  has sections titled "Owner walk-4 defects" … "walk-8", with place names,
  audit numbers and dates. That breaks CLAUDE.md § Current recipe, and the
  word-budget gate evidently does not cover `references/`. It also
  duplicates `procedure.md` § Reader rows in long form, and 20 of its 55
  rows are tagged `rule:`. By its own header, those rows are never pasted to
  a reader.
- **Decision records as live rules.** CLAUDE.md links 0106 and 0118 as
  authorities. Both are history-laden (incident numbers, a superseded
  preflight, an addendum numbered 17 before 16) and partly stale. An agent
  that follows the link reads about 4k words to get the rule CLAUDE.md
  already states. 0079 was rewritten as current policy; 0106 and 0118 were
  not.
- **Per-turn hook text.** Every user prompt injects the 0079 echo, which is
  wrong when the session is not planning (like this one), and the
  session-switch paragraph (about 250 words). Print the paragraph only past
  L\*. Below that, one line is enough.
- **`lead.md` is 1.6k words.** It is the longest agent file and holds three
  mechanisms (plan review, measure loop, waiting) that could each be one
  line pointing at a tool.

## 4. Thought experiment: a mixed round

The task: fix five built places after an owner walk, add climbing, and fix a
global fps regression.

**How it flows today.**
1. Planner (Fable) orients. It loads CLAUDE.md, MEMORY, PROGRESS (1.9k),
   docs/README (1.5k), the decisions index (4.3k), by-task, the phase
   READMEs, 00-core and 20-world-provisions. That is about 25-30k tokens
   before any work.
2. The planner may not look across files. It sends one `find` per area, and
   the Coverage rule makes each one walk all its folders. For three
   workstreams that is 6-10 Haiku cold starts.
3. Walk feedback becomes defect classes and one `investigate` per class.
   `investigate.md` makes the investigator send every look-up, listing and
   git read to `find` agents. Each of those reads costs the Opus agent a
   spawn and wakes, and the code arrives as a Haiku paraphrase.
4. Places: five places, so a lead. The lead writes a standards file and
   brief files, then launches five place-builders with plan-first. Each
   builder cold-starts on CLAUDE.md, place-edit, place-build and
   placement-workbench (about 8k tokens), the type sheet, design.md and the
   layout. The builder returns a plan, the lead reviews it and resumes the
   builder by SendMessage, and only then does work start. The builder runs
   `lane_status.py` "after every five tool calls". That adds about 20 % to
   the turns of the most expensive leaf, and agent_guard already prints the
   context notice. Per place it runs about 4 reader view classes, a
   feel-check reader, kit-review readers, record coherence (6 readers + 1
   synthesis + a set reader), text-review and `deliver` children for causes
   outside the layout. That is 15-25 agents per place. The lead cannot run a
   test or make an edit, so it verifies through `find` and `run` agents,
   which adds one more hop.
5. Climbing: one `deliver` (Opus, effort low) with plan-first, reviewed by
   the planner. The deliver agent sends test suites to `run` agents, so its
   red-green loop goes through a Haiku relay, and it also needs
   `visual:check`.
6. Perf: a lead plus the GPU lane, under the measure-diagnose-fix rules.
   Fix agents may not measure, and pods stop at 30 minutes.
7. The `check` agent runs the review gate (a headless review of up to about
   9 minutes) and then `npm run check`. Reds go to a fix lane, then
   packet, deploy and owner walk.

**Where the waste is (ranked by likely spend).**
1. **Relay depth.** Planner → lead → place-builder → deliver → deliver-small
   is five levels. Each hop costs a brief, a cold start, a report and two
   parent wakes. The bigger cost is loss: every hop paraphrases intent, and
   that paraphrase is the main source of "wrong first time". A lead that
   cannot touch anything, and that relaunches at 150k, is pure relay.
2. **Delegating reads that the decider needs.** The guard forces Opus
   workers to delegate any multi-file look. With the repo's own weights, a
   `find` spawn at a 150k-context parent costs about 2.5k units for the
   brief, about 30k for two wakes and 30-50k for the child's cold start,
   before the child does any work. A direct `grep -rn` that returns 1k
   tokens, carried for 50 more turns, costs about 5k units plus one turn
   (about 15k). Direct is roughly 3-5 times cheaper unless the output is
   large (above about 5-10k tokens) or the job is many turns of trawling.
   It also keeps the evidence exact.
3. **Fixed per-turn overhead in the costliest agents:** the `lane_status`
   calls every five tool calls, progress notes every 20 turns, polling
   waits, and four to five Python hook processes per Bash call
   (agent_guard, role_guard, shell_guard, miner_guard, review_gate).
4. **Per-place agent count.** Record coherence alone is 8+ agents. Quest
   beats are found by `find` agents crawling `docs/quests/`, which a
   `quest_beats --place` script over structured quest rows would answer
   exactly.
5. **The Part A/B/C split.** Three cold starts of an Opus 1M-context agent
   per first-of-type place, each re-reading the skill, packet and
   design.md. With `wb.py session`, one builder can carry a camp end to
   end. Split on the context marker, not on a fixed part boundary.
6. **Effort is inverted.** The design and judgement agents (place-builder,
   lead, deliver) run at **low** effort, while the Haiku `run` agent, which
   only executes named commands, runs at **medium**. Getting it right first
   time needs thinking where the decisions are made.
7. **`[1m]` models with a 150k hand-off.** If the 1M variant carries a
   long-context premium, that premium buys nothing. If it does not, the cap
   binds and the variant is moot. Choose one on purpose.

**Optimal shape.**
- **Planner** (Fable): scopes, reads code itself whenever it must judge
  (the look-up guard stays for the planner only), writes briefs and reviews
  plans and diffs. Plan review moves up to the planner, which removes the
  lead hop for most rounds.
- **Lane owners**: `deliver` and `place-builder` (Opus, **medium**). They
  read, grep and run their own tests and publishes. They spawn
  `deliver-small` for bulk mechanical output, `reader` for sweeps and
  the blind feel check, and `find` only for repo-wide trawls whose detail
  they do not need.
- **`lead`** only for rounds of three or more places, or the GPU measure
  loop. It may make small edits and run tests (drop the agent_guard
  refusal). If that feels wrong, delete the role and let a place-builder
  coordinate sibling builders.
- **`investigate`**: reads directly. Used only by the planner, for a class
  of defects spanning systems.
- **Leaves**: `find`, `run` and `check` (Haiku, **low**), `research` and
  `reader` (Sonnet), `reader`.
- **One delegation rule** in 0079 and CLAUDE.md, replacing the many partial
  copies: *delegate when the output is long and you need only its
  conclusion, or when it can run in parallel with your own work; do it
  yourself when you need the detail to decide, or it is two steps or
  fewer.*

**Quality levers (prevent rather than check).**
- Move judgement into tools at write time, not survey time. Add a
  `wb.py lint <layout>`, run by `session commit` and `edit`, for every rule
  whose failure is known from the layout alone. The type sheets' "Problems
  and approach" lines (for example "pin `kind: prop`", "an unbound member is
  never compiled", "a building pin makes 97 C1 read a smelter as a
  building") are tool traps written down as prose. Each should become a
  default or a lint, after which the line goes.
- Use exemplars over rules. Link one accepted place per type (its
  `design.md` and layout) from each type sheet. A worked example teaches
  Opus more than 2k words of rows.
- Keep plan-first for any open approach, reviewed by the planner, which
  holds the cross-system view.

## 5. The place-build skills: from about 18k words to about 5k

The place-build total is 16.3k words, plus place-edit (0.9k) and
placement-workbench (1.5k).

1. **Delete `reader-checklist.md`** (−2.9k). Its `rule:` rows are checks
   already. Its `reader` rows exist in short form in `procedure.md` §
   Reader rows. Strip the history from those and keep them.
2. **Merge `procedure.md` into `SKILL.md`**, holding SKILL to about 1.5k
   words. The skill keeps only what needs judgement: Site → Intent and
   Walk-through → Palette → Brief → design in the session → Feel check →
   Packet. Every command sequence moves into the tool (item 3).
3. **Make the tool carry the procedure.** The state file already has
   `nextCommand`. Add `wb.py place <id> next`, which runs the next
   mechanical step: site_packet, kit-gaps, blueprint_promises,
   site_dossier, place_facts, the ledger stage stamps, the skeleton, the
   claim, publish and the commit index entry. It prints what needs the
   builder's judgement. Ledger stamps happen inside the tools, never by
   hand. This removes roughly half of SKILL.md steps 1, 2, 7, 10 and 13.
4. **Quest beats by script**: `quest_beats --place <id>` over the quest
   rows, in place of the find fan-out.
5. **Record coherence**: `record_coherence` is the deterministic part. Keep
   one reader for prose versus what is built, and fold that read into the
   batch text-review. The 6 + 1 + 1 agent workflow goes.
6. **Type sheets** (14 × about 650 words): keep Feel and the layout recipe.
   Move tool traps into tools as in § 4. Add the exemplar link. Target
   about 300 words each. Only one sheet loads per place, so this saves
   less context than items 1-3, but it removes the drift.
7. **`placement-workbench`**: shrink to the session loop plus
   `explain`/`--help`. The command index duplicates `wb.py --help` and the
   README.
8. **`place-edit`**: fine in size. Drop step 7's `find` diff, which
   `wb.py whatchanged` or a scoped `git diff --stat` answers directly.

## 6. Workbench verbs vs direct Blender

`wb.py session` is already the right architecture: a persistent headless
Blender holding the place, free bpy scripts through `es`, and the layout as
the single record through uid-delta commit. The gap is that the
deterministic, data-backed verbs (`snap` by mined abuts, `mount --hang`,
`settle`, `seat-on-shell`, `attach`, `boardwalk`) are CLI-only. A builder
therefore switches between two modes: the session, and one process per
verb on a scene file. `place-edit` and the skill describe both.

Recommendation:
- **Expose every verb inside the session as an `es.*` call** (`es.snap`,
  `es.mount`, `es.settle`, `es.seat_on_shell`, `es.attach`,
  `es.boardwalk`), sharing the seat table and the mined data, recorded by
  commit as the matching op. The CLI verbs stay for scripts and tests.
- **The session becomes the only design loop.** An Opus builder gets full
  freedom: any bpy it likes, its own cameras and lighting, and direct
  viewing of its renders. Correctness comes from `commit` running lint and a
  scoped `check` on the touched uids, not from a manual. The "tool manual"
  skill then shrinks to a page.
- Freedom without the guard rails (raw bpy writing straight to a layout)
  would lose the mined-evidence guarantees and the uid record. The session
  plus `es` verbs plus check-on-commit keeps those and still gives the
  builder direct control.

## 7. Change set, in order

1. **Measure right** (minutes): weight `session_tokens.py` units by model
   price, then re-read the table above with the new weights before changing
   tiers.
2. **Resolve C1-C9 and the stale pointers** in the files named (one
   commit).
3. **Agent files**: effort (place-builder, lead and deliver to medium; run
   to low); drop `lane_status` every five calls (the hook notice covers it);
   implementers run their own tests and reads; investigate reads directly;
   the shell look-up guard applies to the planner only; one delegation
   rule. Targets: lead ≤ 600 words, place-builder ≤ 500, deliver ≤ 350.
4. **CLAUDE.md**: delete rules that hooks enforce or agent files own,
   keeping the hooks.md row. Replace the "no caps" rule with "diagnosis
   trigger". Target about 1.4k words.
5. **0106 and 0118**: cut each down to the current decisions with their
   why. Move incident evidence to the research files that already hold it.
6. **Hooks**: one dispatcher process per tool call in place of five; time
   it with `tool_timings.py` before and after. The session-switch paragraph
   prints only past L\*.
7. **Place-build**: § 5 items 1, 2 and 6 as a docs change. Items 3, 4, 5
   and § 6 as a tooling chunk (deliver for `wb.py place next`,
   `quest_beats` and the session `es` verbs, sample-proved on one camp
   before the skill text is cut).
8. Re-run `session_tokens.py` and `cost-review` after one round, and
   compare.

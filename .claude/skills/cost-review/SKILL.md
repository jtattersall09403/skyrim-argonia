---
name: cost-review
description: Periodic cost review of our Claude Code usage. Runs the token report over time windows, checks each cost control still fires, names where the spend comes from and which sessions broke the pattern, and recommends the next safe reductions. Run in a FRESH session whenever the owner asks or about weekly.
---

You are reviewing cost, not doing project work; keep the session short (under 15 turns). The script counts, you
judge. Never edit settings, hooks or agents here: recommend; the owner approves; the change is its own commit.
Read CLAUDE.md "Costs" and decision 0008, and the last section of `docs/research/agent-ops/cost-reviews.md` if it
exists.

## 1. Measure
Hand both commands to one `run` agent and ask for the output verbatim:

    python3 tooling/session_tokens.py --sessions 5
    python3 tooling/session_tokens.py --days 1 --sessions 3

Read the bill from the dollar rows (by model and token class), never from token shares. An UNPRICED row means a
new model id needs a price.

## 2. Check the controls (yes/no, each with its number)
- Sessions are short (turns per session falling); the planner is not exploring (shell calls, explore share).
- No `sleep` in the latest window (each wasted a whole-context turn); the shell guard fired if anything tried.
- Cheap agents are used: calls by type include `find` and `run`; `general-purpose` near 0.
- Subagent spend is proportionate: if an expensive agent type costs more than the planner, check whether its
  briefs sent work a cheaper type could do.
- AWS month-to-date is under $100 and machines were stopped when idle (0008).

## 3. Where the spend is
The three largest sources by dollars, by model and token class, and what made the costliest sessions expensive.
Only if the costliest-sessions line does not explain it, ask a `find` agent one narrow question of that
transcript; never open a transcript yourself.

## 4. Recommend
At most five, each with the number it targets, the saving (from the report, not a guess), the quality risk and
the change in one line; order by saving over risk. Say plainly if nothing needs changing. Research outside the
repo only for a new cost category no control covers; add findings to the same record, not a new file.

## 5. Record
Append one dated section to `docs/research/agent-ops/cost-reviews.md` (create it with a two-line header if
absent): key rows, the control checklist, the recommendations, "owner: pending". Commit that file by pathspec.
Tell the owner the trend in one sentence, then the recommendations as bullets.

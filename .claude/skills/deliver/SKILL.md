---
name: deliver
description: Deliver one chunk of the schedule end to end in this session (the owner says "deliver 1.8", "deliver 2.W3", or /deliver <id>). Reads where things stand from the records, posts the owner's calls, runs the loop on the chunk's checks.md rows until every row is proven or ruled, and keeps PROGRESS, the brief and the ledger current in every commit.
---

# Deliver a chunk

The owner starts one session per chunk with "deliver <id>". This session works that chunk only, from where the
records say it stands to done. It never needs the owner to say where things are, and it leaves the records so the
next session doesn't either.

## 1. Where we are (read, in this order)
1. CLAUDE.md: the binding rules.
2. [PROGRESS](../../../docs/PROGRESS.md): the chunk's row.
3. The part README: the chunk table, Round two and the owner's notes map.
4. The chunk's brief, in full. Its **Starting state** is the last session's hand-off.
5. The chunk's rows in its part's `checks.md`. This is the work list. Every in-game check the chunk owes is a row.
6. The decisions and owner-brief rows the brief cites. Grep [owner-brief](../../../docs/owner-brief.md) for the
   chunk's topics before treating anything as open.

If the brief's Work names a check that has no ledger row, add the row first, as `owed`.

## 2. Owner calls first
Each decision the brief names as the owner's goes out at the start as
`python3 tooling/owner_inbox.py --post call --title ... --body-file ...`: plain English, the options, a
recommendation, how to reply and the cost. Work on everything that doesn't wait on the answer. Watch for replies
by the owner only, ack each at once, and record each ruling in the owner brief.

## 3. The loop (docs/loops.md, decision 0021)
1. **Check everything** the chunk owns, at the cheapest level that proves it (L1 data, L2 logic, L3 stills, L4 in
   game from a scene). Run in-game checks in one batch, crash-prone last, each once.
2. **Diagnose everything:** suspect the harness before the engine. Test only our own integration, never base
   Skyrim or a modder's behaviour.
3. **Fix everything together**, at the source, natively the Skyrim way. Fix rather than defer.
4. **Check again, once.** Repeat only for what is still red. After 3 identical failures, stop and diagnose.

Game machines:
- Use one machine that isn't the owner's (`infra/gpu-box/machines.conf`; never argonia-play while the owner may
  be playing).
- Work in your own worktree (`tooling/worktree.sh`).
- Long jobs run under `job_guard.sh` in the background.
- Stop the machine when the batch ends.
- Nothing may live only on a machine: archive long outputs when they're made (docs/machine-moves.md).

## 4. Keep the records current: every commit, not at the end
In the same commit as the work it reflects:
- each `checks.md` row: owed → proven with its evidence (a run dir, still, report line or sha), or dropped with an
  owner-brief date. run_batch.py updates `journey:` rows by itself.
- the brief's **Status** line and **Starting state**: where things stand now, so a crash or context end loses
  nothing;
- the chunk's PROGRESS row and the part README's Status: the same word.
- an earlier chunk whose last owed row this closes (Round two closes 1.1–1.6's and 2.W1–2.W4's rows): its Status
  moves to done in the same commit.

`make check` runs check_records.py and check_ledger.py and fails when these disagree. Push green work to
origin/main as you go.

## 5. Done
The chunk is done when every one of its `checks.md` rows is proven, or dropped by an owner ruling, and its
Acceptance holds. Then, in one commit:
- set Status to `done (evidence)` in PROGRESS, the README and the brief;
- rewrite the Starting state as the Outcome;
- write the report to `docs/research/<date>/<chunk>.md`.

Post one owner check-in on the chunk's issue: what to look at (scenes or places named), what changed, AWS
month-to-date and Claude usage.

If the chunk can't finish in this session, rewrite the Starting state as the hand-off: done, diagnosed with causes,
still owed. The next "deliver <id>" picks it up from there.

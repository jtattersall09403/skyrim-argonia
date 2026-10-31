# Lane records (2026-10-31): the records updated, made to fail the gate when stale, and the move inventory

## Records updated
- PROGRESS rows for 0.0–0.4, 1.1–1.7 and 2.W1–2.W4 rewritten to the current state. The evidence comes from the run
  history merged over every worktree's `out/` (the per-tree `run_batch --owed` disagrees: each tree sees only its own
  runs), plus lane reports game-17 to game-21 and g6-move. Each row cites commits or lane reports.
- Gone: "[from batch] ... game-13", "LOD by the Creation Kit" (xLODGen kept, owner 2026-10-30), the g4dn. The
  respawn rule now reads "until the place is wholly cleared, then never". Machines are named from machines.conf
  (argonia-play = Paris).
- Merged history at 12:00 UTC. Last run red: die-and-recover, menus-quit, ui-sweep (g21-b5) and ui-review.
  Green only once: grow-at-rest, ui-probe, quest-board, world-sample. Everything else is green, mostly several
  times. No chunk past 0.1 is done; the Part 1 exit is one pass of all.yaml.
- Every part README's chunk table has a Status column, and each brief for 0.x, 1.1–1.7 and 2.W1–2.W4 has a
  `**Status.**` line. The placeholders "Written by the agent that closes ..." are replaced. The Part 0, Part 1 and
  1.7 starting states are rewritten to now.
- Left for the ledger lane: the briefs' "L4 [from batch]" acceptance lines (they become checks.md rows) and
  docs/phases/1-core-loop/in-game-owed.md.

## Real time: tools/check_records.py (in `make check` as `records`)
- Checks: one PROGRESS row per README chunk, with the same status word in the README and in the brief's Status
  line; done ⇒ no owed ledger rows; non-todo rows cite evidence; no unknown commit, missing lane report or path,
  unknown machine, bare game-N older than the newest lane-game report, "[from batch]", g4dn or CK LOD.
- Test tools/tests/test_check_records.py: 6 passed. It covers the green tree, a seeded stale row failing on each
  pattern, a status mismatch, an unknown commit, done with an owed ledger row, and the repo itself.
- No checks.md ledger existed at push, so the done-has-no-owed check is skipped, with a note printed.

## Machine inventory: one read-only run on argonia-play-london (12:0x UTC; g21-lod2 running)
- Result: 7 UNARCHIVED, from the replayed classification of the one listing. The script's mod-name match was fixed
  after the run, offline: the first pass compared against the build VM's mod-id folders and flagged 44 manifest mods.
- **Argonia LOD (generated): 622,563,646 bytes, UNARCHIVED.** s3://argonia-private-…/lod/ is empty; g21-lod2 ends
  with `lod.sh archive`.
- Folders no tool makes: argonia-edge, combat-overlay, combat-state, pandora-adopted, pandora-out, ut. Each needs
  archiving or a reason it isn't needed.
- Saves not ours: 8, all in saves/latest.zip.
- CK outputs: only the Papyrus compile (deploy rebuilds it).
- Scratch: 36 loose .ps1/.ini/.tar files, not counted.
- Paris (argonia-play) was not touched.

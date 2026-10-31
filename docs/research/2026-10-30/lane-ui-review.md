# Lane ui-review (2026-10-30/31): our screens seen in game at desktop size, judged by a reader, fixed

Owner's question: "have our new ui screens and things been seen and reviewed?" Journey `tests/journeys/ui-review.yaml`
(scene ui-props) opens each screen through the real actions and keeps a still per step. Off-game stills (L3, the
harness at 1920x1080, 1280x720 and the Magic V5 folded and unfolded) came from `make ui-stills`. Two independent
`reader` passes judged the L3 stills (round 0 and round 1); the in-game stills go to a reader as the last round.

## Stills (for the owner's packet)

In game, 1920x1080, before the fixes (run 20261030T234801) and after round 2 (run 20261031T002055 and the resumed run):
- `out/runs/ui-review/20261030T234801/01-hud-play.png` … `07-journal-closed.png`
- `out/runs/ui-review/20261031T002055/01-hud-play.png` … `13-inventory-closed.png`
- The container, book, sitting and loading stills come from the resumed run (`--from props-found`, job uireview4).
Off game, after the fixes: `out/ui/stills/{dialogue,journal,sitting,hud,chart}/*@{1080p,v5-folded,v5-unfolded}.png`.

## Verdicts and fixes, by screen

| Screen | Reader finding (MAJOR unless marked) | Done |
|---|---|---|
| Dialogue | answer pane mostly empty; the window covered the speaker | window lowered (72vh, 18vh from the top), so the scene shows above it; the answer column narrowed to give topics more width |
| Dialogue | disposition label cream on the fill, hard to read | the label in ink beside a thin bar, lighter trough |
| Dialogue | forced talk: buttons gone, a blank strip, no way out shown | the line "You cannot leave yet." in Goodbye's place |
| Dialogue | 300 topics: no scroll cue | kept: the themed scrollbar and edge shadows show in game; minor row-snap left (P3 final) |
| Dialogue | **Disposition 0 for every speaker in game** | **not fixed here (rules, not views):** `seam::disposition_of` (skse/core/src/seam.cpp:156) calls `disposition::base({}, p)`, and `Speaker::authored_base` defaults to 0 (skse/core/include/argonia/core/disposition.h:18); no world column holds a person's starting regard. Fix at source: a per-person base disposition in the world db (default 50, Morrowind's middle) generated into the speaker data, then read in `disposition_of`; L2 test beside it. Owner-visible: the bar reads empty and the low band may gate topics. |
| Journal | quest name ran into the entry | the quest name on its own line in red clay, a gap below |
| Journal | "1 of 1, leaf 1 of 3" confusing | the folio reads "Pages 1–2 of 6" |
| Journal | Escape did not close it in game | the test's key route (os ESC is lost in menu context, diag3-g15), not the game: closed by `close_menu`, as ui-sweep; pad B and Close work |
| Journal | a long entry fills the left page and spills two lines to the right | left as is: it is how a book flows; paragraph breaks in quest text are the writers' (P2 rolling) |
| Sitting | cost column far from its row, no header, refusals all in red | columns tightened, header "Cost", refusals in soft ink, disabled Buy in faint ink; "No more at this sitting", "1 more level to take later" |
| HUD | minimal, palette right; bars unlabeled | kept (souls-style by design) |
| Chart | sparse labels, no scale | world-track content (2.W4), P2 rolling |
| Vanilla menus (Tween, inventory, container, book) | per the in-game reader round | see below |
| Loading, title | loading from the resumed run; the title is ui-sweep's last step | see below |
| Barter | owed: no merchant record of ours (ui-sweep) | owed |

Gate: `make ui` green; the harness smoke keeps 8 topic rows on the folded phone (the disposition label sits beside
its bar). Commits: 855b7c1/70943b1 (round 1), 628124e/04ead79 (round 2), aa900cc (gate), a83867d (journey).

## In-game reader round

Pending at writing: job uireview4 queued behind game-18's slot; its stills and the reader's verdict are appended here.

## Hand-off (01:55 UTC, context limit)

- uireview4 (the resumed run on argonia-play) cancelled on the coordinator's call after ~30 min queued behind game-18.
- Next lane: launch argonia-play-2 (`tooling/job_guard.sh run --gpu=argonia-play-2 clone2 -- infra/gpu-box/clone.sh
  argonia-play-2`, lane-play2.md), `stack.ps1 on` if Data is bare, `make plugin` then `ARGONIA_PLAY=argonia-play-2 make
  deploy` from a clean worktree at origin/main, then `python3 tools/run_journey.py tests/journeys/ui-review.yaml`
  (whole journey: argonia-play's step saves do not exist there) under `--gpu=argonia-play-2`.
- Hand every still of that run to a `reader` (checklist above), fix, re-shoot; then add the title screen (ui-sweep's
  main-menu step) and the phone sizes in game (the #17 stream harness).
- Open MAJOR outside views: Disposition 0 for every speaker (see the table).
- Terminate the clone fully when done (instance, volume, spot request, alarm); note its hours. No clone launched yet.

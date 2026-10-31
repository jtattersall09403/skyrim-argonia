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

## Lane ui-review2 (2026-10-31, 01:00-03:40 UTC): in game on argonia-play-2

Clone `argonia-play-2` (i-068ccffaa6e41b5d6, g4dn.xlarge spot, launched 00:50 UTC from ami-0e0653a8c139a7441) is
**left running** for the next UI lane (coordinator's call). Data was bare: `stack.ps1 on` laid 22573 files. Deploy:
origin/main c745ef3 (trader + disp-fix) plus round 1 (f1c81b7); its DLL also carries an unproven ShowHUDMessage
deferral, reverted in the repo (see the book crash). About 2.8 h so far, ~$0.75 at $0.26/h.

Clone lessons: the snapshot-backed volume is cold, so a far `moveto` holds the main thread past the bridge's 3 s;
the journey now waits 6 s after each moveto. A fresh worktree needs `tooling/worktree.sh` (links out/), but a view
change needs the worktree's **own** out/ui (`tools/ui_harness/build.py`), then `stack.py stage` + `push` **and a
lay** (`stack.ps1 on`): push alone left Data's chart/main.js at 00:18 (the chart re-shoot showed the old fit).

Stills (for the owner's packet), 1920x1080:
- `/home/ubuntu/wt-uir2/out/runs/ui-review/20261031T030023/01..20-*.png`: round 2 (HUD-under-sheets and notice fixed)
- `/home/ubuntu/wt-uir2/out/runs/ui-review-nobook/20261031T031415/20..23-*.png`: sitting, loading
- `/home/ubuntu/wt-uir2/out/runs/ui-review2-title/25-main-menu.png`: the title
(out/runs is per worktree; copy them to the main tree's out/runs before the worktree is removed.)

| Screen | State after the readers |
|---|---|
| Dialogue (Takes, Livia) | **PASS** (two readers). Disposition reads 25 and 45 (disp-fix holds). Owed outside views: no Persuasion button, because `talk.cpp:201` leaves persuasion unavailable until 2.5. MINOR: keywords linked only in places; service topic ungrouped; empty space in both panes. |
| HUD notice | **FIXED, PASS**: the notice was raised in the conversation (HUD hidden) and expired before play. Notices now stop ageing while our HUD is hidden (`journal::hide/show`, L2 test). |
| HUD over sheets | **FIXED, PASS**: our bars and plaque sat over Barter, Inventory and Container. Fix: `router::covers_hud` (L2), HUD pushed on sheet open and close; the registry's `Container Menu`/`Barter Menu` corrected to the engine names. |
| Activation prompt ("E Talk") | OPEN MAJOR: vanilla white text, no plate. Our prompt exists (hud render.ts) but is not fed; the crosshair row is "restyled". Route: feed our prompt and hide the vanilla rollover clip. |
| Journal | PASS |
| Chart | OPEN MAJOR, fix written and not yet seen: zoom 1 now covers the sheet (geom.ts; `make ui` green). The re-shoot ran the stale lay. Next: lay, then re-shoot. |
| Barter (Livia) | Works (her stock, 300 gold). Same Dear Diary component as inventory and container. |
| Inventory, container, barter | OPEN MAJOR (theme): list text ~10 px in a condensed face; red knot ornament between the names; tri-colour bars with <> caps. Route: SkyUI config font sizes plus retheme's watermark list, done as an install-time recipe (0014). Not views. |
| Tween | OPEN MAJOR (theme): dark vanilla sheet, small sans date and level text, <> level bar, an empty plate under the sheet. |
| Book | OPEN MAJOR, **crash**: 4 of 4 runs crash at the book or its close (SkyrimSE+0EDC8C8, null read; BookMenu and HUDMenu on the stack; it follows "things: ledger read sets flag.lf83.ledger-read"). Not the harness: TAB close crashes as close_menu did. Not the engine notice: deferring ShowHUDMessage did not help. ui-sweep's book passes, but its scene has not started LF83. Next: diagnose MeetThing's read hook under the BookMenu open event when LF83 is live. |
| Sitting | PASS (MINOR: cost unit, low-contrast disabled Buy) |
| Loading | NOT SEEN: the still caught play after the load. Next: a still within the Loading Menu event. |
| Title | OPEN MAJOR (theme): menu words in Skyrim's condensed caps, ~16 px, dim. Title art passes (no map or wordmark). |
| Phones (folded and unfolded) | NOT RUN (time). Steps are written: `infra/stream-client/e2e/steps/ui-review-phone.json`. Run with `ARGONIA_PLAY=argonia-play-2 ARGONIA_DEVICE=v5-folded\|v5-unfolded infra/stream-client/e2e/drive.sh`; quit the game between shapes, and Sunshine must be on (the clone recipe disables it). |

Commits: f1c81b7 (round 1), plus this hand-off with the journey's book-close and book-wait fixes.

Next steps, in order:
1. Lay the views (`stack.ps1 on`), re-shoot the chart.
2. The book crash (above).
3. The activation prompt onto our plate.
4. The theme majors (item-list size, knot, Tween, title font) as one install-time theme pass.
5. The phone sizes; the loading still.
6. Terminate argonia-play-2 when the UI lanes finish: the instance, the spot request, alarm `argonia-play-2-idle`.

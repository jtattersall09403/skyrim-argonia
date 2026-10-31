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

## Lane ui-review3 (2026-10-31, 03:30-04:30 UTC): argonia-play-2, three rounds

Clone **left running** (hand-off at the context limit). ~3.7 h total since 00:50 UTC launch, ~$1.00 at $0.26/h.
Stills (copied to the main tree): `out/runs/ui-review3/20261031T041616/` (round 3, final), `.../040203/` (round 2),
`.../034534/` (round 1), `out/runs/ui-review3/25-main-menu.png` (the title from a fresh launch, not yet read).

| Screen | State after the readers |
|---|---|
| Activation prompt | **FIXED**: our HUD's prompt fed from SKSE's CrosshairRefEvent (`views::prompt_from_activate_text`, L2; `GetActivateText` takes the activated ref) and the seven vanilla rollover clips hidden through the hudPrompt row (`router::kHudClips`, L2; Views line "hidden 11/11"). Log: Talk Livia Varinius, Open Blackwood, Pick Domica Redwort, Rest Camp. Round 2 reader saw the styled plate with keycap (name was the player's then; fixed). Round-3 reader: **PASS** (plate, real names, E or A glyph by device, no vanilla rollover text). |
| Chart | **FIXED** (round 2 reader): full screen on an opaque paper backdrop. MINOR: the right quarter is empty sea, two labels (world-track content, 2.W4). |
| Push without lay | **FIXED**: `stack.py push` runs `stack.ps1 on` when it changed a mod. |
| Font (lists, title, Tween) | **FIXED at source**: `tools/ui_theme/build.py` makes the whole overlay; the font library had gone to `out/ui_theme/fonts`, never staged. Readers: lists and journal now a serif (Pelagiad). |
| Item-list size | OPEN MAJOR: still ~12-13 px after `skyui/config.txt` entry 14→20, label 12→16 (built into the overlay). Next: check which config SkyUI reads under Dear Diary (it may be per-list sections, or `interface/skyui/` from another mod wins), measure in Data. |
| Knot | OPEN MAJOR: a red knot ~14 px in the barter/container name plate at (226,865) between the two names. Not a bitmap (no red bitmap ≤64 px in any Dear Diary, Wood and Paper or SkyUI SWF): a vector shape, likely in bottombar/itemcard. Next: a DefineShape fill recolour/clear step in retheme. Also "X Take All" overprinted in the container footer (MAJOR). |
| Tween | MINOR now: paper sheet, ~20 px text; a stray empty plate at (745-1190, 778-826) and a <> level bar remain. |
| Loading | NOT SEEN: still gameplay with an interior coc and with a far moveto from indoors. Next: take the still inside the Loading Menu open event (a bridge-side screenshot on the event), not after the step's expect. |
| Title | ui-review's pad quit fails (the pause list changed); a fresh `bridge.py launch` + `screenshot` gives the title still (25-main-menu.png, unread). |
| Phones | NOT RUN. Sunshine on the clone not yet enabled; then `ARGONIA_PLAY=argonia-play-2 ARGONIA_DEVICE=v5-folded|v5-unfolded infra/stream-client/e2e/drive.sh infra/stream-client/e2e/steps/ui-review-phone.json`. |
| Persuasion | owed to chunk 2.5 (talk.cpp:201). |

Gate: skse, ui, unit green; lint red is `tools/world_sample.py:296` F841 (another lane's). Worktree `/home/ubuntu/wt-uir3`.

## Lane ui-review4 (2026-10-31, 04:20-05:15 UTC): argonia-play-2, hand-off at the context limit

Clone **left running** (i-068ccffaa6e41b5d6; ~4.4 h since the 00:50 launch, ~$1.15 at $0.26/h). Worktree `/home/ubuntu/wt-uir4`.
Stills: `/home/ubuntu/wt-uir4/out/runs/ui-review/20261031T045235/` (round 1: knot fixed) and `.../20261031T050520/`
(round 2: loading frames `loading-frames-NN.png`, `pause`, `main-menu`, if that run finished; not yet read).

| Screen | State |
|---|---|
| Item-list size | OPEN MAJOR, cause found (research, file reading): **MCM Helper's** `SKI_ConfigMenu.pex` (mods/mcm-helper/Scripts) re-applies SkyUI's size overrides on every load (OnGameReload -> LoadSettings -> ApplyItemListFontSize, medium "14"/"12", icon "18"), which beat config.txt. Round 1 patched SkyUI's BSA copy instead (no effect, and it shadowed MCM Helper's page). Fixed in `tools/ui_theme/pex.py` (now remaps MCM Helper's pex x1.6, 15940 bytes, all keys found); **not yet built, laid or read in game**. Stage is 2560x720, so 14 pt reads 21 px tall but 10.5 px wide. |
| Knot | **FIXED, PASS** (reader, run 045235): retheme recolours DefineShape fills/lines; the plate ornament is dark ink (124,102,69). |
| "X Take All" | OPEN MAJOR: two labels drawn in one footer slot (x383-418, y925-942); the other hints clean. Not diagnosed (containermenu.swf's AS sets "$Take All"; look for a second hint in the same slot). |
| Loading | still loop written (`{burst}`/`{burst_fetch}` actions, `grab.ps1 -Frames -Fps`); step 26 passed in run 050520; frames not read yet. |
| Title | reader: **PASS** on ui-review3/25-main-menu.png (no Nordic element; MINOR: unselected items 17-20 px, grey, low contrast). Quit step split: a `pause` still, then the pad walk; result in run 050520. |
| Phones | NOT RUN. Sunshine is already Running on the clone; `infra/stream-client/build` is linked from the main tree. |

Lessons: `stack.py stage` takes the masters from the worktree's `out/Argonia.esm` (absent: DepthsOfSkyrim and
sirenroot dropped and the base save failed to load); copy the deployed ESM in first. After a lay, `bridge.py launch
--fresh` re-enables our ESMs. `step_saves: true` is now on the journey, so `--from` works. Iterate the loading capture
in a small journey of its own, not the whole one (coordinator).

Next: build (`python -m tools.ui_theme.build ...`), `stack.py stage`, kill, `push`, `launch --fresh`, re-shoot
inventory/barter (`--from barter-talk`), reader; read run 050520's loading frames and title; the Take All overprint;
the phones; then terminate argonia-play-2 (instance, volume, spot request, alarm `argonia-play-2-idle`).

## Lane ui-review5 (2026-10-31, 05:10-06:00 UTC): argonia-play-2, final state for the owner's packet

| Screen | Final state | Stills |
|---|---|---|
| Item lists | **IMPROVED, reader-measured**: MCM Helper's `SKI_ConfigMenu.pex` remapped x1.6 (15940 bytes, built, staged, laid; the 36134-byte SkyUI copy that shadowed MCM Helper's page is gone from the overlay). Rows went from ~12-14 px to cap ~16-18 px, x-height ~12, row pitch ~52 px. The bigger text clipped the "VAL" header, so weight 0.06→0.08 and value 0.06→0.09 (`build.LIST_SIZES`, L2, 65927e5). Re-shoot reader (taken at 2240x2068, the phone stream's mode, so px are not 1080p): rows ~30 px, labels ~22-25 px; TYPE/WGT/VAL all shown but touching; the footer hints collide at that aspect. Re-shoot at 1920x1080 after `launch --fresh` before closing it. | `/home/ubuntu/wt-uir4/out/runs/ui-review5-lists/20261031T051618/` (07-barter, 15-inventory, 18-container); `.../ui-review5-inv/20261031T054704/07-barter.png` (with the widths) |
| Loading | **OPEN MAJOR** (reader, run 050520): only frames 04-05 are a loading screen, and they show Nordic art: a Celtic-knot border (x390-1530, y45-830), a dragon-prow head (x1200-1310, y290-350) and a vanilla skull-and-rune-table model (x440-1100, y290-700). Our HUD stays drawn over it (bars, prompt, gold). Fix: the loading-screen models and border in the theme or the LSCR records, and hide the HUD while the Loading Menu is open. 26/27 caught gameplay. | `/home/ubuntu/wt-uir4/out/runs/ui-review/20261031T050520/loading-frames-04.png`, `-05.png` |
| Pause / quit | **OPEN**: steps 28 and 29 both caught the Journal, not the pause list or the title; the main-menu step failed (no MainMenu event in 30 s). The Journal itself reads 25-30 px; MINOR: "OBJECTIV" clipped over "Level 1" (x1085-1265, y840-880); Celtic-knot ornaments round its title (x838-1500, y170-205), a Nordic element. | `.../20261031T050520/28-pause.png` |
| Title | PASS (ui-review4 reader, ui-review3/25-main-menu.png); phone reader also saw Argonia's own title. | |
| "X Take All" | **OPEN MAJOR, cause narrowed, not fixed**: crop reader saw "Take All" and a second short label drawn at the same x (x381-418) after the X keycap. Research: not our retheme (containermenu.swf differs only in tag 83; bottombar only in four recoloured shapes; no DefineEditText touched; Pelagiad advances sane). ContainerMenu.updateButtons binds both `$Take All` and `$Store`/`$Give` to XButton, so two hints share the slot (upstream SkyUI/Dear Diary). Next: the same scene with Dear Diary's SWFs alone; if it overprints there too, drop one hint in a containermenu AS patch. | `/home/ubuntu/wt-uir4/out/runs/ui-review5-lists/20261031T051618/18-container.png` |
| Phones | **RUN, OPEN MAJOR**: the stream is live in both shapes. Fixes: the game must be launched by `bridge.py launch` first (killing it let Sunshine start a bare game: vanilla Bethesda menu); the steps closed the console after `load` (load closes it itself), so `bat ui-props` never ran (fixed in ui-review-phone.json). After the fix the player reaches the marsh, but dialogue, journal and Tween never open from the phone inputs, and the console overlay text stays on. Folded: the game picture is only the centre strip (x518-1480 of 2000), sticks and ABXY in the side bars; R3 lies over the title's Continue. Unfolded reader: HUD bars under LT/LB; journal showed an empty book page with its tabs under the stick and R3; Tween live, ~10-12 CSS px, the right stick over the level bar. Next: a touch layout that keeps clear of the menus' corners, and phone steps that open each menu reliably. | `/home/ubuntu/wt-uir4/out/runs/ui-review5-phone/folded3/`, `.../unfolded3/` |

Note: after the phone runs, the journey's `close_menu BarterMenu` failed (none of B, ESC, TAB closed it); a left-over stream session may hold input. The stream also leaves the game at its resolution (2240x2068): relaunch before the next journey.

Clone argonia-play-2 **terminated** at the end of this lane (instance, volume, spot request, alarm): ~5.2 h since the 00:50 launch, ~$1.35 (g4dn.xlarge spot $0.2455/h plus 150 GB gp3).

## Lane phone-take (2026-10-31, build VM): the phone and "Take All" majors diagnosed

**Phones: the cause is the steps, not the input path.** The reader read the ui-review5 stills: in all four folded
stills the developer console is open (its last line is the bat's `player.moveto`); in the unfolded run the console is
closed, and Back opened our journal and Start opened the Tween menu from the phone (both stills show them). So touch and
pad events reach Sunshine and the game window has focus. The bridge's per-key route (protocol/input.cpp) only steers
input the bridge injects, so it cannot stop Sunshine's OS input. The failures come from the console toggles in
ui-review-phone.json falling out of step (Backquote opens or closes the console, and `load` and the cell-changing
moveto close it themselves). The setangle and activate lines were typed into the game. Dialogue never opened, and in
the folded run the taps went to an open console. Fix: drive.mjs gains a `scene` step that loads the save and runs the
scene through the bridge (Runner.apply_scene). The new scene `ui-phone` is ui-props plus the player facing the Takes.
The phone steps use no console and open dialogue with the phone's own A.

**Overlay:** the folded layout puts Back and Start in the side bands as well (Back at the foot of the left band,
Start under RB), so nothing covers the Journal's tabs. The unfolded layout keeps every control in a strip above and
below the picture, and the stream asks for the picture between the strips (`stripHeight`, `pictureCss`). At 784x724
that is 784x388. Every target is at least 44 px (`npm test`, 27 of 27). Cost: the unfolded picture is now 2:1, not the
full near-square screen.

**"X Take All": the bindings are not the cause.** A disassembly of containermenu.swf's updateButtons (our built copy;
the AS is upstream SkyUI as Dear Diary ships it) gives these bindings. In the container branch: `$Take` goes on Activate
and `$Take All` on XButton (only when not in NPC mode), then a jump past the inventory branch. `$Store`/`$Give` sit in
the inventory branch on Activate, not X. So no two hints share X, and no binding or text patch applies. The second label
at the same x is more likely a ButtonPanel layout fault: the next hint is placed from a text width measured as about 0
(our font library or the x1.6 sizes at 2240x2068). This is unproven without the game.

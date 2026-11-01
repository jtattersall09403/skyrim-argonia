# Lane 1.12-menus (owner look 1): Tab, Esc, Wait and the journal from the panes

Batch: out/batch/menus/20261101T135219 (argonia-play, one deploy of this tree). menus-look 18/19 steps ok,
menus-quit 5/5, pad-panes 0/1 (see Red). make check green (497 passed).

## Root causes (why 1.12 passed while the owner saw it broken)
- **Tab flash.** padcursor's TweenSink swapped Dear Diary's TweenMenu for InventoryMenu through a task and the UI
  queue, so the tween drew for several frames first. No check looked at the frames between the two screens.
  Fix: the tween's movie is hidden (`uiMovie->SetVisible(false)`) inside the opening event, before it first draws.
- **Esc was Dear Diary's.** "Who draws each screen" named our System pane, but 1.12 only switched Dear Diary's
  Journal Menu to its System tab (SystemTab). Its Quests tab stayed, and the journeys judged "Journal Menu opened"
  as the evidence. Fix: menus.cpp hides the Journal Menu's movie when it opens and opens our `system` view
  (PrismaUI, frame tokens). Quit to the main menu and quit to the desktop call the Journal's own FxDelegate
  handlers (the suspend save is kept). Settings and Load show the movie and press the page's own category entry.
  Backing out to the main list hides it again and our pane returns.
- **Wait was Dear Diary's.** DESIGN.md said "retheme recipe → frame style" for sleep/wait, but no such recipe was
  ever built (retheme only makes paper). Fix: our `wait` view sits over the hidden Sleep/Wait Menu. Its pick sets
  the movie's own HoursSlider and calls its onOKPress, so the engine runs the wait (log: "wait 2 h through").
- **The journal from the panes.** Wind UI's taskbar Journal toggles its own window, which no setting hides
  (windui.md). Fix: a left click on that taskbar cell (pad::on_taskbar_journal, measured at 1080p and scaled with
  the screen height) is taken from Wind UI, which never sees the press, and opens our book, as J does.

## Rows
- Esc: proven. Stills 08, 10. Reader: a frame pane with four entries and no Quests.
- Journal from the panes: proven. Stills 03 and 06 show the same paper book. Reader: no Wind UI window.
- Tab: owed. Log "Dear Diary's tween hidden at its opening" is present and the still shows Wind UI's windows.
  But the L5 burst missed the press (40 frames at 20 fps all before Tab). The journey now takes 10 fps after a
  2 s lead. Re-run needed.
- Sweep: owed. Wait passes the reader (12) and container/barter are Wind UI's. Left:
  1. Settings and Load are still Dear Diary's parchment page, with its Quests tab visible (09). It needs the page's
     tab bar hidden or our own settings.
  2. Lockpicking was not reached (the book's Esc fell through; the journey now closes the book with close_menu).
  3. Message boxes were not triggered.
  4. Our pane has no focus or hover polish (reader).
  5. The slider looks native (reader).

## Red / for others
- pad-panes start-opens-windows: Start opened the tween, it was hidden and swapped, and WindUIMenu opened and then
  closed at once. It passed before this lane. Suspect: the hidden tween with the pad's Start release. Needs one run.
- Taskbar geometry is proven only at 1920x1080; the folded V5 is unmeasured.
- system-perks/ui-sweep expect Dear Diary's System page reader stills; their reader lists are now stale.

## Part 2 (hand-over agent, 2026-11-01 afternoon)

Batches (argonia-play-ie / argonia-play, pool pick, this tree deployed each time): 20261101T143721, 20261101T150013,
20261101T151959 under out/batch/menus/.

### 1. The Start regression: green, cause not pinned
- pad-panes passed in full in 20261101T143721 and 20261101T151959 (26/26 bar touch, owed); system-perks and
  menus-quit passed both times.
- The change: TweenSink now holds the tween -> InventoryMenu swap until the pad's Start is let go (`g_start_held`, at
  most 1 s), and logs a warning when Wind UI's windows close within 2 s of the tween. In both passing runs the swap
  logged "0 ms after its opening", meaning Start was already up, and the warning never fired. So the guard never had
  to act. The 135219 failure was not reproduced and may have been a one-off race. The guard and its log line stay so
  that a repeat would show it. Ledger row "The system menu ... opens from play by pad and keyboard" was set back to
  owed citing 135219, then proven on the 151959 pass.

### 2. Tab (row owed until the reader's verdict below)
- 143721's burst (40 frames at 10 fps) ended before Wind UI drew: the tween opened at 28.348 s and the windows opened
  at 30.136 s, 1.8 s later. Its reader: no Dear Diary picker in any frame, but no windows either. The burst is now
  40 frames at 8 fps with a 5 s wait. 151959's burst is in 04-menus-look-1-20261101T152726/tab-*.png.
- The 1.8 s of plain play between Tab and Wind UI's windows is Wind UI's own opening cost (the item lane's windows).

### 3. The sweep: owed
- Settings and Load: the tab bar is hidden (QuestsTab, StatsTab, SystemTab, previous/nextTabButton) and the page is
  colour-transformed by AS2 Color objects (menus.cpp FrameMovie/Tint). Dear Diary's files are not touched. The first
  pass (whole Menu_mc inverted) gave teal paper and a light screen dimmer (143721 09). The second pass (each child
  tinted, Background flat) gave a dark green-black ground, but the category list and the left menu came out dark on
  dark. The Mod configuration side list stays on parchment (151959 09). The approach needs one more tuning pass:
  per-child maps (only text children inverted), and the MCM list clip found. The alternative is our own Settings and
  Load views.
- Load's return: the watcher came back at once (state 0 -> 0 at the press). It now waits until the page has left the
  main list (log "left and back"). load-back passes.
- Message boxes: the bridge's new `core MessageBox <text>` (RE::DebugMessageBox, Debug.MessageBox's route; whitelist
  plus test) and MessageBoxMenu are put in the frame style at opening. Not yet reached: the journey stops earlier, at
  lockpicking.
- Lockpicking: still not reached. `lock 25` followed by `activate player` on the lockbox opened no Lockpicking Menu
  (151959 21 shows play). Find out why: check the ref, the lock level, and lockpicks in the scene.
- Polish done, not yet read: the first System entry is focused at opening, and the marked row has a gilt lozenge on
  each side plus a lit trim. The Wait slider has a frame-style groove and a lozenge thumb (webkit and moz pseudo
  elements).

### 4. Journeys refreshed
- system-perks: its Esc step is now our System pane (passes). ui-sweep: the tween step expects Wind UI's windows and
  Tab's close; Esc expects our pane; inventory-closed expects the windows' close, and magic-closed expects our magic
  pane's close. ui-sweep now stops at favorite-one: "dev-favorite: no form ARG_Weap_SteelSword". That is the
  1.12-items lane's renamed kit, not this lane's.

### Left for the next agent
- The tuning pass on FrameMovie for Settings and Load (and the MCM list), then message box and lockpicking stills.
- One reader over the whole sweep, then close the sweep row.
- The Tab row: close it if 151959's burst reader is clean (see the report's return).

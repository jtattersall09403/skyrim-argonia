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

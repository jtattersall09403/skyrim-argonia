# OpenMW on Android: mobile UI reference

Not lore: a UI reference for the 2.9b mobile walk items (walk/run touch
band, dialogue unfolded, trade, effects stack, touch controls). Era policy
(decision 0002) does not apply; the confidence marks below do.

**Confidence marks:** DOC = stated in project docs or source strings;
FORUM = developer or user forum post, old (about 2018-2019); INFERRED =
reasoned from how desktop OpenMW works, no Android page says it; GAP =
searched, nothing found. No screenshot was readable by this lane (the
pages that hold them returned 403/429 or only text); no screenshot-based
fact is claimed. The planner reads no images; a `reader` could describe
the screenshots on https://omw.xyz.is/controls.html (ui.png) if wanted.

## Which port
The Android port is community-made: xyzz/openmw-android (archived, "no
longer under development"; Google Play and F-Droid stable and nightly
builds; DOC https://github.com/xyzz/openmw-android). Its releases are
engine bumps and crash fixes (DOC .../releases). I found no official
OpenMW-project Android release (the 0.49 and 0.50 release posts returned
nothing on Android; GAP). Info site: https://omw.xyz.is (DOC).

## 1. Dialogue, barter, inventory, spells, magic-effects windows
- OpenMW draws Morrowind's own desktop windows (resizable, movable, pinnable
  panes) inside a GL surface; the port adds no phone-specific window layout
  (INFERRED: no Android doc, string or release note mentions one; GAP).
- The only phone lever is scale. "UI scaling factor" (pref_uiScaling, with an
  "Auto (x.xx)" choice) and "Custom resolution" (Normal 1x, Double 2x, Half
  0.5x) (DOC strings.xml:
  https://github.com/xyzz/openmw-android/blob/master/app/src/main/res/values/strings.xml).
  FAQ: "if menus or text are too small, raise GUI scaling factor to 2 or
  higher" (DOC https://omw.xyz.is/faq.html). Desktop engine setting: scaling
  factor 0.5 to 8.0, default 1.0; font size 12 to 18, default 16; menu
  transparency 0.0 to 1.0, default 0.84; "stretch menu background" off means
  black bars (DOC https://openmw.readthedocs.io/en/stable/reference/modding/settings/GUI.html).
- Consequence of one scale for all windows: a user raising scale to read the
  status bars made every other window too large, with no per-window scale
  (FORUM https://forum.openmw.org/viewtopic.php?t=8275, desktop report).
- Windows do not fill the screen; they keep Morrowind's proportions and the
  player drags or resizes them (INFERRED). Dialogue: text pane left, topics
  list right, services above topics (the owner's reference image; DOC for
  the layout in Morrowind itself). Barter is a second window with the two
  item lists side by side and a Barter/Offer/Cancel row (INFERRED from
  Morrowind; no Android page).
- Mouse in menus: "Mouse mode in menus" Hybrid / Relative joystick controls /
  Absolute touch controls (DOC strings.xml). Touch mode = tap is the click,
  cursor hidden; Joystick mode = only the right stick moves a laptop-style
  cursor; Hybrid = both (FORUM https://forum.openmw.org/viewtopic.php?start=250&t=5626;
  DOC https://omw.xyz.is/faq.html: "the touchscreen acts as the mouse: tap
  where you want to click; the right stick moves a cursor, useful when a
  button covers your target"). A button covering a menu target is a known
  problem the port answers with a second pointing device, not a layout.

## 2. Touch controls
- Default layout (DOC FAQ/controls page + forum): left analog stick moves
  (WASD), right stick is mouse look; on-screen buttons send keys; more
  buttons hide in toggled groups ("Enable Quick Keys", "Enable FN keys",
  "Always show top-bar icons", "Hide on-screen buttons") (DOC strings.xml;
  FORUM start=250&t=5626). Three-finger touch opens the keyboard (FORUM).
- Editing: "On-screen controls..." in the launcher; drag buttons; Size+/-
  and Alpha+/- per button; "Reset to defaults" (DOC strings.xml; DOC faq).
  "Virtual touchpad sensitivity" is a setting (DOC strings.xml).
- Run: the port once had a run button and the developer removed it as
  "useless" while changing the default layout and adding camera control
  while the attack button is held (FORUM start=250&t=5626). Run is then the
  engine's: stick deflection scales speed as on a gamepad, with Morrowind's
  Always Run toggle and Autorun key reachable as buttons (INFERRED for the
  stick behaviour; the Autorun button is FORUM-attested as a separate
  button). Engine "always run" default false; joystick dead zone 0.0 to 0.5,
  default 0.1 (DOC
  https://openmw.readthedocs.io/en/stable/reference/modding/settings/input.html).
  A stuck left stick was fixed by resetting mappings (stick is a gamepad
  analog by default) and by disabling the system three-finger gesture
  (FORUM https://forum.openmw.org/viewtopic.php?t=5427, via search summary).
- Combat and casting: no cast-specific touch control exists. Morrowind
  casting is "ready magic" (key) then "use" (attack button); both are plain
  mappable key buttons (INFERRED). Quick Keys hold the numbered hotkeys that
  select a bound spell or item (INFERRED from the option name). Hand
  labels are the player's own choice of button text (DOC: buttons are
  user-configurable; GAP on default labels).
- Gamepads work natively and remap in the in-game settings (DOC faq).

## 3. Active effects and notifications on a small screen
- Nothing phone-specific found (GAP). The HUD is Morrowind's: bottom-left
  health/magicka/fatigue bars and a row of effect icons, the Magic window's
  effects list opened on demand; messages are short toasts at the screen
  edge (INFERRED, desktop). Scaling is global (section 1), so the effect
  icons grow with everything else. Subtitles are a setting, off by default
  (DOC GUI settings).

## 4. Wide and foldable screens
- Nothing found: no doc, string or release note mentions foldables, aspect
  ratios or safe areas (GAP). The only related controls are "Custom
  resolution" (render scale) and "stretch menu background" (centre with
  black bars versus stretch) (DOC). A fold's 905 css px square-ish screen
  would simply get the same scaled windows.

## What this means for our screens
What we have: three viewports (phone 844x390 css, fold-inner 905x835,
desktop) with layouts windows / pages / spread (packages/ui/src/viewport.ts
:35-79); touch stick with travel 0.36 of its width and a sprint band at
0.9 deflection entering, 0.8 leaving (packages/game-core/src/io/input.ts
:109-110, packages/world-render/src/player/TouchControls.tsx:15,
:38-41); labelled buttons ACTIVATE, ROLL/SPRINT, JUMP, ATTACK/CAST,
BLOCK/OFF HAND, LOCK, MORE (text-catalogue entries.ts:831-849).
1. **Evidence is thin where we need it most.** OpenMW Android has no phone
   layout for dialogue, trade or effects; it scales desktop windows and
   gives a cursor fallback. Our pages/spread layout already goes further.
   Treat it as a floor, not a pattern to copy. Do not cite it as support
   for a specific width.
2. **Walk/run.** OpenMW's lesson is negative: a dedicated run button was
   removed as useless and run rides stick deflection (plus a toggle and a
   dead zone, default 0.1). Our band (outer 10 percent sprints, 0.8 to
   keep) is the same idea. Recommendation: keep the band, widen it only if
   the walk shows thumbs missing it (outer 0.25 of travel: enter 0.75,
   leave 0.65, still hysteretic), and add a latch for staying in a run
   (stick pushed past the ring and released into the ring keeps run, or a
   tap on the stick's centre toggles "always run" as the engine's setting
   does) rather than a new button. Add a dead zone of 0.1 on the inner
   edge if the nub drifts. All of this is constants in input.ts and the
   existing ring; no art.
3. **Dialogue unfolded.** OpenMW keeps text left, topics right with
   services above (the owner's reference). Our fold-inner `spread` already
   spans both pages (w0 mechanism 4: screens.css:14-21). Keep services as a
   row above the topics column, text left; at phone `pages`, services row
   then topics on page one, speech on page two. Pointer rule from OpenMW:
   no on-screen button may sit over a menu target, so hide the HUD touch
   controls while a sheet is open.
4. **Trade.** One window with two lists and an Offer row (Morrowind);
   at fold-inner two lists side by side, at phone one list per page with
   the totals and the Offer button held in a strip that is on both pages.
5. **Effects stack.** OpenMW gives no small-screen answer. Use our own
   rule: a row of icons at the HUD edge, max N visible then a "+n" tail,
   full list in the Magic sheet; scale with the band, never its own size.
6. **Touch casting labels.** OpenMW has none; ours already turn ATTACK into
   CAST when that hand holds a spell (entries.ts:846-847). Add the spell's
   short name under CAST so the player knows what is bound, within the same
   button; text only.
7. **UI scale.** The port's one global scale is the cause of the status-bar
   complaint; our tokens scale per viewport kind, which avoids it. Keep
   per-kind scale; do not add a user-wide factor unless a walk asks.

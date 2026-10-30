# Diagnosis: HUD list removals and the Tween menu (game-12, 20261030T133637)

## 1. smoke / ui-probe: "vanilla-hud hidden 4/4, 0 out of HudElements (22 listed)"

CLASS: report counts one call, not the state (code: the Views line; journey expectation rides on it).

ROOT CAUSE: `HideVanillaHud` (skse/ArgoniaCore/src/views.cpp:159-222) runs on every HUD Menu opening
(views.cpp:227-232, HudMenuSink) and every load (views.cpp:407, ViewsGameReady). `listed` (views.cpp:203,215) counts
only what *this* call removed and `g_vanilla_hud` is overwritten each time (views.cpp:218). The first call removes
the 4 entries; every later call finds none left and writes "0 out of". Evidence in the same line:
- "modes cleared 0" while the visited members of Health are `HealthMeter_mc,HealthPenaltyMeter_mc,argoniaHidden,
  PlayReverse,Lock,PlayForward` - no mode members, and our `argoniaHidden` mark is already present: an earlier call
  already deleted the modes and marked the clip. The removal by mark (router.cpp:37) would fire if a marked clip were
  still in the list, so the 22 listed entries hold none of the 4 clips.
- All 12 Views lines across out/batch read exactly "0 out of HudElements (22 listed), modes cleared 0": always a
  repeat call. Not timing (list exists: 22 entries), not the mechanism (the removal works; its count is lost).

FIX (code): report the state, not the delta. Count clips found that are absent from the list after the pass:
```diff
-    for (auto i : ac::router::hud_list_removals(entries, clips)) listed += list.RemoveElement(i);
+    for (auto i : ac::router::hud_list_removals(entries, clips)) list.RemoveElement(i);
+    // out = hidden clips no longer in the list (this call's removals plus earlier calls')
+    for (const auto& f : found) {
+      bool in = false;
+      for (std::uint32_t i = 0, n = list.GetArraySize(); i < n; ++i) { RE::GFxValue el; in |= list.GetElement(i, &el) && el == f; }
+      listed += !in;
+    }
```
(and likewise "modes cleared" -> "modes absent": count clips with no kHudModes member after the pass). Journey
tests/journeys/ui-probe.yaml:28 stays as is ("4 out of HudElements" then means the state). Optional: log the
first-call removal count so the delta stays visible in ArgoniaCore.log.

RE-PROVE: run ui-probe alone; its Views step must read "4 out of HudElements".

## 2. menus-quit: "no menu event matching 'TweenMenu' since the step began (1 menu events)"

CLASS: journey timing (input lands during the scene's cell move), not the sink, not the router.

ROOT CAUSE: scene first-place ends with `player.moveto 100008E9` (tests/scenes/first-place.txt, last line), a
loading screen; run_journey.py:210-211 waits a fixed `time.sleep(2)` after `bat`, then step 1 presses TAB at once.
The key lands while the load/fade holds input, so the Tween menu never opens. Evidence:
- The still 01-tween-stays.png (read by a reader agent): plain gameplay, HUD only, no Tween menu, no loading screen
  - i.e. the load finished after the TAB.
- The single menu event in the step is the load's own (Loading/Fader), consistent with the move ending inside it.
- The bridge sink is unfiltered (skse/ArgoniaBridge/src/ep_events.cpp:66-68, registered :149): any TweenMenu open
  would be recorded. The router lists TweenMenu as `restyled` (data/router/surfaces.json:391-402,
  router_table.h:78): the engine keeps it, no handler, so nothing suppresses it.

FIX (tools, at source): replace the fixed 2 s sleep with a wait for the load to finish, so every journey after a
moveto/coc scene is safe:
```diff
             out = self.b.call("console", f"bat {scene}")["output"]
-            time.sleep(2)  # a coc in the scene loads a cell
+            self.wait_menu_closed("Loading Menu", timeout=30)  # a coc/moveto loads a cell; input before it is lost
+            time.sleep(1)  # the fade-in
             return out
```
(wait_menu_closed: poll the bridge's menu events for `Loading Menu` opening:false, or the `ui` read showing no
Loading Menu/Fader Menu.) Cheaper stopgap in the journey: `do: [{wait: 3}, {key: "TAB 120"}, {wait: 5}]`.

RE-PROVE: run menus-quit alone; step tween-stays must see a TweenMenu opening:true event.

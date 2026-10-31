# 0017: One coherent Argonian UI, Morrowind in spirit and good by today's standards; the approach is chosen with the owner

**Status:** decided 2026-10-27; the approach as it stands was chosen with the owner on 2026-10-31 (the 1.12 grilling):
Wind UI is the in-game base, under our own Argonian patch, with our own views where Wind UI stops or where the game
needs ours. Earlier owner rulings: "our own new original UI… performing the same functions broadly as their Skyrim
equivalents but looking completely different, like Morrowind versions but adapted for our game's theme"; "HUD I want
to be our own new original version"; the approach left open to reuse ("adapting the threejs work or adapting skyrim's
UI or OpenMW's or indeed anything else").

## The goals (owner, 2026-10-28, in their order)

1. **Morrowind-style dialogue:**
   - branching topics, with Morrowind-level numbers of topics per person (far more than Skyrim or Oblivion);
   - persuasion we can customise (admire, intimidate, taunt, bribe and our own).
2. **A Morrowind-style pause menu:**
   - its several windows (map, inventory, magic, stats) open together;
   - on desktop, each window **draggable and resizable, remembered between sessions**, as in Morrowind ("I loved
     that");
   - on the phone and with a gamepad, a layout that keeps the same windows and works by touch and pad.
3. **One coherent design system for the whole game:**
   - every screen, the HUD, popups and transitions look like one design, never a mishmash;
   - thematic for Argonia, with no accidental Nordic touches (decision 0006).
4. **It looks good.** That is judged with the owner in rounds. Modern styling that Skyrim's UI mods brought, and
   that neither Morrowind nor the old three.js UI had, is studied and used where it helps. Examples: typography,
   spacing and hierarchy, motion, depth and blur, controller-first focus.

These join the standing rules:
- the whole game is playable by touch (0.0);
- in normal play the player never sees a vanilla Skyrim screen (§4);
- Pelagiad everywhere;
- the HUD is our own;
- assets have clean provenance (§5).

## Decision

1. **The front door is parchment.** The main menu (continue, new game, load) is Dear Diary (23010) under our retheme
   recipe (`tools/ui_theme/retheme.py`) with the Argonia title (1.2 §a). The loading screens are Skyrim's classic
   ones, each a 3D model from our stack with Argonia facts in our font (1.9).
2. **In play, Wind UI (Nexus 196534) is the base** for every menu it covers: Morrowind's windows open together,
   draggable, resizable and remembered (goal 2, met by reuse, 0010 route 2). Its own escape to Skyrim's menus is
   switched off. Facts: `docs/research/2026-10-31/windui.md`.
3. **Our Argonian patch sits on top**, built at install where it derives from others' files (0014):
   - a light retint of Wind UI's frames toward the owner's reference;
   - our parchment chart in the map pane (no fast travel from it, no quest markers);
   - our paper book in the journal window (no "show on map");
   - our sheet and vastei in the stats pane; perks visible and taken there, reworded for the Nordic review;
   - our own System pane (settings, load, quit).
4. **Our own views** (PrismaUI, §0 below) draw what Wind UI does not: the Morrowind dialogue window in the panes' frame
   style, our HUD with its top-right minimap and compass rose, and the chart and the book where Wind UI's windows
   cannot hold them. They speak the typed message schema (`ui/schema/`) to ArgoniaCore and hold no game rules.
5. **Every device:** keyboard and mouse, touch (Wind UI's full-screen one-pane mode on small screens) and the GameSir
   pad (Wind UI's pad support, else our focus navigation: the bumpers cycle panes, the d-pad or left stick moves
   within one, the triggers zoom the map and the right stick pans it). The input map is in 1.12's brief and may be
   changed per device where it reads better.
6. **One design system, kept by one designer.** A design agent sees every screen in the game (front door, loading,
   panes, dialogue, HUD, notices, books), renders them off game at four viewports, tunes the shared tokens and the
   patch with small changes until they read as one design, then proves them in game. The tokens and the UI map live in
   `ui/DESIGN.md`. In normal play the player never sees a vanilla Skyrim screen: each engine leftover is replaced,
   suppressed or restyled.
7. **Assets:** only clean provenance. Pelagiad (OFL); our Fal-made glyphs and the owner's flourishes; Bethesda's and
   other mods' art is never committed, only recoloured on the player's machine by our recipes.
8. **OpenMW and Morrowind are references for structure and behaviour, never art.**

## Consequences

- 1.12 builds all of this for the first place; 2.2 brings each later system's screens onto it as they land; 3.1 the
  front door's settings and controls.
- Wind UI is a single-author beta: pinned and archived privately; if it breaks, our views stand in pane by pane.
- PrismaUI is a single-author dependency too: pinned, with each view's fallback named in §0.

## 1.2 §0 record: what draws our own views (to fill from the probe)

The planner owns this choice (owner ruling, 2026-10-30). The candidate built first is **PrismaUI 1.5.1**, because our
four views already exist as web views (L3 green) and the binding is built (lane ui-live, 2026-10-30):
- `skse/ArgoniaCore/src/views.cpp` calls PrismaUI's published API through our own declaration of it (`prisma_api.h`);
- the host's rules are `skse/core` views (L2), so a Scaleform adapter would replace only that file;
- the bundle is made at install (`tools/ui_harness/build.py`) and laid by `stack.py` as `argonia-views`.

**The map.** Our chart is drawn by us and shown in Wind UI's map pane (1.12 §2 picks how); FWMF's chart stays laid as
the fallback. Two reasons:
- the revealed layer is per visited cell and place markers appear only on discovery, which a static texture cannot show;
- one technology for our own screens keeps one input model: pad, keys and touch through `nav.ts`.

If PrismaUI does not load, the map handler is never registered and the M key opens FWMF's map.

**What decides** (`tests/journeys/ui-probe.yaml`, run by the game lane). PrismaUI is chosen when all of these hold:
1. `bound`: PrismaUI's API answers on 1.7.104 and all five pages report DOM ready;
2. `frames-open`: the p99 frame time with the 300-topic window open is within the 0.2 §d bar (≤ 22.2 ms). The cost is
   the open p50 minus the closed p50, and it should be ≤ 1.0 ms;
3. the L5 clip of `scroll` shows no hitch, and the `filter` still shows the 13 topics of "29";
4. `chart-reopen` comes back to the view where it was left; `remembered` does the same after a relaunch, once the
   runner can relaunch;
5. J and the pad's Back open our journal, and Escape still opens the System tab;
6. a reader passes the stills: Pelagiad, no vanilla menu behind, no flash.

Scaleform is chosen when 1 fails (PrismaUI will not load, or the API is refused), or when 2 fails and a profile
shows the cost is the web view itself rather than our page.

**The switch cost, if Scaleform:**
- each of the five views is re-authored as an SWF (render and glue). JPEXS needs Java, which the build VM lacks, so
  the SWFs are written by our own writer, as the font library is (`tools/ui_theme`);
- `views.cpp`'s ops become a custom `IMenu` per view with `GFxValue::Invoke` for the push, and an `ExternalInterface`
  handler for the intents;
- `ui/schema`, `skse/core` (the rules and the host's ops), the router and the journey are unchanged;
- goal 2's draggable, remembered windows would have to be built in ActionScript.

**Filled from the probe** (the game lane's run; the planner writes the choice here and in 1.2's brief):

| Measure | Value | Bar |
|---|---|---|
| PrismaUI bound, pages ready | | all five |
| frame time closed p50 / p99 (ms) | | |
| frame time open p50 / p99 (ms) | | p99 ≤ 22.2 |
| open − closed p50 (ms) | | ≤ 1.0 |
| scroll clip: hitch seen | | none |
| chart remembered (reopen / relaunch) | | both |
| journal key, Escape kept | | both |
| **Choice** | | |

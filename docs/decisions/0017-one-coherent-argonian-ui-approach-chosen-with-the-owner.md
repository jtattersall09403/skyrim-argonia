# 0017: One coherent Argonian UI, Morrowind in spirit and good by today's standards; the approach is chosen with the owner

**Status:** decided 2026-10-27, rewritten 2026-10-28; 2026-10-29 [0027](0027-build-in-the-order-of-the-usps.md) §5
added the two-stage build (stage one in 1.2: the font, a paper theme, the dialogue window and the journal; stage
two in 2.2, 3.1, 3.2: everything else) as 1.2 §0's standing recommendation; the goals and the choice with the owner
are unchanged. Earlier owner rulings: "our own new original UI…
performing the same functions broadly as their Skyrim equivalents but looking completely different, like
Morrowind versions but adapted for our game's theme"; "HUD I want to be our own new original version". On
2026-10-28 the owner opened the approach: "I am open to either adapting the threejs work or adapting skyrim's UI
or OpenMW's or indeed anything else. I will want the agent building/overhauling the UI to reason over possible
options and work with me to choose the best approach."

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

1. **The approach is chosen in spike 1.2 §0 (0.2), with the owner.** The UI agent sets out the options, reasons
   over them against the goals, prototypes the hardest capability in game, and shows the owner mock-ups. The
   owner chooses. Candidates include, without limit:
   - **the old React design system in PrismaUI** (web views over Skyrim; the owner ruled the old dialogue UI a
     foundation to improve);
   - **Skyrim's own Scaleform menus restyled**, as SkyUI and its successors do;
   - **tes4skyrim's MorrowindRuntime menu** as the dialogue base, restyled with our own art, since its art comes
     from a Morrowind install we do not own;
   - **OpenMW's window layouts and behaviour** as the structural model for any of these;
   - **hybrids**, such as web views for the windowed screens and native menus where the engine owns the job.

   Until 1.2 §0 chooses, the plan names PrismaUI views as the working assumption. If 1.2 §0 chooses otherwise, the
   planner rewrites the briefs that name PrismaUI. That is a change of method, applied without a further call.
2. **The look is worked through with the owner in rounds** (1.2 §a). The rounds cover a study of modern Skyrim UI
   mods and current game UI; then mood boards; then the design language as tokens (type scale, colour, spacing,
   window chrome, motion, focus states); then the three hardest screens in it. That language is written down
   once and every screen composes it.
3. **Data layer:** a typed message schema (`ui/schema/`) between the views and ArgoniaCore, whatever the
   technology. Views show state and send actions, and hold no game rules.
4. **The UI is designed and checked as one whole.**
   - A UI map lists every screen, overlay, popup, notification and the transitions between them: opening,
     closing, hand-offs to and from gameplay, loading, death, sleeping, dialogue entry and exit.
   - The rule: **in normal play the player never sees a vanilla Skyrim screen.** Engine-owned leftovers (message
     boxes, "you cannot sleep now", quest and discovery notifications, tutorial popups, activation prompts, the
     loading menu, the console) are suppressed, replaced or restyled.
   - One UI lane designs holistically. Each transition gets an L5 clip (reason: motion and hand-off cannot be
     judged from stills), judged by readers, then the owner. 2.2 §a and 3.1 hold the work.
5. **Assets:** only assets with clean provenance come across.
   - `Pelagiad.woff` with `Pelagiad-OFL.txt`: OFL, import.
   - The Black Marsh map glyphs and the spell-school, status and deck-tab symbols (Fal-made, traced): import.
   - Shapes from Skyrim's own HUD file (`hudmenu.gfx`: sneak eye, map pins, button glyphs) are Bethesda's. They
     are **not committed**: the installer extracts them from the player's own `Skyrim - Interface.bsa`
     (decision 0014).
   - The trim flourishes (`flourish-*.webp`, made by the owner with ChatGPT): our own art, import, with a
     sourcing-register row.
6. **OpenMW is consulted for structure and behaviour, never art.** A research pass in 1.2 §0 reads its window
   layouts and how its windows drag, resize and persist, along with Morrowind's own screens. It writes a gap
   analysis against the old UI. Mod frameworks (SkyUI, Infinity UI, TrueHUD and the rest) are used where they
   save engineering or carry the chosen approach.

## Consequences

- 0.2 gains G11. 1.3 §b proves the dialogue *engine* (MorrowindRuntime first) behind a minimal window; the window's
  final technology and look follow 1.2 §0 and 1.2.
- 1.2 builds the design system in the chosen approach, after the look rounds; 2.2 and 3.1 build from it.
- The PrismaUI risk (0001 §2) stands while it is the working assumption: pin its version early and keep a
  fallback per screen.

## 1.2 §0 record: PrismaUI or Scaleform (to fill from the probe)

The planner owns this choice (owner ruling, 2026-10-30). The candidate built first is **PrismaUI 1.5.1**, because our
four views already exist as web views (L3 green) and the binding is built (lane ui-live, 2026-10-30):
- `skse/ArgoniaCore/src/views.cpp` calls PrismaUI's published API through our own declaration of it (`prisma_api.h`);
- the host's rules are `skse/core` views (L2), so a Scaleform adapter would replace only that file;
- the bundle is made at install (`tools/ui_harness/build.py`) and laid by `stack.py` as `argonia-views`.

**The map.** Our chart view replaces the MapMenu; FWMF's chart stays laid as the fallback. Three reasons:
- the vanilla map draws the player's marker, which C9 forbids;
- the revealed layer is per visited cell, which a static map texture cannot show;
- one technology for the four screens keeps one input model: pad, keys and touch through `nav.ts`.

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

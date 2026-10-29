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

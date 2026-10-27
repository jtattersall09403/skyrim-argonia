# 0017: Our own original UI and HUD, ported from the old project's React design system

**Status:** decided 2026-10-27 (owner: "for most major things I want us to create our own new original UI…
performing the same functions broadly as their Skyrim equivalents but looking completely different, like
Morrowind versions but adapted for our game's theme, as we had done quite a lot of for the other Elder Souls
Argonia repo"; "HUD I want to be our own new original version like in the other repo").

## Context

- The old project built a complete UI design system in React 19 (`packages/ui`, ~18,400 lines, 121 `.tsx`
  files, reviewed in `apps/ui-lab`): tokens and palette, components (Window, Deck, List, Tabs, Tip, Bar, Meter,
  Slider, CountPicker, Linked text, Items, Overlays), a focus model for keyboard/gamepad/touch, a viewport model
  for desktop and the phone's folded/unfolded shapes, the HUD (bars, belt, corners, crosshair, sneak eye,
  effects, place banner, quest notices, wind mark), the map, and screens: Dialogue, Barter, Container,
  Inventory, Journal, Magic, Spells, Stats, Sheet, LevelUp, Rest, Death, Gift, Factions, Crime, Lock,
  Pickpocket, Alchemy, Enchanting, Smithing, crafting stations, Services, Settings, Load, Loading, PauseDeck,
  Reader (books), WindCall.
- PrismaUI renders HTML/CSS/JavaScript (React or Vue) over Skyrim with JSON interop to C++. So the old React
  code can run almost as-is inside PrismaUI views; what changes is the data layer (old `game-core` and
  `text-catalogue` imports become ArgoniaCore messages).
- No Morrowind-style UI exists in the Skyrim mod scene (research: no Morrowind UI replacer; Classic Dialogue Menu
  is only a look-alike skin; Skywind's UI is unreleased). OpenMW's UI is MyGUI XML layouts and Lua widgets
  (GPL): useful only as a **structural reference** (window layouts, what each Morrowind screen shows); its
  textures are Bethesda's and are not usable.

## Decision

1. **Every major screen and the HUD are our own original PrismaUI views**, ported from the old `packages/ui`:
   dialogue, journal, inventory with paperdoll, stats/character sheet, magic and spells, map (world and local),
   barter, container, services (training, travel, repair, spellmaking, enchanting), crafting stations (alchemy,
   smithing, enchanting), level sitting, rest/wait, death and vastei pile, persuasion and gifts, factions, crime
   and the Owing, lockpick threshold, pickpocket, books and notes, character creation, pause menu, settings,
   load/save (rest-only rules), loading screens and the main menu where PrismaUI can draw them, and the whole HUD.
2. **Porting order:** the design system first (tokens, components, focus and viewport models), then the HUD, then
   screens in the order P4 needs them. The old tests (vitest) come along and run in the L3 harness.
3. **Data layer:** a typed message schema (`ui/schema/`) replaces old `@elder-souls/game-core` and
   `text-catalogue` imports; ArgoniaCore supplies state and receives actions.
4. **Vanilla menus that remain** (only those with no player-facing role in Argonia, or engine-owned ones we
   cannot replace, e.g. some system dialogs, MCM for settings if we keep it) are restyled with our own
   original SWFs or hidden, per decision 0014 §7, and listed in the immersion inventory.
5. **Assets:** only assets whose provenance is clean come across. From the old README credits:
   - `Pelagiad.woff` + `Pelagiad-OFL.txt`: OFL, import.
   - The Black Marsh map glyphs (`map/icons/argonia/sheet.png`, Fal-made, traced to `glyphs.json`): import.
   - The spell-school, status and deck-tab symbols (Fal-made, traced): import, **but they live in
     `symbols.svg` together with shapes exported from Skyrim's `hudmenu.gfx`** (sneak eye, map pins, button
     glyphs), which are Bethesda-derived and may not be published: split the sheet, import only the Fal-made
     symbols, and redraw the rest as original SVG (or Fal + trace).
   - The trim flourishes (`flourish-*.webp`, cut from a "Morrowind pause screen, Black Marsh restyle" reference
     image): import only after checking that reference image's provenance (if it is a restyled Morrowind
     screenshot it is derived; redraw).
6. **OpenMW** is consulted for structure and behaviour (what Morrowind's windows contain and how they
   interact), never for art. Mod-scene UI frameworks (SkyUI 6, Infinity UI, TrueHUD) are used only where they
   remove engineering work (e.g. TrueHUD's boss-bar data, Infinity UI's injection for any remaining SWF), never for
   the look.

## Consequences

- P2-WP2.8 becomes "port the design system"; P4-WP4.10 and P8-WP8.3 build from the port.
- 0014 §7's per-screen order now starts from "our own PrismaUI view" for every major screen.
- The PrismaUI dependency risk grows (0001 §2): pin its version early; keep the fallback rule.

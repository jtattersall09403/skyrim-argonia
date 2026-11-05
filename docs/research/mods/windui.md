# Wind UI (Nexus 196534): what it is, for 1.12

Source: the mod's Nexus description, read 2026-10-31 (the owner's copy; the full text is kept privately in
`argonia-private/work/research-2026-10-31/windui-nexus-page.md`). Facts marked **open** are 1.12 §1's to find in game; §1's answers are under "In game" below.

## What it is
A UI-only SKSE mod (no plugin file, so no load-order slot) that turns Skyrim's menus into Morrowind's windows: inventory,
stats, magic, quick keys, journal and map on screen together, each movable, resizable and lockable, shown or hidden
from a taskbar. Each save remembers its layout. No gameplay changes; Skyrim's prices, weights, skills and perks stand.

## What it covers
- **Inventory:** a grid with icons rendered from each item's 3D model (mod items included), a paper doll with
  equipment slots, tabs and sorting, stolen and enchanted marks, an item card compared with what is worn.
- **Stats:** health, magicka, stamina and level progress; every skill with progress; every perk tree as a plain list
  (owned, available, requirements); factions and bounties; level-ups in their own window.
- **Map:** roads, buildings and fog of war over unexplored land; three looks (terrain, relief, stylised); local and
  world views; fast travel from the map; a pinnable corner minimap. A setting picks its own map or Skyrim's.
- **Trade and containers:** containers, corpses, followers and pickpocketing beside the inventory; Morrowind-style
  one-deal barter at Skyrim's prices; a gift window.
- **Crafting:** forge, enchanting (enchant and disenchant) and alchemy windows fed from the inventory.
- **Magic:** spells by school, powers and shouts; left and right click ready a spell per hand; active effects.
- **Quick keys:** Morrowind's bar on number keys 1–8.
- **Journal:** current, completed and misc quests, statistics and "show on map".
- **Settings:** its own page under Esc > System > Settings: item stacking, grid scrolling, map style, icon memory and
  prebuilt icons and map data, a performance log.
- **Escape hatch:** holding Shift while opening a menu gives Skyrim's original (1.12 switches this off).

**Not named on the page (open):** dialogue, the HUD, message boxes, the tween menu, sleep and wait, lockpicking,
books, the main menu, loading screens, pad navigation, touch.

## Requirements and compatibility
- Skyrim 1.5.97, 1.6.1170 and 1.7.104 in one file (both of our candidate runtimes, 0002); SKSE for the version;
  Address Library (All in One).
- SkyUI optional: if present, Wind UI uses its map-marker art and spell icons. Without it, the window frames come from
  Skyrim's own menus. Font and UI art mods carry over because it reads fonts and frames from the game.
  So our retint acts on what it reads.
- Not compatible with other inventory, container or barter replacers: Dear Diary's versions of those menus give way.
- Tested by its author with SkyUI 6.11 on 1.7.104.

## Status and risks
- **1.3.0 Beta,** single author: pin it and archive the file privately (0002, the machine-moves rule).
- **Known issues:** some roads missing on its map (we replace its map), small icons for thin items.
- **Technology (open):** whether its windows are Scaleform or drawn by the plugin decides 1.12 §2's route for our
  chart and book.
- **Permissions (open in the record):** the owner has read them as allowing our patch on top. 1.12 §1 writes them here
  in our words. The page notes that some of its assets belong to other authors.

## In game (1.12 §1 probe, argonia-play-ie, 2026-10-31)

Wind UI 1.3.0 Beta laid by `stack.py` (row `windui`), SKSE "loaded correctly" on 1.7.104. Stills and logs are in the
private archive (`work/research-2026-10-31/windui-stills/`, `windui-probe-p112/`); the batch is
`tests/journeys/batches/probe-1.12.sh` (its OS-route keys were lost: keys reach Wind UI only by the engine route).

- **Technology.** One DLL drawing Dear ImGui over the game; no SWF, no plugin file. It registers its own menus
  (`WindUIMenu`, `WindUIHud`) and intercepts `MenuOpenCloseEvent` for TweenMenu, InventoryMenu, MagicMenu, StatsMenu,
  FavoritesMenu, ContainerMenu, BarterMenu, GiftMenu, Crafting Menu, Journal Menu and MapMenu. It yields to
  ("goes over ours") Dialogue Menu, Book Menu, MessageBoxMenu, Tutorial Menu, Cursor Menu and RaceSex Menu. So the
  dialogue window, books, message boxes, the HUD, the main menu, loading, sleep/wait and lockpicking stay ours or
  Skyrim's.
- **Where its look comes from.** Fonts through `interface/fontconfig.txt` (it took Pelagiad from our theme:
  `$EverywhereMediumFont = "Pelagiad"`). Four pieces of frame art (`panel9`, `knot`, `cap_left`, `cap_right`) are drawn
  from shapes in `interface/tweenmenu.swf` and `interface/inventory components/itemcard.swf` and cached as PNGs in
  `SKSE/Plugins/WindUI/ArtCache/windui_100/` with a `stamp.txt` of each source's size and hash. Colours are fixed in the
  DLL (black panes, grey-white text); nothing in `settings.json` themes it. So our retint acts on the SWF shapes it
  reads (the install-time recipe in `tools/ui_theme`), never on Wind UI's files.
- **Settings** (`SKSE/Plugins/WindUI/settings.json`, nlohmann JSON; its keys are `fovWorld`, `fovFirstPerson`,
  `magicGlowAllEffects`, `separateIdentical`, `gridSideways`, `mapLayer`, `morrowindMap` (boolean), `mapPinned`,
  `inventorySort`, `figure`, `pinnedMapSpan`, `iconsInMenus`, `iconMemory`, `terrainCacheMB`, `itemListReuse`,
  `perfLog`; the `mwui_*` names are only its settings page's row ids, and a file keyed by them is ignored). Its settings page is added to Skyrim's System page (log:
  "the WindUI page added to Settings").
- **Shift for Skyrim's menus: no switch (a known limit).** `SKSE/Plugins/WindUI/vanilla.txt` reading `off` logs
  "inventory intercept installed (vanilla passthrough: off)", but it turns Wind UI's takeover off altogether: no
  "menu opened", Skyrim's menus every time (2026-11-01, argonia-play, `tests/journeys/batches/probe-vanilla.sh`;
  without the file: "menu opened (inventory, 0 items)"). The first probe read the line the wrong way round and
  tested only M after laying it. So no `vanilla.txt` is laid, and holding Shift while opening a menu still gives
  Skyrim's (the paper) menu.
- **Fast travel and the map.** `morrowindMap: false` (the first probe's `mwui_map_style: 1` was ignored; its "chart ready open" came while vanilla.txt had Wind UI off) makes M and the taskbar's Map open Skyrim's MapMenu, which
  our chart stands in for (ArgoniaCore's mapMenu surface: "chart ready open"). Wind UI's own map (Skyrim's LOD terrain,
  local and world views, fast travel by click) is then not used. The engine-side refusal is 1.12 §5's.
- **Show on map.** In Wind UI's journal window only; with map style Skyrim it would open our chart. J opens our
  journal (the "Journal" user event), drawn over Wind UI's windows; the taskbar's Journal still toggles Wind UI's
  journal window (no setting hides it).
- **Pad.** None: in menu mode Start, the bumpers, the d-pad and A change nothing (the ImGui nav strings are the
  library's). Start from play opened Skyrim's tween menu during the probe's first, frozen minute; engine-route keys
  open Wind UI's menu mode. 1.12 builds the pad (§8).
- **Mouse.** It draws Skyrim's own cursor ("the cursor was gone, shown again"); an OS SetCursorPos and posted
  WM_ mouse messages did not move or click it, so it reads the game's cursor and input events.
- **Its stats pane** groups skills Combat / Magic / Stealth from the 18 vanilla skills plus Custom Skills Framework
  skills, shows perk points and level; vanilla skills we pin at 0 (One-handed, Two-handed, Archery) show. Its magic
  pane groups spells under five hardcoded school names (Alteration, Conjuration, Destruction, Illusion,
  Restoration), plus Powers, Shouts ("Voice" slot) and active effects.
- **Our HUD** draws over Wind UI's windows (it should hide while `WindUIMenu` is open).
- **Cost.** After the first load its map layers took 15.6 s ("made from 42 plugins"), and the first load froze 44 s
  and 34 s in its explored-area check; a warm second launch was smooth.
- **Its own words.** Its level-up window carries joke lines (cheese wheels, Sheogorath); the sitting replaces it.

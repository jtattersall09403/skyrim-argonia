# Wind UI (Nexus 196534): what it is, for 1.12

Source: the mod's Nexus description, read 2026-10-31 (the owner's copy; the full text is kept privately in
`argonia-private/work/research-2026-10-31/windui-nexus-page.md`). Facts marked **open** are 1.12 §1's to find in game.

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

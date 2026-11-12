# Level-up audio: what plays when (SkyrimSE.exe 1.7.104)

Found by static analysis of the executable (2026-11-12): a scan of every rip-relative reference to the default-object
manager's two tables below.

- The default-object manager is a singleton at `0x14219d180` (getter: Address Library id 13894). For this runtime its
  objects sit at `singleton + 0x20 + 8 * i` and their init flags at `singleton + 0xbc0 + i`.
- The Level Up Music default object is index 12 (`LUMS`, MUSC 03B565 MUSSpecialSuccess in Skyrim.esm). It is read at
  exactly two sites, both constructors of `LevelUpMenu`: `0x14094a920` (id 51908) and `0x14094af20` (id 51920). Each
  sends `BSMusicEvent{musicType, add}` to the `BSMusicManager` singleton (id 400896) as the menu is built. So the
  level-up music plays when the level-up menu (choose Health, Magicka or Stamina) opens: not at the HUD notice, and
  not at the confirm.
- The level-up sting is the UI sound `UILevelUp` (SOUN 057B45 -> SNDR 057B44, `UI_LevelUp.wav`), requested by the
  HUD's SWF with its level-up meter (`hudmenu.swf` constants): it plays when the LEVEL UP notice appears.
- Not traced: whether the music is removed when the menu closes; readers of the default-object table by a variable
  index.

Used by: `docs/design/music.md` (the new world's level-up, in Skyrim's two parts).

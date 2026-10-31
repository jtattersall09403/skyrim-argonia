# Install step: the UI theme (1.2 §a; decisions 0006, 0014 §7–8)

Made on the player's machine after the mods are laid and before the first launch. Every output is a derived file:
it is written into the player's mod folder and is never shipped or committed. 3.4 builds the installer around these
commands; the build VM runs the same ones on the cached mods (`~/.argonia/stack/MO2/mods`) into `out/ui_theme/`.

Needs: Python with the `py:` pins in `infra/build-vm/toolchain.lock` (numpy, pillow, fonttools); the player's copy of
Pelagiad (OFL) with its LICENSE.txt, which the installer fetches as `tools/chart fetch-font` does; Dear Diary (23010),
Wood and Paper (44174) and the Oblivion-like Loading Menu (38708) laid as the profile's FOMOD choices record.

0. **One command** for steps 1-2 plus the SkyUI list sizes (ui-review3: the font library had gone to a folder that
   was never staged, so every menu kept Skyrim's condensed face; the item lists read ~10 px at 1080p):
   `python -m tools.ui_theme.build --mods <mods> --ttf <Pelagiad.ttf> --out <mods>/argonia-theme` writes all of the
   below and `interface/skyui/config.txt` (Dear Diary's, entry text 14 to 20, labels 12 to 16). Exit 1 as below.
1. **Font library.**
   `python -m tools.ui_theme.fontlib --ttf <Pelagiad.ttf> --out <mods>/argonia-theme --check <mods>/dear-diary <mods>/skyui <mods>/wood-and-paper <mods>/oblivion-loading-menu`
   writes `interface/fonts_pelagiad.swf` and `interface/fontconfig.txt`. Exit 1 means a menu imports a font name the
   config does not map: stop the install and report it. Copy Pelagiad's `LICENSE.txt` beside the SWF (OFL §2).
2. **Retheme and title.**
   `python -m tools.ui_theme.retheme --mods <mods>/dear-diary <mods>/wood-and-paper <mods>/oblivion-loading-menu --ttf <Pelagiad.ttf> --out <mods>/argonia-theme`
   (roots lowest priority first) writes the recoloured `interface/deardiary/**/*_BG.swf`, `interface/loadingmenu.swf`,
   the SkyUI config panel's copy, and `textures/interface/objects/mainmenuwallpaper.dds` (the Argonia title on our own
   paper; Dear Diary's Skyrim map is replaced, not recoloured). Exit 1 means a Nordic watermark was not where it was
   measured (a changed Dear Diary version): stop and report.
3. **Order.** Add `argonia-theme` to the profile above `oblivion-loading-menu`, `wood-and-paper` and `dear-diary`
   (MO2 `modlist.txt`: earlier line wins), so its `fontconfig.txt` replaces Dear Diary's.
4. **Verify.** `argonia-theme/argonia-theme.json` lists every file written and each bitmap's treatment; the verify
   script checks it names 44 files on Dear Diary 3.0.6 + Wood and Paper 1.0.2 + Oblivion-like 1.0.

Measured on the build VM (2026-10-30): fontlib 274 glyphs, 40 KB SWF, 41 MB peak; retheme 44 files, 6.9 s, 277 MB peak.

# Imported from elder-souls-argonia: the map's place glyphs

- **File:** `tools/chart/glyphs.json`, byte-identical to the owner's private repo `jtattersall09403/elder-souls-argonia`
  at commit `b581910f0f87d8da88eaa9876d238cdc5d709e78`, path `packages/ui/src/map/icons/argonia/glyphs.json`
  (last changed in `878cdbd3`). sha256 `b15c6042aa3df64826af0e1fbc3164a36ee0b71dc8e071b4c92b5c4dbebeb240`.
- **What it is:** 12 traced vector glyphs (one even-odd path each, 100-unit box): pin-city, pin-town,
  pin-settlement, pin-ruin, pin-cave, pin-shrine, pin-docks, pin-mine, pin-camp, pin-farm, pin-fort, pin-landmark.
- **Provenance:** our own UI art. The old repo's `icons/argonia/SOURCE.md`: `sheet.png` was generated on fal.ai with
  `fal-ai/nano-banana-pro/edit` (request `01a14974-5fe0-7090-bb61-c59b233a6be4`, seed 37), and `trace.py` traced it
  into `glyphs.json`. The edit was guided by a reference render of the old Skyrim-derived pin set for layout only;
  the glyphs are Black Marsh subjects (a xanmeer, stilt houses, a hist, a reed boat, a palisade), with no Nordic
  element. The sheet itself (sha256 `861b9ef5...f57f`) is not imported.
- **Credit:** map glyphs generated with Google Nano Banana Pro via fal.ai for Elder Souls: Argonia.
- **Used by:** `tools/chart/render.py` (`glyph_image`, the `PIN` table, also from the old `packages/ui/src/map/pins.ts`).

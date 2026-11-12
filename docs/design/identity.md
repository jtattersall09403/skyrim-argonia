# The regions' identities

Each of the new world's 24 regions has a one-line identity, so that walking from one region into the next changes
what you see, hear and stand in. Sheet: `newworld/sources/identity/regions.json`. Check: `tools/newworld/identity.py`.
Readers: the atmosphere (`docs/design/atmosphere.md`), the water types (`tools/newworld/world/water_types.py`), the
regions' ambient sound (`atmosphere.py` spec `sounds`), the ground cover's colour and the small signature things
(the dressing stage).

## A row

One row per region, every field cited to the region's research (`newworld/story/data/db/region_note.jsonl#<region>/<aspect>`,
the ecology file `newworld/sources/ecology/regions/<region>.json`) or carrying a stated `extrapolation` (decision 0032):

- **slot**: the region's fixed place in the atmosphere's form id formula; never renumbered, a new region takes the
  next slot.
- **light**: `haze`, the day haze's mood colour (a mood, not a tint: black-green gloom, sulphur-amber steam, cold
  blue-grey sea mist, the clear bright mesa); `brightness` (0.6 to 1.3), `saturation` (0.6 to 1.3) and `night` (0.5
  to 1.2), multiples of Skyrim's source weather's light, colour strength and night level; `mood` in words.
- **sight**: `visibility`, the fraction of Skyrim's base fog distances (0.3 to 1.2).
- **weather**: `chances` over the six kinds (fair, cloudy, mist, rain, storm, steam; each at least 1, summing to
  100), written so the mix differs in kind (nearly always dripping, mostly clear, sudden storms, standing fog), and
  its `character` in words.
- **sound**: a `day` and a `night` bed from the sheet's `sound_beds` (frog chorus, cicadas, surf and gulls, sea
  swell, reed wind, rain-forest birds, deep hush, dusk insects, rain drip, upland wind, marsh birds, night crickets,
  fly drone, owls), each a set of the load order's own sound records.
- **ground**: the `family` of the dominant flower and grass colour (from `ground_families`) and the `flowers` in words.
- **water**: the `look` of the region's still water (from `water_looks`: black, tea-brown, silt-brown, algae-green,
  reed-green, pale-silt-grey, turquoise, sea-green-grey, slate-blue) and its words.
- **signature**: one small thing found only there (glowing fungi, bone piles, egg clutches, drifts, fireflies,
  wisps), placed by the dressing stage.
- **creature**: one signature creature, a kind from the region's ecology file.

## The check

`python -m tools.newworld.identity check` (in the gate through `tools/tests/test_newworld_identity.py`):

1. Every row has every field with a cite or an extrapolation; the numbers inside their ranges; every bed, family
   and look one of the sheet's lists; the creature in the region's ecology file; no two slots alike.
2. Every two neighbouring regions differ on at least three of the six measured things:
   - light: the hazes' hue angle (CIE Lab, both chroma at least 12) at least 40 degrees, or haze luminance times
     brightness a ratio of at least 1.3;
   - sight: visibility a ratio of at least 1.5;
   - weather: the most likely kind differs;
   - sound: the day bed or the night bed differs;
   - ground: the colour family differs;
   - water: the look differs.

Neighbours are measured, not written: `python -m tools.newworld.identity adjacency` reads the landcover's region
raster (`out/newworld/landcover/region.npy`) and writes `newworld/sources/identity/adjacency.json` (two regions
whose samples touch). Rerun it when the regions' borders move. `python -m tools.newworld.identity table` prints the
contrast table of every neighbouring pair.

## Writing or changing a row

1. Read the region's research (climate, look, ecology notes; its ecology file's signature creatures).
2. Write the row from those words; where the research says nothing, choose and state the extrapolation.
3. Run the check. A pair that differs on fewer than three: change the row whose research leaves room (a light or
   sight value, the sound bed, the flower family), never a cited fact.
4. Rebuild with the world-build skill: a change to light, sight or weather makes the `atmosphere` stage stale; to
   water, `cells`; to sound, `atmosphere`; to ground or signature, the stages that read them.

# New art: the making tools

The first tools of the model workshop ([the proposal](../../docs/research/new-art/PROPOSAL.md)), written for the
dugout canoe test. Each is one half of a measure-and-look stage; nothing they make is committed (it lives under
`out/newart/`).

| Tool | Stage | What it does |
|---|---|---|
| `measure.py` | every stage | The numbers: triangles, separate pieces, open and shared edges, closed or not, size, surface, textures |
| `look.py` + `sheet.html` | every stage | The look: one sheet of six fixed named views (surfaced, plain clay or triangles) |
| `tobrief.py` | every generation | Puts a generation into true metres before anyone looks at it: turned about the vertical so its long axis runs along X, scaled by one measure of the brief (length, height or across), the cross-section brought to the brief's beam when asked, stood on the ground |
| `shape.py` | shaping, clean-up | Aligns a generation to its own axes from its real vertices, stands it upright, scales it to the brief, cuts triangles keeping the texture layout |
| `polearm.py` | shaping a long weapon | A generated head set on a shaft made by hand to the donor's measurements (grip at the origin, butt and tip where the donor's are), the shaft's wood from the head's own stub; `finish` makes the finished weapon: a raised cord grip and a binding collar as real geometry, wear painted along the shaft's own length, and two short generated end pieces (butt cap, grip band) seated on the shaft's measured radius |
| `building.py` | shaping a building shell | `shell`: loose pieces off, triangles cut. `view`: the four sides drawn flat with a grid, from rays on the real triangles. The agent looks and marks the painted door by eye as outline points. `door`: the shell scaled by the marked door, the door plate laid on the real surface inside the outline (leaning with the leaf, clear of its proudest part) with the arrival point, and a side section that checks it. There is no automatic door finder |
| `reference.py` | consistency | The reference numbers per material (weathered wood, reed and thatch, rope, bone, stone, iron and bronze) from the game's own archives and the mods we hold, on real triangles and UVs: texel density, diffuse lightness, chroma and hue, normal-map tilt, specular |
| `grade.py` | surface | Grades a generated texture toward those numbers: `regions` splits it into colour regions for the agent to name by eye, `apply` moves each named region toward its material (lightness, chroma, hue, normal strength), blended softly, the geometry and UVs untouched; writes the numbers before and after |
| `densify.py` | surface | Brings a building-sized generation up to the game's texel density keeping its look: new UVs at a set pixels per metre (xatlas, as many atlases as it takes, the same triangles), the generator's texture re-baked onto them, and a fine grain from one of our swatches laid per chart along the re-bake's own strokes, only where it lacks fine detail and the colour is wood-like; mean colour unchanged; writes the numbers before and after |
| `held.py` | review | A held vanilla model as a line-up neighbour, in metres with its own textures (a mod's model only for our own looking, never published) |
| `lineup.py` | review | One scene of our models beside held neighbours on one ground, each turned along the line or stood upright from its real vertices |
| `webcopy.py` | review | Writes the explorer's web copy of a model: one `.gltf.json` with buffers and textures as data URIs, textures as JPEG, refusing anything over the triangle cap |
| `surface.py` | surface | Makes a swatch into a repeating material; wraps a mesh in it by box projection from the real face normals at constant pixels per metre; carries shading as vertex colour; writes light copies for the page |
| `asset_explorer.py` + `asset_explorer_page.html` | review | Builds the asset explorer's publishable folder `out/newart/explorer-site/` (in the main tree, canonical paths, real copies, no links) from the asset records and `out/newart/explorer/`, with `PUBLISH.json` listing every served path, its size and what to remove; refuses a version off its brief's size. A lane builds; the lead publishes the folder as `PUBLISH.json` lists it. Url and note contract in `asset_explorer.json` |

They run in a scratch environment (`out/newart/.venv`: trimesh, pymeshlab, pygltflib, pillow, rtree, embreex, playwright). pymeshlab needs `libOpenGL.so.0` on the library path.

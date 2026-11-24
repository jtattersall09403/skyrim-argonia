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
| `webcopy.py` | review | Writes the explorer's web copy of a model: one `.gltf.json` with buffers and textures as data URIs, textures as JPEG, refusing anything over the triangle cap |
| `surface.py` | surface | Makes a swatch into a repeating material; wraps a mesh in it by box projection from the real face normals at constant pixels per metre; carries shading as vertex colour; writes light copies for the page |
| `asset_explorer.py` + `asset_explorer_page.html` | review | Builds the asset explorer's publishable folder `out/newart/explorer-site/` (in the main tree, canonical paths, real copies, no links) from the asset records and `out/newart/explorer/`, with `PUBLISH.json` listing every served path, its size and what to remove; refuses a version off its brief's size. A lane builds; the lead publishes the folder as `PUBLISH.json` lists it. Url and note contract in `asset_explorer.json` |

They run in a scratch environment (`out/newart/.venv`: trimesh, pymeshlab, pygltflib, pillow, rtree, embreex, playwright). pymeshlab needs `libOpenGL.so.0` on the library path.

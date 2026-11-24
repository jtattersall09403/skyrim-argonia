# New art: the making tools

The first tools of the model workshop ([the proposal](../../docs/research/new-art/PROPOSAL.md)), written for the
dugout canoe test. Each is one half of a measure-and-look stage; nothing they make is committed (it lives under
`out/newart/`).

| Tool | Stage | What it does |
|---|---|---|
| `measure.py` | every stage | The numbers: triangles, separate pieces, open and shared edges, closed or not, size, surface, textures |
| `look.py` + `sheet.html` | every stage | The look: one sheet of six fixed named views (surfaced, plain clay or triangles) |
| `shape.py` | shaping, clean-up | Aligns a generation to its own axes from its real vertices, stands it upright, scales it to the brief, cuts triangles keeping the texture layout |
| `polearm.py` | shaping a long weapon | A generated head set on a shaft made by hand to the donor's measurements (grip at the origin, butt and tip where the donor's are), the shaft's wood from the head's own stub |
| `building.py` | shaping a building shell | Loose pieces removed; the painted door found on the real geometry; the shell scaled by its door; triangles cut; the door plate made to the door's outline, with the arrival point |
| `webcopy.py` | review | Writes the explorer's web copy of a model: one `.gltf.json` with buffers and textures as data URIs, textures as JPEG, refusing anything over the triangle cap |
| `surface.py` | surface | Makes a swatch into a repeating material; wraps a mesh in it by box projection from the real face normals at constant pixels per metre; carries shading as vertex colour; writes light copies for the page |
| `asset_explorer.py` + `asset_explorer_page.html` | review | Builds the asset explorer's folder from the asset records (`newworld/sources/art/`); its url and note contract are in `asset_explorer.json` |

They run in a scratch environment (`out/newart/.venv`: trimesh, pymeshlab, pygltflib, pillow); `look.py` uses the
studio's Playwright. pymeshlab needs `libOpenGL.so.0` on the library path.

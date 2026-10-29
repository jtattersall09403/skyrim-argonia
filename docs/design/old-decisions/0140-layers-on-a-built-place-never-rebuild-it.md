<!-- imported unchanged from elder-souls-argonia docs/decisions/0140-layers-on-a-built-place-never-rebuild-it.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0140 Layers on a built place never rebuild it

**Decision (owner).** Once a place is built and accepted, every
later phase adds to it in layers: people, creatures, dens, loot, plants,
signs, dialogue, quests. Adding a layer republishes only that layer. The
built place (its ground, kit poses, interiors, lights, water) is never
re-solved, re-exported or re-baked for a layer change; a publish that would
touch them for a socket-only change is a defect in the tool.

The same holds between layers and within one. Adding or changing a few
people never regenerates, republishes or re-checks every person; adding a
dialogue line, a service, a creature's moveset or a quest stage touches
only the records it names and the derived view of those records. Every
generator and gate from 2.5 on is incremental by record id: it keys its
output and its freshness on the inputs each record reads, so an unchanged
record costs nothing on a rerun. A whole-set regenerate is for a schema
change, never for an edit.

**Why.** A socket-only change must not re-solve or re-export the built
place: a whole export re-solves unchanged pieces against rebuilt kits and
moves them by millimetres, and the freeze then refuses a place whose only
change is new sockets. A full publish costs one to six minutes under load;
the chain of fills, gates and bakes over the sixteen places takes hours. Part 4 adds hundreds of
places and every later chunk layers on all of them; a rebuild-per-layer
chain would never finish.

**Consequences.**
- `wb.py publish` detects a layer-only change (sockets, bindings, record
  `life` and loot fields) and runs the layer path: compile the bindings,
  patch the published bundle and index, re-bake only the nav class the
  layer needs, run the layer's gates. No export, no kit solve, no interior
  re-export, no full nav bake.
- The freeze hash covers the built place only (0100 decision 6; the
  socket exclusion in the freeze hash is the first half of this rule).
- A layer's data lives beside the place, never inside the built geometry
  files, so the bundle patch is a merge, not a rewrite.
- Every later brief says which layer it adds and names the layer path.
- Vegetation is a built layer. The published vegetation release is frozen: it
  is never rebuilt or republished whole unless the owner says so
  (`ES_OWNER_VEGETATION_REBUILD=<reason>`). A change edits and patches the
  shipped bundles (`apply_vegetation_patches`) and republishes only the
  patched archive; `compile_scatter --out` and `province:publish` of a
  rebuilt archive refuse, and `agent_guard.py` refuses a lane command naming
  the scatter stage without the flag.
- Furniture is a layer. New `place` ops of settled
  furniture kit rows (`settle: true`, no pad, no mount, at most a ground
  bind into a shell's assembly), and no other geometry change, classify as
  `furniture` (`layer_publish.classify`). Its publish exports the blueprint
  and compiles, then appends only those placements and the export's rows
  keyed to them to the published bundle, every other placement
  byte-identical; the shell they join takes its new compiled object row.
  The nav re-bakes when they move its input. On an accepted place the layer
  amends the freeze receipt instead of reopening it: the receipt's `layers`
  records each layer's placement ids, date and hash
  (`accepted_places.record_layer`), and the place stays frozen while its
  record without them hashes to the accepted hash. `seat_sockets` plans
  seats on such pieces from the layout before they are published.
- Ground is a layer. A change of the layout's `mound` ops only (`es.mound`)
  classifies as `ground`; its publish replaces the place's mound pads in the
  bundle and the ground sidecar, every other row byte-identical, and the nav
  re-bakes for that place.
- A published place rebuilds only by choice: `wb.py publish <id> --rebuild
  "<reason>"`, refused unless the classifier finds a structural change; a
  structural change without it is refused naming the layer path.

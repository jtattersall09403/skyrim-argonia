<!-- imported unchanged from elder-souls-argonia docs/decisions/0128-places-are-edited-in-place-never-rebuilt.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0128 — Places are edited in place, never rebuilt

Date: 2026-10-06 (16k walk 12, process lane). Supersedes nothing.

## Context

Fix rounds on walked places reopened the whole place procedure for a
change of a few uids: a fresh orientation, a re-read of the whole layout, a
render round, a full survey per fix. The layout file already holds every
op by `uid`, the workbench re-applies it with a cache and publishes one
place, so the cost of a small change should be the change.

## Decision

1. Any change to a place that already has a layout file is made with the
   `place-edit` skill (`.claude/skills/place-edit/SKILL.md`), run by
   `place-builder`: read the layout and its lessons, edit the delta ops,
   `wb.py apply --cache`, `wb.py check --only`, `wb.py survey` once,
   `wb.py publish <place-id>`, a diff of the published bundle against HEAD,
   one walk-packet row per edited uid.
2. The `place` skill is the procedure for a new place or a re-author of a
   place's design; its `references/edit.md` is the delta edit.
3. `wb.py publish` exports from the scene, so the layout is re-applied
   before every publish; a skipped apply is caught by the compile's
   "layout changed since this blueprint was exported" line.

## Cost

Measured on Claywater Station, 2026-10-06. Apply took 16 to 27 s for one
yaw change on `b1-bucket`. Publish took 34 s for that exterior-only edit,
with gates 17 s, the settlement bundle 9 s and the interior bundle 1 s.
The bar is 2 min for the whole edit. The interior bundle reads each cell
from a cache keyed on its inputs (`export_interior_bundle.bundle_cache_key`).
The key hashes only the worldgen modules the export loads. When it hashed
every module, any unrelated commit re-exported every cell and publish took
100 to 172 s.

## Consequences

The delta test also showed that a place published before a kit rebuild
carries the old kit hashes until it is republished. Claywater's committed
bundle and blueprint name the kit hashes from before commit c8b4458c0
(2026-10-05 kit rebuild). Any republish therefore moves five kit hashes and
the ground overlays beside the edit. A kit rebuild republishes every place
that reads the kit in the same batch.

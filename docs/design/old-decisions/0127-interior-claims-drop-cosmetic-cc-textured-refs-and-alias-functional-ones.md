<!-- imported unchanged from elder-souls-argonia docs/decisions/0127-interior-claims-drop-cosmetic-cc-textured-refs-and-alias-functional-ones.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0127 — Interior claims drop cosmetic CC-textured references and alias functional ones

Date: 2026-10-04 (16k walk 11, planner ruling). Supersedes nothing.

## Context

Every King of the Murkmire round hut (RootWhisper) and thatch house (Seekhat)
cell failed the interior acceptance gate (decision 0103: placements + drops +
substitutions = the cell's reference count) only on references whose mesh, or
a diffuse texture the mesh needs, lives in a Creation Club, AE `_ResourcePack`
or DLC archive. The vault does not hold those archives and the owner rule bans
shipping them, so no kit can carry those pieces. Walk 11 counted 43 cosmetic
references (trees, flora, fish, food, clutter) and 7 functional ones.

## Decision

1. A COSMETIC reference held out of every kit only by a CC / DLC archive is a
   listed drop with reason `cc-texture` and its `ccPath`. 0103 already allows
   listed drops; the count rule is unchanged.
2. Cosmetic or functional is read from the reference's BASE RECORD TYPE, never
   from its name: `DOOR`, `FURN`, `CONT`, `ACTI` and `LIGH` are functional
   (`FUNCTIONAL_BASES` in `export_interior_bundle.py`). A functional reference
   is never dropped. When its mesh is in the vault, the kit's `textureAliases`
   table textures it from the nearest vanilla or Tropical texture of the same
   role. When its mesh is a CC mesh, it stays a gap: the cell fails unless a
   0103 stand-in exists.
3. What counts as CC-held: a mesh under a CC / DLC folder (`CC_MESH_PREFIXES`),
   or a mesh row in `world/sources/placement/kit-interiors/cc-only-assets.json`.
   A row there comes from build_kit's "unresolved diffuse" refusal for a texture
   that exists only in such an archive. A cosmetic reference whose texture the
   source mod's own archive and loose files never shipped (absent from its BSA
   file table) is a listed drop like a CC one: the turtle shell (`doll_turtle.nif`,
   `textures/argonia/curse of immortals/turtle-shell-nor.dds`, absent from King of
   the Murkmire's BSA; the Curse of the Immortals assets are off Nexus) is the
   example. A texture missing for any other reason is not covered.
4. A CC texture is never shipped. An alias always names a texture we hold.
5. Structural pieces are never cosmetic: a CC-held structural STAT (a bridge span) whose plugin bounds (OBND) equal a held STAT's with a published kit row of its class stands in as that twin (`geometry_twin`), solid and walked.

Same change (walk 11 fix row 7): a placement outside the box of every structural
piece in its cell (plus 0.5 m) is the author's off-room dressing. It becomes the
listed drop `outside-shell`, and its sockets go with it.

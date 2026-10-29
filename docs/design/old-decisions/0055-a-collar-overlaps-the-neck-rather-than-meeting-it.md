<!-- imported unchanged from elder-souls-argonia docs/decisions/0055-a-collar-overlaps-the-neck-rather-than-meeting-it.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0055 — A collar overlaps the neck rather than meeting it

**Status** superseded by [0056](0056-armour-is-blended-to-the-wearer-not-deformed-to-fit.md):
armour is blended to the wearer's sex and weight, so the seam is exact and
nothing is snapped or lifted. The record as it stood, with its measurements,
is [archived](../research/archive/armour-neck-seam/0055-as-recorded.md).

The overlap fix snapped each cuirass's neck ring onto the weight-zero male
neck, lifted by 0.15 of its radius. It held only for male wearers and deformed
authored art (the cuirass's embedded body skin) to compensate for loading the
wrong mesh. Two findings outlive it:

- **A collar is found by geometry, never by name**: a real ring concentric
  with the neck axis at the neck's height and girth, covering a full turn with
  no angular gap over 90°; where several are concentric, only the innermost is
  the seam.
- **Matching positions closes only the bind pose.** Skin weights are copied
  across a stitched boundary from the edge each vertex lands on, or the seam
  parts on the first idle breath.

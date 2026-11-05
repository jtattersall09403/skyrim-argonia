# Lane 1.15-r6-no-birch: the northern palette leaves every list

Decision 0006 (no Nordic element survives), 0032 (grounded in lore).

## What was where
The pool (`object_form`, all BM&V mod forms) holds five northern trees: 01BIRCH (birch-.nif), 01redbirch, 01popular
(poplar), 01Juniper (dwarfjunip01), 01briscone (bristlecone). No pine, spruce, fir or aspen form exists in the pool.
Placed in the current shards (out/terrain/vegetation, share of tree-role stems per eco class):
- 01BIRCH: coastal-lagoon 1037 stems, 0.092 of that class's tree stems (the lane note's 0.026 used another denominator).
- 01Juniper: flooded-forest 902 stems, 0.007.
- 01redbirch, 01popular, 01briscone: 0 stems (the uplands already denied them via UPLAND_DENY).
The redwoods (coastredwood, giantredwood) place nowhere and are left to UPLAND_DENY and the "giant" tag.

## What replaced it
`lists.NORTHERN_PALETTE` is denied in `lists.admits` for every region class. The drafts refill from the class's own
ranked ecology families (coastal-lagoon: mangrove, palm, cypress; flooded-forest: cypress, willow) at the same per-role
pick counts, so density is unchanged. Dead names (birch, aspen, juniper) left the upland "broadleaf" family.
Citation: lore `world/sources/lore/topics/fauna-hazards.md:92-96` (Flora, CANON_EXPLICIT: cypress, mangrove, bamboo,
palms, bog willow, ferns, blue moss); no lore dossier names birch, poplar, juniper or bristlecone.

## Proof
`tools/argonia_world/vegetation/tests/test_lists.py` (two new tests); vegetation suite 66 passed, ruff clean.
No province regenerate: the chain's vegetation stage re-places.

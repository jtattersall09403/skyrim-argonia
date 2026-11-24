# jal-veesa: state

A market town of the Sedge-Wardens round a sick Hist on its mound (record: `python3 -m tools.newworld.place_card jal-veesa`).
Source Seekhat Yol (King of the Murkmire), three Alten Meerhleel houses added at the south edge. Drafted; the owner
has no open or finalised save here (`replay jal-veesa`: 0 ops, 0 conflicts on 2026-11-24).

## Quest states (states.jsonl)
- hist-sick (default), hist-healed (MN19 Use), hist-dead (MN19 Take/Give), on markers STATE.HEALED and STATE.DEAD.
- The living tree, its sap pool, eggs and nests ride STATE.DEAD opposite; the dead twin STATE.DEADHIST rides it.

## Pass 2026-11-24: spigot and clothing (have-get-make section 5)
- Spigot: `Skyrim.esm:0E1FC1` (USSEP's static "Sap Spigot"), scale 2, LOOK039PLACE, in the end of the Hist's east root
  where it meets the deck Weeltul kneels on (her PrayCrouched marker XP3JHQY, 1.3 m east), facing her. Living parent.
- Jar: KotM "Hist Sap" `394B35` (the same model as the doc's `0AED90`, named for the marsh) LOOK040PLACE on the deck
  under the tap (living parent); a second jar LOOK041PLACE on STATE.HEALED only (the healed scar weeps sap). Both
  are loose stock rows owned by Weeltul.
- Not used: `dunSleepingTreeCampSpigot` 0AED89 (a FLOR that harvests "Sleeping Tree Sap", a Skyrim giants' item) and
  `0AED90` "Sleeping Tree Sap" (the name); the jar is magenta in the viewer (the model's sap colour as the viewer draws it).
- Clothing: 19 people dressed from the kits' clothing rows (Saxhleel tunics, sashed for priest/elder/trader/host
  kits; HTBM rough fibre clothes for the sedge and rope weavers; boots for the two ruin-wardens, sandals for the
  Stormhold carrier). Naga and Kothringi dress left out (Naga are the record's brigands; Kothringi are gone).
- Enable parents were set in refs.jsonl by field (no hand op writes one), as the states commit did.

- Lights: the smoke fire under the fish racks (LOOK031PLACE) given its light by `draft lights`; the four lane lamp
  sets keep their copied light (tool fix in draft/lights.py: a free light within BIND lights the added source).

## Last checks (2026-11-24, working tree)
- seat 0 moved; draft check PASS; build + check 17/17 green, built check current; probe --all 0 faults; stock reach 0.
- Commit refused only by the gate's storyexplorer stage (page behind): waiting on the lead to publish.

## Next
- After publish: lane_commit the same paths; then capture the tap in each state (sick, healed, dead) from the deck.

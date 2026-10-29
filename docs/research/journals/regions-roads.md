# Journal: regions and roads (2.W3)

- **2026-10-29, first agent.** Data side: 48 regions over every cell, weather and object lists, climate; roads traced
  off their paint, the route graph in one component. The old raster was not in the vault, so each cell's class is
  reconstructed (0.758 leave-one-out).
- **2026-10-29, second agent.**
  - The records are written: Argonia.esm overrides REGN shells that live in ArgoniaWorld.esm, because the generated
    master's cells cannot link to their dependant (the shell pattern, added to decision 0031).
  - Weather values are ours, and only references come from the templates.
  - Roads are painted unbroken into the land cover.
  - Gates and landings are persistent refs, all pending their pieces.
  - The season rule is in ArgoniaCore.
  - Signpost arms name places, never junctions.
  - The old roads' extra length is mostly 8° grading round steep ground: our roads are straighter and 8.6% steeper
    than the cap. The next step is a slope cost in the trace.
  - Gate green.

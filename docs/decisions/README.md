# Decision records

One record per decision the code does not make obvious: the why, never the recipe. Rewritten in place when the
decision changes; a record replaced whole is marked superseded here. Under about 120 lines each. Read the line
of any record touching your task, then the record.

Rulings inherited from elder-souls-argonia are listed (carry / adapt / drop) in
[inherited-rulings.md](../inherited-rulings.md); they are not re-numbered here.

- [0001](0001-skyrim-se-is-the-host-engine.md) Skyrim SE is the host engine; S2 plugins carry the systems; HTML screens carry the Morrowind UI
- [0002](0002-one-pinned-skyrim-runtime.md) One pinned Skyrim runtime
- [0003](0003-nothing-shipped-that-players-do-not-own.md) The repo is public and ships only our own code and data
- [0004](0004-ds1-remastered-is-the-combat-oracle.md) Dark Souls Remastered is the combat oracle; match DS1 timings; knowledge only
- [0005](0005-the-morrowind-soul-contract.md) The Morrowind soul contract (C1–C15)
- [0006](0006-black-marsh-immersion-no-nordic-element-survives.md) Black Marsh immersion: no Nordic element survives; Pelagiad, new music, 100% audit, Fal for minor art
- [0007](0007-the-owner-plays-by-browser-streaming.md) The owner plays by browser streaming from an AWS GPU machine
- [0008](0008-infrastructure-aws-london-under-100-a-month.md) Infrastructure: AWS London, x86 build VM, on-demand GPU box, under $100 a month
- [0009](0009-world-content-is-imported-then-generated-into-plugins.md) World content is imported, owned here, and generated into plugins
- [0010](0010-reuse-first-and-the-running-game-is-the-oracle.md) Reuse first in a fixed route order; the running game is the oracle; Ghidra is a scalpel
- [0011](0011-ways-of-working-are-inherited-lean.md) Ways of working are inherited, lean
- [0012](0012-vanilla-skyrim-is-quarantined.md) Vanilla Skyrim is quarantined
- [0013](0013-subscription-and-pace.md) Subscription and pace: 5x first, 20x for parallel content

## Open owner calls

Calls only the owner can make. The planner raises each in an owner check-in when its phase reaches it, with a
recommendation; the answer is recorded in the named record (or a new one) and the row is struck through.

| Id | Call | Needed by | Recommendation |
|---|---|---|---|
| O-1 | Fate of the old elder-souls-argonia EC2 machine (stopped; ~$23/month for its 250 GiB disk) | P0 | Snapshot the disk to S3, then delete the volume; keep the R2 vault |
| O-2 | Subscription: 5x now, 20x from P9 | P0, P9 | 0013 |
| O-3 | Confirm the pinned runtime chosen in P1 | P1 end | 0002 rule |
| O-4 | Perks: invisible engine layer only, or a visible Morrowind-flavoured perk layer merged with vastei | P4 | Invisible layer (0005 C4) |
| O-5 | Send permission requests to mod authors (drafted by agents, sent from the owner's Nexus/ModDB account): Black Marsh & Valenwood (dalecallen1987), MihailMods, Tropical Skyrim (Soolie) and its SSE port (78044), King of the Murkmire (pancake0723; AI clause), Xanmeer tileset (NorthwindBlue, DarthVitrial), Sign of Cipactli (URL unknown), Tamriel Worldspaces – Argonia (118678) | P2 | Send all in one batch early; build only on cleared mods |
| O-6 | Nexus Premium (needed for scripted API downloads; otherwise each download is a manual click) | P1 | Use Premium for the build and GPU machines if already held; otherwise one manual download session, cached to S3/R2 |
| O-7 | Steam login on the GPU box (Steam Guard approval on the owner's phone, once) | P1 | Owner logs in through the stream once; then offline mode |
| O-8 | Music source: CC-licensed, commissioned, or Fal-generated (AI clause interactions) | P8 | CC-licensed first, Fal for gaps |
| O-9 | Split pauldrons/gauntlets if no sourced split meshes exist | P4 | Accept paired pieces in separate slots |
| O-10 | Slice region and opening (default: the opening work camp near Stormhold / Alten Corimont, as in the old main quest) | P7 | Default |
| O-11 | Voice: stay unvoiced text dialogue (old 0139/0143) | P4 | Yes |
| O-12 | Old repo's GitHub Pages build exposes converted assets publicly (outside this repo's scope) | any time | Owner's choice; flagged only |
| O-13 | Public name: "Argonia" overlaps Tamriel Rebuilt's planned territory and the dormant Beyond Skyrim: Argonia; release title and Nexus wording must not imply either | P10 | "Elder Souls: Argonia" or similar, with a "not affiliated" line |

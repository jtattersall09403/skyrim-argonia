# Decision records

One record per decision the code does not make obvious: the why, never the recipe. Rewritten in place when the
decision changes; a record replaced whole is marked superseded here. Under about 120 lines each. Read the line
of any record touching your task, then the record.

Rulings inherited from elder-souls-argonia are listed (carry / adapt / drop) in
[inherited-rulings.md](../inherited-rulings.md); they are not re-numbered here.

- [0001](0001-skyrim-se-is-the-host-engine.md) Skyrim SE is the host engine; S2 plugins carry the systems; HTML screens carry the Morrowind UI
- [0002](0002-one-pinned-skyrim-runtime.md) One pinned Skyrim runtime
- [0003](0003-nothing-shipped-that-players-do-not-own.md) The repo is public and ships only our own code and data
- [0004](0004-ds1-remastered-is-the-combat-oracle.md) Dark Souls Remastered is the combat yardstick; match DS1 timings where we set them; knowledge only
- [0005](0005-the-morrowind-soul-contract.md) The Morrowind soul contract (C1–C15)
- [0006](0006-black-marsh-immersion-no-nordic-element-survives.md) Black Marsh immersion: no Nordic element survives; Pelagiad, new music, 100% audit, Fal for minor art
- [0007](0007-the-owner-plays-by-browser-streaming.md) The owner plays by browser streaming from an AWS GPU machine
- [0008](0008-infrastructure-aws-london-under-100-a-month.md) Infrastructure: AWS London, x86 build VM, on-demand GPU box, under $100 a month
- [0009](0009-world-content-is-imported-then-generated-into-plugins.md) World content is imported, owned here, and generated into plugins
- [0010](0010-reuse-first-and-the-running-game-is-the-oracle.md) Reuse first in a fixed route order; the running game is the oracle; Ghidra is a scalpel
- [0011](0011-ways-of-working-are-inherited-lean.md) Ways of working are inherited, lean
- [0012](0012-vanilla-skyrim-is-quarantined.md) Vanilla Skyrim is quarantined
- [0013](0013-subscription-and-pace.md) Subscription and pace: 5x first, 20x for parallel content
- [0014](0014-derived-files-are-made-on-the-players-machine.md) Derived files (FaceGen, LOD, behaviours, timing, menus) are made at runtime or on the player's machine
- [0015](0015-repo-licence-and-licence-tracking.md) Repo licence (GPL-3.0 code, CC BY-NC-SA content, recommended) and licence tracking
- [0016](0016-weapon-classes-follow-morrowind.md) Weapon classes follow Morrowind, including crossbows and thrown
- [0017](0017-one-coherent-argonian-ui-approach-chosen-with-the-owner.md) One coherent Argonian UI, Morrowind in spirit and good by today's standards: Morrowind dialogue and pause-menu windows (draggable, resizable, remembered); the approach chosen with the owner in G11
- [0019](0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md) Combat maps each DS1 behaviour to a tuned mod or to our own build of DS1's system (the combat map decides, row by row); nothing from the old project's combat
- [0020](0020-reuse-others-methods-universal-modder-and-ghidra-tooling.md) Reuse others' methods: universal-modder's skills, agents and field notes; agent-ready Ghidra tooling (ReVa, pyghidra-mcp)
- [0021](0021-fast-focused-loops-and-the-ladder.md) Fast focused loops with eyes on the cheapest rung of the ladder; one lane tests a feature and its joins; journeys are eyeless on two runners
- [0022](0022-the-studio-boots-into-any-place.md) The studio: a dev build of the game that boots into any place, for agents and the owner; it only observes and teleports
- [0023](0023-five-parts-de-risk-first.md) Five parts, de-risk first: foundation, the core loop (the host go/no-go), the slice in two tracks, the shell, the build-out
- [0018](0018-the-creation-kit-is-a-tool-not-the-workflow.md) The Creation Kit is installed and used as a scripted tool; records are written by code
- [0024](0024-content-is-written-from-one-source-of-truth.md) Quests, dialogue and text are written from one source of truth, through generated briefs and the quest-write, quest-review and dialogue-write skills; old written lines are not used
- [0025](0025-a-detectives-faction.md) A detectives' faction, rival to the Shadowscales and the Night-Reed Chapter, escalating to a grand murder-mystery finale
- [0026](0026-everything-is-built-natively-the-skyrim-way.md) Places are rebuilt natively, the Skyrim way: the old project gives content (heightfield, designs, people), never machinery; navmesh by tes4skyrim's method; whole-body NPC templates
- [0028](0028-the-land-is-tropical-skyrim-through-skyrims-own-systems.md) The land is Tropical Skyrim through Skyrim's own systems: we author LAND, LTEX paint, regions (object and weather lists) and water; the engine does grass, weather and fog; the CK's region generator places trees, rocks and scatter once; BM&V and the Black Marsh mods are for buildings, props and creatures only
- [0030](0030-one-relational-world-database.md) One relational world database from day one: `world/schema.sql` in 3NF with keys and constraints, one JSONL file per table, read and written only through `db.py`; everything else derived; the writing skills read and write rows (built in 0.4 §0)
- [0031](0031-the-generated-world-is-its-own-master.md) The generated ground (WRLD, exterior CELL and LAND, later other bulk world outputs) is `ArgoniaWorld.esm`, a master of `Argonia.esm`, built by `make plugin` and checked by hash, never serialised to YAML
- [0029](0029-part-0-is-one-sequence-not-spikes.md) Part 0 is one sequence, not spikes: our stack, the agent's hands (SkyLink as the bridge), the pipeline and the first block; scenes are a save plus batch files; journeys read state and keep stills; no installer until release; no time budgets; a Starting state is the state now
- [0027](0027-build-in-the-order-of-the-usps.md) Build in the order of what makes Argonia worth playing: world and places, then story and people; combat rides the tuned stack until its map (2.7); the UI in two stages; the world track starts after G4; tools just in time

## Open owner calls

Calls only the owner can make. The planner raises each in an owner check-in when its chunk reaches it, with a
recommendation; the answer is recorded in the named record (or a new one) and the row is struck through.

| Id | Call | Needed by | Recommendation |
|---|---|---|---|
| O-1 | Fate of the old elder-souls-argonia EC2 machine (stopped; ~$23/month for its 250 GiB disk); the R2 keys are already copied (2026-10-29) and the frozen arrays pulled | 0.2 | Snapshot the disk to S3, then delete the volume; keep the R2 vault |
| O-2 | Subscription: 5x now, 20x from Part 4 (or Part 2's two tracks, if measured) | 0.1, 1.7, 2.17, 4.1 | 0013 |
| O-3 | Confirm the pinned runtime chosen in 0.2 | 0.2 end | 0002 rule |
| O-4 | Perks: invisible engine layer only, or a visible Morrowind-flavoured perk layer merged with vastei | 2.1 (asked in 1.7) | answered 2026-10-31: invisible for now, a visible layer kept possible (#20) |
| O-5 | Send permission requests to mod authors (drafted by agents, sent from the owner's Nexus/ModDB account): Black Marsh & Valenwood (dalecallen1987), MihailMods, Tropical Skyrim (Soolie) and its SSE port (78044), King of the Murkmire (pancake0723; AI clause), Xanmeer tileset (NorthwindBlue, DarthVitrial), Sign of Cipactli (URL unknown), Tamriel Worldspaces – Argonia (118678) | 0.3 | Send all in one batch early; build only on cleared mods |
| ~~O-6~~ | ~~Nexus Premium~~ | — | **Answered 2026-10-29: held; the key is `NEXUS_API_KEY` in the secrets file** |
| O-7 | Steam login on the GPU box (Steam Guard approval on the owner's phone, once) | 0.0 | Owner logs in through the stream once; then offline mode |
| O-8 | Music source: CC-licensed, commissioned, or Fal-generated (AI clause interactions) | 2.16 | CC-licensed first, Fal for gaps |
| O-9 | Split pauldrons/gauntlets if no sourced split meshes exist | 2.3 (asked in 1.7) | answered 2026-10-31: base Skyrim pieces as they are (#21) |
| O-10 | The opening's scope (default: the Opening Work Camp near Stormhold / Alten Corimont, as in the old main quest) | 3.3 | Default |
| O-11 | Voice: stay unvoiced text dialogue (old 0139/0143) | 1.7 | answered 2026-10-31: yes, plus Skyrim's voiced barks, Nordic-filtered (#22) |
| O-12 | Old repo's GitHub Pages build exposes converted assets publicly (outside this repo's scope) | any time | Owner's choice; flagged only |
| ~~O-14~~ | ~~Repo licence~~ | — | **Answered 2026-10-29: the recommendation stands** (GPL-3.0-or-later code, CC BY-NC-SA 4.0 content; decision 0015) |
| ~~O-15~~ | ~~Crossbows and thrown weapons back in~~ | — | **Answered 2026-10-27: yes** (decision 0016) |
| O-16 | Does one rest bank one pending level or all of them (left open by old 0147) | 1.7 | answered 2026-10-31: one per rest (#23) |
| O-17 | Evidence of the permissions the owner already holds (old sourcing log, 2026-09-24: "permission is held from every mod author in the pool, KotM included"): do they cover a public dependency and AI use? | 0.3 | Share the evidence; send new requests only where it falls short |
| O-18 | Quest target at maturity: 450–550 (old 0027) or 550–740 (old quest docs) | 4.1 | 450–550 baseline, 550–740 stretch |
| O-19 | Contribute our working ports back to universal-modder's knowledge base as scrubbed field notes (decision 0020 §7) | 2.7 onward | Yes, after the owner sees each note |
| O-13 | Public name: "Argonia" overlaps Tamriel Rebuilt's planned territory and the dormant Beyond Skyrim: Argonia; release title and Nexus wording must not imply either | 3.4 | "Elder Souls: Argonia" or similar, with a "not affiliated" line |
| O-20 | Publish the slice as early access once the stranger's install is clean | 3.5 | Yes: real players find install problems no test machine does |
| ~~O-21~~ | ~~The Morrowind dialogue corpus~~ | — | **Answered 2026-10-29: the owner rules it need not be private (it was pulled from UESP, a public site).** Applied as: the skills read it from `$ARGONIA_PRIVATE/dialogue/morrowind/` on the build VM (staged, 17 topic groups); it still stays out of the public repo and out of lines, briefs and issues, because the text is Bethesda's whatever site hosts it (0003); the owner may overrule that last point |

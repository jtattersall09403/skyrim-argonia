# P2: Foundation: the pinned stack, the installer, the test harness, the pipeline, the inventory

**Goal.** Turn the spikes into production foundations that every later phase builds on: a pinned and
reproducible dependency stack, one-command deploys to the GPU box, a full in-game test harness, the record
generation pipeline, the PrismaUI view harness, the vanilla quarantine baseline, the immersion inventory v1,
and permission requests out to mod authors.

**Starting state.** P1 exit gate passed; the pinned runtime is known (decision 0002); the spikes' code is in
`spikes/`.

**Read first.** Decisions 0002, 0003, 0006, 0009, 0010, 0012; research
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md) §1–5,
[skyrim-combat-traversal](../research/2026-10-27/skyrim-combat-traversal.md) §0, §5,
[assets-creatures](../research/2026-10-27/assets-creatures.md) §3d; [legal-and-sourcing.md](../legal-and-sourcing.md).

## Work packages

### WP2.1 The dependency manifest
- `data/dependencies.json`: every third-party mod the game needs, with: name, source URL (Nexus mod id and
  file id, ModDB id), exact version, file hash, licence/permission text summary, **AI clause** (none / forbids
  AI / unknown), redistribution flag (always "player downloads" unless licensed otherwise), why we need it,
  which systems depend on it, required or optional, runtime support, known conflicts (BFCO vs MCO/ABR/SkySA/
  Dual Wield Parrying/CGO; CPR vs Fenix Combat AI; SkyParkour vs SkyClimb; Poise mods vs Valhalla's TrueHUD
  bar; TDM vs other lock-on mods; Precision vs No Follower Attack Collision; OAR vs DAR).
- Includes the gameplay stack from G3 and the **asset mods** the world uses: Black Marsh & Valenwood (ModDB, a
  ~9 GB manual download), **Tropical Skyrim SSE (Nexus SSE 78044; the base-asset layer, decision 0006 §8)**, Argonian Xanmeer Tileset (181193), King of the Murkmire (190459),
  Here There Be Monsters – Sign of Cipactli (35933; confirm URL), Mud Mother Grove (146557), Xalfek home
  (55595), Darkwater Den (52630), Marsh-Rest (50111), Morrowind Imperial Keep Set Remodeled (133090), Morrowind
  Hlaalu Architecture (157997), Ayleid Ruins Building Kit (90667), CC Ayleid resources (83999), Project
  Rainforest SE (20636), Argonian weapon packs (67137, 35555, 79717, 48551, 23920), boat mods (SFSS canoe,
  Sailboats Expanded, RowBoats 35341 / Skyrim Rowboats 1019, Sailable Ship 72070), animation mods (Animated
  Armoury, Heavy Armory, spear mechanic, Rim Parry, Dynamic Dodge, CLAMBER if used), Monk Prayer Beads (63100),
  Landscape – Aendemika of Vvardenfell (Morrowind Nexus 59713, ground materials: check it is usable from Skyrim
  or drop). The full list comes from the old repo's README credits (lines ~48–320), `sourcing-register.json`,
  `tooling/asset-pipeline/mod-register.json` and `world/sources/assets/registry-summary.json`.
- `tools/deps_check.py`: verifies hashes of downloaded files, flags unknown AI clauses and missing permissions.
- **Acceptance:** every mod the old world JSON references (by mesh path or plugin) is in the manifest; the check
  lists zero unknowns or each unknown has an O-5 request open.

### WP2.2 Permission requests (owner call O-5)
- Draft, per author, a short message: what Argonia is (free, requires Skyrim, nothing redistributed; players
  download your mod), which of their files we reference, that the project uses AI for code and text (and Fal for
  minor 2D art), and the specific ask (OK to require your mod as a master/dependency and reference its records
  and meshes; OK despite the AI use). Authors: dalecallen1987 (Black Marsh & Valenwood), MihailMods (creatures),
  Soolie (Tropical Skyrim) and the author of its SSE port (78044) (plus its bundled GKB/Muppetpuppet/Tamira/Birds of Skyrim/lookout21 terms),
  pancake0723 (King of the Murkmire; its terms forbid use in mods that "make use of AI"), NorthwindBlue and
  DarthVitrial (Xanmeer), the Sign of Cipactli author, the Tamriel Worldspaces – Argonia author (118678; our
  heightfield's origin), plus any manifest row whose terms say "ask".
- **Owner step:** send them from the owner's accounts. Track replies in the sourcing register.
- **Acceptance:** all requests sent; each reply recorded; a mod whose author refuses or does not reply in 30 days
  is replaced or dropped, and the affected places re-kitted (P3/P9 note).

### WP2.3 Installer and deploy
- `installer/install.py` (runs on the GPU box; later on players' machines under Windows or Linux): checks the
  Skyrim exe version against the pin, downloads or locates each manifest mod (Nexus API with the owner's key if
  Premium, else a manual-download folder), verifies hashes, extracts in load order into a clean Data overlay,
  writes `plugins.txt`/`loadorder.txt`, runs Pandora headless, installs our plugin, DLLs and PrismaUI views,
  and runs the smoke scenario.
- `make deploy` from the build VM: build, rsync outputs to the GPU box, restart the game, wait for the bridge.
- **Acceptance:** from a fresh GPU box (`infra/gpu-box/create.sh` + `setup.sh` + `installer/install.py`), the
  smoke scenario passes with no manual steps except the documented manual downloads.

### WP2.4 ArgoniaBridge and the scenario runner (the in-game oracle)
- Grow the S1 bridge into `skse/ArgoniaBridge` (built only in dev configuration, never shipped): endpoints for
  teleport, console, Papyrus calls, state reads (quest stages, globals, actor values, AI package, position,
  inventory, dialogue topic list, nav path result, our ArgoniaCore state), time scale and wait, an input queue
  (keyboard/gamepad events), in-process screenshots with frame counters, and event subscriptions (hit events
  with timestamps from Precision callbacks, animation events) for timing checks.
- `tests/scenarios/*.yaml` + `tools/run_scenario.py`: steps, expectations, timeouts; crash detection (Crash
  Logger file, process gone) reported as a failure, never "still running" (AutoTest's flaw); the stale-frame
  check (two frames must differ); circuit breaker after 3 identical failures; artifacts to `out/runs/<id>/`.
- Skill `scenario-author` (from the old journey-author): how to write a scenario that can fail.
- **Acceptance:** 10 scenarios covering the smoke list pass; a deliberately broken one fails with a readable
  reason; a forced crash is reported as a failure within 60 s.

### WP2.5 The generation pipeline
- `tools/argonia_world` (Python package): loaders for every imported schema, the units module
  (`skyrim_units.py`), the FormID allocator (`data/formids.json`, append-only), intermediate JSON writers.
- `tools/ArgoniaGen` (C#): reads intermediate JSON, writes records with Mutagen into `Argonia.esm` (ESM flag;
  split into ESL-flagged helpers only if record counts require), then Spriggit serialize to `plugin/`.
- `make plugin` regenerates deterministically; `make check` includes a Spriggit round trip
  (serialize → deserialize → byte-identical plugin) and "regenerate twice, no diff".
- Papyrus build: the reference compiler (CK PapyrusCompiler under Wine) with the base script sources from the
  player's Skyrim install (never committed); compare russo-2025/papyrus-compiler as a native option.
- BSA packing with BSArch under Wine (our files only: UI images, fonts, Papyrus `.pex`, our textures if any).
- **Acceptance:** `make plugin && make check` green; an intentional record change shows up as a one-file
  Spriggit diff.

### WP2.6 Vanilla quarantine baseline (decision 0012)
- Our start quest: new game → a black screen → Argonia's opening cell (placeholder in the S4 block until P7);
  MQ101 and every start-game-enabled vanilla quest prevented; dragons, word walls and shouts removed from the
  player's world; the Tamriel worldspace unreachable.
- Scenario: list running quests after a new game and after 1, 10 and 50 in-game days (time skipped through the
  bridge); compare with `data/quarantine/allowed-quests.json`.
- **Acceptance:** the scenario passes; no vanilla music plays (bridge reads the music type).

### WP2.7 The immersion inventory v1 (track T-IMM)
- `tools/immersion/inventory.py`: enumerates every record type listed in decision 0006 §1 across our load
  order (Mutagen over the masters and dependencies), every vanilla menu SWF in the stack, every PrismaUI view,
  every music/sound record, every GMST/string; computes reachability from our world (placed, sold, levelled
  lists, spawns, menus); writes `data/immersion/inventory.jsonl`.
- Verdicts start as `unreviewed`; the gate fails only on reachable `unreviewed` rows **from P7 on** (until then
  it reports counts).
- **Acceptance:** the inventory lists every vanilla menu and every record our sample world references; counts
  by type are in PROGRESS.

### WP2.8 The PrismaUI view harness
- `ui/` (TypeScript, Vite): shared tokens from the old `packages/ui/src/tokens/palette.ts` (panel #0e1711, trim
  #6b7744, bone #d6cfb0, health #8f2e22, stamina #2a6b33, magicka #2f4e94, breath #386570, marker tan #d8b070,
  crime #e0705a), Pelagiad web font (OFL licence file shipped), components (window, scroll list, hyperlink
  text, tooltip, button, bar), a mock data server, Playwright screenshot tests at 1920×1080 and 1280×720,
  keyboard/gamepad navigation tests.
- The bridge between ArgoniaCore and views: a typed JSON message schema (`ui/schema/*.ts` and its C++ twin
  generated from one source).
- **Acceptance:** the G5 dialogue view moves into the harness and passes; screenshot tests are deterministic.

### WP2.9 Graphics baseline
- Community Shaders on the pinned runtime with the features we need (lighting, screen-space GI or ambient
  occlusion, volumetric lighting / god rays, improved fog, water); weather and image-space defaults neutral
  until P3/P8 restyle them. Choose CS over ENB (open source, maintained, scriptable config).
- **Acceptance:** the G2 benchmark scene holds the G2 frame-time bar with the baseline enabled.

### WP2.10 Saves, idle-stop, cost logging
- Saves on the GPU box backed up to S3 after each session and on stop; restore script.
- GPU box idle-stop (15 min); every start/stop logged with its cost estimate to `out/costs.jsonl`;
  `tools/cost_report.py` sums AWS cost and Claude usage for check-ins.
- **Acceptance:** a stop/start round trip keeps the save; the cost report shows the week.

## Exit gate
A fresh GPU box reaches a passing smoke scenario through the installer; the pipeline regenerates the sample
world deterministically; 10+ scenarios green; the dialogue view lives in the harness; the quarantine scenario
passes; the inventory v1 exists; all permission requests sent. P2 owner check-in: the stack and its licences
summary, permission replies so far, costs.

## Risks and fallbacks
- **Pandora fragile under Proton**: pin the Pandora version, generate on the box, keep the generated output
  hash in the manifest; if it breaks, Nemesis under Proton.
- **Nexus downloads without Premium**: a one-off manual session through the stream, cached to S3 privately
  (never public).
- **A dependency's author refuses**: replace it (the manifest names alternatives) or build the function
  ourselves on a higher route.

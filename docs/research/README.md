# Research

Dated research packs. A pack is evidence, not instructions: where a pack and a decision record disagree, the
decision wins. Facts that go stale (prices, mod versions, game runtime versions) must be re-checked before a
phase depends on them; each phase brief says which.

## 2026-10-27: founding research (planning conversation)

Written by research agents during the founding conversation. Confidence labels inside each file: "[V]" fetched
and read that day, "[K]" prior knowledge, "[I]" inference to prove on a sample.

| File | What it covers | Main consumers |
|---|---|---|
| [skyrim-tooling.md](2026-10-27/skyrim-tooling.md) | Mutagen, Spriggit, xEdit/Papyrus/LOD under Wine, navmesh and FaceGen gaps, SKSE builds from Linux, running Skyrim under Proton headless, agent bridge, distribution, mapping the world JSON onto Skyrim records, the S1–S4 tiers | 0.1–0.5, 2.W, 3.4 |
| [skyrim-morrowind-soul.md](2026-10-27/skyrim-morrowind-soul.md) | Which Skyrim mods already deliver Morrowind's systems (dialogue, attributes, levelling, death pile, item classes, armour slots, markers, journal, map, UI/HUD, danger, travel, economy) and what needs S2/S3 | Parts 1–2 (soul systems) |
| [skyrim-combat-traversal.md](2026-10-27/skyrim-combat-traversal.md) | Souls combat, poise, lock-on, AI, climbing, ladders, swimming, boats, ragdolls in Skyrim; the ArgoniaCombat plugin design; DS1 measure-implement-verify loop | 1.4, 1.7, 2.7, 2.13, 2.15 |
| [um-ghidra-lens.md](2026-10-27/um-ghidra-lens.md) | universal-modder's method, Ghidra and its MCP bridges, DSR/DS3 data tools (Paramdex, soulstruct, DSAnimStudio, Smithbox), experience reports, legal line, per-system lens | 0.1, 0.2, 1.4, 2.7, 2.13, 2.15, all |
| [hosting-streaming.md](2026-10-27/hosting-streaming.md) | AWS and alternative GPU prices, Selkies and other browser streaming, latency estimates, EULA notes | 0.1, 0.2, infra |
| [engine-feasibility-and-openmw.md](2026-10-27/engine-feasibility-and-openmw.md) | OpenMW, Mudcrab, DS3 assets, OpenMW mod scene: why not OpenMW, and the fallback | decision 0001 |
| [assets-creatures.md](2026-10-27/assets-creatures.md) | Morrowind/OpenMW asset and creature coverage for Black Marsh; Skyrim mod permission terms (Tropical Skyrim, Black Marsh & Valenwood, King of the Murkmire, Mihail) | 0.3, 2.W5, 4.1, legal |
| [forks-water-anims.md](2026-10-27/forks-water-anims.md) | OpenMW forks, water engine facts, animation mods and their permissions | decision 0001, 2.13, 2.15 |
| [audit-plan.md](2026-10-27/audit-plan.md) | Old repo: vision, every owner ruling (engine-agnostic vs three.js-tied), status, hardest problems, process lessons | inherited-rulings, ways-of-working |
| [audit-systems.md](2026-10-27/audit-systems.md) | Old repo: every gameplay system's design, numbers and build status | Parts 1–2 |
| [audit-world.md](2026-10-27/audit-world.md) | Old repo: setting, content inventory, what data ports, asset pools | 0.3, 2.W, 4.2 |
| [audit-infra.md](2026-10-27/audit-infra.md) | Old repo: research, infra, vault, agent model, licensing | 0.1, ways-of-working |
| [2026-10-29/reuse-audit.md](2026-10-29/reuse-audit.md) | The build-versus-reuse audit (0.1 §j): every PLAN §4 row with a verdict, licence, runtime and evidence; tes4skyrim read in full (MorrowindRuntime's sidecar input, the activate-slot interception, the navmesh writer as a binary spec); licence gaps (Mutagen GPL-3 no linking exception, PrismaUI custom, tes4skyrim's unfiled MIT); the paper-theme family and Magic Expanded | 0.3, 0.2, 0.4, 1.3 §b, 1.1 §a, 1.2 §0; 1.2; 2.7; 0015 |
| [quest-design-elder-scrolls.md](2026-10-27/quest-design-elder-scrolls.md) | What makes Elder Scrolls quests work or fail: no-marker directions, investigations, radiant criticism; reviewer checklist | quest-write, quest-review (0.1 §i, 1.4, 2.12, 4.3) |
| [quest-design-open-world-rpg.md](2026-10-27/quest-design-open-world-rpg.md) | Open-world RPG quest design: Three Clue Rule, hidden truth, knowledge matrix, pre/postconditions, consequence | quest-write, quest-review |
| [quest-shape-investigation.md](2026-10-27/quest-shape-investigation.md) | MURDER, MISSING, RECKONING; fair, solvable cases; accusation with evidence; the detectives' line | 0.1 §i, 2.12, 4.1 §d, 4.3 |
| [quest-shape-crime-and-deceit.md](2026-10-27/quest-shape-crime-and-deceit.md) | THEFT (commit and solve), FRAUD, SMUGGLING | 0.1 §i, 4.3 |
| [quest-shape-social.md](2026-10-27/quest-shape-social.md) | DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE (the Owing handled seriously) | 0.1 §i, 4.3 |
| [quest-shape-threat-and-journey.md](2026-10-27/quest-shape-threat-and-journey.md) | PREDATOR, CONTAMINATION, EXPEDITION; directions without markers | 0.1 §i, 4.3 |
| [quest-shape-otherworldly.md](2026-10-27/quest-shape-otherworldly.md) | HAUNTING, RITE, WONDER, Daedric and oddity quests | 0.1 §i, 4.3 |
| [questline-design.md](2026-10-27/questline-design.md) | Faction and main lines: line template, ranks, seeding, finale; detectives' line options | 0.1 §i, 4.1 §d, 4.3 |
| [quest-actions-and-skills.md](2026-10-27/quest-actions-and-skills.md) | Skill-based action in quests: verb families, combinations, faction profiles, variety measures | 0.1 §i, quest-write |

# Source map: what to take from elder-souls-argonia, and what not

The old repo is `jtattersall09403/elder-souls-argonia` (private, the owner's; three.js browser game). P0-WP0.6
imports from it at a recorded commit. The old repo is never modified by this project. Paths are relative to the
old repo root. Before importing, re-check each path exists (the old repo may have moved on); a missing path is
recorded in `world/IMPORTED_FROM.md`, never silently skipped.

## 1. Content data → `world/`

| Old path | What | New path | Notes |
|---|---|---|---|
| `world/sources/catalogue/places-*.json` | 827 places in 8 region packets | `world/sources/catalogue/` | |
| `world/sources/blueprints/*.layout.json`, `place.*.json` | ~20 built place layouts (poses of Skyrim kit pieces) | `world/sources/blueprints/` | P3-WP3.9 |
| `world/sources/placement/` (incl. `accepted-places.json`, `exterior-interior-links.json`, `boats.json`) | acceptance, interior links (38 kit interiors), moorings | `world/sources/placement/` | |
| `world/sources/registries/` (npcs, factions, items, creatures, quests, locks, loot, traps, pickpocket, detection, hazard-volumes, grave-stakes, creature-harvest, deeds, rumour-pools, markers, physical-materials, trainers, sourcing-register…) | the normalised record set | `world/sources/registries/` | every registry has a named consumer (P4-WP4.21 lists the ones no other WP names) |
| `world/sources/quests/` | quest lines and stages (main, factions, standalone, proposed, local-<region>) | `world/sources/quests/` | |
| `world/sources/dialogue/` | place lines, pool, culture sheets, stance, topics, facts, gates, glossary, exemplars | `world/sources/dialogue/` | exemplar corpus is Morrowind text quoted for style reference: keep it private (`$ARGONIA_PRIVATE`), not public, unless its size and use are fair-use-clear (owner decides) |
| `world/sources/text/` | journal, books/documents, signs, loading facts, names | `world/sources/text/` | |
| `world/sources/hydrology/` | hydrology graph (101 rivers, 615 reaches, 2,280 bodies), bodies, corrections | `world/sources/hydrology/` | |
| `world/sources/routes/` | road legs, travel services (23), harbour and rootworm stations | `world/sources/routes/` | |
| `world/sources/terrain/` (freeze.json, patches) | hashes and patches of the frozen heightfield | `world/sources/terrain/` | arrays themselves come from R2 (decision 0009 §5) |
| `world/sources/climate/`, `sky/`, `flora/`, `regions/`, `settlements/`, `sites/`, `demographics/`, `economy/`, `vocab/`, `anchors/`, `audio/` (metadata only) | climate, weather states, stars, flora and groundcover rules, region data, socket vocabulary | same under `world/sources/` | no audio files |
| `world/sources/lore/` | lore dossiers (era policy, sources) | `world/sources/lore/` | the Morrowind dialogue corpus file: private, as above |
| `world/sources/assets/registry-*.jsonl`, `registry-summary.json` | vault inventory (27,929 rows) and pool summary | `world/sources/assets/` | metadata only, no assets |
| `packages/world-schema/schemas/*.json`, `integrity.py` | 21 schemas and the integrity checker | `world/schemas/`, `tools/argonia_world/integrity.py` | |
| `packages/ui/src/tokens/palette.ts` | UI palette tokens | `ui/src/tokens/palette.ts` | |
| Pelagiad font files and licence (from the old repo or OpenMW) | font | `ui/fonts/` | OFL; allowlisted |

Read **in place** from the old repo, not imported: README credits (~lines 48–320), `tooling/asset-pipeline/mod-register.json`,
the settlement kit sourcing log (`docs/research/placement-settlements/settlement-kit-sourcing-log.md`, for O-17's
permission evidence), the old kit manifests used by the kit-id mapper (P1-S4).

## 2. Design docs → `docs/design/` (unchanged copies with a source header)

- `docs/world/` in full, especially `00-core.md`, `20-province-design.md`, `60-water-traversal.md`,
  `72-navigation-ai.md`, `75-combat-compatibility.md`, `76-stats-progression.md`, `90-asset-strategy.md`,
  `97-placement-principles.md`, `98-data-model.md`.
- `docs/quests/` in full (00-overview, 20-world-provisions, 30-main-quest, 40-factions, 60-writing-and-lore,
  85-condition-vocabulary…).
- `docs/standards/text/` (style guide) and `docs/standards/by-task.md`, `engineering.md` (for reference).
- `docs/research/combat-and-systems/` (dark-souls-poise-mechanics, stats-progression-reference-games,
  botw-climbing-system, skyrim-climbing-mod-survey, swim-climb-boat-implementation, player-boats-as-horses,
  source-game-systems-crosscheck, slice-systems-checklist), `docs/research/lore/creature-asset-availability.md`.
- `docs/phases/2-slice/` (2.1–2.15 briefs and outcomes) for design intent; `docs/phases/P-polish/backlog.md`
  (~470 rows) to triage in P7 for anything still relevant.
- `apps/combat-sandbox/docs/architecture/` (poise-and-stagger, ranged-combat, input) and
  `packages/game-core/src/combat/README.md`, `packages/game-core/src/stats/README.md`.
- `docs/decisions/` in full as `docs/design/old-decisions/` (the why behind every inherited ruling).
- `apps/ui-lab` screenshots are referenced by path in the old repo only (they contain rendered Skyrim assets:
  never copied here).

## 3. Ways of working → `.claude/`, `tooling/`

| Old path | Take | Change |
|---|---|---|
| `.claude/agents/deliver.md`, `deliver-small.md`, `find.md`, `run.md`, `check.md`, `research.md`, `reader.md` | frontmatter pattern (model, effort, tools, omitClaudeMd) and the core instructions | remove three.js/studio/kit specifics; point at this repo's gate and bridge |
| `.claude/agents/dialogue-lane.md`, `dialogue-writer.md`, `voice-reader.md`, `corpus-reader.md` | as-is in P0, adapted in P4 | output to ArgoniaCore data, not TS packages |
| `.claude/agents/place-builder.md` | becomes `world-builder` in P3 | Skyrim records, not GLB kits |
| `.claude/skills/text-review`, `dialogue-write`, `cost-review`, `routing-audit` | adapt | paths |
| `.claude/skills/journey-author` | becomes `scenario-author` (P2) | bridge YAML scenarios |
| `.claude/skills/place`, `kit-build`, `kit-mining`, `composite-author`, `modular-runs`, `visual-look` | read for lessons only | three.js kit pipeline; not copied |
| `tooling/repo-standards/brief_template.py`, `shell_guard.py` (subset), `job_guard.sh` (simplified), `session_tokens.py`, `owner_inbox.py`, `test_word_budget.py` | copy and trim | per decision 0011 |
| `tooling/repo-standards/agent_guard.py`, `role_guard.py`, `review_gate.py`, `commit_hunks.py`, `lane_*.py`, `memwatch.sh`, `cpu_watchdog.py`, `edit_ledger` | not at start | add one only after an incident it would have prevented |
| `tooling/bootstrap/` (idle-stop.sh, restore scripts), `docs/research/infrastructure/codespaces-migration-plan.md` | idle-stop idea; R2 restore recipe | AWS + this repo's layout |
| `tooling/asset-pipeline/` | Wine + Blender + PyNifly recipes, for reference only | Skyrim renders the meshes itself: no GLB conversion |
| `docs/standards/hooks.md`, decisions 0079, 0083, 0106, 0118, 0131, 0154–0156 | the doctrine | rewritten as `docs/ways-of-working.md` |

## 4. Not imported (deliberately)

- `apps/`, `packages/*` code (three.js renderer, R3F, Rapier, ecctrl, studio, game shell), except the data
  and docs listed above. The TypeScript dialogue/narrative runtime may be read in P1-S5 to decide whether it runs
  inside PrismaUI; if so it is copied then, with a note.
- `apps/world-studio/public/` (562 MB of converted Skyrim and mod assets): never.
- `lanes/` (2.3 GB of agent work folders): never; lessons are already in the audits.
- The Python world-generation pipeline (`tooling/world-generation/`, ~208k lines): not imported; the frozen
  outputs are. If terrain must be regenerated, run it in the old repo.
- `tooling/gpu-lane/` (RunPod/Chrome/WebGL harness): not applicable.

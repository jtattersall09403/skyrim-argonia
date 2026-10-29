# Source map: what to take from elder-souls-argonia, and what not

The old repo is `jtattersall09403/elder-souls-argonia` (private, the owner's; three.js browser game). 0.1
imports from it at a recorded commit. The old repo is never modified by this project. Paths are relative to the
old repo root. Before importing, re-check each path exists (the old repo may have moved on); a missing path is
recorded in `world/IMPORTED_FROM.md`, never silently skipped.

## 1. Content data → `world/`

| Old path | What | New path | Notes |
|---|---|---|---|
| `world/sources/catalogue/places-*.json` | 827 places in 8 region packets | `world/sources/catalogue/` | |
| `world/sources/blueprints/*.layout.json`, `place.*.json` | ~20 built place layouts (poses of Skyrim kit pieces) | `world/sources/blueprints/` | 2.W5 |
| `world/sources/placement/` (incl. `accepted-places.json`, `exterior-interior-links.json`, `boats.json`) | acceptance, interior links (38 kit interiors), moorings | `world/sources/placement/` | |
| `world/sources/registries/` (npcs, factions, items, creatures, quests, locks, loot, traps, pickpocket, detection, hazard-volumes, grave-stakes, creature-harvest, deeds, rumour-pools, markers, physical-materials, trainers, sourcing-register…) | the normalised record set | `world/sources/registries/` | every registry has a named consumer (2.12 §c and 2.14 lists the ones no other WP names) |
| `world/sources/quests/` | quest lines and stages (main, factions, standalone, proposed, local-<region>) | `world/sources/quests/` | |
| `world/sources/dialogue/` | place lines, pool, culture sheets, stance, topics, facts, gates, glossary, exemplars | `world/sources/dialogue/` (the written lines are reference only, never shipped or used as models: decision 0024 §7) | the exemplar corpus (`exemplars/morrowind-full.json`, `morrowind.json`) is Bethesda's text from UESP: it goes to `$ARGONIA_PRIVATE/dialogue/morrowind/`, never `world/`, and only once O-21 is answered |
| `world/sources/text/` | journal, books/documents, signs, loading facts, names | `world/sources/text/` | |
| `world/sources/hydrology/` | hydrology graph (101 rivers, 615 reaches, 2,280 bodies), bodies, corrections | `world/sources/hydrology/` | |
| `world/sources/routes/` | road legs, travel services (23), harbour and rootworm stations | `world/sources/routes/` | |
| `world/sources/terrain/` (freeze.json, patches) | hashes and patches of the frozen heightfield | `world/sources/terrain/` | arrays themselves come from R2 (decision 0009 §5) |
| `world/sources/climate/`, `sky/`, `flora/`, `regions/`, `settlements/`, `sites/`, `demographics/`, `economy/`, `vocab/`, `anchors/`, `audio/` (metadata only) | climate, weather states, stars, flora and groundcover rules, region data, socket vocabulary | same under `world/sources/` | no audio files |
| `world/sources/lore/` | lore dossiers (era policy, sources), **including `extrapolation/`** (the province in 4E 201, settlement register, quest-plan deltas; read by decision 0025's lore pass) | `world/sources/lore/` | `morrowind-dialogue-corpus-full.md`: private, as above |
| `world/sources/assets/registry-*.jsonl`, `registry-summary.json` | vault inventory (27,929 rows) and pool summary | `world/sources/assets/` | metadata only, no assets |
| `packages/world-schema/schemas/*.json`, `integrity.py` | 21 schemas and the integrity checker | `world/schemas/`, `tools/argonia_world/integrity.py` | |
| `packages/ui/` (src, tests, CSS: tokens, components, focus and viewport models, HUD, map, screens; ~18,400 lines of React 19) | our design system and every screen | `ui/` (1.2, 2.2) | decision 0017; assets only if provenance-clean: `Pelagiad.woff` + OFL (yes), Fal-made map glyphs (yes), `symbols.svg` (split: Fal-made symbols yes; the shapes exported from Skyrim's `hudmenu.gfx` are **not committed** but extracted on the installing machine by the ported `tooling/ui/extract_symbols.mjs`), `flourish-*.webp` (yes: the owner made them with ChatGPT) |
| Pelagiad font files and licence (from the old repo or OpenMW) | font | `ui/fonts/` | OFL; allowlisted |
| The engine-neutral rule packages with their tests: `packages/dialogue`, `narrative`, `economy`, `crafting`, `save`, `magic`, `world-time`, `text-catalogue`, and `packages/game-core/src/{stats,crime,factions,inventory,equipment,scheduling,perception,traps,travel,encounters,people,rng,validation}` | goal evidence for the goals list (decision 0026) | `private/old-packages/` (read-only), never built | **never** `combat`, `ai`, `anim`, `movement`, `locomotion` or render folders (decision 0019); our own code, so no licence issue |
| The old journey format and runners: `.claude/skills/journey-author/`, `journey.ts`, `seams-session.test.ts`, `apps/game/src/journey.test.tsx` | the journey script format, the starting point for the core runner | read in place by 0.4 | |
| `docs/research/combat-and-systems/slice-systems-checklist.md` | the slice coverage checklist | `docs/design/slice-systems-checklist.md` (rewritten in 2.17) | |
| `world/sources/blueprints/place.fixture.proving-ground*.json` | the studio's proving ground | regenerated through the pipeline in 0.4 | studio-only, never reachable in the game |

Read **in place** from the old repo, not imported: README credits (~lines 48–320), `tooling/asset-pipeline/mod-register.json`,
the settlement kit sourcing log (`docs/research/placement-settlements/settlement-kit-sourcing-log.md`, for O-17's
permission evidence), the old kit manifests used by the kit-id mapper (0.4).

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
- `docs/phases/2-slice/` (2.1–2.15 briefs and outcomes) for design intent; the old repo's `docs/phases/P-polish/backlog.md`
  (~470 rows), triaged once in 0.1: each row carried to its chunk or dropped with a reason.
- `packages/game-core/src/stats/README.md` (the sheet). The old combat docs
  (`apps/combat-sandbox/docs/architecture/`, `packages/game-core/src/combat/README.md`, the poise research) are
  **background on intent only**: the old combat is not ported (decision 0019).
- `docs/decisions/` in full as `docs/design/old-decisions/` (the why behind every inherited ruling).
- `apps/ui-lab` screenshots are referenced by path in the old repo only (they contain rendered Skyrim assets:
  never copied here).

## 3. Ways of working → `.claude/`, `tooling/`

| Old path | Take | Change |
|---|---|---|
| `.claude/agents/deliver.md`, `deliver-small.md`, `find.md`, `run.md`, `check.md`, `research.md`, `reader.md` | frontmatter pattern (model, effort, tools, omitClaudeMd) and the core instructions | remove three.js/studio/kit specifics; point at this repo's gate and bridge |
| `.claude/agents/dialogue-lane.md`, `voice-reader.md` | as-is in 0.1, adapted in 2.5 | output to ArgoniaCore data, not TS packages; drive the writing skills' agents |
| `.claude/agents/dialogue-writer.md`, `corpus-reader.md` | not copied | superseded by the writing-skills branch's `dialogue-writer` and `corpus-find` (§5) |
| `.claude/agents/place-builder.md` | becomes `world-builder` in 2.W5 | Skyrim records, not GLB kits |
| `.claude/skills/text-review`, `cost-review`, `routing-audit` | adapt | paths; **not** the old `dialogue-write`: ours was written from scratch (0024, §5) |
| `.claude/skills/journey-author` | becomes `scene-author` (0.4) | studio scenes and eyeless journeys for both runners |
| `.claude/skills/place`, `kit-build`, `kit-mining`, `composite-author`, `modular-runs`, `visual-look` | read for lessons only | three.js kit pipeline; not copied |
| `tooling/repo-standards/brief_template.py`, `shell_guard.py` (subset), `job_guard.sh` (simplified), `session_tokens.py`, `owner_inbox.py`, `test_word_budget.py` | copy and trim | per decision 0011 |
| `tooling/repo-standards/agent_guard.py`, `role_guard.py`, `review_gate.py`, `commit_hunks.py`, `lane_*.py`, `memwatch.sh`, `cpu_watchdog.py`, `edit_ledger` | not at start | add one only after an incident it would have prevented |
| `tooling/bootstrap/` (idle-stop.sh, restore scripts), `docs/research/infrastructure/codespaces-migration-plan.md` | idle-stop idea; R2 restore recipe | AWS + this repo's layout |
| `tooling/asset-pipeline/` | Wine + Blender + PyNifly recipes, for reference only | Skyrim renders the meshes itself: no GLB conversion |
| `docs/standards/hooks.md`, decisions 0079, 0083, 0106, 0118, 0131, 0154–0156 | the doctrine | rewritten as `docs/ways-of-working.md` |

## 4. Not imported (deliberately)

- `apps/`, `packages/*` code (three.js renderer, R3F, Rapier, ecctrl, studio, game shell), except the data
  and docs listed above, **`packages/ui`**, which is ported (decision 0017), and the engine-neutral rule packages
  above, which are read for goals only (decision 0026).
- `apps/world-studio/public/` (562 MB of converted Skyrim and mod assets): never.
- `lanes/` (2.3 GB of agent work folders): never; lessons are already in the audits.
- The Python world-generation pipeline (`tooling/world-generation/`, ~208k lines): not imported; the frozen
  outputs are. If terrain must be regenerated, run it in the old repo.
- `tooling/gpu-lane/` (RunPod/Chrome/WebGL harness): not applicable.

## 5. The writing-skills branches of this repo → `.claude/`, `docs/research/`

Two side branches of this repo hold work done with the owner before this plan's restructure. 0.1 §b brings
them in (the list, what is adapted, and the acceptance); they are never merged.

| Branch and path | Take | Change |
|---|---|---|
| `claude/blissful-bardeen-rstsfp`: `.claude/skills/dialogue-write/`, `quest-write/`, `quest-review/`; `.claude/agents/corpus-find.md`, `dialogue-writer.md`, `quest-reviewer.md` | all files | P-phase ids → chunk ids; its decisions 0017/0018 → 0024/0025; corpus under `$ARGONIA_PRIVATE`; no model names outside frontmatter; fitted to the import in 0.1 §i |
| the same branch: `docs/research/2026-10-27/quest-*.md`, `questline-design.md` (nine packs) | as-is | indexed in the research README |
| the same branch: its decisions, owner-brief and ACCOUNTING rows, PLAN, PROGRESS, CLAUDE.md, source-map and P-phase edits | already carried into this plan | not copied |
| `claude/sweet-rubin-96mlvj`: `tooling/dialogue/fetch_morrowind_corpus.sh` | its three copy paths | folded into `tools/import_old.py`'s private routing (§1) |

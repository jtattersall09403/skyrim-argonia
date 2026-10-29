<!-- imported unchanged from elder-souls-argonia docs/standards/by-task.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Standards by task

Which binding standards bear on which kind of task. A brief quotes the rows
for its task; read the named sections in full before you act. Sections are
from [engineering.md](engineering.md) (§ numbers), the
[style guide](text/style-guide.md) and [hooks.md](hooks.md).

## Every task

- engineering § 15: live documents are current (links resolve, retired words gone, research indexed).
- engineering § Running the checks: the one gate is `npm run check`, run by the `check` agent once per batch; a lane runs only the tests beside its change; after a red, `check.mjs --retry` reruns only the failing test files and stamps the job green on a pass.
- hooks.md: what the shell, role, agent and commit guards refuse.
- A `deliver` or `deliver-small` brief starts from `tooling/repo-standards/brief_template.py`, which prints the fields `agent_guard` requires.

## Code in `packages/` or `apps/`

- § 7 every data bundle carries a `schemaVersion`.
- § 8 no new module-level mutable singletons in `packages/`.
- § 4 every player-visible string lives in `packages/text-catalogue` with an id.
- § 17 saved state is versioned, serialisable data from the moment a system is written.
- § Performance checklists: draw calls, triangles, quality bands, budgets.
- § 16 what ships is compressed; the payload is a budget with a gate.
- A game screen is built from `packages/ui` and lifted into the studio and apps/game by `packages/ui/README.md` § Lifting a screen, its view built in `@elder-souls/scene/ui`.

## Tooling, generators, miners, exporters

- § 6 determinism in world building.
- § 19 one place changes without re-deriving the others: every place tool takes `--place <id>`.
- § Memory discipline: chunk A×B work, load once, free between items, float32; a peak target beside the time target.
- § 14 a gate reads shipped data and has been seen to fail.
- hooks.md: `job_guard.sh` for heavy jobs; miners carry `--assets` or `--rule-change`.

## Data and records under `world/sources/` or runtime data

- § 2 stable ids and a registry from the first placed object.
- § 18 one home table per entity, references by id, the integrity gate.
- § 11 one content-unit convention.
- § 7 `schemaVersion`.

## Placing anything (places, POIs, interiors, kits)

- § 2 stable ids; § 3 ownership and value ship with placement.
- § 13 the placement lesson moves with the placement work.
- § 19 per-place scope.
- § 9 the creature statblock schema precedes creature placement.

## Quests, dialogue, conditions

- § 1 the typed condition/action vocabulary exists before content is authored.
- § 5 the quest runtime is headlessly drivable.
- § 4 text catalogue ids.

## Assets (meshes, textures, animations, kits)

- § 10 source, hash and credit (root README § Credits) in the same change.
- § 16 compressed shipping and the download budget.

## Player-visible or world-record prose

- Writers: [style guide](text/style-guide.md) § Before you write, § 1 house rules, § 2 the voice, § 3 the surface, § 4 before you commit.
- Reviewers: [style core](text/style-core.md), the reader's one-file checklist.
- engineering § 12 prose is written against the record and checked against it.
- The `text-review` skill runs before commit: one `reader` pass, then the prose linter.

## Hooks and agent tooling

- hooks.md in full; engineering § 14 (make the hook fail on purpose once) and § Running the checks.

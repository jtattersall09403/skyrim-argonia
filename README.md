# Elder Souls: Argonia (Skyrim SE)

A free, non-commercial total conversion for **The Elder Scrolls V: Skyrim Special Edition**, set in Black Marsh,
with Morrowind's systems and spirit, Dark Souls-style combat, climbing, swimming and sailable boats.

**Status:** planning complete; Phase 0 (bootstrap) next. See [docs/PLAN.md](docs/PLAN.md) and
[docs/PROGRESS.md](docs/PROGRESS.md).

## What this repo contains, and what it never will

This repository is public on purpose. It contains only our own source code, our own generated data, docs and
tests. **It never contains any file from Skyrim, any other game, or any third-party mod**, converted or not.
To play, you will need your own copy of Skyrim Special Edition and a list of free mods downloaded from their
authors' pages; the installer will guide you. Details: [decision 0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md).

Not made, distributed or supported by ZeniMax Media, Bethesda Softworks, FromSoftware or Bandai Namco. Not
affiliated with Tamriel Rebuilt or Beyond Skyrim. Built largely with AI assistance (Claude Code).

## Layout

| Path | What |
|---|---|
| `docs/` | plan, phases, decisions, research, ways of working, legal |
| `world/` | the world's source data (imported from the earlier three.js project) |
| `tools/` | generators (Python, C# with Mutagen) |
| `plugin/` | the generated plugin as Spriggit YAML |
| `skse/` | our SKSE plugins (C++, CommonLibSSE-NG) |
| `papyrus/` | our Papyrus scripts |
| `ui/` | PrismaUI views (HTML/CSS/TypeScript) |
| `data/` | combat golden table, dependency manifest, immersion inventory, sourcing register |
| `installer/` | install and verify scripts |
| `infra/` | machine setup and operations |
| `tests/` | in-game scenarios and unit tests |
| `tooling/` | guards and agent tooling |

## Credits

Credits are generated from `data/sourcing-register.json` once it exists (Phase 2). The plan already depends on
the work of many mod authors; see [docs/legal-and-sourcing.md](docs/legal-and-sourcing.md).

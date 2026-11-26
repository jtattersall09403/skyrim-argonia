# 0002: One pinned Skyrim runtime

**Status:** decided 2026-10-27 (owner: "Yes on pinning the Skyrim version"). The pin is **1.7.104 with SKSE 2.3.1**
(Steam build 24914197), where the whole dependency list loads.

## Context

Bethesda shipped 1.7.99 and 1.7.104 in 2026, and many SKSE plugin stacks broke; the community's usual fix is
rolling back to 1.6.1170. CommonLibSSE-NG and Address Library let one of our own DLLs cover several runtimes, but
third-party dependencies each support their own range. King of the Murkmire's meshes use textures from the
Creation Club and AE archives, so a 1.5.97 pin would drop it or need those masters.

## Decision

1. We support **exactly one Skyrim runtime** at a time. Our own plugins are built multi-runtime (NG) so that
   moving the pin is cheap.
2. The play machine is never updated by Steam: Steam runs in offline mode with updates disabled, and the exact
   depot manifest is recorded in `infra/README.md` so the machine can be rebuilt (steamcmd `download_depot` of that
   manifest).
3. Players get a downgrade guide in the install docs, and the installer refuses to run on another version (it
   reads the exe version).
4. A move of the pin is a decision-record change with a full smoke run of the dependency list.

## Consequences

- Dependency mods are pinned to exact file versions that support the runtime; a mod with no build for it is
  swapped for an equivalent or dropped.
- An upstream Skyrim update never breaks the owner's game: the streamed machine does not update.

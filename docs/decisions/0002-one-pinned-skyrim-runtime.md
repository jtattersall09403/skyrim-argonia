# 0002: One pinned Skyrim runtime

**Status:** decided 2026-10-27 (owner: "Yes on pinning the Skyrim version"). Which version: chosen in Phase 1
(P1-S6) and recorded here.

## Context

Bethesda shipped 1.7.99 (20 Aug 2026) and 1.7.104 in 2026. Many SKSE plugin stacks broke; the community's
usual fix is rolling back to 1.6.1170 through the Steam depot
([gist](https://gist.github.com/SuperMalinge/203119e71b005fdb5b19336bce7bf615)). SKSE builds: AE 2.3.1 for
1.7.104, SE 2.0.20 for 1.5.97, GOG 2.2.6 for 1.6.1179; the silverlock page's "latest Steam 1.9.32" line
contradicts the rest and must be checked against the actual exe. CommonLibSSE-NG + Address Library let one of
*our* DLLs cover 1.5.97 through 1.7.x, but third-party dependencies each support their own range.

## Decision

1. Argonia supports **exactly one Skyrim runtime** at a time. Our own plugins are still built multi-runtime
   (NG) so that moving the pin is cheap.
2. Candidates, decided by Phase 1 test S6: **1.6.1170** (widest mod ecosystem, the community's rollback
   target) or **1.7.104** (current; BFCO 3.100.8+, Underwater NG, FreeClimb, CSF 3.2 support it). Rule: the
   version on which the whole pinned dependency list (docs/phases/P2-foundation.md, WP2.1) loads and passes the
   smoke test wins; ties go to 1.6.1170.
3. The GPU machine image is never updated by Steam: Steam runs in offline mode with updates disabled, and the
   exact depot manifest is recorded in `infra/README.md` so the image can be rebuilt (steamcmd
   `download_depot` of that manifest).
4. Players get a **downgrade guide** in the install docs (P10) and the installer refuses to run on another
   version (it reads the exe version).
5. A move of the pin is a decision-record change with a full smoke run of the dependency list.

## Consequences

- Dependency mods are pinned to exact file versions that support the chosen runtime (P2-WP2.1).
- An upstream Skyrim update never breaks the owner's game: the streamed box does not update.

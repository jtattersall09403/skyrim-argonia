# 0015: The repo's licence is chosen in 0.1; every component's licence obligations are tracked

**Status:** recommendation 2026-10-27; **applied as the recommendation on 2026-10-29** (`LICENSE` GPL-3.0-or-later,
`LICENSE-content` CC BY-NC-SA 4.0, a README section), so the public repo is not unlicensed; owner call **O-14**
confirms or changes it (the owner is the sole author, so a change before any outside contribution is free).
Noted from the reuse audit: Mutagen is GPL-3.0-only with no linking exception and FreeClimb GPL-3.0-only, both
compatible with GPL-3.0-or-later code.

## Context

The repo is public from day one (0003) but has no licence. Some components we write will link or fork GPL code:
ArgoniaGen links Mutagen (GPL-3.0); a FreeClimb fork would be GPL-3.0-only; Precision/TDM/OAR/TrueHUD are
GPL with modding exceptions; vendored universal-modder is MIT; PrismaUI forks need its author's permission.
Choosing late risks mixing code under incompatible terms.

## Decision (recommended; owner confirms O-14)

1. **Code:** GPL-3.0-or-later for the whole repo's code (compatible with Mutagen and a FreeClimb fork, and with
   the modding exceptions of the GPL SKSE frameworks we call).
2. **Our original content** (world data we write, dialogue and books, docs, our UI art and Fal-made art,
   music we commission): **CC BY-NC-SA 4.0** (non-commercial, matching the owner's "free" rule and the CK EULA's
   non-commercial terms).
3. Third-party files keep their own licences: Pelagiad (OFL, with its licence file), vendored universal-modder
   (MIT, with its licence file and credit).
4. `data/dependencies.json` and `data/sourcing-register.json` carry a **licence column** and a "linked or forked
   by" column naming which of our binaries include GPL code; 3.4 checks the release's licence notices
   against it.

## Consequences

- 0.1 adds `LICENSE` (GPL-3.0), `LICENSE-content` (CC BY-NC-SA 4.0) and a short licensing section in README.

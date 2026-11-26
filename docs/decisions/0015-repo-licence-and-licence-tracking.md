# 0015: Repo licence and licence tracking

**Status:** decided 2026-10-29 (owner: "I agree with the recommendation"); applied the same day (`LICENSE`
GPL-3.0-or-later, `LICENSE-content` CC BY-NC-SA 4.0, a README section). The owner is the sole author, so a change
before any outside contribution is free.

## Context

The repo is public ([0003](0003-nothing-shipped-that-players-do-not-own.md)). Some components we write link or fork
GPL code: our plugin tools link Mutagen (GPL-3.0, no linking exception); a FreeClimb fork would be GPL-3.0-only;
Precision, TDM, OAR and TrueHUD are GPL with modding exceptions; vendored universal-modder is MIT. Choosing late
risks mixing code under incompatible terms.

## Decision

1. **Code:** GPL-3.0-or-later for the whole repo's code (compatible with Mutagen and a FreeClimb fork, and with
   the modding exceptions of the GPL SKSE frameworks we call).
2. **Our original content** (world data we write, dialogue and books, docs, music we make): **CC BY-NC-SA 4.0**
   (non-commercial, matching the owner's "free" rule and the CK EULA's non-commercial terms).
3. Third-party files keep their own licences: Pelagiad (OFL, with its licence file), vendored universal-modder
   (MIT, with its licence file and credit).
4. `mods/dependencies.json` and `mods/sourcing-register.json` carry a licence column and a "linked or forked by"
   column naming which of our binaries include GPL code; the release check compares the release's licence notices
   against it.

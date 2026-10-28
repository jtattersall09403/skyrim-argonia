# 0004: Dark Souls Remastered is the combat oracle; we match DS1 timings; knowledge only

**Status:** decided 2026-10-27 (owner: "we should match DS1 for timings"; prefers DS1 Remastered, owns it;
DS3 only came up because ds3-open-re looked like tooling, which it is not: it is netcode).

## Context

The old design (elder-souls-argonia `docs/world/76-stats-progression.md`, decision 0037 there) specified DS1
poise and roll i-frames 13/11/9 frames by equip tier, a 0.1–0.29 s parry window and a ~5 s poise refill.
The Dark Souls wiki lists 11 i-frames for fast, mid and fat rolls and 13 only for the ninja flip, which
conflicts with 13/11/9. Bandai Namco's EULA forbids reverse engineering and derivative works; DSR servers are
live (since Nov 2022) though it has no client anti-cheat.

## Decision

1. **Timings and combat numbers come from measuring DS1 Remastered.** Where the old design's numbers differ
   from DSR, **DSR wins** (owner ruling). Stats-driven damage, mitigation and attribute effects still come from
   Argonia's own Morrowind-based model (decision 0005): DS1 supplies the *feel* (windows, frames, poise
   behaviour, stamina rhythm, AI shape), Argonia supplies the *character sheet*.
2. **Knowledge only.** We record derived numbers in our own golden table
   (`data/combat/golden-table.json`) with a provenance tag per value (`DSR: c0000 a00_0300 TAE ev InvokeAttack
   0.433–0.567 s`, `DS3:` for the rare secondary values, `OWNER:` for owner overrides, `GUESS:` for
   unmeasured placeholders). No param dumps, TAE files, AI Lua, decompiles or animations ever enter the repo
   (decision 0003). Decompiled text and dumps live under `$ARGONIA_PRIVATE` on the VM, never committed.
3. **Tools, in order of preference:** soulstruct (Python, native on Linux: params, AI decompile), Paramdex
   DS1R names, DSAnimStudio (TAE timings; Wine or a Windows box), in-game capture offline (Steam offline mode,
   proxy DLL removed before any online session, separate backed-up save). Ghidra only for a named native
   constant the data cannot answer, via targeted headless PyGhidra scripts on a runtime memory dump (DSR's exe
   is packed on disk), never a whole-binary chat session.
4. **DS3** is a secondary source only for what DS1 lacks (HKS input-buffer rules, hyper-armour), tagged `DS3:`.
5. **Animations stay Skyrim-side** (vanilla or permitted mod movesets), brought to the golden table's timings
   by the mechanism in decision 0014 §2 (runtime speed and window control first; an install-time patcher of the
   player's own clips only if needed), never by shipping edited clips. No
   FromSoftware-derived movesets (several Nexus packs are DS3/ER rips: excluded whatever their Nexus page says).
6. **Verification:** every window edge in game is within ±1 DS1 frame (33 ms, aim 16 ms) of the golden table,
   checked by the scripted test dummy at capped 30 and 60 fps (1.4, 2.7 §f).

## Consequences

- The 13/11/9 question is first answered by gate G6 (0.2) and confirmed (with the full table) in 2.7 §b; the
  result is written back here.
- Decision 0019 widens this record: DSR specifies the whole combat system, not only timings; nothing of the old
  project's combat (code, constants, animation choices) is inherited.
- Burden tiers: Argonia's ratios (fast < 0.2, mid < 0.35, fat < 1, of carry capacity) define the tiers; DSR
  supplies the i-frames and recovery per tier (DSR's own 25%/50% thresholds do not bind).
- Combat feel depends on Skyrim animations matching DS1 windows; timing is fixed on the animation side through
  decision 0014 §2, never by bending the numbers.

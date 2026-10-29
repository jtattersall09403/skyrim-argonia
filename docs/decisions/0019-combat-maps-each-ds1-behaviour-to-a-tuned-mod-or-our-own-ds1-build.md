# 0019: Combat maps each DS1 behaviour to a tuned mod or to our own build of DS1's system

**Status:** decided 2026-10-27, revised twice on 2026-10-29.

- **2026-10-27:** the old project's combat is not to be reproduced ("lots of the combat and animations and
  stuff in our previous repo was quite bad and buggy… I want Dark Souls-like combat tailored to be as close as
  possible to the Dark Souls 1 Remastered numbers and engine/system/feel, but wired to our stats").
- **2026-10-29, after playing the stock souls-like stack in 0.0** (combat "felt reasonably good"): "we shouldn't
  build it unless we *need* to… a deep dive into how far we can go by using existing mods and perhaps tweaking
  slightly (e.g. the backstab single press)".
- **The same day, correcting an overshoot that made mods the whole answer:** "map out what we can do with mods
  (including tuning them) and what we need to build fully from DS1's system. I don't mean we should abandon that
  whole 'rebuild DS1's system' thing completely, I just mean we should make informed decisions about how much of
  it we need to rebuild."

## Decision

1. **DS1 Remastered's whole combat system is the target.** That means:
   - the action state machine and its input buffering and cancel rules;
   - startup, active and recovery per attack;
   - roll and backstep i-frames and recovery by equip load;
   - stamina costs, regeneration, its delay and exhaustion;
   - guard: stability, chip damage, guard break;
   - parry, the parried state and riposte; backstab;
   - poise, stagger levels and knockback, and hyper-armour;
   - per-hitbox damage rates;
   - lock-on;
   - throws where a boss needs them;
   - enemy AI shape.

   All of it is measured from the owner's copy (decision 0004) and wired to our stats.
2. **The combat map decides, behaviour by behaviour, how each part is reached.**
   `docs/research/<date>/combat-map.md` (2.7 §0; moved from 1.4 by decision 0027) has one row per DS1 behaviour, giving:
   - the mods that could carry it, tried in game;
   - how close they get once tuned, measured against DSR where a number decides it;
   - what a small tweak would add;
   - the verdict, one of three:
     - **mod, tuned:** settings only;
     - **mod, tweaked:** a config patch, a Papyrus or SPID shim, or a fork of an open mod;
     - **build from DS1:** our own implementation of that part of DS1's system, from measured numbers.

   Verdicts weigh fidelity to DS1 against cost and risk, and the owner sees the map before any "build" row
   starts. A row can move later (tuned first, built when the fidelity is not good enough).
3. **Building from DS1 is a real option, not a last resort.** Where a mod's model cannot express DS1 the rows are
   built: true DS1 poise, input buffering and cancel windows, i-frames by equip load, and the parried and riposte
   states are likely candidates. The rows a mod already does well stay the mod's. Already settled:
   - The 0.0 stack is the starting stock (`infra/gpu-box/combat-test-mods.json`): SkySA with the Elder Souls sword
     moveset, Precision, TDM, TrueHUD, TK Dodge RE with Dynamic Dodge Animation and IFrame Generator, Elden Parry
     with Rim Parry and Execution, Modern Stagger Lock, MaxsuBlockOverhaul, OAR-added Stamina Cost, and One Click
     Power Attack for R2.
   - The candidates beyond it: BFCO, SCAR, CPR and the like.
   - Known tweaks: the backstab on a single press, and the gamepad in DS1's layout (0.0 §d).
4. **Argonia's stats are wired in whichever way the row is reached.** Damage, stamina, carry and protection come
   from the Morrowind-based sheet (decision 0005), by game settings, perk entry points or mod settings for mod
   rows, and by our core for built rows. One written wiring spec (2.7 §a) covers both, so the sheet stays one
   source of truth.
5. **The old project's combat is not inherited**:
   - not its code (`packages/game-core/src/combat`, `character`'s combat runtime);
   - not its tuned constants (the 0.1–0.29 s parry, 13/11/9 i-frames, 5 s poise refill, 20 m lock-on, head ×2,
     weapon-family parries);
   - not its animation choices or animation-pack decisions (old 0040);
   - not its combat tests as acceptance.

   Old designs are background on intent only.
6. **Movesets are chosen for fidelity**: permitted Skyrim movesets whose motion already reads like DS1 (weight,
   wind-up, recovery), corrected at runtime if at all (decision 0014 §2); never FromSoftware-derived packs.
7. **Engineering rigour for built rows, because the old combat was buggy.** Built rows run on one state machine
   in a pure C++ core with exhaustive unit tests (L2), driven in game through a thin adapter over the mods'
   APIs (Precision, TDM, OAR, the dodge and attack frameworks). Every DS1 window we set has a ±1-frame in-game
   test (L4), and every bug found becomes a test before it is fixed. Mod rows are pinned in the dependency
   manifest and checked in game.

## Consequences

- 1.6 runs the tuned stack on the sheet, settings only (decision 0027 §3). 2.7 makes the combat map first, then
  reaches each row as the map decides (tuned, tweaked or built) for every class, archetype, boss and encounter.
- G6 (measuring DSR) runs as soon as a map row needs DSR numbers. G9 (runtime timing control) runs as soon as a
  set window cannot be met by settings. The owner ruled on 2026-10-28 that they run only when needed.
- `ArgoniaCombat` holds the built rows, and its scope is what the map sends to it.
- Inherited rulings keep the old combat records Drop (as implementation) or Adapt (as intent only).

# 0019: Combat is existing mods, tuned; we build only where they fall short

**Status:** decided 2026-10-27, revised 2026-10-29. The owner first ruled that the old project's combat is not to
be reproduced ("lots of the combat and animations and stuff in our previous repo was quite bad and buggy… I want
Dark Souls-like combat tailored to be as close as possible to the Dark Souls 1 Remastered numbers and
engine/system/feel, but wired to our stats"). After playing the stock souls-like stack in 0.0 (combat "felt
reasonably good") the owner corrected the plan: "we shouldn't build it unless we *need* to… a deep dive into how
far we can go by using existing mods and perhaps tweaking slightly (e.g. the backstab single press) and then only
build what genuinely needs building."

## Decision

1. **Existing mods are the combat system.** The souls-like stack from 0.0 (SkySA with the Elder Souls sword
   moveset, Precision, TDM, TrueHUD, DMCO on Dodge Framework NG with IFrame Generator, Elden Parry with Rim Parry
   and Execution, Modern Stagger Lock, MaxsuBlockOverhaul, OAR-added Stamina Cost;
   `infra/gpu-box/combat-test-mods.json`) is the starting point, widened with other permitted mods (BFCO, SCAR,
   CPR and the like) where they cover more of DS1. Each mod is reached in the
   reuse route of decision 0010: its own settings first, then a small tweak (a config patch, a Papyrus or SKSE
   shim, a fork of an open mod), and our own code only last.
2. **A deep dive decides what, if anything, we build.** Before anything is written, 1.4 lists DS1's combat
   behaviours (the action states, rolls and backstep by load, guard and guard break, parry, parried state and
   riposte, backstab, poise and stagger, stamina rhythm, running, rolling, backstep and plunging attacks, kicks,
   lock-on, enemy AI shape) and records, for each, the mod that covers it, how close it is, the setting or tweak
   that closes the gap, or why it genuinely needs building. That gap register
   (`docs/research/<date>/combat-gap-register.md`) is the only licence for new combat code. Known tweaks from the
   0.0 test: backstab on a single press instead of block-then-attack; stagger, poise and interrupts; a riposte
   animation; stamina and damage tuning; kicks and the running, roll and backstep attacks.
3. **DS1 Remastered is the reference, not a blueprint.** The owner's copy is the yardstick for judging a gap and
   tuning a setting (decision 0004): a behaviour or window is measured from DSR only when a gap or a tuning
   question needs the number. No DS1 state machine is rebuilt for its own sake.
4. **Argonia's stats are wired in through the mods.** Damage, stamina, carry and protection come from the
   Morrowind-based sheet (decision 0005) by the cheapest route that reaches them: game settings, perk entry points,
   mod settings, then a thin hook. The wiring is written down (2.7 §a) so the sheet stays one source of truth.
5. **The old project's combat is still not inherited**: not its code (`packages/game-core/src/combat`,
   `character`'s combat runtime), not its tuned constants (the 0.1–0.29 s parry, 13/11/9 i-frames, 5 s poise
   refill, 20 m lock-on, head ×2, weapon-family parries), not its animation choices or animation-pack decisions
   (old 0040), and not its combat tests as acceptance. Old designs are background on intent only.
6. **Movesets are chosen for fidelity**: permitted Skyrim movesets whose motion already reads like DS1 (weight,
   wind-up, recovery), corrected at runtime if at all (decision 0014 §2); never FromSoftware-derived packs.
7. **Rigour wherever we do write code.** Anything the gap register sends to our code is a pure C++ core with
   unit tests (L2) behind a thin adapter, with an in-game check that can fail (L4); every combat bug found becomes
   a test before it is fixed. Tuned mod settings are pinned in the dependency manifest and checked in game.

## Consequences

- 1.4 is the deep dive and the tuned first rung: the gap register, the stack tuned for one weapon class and one
  archetype, the small tweaks, and only the code the register licenses. 2.7 widens the tuned stack to every
  class and archetype, the bosses and the encounters, and builds only the register's remaining gaps.
- G6 (measuring DSR) and G9 (runtime timing control) run only when the gap register needs them (owner ruling
  2026-10-28).
- `ArgoniaCombat` exists only if the register licenses code; its scope is the register's gaps.
- Inherited rulings keep the old combat records Drop (as implementation) or Adapt (as intent only).

# 0019: Combat is rebuilt from Dark Souls Remastered, not ported from the old project

**Status:** decided 2026-10-27 (owner: "lots of the combat and animations and stuff in our previous repo was
quite bad and buggy so I do not want the new plan to reproduce that… I want Dark Souls-like combat tailored to be
as close as possible to the Dark Souls 1 Remastered numbers and engine/system/feel, but wired to our stats").

## Decision

1. **DSR is the specification for the whole combat system**, not just its timings: the action state machine (what
   the player and enemies can do from each state), input buffering and cancel rules, startup/active/recovery per
   attack, roll and backstep i-frames and recovery by equip load, stamina costs, regeneration, its delay and
   exhaustion, guard (stability, chip damage, guard break), parry, parried state and riposte, backstab, poise and
   stagger levels and knockback, hyper-armour where DS1 has it, per-hitbox damage rates where DS1 data defines them,
   lock-on (DS1's `LockCamParam` range and switching), throws/grabs where a boss needs them, and enemy AI shape.
   Measured from the owner's copy (decision 0004), recorded in the golden table with provenance.
2. **Argonia's stats are wired in, not substituted.** DS1 governs how combat *behaves and feels*; Argonia's
   Morrowind-based sheet governs *who you are*: how hard you hit, how much stamina you have, how much you can
   carry, how well armour protects you. A written **wiring specification** (2.7 §a) maps each DS1 quantity onto
   our attributes, skills and formulas (e.g. DS1 weapon scaling → our skill score k(s) and Strength; DS1 Endurance
   stamina and equip load → our Endurance, carry capacity and burden tiers; DS1 armour defence and poise → our
   armour rating, mitigation and armour skills), preserving DS1's ratios at equivalent character strength. Where
   the two disagree on feel, DS1 wins; where they disagree on progression, our sheet wins; the spec records each
   case.
3. **The old project's combat is not inherited**: not its code (`packages/game-core/src/combat`, `character`'s
   combat runtime), not its tuned constants (the 0.1–0.29 s parry, 13/11/9 i-frames, 5 s poise refill, 20 m
   lock-on, head ×2, weapon-family parries), not its animation choices or animation-pack decisions (old 0040), and
   not its combat tests as acceptance. Old designs are consulted only as background on intent; any old rule DS1 has
   no equivalent for is dropped unless the owner asks for it back.
4. **Animations are chosen for fidelity first.** Movesets are surveyed and picked because their motion already
   reads like DS1 (weight, wind-up, recovery) and is close to DS1's measured windows, so timing control (decision
   0014 §2) makes small corrections, never rescues a poor clip. Original Skyrim-modder movesets with permission;
   never FromSoftware-derived ones.
5. **Engineering rigour, because the old combat was buggy:** the combat engine is one state machine in a pure C++
   core with exhaustive unit tests (L2), driven in game through a thin adapter over Precision/BFCO/TDM/OAR; every
   DS1 window has a ±1-frame in-game test (L4); every bug found becomes a test before it is fixed; feel is judged by
   side-by-side comparison with DSR footage captured under the same inputs (L5, reason: feel), then the owner.

## Consequences

- Combat (first rung 1.4, whole 2.7) is written around DSR as the specification (2.7 §a wiring spec, 2.7 §b measurement, 2.7 §c state machine).
- Decision 0004's "old constants" consequences are replaced by this record; inherited-rulings mark the old combat
  records Drop (as implementation) or Adapt (as intent only).

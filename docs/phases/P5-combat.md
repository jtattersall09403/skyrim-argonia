# P5: Dark Souls 1 combat on Argonia's stats

**Goal.** Combat that feels like Dark Souls Remastered (timings measured from DSR, decision 0004) while damage,
mitigation and stamina come from Argonia's Morrowind-based sheet (decision 0005), for the player and every
enemy, with souls-style enemy AI and authored bosses.

**Starting state.** P2 passed (stack pinned with Precision, TDM, BFCO, OAR, TK Dodge, Elden Parry, SCAR, CPR,
TrueHUD; bridge with hit and animation event timestamps). G6 gave the first golden-table rows. P4-WP4.1 stats
are in place (or stubbed with the same interface).

**Re-check before starting:** BFCO, Precision (and its 1.7.x port), TDM, OAR, SCAR, CPR versions on the pinned
runtime; the DSR patch version.

**Read first.** Decisions 0004, 0014 (§2: how timing reaches the game, proven in G9); [skyrim-combat-traversal](../research/2026-10-27/skyrim-combat-traversal.md) §1,
§3, §4 in full; [um-ghidra-lens](../research/2026-10-27/um-ghidra-lens.md) §1.7 (DSR→ER note), §3A;
[audit-systems](../research/2026-10-27/audit-systems.md) (combat, poise, ranged, hit zones, AI); imported
`docs/design/world/76-stats-progression.md` §102, §118, §121, §128; `docs/design/research/dark-souls-poise-mechanics.md`;
old decisions 0031–0037, 0040, 0089–0091, 0142.

**Design constants that do not move** (76 §102): stats never scale i-frames, parry windows or wind-ups; no to-hit
dice: a swing that visibly connects lands; timing is fixed on the animation side, never by retuning numbers, and
"the animation side" means runtime speed/window control or the install-time patcher of decision 0014 §2, never a
shipped edited clip. **Burden tiers** are Argonia's (fast < 0.2, mid < 0.35, fat < 1 of capacity); DSR supplies
the i-frames and recovery per tier, not its own 25%/50% thresholds (decision 0004).

## Work packages

### WP5.1 Measure DSR into the golden table
- Extend G6 to the full list: per player action (light, heavy, running, rolling, jumping and plunging attacks
  for each weapon class we have: dagger, straight sword, curved sword, greatsword, axe, hammer, spear, fist,
  bow, crossbow), startup / active / recovery frames, cancel windows (JumpTable flags), stamina cost, poise damage
  (`dmgLevel`, AtkParam poise fields), guard values (GuardRate, GuardStaminaCutRate, GuardBreakRate); rolls
  (fast/mid/fat i-frames and recovery; the 25%/50% equip-load thresholds, mapped to Argonia's burden tiers
  fast/mid/fat); backstep; parry windows by shield class and parry-broken state (SpEffect 30) duration; riposte
  and backstab damage multipliers; poise pools per armour class (EquipParamProtector), the refill rule (DS1:
  full refill after a time unhit; measure it); stamina regen rate and delay; NPC poise (`superArmorDurability`)
  for the enemy archetypes; throw/grab rows only if a boss uses them.
- AI shape: decompile the Hollow, Balder Knight and Black Knight AI Lua with soulstruct (local names intact) and
  write our own goal-tree summaries (approach distances, combo odds, punish rules, retreat rules) as knowledge;
  never transcribe the Lua.
- Every row has provenance (`DSR:` file, animation id, event; `OWNER:`; `GUESS:`); 13/11/9 settled.
- Live capture for rows the files cannot answer: DSR offline on the GPU box under Proton, debug menu mod
  (Nexus DSR 266) or DSR Gadget for stable cameras, 20 repeats at 60 fps.
- **Acceptance:** golden table complete for the list; `GUESS:` rows ≤ 5% and each named.

### WP5.2 Configure the stack
- BFCO (attack framework; MCO excluded), Precision (hit detection, with its Pandora patch), TDM (lock-on,
  target switching, projectile aim), TK Dodge RE/Redux (roll input and animations; its own i-frames set to 0),
  OAR (animation choice by our conditions), Elden Parry (kept only if its projectile deflect is wanted; its
  window replaced by ours), TrueHUD (boss bars; poise meter hidden), SCAR (combo AI), CPR (spacing,
  strafing), Ultimate NPC Dodging, Wait Your Turn (attack tokens), AMR/AMF (root motion), XP32 True Ragdoll.
- Movesets: permitted Skyrim-modder movesets or vanilla attacks, brought to the golden table's timings by the G9
  method (runtime speed and window control; the install-time patcher only where runtime control cannot reach a
  window); **no** packs ripped from FromSoftware games (decision 0004); each in the dependency manifest with its
  permission.
- **Acceptance:** smoke combat scenario on the pinned runtime with no crash; every framework's API version
  recorded.

### WP5.3 ArgoniaCombat: the timing and poise core
In `skse/core/combat` (pure C++, L2-tested) plus `skse/ArgoniaCombat` (adapters), all numbers from
`data/combat/golden-table.json` + Argonia's sheet:
- **Hit pipeline** on Precision's pre-hit callback: ignore hits in the target's i-frame window; parry window
  check; hit zone from the hit rigid body (head ×2 via `GetOriginalFromClone` → bone; any hurtbox lands); push
  stagger 0 so vanilla stagger is suppressed; post-hit callback timestamps hits for the poise refill.
- **Damage:** listed damage × (0.40 + 0.60 × k(score)) × (Str + 50)/100 × crit × hit zone (76 §121.1; Strength
  does not scale bows), armour mitigation from WP4.1, arrowheads at 60% armour effect.
- **Dodge:** roll animation chosen by an OAR custom condition `ArgoniaBurdenTier` (fast/mid/fat); i-frame
  timer starts on the dodge-start event with the measured window per tier (in game seconds, never frame counts).
- **Parry, riposte, backstab:** parry window opened from the bash/parry start event per shield class; a hit inside
  it is cancelled and the attacker enters the parried state for the measured duration; riposte input in that
  state plays a paired animation with the class multiplier (dagger highest; never stacks with the sneak table);
  backstab by facing angle (|Δyaw| < measured θ, ~60° prior), distance, target not attacking.
- **Poise:** forked from Chocolate Poise (MIT) or written fresh (~300 lines): hidden pool = Agility/2 + armour
  pieces' poise (heavy > medium > light, skill sets the position in the range) + effects; each hit subtracts the
  weapon class × attack type poise damage; pool ≤ 0 → stagger and full reset; full refill after the measured
  time unhit (~5 s in the old design); hyper-armour flags from attack annotations; bosses may be unstaggerable;
  spell casts interrupted on poise break.
- **Stamina:** one bar; per-action costs and regen from the table; regen blocked during actions (graph variable
  check); exhaustion behaviour per DSR.
- **Guard:** stability, chip damage and guard break from the table.
- **Lock-on:** TDM; enforce 20 m (~1,400 units) by its setting or by `RequestDisableTargetLock` past range;
  nearest pick, stick flick retargets.
- The parity table records that the old weapon-family parries (old 0040: one-hand 0.20 s, two-hand 0.16 s, shield
  0.26 s) and the old 0.1–0.29 s constant are replaced by DS1's measured shield and parry-weapon windows.
- **Acceptance:** L2 tests for every rule; parity table `data/combat/parity.md` lists every feature, DSR value,
  our value, substitution and check.

### WP5.4 The ±1-frame test dummy
- Bridge command spawns a test dummy whose scripted attack contacts at t0 + k/60 s relative to the player's
  roll or parry start; logs pre-hit accept/ignore with timestamps from one clock; runs at capped 30 and 60 fps.
- Also logs Precision contact time against annotation time to catch tunnelling on fast swings.
- **Acceptance (L4):** every measured window edge (roll per tier, parry per shield class, attack active frames,
  parried-state duration) within one DS1 frame (33 ms) of the table, aiming for 16 ms, at both frame caps.

### WP5.5 Enemy AI and archetypes
- The old project's 12 humanoid archetypes and 27–30 creature clip sets (old `ai/enemyAi.ts`,
  `hostileReaction.ts`, `search.ts`, `speciesHunt.ts`, `casterSeam.ts`) mapped onto combat styles, SCAR data
  (combo choice by distance and angle), CPR data (advance, back off, circle, fall back), UND (NPC dodges) and
  Wait Your Turn (attack tokens); DSR AI-shape summaries guide approach distances and punish rules ("punish"
  reads our state via graph variables: target recovering, whiffed, healing).
- Calm / draw / come / fight / return / flee from each record's fight-flee-alarm; packs with leaders; archers;
  casters; per-observer detection from P4.
- **Acceptance:** the old project's duel tests reborn as L4 scenarios (a sample of the 1,085 duels): win-rate and
  time-to-kill bands by danger band within the old balance harness's predicted ranges.

### WP5.6 Bosses
- Authored bosses with phases in ArgoniaCombat (HP thresholds swap combat style or moveset via OAR conditions),
  TrueHUD boss bars restyled, arenas: the old prototype Xal-Krona, the swamp leviathan, the Wamasu guardian of
  the main quest, boss variants at health ×5 (old 0042 §5).
- **Acceptance:** each boss has an L4 scenario (phase transitions fire) and an owner feel packet.

### WP5.7 Ranged and hand-to-hand
- Bows and crossbows: Skyrim archery with TDM projectile aim; shoulder-aim camera (+0.55 right, +0.22 up, 1.7
  back; old TotK reference); recoverable arrows (Skyrim native chance, tuned), fire and effect arrows, coatings;
  Strength does not scale bow damage; the old arrow calibration (old 0090) checked against the band ladder.
- Hand-to-hand drains stamina; the knock-out finisher (deferred in the old design) built if cheap.
- Arrow surface response (stick, ricochet, break) from the old `physical-materials.json` mapped onto Skyrim
  projectile impact data where possible; anything Skyrim cannot express is recorded as a substitution.
- **Acceptance:** L4 scenarios; the old bow regression cases where they translate.

### WP5.8 Ragdolls and hit feel
- XP32 True Ragdoll for deaths; Precision hit impulses; hit-stop and recoil from Precision settings tuned to DSR
  footage, not invented.
- **Acceptance:** reader panel on clips (L5, reason: feel) and the owner packet.

### WP5.9 Owner feel packets
Two packets: (1) player combat vs three archetypes and one boss; (2) the full roster by danger band. Each with
a list of things to feel (roll timing per burden tier, parry, riposte, poise breaks, stamina rhythm) and how to
reply. Feel fixes go to the animation side (runtime speed and window control, moveset choice; decision 0014 §2), never to the golden table's measured
numbers unless the owner rules a deliberate deviation (recorded as `OWNER:`).

## Exit gate
Golden table complete; ±1-frame suite green at 30 and 60 fps; archetype and boss scenarios green; owner feel
packets with no open blocker.

## Risks and fallbacks
- **Animation feel** is the weak link (Skyrim clips vs DS1 timing): survey permitted movesets early; re-time
  vanilla with annotations; never import FromSoft animations.
- **Framework conflicts** (BFCO vs others): the manifest's conflict list; test after each addition.
- **Precision tunnelling** on fast swings: lower its collision step or widen capsules for those weapons.

## Deliberately out of scope
Weapon arts and DS3-only mechanics (hyper-armour beyond what DS1 has) unless the owner asks; active ragdoll (VR-only
PLANCK); multiplayer/invasions; FromSoftware animations or data in any form.

# Combat wiring: how the sheet reaches the combat stack (1.6 draft of 2.7 §a)

Lane 1.6-wiring, 2026-10-30. The owner reviews this draft in 1.7. The routes are data: `combat_wiring` (one row per
id below), `combat_mod_setting`, `game_setting` + `game_setting_combat`, `combat_carrier`, `danger_band_combat`,
`weapon_class_combat`, `combat_constant` and `combat_archetype` (world/schema.sql, the 1.6-wiring section). Records:
`tools/argonia_world/combat_records.py`. Settings are applied at stage by `infra/gpu-box/stack.py` (`combat_settings`).

**Fixed rules.** Decisions 0004, 0014 and 0019 apply. DS1 supplies feel (windows, frames, costs, regen, poise
behaviour), and the sheet supplies progression. A number 2.7 §b measures from DSR is a placeholder here, tagged
`GUESS:` (DSR owed) or `MOD:` (the mod's value, kept), and is never retuned for feel. Stats never touch i-frames,
windows or wind-ups.

## Why the db, not data/combat/ or the manifest

Decision 0030 makes the relational db the one home of every fact, and every data step "a set of tables, never a new
file format". A tuned setting is a fact with a provenance and a wiring row, both foreign keys, so it is a row.
`data/dependencies.json` keeps what is install configuration: bindings (TDM `uTargetLockKey`, OCPA, TK Dodge's
sprint key) and archive facts. Elden Parry's parry window moved out of the manifest into the db, and an L1 test
refuses a key that has both homes. stack.py reads the db through db.py, and a changed setting re-stages only its
own row.

## The mechanism (P1 carriers)

ArgoniaCore computes each player quantity in `skse/core` (`carriers::compute`, `derive`). It writes `factor − 1`
into a reserved actor value, and the perk `ARG_Perk_Carriers` applies it with *Multiply 1 + Actor Value Mult*. An
unwritten carrier is 0, so the entry is neutral and never zeroes damage. NPCs carry no live carriers: their
numbers are compiled into a per-archetype perk and record (P5).

| Carrier | AV (av-audit reserve order) | Entry point | Value ArgoniaCore writes | Wired |
|---|---|---|---|---|
| right.attack-damage | VoicePoints | ModAttackDamage | P × S − 1 (bow: P − 1) | yes |
| right.power-stamina | VoiceRate | ModPowerAttackStamina | stamina_mult − 1 | yes |
| body.incoming-damage | Energy | ModIncomingDamage | −mitigation(AR, 24) | yes |
| body.block | OneHandedSkillAdvance | ModPercentBlocked | block_stability − 1 | yes |
| left.attack-damage | TwoHandedSkillAdvance | ModAttackDamage | reserved | no |
| body.incoming-stagger | MarksmanSkillAdvance | ModIncomingStagger | reserved | no |

Mutagen 0.54.4 has no names for the limb AVs 46–52, so the skill-advance AVs follow Energy (av-audit's order).

**Owed by the ArgoniaCore lane** (skse is not in this lane's paths):
- write the four wired carriers on every sheet, equip and burden change;
- add `ARG_Perk_Carriers` to the player (like `EnsurePerk`);
- pin the vanilla OneHanded, TwoHanded and Archery base AVs at 0, which neutralises Skyrim's own skill term
  (UESP's displayed-damage `1 + skill/200`).

## The rows (group A, the 0.0 stack)

Formulas are 76's, as `skse/core` implements them:

- P = 0.40 + 0.60 × k(score), with score = (skill + Agi/5)/1.2 and k(s) = 1 − (1 − s/100)^1.6;
- S = (Str + 50)/100;
- mitigation = AR/(AR + 135.6 + 0.6 × blow).

The route column of `combat_wiring` says how each row is reached; the writer column says who writes it.

| Id | Quantity | Carrier | Formula | Writer | Number source | L4 |
|---|---|---|---|---|---|---|
| w.damage.listed | listed damage | WEAP DATA damage | motion × set damage_scale × 24; steel sword 24 | generated | motion `GUESS:` (DSR) | fight-damage-builds |
| w.damage.position-strength | blow quality × Strength | right.attack-damage | P × S | ArgoniaCore | sheet | fight-damage-builds |
| w.damage.vanilla-skill | Skyrim's skill term | OneHanded/TwoHanded/Archery base AV = 0 | ×1 | ArgoniaCore | sheet | fight-damage-builds |
| w.damage.difficulty | difficulty damage | GMST fDiffMultHP{By,To}PC{VE,E,N,H,VH,L} = 1 | lethality knob 1.0 (76 §121.4) | generated | `OWNER:` | fight-damage-builds |
| w.damage.left-hand | left weapon blow | none (no hand condition exists) | P × S of the left skill | owed | sheet | — |
| w.damage.critical | riposte, backstab | Rim Parry Payload config | class multiplier (76 §121.1) | mod | `MOD:`, DSR owed | fight-archetype |
| w.stamina.max | max stamina | Stamina base AV (G14.1) | 60 + 0.8 End (+4 above 50) | ArgoniaCore | sheet | fight-damage-builds |
| w.stamina.regen | regen in combat | GMST fCombatStaminaRegenRateMult = 1 | one rate 12 + 0.24 Agi by StaminaRate | generated | `SHEET:`, DSR owed | fight-roll-burden |
| w.stamina.regen-delay | regen delay | GMST fDamagedStaminaRegenDelay = 1.05 | 76 §121.2 | generated | `GUESS:` (DSR) | fight-roll-burden |
| w.stamina.power | power attack cost | right.power-stamina | skill band × burden tier × (1 + 0.07 d) | ArgoniaCore | sheet | fight-damage-builds |
| w.stamina.actions | light attack, block, stagger costs | OAR-added Stamina Cost JSON constants | none: flat ModActorValue | mod | `MOD:`; **thin row for 2.7** | — |
| w.stamina.roll | roll cost | tk-dodge.toml fDodgeCost = 15 | DS1 cost × ratio of maxima (2.7) | data | `GUESS:` | fight-roll-burden |
| w.guard.stability | share blocked | body.block | min(Block band, 0.95) + effects | ArgoniaCore | sheet | fight-archetype |
| w.guard.stamina | guard stamina | none per actor (fStaminaBlock* are global) | Block guardStamina band | owed | **thin hook, 2.7** | — |
| w.parry.window | parry window | EldenParry.ini 0.02–0.2 s | none (never stat-scaled) | data | `MOD:`, DSR owed | fight-archetype |
| w.roll.tier | no roll when overloaded | TK Dodge Addon `bUsePerkLock` + its required perk, toggled by burden tier | r ≥ 1 → no roll | ArgoniaCore | sheet; **thin row** | fight-roll-burden |
| w.roll.distance | distance and recovery by tier | animation speed (0014 §2) | tier ×1.10/1.00/0.80 | owed | DSR | fight-roll-burden |
| w.iframes.duration | i-frame window | tk-dodge.toml fIFrameDuration = 0.3 | none | data | `GUESS:` (13/11/9 question) | fight-roll-burden |
| w.iframes.tier | i-frames by tier | graph variable TKDR_IframeDuration × tier scale | tier ×1.15/1.00/0.80 | owed | DSR; **thin hook** | fight-roll-burden |
| w.poise.stagger | poise and stagger | Modern Stagger Lock (A); body.incoming-stagger reserved | Agi/2 + pieces (76 §121.3) | owed | DSR | — |
| w.armour.mitigation | the player's mitigation | body.incoming-damage | at the reference blow 24 | ArgoniaCore | sheet | fight-damage-builds |
| w.armour.vanilla | Skyrim armour rating | ARMO rating 0 on our items | none | generated | sheet | fight-damage-builds |
| w.power.heavy | heavy over light | race attack data or ModPowerAttackDamage | motion_heavy / motion_light (2.4 `GUESS:`) | owed | DSR | — |
| w.archery.damage | bow damage | right.attack-damage (no Strength) | P | ArgoniaCore | sheet | (2.7 §i) |
| w.archery.draw | draw time and stamina | fBowDrawTime; drawStamina band | none yet | mod | DSR | — |
| w.lockon.distance | lock range | TDM fTargetLockDistance = 2000 u | none | data | `GUESS:` (LockCamParam) | fight-lock-on |
| w.enemy.health | archetype health | NPC_ HealthOffset | lerp(band, position) − race start 50 | generated | sheet (76 §128) | fight-archetype |
| w.enemy.damage | archetype light hit | its perk, ModAttackDamage × const | light hit / listed | generated | sheet | fight-archetype |
| w.enemy.armour | archetype armour | its perk, ModIncomingDamage × const | 1 − mitigation(AR band, 24) | generated | sheet | fight-archetype |
| w.enemy.level | fixed danger | NPC_ level, ECZN min = max | band level | generated | sheet | fight-archetype |

## Losses and errors to record

- **Mitigation at one blow size.** Skyrim's armour cannot express a blow-dependent curve, so Part 1 applies
  mitigation at the reference blow of 24. The error against the true curve:

  | AR | blow 14 | blow 40 | blow 92 |
  |---|---|---|---|
  | 25 | +0.5 pp | −0.8 pp | −2.7 pp |
  | 50 | +0.8 pp | −1.1 pp | −4.2 pp |
  | 100 | +1.0 pp | −1.5 pp | −5.6 pp |

  It is fully fixed when 2.7 moves this row into the `HandleHealthDamage` hook (native map G30.2).
- **No hand condition.** Skyrim has no condition that names the attacking hand, so a left-hand weapon blow uses
  the right-hand carrier. Under DS1's layout the left hand holds the shield, so 1.6 does not meet this case.
- **Flat OAR stamina.** OAR's stamina costs are constants, so the sheet's stamina multiplier reaches only power
  attacks.
- **One roll for every tier.** TK Dodge has one roll and one i-frame value. Tiers need the perk lock (roll or no
  roll) plus a graph-variable write. Group B or B2 (Dark Souls Combat) has three bands, keyed to max stamina, not to
  burden.

## Group B and B2 differences

- **B (Dark Souls Combat) owns the poise pool and stagger** (armour weight), rolls (bands at stamina/8 and /4,
  Papyrus i-frames) and bash parry. The `w.roll.*`, `w.iframes.*`, `w.parry.window` and `w.stamina.roll` settings
  do not apply. DSC's `BB_Poise_Var*` globals are set at scene step 0, never in the MCM.
- **B2** keeps A's rows for rolls, parry and riposte. It takes DSC's poise and stamina layer, and sets
  `BB_Poise_VarCritsAllowed` = 0 and DSC's roll key to an unused key. DSC's attack stamina and OAR's overlap, so
  one is picked per the trial.
- **The damage, armour and enemy rows are the same in every group.**

## The five reference builds (L2)

These are computed from the core's formulas; `core.carriers` and `core.sheet` are the L2 tests of record. The
builds are skse/core/tests/builds.h, with the steel sword at 24 listed.

| Build | P | S | carrier | blow | max stamina | burden | power stamina × |
|---|---|---|---|---|---|---|---|
| marsh-hand (Str 50, LB 60, Agi 50) | 0.852 | 1.00 | −0.148 | 20.5 | 100 | mid (0.25) | 0.984 |
| novice (40, 5, 40) | 0.501 | 0.90 | −0.549 | 10.8 | 92 | fast (0.07) | 1.175 |
| mage (30, 5, 40) | 0.501 | 0.80 | −0.600 | 9.6 | 88 | fast (0.17) | 1.175 |
| hauler (70, 5, 35) | 0.493 | 1.20 | −0.408 | 14.2 | 140 | overloaded (1.25) | 1.593 |
| god (100, 100, 100) | 1.000 | 1.50 | +0.500 | 36.0 | 300 | fast (0.00) | 0.800 |

The archetype is D2 at 0.5: health 44.5 (offset −6 from the race's 50), light hit 32 (24 × 1.333), AR 31.5 (it
takes 0.826 of a blow).
- The marsh-hand kills it in 3 blows (16.9 each).
- Unarmoured, it kills the marsh-hand in 4 blows (76 §128's D2 target is 4).

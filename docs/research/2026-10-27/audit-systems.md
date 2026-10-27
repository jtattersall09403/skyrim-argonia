# Gameplay systems audit (Elder Souls: Argonia) -- for an OpenMW rebuild decision

Root: /home/claude/elder-souls-argonia. Paths below are relative to it. Built status = three.js repo, per docs/PROGRESS.md (Part 2 rows 2.1-2.12, 2.15 "done"; 2.13 persistence and 2.14 sound "todo"; apps/game is only the slice shell).

## Reconciliation block
- Live docs: docs/world/76-stats-progression.md (the spec, 1640 lines), docs/world/75-combat-compatibility.md, docs/phases/2-slice/*.md (briefs plus Outcome sections), docs/research/combat-and-systems/slice-systems-checklist.md, systems-inventory-2026-10-14.md (STALE: says no magic runtime, no climb, no save, no boat controller; the code now has packages/magic, packages/crafting, packages/save, game-core/src/boats, character/src/combat/climbRuntime.ts).
- Single doc to edit if anything is written: docs/phases/2-slice/README.md (chunk table) or the 2.13 brief; do not add files.
- Owner's overall framing (0149, docs/decisions/0149-...md): "mostly morrowind and skyrim shaped with dark souls combat".

## Reference games, by system (owner's own citations)
Combat: DS1 (poise, i-frames 13/11/9 by equip tier, parry/riposte, lock-on), explicitly NOT DS3 hyperarmour (docs/research/combat-and-systems/dark-souls-poise-mechanics.md). Skyrim for animations, weapon classes, sneak multipliers, dual-cast, hand slots, detection. Morrowind for every formula (score = skill + attr/5, no Luck), UI window layout, journal, dialogue, barter, spellmaking, enchanting, alchemy, birthsigns, 27 skills minus Luck. BotW for climbing + stamina gating. Tears of the Kingdom for shoulder bow aim and camera pull-in. Wind Waker for sailing. Skyrim horses for boat ownership. Dark Souls HUD for bars.

## Systems

### Combat: melee, guard, parry, i-frames, lock-on, stamina
(a) DS1-shaped real-time: roll with i-frames (varies by equip-load tier, DS1 13/11/9 frames), guard with stability/chip/guard-break, parry window 0.1-0.29 s after raise (parryActiveStart/End, packages/game-core/src/combat/weapon.ts:218-231), riposte/backstab paired criticals, one resolveHit path for melee and arrows (packages/game-core/src/combat/README.md). Stamina one bar: max = 60+0.8*End to End 50 then +4/pt; regen 12+0.24*Agi/s after 1.05 s delay (76 §121.2). Dual wield, two-hand toggle, shield bash. Lock-on range 20 m (anim/lockOn.ts), nearest-pick, stick flick retargets. Damage = listed x P(score) x (Str+50)/100 x crit x hitZone; no dice, a swing that visibly connects lands (76 §102, §121.1). Never stat-scale i-frames, parry windows, windups (76 §102).
(b) Built and working: resolveHit, blockReaction, backstab, dodge, 22 combat tests, sandbox visual:check groups pass (2.7 Outcome). Lock-on "thin".
(c) OpenMW: the HARD part. Vanilla OpenMW melee is a stat-roll hit/chargeup system with a fixed attack animation and no hit-sphere sensors, no i-frames, no guard stance, no stagger-by-poise, no lock-on. Needs engine fork (or very heavy 0.49+ Lua plus new animation groups): per-frame weapon sensors vs hurtboxes, active-block/parry state machine, roll/dodge with i-frames, lock-on camera. Lua can run poise/stamina numbers and cancel/replace animations via animation API, but cannot easily give real-time collision hit detection on limbs. Needs new animations (rolls, parries, paired kills, guard). Skyrim clips are the source assets (retarget to Morrowind skeleton or ship OpenMW's Skyrim-skeleton mods).

### Poise / stagger
(a) DS1 model (decision 0037): hidden pool, maxPoise = Agility/2 + sum armour-piece range (heavy>medium>light, skill sets position in range) + effects; attacker poise damage by weapon class x attack type; empties = stagger; refills instantly after ~5 s unhit; bosses `staggerable:false`. Shared by player and enemies (76 §121.3; apps/combat-sandbox/docs/architecture/poise-and-stagger.md). Numbers provisional, tuned by feel.
(b) Built: packages/game-core/src/combat/poise.ts, poise-break scenario, HUD poise bar; calibration at "10c" noted open.
(c) Doable in OpenMW Lua IF hits are visible to Lua (onHit-style events exist in 0.49 for actors; damage values yes, attack-type partial). Stagger animation play is doable; the pool logic is pure arithmetic.

### Ranged: bows, arrows
(a) Physical ballistics (draw force, arrow mass), arrow is a rigid body, recoverable arrows, surface response table (stick/ricochet/break), shoulder-aim camera (TotK), first-person rig, aim spread seeded. No Str on bow damage. Arrowheads 60% armour effect. Effect/fire arrows, coatings (76 §121.1; combat/bowShot.ts, arrowFlight.ts; apps/combat-sandbox/docs/architecture/ranged-combat.md; 75 §55).
(b) Built and working (bowAimRegression tests, 2.9c fire arrows).
(c) OpenMW has projectile objects with gravity but not custom ballistics/stick-and-recover; Lua has limited projectile control (0.49 adds some). Probably fork or Lua-spawned items per arrow. Shoulder aim camera = Lua camera API (doable). Bow animations new.

### Hit zones, riposte/backstab, hand-to-hand
(a) Head x2, any hurtbox including limbs lands; riposte/backstab per weapon-class multiplier (dagger highest), never stacks with sneak table. Hand-to-hand drains stamina, KO finisher (76 §118, §121.1, §121.5).
(b) Hit zones built; backstab built; h2h finisher deferred to 4.5.
(c) Needs fork for per-bone hurtboxes (OpenMW has bounding boxes/ray cast on actor; Lua raycast gives hit coords but no bone/zone); paired kill animations new.

### Enemy AI, creatures, bosses, encounters
(a) Utility-ish brain: calm/draw/come/fight/return/flee driven by per-record `fightFleeAlarm`; per-observer detection; search and give up; packs with leader; casters via caster seam; archers; 12 humanoid archetypes + 27-30 creature clip sets (ai/enemyAi.ts, hostileReaction.ts, search.ts, speciesHunt.ts, casterSeam.ts). Hostile places attack on sight; violence answered by victim's kin; roaming bands from per-region table (decision 0142). Bosses authored, not tuned; one prototype Xal-Krona; swamp leviathan; boss variant health x5 (76 §128; 0042 §5). Fixed D1-D5 ladder: D1 health 18-28, D5 96-205; blows that kill you 6/4/3.5/3/3 (76 §128 table); enemies resolved to absolute numbers by a semantic compiler (band + position + variants).
(b) Built: 217 hostile records with loadouts, 1085 duels passed, roaming bands met 0.83-1.06/km (2.7 Outcome). Boss AI depth, group tactics: P2/later. NavService baked per place (humanoid/large/swim classes).
(c) OpenMW has native AI packages (combat/flee/wander/travel) and navmesh, Lua can drive via control inputs and AI packages. Real-time Souls-style enemy move/attack selection with telegraphed windups is doable in Lua per-frame but fights vanilla combat AI; new creature/NPC attack animations needed. Roaming bands/respawn-on-rest: Lua spawn via world.createObject, doable. Fixed difficulty (no leveled lists) is natively Morrowind-friendly (Morrowind has fixed placed enemies plus leveled creatures; just avoid them).

### Stats and progression (76 full)
(a) 7 attributes (Morrowind minus Luck), 27 skills (Armorer->Smithing), race, one of 13 birthsigns (chosen), class 5 major/5 minor/specialization/2 favoured, 18 presets. Score = (skill+attr/5)/1.2, k(s)=1-(1-s/100)^1.6, band(lo,hi). maxHealth=(Str+End)/2+level*End/10 (retroactive); stamina above; magicka=20+3*Int. Skills grow by use ("in anger", worthiness anti-grind). Currency "vastei" (not XP) earned from qualifying uses; 10 major/minor ranks (curve 1,2,..8 ceiling 8, decision 0147) = one pending level; level banked only on REST; attribute purchases at the sitting: cost = 40(1+lvl/10)^1.3 (1+attr/50)^2 (1+0.5(n-1)), max 5 pts per attr per sitting; no practice discount. Level 2 in 15-30 min; level 10 ~4-6 h; no hard ceiling. Armour mitigation = AR/(AR+135.6+0.6 dmg); armour material ladder steel 1.0 to daedric 4.4; light/medium/heavy x0.75/0.9/1.0. No wield requirements, soft requirements (stamina x(1+0.07d)). Condition 0-100, weapon unusable at 0, full damage above. Burden tiers by r=carried/(30+3Str): fast<0.2 / mid<0.35 / fat<1 / overloaded; capacity 30+3*Str kg. One StatEffect stack (field, op, magnitude, source) for races, signs, disease, potions, spells, enchants. Difficulty knob enemyDamageMultiplier (0.7/1.0/1.35). Death/rest in §126.
(b) Built: whole 2.8 (stats/compile.ts, store.ts, effects.ts, balance.test.ts, ladder-table.md, save family progression). Stats-lab app. Birthsign null until character creation (3.3, not built). Character creation lives only in the sandbox CharacterPicker.
(c) OpenMW: attributes/skills/classes/birthsigns/races are native, and the engine is the reference implementation of Morrowind's formulas. Lua (0.49 types.NPC/Skill/Attribute interfaces, skill-use handlers `I.SkillProgression`) can: remove Luck from use (ignore), replace skill XP with a vastei currency, gate levelling to rest, rebuild the level-up UI (Lua UI), rewrite health recompute (Actor stat modifications), burden tiers via Lua reading encumbrance. Replacing the dice hit formula requires combat rewrite (see Combat). The effect stack maps to OpenMW magic effects + Lua. Class/birthsign data = esp content. Mostly doable in Lua.

### Magic
(a) Casting never fails; castable iff 2*school + Wil/5 >= cost (working spell ~60% of limit, 50-point reliable line); magnitude scales 0.75-1.25 with skill; spell dmg bypasses physical armour; Wil/4 % innate resist; spell-cost reduction capped 75%; 6 schools incl. Mysticism; spellmaking up to 8 effects fee 7x cost; enchanting points=(Enchant+Int/5)/3, constant effects tiered by soul size, disenchant-to-learn; spell in a hand like a weapon (hold-charge, release), dual-cast x2.2 magnitude x2.8 cost, stream spells; interrupted by poise break; powers once a day; Atronach sign; levitate speed copied from OpenMW; folk sellers, no guilds (76 §123; decisions 0146, 0148).
(b) Built whole: packages/magic (300 effects, 876 spells), castCycle.ts, FamilySystem VFX, 39 CAST_* clips; save family magic.
(c) Native in OpenMW: spell/effect/enchant/soul gem/spellmaking systems and magic effects list (Morrowind names). Doable in Lua: casting never fails (OpenMW setting/ Lua cast handler, `I.MagicEffects`/ `Actor.spells`), hand-held spell with charge (Lua input + spell cast via `core.magic`/ `Actor.activeSpells`; real-time hold-charge needs animation hooks), dual-cast, dual hands, magnitude scaling by skill. Needs fork: nothing hard; magicka formula via Lua modifiers. New spell VFX: OpenMW supports particle/nif effects (reuse). Easiest system to port.

### Stealth, crime, locks, traps
(a) Per-observer detection (light, gait noise, armour weight, view cone, LOS, scent/hearing, Sneak+Agi vs spot); 4 eye states (hidden/caution/danger/detected); search then give up; alarm radius; sneak blow = band multiplier (dagger x3..x15, bow x2..x8), never auto-kill; crime exists only when seen; "Owing" debt ledger per region in nushmeekos (pay gold, serve custody that advances clock and costs pending skill progress, or resist); trespass zones with hours; pickpocket is the one seeded gamble; locks threshold (Security+Agi/5)*tool>=lock; traps (kinds as data); water stealth (submerged breaks sight) (76 §121.5, §124; decision 0151; 2.10).
(b) Built whole: 183 locks, 7 traps, 19 keys, 28 zones, Owing ledger, guard stop, pickpocket (2.10 Outcome); five journeys green headless.
(c) OpenMW has native sneak, detection (hit/ spot formulas), crime/bounty, lockpick/probe, traps, pickpocket (all dice-based). Lua can override: per-observer detection is doable with raycasts and light queries (AI sneak awareness is engine-internal; fork or Lua replacement of "spot" via AI package control); bounty->Owing: Lua can read `types.Player.getCrimeLevel`/ crime events (0.49 has crime hooks) and replace consequences; locks as threshold: Lua on lockpick activation handler. Moderate.

### Crafting: alchemy, smithing, enchanting
(a) Alchemy canon formula, always succeeds; effects visible at skill 15/30/45/60; weapon poisons and oils coat next hit; potions are the healing economy (no estus); smithing = repair+temper (3 grades, +8% each at 25/55/80)+forge (tier 1+floor(skill/14)); 7 stations, 154 recipes, 8 material tiers; resource nodes; fortify-crafting loop allowed but scarce (decision 0144, 0150) (76 §124; 2.9b).
(b) Built whole (packages/crafting).
(c) Alchemy/enchant native; smithing is a Skyrim feature: Lua + custom UI + items records (doable). Poison coating: Lua on-hit, doable. Forge stations: activators + Lua menus. Doable.

### Economy, trade, services, training
(a) No haggle: buy = base*clamp(1.35 - advantage/200, 0.8, 1.35), sell clamp(0.55+adv/200, 0.55, 0.95) where advantage uses Morrowind's pcTerm and merchant mirror; purses finite by trade class (general 750, smith 1000...) x place tier (city 1, town .75, village .5), refill 48 h; rich merchants 9375; training 10 x skill gold per rank, cannot exceed governing attribute (base), skill books +1 rank (5 per skill); spells 2 gold/magicka; services repair, enchant, spellmake, recharge, cure, guides, ferries, tolls (76 §124; decision 0141 "one price contract: coin, goods or a favour"; 2.6).
(b) Built: packages/economy, services, restock, barter screen; trade 5, beds 3, ferry 3, repair 1, train 3 in the slice.
(c) Native Morrowind: barter, merchant gold, training, services. Haggle removal and price formula: Lua override of barter (limited: barter UI in OpenMW is C++; services formula in engine; needs mod/fork to remove haggle) -- minor. Finite purse + restock native (Morrowind has it).

### Factions and reputation
(a) FactionStanding {membership, rank, reputation -100..100, competencyFlags, sponsors}; ranks are ceilings of reputation (associate 0, member 10, senior 40); crime against a member lowers reputation with all; disposition from faction half of reputation; allegiance rites = corprus-style permanent packages (decision 0028); 111 faction records (32 real); no followers (76 §125; quests/40-factions.md).
(b) Built: game-core/src/factions/standing.ts, narrative/src/standing; runtime partial (checklist rated "later").
(c) Native: Morrowind factions with ranks, reaction matrix, expulsion. Reputation scale differs; Lua/ESP data. Doable.

### Dialogue, quests, journal
(a) Morrowind topic web with hyperlinked words, disposition/persuade/bribe; persuasion threshold, no dice; authored thresholds with evidence flags; quests as data over one world record; journal is a Black Marsh book with ribbons, filter, directions until discovered then Show-on-map (decision 0137, 0153; 2.11; 2.2 §c). Dialogue content is huge (89 people full lines, Opus-written).
(b) Built: packages/dialogue, packages/narrative (runtime), journal book screen in packages/ui.
(c) Native: Morrowind dialogue/journal engine (topics, conditions, journal indices). Authoring data is mostly portable to ESP INFO records via a converter. Persuasion UI replacement: Lua UI. Doable/native.

### Climbing (decision 0152)
(a) BotW climbing as a province-wide rule from geometry only: slope bands (walk < ~57 deg, scramble to climb), solid-mesh size, surface classes with wet grip; free climb in any direction with corners, hang, shimmy, leap catches, drop, mantle tiers, slip when wet, fall at zero stamina; ladders; no wall running. Stamina is the sole limiter: speed 1.1 m/s x band(0.85-1.25), drain 7.5/s x band, mantle 18, burden mult; walls <10 m free to all, 25 m real climber, >40 m specialist (76 §122.1; 2.12; docs/research/combat-and-systems/botw-climbing-system.md). Clips from FreeClimb mod (Nexus 193552), EVG Animated Traversal, SkyParkour.
(b) Built (character/src/combat/climbRuntime.ts, ladderRuntime.ts), province survey, touch controls.
(c) NOT in Morrowind/OpenMW. Needs engine fork (collision-mesh-following kinematic character mode, hand/foot IK) or a Lua hack (position-set each frame via `Actor` teleport with raycasts: feasible but janky; physics body controlled by Lua is limited). New animations (Skyrim-sourced, retarget). High risk.

### Swimming and diving
(a) Closed as built. Stroke 2.8 m/s, shoulder-depth entry 1.4 m, sprint-swim x1.4 drains stamina; pitch-driven dive/rise; breath = 25+0.35 Athletics+0.25 End s (Argonians unlimited; 30 s free to all, 60 s specialist); drowning damage; underwater camera; water as stealth medium; no mandatory-Argonian routes (76 §122; 0152 §4; 2.12).
(b) Built, played by owner.
(c) OpenMW swims natively (surface swim, dive, breath, water breathing effect, levitate, water walking). Argonian water breathing is a race ability. Variable breath, stamina swim sprint = Lua tweaks (OpenMW 0.49 exposes some). Mostly native.

### Boats (0158, 0159, 2.15)
(a) Boats as Skyrim's horse: bought/taken/found, owned, tied at moorings, recovered after rest to the last tied mooring or fetched for 10% price (min 5 gold). Sailing as Wind Waker: cruise speed to steered direction, faster with the wind astern, the player can turn the wind with a quick power/item/spell, HUD wind mark. Two classes in slice (dugout, sea hull), others config rows; crew animation tried then pose fallback; theft is an Owing entry; wake and water response (wake from ripple sim) (2.15 brief). Fare services for ferries/boats are separate (travel-services.json).
(b) Built: game-core/src/boats (sailing.ts, moorings.ts, recovery.ts, ownership.ts), boatRuntime in character; 2.15 done, plus 2.15x fixes.
(c) NOT in vanilla Morrowind/OpenMW (no rideable boats, no vehicles). Needs fork or a Lua kinematic-vehicle hack (move player plus passengers with a platform object; OpenMW has no moving-platform physics for actors, buoyancy is not simulated). Wave/wind systems exist only in visuals (wind is weather-driven in the repo). High risk.

### Movement, camera, controls
(a) Third-person follow camera with collision sweep (0.3 m ball, pull in at once, return 2.5 m/s only with input; model fades from 1.2 m arm), swim camera treats surface as ceiling, shoulder aim camera for bows (+0.55 right, +0.22 up, 1.7 back). Walk 4.5 m/s, sprint x(1+Athletics/250), jump 1.378 m. Input: desktop (mouse light/heavy, RMB guard, Q lock-on), GameSir X2s pad table (docs: apps/combat-sandbox/docs/architecture/input.md), phone touch on landscape-only HUD with stick sprint band 0.95/0.85 (io/input.ts:172). Three viewports: desktop, phone landscape 844x390, unfolded Honor Magic V5. Controller is clipped to phone.
(b) Built in packages/game-core/src/camera, io/input.ts, PlayerMovementController (ecctrl hidden behind it).
(c) OpenMW supports third-person camera, keyboard/gamepad (SDL), but touch is not a supported target (no OpenMW mobile main build; browser/phone target would be lost). Camera: Lua `openmw.camera` is capable (modes, offsets, collision). Souls-style locked camera: doable in Lua. Platform loss (phone/browser) is the strategic cost of OpenMW.

### UI, HUD, menus, theme
(a) "Morrowind made today" with Dark Souls HUD lean: dark mossy green-black panels, olive-bronze trim with vine/serpent flourishes, bone text, 4 tiled windows (stats, magic, inventory with paperdoll, map); font Pelagiad (OpenMW's free twin of Magic Cards); tokens in packages/ui/src/tokens/palette.ts (panel #0e1711, trim #6b7744, bone #d6cfb0, health #8f2e22, stamina #2a6b33, magicka #2f4e94, breath #386570, marker tan #d8b070, crime #e0705a). Souls bars top-left (grow with attribute), minimap (no compass), sneak eye, equipped-hands plaque bottom-left, effect stack bottom-right, toast queue, vastei plaque, place-discovered banner, floating prompt with glyph. Three map styles (faithful, chart default, waterways) rendered from real terrain data; golden-dart marker. Screens: pause windows, container, barter, dialogue, journal book, rest/wait, lockpick, death. Windows on desktop, full-screen pages on phone (2.2; apps/ui-lab 338 shots).
(b) Built: packages/ui + apps/ui-lab; live in studio and game.
(c) OpenMW Lua UI (`openmw.ui`) supports custom widgets, textures, fonts, layers: all menus rebuildable in Lua; HUD bars and layouts doable; map from real terrain would use OpenMW's own world map (cell-based) -- fork or render-to-texture. Pelagiad font is already an OpenMW asset. Good fit for UI.

### Save, rest, death, respawn
(a) Rest = the one mechanic: saves, consolidates one level, opens attribute sitting, restores pools; camp anywhere calm in wild but not in a dungeon, combat, hunted or inside a settlement (town: wait only; bed owned/rented gives rested buff x1.05/1.08 XP for 8 h). Death: wake at last rest, nothing lost, vastei pile drops at death spot (one pile, recoverable). Generic enemies respawn on rest, named/boss never, placed treasure never. Hidden suspend-save. No estus (76 §126, decisions 0031, 0039, 0144).
(b) Save families exist (progression, magic, crafting, owing, respawn, boats, traversal, death, locks, ...) but 2.13 (slot writer, coverage gate, export/import) is "todo".
(c) OpenMW has native saves and rest; Lua can add rest rules and death handling (0.49 `onDeath`, saved Lua state via `onSave`). Respawn on rest via Lua. Doable.

### Fast travel and travel services
(a) Morrowind-style: speak to ferryman/boat owner, pay a flat fare, arrive instantly over a defined graph; kinds ferry, boat, canoe, rootworm (guide/cart removed in Black Marsh); 23 services in travel-services.json. No generic fast travel. Hire rides closed in the game app; opened in studio (2.6, world/60 §430-440).
(b) Built: game-core/src/travel, resolveTrip, TravelMenu.
(c) Native Morrowind (travel services/silt strider). Easy.

### Time, schedules
(a) GAME_TIME_SCALE = 30 (1 game hour per 2 real min, day = 48 min); calendar, ephemeris, tides, weather timeline. One village clock: rise 05:30, work 06:30, meal 12-13, home 17:30 when lamps come on, bed 22:00; per-person jitter; role exceptions; predator hunt blocks; NPCs walk the path network when seen and swap when unseen (decisions 0138, 0140; world/72; people/clock.ts).
(b) Built (packages/world-time, game-core/src/people).
(c) OpenMW: timescale native (default 30); NPC schedules are NOT native (AI packages only, no schedule): Lua required (doable, a common mod pattern). Day-night sky and weather: OpenMW has weather and sky; custom weather/tides need fork.

### Fixed regional danger / difficulty
(a) Decision 0004: world never receives the player's level; enemies, traps and loot resolve to fixed absolute numbers by band D1-D5 (D0 = safe ground, location property); fixed difficulty binds the world, never the player; becoming absurdly powerful is a feature; play-time difficulty knob scales enemy damage only (0.7/1.0/1.35) (76 §102, §121.4, §128). Per-region roaming band table (0142).
(b) Built: ladder compiler, ladder-table.md, sim-based balance harness (packages/game-core/src/stats/sim).
(c) Native-friendly: Morrowind already has fixed placed actors; just avoid leveled lists and creature level scaling (OpenMW Lua can disable scaling). Doable.

### Items, inventory, containers, loot
(a) Items from class x material, soft requirements, 0-100 condition, tempering grades, burden, two hands each hold weapon/spell/torch/shield, quick belt, paperdoll; fixed placed loot (never levelled); containers with respawn class; locks/keys per container (76 §128.2, 2.3).
(b) Built (packages/game-core/src/inventory, items.json).
(c) Native: Morrowind item records, condition, weight. Skyrim weapon meshes need converting to OpenMW (NIF is shared lineage but SSE NIF needs conversion; OpenMW handles some SSE meshes since 0.49).

## Summary fit table
Native in Morrowind/OpenMW: attributes/skills/class/birthsign/race, spells/enchant/alchemy/soul gems/spellmaking, barter/training/services/travel, factions, dialogue/journal/quests, swimming, saves/rest, time scale.
Doable in OpenMW Lua: progression (vastei, rest-banked levels), stamina/poise arithmetic, effect stack, crafting stations/smithing, UI/HUD, camera, no-dice formulas for spells/locks/persuasion, NPC schedules, roaming bands/respawn, Owing ledger, dual-hand magic, burden tiers, danger bands.
Needs engine fork (or major risk) / new animations: real-time melee with sensors, i-frames, guard/parry, lock-on, poise stagger hit reactions, per-bone hit zones, projectile ballistics, BotW climbing, ladders, boats/sailing, touch/phone/browser target.

## Recommendations
- Treat 76 as the portable asset: its formulas are Morrowind formulas expressed deterministically (76 §116-127); the numbers (D-ladder, armour ladder, vastei) port to Lua tables directly.
- Combat feel (DS1) is the stack's riskiest port; prototype hit sensors + roll + parry in OpenMW before any other decision (evidence: vanilla OpenMW melee is skill/dice-based; the repo's combat is real-time resolveHit).
- Climbing and boats are the owner's explicit pillars (0152, 0159) and have no OpenMW substrate; scope them as fork items.
- The repo's own stale doc: docs/research/combat-and-systems/systems-inventory-2026-10-14.md contradicts PROGRESS.md; trust PROGRESS.md.

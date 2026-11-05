# Skyrim SE as the base for a DS1-feel total conversion: mod landscape, gaps, implementation

Research date 2026-10-27. Sources: Nexus mod pages and GitHub repo pages, read via WebFetch, plus wikis and community posts.

How to read this:
- "n/s" means the page did not show the field. Nexus often hides dates and permissions from fetchers.
- "page not retrieved" means Nexus refused the fetch. Facts in those rows come from search snippets or third-party mirrors.
- The GitHub API was gated in this session, so commit dates for GitHub repos are unverified.

> **Scope flag for the planner.** The repo's CLAUDE.md says Argonia is a *standalone browser game on Skyrim's assets* that takes "assets, never Papyrus or SKSE code". This brief instead frames a Skyrim SE + SKSE total conversion. The research below answers the brief as written. If the browser build is the real target, read these mods as **reference designs and licensed algorithm sources** (several are GPL/MIT/BSD), not as dependencies.

## 0. Platform state (affects every DLL below)

- **Runtime churn in 2026.** Bethesda shipped 1.7.99 on 20 Aug 2026, then 1.7.104. Heavily modded installs crashed at the menu.
  - The common workaround is to roll back to 1.6.1170 through the Steam depot (https://gist.github.com/SuperMalinge/203119e71b005fdb5b19336bce7bf615; forum thread https://forums.nexusmods.com/topic/13543597-skyrim-se-updated-to-1799/page/3/).
  - SKSE64 builds: 2.3.0 for 1.7.99, 2.3.1 for 1.7.104, with Address Library v13. These come from the Underwater NG compatibility page.
  - Many DLLs lag behind. Precision has an unofficial third-party port for 1.7.99/1.6.1170/1.7.104 (https://www.nexusmods.com/skyrimspecialedition/mods/189664, page not retrieved).
- **Recommendation: pin one runtime, 1.6.1170 or 1.5.97, and ship a downgrade guide.** Each upstream Skyrim patch can otherwise break the stack.
- Behaviour engines:
  - **Pandora Behaviour Engine Plus** (https://www.nexusmods.com/skyrimspecialedition/mods/133232; https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus). GPL-3.0, version 5.0.0-beta, updated 26 Oct 2026. Reads Nemesis and FNIS patch formats ("almost all" of Nemesis), patches creatures, and supports code-based plugins.
  - **Nemesis** (https://github.com/ShikyoKira/Project-New-Reign---Nemesis-Main) is the legacy option. Most frameworks below accept either engine.

### Linux / Proton
- SKSE works under Proton with MO2 through the community Linux installer (https://forums.nexusmods.com/topic/13472114-skyrim-se-in-mod-organizer-2-on-linux-working-well-so-far). The same thread reported OAR 2.0+ problems in 2024, possibly fixed by Proton 9.
- Pandora: the README says it runs on Linux via Wine or Proton but is "only Windows extensively tested". In practice (https://github.com/Furglitch/modorganizer2-linux-installer/issues/711):
  - Run `protontricks 489830 dotnetdesktop8`, add d3dcompiler_47/43, and add Pandora as an MO2 executable.
  - Some users saw Pandora detect no mods. Renaming `meshes`/`Scripts` to the casing FNIS used is a suggested, untested fix.
  - One user found that output generated on Windows and copied to Linux made NPCs stop meleeing.
- **Verdict:** workable but fragile. Generate behaviours on the machine that plays, and document the protontricks steps.

## 1. Combat: existing mods

| Mod | URL | Type | Last update | SE/AE | Source / licence | Notes, conflicts |
|---|---|---|---|---|---|---|
| **Precision** (Ersh), accurate melee collisions | https://www.nexusmods.com/skyrimspecialedition/mods/72347 ; https://github.com/ersh1/Precision | SKSE DLL; Nemesis/Pandora patch recommended (pitch and annotation events) | n/s (unofficial 1.7.x port at mods/189664) | SE+AE, no LE | GPL-3.0-or-later with Modding and Linking exceptions | **API (PrecisionAPI.h, V1–V4):** pre-hit callback (ignore the hit or add Damage/Stagger modifiers, additive or multiplicative), post-hit callback, weapon-weapon and weapon-projectile callbacks, collision filter and contact listener, `GetAttackCollisionCapsuleLength`, `ApplyHitImpulse2`. Hit data includes the hit rigid body, hit position, normal and velocity. Conflicts: No Follower Attack Collision (melee part), other hitstop/trail/recoil mods, and old TDM. TK Dodge needs Precision's patch. |
| **True Directional Movement** (Ersh), lock-on | https://www.nexusmods.com/skyrimspecialedition/mods/51614 ; https://github.com/ersh1/TrueDirectionalMovement | SKSE DLL | n/s | SE+AE | GPL-3.0+ with exceptions | Target lock with switching, multiple target points per actor (TOML), sprint while locked, projectile aim. **API V1–V5:** `GetTargetLockState`, `GetCurrentTarget`, `RequestYawControl`/`SetPlayerYaw`, `GetDirectionalMovementMode`, `GetActualMovementInput`, `IsTargetLockBehindTarget`, `RequestDisableTargetLock`. Behaviour events `TDM_TargetLock`, `TDM_Dodge`, `TDM_AttackStart/Mid/End`. **No API setter for lock distance.** The page does not document an MCM/INI distance setting; check `MCM/Config/TrueDirectionalMovement` in the repo. Conflicts: other lock-on mods and 360° movement behaviour mods. TK Dodge direction can go wrong. |
| **TrueHUD** (Ersh) | https://nexusmods.com/skyrimspecialedition/mods/62775 ; https://github.com/ersh1/TrueHUD | SKSE DLL | n/s | SE only | GPL-3.0+ with exceptions | Floating enemy bars, **boss bars** (INI-detected, queued), player widget, **special bars driven by other plugins** (poise/stun), and a widget API. Covers the boss-HUD need. |
| **Open Animation Replacer (OAR)** (Ersh) | https://nexusmods.com/skyrimspecialedition/mods/92109 ; https://github.com/ersh1/OpenAnimationReplacer | SKSE DLL | v2.3.6 | SE, AE, VR | GPL-3.0+ with exceptions; Nexus: no re-upload or modding without permission; asset use with credit | Condition-driven animation replacement that also reads DAR mods. **API lets SKSE plugins register custom conditions** (example plugin and Math plugin in the repo). Requires Animation Queue Fix. Incompatible with DAR itself. |
| **Attack – MCO\|DXP** (distar66), combo/attack behaviour framework | Attack - MCO (https://www.nexusmods.com/skyrimspecialedition/mods/175044 and "MCO Updated" https://www.nexusmods.com/skyrimspecialedition/mods/181779, both pages not retrieved) | Behaviour (Nemesis/Pandora) plus annotations (`MCO_WinOpen`, `MCO_PowerWinOpen`, recovery events) | 1.6.0.6 is the base most patches target; the bug-fix ecosystem was active April 2026 (https://www.nexusmods.com/skyrimspecialedition/mods/176565, https://nexusmods.com/skyrimspecialedition/mods/117275) | SE/AE | Closed | The de-facto moveset standard for years. Incompatible with BFCO. The older Attack Behavior Revamp (https://www.nexusmods.com/skyrimspecialedition/mods/45378, 2021, Nemesis+DAR) has very open permissions. |
| **BFCO – Attack Behavior Framework** (BF001) | https://www.nexusmods.com/skyrimspecialedition/mods/117052 ; SKSE part: https://github.com/max-su-2019/BFCO | SKSE DLL plus behaviour | **v3.100.11, 20 Sep 2026**; 3.100.8 supports 1.7.104 | SE/AE, VR NPCs only | Nexus: upload, modify and use with credit; no paid use. GitHub licence n/s | Melee and ranged, jump and **swim attacks**, charge, directional power attacks, NPC combos, custom events. Requires AMR, OAR, Payload Interpreter, MCM Helper, XPMSSE, Nemesis or Pandora. **Incompatible:** MCO/ABR/SkySA, power-attack hotkey mods, Dual Wield Parrying, CGO, FNIS. **The most actively maintained choice.** |
| **SCAR** (Maxsu), NPC combo AI | https://www.nexusmods.com/skyrimspecialedition/mods/72014 ; https://github.com/max-su-2019/SCAR | SKSE DLL (SE/AE/VR) | releases on GitHub (SCAR 2.0) | SE/AE/VR | **MIT** | Per-moveset attack AI: distance and angle checks pick the next strike. Movesets must be SCAR-patched. Patches are needed for SkySA, ABR and DBC. |
| **Combat Pathing Revolution (CPR)** (Maxsu), spacing and strafing | https://nexusmods.com/skyrimspecialedition/mods/86950 ; https://github.com/max-su-2019/CombatPathingRevolution | SKSE DLL | n/s; stable on 1.5.97, unofficial 1.6.x build | SE (AE unofficial) | n/s | Advance, Backoff, Circle and Fallback behaviours, data per moveset. **Incompatible with Fenix Combat AI (crash).** Example data: https://www.nexusmods.com/skyrimspecialedition/mods/125740. |
| **Ultimate NPC Dodging (UND)** | https://nexusmods.com/skyrimspecialedition/mods/120738 | SKSE DLL | n/s | n/s | Credits dTry's open code | NPC sidesteps and rolls against melee, bow and shouts. Tactical flanking and backing off. Needs TK Dodge RE files. |
| **Wait Your Turn** (Monitor144), enemy circling and attack tokens | covered at https://www.sportskeeda.com/esports/new-skyrim-combat-mod-adds-enemy-circling-behavior | Behaviour/ESP | n/s | SE | n/s | Caps simultaneous attackers and sets an attack interval. Compatible with CPR. |
| **Distance Based Combat** | https://nexusmods.com/skyrimspecialedition/mods/60855 | Skyrim Platform + Nemesis | n/s | SE/AE | n/s | Range-banded NPC behaviour, gap closers. |
| **TK Dodge SE** (tktk) | https://www.nexusmods.com/skyrimspecialedition/mods/15309 | Papyrus + behaviour (FNIS for step dodge) | v3.18 | SE 1.5.97 + AE 1.6.353 | **Restrictive:** no modify, no re-upload, asset use only with permission | Fixed i-frames (default 0.3 s) at the dodge start. Carry-weight condition. |
| **TK Dodge RE** (Maxsu et al.) | https://www.nexusmods.com/skyrimspecialedition/mods/56956 | SKSE DLL, script-free | n/s | SE/AE | n/s | **`iFrameDuration` (seconds) in the INI**, via I-Frame Generator. Works with TDM. Step and sneak dodge. Successors: TK Dodge NG Redux (https://www.nexusmods.com/skyrimspecialedition/mods/156666; v1.5, Oct 2025, configurable i-frames per roll and step, needs Precision and Pandora; marked unmaintained) → TK Dodge Redux (https://www.nexusmods.com/skyrimspecialedition/mods/160098, page not retrieved). |
| **Ultimate Combat** (TK) | Oldrim: https://www.nexusmods.com/skyrim/mods/29137 | Papyrus/behaviour | old | SE versions exist as ports | restrictive | Legacy. Do not build on it. |
| **Valhalla Combat** (dTry) | https://nexusmods.com/skyrimspecialedition/mods/64741 ; https://github.com/D7ry/valhallaCombat | SKSE DLL | n/s | SE/AE | **BSD-3-Clause** | Stamina regen and costs, exhaustion, timed block or parry (default window 0.25 s), stun meter, executions, TrueHUD special bar. Clashes with Poise mods over the TrueHUD bar. |
| **Elden Parry** (dTry) | https://www.nexusmods.com/skyrimspecialedition/mods/70240 ; https://github.com/D7ry/EldenParry | SKSE DLL + ESL | n/s | SE/AE | n/s | A light bash becomes a parry. **`fParryWindow_Start`/`fParryWindow_End` configurable** (one addon suggests 0.02–0.2). Deflects projectiles, slow-time feedback. **No riposte**; addons provide it. |
| **Rim Parry** (SHADOWPQ) | https://nexusmods.com/skyrimspecialedition/mods/114366 | OAR anims + addon | n/s | SE/AE | n/s | Adds what Elden Parry lacks: parry ×2 → execution, **backstab within ~60° behind → execution**. Needs ModernStaggerLock, Payload Interpreter, BDI, Elden Rim. |
| **zxlice Backstab and Parry** | https://nexusmods.com/skyrimspecialedition/mods/43436 | SKSE DLL + Nemesis | v1.1.2 | SE/AE | n/s | Backstab from behind, timed-bash parry (0.1–2 s), creature fallbacks. Incompatible with CGO. |
| **Blade and Blunt** (Simonrim) | https://nexusmods.com/skyrimspecialedition/mods/34549 | SKSE DLL | n/s (supports 1.5.97 + 1.6+) | SE/AE, not VR | DLL source linked | Stamina costs, attacks of opportunity, stagger, block and parry, injuries. A systemic rebalance, not a Souls timing system. |
| **Poise (Loki) → Poisebreaker** | https://nexusmods.com/skyrimspecialedition/mods/74032 | SKSE DLL | n/s; SE 1.5.97 and AE files | SE/AE | n/s | Pool from equip weight, Heavy Armor skill, level and armour; damage from weapon weight plus 10% of damage; Loki's base regen tick of 3.5 s; brief immunity after a break; hyperarmour. Replaces vanilla stagger, so patches are needed. |
| **Chocolate Poise** (doodlum) | https://nexusmods.com/skyrimspecialedition/mods/70478 ; https://github.com/doodlum/skyrim-poise | SKSE DLL | n/s | SE/AE | **MIT** (+ GPL file); "do whatever you want" | Pool = mass + ½ armour. Regen to full over 30 s (configurable). Weight and type based poise damage. TrueHUD meter. Precision recommended. **The best MIT base for a DS1 poise fork.** |
| **Archery Locational Damage** (Tossapon) | https://nexusmods.com/skyrimspecialedition/mods/63863 | SKSE DLL | n/s | SE/AE | n/s | Arrows only. Head ×2.0 (×1.5 against a heavy helmet). There is **no melee hit-zone mod**; Precision exposes the hit rigid body, so it is buildable. |
| **Animation Motion Revolution / Fix** | AMF: https://nexusmods.com/skyrimspecialedition/mods/145100 | SKSE DLL | n/s | SE/AE/VR | n/s | Root-motion and magnetism fixes needed by BFCO-era movesets. |
| Modlists | LoreRim https://lorerim.com/read-me.html ; Elder Souls (Wabbajack) https://github.com/Timboman/eldersouls ; Nolvus guide https://www.nolvus.net/guide/asc/animations/attack (not retrievable) | — | — | — | — | LoreRim: Requiem + Attack-MCO on 1.5.97 with 1.6.1170 CC. Elder Souls: Blade and Blunt + DS-style death and bonfire loop. No modlist ships **DS1 numbers**; all are tuned by feel. "Elden Rim" (Weapon Arts) is a moveset and skill ecosystem, not a full list. |

## 2. Traversal, water, boats, ragdoll

| Mod | URL | Type | Last update | Runtimes | Licence | Notes |
|---|---|---|---|---|---|---|
| **FreeClimb** (Eelta) | https://www.nexusmods.com/skyrimspecialedition/mods/193552 (page not retrieved) ; https://github.com/Eelta/FreeClimb (fork: HelloWorld-Z000/FreeClimb) | SKSE DLL (CommonLibSSE-NG), own action/state system, 35 HKX anims | 2026 (repo had 1 commit) | 1.5.97; AE 1.6.317–**1.7.104**; GOG 1.6.1179; no VR/GamePass/Epic | **GPL-3.0-only** code; menu API LGPL-2.1; anims Mixamo/Threepeat (third-party terms); audio Kenney (CC0) | Free climbing on any valid wall, **wall run, sideways leap catches, push-away, let go, auto mantle**, obstacle bypass, **optional stamina drain (wall run 2×)**, menu, diagnostics. Swappable anim slots. **Closest to BotW.** No ladders. |
| **SkyParkour v3 (SPPF)** (Tsptds / JellyfishInLoop) | https://www.nexusmods.com/skyrimspecialedition/mods/132292 | SKSE DLL + behaviour (Pandora/Nemesis), needs TDM | **v3.5.4, ~May 2026** | SE/AE | n/s | Procedural ledge climb and vault, mid-air ledge grab, climbing out of water, stamina based on equipment weight, 360° camera, weapons drawn, landing roll. Incompatible with SkyClimb. **Ledges only, no wall hang or shimmy.** |
| **SkyClimb** (Sokco) | https://www.nexusmods.com/skyrimspecialedition/mods/97253 ; https://github.com/Sokco/SkyClimb | SKSE DLL + EVGAT anims + PO3 Papyrus Extender | v1.1.1, Aug 2023 | SE/AE | Restrictive Nexus permissions; source on GitHub | Ledge climb plus vault. Superseded by SkyParkour. |
| **EVG Animated Traversal** (Everglaid) | https://www.nexusmods.com/skyrimspecialedition/mods/63232 | Marker based (placed in the CK), OAR | v2.1, May 2024 | SE/AE | n/s | **Ladders**, ledges, vault and duck **at authored markers**, NPC traversal scripts. Ladder marker packs: https://nexusmods.com/skyrimspecialedition/mods/70635. **The best ladder option; it fits hand-built places.** Stamina add-on: https://www.nexusmods.com/skyrimspecialedition/mods/93346. |
| **Underwater NG** (Ckw25) | https://www.nexusmods.com/skyrimspecialedition/mods/187230 | SKSE DLL | **v1.0.1.4, 8 Sep 2026** | 1.5.97 → 1.7.104 | Mixed: C++ GPL-3.0+, other files separate | Buoyancy from equipment, swim speed, **Diving skill**, depth visuals and audio, wetness, cold. No underwater combat (BFCO covers swim attacks). Vanilla already allows diving and breath. |
| Swim sprint (AndrealphusVIII) | https://nexusmods.com/skyrimspecialedition/mods/67028 | ESP + anims | n/s | SE | n/s | Sprint-swim (dolphin kick underwater, freestyle on the surface). |
| **Sailable Ship VR and SE** (ziher) | https://www.nexusmods.com/skyrimspecialedition/mods/72070 | SKSE + Papyrus (script heavy) | v1.12, Dec 2023 | SE/VR | Modify with credit; asset use with credit | **Player steers at the helm** with a keyboard or pad. Wind simulation. Deck walking at speed is unstable, sails do not animate, saving at the helm can stick the player, needs 60 fps. The best "real helm" base, but it is scripted translation, not physics. |
| **Sailboats – Script Free Sailing EXPANDED** | https://www.nexusmods.com/skyrimspecialedition/mods/40057 | **Mount (race) based** | May 2021 | SE | Restrictive | Boat is a mount (horse-like ownership, storage, anchor, passengers). Two-race sail trick. Drives over land. |
| L.V.X Boats | https://www.nexusmods.com/skyrimspecialedition/mods/36149 | Papyrus | v1.3.2, Apr 2023 | SE | Restrictive | Craft and deploy boats, raise sails, auto-level float. |
| Skyrim Rowboats (DE) | https://www.nexusmods.com/skyrimspecialedition/mods/1019 | ESP | 2022 | SE/AE | **CC BY-SA 4.0; code Unlicense** | Buyable rowboat steered like walking. Open licence. |
| Rowboat spell (Vusz) | https://nexusmods.com/skyrimspecialedition/mods/123321 | Mount, no scripts | n/s | SE | n/s | Summoned rideable rowboat. |
| Animated Ships | https://www.nexusmods.com/skyrimspecialedition/mods/110260 | NPC ambient | n/s | SE | n/s | NPC-sailed only. |
| **PLANCK** (FlyingParticle) | https://nexusmods.com/skyrimspecialedition/mods/66025 | SKSE DLL | n/s | **VR only** (needs HIGGS) | source on GitHub | True active ragdoll and physical hit reactions. No flat-screen equivalent. |
| XP32 True Ragdoll Physics | https://www.nexusmods.com/skyrimspecialedition/mods/161116 | Skeleton NIF edits | Oct 2025 | SE/AE | MIT-style per the author | Better death ragdolls (sphere inertia, friction). |
| Precision hit impulse | (Precision API `ApplyHitImpulse2`) | — | — | — | — | Hit impulses on ragdolls and creatures. Fine for "ragdoll nice-to-have". "Skyrim Delirium – GTA IV-style hit reactions" (https://www.nexusmods.com/skyrimspecialedition/mods/196333) exists but was not retrievable. |

## 3. Coverage verdict per feature

| Feature | Verdict | Best stack | Difficulty to reach DS1-exact |
|---|---|---|---|
| Weapon-contact hit detection | **Covered** | Precision | Low |
| Roll i-frames by equip load (13/11/9 f) | **Partly**: i-frames configurable globally (TK Dodge RE `iFrameDuration`); no equip-load tiers | TK Dodge RE/Redux + own plugin | Medium |
| Parry 0.1–0.29 s + riposte | **Partly**: Elden Parry window configurable; riposte via Rim Parry or Valhalla execution | Elden Parry + own riposte paired anim | Medium |
| Backstab | **Partly**: zxlice / Rim Parry (angle-based, paired anims) | own (angle + vanilla paired sneak kills) | Low–Med |
| Lock-on 20 m | **Covered** (TDM); distance via TDM settings, unverified | TDM | Low |
| One stamina bar | **Covered** (vanilla AV + Valhalla/B&B costs) | vanilla + own costs | Low |
| DS1 poise (hidden pool, ~5 s refill, break → stagger) | **Partly**: Chocolate Poise/Poisebreaker are close but refill differently (30 s gradual / 3.5 s tick), and their meters are visible (can be turned off) | fork Chocolate Poise (MIT) | Low–Med |
| Hit zones (head ×2) | **Gap** for melee (arrows only exist) | own via Precision pre-hit (hit rigid body → bone → multiplier) | Low |
| Enemy AI spacing, strafing, punishing | **Partly/covered**: CPR + SCAR + UND + Wait Your Turn; punish windows need data | CPR+SCAR+UND | Medium (tuning) |
| Bosses | **Partly**: SCAR movesets, TrueHUD boss bar; phases and arenas are bespoke | own | Medium–High (content) |
| BotW free climb (hang, shimmy, leap, mantle, stamina) | **Partly→mostly**: FreeClimb (GPL) | FreeClimb (+ SkyParkour for ledges) | Medium |
| Ladders | **Covered at markers** (EVGAT) | EVGAT | Low |
| Swimming and diving | **Covered** (vanilla + Underwater NG) | Underwater NG | Low |
| Wind Waker player-steered sailing | **Partly**: Sailable Ship (scripted helm, wind) | fork or rewrite as SKSE | High |
| Boats owned like horses | **Partly**: Sailboats (mount race) | mount race + own stabling | Medium |
| Ragdolls | **Partly**: death ragdoll tweaks, Precision impulses; active ragdoll VR-only | XP32 TRP + Precision | Low (nice-to-have) / Very High (active) |

## 4. Getting DS1-exact numbers on top: "ArgoniaCombat.dll"

### 4.1 Architecture
One CommonLibSSE-NG SKSE plugin that *consumes* the framework APIs and owns all numbers in one data table (TOML/JSON keyed by record id). It replaces none of the frameworks.

- **Hit pipeline (Precision API V4).**
  - In `PreHitCallback`, return `bIgnoreHit` when the target is in an i-frame window. This is the authoritative i-frame source, more reliable than the engine's ghost flag.
  - Map `hitRigidBody` to its skeleton bone (`GetOriginalFromClone` → node name, e.g. `NPC Head [Head]`) and push a `Damage × 2` modifier for head hits.
  - Push a `Stagger` modifier of 0 so vanilla stagger is suppressed, and apply our poise instead.
  - Use `PostHitCallback` to record the time of the last hit, which starts the poise refill clock.
  - Use the weapon-weapon callback for parry clash detection.
- **Dodge.**
  - Keep TK Dodge RE (or Redux) for input and animation.
  - Pick the roll animation by equip-load tier with an **OAR custom condition** registered by our plugin (`ArgoniaEquipLoadTier == 0/1/2`). Equip load = equipped weight ÷ capacity, computed ourselves.
  - Start our own i-frame timer on the dodge-start animation event (`TKDodgeStart`/`TDM_Dodge`) with tier lengths 13/11/9 frames at 30 fps (0.433/0.367/0.300 s). Set TK's `iFrameDuration` to 0 so the two do not compete.
- **Parry and riposte.**
  - Listen for the bash-start event and open a parry window from 0.10 s to 0.29 s after it, game time.
  - A hit whose attack frames land inside that window is cancelled. The attacker gets a parried-stagger state for N s.
  - A riposte input during that state plays a paired idle (vanilla killmove or paired system; Paired Animation Improvements) with a riposte damage multiplier.
  - Elden Parry can be dropped or kept only for projectile deflect.
- **Backstab.** Check the target-facing angle (|Δyaw| < θ), distance and that the target is not attacking, then play a paired sneak-attack idle. Rim Parry uses about 60°, a useful prior.
- **Poise.**
  - Fork Chocolate Poise (MIT), or write about 300 lines.
  - Hidden pool from armour poise. Each hit subtracts the weapon's poise damage. Pool ≤ 0 triggers stagger and a full reset.
  - Refill to full after 5 s with no hit (DS1 behaviour as the owner specifies). Hyperarmour flags come from attack animations through annotations.
  - Hide the TrueHUD meter.
- **Lock-on.** Keep TDM. Set the lock distance in its settings (20 m ≈ 1400 Skyrim units, since 1 unit ≈ 1.43 cm). If no setting exists, use `RequestDisableTargetLock` when the target is beyond range, polled per frame from our plugin.
- **Stamina.** Use the vanilla Stamina AV. Set costs and regen per action from our table. Block regen during actions with a graph-variable check.
- **AI.** CPR for spacing and strafing, SCAR for combo choice, and UND/TK RE for NPC dodges. "Punish" = SCAR conditions on target state (recovering, whiffed, healing) read from our plugin's state via custom graph variables. Bosses get per-boss SCAR and CPR data, TrueHUD boss bars, and phase switches done in our DLL (HP thresholds → swap combat style or moveset with OAR conditions).

### 4.2 The universal-modder loop: measure DS1R, implement, verify ±1 frame
1. **Measure DS1R.**
   - Unpack with **Soulstruct** (https://github.com/Grimrukh/soulstruct; DS1PTDE/DS1R params, maps, EMEVD, AI).
   - Read and compare TAE event timings in **DSAnimStudio** (https://github.com/Meowmaritus/DSAnimStudio, GPL-3.0; DS1R editable, events mapped).
   - Name params with **Paramdex** (https://github.com/nex3/paramdex, DS1R defs).
   - Pull these numbers:
     - roll TAE invincibility event start and end per roll animation (fast, mid, fat, flip);
     - parry TAE active window per shield class;
     - armour poise and weapon poise damage from the EquipParamProtector/EquipParamWeapon fields (names per Paramdex);
     - the poise recovery timing;
     - stamina costs and regen.
   - TAE times are seconds, and DS1 logic runs at 30 fps. Convert with frame = round(t × 30).
2. **Record a "golden table"** (CSV/JSON) of seconds and frames, with the source file and anim id per row. This is the single source of truth. The owner's values (13/11/9 i-frames, 0.1–0.29 s parry, 5 s poise refill) override it where they differ.
   - **Note:** the Dark Souls fandom wiki lists 11 i-frames for fast, mid and fat rolls and 13 for the ninja flip (https://darksouls.fandom.com/wiki/Rolling). That does not match 13/11/9, so the measurement will settle it, and the owner decides.
3. **Implement in SKSE** using game-time timers. Never count frames, because Skyrim's frame rate varies. Do the windows in seconds from animation events.
4. **Verify ±1 frame (±33 ms at 30 fps; aim for ±16 ms).**
   - Add a debug console command to the plugin: spawn an NPC test dummy and script its attack so contact lands at offsets of t0 + k × (1/60) s relative to the player's roll or parry start.
   - Log `PreHit` accept or ignore, with timestamps from the same clock.
   - The measured window boundaries must sit within one DS1 frame of the golden table.
   - Run at a capped 60 fps and a capped 30 fps to show frame-rate independence.
   - Extra check: Precision's collision runs inside the havok step, so a fast swing can tunnel. Log contact time against annotation time.

### 4.3 Animation sourcing
- **Existing movesets.**
  - BFCO and MCO movesets on Nexus. Permissions vary: Elden Rim ecosystem packs such as https://www.nexusmods.com/skyrimspecialedition/mods/175303 defer to the original animators; DS3-derived packs such as "Cathedral Knight Greatmace" https://www.nexusmods.com/skyrimspecialedition/mods/178147 forbid modifying or reusing assets without permission.
  - Attack Behavior Revamp (45378) has very open permissions but an old moveset.
  - BFCO permits use with credit. Movesets for it are separate works.
- **IP risk.** Packs extracted from FromSoftware games (DS3/ER animations) are FromSoftware IP whatever the Nexus permissions say. Avoid them for a distributed TC.
- **Better routes:**
  - Original Skyrim-modder movesets, with permission from the animator (credit and sourcing-register row).
  - Vanilla Skyrim attacks retimed with hkanno annotations (timing on the animation side, which matches the repo rule).
  - FreeClimb's Mixamo/Threepeat climb anims under their own licences (check that Mixamo terms allow redistribution inside a mod).
- Because players download dependencies, the TC can *require* moveset mods rather than redistribute them. This avoids most permission problems. Pin exact file versions.

## 5. Recommended dependency stack (pinned runtime 1.6.1170)
SKSE 2.2.6, Address Library, Pandora, OAR (+ Math), Precision, TDM, TrueHUD, BFCO (+ AMR, Payload Interpreter, MCM Helper, XPMSSE), SCAR, CPR, UND, TK Dodge RE (+ I-Frame Generator, i-frames handed to our DLL), FreeClimb, EVGAT (ladders), Underwater NG, Sailable Ship (interim), XP32 True Ragdoll. Then **ArgoniaCombat.dll** (dodge tiers, parry/riposte, backstab, poise, hit zones, stamina table, boss phases) and **ArgoniaBoats.dll** (helm + mount-race ownership: stabled at docks, whistle-equivalent "call boat" to nearest shore marker; water check to forbid land travel).

Known conflict pairs to keep in mind: BFCO vs MCO/ABR/Dual Wield Parrying/CGO; CPR vs Fenix Combat AI; SkyParkour vs SkyClimb; Poise mods vs Valhalla (TrueHUD bar); TDM vs other lock-on and 360° behaviour mods; Precision vs No Follower Attack Collision (melee).

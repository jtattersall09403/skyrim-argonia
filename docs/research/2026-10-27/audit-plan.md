# Audit: the plan and the owner's rulings (Elder Souls: Argonia)
Repo: /home/claude/elder-souls-argonia/docs (paths below relative to it unless absolute). Read-only audit, 2026-10-27.

## 0. Reconciliation
- Live docs: phases/README.md (plan), PROGRESS.md (status), ../lanes/handoff/STATE.md, decisions/README.md (index, 0001-0159), world/00-core.md (vision), phases/2-slice/README.md (perf section).
- Confirms: PROGRESS.md and phases/README agree: Part 1 closed (0135), Part 2 all done except 2.14 sound and 2.13 persistence (todo). STATE.md says "2.14 sound and 2.13 persistence need the owner's ask".
- Supersedes: 0034/0062/0038 order (by 0134). 0106 partly by 0131. 0087 partly by 0106. 0121 by 0122.
- Single doc to edit for any rebuild-direction note: phases/README.md (plan) + one new decision record (decisions/ is the home of "why").

## 1. Vision, in the owner's terms
- Elevator (README.md:1-6; world/00-core.md "What we are building"): fan, non-commercial, standalone total-conversion-style Skyrim game; "vibe and world-design values of Morrowind, Dark Souls-like combat, BotW climbing, extensive swimming, sailing and underwater exploration", Black Marsh province, ~7.4 km, about Skyrim's land area (0015), played in the browser. Owner's one-line steer (0149): "mostly morrowind and skyrim shaped with dark souls combat".
- Fixed regional danger (0004, 0007, world/00-core rule 2): world never receives player level; encounters, loot, hazards fixed by place/era/state. Player earns depth via capability (swimming, boats, resistance gear, alchemy). Owner philosophy (0031): "fixed difficulty binds the world, never the player's earned capacity to cope"; buying/brewing your way through a hard area is the intended fun. One difficulty multiplier scales incoming damage only (0033).
- Morrowind density (0027): 18-22 named places/km2 in low-danger land, 8-12 deep; something named within 300 m of travel on every road; new landmark about every minute of walking; ~550-750 named places, ~450-550 quests at maturity; every settlement building enterable (0103, owner 2026-09-28) and every NPC named. Soft: hostile density preference not a floor (0049 item 5).
- Discovery (0137, owner): no markers until reached on foot; journal and dialogue give directions written against the real route network; "finding a place is the play". Grantable markers only via in-world acts.
- Tone/story (0026, owner): stakes visceral and legible within first two hours, assume no lore beyond "maybe played Morrowind"; 23 core quests (was 32), playtime target 25-35 h main line; three endings CUT / CLAIM / MEND; dropped boats-chasing-boats (rails-following craft "a minefield"); Argonian lore (Hist trees, Owing ledger, vastei = levelling currency, cult killing the tree-gods).
- Combat/stats (0031, 0033, 0035, 0037, 0040, 0147): Souls-like currency (vastei) drops where you die, one retrieval; seven attributes (Morrowind minus Luck), 27 skills; weapon skill sets damage position not dice; DS1 poise model (0037 item 5); parry windows per weapon family (0040); estus cut, potion healing; no moveset unlocks or wield requirements; level 2 in 15-30 min and early levels quicker than later (0147); owner's memory of Morrowind pace used as the calibration; campaign ends L69-90.
- Rest is the one mechanic (0144): rest saves, levels up, respawns generic enemies (0031 owner ruling), no manual/quick save; death wakes at last rest. No survival layer, no bleedout, no mounts (0039, 0042).
- Systems whole, content thin (0134, 0144, 0146, 0150, 0151, 0152, 0153): every system ships "whole"; slice fills only what it touches but whatever the player meets is complete.
- Traversal: Swim in 3D "as Skyrim does" (0093); climbing = BotW, province-wide generalised (0152); boats sailed like The Wind Waker, wind is the weather's, dugout and sea hull first, horse-like ownership (0159, 0158).
- Graphics/devices (0084; lanes/2.15x/owner-fixes.md): "only aiming for Skyrim-era graphics; almost trivial on an M2"; reference devices Apple M2 (MacBook Air) and Honor Magic V5 phone (folded/unfolded). Latest owner goal 2026-10-26: native resolution, 60+ fps 95% of frames, GPU offload, "Walk here" to loaded <= 15 s (lanes/handoff/STATE.md).
- UI: one consistent UI on desktop/phone/pad (2.2); every action reachable on keyboard, pad, touch (STATE.md rules).
- Provenance: Skyrim assets + credited community mods (README Credits); private personal-use, undistributed; "we never make art" (CLAUDE.md, world/90). Owner's permission covers every asset in the owner's collection (0098).

## 2. Owner rulings: durable preferences

### 2a. Engine-agnostic (carry to OpenMW)
| Ruling | Gist | File |
|---|---|---|
| Fixed difficulty | no player-level scaling anywhere | 0004, 0007, 0031 |
| Era 4E 201 | lore frozen to early 4E | 0002 |
| Morrowind density | places/quests per km2, enterable buildings, named NPCs | 0027, 0103 |
| Directions not markers | discovery by walking | 0137 |
| Fixed loot, never levelled | containers are authored records | world/00-core rule 9 |
| Respawn on rest | generic enemies respawn at rest; named/boss never; completed dungeon stops | 0031 |
| Rest is the one save | no quick/manual save; death wakes at rest | 0031, 0144 |
| Souls currency | vastei drops where you die, one retrieval | 0031, 0033 |
| Stats | 7 attributes, 27 skills, Morrowind formulas minus dice; deterministic score compares | 0035 |
| Poise | DS1 model, shared by player and enemies | 0037 |
| No practice discount, no repeat-target damping | grind is chosen play | 0037 |
| Early levels fast | L2 in 15-30 min | 0147 |
| Disposition changes talk, essential topics never gated, floor 0, recovery daily | 0145 |
| Dialogue | Morrowind-shaped mechanics; facts once, opinions per person; no two identical sentences; voice acting out | 0139, 0143 |
| One price contract | coin, goods or favour; money thins inland | 0141 |
| Hostile places attack on sight; roaming bands from region table; violence answered by victims | 0142 |
| People live by lamp clock; Skyrim-style days; shops lock; no followers; no one unkillable | 0138 |
| Magic whole | Skyrim hands, five cast styles, effect families, Morrowind spell list; folk sellers | 0146, 0148 |
| Crafting whole | alchemy picks, smithing, enchant with soul tiers | 0150 |
| Stealth/crime whole | per-observer detection; sneak blow never auto-kills; Owing (pay/serve/resist); no watch = locals challenge | 0151, 0039 |
| Climb BotW generalised; swim 3D; boats Wind Waker | 0152, 0093, 0159 |
| Quests as data; text apart from logic; validator checks directions against route graph | 0153 |
| Tier protection for quests (main > faction > side) | 0030 |
| Cuts: mounts, drifting settlements, fire spreading, tide gating, river-pirate system | 0042 |
| Kept: Hist communion powers race-neutral | 0042, 0039 |
| Main quest shape/endings | 0026, 0028 |
| Studio plays the game: no modes/flags for game actions | 0149 (rule is engine-agnostic: test what ships) |
| Test each block at cheapest level | 0156 |
| Agent cost/process | 0079, 0083, 0106, 0118, 0131 |
| RunPod no fixed time cap; price first, delete when done | 0119 |
| Dialogue on Sonnet not Opus | 0079 (owner 2026-10-18) |
| Fix-forward deploy: build gates deploy, checks signal | 0154 |
| Layers on a built place never rebuild it; incremental by record id | 0140, 0128 |
| Cities hand-built by district in 3D | 0133 |
| Place loop: owner walks each place until right; two clean passes per type | 0099 |
| A place carries its own ground; builder verifies everything measurable before handing over | 0102 |

### 2b. Tied to three.js / Skyrim assets / browser
| Ruling | Why tied | File |
|---|---|---|
| Package-shaped code, apps compose | monorepo/three architecture | 0134, 0038, CLAUDE.md |
| Triangle budget 4 M/frame on M2 Chrome; LOD ladder as Skyrim; tree cards | WebGL budget | 0084, 0075, 0082, 0108 |
| Fixture light field (100-slot texture) | three.js point-light limitation | 0108 |
| WebGPU retired, WebGL canonical | owner 2026-10-03 ("not working super well") | 0122 |
| Audio as Opus/WebM | browser | 0094 |
| Kits stream per piece | browser download | 0120 |
| Skyrim assets via compilers/kits; NIF root rotation rules; plugin data is the interior manifest | Skyrim data | 0114, 0135, 0127 |
| Skyrim animation packs/rig; FreeClimb clips | Skyrim rig | 0040, 0152 |
| RunPod pod lane / SwiftShader | no local GPU | 0119 |
| GitHub Pages deploy; phone check | hosting | 0154 |
| ecctrl behind PlayerMovementController | physics lib | 0093, CLAUDE.md |
| Rapier physics aliasing bug etc. | | lanes/2.15x/owner-fixes.md |

## 3. Status per phase
- Part 1 (closed, 0135): 0-8c, 10, 16 done; frozen hydrology/terrain/water/apron/routes/vegetation; 16 real places; tier A interiors. The 16k place loop took 12+ owner walks (walk 11/12 cited in 0122, 0129). Helstrom city paused to 4.1b; its cost audit (0133: 13 builder parts, ~34 agents past 150k context, 30.5 VM-hours, 13 whole-city re-emits) forced "cities are hand-built".
- Part 2 slice: done 2.1-2.12, 2.9c, 2.10, 2.10b, 2.15, 2.15x (PROGRESS.md). Todo: 2.14 sound and music, 2.13 persistence + coverage gate + owner playthrough (the Part 2 exit). Deployed to GitHub Pages most rounds (run ids in PROGRESS).
- Part 3 (shell: boot, menus, char creation, opening, first playable) todo, Starting state not written. Part 4 (region packets; 827 catalogue records, 567 sited, 327 dungeon-kind interiors, per FACTS.md) todo. Polish backlog ~470 table rows (phases/P-polish/backlog.md).
- Counts: 782 people, 42 species, 89 people with full lines (PROGRESS rows 2.4/2.5).
- Reds (STATE.md): three climb visual:check scenes red since 2.12; 60 fps on Honor Magic V5 estimated not measured; ~90 s to playable on Fast 4G vs owner's 15 s.

### Hardest / longest, and why
1. Frame rate and load on mobile. lanes/2.15x-full-res/report.md: estimate misses 16.7 ms by 2.3-8x at native DPR; pod GPU timer did not respond to pixel count, so the limit is CPU submission/gap time under phone CPU throttle (773 draws/frame, ~448 materials, setProgram 5.2 ms/frame; lanes/2.15x-cut-3ms/report.md). Cuts of a few ms did not resolve in A/B. Load: 27 s -> estimated 8-15 s only after cache warming while map is open (lanes/2.15x-load-15s/report.md); before, 75 MB fetched after click. Lesson: three.js main-thread overhead plus streaming of huge kit/texture sets is the long pole; 777 MB Pages build (3.1 brief).
2. Place building / asset kit truth (Part 1): mined abuts/mounts/sinks, kit rebuilds (83-min abuts full run for one kit piece, workflow-cost-review-2026-09-28.md); cities (Helstrom) cost; "frozen world" decisions 0059, 0102, 0140 exist because rebuild chains were intractable. Lesson: freeze base, layer on top, incremental by id.
3. Test/film harness churn (2.10): "Twelve filming passes for one feature, almost none finding a game defect. The owner's words: inexcusable; we build the game, not the tools." (0156).
4. Gate churn: preflight ran 16 times for 7 commits, each red on already-red HEAD; code review 13 times in a day (workflow-cost-review). 0131 one gate; 0106 owner: "too slow, overcautious; every VM minute and token costs me".
5. Water (8b, 0045/0046 retired overhaul, 0047-0049, 0060-0065): repeated owner walk rulings; terrain scale judged on foot only (0015: flyover lied: "on foot it reads absurdly steep").
6. Studio vs game divergence: modes/flags tested instead of the shipped path (0149); roll did nothing in deployed build.
7. Specific game bugs hit: Rapier "unsafe aliasing" on reload; ground bob on load; shredded canopies on medium tier; camera in interiors (owner-fixes.md).

## 4. Process lessons
- Cost model (0079): cache reads 95% of tokens but ~46% of dollars; cache writes ~48%; Opus 68% of spend. Rule: keep output out of context; cheapest tier that does it; planner never hands off for cost (0083: audit of 10 hand-offs saved $2-4 per 100 steps vs $1.1-2.6 re-orientation; parallelism worth more). Cache lapses: 502 in a week, $0.75 each at 150k Opus -> wait in <270 s calls.
- Cost per session rose ~13x after delegation controls (instruction-and-agent-tree-review-2026-10-14.md section 1); cost unit then did not weight by model (tuned blind); 984-turn Helstrom session; 75 lead launches in a week -> lead tier removed (0079). Conflicts between rules ("C1-C9") each a coin-flip for agents; fixed by single recipe and `test_word_budget.py` gating CLAUDE.md size.
- Chunk to one context (0118): hand-off marker 300k (100k Haiku); session cost grows with square of length.
- Testing ladder (0156, loops.md): 1 data, 2 still, 3 motion, 4 headless staged script on both runners, 5 filmed pod strip only with a reason, 6 owner playing deployed build. Journeys are staged scenes (0155).
- One gate (0131): `npm run check` <= 3 min wall, 4 GiB; regen.py --check for generated artefacts (stale generated data was the commonest red); gate earns place by catches per second; made to fail on purpose first. Review triggered by size > 1,500 changed lines (owner amendment 2026-10-20).
- Fix-forward deploy (0154): build gates Pages deploy only; CI checks run beside and post a signal; owner walks only the deployed build.
- Measure-diagnose-fix loops (loops.md): survey everything, diagnose all, fix batch, re-measure; "one finding at a time is the anti-pattern".
- Owner-as-visual-authority: agents measure; owner walks; walk packets posted to GitHub issues; 0102: nothing measurable goes to the owner.
- What worked: de-risk order (0134), frozen base + layers (0059/0140), records as one normalised set (0104), gates incremental by record id, owner steers recorded verbatim in decisions, hooks enforcing rules (shell_guard, agent_guard).
- What didn't: large autonomous swarms on one problem (Helstrom), eyes-loops on expensive harness, GPU-less dev (needs RunPod and SwiftShader fallback; 0119), estimates of phone fps from pod ratios (non-linear by ~35%, cut-3ms report), cost accounting blind to model price, rules accreting in CLAUDE.md.
- Infra: dev box is EC2 m7i.2xlarge no GPU (gpu-dev-machine-cost-analysis.md); GPU options analysed (g4dn $0.75/h ... Mac minis); RunPod chosen, $15/month cap (later lifted to price-first, no time cap 0119 item 9). Metal-specific bugs only reproduce on Apple hardware (ANGLE/Metal multi-draw expansion, perf round 12).

## 5. Observations relevant to an OpenMW rebuild (for caller's judgement)
- Content that is engine-neutral and already data: 827 catalogue records, place/socket records, 782 NPCs with dialogue, quests as data (0153), stats tables and compile (0144), hydrology/terrain heightfield.
- Engine-coupled: the whole renderer/streaming/LOD architecture (0075, 0082, 0084, 0108, 0120), kit pipeline from Skyrim NIF to GLB, Rapier, UI (React).
- Owner wants "Skyrim-shaped" ambient systems on Morrowind-shaped mechanics; OpenMW already provides cell streaming, dialogue/topic system, barter, skills, magic, Lua API; but no BotW climbing, Souls combat, sailing, 3D swim (OpenMW has swim), fixed-danger rework would be Lua/engine work.
- The assets are Skyrim's (NIF in OpenMW supports Skyrim NIF only partially; check); the owner has already built an asset pipeline from Skyrim data (tooling/asset-pipeline).
- Owner requirement of runnable-in-browser/phone native-res 60 fps conflicts with a streamed-GPU model unless latency accepted; phone use-case is central (Honor Magic V5, folded viewport touch controls).

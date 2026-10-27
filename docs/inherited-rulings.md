# Rulings inherited from elder-souls-argonia

Every decision record of the old project (0001–0159), with what happens to it here. **Carry**: binding here as
written (the old record, imported to `docs/design/old-decisions/`, is the text). **Adapt**: the intent binds;
the mechanism changes because Skyrim is the host (how, in the note). **Drop**: three.js-, browser- or
pipeline-specific; does not apply. Owner rulings inside old records keep their authority unless this project's
decisions or a later owner ruling change them. A row's verdict changes only by a decision record here.

| Old | Title (short) | Verdict | Note |
|---|---|---|---|
| 0001 | migration sources and asset vault | Adapt | R2 vault used for the heightfield and metadata only (0009) |
| 0002 | era policy and source confidence | Carry | 4E 201; lore dossiers first, UESP next, fan material a prior |
| 0003 | coordinates and units | Adapt | metres in data; Skyrim units only in the units module |
| 0004 | fixed difficulty is architectural | Carry | C14 |
| 0005, 0006 | heightfield ingest, provisional scale | Drop | superseded in the old repo; frozen output used |
| 0007 | deep-marsh access progression | Carry | capability-gated access (swim, boats, resist gear) |
| 0008 | reference watershed | Drop | world-build process |
| 0009, 0010 | quest/world plans modularised | Drop | process |
| 0011 | ground material system | Adapt | land-cover classes → LTEX (P3-WP3.1) |
| 0012 | portage resolution | Carry | routes data |
| 0013, 0014 | package shape, browser chunk encoding | Drop | three.js |
| 0015 | province ×1 scale, mountain drama in data | Carry | frozen heightfield |
| 0016 | natural light and world time | Adapt | Skyrim weather/image spaces (P3-WP3.5, P8-WP8.6) |
| 0017, 0020, 0021 | sandbox parity, light implementation | Drop | three.js |
| 0018 | cast, lore, delivery tiers | Carry | quest delivery tiers |
| 0019 | stats workstream | Drop | process (design carried via 0033/0035/0037) |
| 0022 | world build gap audit | Drop | process |
| 0023, 0024 | soundscape polish, credits consolidation | Adapt | credits rule carried (sourcing register); audio replaced (P8) |
| 0025 | water rendering shape | Drop | three.js |
| 0026 | main quest sharpened | Carry | 23–24 core quests, three endings, no boat chases |
| 0027 | Morrowind density | Carry | P9 targets |
| 0028 | allegiance reward tracks, quest index, novelty rule | Carry | |
| 0029 | forward research pack | Drop | process |
| 0030 | quest tiers, locks, swimming | Carry | tier protection |
| 0031 | stats round 1 (vastei, respawn on rest; cut whips, crossbows, throwing) | Carry / Adapt | C3 carries; the crossbow/thrown cut is reversed by 0016 (owner, 2026-10-27); whips stay cut |
| 0032 | weather and atmosphere | Adapt | Skyrim weather + Community Shaders |
| 0033 | stat design, numbers, balance harness | Carry | numbers; the harness logic ported to L2 tests |
| 0034 | build sequence (superseded) | Drop | |
| 0035 | attributes and pace | Carry | |
| 0036 | vegetation placement | Adapt | REFR scatter + grass (P3-WP3.7) |
| 0037 | stat QA rulings (DS1 poise, no practice discount) | Carry | poise numbers now measured from DSR (0004) |
| 0038 | package rule (superseded) | Drop | |
| 0039 | source-game crosscheck triage (no survival, no bleedout) | Carry | |
| 0040 | animation packs and combat rules they carry | Adapt | Skyrim movesets as dependencies; no FromSoft rips (0004) |
| 0041 | settlements and places | Carry | |
| 0042 | build-out steers (cuts: mounts, fire spread, tide gating, river pirates, drifting settlements; Hist powers kept; engineering standards) | Carry / Adapt | cuts and Hist powers carry; engineering standards replaced by ways-of-working |
| 0043 | text quality workstream | Carry | style guide, linter, reviewer |
| 0044 | world registries framework | Carry | |
| 0045–0050 | water overhauls, water physical model, vegetation ladder, water season, hammock class | Adapt / Drop | the measured water record carries; seasonal water dropped (static planes, P3-WP3.3) |
| 0051 | route span systems | Carry | as data |
| 0052, 0053 | bundle runtime contract, suppression register | Drop | three.js pipeline |
| 0054 | sex is an axis | Carry | |
| 0055, 0056 | collars, armour blended to the wearer | Drop | Skyrim armour meshes fit natively |
| 0057–0066 | terrain once, water once, rivers graded, waterfalls vanilla kit, signed record read downstream | Carry (as data) / Adapt | 0064 waterfalls are the vanilla kit carries directly |
| 0067 | apron is the Tamriel map 1:1 | Adapt | apron cells + LOD (P3-WP3.2) |
| 0068, 0069 | roads on frozen ground; six legs and two exits | Carry | |
| 0070 | vegetation reads the record | Carry | |
| 0071–0073, 0075, 0082, 0084, 0108, 0120, 0122 | quality bands, ring fade, cards, LOD ladder, vegetation cells, triangle budget, performance architecture, kit streaming, WebGPU | Drop | three.js; Skyrim's LOD and our frame-time bar replace them |
| 0074, 0076, 0077 | weapons lane rounds (Animated Armoury movesets, Skyrim-calibrated tables) | Adapt | tables inform item import; movesets as dependencies |
| 0078 | places adapt to the frozen world | Carry | |
| 0079 | cheap hands, expensive head | Carry | ways-of-working |
| 0080 | chain runs by dependency | Carry | phases by dependency |
| 0081 | doors are transitions | Carry | load doors |
| 0083 | planners never hand off for cost | Carry | |
| 0085, 0086 | kit truth mined from placement evidence; kit skills | Adapt | "read what goes with what from plugin data" carries; kit skills not copied |
| 0087 | Opus decides when delegated (superseded in part) | Drop | |
| 0088, 0089 | stats model and combat runtime as packages | Adapt | ArgoniaCore/ArgoniaCombat with a pure core library |
| 0090 | arrow damage calibrated to the band ladder | Carry | |
| 0091 | off hand holds shield, weapon or light | Carry | native |
| 0092 | stealth is a detection service | Adapt | Skyrim detection tuned (P4-WP4.17) |
| 0093 | swimming behind the controller boundary | Adapt | Skyrim swim + Underwater NG |
| 0094, 0095 | audio as Opus/WebM; injected audio manager | Drop | Skyrim audio |
| 0096 | one race record with Morrowind's packages | Carry | |
| 0097 | placement workbench | Drop | |
| 0098 | variety measured per settlement; owner permission covers the collection | Adapt | variety carries; permissions are now asked per author (0003, O-5) |
| 0099, 0100 | places built in a loop until the skill is proven; accepted place frozen | Carry | world-builder skill |
| 0101, 0102 | building pads; a place carries its own ground | Carry | |
| 0103 | tier A interiors; every promise a placed socket | Carry | every building enterable |
| 0104 | the world is one normalised record set | Carry | |
| 0105, 0109, 0113, 0123, 0125–0127, 0129, 0130 | setting class/doors/lights band, interior additions, socket interact point, interior lighting, mound op, scene states, interior claims, walk-12 contracts, one collider per placement | Adapt | intents carry where they describe the world; three.js mechanisms drop |
| 0106 | how we work | Carry (as amended by 0131) | |
| 0107 | config-driven fire system | Adapt | Skyrim fire effects |
| 0110–0112 | (not in the index) | — | numbers unused in the old repo |
| 0114 | plugin data is the interior manifest | Carry | native in Skyrim |
| 0115 | route compile builds no crossings | Carry | |
| 0116, 0117 | the record is the built place; coherence gate | Carry | data checks in the gate |
| 0118 | one context per brief | Carry | |
| 0119 | RunPod is the GPU lane | Adapt | AWS GPU box (0008); "price first, delete/stop when done" carries |
| 0121 | WebGPU second build (superseded) | Drop | |
| 0124 | mist volumes raymarched | Adapt | Community Shaders fog + emitters |
| 0128 | places edited in place, never rebuilt | Carry | |
| 0131 | one check gate | Carry | |
| 0132, 0133 | city build methodology; cities hand-built | Carry | one builder per district |
| 0134 | four parts, de-risk first | Adapt | this plan's phases; "systems whole, content thin" carries |
| 0135 | phase 16 closes | Drop | |
| 0136 | haze by default | Carry | P8-WP8.6 |
| 0137 | directions, not markers | Carry | C7 |
| 0138 | lamp clock; no followers; nobody unkillable | Carry | |
| 0139 | facts once, opinions each | Carry | |
| 0140 | layers on a built place never rebuild it | Carry | |
| 0141 | one price contract | Carry | |
| 0142 | combat everywhere: hostile places, roaming bands, answered violence | Carry | |
| 0143 | anyone may explain; restatement near-verbatim | Carry | |
| 0144 | progression ships whole; rest the only save | Carry | |
| 0145 | disposition changes the talk | Carry | |
| 0146 | magic ships whole: Skyrim hands | Carry | |
| 0147 | early levels fast | Carry | |
| 0148 | spell sellers carry a sheet | Carry | |
| 0149 | the studio plays the game: no modes/flags for game actions | Carry | test the shipped path |
| 0150 | crafting ships whole | Carry | |
| 0151 | stealth, crime and locks whole; the Owing | Carry | |
| 0152 | province-wide climbing from FreeClimb's clips; swim closed; ladders; water stealth | Adapt | FreeClimb runs natively as a dependency; licence-reading waiver ("private, undistributed") **does not carry**: permissions are asked (0003) |
| 0153 | quests as data | Carry | |
| 0154 | only the build gates deploys | Adapt | release artifacts gated by the build and the no-assets guard |
| 0155 | journeys are staged scenes | Carry | in-game scenarios |
| 0156 | test each block at its cheapest level | Carry | levels L1–L6 |
| 0157 | the marsh does what the loading facts say | Carry | |
| 0158, 0159 | boats whole; Wind Waker sailing, dugout and sea hull first | Carry | P6 |

The old `CLAUDE.md` rules "we never make art (UI excepted)" and "take assets, never Papyrus or SKSE code" are
**adapted**: art stays sourced except UI and minor Fal-made 2D elements (0006); Papyrus and SKSE code from
open-licence mods may be used or forked under their licences (0010), because Skyrim is now the host.

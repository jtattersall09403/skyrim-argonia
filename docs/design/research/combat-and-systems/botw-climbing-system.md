<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/botw-climbing-system.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# BotW climbing, as a rule set for Argonia (2.12a, 2026-10-14)

Answers [2.12 § a](../../phases/2-slice/2.12-swim-and-climb.md). One line per
rule: a number or a rule, then its source. Tags: **[C]** Cantão's UE
recreation (vitorcantao.com/post/climbing-system; its numbers are *his
defaults in UE cm*, not Nintendo's); **[D]** the zeldaret/botw decompilation
(`src/Game/Actor/Player/…`, names only, no values); **[W]** a BotW/TotK wiki
or guide claim seen in a search result (Fandom 402, Zelda Dungeon 403 and
Nexus 403 blocked page fetches, so these are secondary); **[R]** recorded
play behaviour, unsourced; **[76]** `docs/world/76-stats-progression.md`;
**[OURS]** a decision made here, tunable, to be proved in the micro-lab.
BotW's real internal numbers are not published anywhere reachable; where no
number exists the line says so and gives ours.

## 0. Reconciliation block

| Live doc | Claim | Verdict |
|---|---|---|
| [swim-climb-boat-implementation.md](swim-climb-boat-implementation.md) §4.1-4.3, §5, Open Qs 5/6/8 | Cantão's sweep/attach/stick/tangent-basis/top-out/dash design; Rapier `castShape`/`castRayAndGetNormal`/`projectPoint`; kinematic mode; CCDIK + analytic two-bone IK; wet grip "degrade, don't deny" | **Confirmed and reused, not repeated.** §9 resolves Q5 (kinematic, local-space contact), §7 Q6 (degrade + slip event), §10 Q8 (ladder one-shots cannot carry lateral movement) |
| [world/90 §74.3](../../world/90-asset-strategy.md) (line 352 ff.) | "EVG ladder loops = primary BotW wall-climb candidate"; "vanilla has no climbing animation" | **Partly contradicted.** EVG's ladders are timed one-shots (Short Ladder 5 s), not shown as loops; see §10. Vanilla Skyrim ladders are load doors, no motion (§10). Edit 90 §74.3 |
| [world/60 §43, §46](../../world/60-water-traversal.md) (lines 198-223, 352-376) | `ClimbSurfaceProfile{material,climbable,grip,wetGripMultiplier,requiredAbility,exclusionReason}`; corridors, ledges, top-out clearance, camera clearance, alternate routes | **Confirmed.** This doc fills the field values (§3) and adds the traction link to `WeatherContact.grip` (`packages/contracts/src/index.ts:459`) |
| [world/76 §122.1](../../world/76-stats-progression.md) (lines 1001-1040) + `stats/data/curves.json:211-223` + `stats/derived.ts:138-152` | 1.1 m/s, 7.5 stamina/s, mantle 18, ledge grab 8, hold regen 12 %, burden drain 0.85/1.0/1.35, wall tiers 10/25/40 m, Acrobatics bands | **Confirmed; adopted unchanged.** New costs here (climb leap, shimmy, slip) are additive fields in the same `climbing` block |
| decision 0004 + `0004-fixed-difficulty-constraint.md` | Fixed difficulty; brief says stamina is the only limiter | **Confirmed.** 0004's text names no stamina; it forbids player-level input to world generation. Consequence used: wall height and wetness are world state, never scaled to the player. Stamina (via stats API) is the sole limiter; no breakable-grip or timer limiter |
| `packages/game-core/src/physics/capabilityProfiles.ts:19-40`, `contracts/src/index.ts:495-536` | `climbSpeed` 0; ecctrl default slope 1 rad; `LocomotionMode` already has `"climb"` | **Confirmed.** `maxWalkableSlopeDeg` = 57.3 (1 rad); used as the walk/climb pivot (§1) |

**Edit target:** this file is the one research record; the single live doc to
edit afterwards is `docs/world/90-asset-strategy.md` §74.3 (clip pools, §10
table), already carrying the §10 verdicts. Rules that become code land in `curves.json` `climbing`.

## 1. Gradient thresholds and the band between

- BotW climbs automatically when you run into a steep face; a slope too steep to walk either auto-climbs (ascending) or drops you (descending) [W: Game Developer, "Gravity to go Forward"]. No degree figure is published for BotW [R: search of Zelda Wiki, Game Developer, GameFAQs found none].
- BotW has distinct `Slide`/`SlideLand` and `WallSlip` actions beside `Climb`, `ClimbRest`, `TreeClimb` [D: `Action/` directory listing], so too-steep unclimbable ground slides, it does not hold you.
- Attach needs the facing within 25 deg of the wall normal [C: min 25, max 75 deg in his build]; it is horizontal angle only, from the dot of forward and the horizontally projected normal.
- Walk limit = ecctrl 57.3 deg (`capabilityProfiles.ts:24`). [OURS] Bands, by slope angle of the surface under the contact:
  - 0-45 deg: walk, no change.
  - 45-57.3 deg: walk with strain, speed x(1 - 0.4 x (a-45)/12.3); visual lean only, no stamina.
  - 57.3-70 deg: **scramble**: climbable if the material is, and the climb clips play in the "lean" pose; a non-climbable material here **slides** at 3 m/s down the fall line with steering (no damage, no fall).
  - >=70 deg to the overhang cut-off (§2): full wall climb.
- [OURS] Hysteresis: walk->climb at >= 57.3 deg with forward input within 25 deg of -normal held 0.1 s; climb->walk when the surface under the feet drops to <= 50 deg for 0.2 s (7 deg of hysteresis stops flicker, the Catlike/Cantão failure on bumps).
- On a slope between a climb surface and walkable ground the body keeps the climb pose until the support normal under the feet is walkable, then the capsule snaps upright over 0.25 s [C: transition on "floor within 100 uu below + downward speed >= max/3 (40 cm/s) or surface walkable"].

## 2. What is climbable

- BotW: climb anything except ceilings, the walls of Sheikah shrines and divine beasts (puzzle protection), and surfaces made unclimbable by rain/ice slipping [W: Zelda Wiki "Climbing", GameFAQs "Unable to climb most walls in a shrine"].
- Ceilings and overhangs: Cantão rejects walls "perpendicular to the surface normal" i.e. normal.y ~ 0 only for flat ceilings; BotW lets Link hang under slight overhangs ("past 90 deg his body hangs and his back stiffens") [W: GameFAQs animation comment, anecdotal]. [OURS] climbable if normal.y >= -0.17 (<= 100 deg from the ground plane); steeper = ceiling, rejected (a top-out check from below fails, so the climber stops under it).
- Surface material is data, `ClimbSurfaceProfile.climbable/grip` (world/60 §46). [OURS] defaults (grip 0..1): rock, root, bark, timber, rough stone 1.0; masonry, xanmeer white stone 0.8; wet or algal stone 0.6; thatch 0.7; glass, polished or ice 0 (unclimbable); `exclusionReason` required when `climbable:false` on a surface that looks climbable.
- Minimum size [OURS]: a contiguous patch >= 0.6 m wide x 0.8 m tall of valid normals (hands+feet envelope; Cantão's sweep capsule is 0.5 m radius x 0.72 m half-height). Props whose top is <= 1.2 m high are mantled or vaulted, not climbed; a thin pole (< 0.3 m wide) is climbable only as a **pole/trunk**: wrap-around contact (§8).
- Trees: BotW has a dedicated `TreeClimb` action [D]; trunks are climbed by wrapping, branches are ledges. [OURS] trunk >= 0.3 m radius is a pole; canopy branches count as ledge routes (world/60 §46 "tree branch routes").
- Building walls: climbable by default when the kit piece's collision is a wall and its material is climbable; stilt posts are poles; roofs follow the slope bands. Interiors: not climbable unless a place authors it (BotW's shrine rule). [OURS]
- Placed objects: any collider tagged by the `climbable` collision group (`castShape` filter, existing doc §4.3). Province boundary colliders are never in the group (2.12 brief, Starting state).
- Cliffs: terrain heightfield faces up to ~85 deg; normals per triangle [existing doc §4.3]; overhangs only from placed rock.
- Wet surfaces: §7 (slip). Moving things: [OURS] v1 climbs static colliders only; a climber on a kinematic mover stores the contact in the mover's local space and rides it (boat hull, mooring post: 2.15 reuse; Catlike handles moving walls the same way, existing doc §4.2).

## 3. Starting a climb

- From the ground: forward input into a climb surface, rule in §1; or the `climbHold` action while facing within 25 deg. Cost: 0 on attach. [OURS]
- From a jump: BotW grabs when you jump into a wall [R]. [OURS] while airborne, each frame the chest sweep (r 0.5 m, 1 m ahead) runs; a valid patch plus forward input attaches, no cost; a **ledge** within the hand envelope (lip 1.4-2.2 m above feet) grabs as `ledgeCatch`, cost 8 stamina (`ledgeGrabStaminaCost`, curves.json:215). Mid-air grab is refused within 0.35 m of the ground [SkyParkour changelog: 35 uu].
- From a swim: surface swimmer whose head-height sweep hits a valid face attaches at the waterline (`waterExit`); if the top is <= 1.0 m above the water it mantles straight out, otherwise it climbs from the waterline. Submerged swimmers surface first (no attach below the surface). [OURS]
- From the top of a cliff (climbing down over an edge): [OURS] standing within 0.4 m of an edge with a climbable drop face > 1.5 m, hold toward the edge + `climbHold` 0.3 s: the body turns, lowers into a ledge hang, then wall-climbs down. Cantão's inverse check: floor probe 100 uu below, down speed >= max/3 [C].
- From a ledge hang: up input past 0.2 s = pull to mantle (§5); down input = release and fall; a wall below the hang within hand reach attaches as wall climb. [OURS]
- Re-grab lock after any release: BotW's `PlayerClimb` carries a static `NoClimbTime` [D `aiPlayerClimb.cpp:loadParams_`]; value unpublished. [OURS] 0.35 s; kills the BotW state-cycling exploit (climb/run toggle to refill stamina, Gameranx/Mic write-ups).
- Auto-attach while falling from a climb leap: BotW re-attaches to a nearby surface if stamina runs out mid-jump [W: Kelvaris]. [OURS] yes, once, within the 0.5 m sweep.

## 4. Hang, shimmy, drop, jump, dash, zero stamina

- BotW has `HangWallCatch` (mid-air ledge catch), `WallJump`, `WallDashUp`, `WallSlip`, `ClimbRest` as separate actions [D]; `WallJump` takes `JumpHeight`, `JumpSpeedF`; `WallDashUp` takes `MinSpeedF`/`MaxSpeedF` (a speed ramp), `ClimbRest` has `EnergyClimb` [D]. Values are unpublished.
- Hang: hands on the lip, feet free; no drain while still, 12 % of normal regen (`restOnHoldRegenFraction`, curves.json:222; 76 §122.1). Applies to wall idle too (BotW: pause costs nothing [W: Kelvaris, "standing on ledges pauses the drain"]). [76]
- Shimmy along a ledge: [OURS] 0.55 m/s (0.5 x climb speed), drain 0.6 x base while moving (4.5 /s), stops where the lip ends or a corner is not wrappable (§8).
- Drop (release): `climbRelease` input or `crouch`; the body detaches along -normal x 0.2 m then falls; fall damage by 76 §122 (`safe fall 2 + Acrobatics/25 m`). Re-grab is locked 0.35 s (§3). [OURS]
- Climb leap (BotW "jumping while climbing"; Cantão's "climb dash"): the leap is **one action with a direction**: up (2.0 m gain, 0.75 s), sideways/diagonal (1.5 m, 0.6 s) [OURS magnitudes; BotW's is ~2 m by sight, R]. Cost [OURS]: 25 stamina x Acrobatics band x burden (a quarter of a 100 pool; GameFAQs estimate "~1/3 of a wheel" [W anecdotal], TotK's Climbing Jump Stamina Up halves it [W]). Free of regen while airborne; reattach on landing.
- Cantão dash curve (shape only): launch 0.29 s, peak 950 cm/s at 0.4 s, total 1.15 s, acceleration multiplier = velocity/max (min 1.0), direction projected onto the surface plane so momentum survives corners [C]. Use the shape, not the 9.5 m/s peak.
- Zero stamina: BotW lets go and falls, wheel flashes red first [R]; ladders are free and still climbable slowly at zero [W: Zelda Wiki]. [OURS] below 15 % stamina: the tired climb pose (flag on the speed-0.7 clip variant) and HUD pulse; at 0: release and fall, regen blocked for the `regenDelay` 1.05 s (curves.json:26). Ladders: free, 0.5 x speed at zero.
- Overloaded burden (>= 1.0) cannot start (76 §122.1 "being overloaded means you cannot start"); a tutorial hint is shown, not silent failure.

## 5. Mantle at the top

- Trigger [C]: moving up fast enough, the eye-height ray finds no wall, the surface above is walkable, then a capsule sweep confirms the destination is clear; the montage ends 0.5 s early to blend. Ledge probes: 160 uu up, 120 uu forward, 250 uu down for walkability [C].
- Cost: 18 stamina x Acrobatics band (`mantleStaminaCost`, curves.json:214).
- [OURS] Tiers, by lip height above the feet when triggered: **vault/step** <= 1.0 m (SkyParkour `Vault`/`LowStep`); **low mantle** 1.0-1.5; **mantle** 1.5-2.2 (the climb-top case, hands on the lip); **high pull-up** from a hang with feet free (SkyParkour `ClimbHighest`).
- Sloped top: if the top surface within 0.6 m of the lip is <= 57.3 deg, mantle onto it and stand; steeper (a roof): attach as a wall climb on the roof, not a mantle.
- Cluttered top: the destination capsule sweep (r 0.3, full stance height) must be free; if blocked, shift the landing point up to 0.5 m along the lip, else stay hanging and let the player shimmy. A blocked mantle is reported as a hint, never a silent stall.
- Too narrow to stand: support disc (landing point +- foot length) needs >= 0.6 x capsule radius of valid ground; narrower = no mantle; the climber may use the top as a hang point. [OURS]
- The top-out also fires for branch ledges and for rope/ladder tops via the same probe.

## 6. Stamina costs and modifiers (through the stats API)

Base set is 76 §122.1; the new rows extend `curves.json` `climbing` (one block, same data file, per standard 18):

| Action | Cost | Source |
|---|---|---|
| Climb moving | 7.5 /s x climbStamina band (1.25->0.75) x burden (0.85/1.0/1.35) | 76 §122.1, `derived.ts:142-144` |
| Climb still | 0, regen at 12 % | 76 §122.1 |
| Ledge grab (mid-air) | 8 | curves.json:215 |
| Mantle | 18 x band | curves.json:214 |
| Climb leap | 25 x band x burden | [OURS] (`climbLeapStaminaCost`) |
| Shimmy | 4.5 /s | [OURS] |
| Wet drain multiplier | 1 + 1.5 x (1 - grip) up to 2.5 | [OURS], §7 |
| Ladder | 0 | [W] |
| Water exit mantle | 12 | [OURS] |

- Weight: burden tier multiplies drain (0.85/1.0/1.35) and overloaded blocks the start (76 §122). Gear: BotW's Climbing Set gives +20/25/30 % climb speed for 1/2/3 pieces and no stamina saving [W: Zelda Wiki "Climbing Gear"; existing doc §4.1]; TotK adds leap-cost reduction (halved at full set) and Slip Resistance [W]. [OURS] gear and effects set three named climb modifiers via `modifiers.ts`: `climbSpeedMul`, `climbDrainMul`, `gripBonus` (+0..0.3 to grip). No new stat; skills (Acrobatics `climbSpeed`/`climbStamina` bands, skills.json:266-270) are already the base.
- Food/potion analogues: a timed effect writes the same three modifiers (BotW food: temporary extra wheels from endura items [W: Kelvaris]; ours: `maxStamina` temporary boost via the effect system). No second stamina bar (decision 0031).
- Drain is world-fixed (0004): the same wall costs the same on the same character; no auto-scaling.
- Argonian: no canonical climbing trait. Any claw-grip bonus would be fan-prior design; flagged as an owner call, not adopted.

## 7. Wet surfaces and rain

- BotW: rain makes Link slip off wet walls periodically (about every four moves; players "climb 4, jump"), unaffected by food; TotK shipped Slip Resistance after the mechanic was the most disliked [existing doc §4.1; W: Zelda Dungeon]. TotK base slip while climbing in rain: one every 6 s, Froggy set level 3 makes it rare [W: hardcoregamer].
- [OURS] Degrade, don't deny. Effective grip = `surface.grip x wetGripMultiplier(wetness) x (1 + gripBonus)`; `WeatherContact.grip` (contracts:459) is the dry/wet traction term. Drain multiplier per §6. A **slip event** only when effective grip < 0.5: the climber slides down 0.6 m over 0.5 s (a `slip` clip), at most once per 6 s, interruptible by a leap (counter-play) or a hold press; never a fall by itself. Holding still on a wet wall costs 0 as dry.
- Wet-grip knobs live in `ClimbSurfaceProfile.wetGripMultiplier` (world/60 §46). Black Marsh is damp often, so defaults keep grip >= 0.6 on algal stone and bark in rain (so wet routes cost more, not close).

## 8. Camera

- BotW: the climb camera pulls back, frames the wall, and recentres behind the facing; the player sees only the wall, less information [W: Game Developer]. No published numbers.
- [OURS] Wall yaw target = -normal (projected), recentre only after 1.5 s without look input, rate 90 deg/s max (the follow-camera rule: return gradually, on input; follow-camera-collision.md, TotK). Distance +0.5 m, pitch bias +10 deg (to 25 deg) so the route above is visible.
- Walls facing away / overhangs: camera cannot sit inside geometry: sphere sweep (near-plane half-diagonal) pulls in; player model blends out under 0.4 m (follow-camera-collision.md, Skyrim).
- Inside corner: target yaw interpolates to the new wall over 0.25 s after the contact switches. Outside corner: hold yaw until the wrap completes, then interpolate; never swing more than 90 deg in 0.25 s.
- Mantle: camera follows the root with 0.25 s lag, no recentre until the climber stands.

## 9. Staying on the real surface

Reuses existing doc §4.2/§5 (sweep, centroid + summed normal, secondary sphere-casts, spring to standoff, tangent basis, per-limb traces). New rules:

- Standoff 0.45 m from the surface (Cantão 45 uu) spring-driven at snap 4 uu/frame; rotation lerp rate 6 /s; collision shrinks by 0.3 m while climbing [C]. The standoff is a **clip property**: the micro-lab measures each sourced clip's hand-to-chest distance and sets standoff per clip, so no arm clips through the mesh.
- Probes per frame: chest capsule sweep (r 0.5, half-height 0.72, start 0.2 m ahead); assist sphere casts r 0.06 m, 1.2 m, per hit; eye-height ray base 0.8 m x (1 + (1 - steepness) x 5) [C].
- Hand targets: two rays along -normal from shoulder height, +-0.22 m lateral, 0.6 m long; feet: two rays from hip -0.55 m, +-0.15 m lateral. Each limb target = ray hit + 0.02 m; IK blend weight 0 when the ray misses (the clip plays unmodified), 1 within 0.1 m of the clip's own pose; analytic two-bone IK (existing doc §5; our sandbox foot-planting is the same family). [OURS]
- Cadence: playback speed = actual climb speed / clip's authored speed (the stride calibration in 90 §74.3).
- Inside corner (wall meets wall, concave): the sweep sums two normals; when the forward probe hits a second face within 0.45 m with angle >= 30 deg between normals, the contact switches to it and the body rotates at the lerp rate. Outside corner (convex edge): when lateral input finds no surface, probe a 0.6 m arc around the edge (up to 120 deg turn); found = wrap (pole/trunk/corner), else shimmy ends. Both [Catlike Coding, cited in existing doc §4.2]; thresholds [OURS].
- Transitions between pieces of different normals: the normal is low-passed (rate 6 /s) and clamped to a 60 deg change per 0.25 s; a larger jump (kit seam) is treated as a corner. Never ride a bounding box: contact comes from the render-matching collision mesh (2.12 goal), and the ray hit's triangle normal is the truth.
- Mode: kinematic body (`setNextKinematicTranslation`); friction 0 [C]; resolves existing Open Q5 (moving mounts handled by local-space contact, §2).

## 10. Mod scene audit (world/90 §74.3)

Verified through the Nexus API (FreeClimb, SkyClimb, SkyParkour) and Nexus search snippets, Fandom and Gamesradar summaries for the rest. Licence reading is waived for the private build ([0152](../../old-decisions/0152-climbing-is-a-province-wide-system-swim-is-closed-ladders-and-water-stealth-join.md) §2); credits still land with every download.

| Source | Supplies (motion -> use) | Misses | Evidence |
|---|---|---|---|
| EVG Animated Traversal 63232 (Everglaid, v2.1) | Ledge (2.5 s) and Medium Ledge (2.25 s): mantle; Ledge Catch (1.5 s): mid-air grab; Failed Ledge: slip/fail; Wall Drops: drop; LadderSlide; Short Ladder (5 s) and Tall Ladder: ladder up; Vault 2.2 s, Raider Roll, Duck, Squeeze (2.5 s shimmy-through), Deep Walk | No continuous wall loop, no lateral/down loop, no hang idle, no shimmy along a ledge. Ladders are **timed one-shots** by the summary, not loops: the 90 §74.3 "ladder loop = wall climb cycle" claim is **unverified and doubtful** | Nexus 63232 summary; Schaken-Mods |
| SkyParkour v3 (JellyFishInLoop clips, built in; mod 132292, modder article 10726) | Root-motion one-shots: ClimbLow/Medium/High/Highest (mantle tiers), High/Low Step, Vault, Grab (ledge catch), Fail, midair grab, water exit, crouch slide | No wall-climb loop; no hang idle or shimmy; no climb-down | Nexus 132292, 10726 (graph var `SkyParkourLedge` 8..0 = highest..fail) |
| SkyClimb 97253 | Code only (SKSE, procedural ledge check); uses EVGAT clips. Design reference only (90 §74.3 rule) | no clips of its own | Nexus 97253 |
| Dynamic EVGAT SkyClimb and Parkour animations 109022 | OAR variants (sneak-level conditioned) of the same clips; more permissive licence per summary | same gaps | Nexus 109022 |
| EVGAT Dynamic Climb-able Ladder Doors 108900 | Ladder script via Base Object Swapper; code; climb-down ladder removed in latest changelog | no clips | Nexus 108900 |
| EVG CLAMBER 114753 (Everglaid, miken1ke, Ersh) | Slope walk/run: effort steps from ~45 deg, near-slide with braced arm at 60 deg+ downward: **the 45-70 deg scramble band and the slide** | no vertical climb | Nexus 114753 |
| Simply Climb / V2 26488, 170550 | Nothing: mechanic with no animation, character floats | everything | Nexus pages |
| Vanilla Skyrim | Jump, fall/land, swim, sneak. **No ladder, no mantle**: ladders are load doors, instant, no animation | all climbing | GameFAQs "Will this game have climbable ladders"; Gamesradar; Nexus 108900 comments |
| FreeClimb 193552 (Epsilona11, v0.5.0) | Wall climb up, down, left and right loops with corners, hang idle, leap catches up and sideways, drop, release, re-grab, mantle. Also wall running and overhang traversal, not used per [0152](../../old-decisions/0152-climbing-is-a-province-wide-system-swim-is-closed-ladders-and-water-stealth-join.md). Form: loose HKX played by an SKSE DLL; Mixamo and Threepeat content on the Skyrim rig; code GPL-3.0, none taken | Ladder loop, mount and dismount, tired, slip | Nexus 193552 (API read) |
| Wall climb loop, lateral loop, hang idle, climb-down, leap catches, drop, re-grab | **Found in FreeClimb** (row above) | | Nexus 193552 |
| Ladder loop with mount and dismount | **Not found in any mod**: EVGAT ladders are timed one-shots, the ladder-door addon has no clips | | search sweep; Nexus 63232, 108900 |

Consequence: the continuous set (wall up, down, left and right with corners, hang, leap catches, drop, re-grab, mantle) comes from FreeClimb. The one-shots (mantle tiers, ledge catch, slip, water exit, ladder mount and dismount) come from EVGAT and SkyParkour; the scramble from CLAMBER. The ladder loop is FreeClimb's climb loops retimed to a rung pitch with EVGAT mount and dismount, never a one-shot cut into a loop. The walk, scramble and climb rule generalises province-wide in 2.12 a2.

## 11. OUR rule set (summary of adopted rules)

1. Climb mode is `LocomotionMode "climb"` behind `PlayerMovementController`, kinematic, local-space contact on movers. (§2, §9)
2. Walk <= 57.3 deg; scramble 57.3-70; wall 70 to normal.y >= -0.17; steeper rejected. Hysteresis 7 deg, dwell 0.1/0.2 s. (§1)
3. Attach: facing within 25 deg, patch >= 0.6 x 0.8 m, collision group `climbable`, material `climbable:true`, never boundary colliders. (§2)
4. Entries: ground, jump (ledge catch 8), swim/waterExit, cliff-top climb-down (0.3 s hold), ledge hang. Re-grab lock 0.35 s. (§3)
5. Stamina: all through `curves.json climbing` + Acrobatics bands + burden; still = free with 12 % regen; leap 25; shimmy 4.5/s; mantle 18; zero = release; ladders free. (§4, §6)
6. Wet: degrade drain by grip, slip event only below grip 0.5, max once per 6 s, leap cancels. (§7)
7. Mantle by lip height tiers, destination sweep, narrow-top refusal and clutter shift. (§5)
8. Camera: wall-yaw target, 1.5 s idle recentre, +0.5 m, pull-in sweep, corner yaw limit. (§8)
9. Surface following: standoff per clip, four limb rays + two-bone IK, normal low-pass, corner wrap. (§9)
10. Every rule maps to a `visual:check` scenario or unit test (acceptance): see the test column in §12.
11. Province-wide: one predicate over a hit (exclusions, solid size, bands, material grip, tops, transitions) with the survey columns and tunables: §11a.

## 11a. What is climbable, province-wide (2.12 a2)

One predicate, `climbable(hit)`, over a ray or sweep hit (collider, triangle
normal `n`, world point) plus a local probe; no per-place data, no labels or
filenames ([0152](../../old-decisions/0152-climbing-is-a-province-wide-system-swim-is-closed-ladders-and-water-stealth-join.md) §1).
It extends §1, §2 and §5 and governs where they differ. Slope angle
`a = acos(n.y)` in degrees. Each rule names its test: U unit test on the
predicate, S survey column, V `visual:check` scenario.

### 11a.1 Order of evaluation

`climbable(hit) = !excluded(hit) && solidEnough(hit) && band(a) in {scramble, wall} && grip(material(hit), wetness) > 0`.
The first failing clause is the verdict's reason (one enum, counted by the
survey): `excluded:<why>`, `tooThin`, `tooSmall`, `walk`, `ceiling`, `noGrip`.
A scramble-band hit with `noGrip` is a `slide` (§1), not a refusal.

### 11a.2 Exclusions (checked first, cheapest)

| # | Predicate | Source | Test |
|---|---|---|---|
| X1 | province boundary bodies (`game-core/src/boundary/BoundaryWalls.tsx:26` creates them with no tag or group): they get a `NOT_CLIMBABLE` collision-group bit beside the camera bits (`camera/cameraCollision.ts:22-36`) and the climb sweep's filter excludes it | brief Starting state; BotW's shrine and divine-beast walls are the analogue [W] | U; S accepted count 0 |
| X2 | no solid: asset `collision == "none"` (846 of 3,239 kit rows in 174 published `*.kit.json`), or category in the foliage set (`grass`, `shrub`, `plant`, `aquatic-plant`): cards and groundcover carry no collider | `build_kit.py:1009-1015` (tiered collision, module 65 §111) [OURS] | S |
| X3 | the water surface: the water plane is no collider; a hit below the local water height is refused unless the climber is a surface swimmer, who attaches at the waterline (§3 waterExit) | §3 [OURS] | U; V water exit |
| X4 | animated or dynamic bodies: rigid body not `fixed` and not a registered kinematic mount (doors, traps, creatures, havok-simulated clutter; categories `door`, `trap`, `creature`, `effect`, `weapon`, `armour`, `ammo`, `marker`) | BotW climbs static geometry and its designed platforms [R]; §2 [OURS] | U |
| X5 | kinematic mounts (hulls, moored boats) are **included**; contact in the mount's local space | §2, §9 [OURS]; 2.15 | V hull |
| X6 | interior cells: excluded unless the cell's record marks a climb route | BotW shrine rule [W]; §2 [OURS] | S |
| X7 | a ladder collider routes to ladder mode (§12 row 32), never a wall climb | brief § b [OURS] | V ladder |

### 11a.3 Solid size: the floor below which nothing is a climb

Local probe at the hit: a 9 x 9 grid of rays along `-n` over a 0.8 m wide x
1.0 m tall window centred on the hit; a ray is valid when it hits the same
collider within 0.15 m of the hit plane with a normal within 30 deg of `n`.

The probe asks the merged collision world: each ray stops at the first thing it
meets, terrain and neighbours included. The patch measured is the solid you grip,
its faces the hands can reach. A face buried in the ground, or hidden behind a
neighbour (a candle inside a hut, a crane inside a barge), is not a hold. Measured
over the hit collider alone, the rule accepted 361 samples the world refused and
refused 62 it accepted, nearly all wall feet under terrain and pieces overlapping
their assembly. [OURS]

A narrow column (a pole candidate) runs along the pole's axis, not the hit normal
from a fixed plane: each ray starts at the standoff point, aims flat at the axis (the
hit pulled back by the pole radius, as the climb runtime aims a held pole) and
re-takes the axis from the point it strikes, so a leaning trunk keeps its full
`columnAboveM` run. [OURS]

| # | Rule | Numbers | Source | Test |
|---|---|---|---|---|
| Z1 | **wall patch**: valid footprint >= 0.6 m wide x 0.8 m tall | hands-and-feet envelope; Cantão sweep r 0.5, half-height 0.72 m | §2 [OURS], [C] | U, S |
| Z2 | **pole**: narrower than Z1 but a convex column of radius 0.15-0.6 m, >= 2.0 m tall; climbed by wrap (§12 row 31). Radius from `collisionCapsule.radiusM` / `collisionSegments[].radiusM` where the kit row has them (49 `trunk-capsule` rows, e.g. `bmv:landscape/trees/dwarfjunip05` r 0.381 m), else an arc fit of the probe | BotW `TreeClimb` [D] | U, S |
| Z3 | **too thin**: column radius < 0.15 m (sapling, rail, slat, rope post) or patch < 0.3 m wide: `tooThin`; vaulted if its top is <= 1.0 m | hand rays +-0.22 m (§9) [OURS] | U, S |
| Z4 | **too short**: top <= 1.2 m above the climber's ground: vault or mantle, never a climb (`tooSmall`) | §2 [OURS] | U; V mantle sweep |
| Z5 | top 1.2-2.2 m: taken by the §5 mantle tiers from the ground; attach only when the lip is above 2.2 m | §5 [OURS] | U |

### 11a.4 Slope bands (triangle normal under the contact)

| Band | Range | Behaviour | Source | Test |
|---|---|---|---|---|
| walk | `a < 45` | unchanged | ecctrl | U |
| strain | `45 <= a < 57.3` | speed x(1 - 0.4 x (a-45)/12.3), lean only | §1 [OURS] | U |
| scramble | `57.3 <= a < 70` | grip > 0: scramble clips; else slide 3 m/s down the fall line, steerable | ecctrl 1 rad (`capabilityProfiles.ts:37`); [OURS] | U; V slope |
| wall | `70 <= a <= 100` (`n.y >= -0.17`) | full climb | BotW hangs under slight overhangs [W]; [OURS] | U; V cliff |
| ceiling | `a > 100` | refused; the climber stops beneath | BotW: no ceilings [W] | U |

Hysteresis per §1 (in at 57.3 deg after 0.1 s, out at <= 50 deg for 0.2 s).
Terrain heightfield triangles are classed the same way (faces reach ~85 deg;
overhangs only from placed rock).

### 11a.5 Surface classes, grip and wet grip

What the data carries today:

- Vocabulary: 14 ids in `contracts/src/physicalMaterial.ts:23-25` (`soil peat mud wood bark bone stone metal ceramic foliage water flesh glass fungus`), one record each in `world/sources/registries/physical-materials.json` (ids at lines 7-345), each carrying only `projectileResponse`: no grip yet.
- A collider's material is `userData.physicalMaterial` on its body or an ancestor (`game-core/src/combat/arrows/surfaceResponse.ts:116-130`); untagged falls to `soil` (`:50`). Only sandbox fixtures set it (`apps/combat-sandbox/src/components/Arena.tsx:208`, `ArrowMaterialTargets.tsx:65,76`).
- **No published kit row carries a material.** Across the 174 kit manifests (3,239 rows) the keys are geometry, textures, render materials, placement and collision kind (`mesh` 1,393, `none` 846, `convex` 784, `box` 167, `trunk-capsule` 49). The NIF's Havok shape material is not read: `nifCollision` is only a boolean (268 rows) and `pipeline/nif_blocks.py` parses render blocks.
- Terrain: each ground-material id maps to a footstep family (`audio/src/surfaces.ts:59`) and on to a physical id (`game-core/src/perception/noise.ts:62-72`: stone, soil, mud, wood, foliage, water).

The classifier's material, in order: (1) the body's `physicalMaterial` tag;
(2) for kit pieces a **new kit-row field `physicalMaterial`** written by
`build_kit` from the source NIF's Havok shape material (Skyrim's `SKY_HAV_MAT_*`
values, plugin data, never a filename), mapped once to our ids in a registry
table, and set on each settlement body at load (a composite whose larger
parts name no Havok material takes none from a minor part: a hull under a
stone-named door is unanswered, [OURS]); (3) terrain through the
footstep mapping; (4) else the category fallback in the table, counted as
`materialFromCategory` so its shrinkage is measured. The pipeline lane
confirms the Havok enum values on vault NIFs before the mapping lands.

Effective grip = `grip x wetGripMultiplier ^ wetness x (1 + gripBonus)`,
`wetness` from `WeatherContact.wetness` (`contracts/src/index.ts:453-466`).

| Class | Material id | How the data tells it | grip | wet mult. | Source |
|---|---|---|---|---|---|
| stone (rock, cliff, rough masonry) | `stone` | Havok stone family; terrain stone/gravel; fallback categories `rock`, `ruin`, `dungeon-kit`, `terrain-feature` | 1.0 | 0.6 | §2 [OURS]; BotW rain slip [W] |
| stone, dressed (xanmeer, plaster) | `stone` | **not separable by material** (both Havok stone): told by planarity in the probe window, >= 90 % of valid rays on one plane within 5 deg; only on a built stone kit solid, never terrain, a moored hull (`kinematicMount`), a `boat`/`vehicle` row or natural stone (`rock`, `terrain-feature`): dressing is masonry work | 0.8 | 0.6 | §2 [OURS] |
| bark (trunks) | `bark` | Havok wood on `tree` / `root` / `deadfall` rows, or on a model the plugin files as a TREE record (registry `recordTypes`; Hist and kapok trees sit under a `misc` path category) | 1.0 | 0.7 | §2 [OURS]; BotW trees slip in rain [W] |
| root (mangrove, Hist roots) | `bark` | **no `root` id**: told by category `root` (5 rows) and `deadfall`; same numbers as bark, so no new id unless a test needs one | 1.0 | 0.7 | [OURS] |
| timber (posts, stilts, planks, hulls) | `wood` | Havok wood families on non-tree rows; fallback `architecture`, `boat`, `bridge` with wood render textures counted as category | 1.0 | 0.65 | §2 [OURS] |
| metal (Dwemer, fittings) | `metal` | Havok metal family | 0.5 | 0.4 | [OURS] |
| thatch (roofs) | none: reads `wood` or `foliage` | **not separable by material**: told by `wood`/organic Havok + an alpha-masked render material on the hit (`alphaMaskMaterials`, 1,157 rows); roofs mostly land in the strain/scramble bands | 0.7 | 0.7 | §2 [OURS] |
| water-lily (pads) | `foliage` | category `aquatic-plant`; most `collision: none` (X2) | 0 | n/a | [OURS]: walked or swum, never climbed |
| bone, fungus, ceramic, glass | as named | Havok organic, glass | 0.8, 0.6, 0.3, 0 | 0.6 | [OURS] |
| soil, peat, mud | as named | terrain splats | 0.6 (banks scramble) | 0.5 | [OURS] |

`noGrip` when effective grip <= 0; slip events below 0.5 (§7); no class is
climbable dry and refused wet (degrade, never deny). Grip and wet multiplier
land as a `climb` block on each physical-materials record, generated by
`worldgen.material_views` (one home, standard 18; world/98 in the same change).

### 11a.6 What a top is

| # | Predicate | Numbers | Source | Test |
|---|---|---|---|---|
| T1 | area: valid ground under >= 0.6 x capsule radius of the support disc behind the lip (5 rays down within 0.6 m) | capsule r 0.3 m | §5 [OURS] | U; V narrow ledge |
| T2 | slope: `a <= 57.3` within 0.6 m of the lip; steeper keeps climbing (a roof) | ecctrl | §5 | U |
| T3 | clutter: capsule sweep (r 0.3, stance height) free at the landing; else shift up to 0.5 m along the lip; else hang | probes 1.6 up, 1.2 forward, 2.5 down m [C] | §5 | V cluttered top |
| T4 | headroom >= stance height | [OURS] | | U |
| T5 | the top is not excluded (X1-X4) | | | U |

### 11a.7 Transitions, both ways

| From -> to | Trigger | Source | Test |
|---|---|---|---|
| walk -> scramble | `a >= 57.3` underfoot, grip > 0, forward input | §1 [OURS] | V slope |
| walk -> wall | forward within 25 deg of `-n`, wall band, Z1 or Z2, 0.1 s; or a jump into the wall | [C]; BotW [W] | V rock |
| walk -> climb-down | within 0.4 m of an edge, climbable drop > 1.5 m, hold toward it 0.3 s | §3 [OURS] | V climb-down |
| climb -> walk, bottom | support `a <= 50` for 0.2 s, upright over 0.25 s | §1, [C] | V cliff |
| climb -> walk, top | §5 tiers when T1-T5 hold | §5 | V mantle sweep |
| climb -> fall | release, zero stamina, or grip loss with no re-grab; re-grab lock 0.35 s | §3-§4 | U; V drop |
| swim -> climb | surface swimmer's head sweep hits a valid face: mantle if top <= 1.0 m above water, else waterline attach | §3 | V water exit |
| scramble -> slide | `noGrip` in the band, or stamina zero | §1 | V slide |

### 11a.8 Survey classification (what `2.12-loops/survey.py` counts)

Per place (the 24 in the build ledger) and per terrain tile, over grid sample hits:

| Column | Counts |
|---|---|
| `walk`, `strain`, `scramble`, `slide`, `wall`, `pole`, `ceiling` | band verdicts |
| `tooThin`, `tooSmall` | Z3, Z4 |
| `excluded:boundary`, `excluded:noCollider`, `excluded:water`, `excluded:dynamic`, `excluded:interior`, `ladder` | X1-X4, X6, X7 |
| `stone`, `stoneDressed`, `bark`, `root`, `timber`, `metal`, `thatch`, `other` | accepted samples by class |
| `materialFromTag`, `materialFromHavok`, `materialFromTerrain`, `materialFromCategory` | material provenance |
| `wet:noGrip` | climbable dry, refused at wetness 1 (must be 0) |
| `ruleAcceptsRuntimeRefuses`, `ruleRefusesRuntimeAccepts` | the rule column (every published solid in one ungrouped Rapier world, §11a.3) against the runtime column (`survey_runtime.ts`: the same colliders in a live Rapier world with the game's `userData` and collision groups, struck and classified through `rapierClimbProbe`); they share `classifySurface` and the ray arithmetic, so a wrong group or tag reds them (`survey_runtime.test.ts`) and two ray casters' sub-millimetre edge and origin noise never does [OURS]. A sample stands only when the triangle a ray from outside strikes first is the sampled triangle: the hand grips the triangle the ray meets, so an overlapping shell's coplanar face is that shell's sample [OURS]. The strike starts in open air: a face whose 0.3 m standoff lies under the terrain at its x,z is buried, no ray from open air reaches it, so it is no sample (`inOpenAir`, `survey_runner.test.ts`) [OURS]. A prop face that meets §11a.3's size floor and the slope bands is climbable like any other (BotW: anything big enough) [OURS]. The rule classifies the strike's point and normal, as the runtime does. A sample the probe strikes nothing at counts as refused. Target 0 each; a disagreement carries `firstDiff`, the first probe ray the two worlds answer differently |
| `classDiffers` | both columns accept and the surface class differs |
| `aloneAcceptsWorldRefuses`, `aloneRefusesWorldAccepts` | verdicts burial and neighbours change (the hit collider alone vs the world) |
| `spotRender` | sampled ids per class for the reader's `look` sheets |

### 11a.9 `curves.json` `climbing` tunables

Kept (`game-core/src/stats/data/curves.json:216-228`, 76 §122.1):
`baseSpeedMetresPerSecond 1.1`, `baseStaminaPerSecond 7.5`,
`mantleStaminaCost 18`, `ledgeGrabStaminaCost 8`,
`burdenDrainMultiplier {fast 0.85, mid 1.0, fat 1.35, overloaded 99}`,
`restOnHoldRegenFraction 0.12`. New, landed by the climb-system lane:

| Name | Value | Source |
|---|---|---|
| `climbLeapStaminaCost` | 25 | §4 [OURS] |
| `shimmyStaminaPerSecond` | 4.5 | §4 [OURS] |
| `waterExitStaminaCost` | 12 | §6 [OURS] |
| `wetDrainK`, `wetDrainMax` | 1.5, 2.5 | §7 [OURS] |
| `slipGripThreshold`, `slipDropM`, `slipSeconds`, `slipCooldownSeconds` | 0.5, 0.6, 0.5, 6 | §7 [OURS]; TotK 6 s [W] |
| `tiredFraction`, `tiredSpeedMul` | 0.15, 0.7 | §4 [OURS] |
| `regrabLockSeconds`, `minGrabHeightM` | 0.35, 0.35 | §3 [OURS]; SkyParkour 35 uu |
| `attachFacingDeg`, `attachDwellSeconds`, `detachDwellSeconds` | 25, 0.1, 0.2 | [C]; §1 [OURS] |
| `strainStartDeg`, `scrambleStartDeg`, `wallStartDeg`, `overhangMinNormalY`, `walkReturnDeg` | 45, 57.3, 70, -0.17, 50 | §1-§2; ecctrl |
| `slideSpeedMps`, `strainSpeedLoss` | 3, 0.4 | §1 [OURS] |
| `patchWidthM`, `patchHeightM`, `poleRadiusMinM`, `poleRadiusMaxM`, `poleMinHeightM`, `mantleOnlyBelowM`, `attachLipMinM` | 0.6, 0.8, 0.15, 0.6, 2.0, 1.2, 2.2 | §11a.3 [OURS] |
| `mantleTiersM` | [1.0, 1.5, 2.2] | §5 [OURS] |
| `climbDownEdgeM`, `climbDownDropM`, `climbDownHoldSeconds` | 0.4, 1.5, 0.3 | §3 [OURS] |
| `waterExitMantleMaxM` | 1.0 | §3 [OURS] |
| `shimmySpeedMul`, `leapUpM`, `leapSideM` | 0.5, 2.0, 1.5 | §4 [OURS] |

Grip and wet grip are not curves: they live on the physical-material records (§11a.5).

## 12. MOTION LIST (clip sourcing must cover every line)

Name | when it plays | kind. L = loop, O = one-shot, S = state pose (hold).

| # | Motion | When it plays | Kind | Test |
|---|---|---|---|---|
| 1 | climbGrabGround | attach from the ground into a face | O | rock scenario |
| 2 | climbIdle | still on the wall (regen 12 %) | L | hang-regen unit |
| 3 | climbUp | up input | L | cliff scenario |
| 4 | climbDown | down input | L | climb-down scenario |
| 5 | climbLeft | left input | L | corner scenario |
| 6 | climbRight | right input | L | corner scenario |
| 7 | climbDiagonal | up+side, may be blend of 3/5/6 | L | blend check |
| 8 | climbTired | stamina < 15 % | L | stamina scenario |
| 9 | climbRest | optional rest pose at a ledge/branch | S | polish |
| 10 | ledgeCatch | mid-air or jump grab of a lip | O | jump scenario |
| 11 | ledgeHangIdle | hang, feet free | L | hang scenario |
| 12 | ledgeShimmyLeft/Right | lateral on a lip | L (a left and a right clip) | shimmy scenario |
| 13 | mantleVault (<= 1.0 m) | step/vault from the ground | O | mantle sweep |
| 14 | mantleLow (1.0-1.5 m) | low top-out | O | mantle sweep |
| 15 | mantleHigh (1.5-2.2 m) | top of a wall/cliff | O | cliff scenario |
| 16 | pullUpFromHang | hang -> mantle | O | hang scenario |
| 17 | mantleNarrow | top too narrow: crouch-perch or deny blend | O | edge case |
| 18 | climbDownFromTop | cliff-top start over an edge | O | climb-down scenario |
| 19 | climbLeapUp | climb leap upward | O | leap scenario |
| 20 | climbLeapSide | sideways/diagonal leap (L and R by mirror) | O | leap scenario |
| 21 | climbRelease | let go | O | drop scenario |
| 22 | climbDropFall | after release, until land | L | drop scenario |
| 23 | climbDropLand | landing from a drop | O | drop scenario |
| 24 | climbSlip | wet slip event | O | wet scenario |
| 25 | climbFail | failed attach/leap (Failed Ledge) | O | leap edge |
| 26 | waterExit (low) | swim -> bank mantle | O | swim-out scenario |
| 27 | waterClimbOut | swim -> wall climb at the waterline | O | swim scenario |
| 28 | scrambleUp | 57-70 deg slope walk | L | slope scenario |
| 29 | scrambleDown | 57-70 deg descent | L | slope scenario |
| 30 | slopeSlide | unclimbable steep slope | L | slide scenario |
| 31 | poleClimbUp / poleClimbDown | tree trunk, stilt post (wrap) | L (an up and a down clip) | tree, stilt scenarios |
| 32 | ladderUp / ladderDown / ladderMountTop / ladderDismountTop | authored ladders | L, L, O, O | ladder scenario |
| 33 | cornerInside / cornerOutside | wall-switch pose; may be blend | O | corner scenario |

Notes: 5/6 and 12 are mirrors if the sourced clip is symmetric (retarget flip); 9 and 33 are optional only if blends are proved on contact sheets; every other line is mandatory (a system judged with half its clips is judged wrong, 2.12 Wide loads).

## Recommendations

- Add `climbLeapStaminaCost`, `shimmyStaminaPerSecond`, `wetDrainK` beside `ledgeGrabStaminaCost` in `stats/data/curves.json:215` and a `climb` unit test per rule in §11.

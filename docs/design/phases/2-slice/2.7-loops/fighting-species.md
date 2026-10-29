<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/fighting-species.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the fighting species (2.7 § b, lane 2.7b2)

Rule (decision 0142, world/74 § Packs): a hostile creature notices by its
record's `notice`, draws, comes, fights with the sandbox brain
(`fightStep` over `selectEnemyIntent`), flees under flee/2 of its health, calls
its pack by the pack rule and turns in place at its species' `turnDegPerS`
before it moves. Every number is read from the record
(`packages/game-core/src/ai/recordDisposition.ts`). Drive:
`packages/game-core/src/ai/speciesHunt.test.ts`, each species' first record in
`living.json`, flat nav stub, dt 0.1 s, a stand-in player walking in at 1.4 m/s
from outside the species' furthest sense; the actor starts facing 90 degrees
off the player. Ticks are dt steps; "turn ticks" are ticks spent turning in
place. Capture: `lanes/2.7/b-shots/drives/species-hunt.txt`.

| Species | Band | Health | Hit | Heavy | Armour | Attack period s | Group kind | Pack alarm | Notice tick | First attack tick | Flee tick | Rallied | Max turn deg/tick (limit) | Strip | Capture |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bog-dog | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | pack | rally 30 m, breaks at 2 | 165 | 212 | 213 | 1 | 18 (18) | `lanes/2.7/b-shots/species/bog-dog.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), phases read, flees left, head direction unreadable at that size | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| crocodile | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | solitary or loose bask | none | 81 | 117 | 118 | 0 | 7 (7) | `lanes/2.7/b-shots/species/crocodile.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), all five checks yes | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| death-hopper | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | pack | rally 30 m, breaks at 2 | 91 | 127 | 128 | 1 | 20 (20) | `lanes/2.7/b8-shots/species/death-hopper.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale, small body; attack frames alike | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| giant-leech | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | cluster | rally 12 m | 57 | 109 | 110 | 1 | 6 (6) | `lanes/2.7/b8-shots/species/giant-leech.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale; flee and die alike (clip is another lane's) | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| giant-wasp | D3 | 275 | 80 | 192 | 62.5 | 2.2 | nest group | rally 25 m | 55 | 109 | 110 | 1 | 16 (16) | `lanes/2.7/b-shots/species/giant-wasp.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), all five yes (chaurus set, no wings) | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| hackwing | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | flock | scatter 25 m | 91 | 251 | 252 | 1 | 10 (10) | `lanes/2.7/b-shots/species/hackwing.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), all five yes | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| hoarvor | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | cluster | rally 12 m | 66 | 109 | 110 | 1 | 9 (9) | `lanes/2.7/b8-shots/species/hoarvor.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale; die rolls belly up (settle after the stock clip, which ends upright); attack and hit alike | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| kaj-thux | D3 | 275 | 80 | 192 | 62.5 | 2.2 | solitary | none | 118 | 189 | 190 | 0 | 3.5 (3.5) | `lanes/2.7/b-shots/species/kaj-thux.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), partly: thin and tiny, head left in flee | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| marsh-rat | D1 | 55 | 8.5 | 20.4 | 9 | 2.7 | nest | scatter 10 m | 83 | none (never attacks) | 83 | 1 | 22 (22) | `lanes/2.7/b8-shots/species/marsh-rat.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale; strike staged (flees on sight); die reads as a crouch | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| slaughterfish | D1 | 55 | 8.5 | 20.4 | 9 | 2.7 | school | rally 15 m | 66 | 110 | 111 | 1 | 15 (15) | `lanes/2.7/b8-shots/species/slaughterfish.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale; flee and die alike, attack 2/3 end-on | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| voriplasm | D4 | 550 | 187 | 448.8 | 105 | 2.05 | solitary | none | 52 | 94 | none | 0 | 7 (7) | `lanes/2.7/b8-shots/species/voriplasm.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale; die squashes flat (settle after the stock clip); flee 0 so no retreat | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| wamasu | D3 | 275 | 80 | 192 | 62.5 | 2.2 | solitary | none | 61 | 103 | 104 | 0 | 7 (7) | `lanes/2.7/b-shots/species/wamasu.png`: reader (verdicts: reader-verdict.md, 3rd pass reader-verdict-3.md), all five yes | `lanes/2.7/b-shots/drives/species-hunt.txt` |
| wisp | D2 | 135 | 31 | 74.4 | 31.5 | 2.4 | drift | none | 80 | 202 | 203 | 0 | 18 (18) | `lanes/2.7/b8-shots/species/wisp.png`: reader (verdicts: b8-shots/species/reader-verdict-d.md for hoarvor and voriplasm, -c.md for the rest), fixed camera scale, creature in every tile but tiny; attack/hit and flee/die alike (clip is another lane's) | `lanes/2.7/b-shots/drives/species-hunt.txt` |

Measured by the same drive: every row but the marsh rat reads notice, then
draw, then come, then an attack intent. The rows copy each species' authored
`fightFleeAlarm` from creatures.json (flee 0 to 40; fight below flee for the
marsh rat, 40 against 60), so the flee tick is the tick after health falls
under flee/2: voriplasm (flee 0) never flees, and the marsh rat, whose flee
outweighs its fight, runs on sight (tick 83, no draw, no attack). The max
heading change per tick equals the species' `turnDegPerS` x dt and never
exceeds it. "Rallied" is the second member of the den after the first
calls: a creature calls by its pack kind's rule (world/74 § Packs; `packs.json`
`alarm`), never by Morrowind's alarm number, which decides only for a person
calling its band or household. Rally kinds (pack, cluster, nest group, school)
bring the mate to `seen`; scatter kinds (flock, nest) send it fleeing; solitary,
drift and loose-bask kinds call nobody, so their mates stay
calm. Bog dogs and death hoppers break when 2 are down (`breakAtFallen`). A
person's turn rate is the hollow warden's approach turn rate in degrees
(`HUMANOID_TURN_DEG_PER_S`, about 123 deg/s), the only humanoid rate in the data.

## Pod capture (2.7cap, GPU, 2026-10-19)

Strip fill is the median tile's share of the tile on the body's dominant axis
(`creature-fight-strips.mjs`); the bar is 45-60 percent on the median tile.
Verdicts: `lanes/2.7/b8-shots/species/reader-verdict-cap.md`.

| Species | Fill median (range), first shot | After the lens fix (view plane through the body centre) | Reader after the fix |
|---|---|---|---|
| hoarvor | 42 (40-43) | 61 (57-62) | GREEN: every tile, states differ, DIE 3/3 on its back |
| voriplasm | 44 (41-51) | 67 (60-76) | RED: clipped left in four tiles; states one blob |
| death-hopper | 50 (40-64) | 101 (75-119) | RED: clipped at the bottom; attack tiles alike; DIE 3/3 upright |
| giant-leech | 38 (24-44) | 57 (33-68) | RED: states alike; DIE 3/3 not clearly dead |
| slaughterfish | 39 (21-42) | 56 (28-65) | RED: DIE 3/3 like flee; a duplicate DIE 1/3 caption |
| marsh-rat | 42 (31-54) | 58 (43-78) | RED: rearing tiles clipped at the top; DIE 3/3 a crouch |
| wisp | 44 (44) | 58 (58) | RED: faint; attack and hit alike; DIE 3/3 empty (fade completes) |

Visual groups on the pod: `creatures` PASS (mist depth, guar, fellrunner,
marsh-rat wander; marsh-rat max jump 0.0095 m), `offense-outcomes` PASS twice.

## Strip lens and death settle (2.7b10, GPU pod)

The lens comes from two probe passes (`stripView`: median tile on 52 percent,
widened so no tile passes 90); the camera pans to the posed body's centre.
Hopper, slaughterfish and marsh-rat gained `DEATH_SETTLE` rows (belly up);
the wisp's DIE 3/3 is taken at 65 percent of its fade. `poseDegrees` in each
strip's json is the mean bone rotation between stills.

| Species | Fill median (range) | Reader (`reader-verdict-b10.md`) |
|---|---|---|
| voriplasm | 55 (52-64) | RED: states alike (clip-set gap below) |
| death-hopper | 55 (46-68) | RED: ATTACK 1-3 identical (clip-set gap below); DIE 3/3 dead |
| giant-leech | 56 (45-60) | GREEN (weak) |
| slaughterfish | 54 (39-62) | RED: hit and flee share the swim pose (clip-set gap below); DIE 3/3 dead |
| marsh-rat | 52 (40-70) | GREEN |
| wisp | 52 | RED: every state one pose (clip-set gap below); DIE 3/3 a faint ghost |

No strip clips the body.

## Redesigned around the clips we have (2.7b11)

No vault or mod clip fills these gaps (vault clip lists; the Nexus hostile-hare
mods script a dummy spell; wisp and slaughterfish mods are textures only), so
each species is redesigned on the animation side (`ATTACK_STAGING` in
`packages/scene/src/creatures/creatureRig.ts`). Attack stills sit at each
clip's most-apart poses by `poseDegrees`; the blow's window is unchanged.
Strips: `lanes/2.7/b11-shots/local/` (software GL), reader
`reader-verdict.md` there. The GPU strips are still owed. On the 2.7cap2 pod
(headed Chrome on Vulkan), `creature-fight-strips.mjs` shot no stills: the
hopper took 844 s with every still missing and an empty log. hostile-stills
and the visual groups ran on the same Chrome.

| Species | Clip set and staging | Reader |
|---|---|---|
| death-hopper | `attack` is the hare's hop (`runforward`, once): the frog leaps at its prey. Its warning poses moved under 1 degree. Beats 0.15/0.45/0.85, 29-33 degrees apart. | GREEN |
| slaughterfish | `attacklslash` already swings it broadside; the drawn body turns a quarter back through the strike and the recoil (`flank`), so the jaws come three-quarters to the player. | GREEN (pass 2) |
| voriplasm | Its record never flees (flee 0, kept): the FLEE stills show it holding and striking. Attack beats 0.25/0.40/0.80 (25.5 degrees apart, against 14 before). | GREEN |
| wisp | A 2-bone light whose `attack1` and `recoil` are one frame: its light shows the state (`glow`). It dims at the windup, flares at contact, gutters after, goes dark when hit and pale as it flees. | RED (pass 3): light alone reads as one flash, not three beats; the strike needs a 2.9 spell effect or a root dart |

## Staged on the animation side (2.9xc)

Ruling (planner, under world/90: redesign around what we have; staging is code, not new art): no vault or mod
set fills these gaps. HTBM's frog race is the vanilla hare race with no attack records; KotM's voriplasm races
are horker races whose attack events are the horker clips we ship; no mod adds slaughterfish clips. So, on
the drawn body only (`CreatureEnemyBody`; the brain's position, blow window and numbers are unchanged):
`ATTACK_STAGING.lunge` makes the hopper's hop and the slaughterfish's strike close the measured gap from
the snout to the prey's capsule (`lungeGap`, from `lastKnownPlayer`; the set's `reach` when no prey is
known; the strip json logs it as `gap`: 0.38 m hopper, 0.49 m fish), the hopper rising 0.15 m; both land
at the contact beat, hold to 90 percent of the clip and ease back after; their follow-through stills sit
inside the hold (hopper 0.7, fish 0.88). `squash` makes the voriplasm
gather low (0.7), surge up and 0.7 m forward at contact (1.35) and slump (0.85), its volume kept;
`fleeBank` rolls the slaughterfish up to 0.6 rad into its flee turn. The strip scene frames a strike two
thirds of the way from prey to body, half again further back, and holds its eye straight behind and above
a flight's start. GPU strips: `lanes/2.9x/c-shots/pod/` (shot on the shared capture pod, 3 min 1 s for the
three), reader `reader-verdict-2.md` there. Closed green by the planner's rule: a "partly" on an attack that
reaches the prey is accepted, and no act reads "no".

| Species | Fill median (range) | Attack | Flee | Die 3/3 |
|---|---|---|---|---|
| death-hopper | 54 (9-72) | GREEN (accepted partly: a low lunge that touches the prey at contact and crumples at it after) | GREEN | GREEN |
| slaughterfish | 56 (29-74) | GREEN (accepted partly: rears, a gap at contact, then at the prey on the follow-through) | GREEN: moves away, shrinking | GREEN |
| voriplasm | 56 (35-81) | GREEN: low, reared at contact, down against the prey after | GREEN (holds: flee 0) | GREEN |

## Named gaps

- Placed creature records copy their species row's `fightFleeAlarm` (2.7b5;
  a worldgen test pins it, 0 of 177 differ). The pack call reads the pack rule,
  so the wasp's buzz, the hackwing flock and the death-hopper pack call as
  world/74 describes.
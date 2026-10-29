<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/skyrim-creature-locomotion.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Skyrim creature locomotion

How Skyrim's Creation Kit moves ambient (non-combat) creatures, and the per-species wander numbers 2.7m4 derives from it. Read by the ambient-creature mover in the 2.7 combat round.

Confidence key: **H** read on the cited page this session; **M** inferred from a cited page; **L** design choice with no Skyrim source. Fetch route: the CK wiki and UESP block page fetches (HTTP 403), so every page below was read as wikitext through the MediaWiki API (`https://ck.uesp.net/w/api.php?action=query&prop=revisions&rvprop=content&titles=<Title>`); the URL on each line is the page's normal address.

## Findings

### Sandbox: what an ambient actor does

- Sandbox is a procedure that never completes; it makes the actor move around inside a Location and use idle markers, furniture and other actors. Location is the area it sandboxes within. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- `AllowWandering` lets it aimlessly wander ("Usually False"); `MinWanderDistance` is the least distance from its current position of the next wander point, picked on the navmesh within the sandbox distance. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- `WanderPreferredPath` keeps it on preferred-path navmesh triangles. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- A sandboxing actor gives up pursuing a target that leaves the Location, so the radius is a hard leash. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- Action choice: each nearby object is scored, the kind just used drops to probability zero and the others rise, so the same action is not repeated back to back. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- Action duration: `BaseDuration = fSandboxDurationBase * fSandboxDurationMult<Kind>`, scaled by `(1 + Energy * fSandboxEnergyMult * fSandboxEnergyMult<Kind>)`, then drawn uniformly in `[x(1 - fSandboxDurationRangeMult), x(1 + fSandboxDurationRangeMult)]`. The page gives no values for the game settings. H for the form, values unknown. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- Related game settings by name: `fMinSandboxRescanSeconds` / `fMaxSandboxRescanSeconds` (rescan delay), `fSandboxCylinderTop` / `fSandboxCylinderBottom` (the sphere is cut to a cylinder), `fSandBoxRadiusHysteresis` (edge padding so it does not re-path at the border), `fSandBoxDelayEvalSeconds`, `fSandBoxInterMarkerMinDist`, `fAIWanderDefaultMinDist`. Names only; values not on the page. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- Meal and sleep times are in hours of game time (sleep starts 19 to 1, lasts 6 to 10; meals 0 to 2) and apply to NPCs, not ambient fauna. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>

### Wander, Travel, Patrol, Hover

- Wander: moves to the Location and meanders within its radius; never completes; `MinimumDistance` is the least distance of the next point. The page says Sandbox is almost always preferred. H. <https://ck.uesp.net/wiki/Wander_(Procedure)>
- Travel: walks to a destination; with a duration above 0 and Must Complete set, the actor stands still at the destination until the duration expires. H. <https://ck.uesp.net/wiki/Travel_(Procedure)>
- Patrol: walks a linked-ref chain; `PointRadius` is how close it must get to each point (32 units suggested as a small radius); idle markers are used while it waits at a point. H. <https://ck.uesp.net/wiki/Patrol_(Procedure)>
- Hover is "essentially the travel in the air procedure for flying creatures": a target location and a height above it; the page marks its completion rule unknown. H. <https://ck.uesp.net/wiki/Hover_(Procedure)>

### Idle markers and pauses

- Idle markers hold one animation or a random set; actors use them during Sandbox, or while waiting at a Patrol point. H. <https://ck.uesp.net/wiki/Idle_Markers>
- The marker's Idle Timer Setting is "how long to wait before picking a new idle" (between each idle when Random, between sequences when Run In Sequence). Its value is per marker and not given. H. <https://ck.uesp.net/wiki/Idle_Markers>
- "Ignored by Sandbox" hides a marker from wandering actors; only actors linked to it use it. H. <https://ck.uesp.net/wiki/Idle_Markers>
- A sandboxing actor uses a marker only if it is unowned or owned by the actor or its faction, and reserves the marker it targets. H. <https://ck.uesp.net/wiki/Sandbox_(Procedure)>
- Skyrim implements many idles as furniture markers instead of idle markers. H. <https://ck.uesp.net/wiki/Idle_Markers>
- Wild creatures usually carry the Default Master Package, which gives follow-linked-actor (larger bodies keep a longer follow distance), travel-and-wait then patrol, guard and patrol behaviours from linked refs; the page is marked incomplete. H. <https://ck.uesp.net/wiki/Default_Master_Package>

### Package flags: walk, run, swim

- `Preferred Speed` (walk, jog, run) is the speed the actor tries to hold through the package. H. <https://ck.uesp.net/wiki/Package_Flags>
- `Allow Swimming`: actors do not swim to reach destinations unless set. H. <https://ck.uesp.net/wiki/Package_Flags>
- `Maintain Speed at Goal`: by default an actor slows before arriving at its destination. H. <https://ck.uesp.net/wiki/Package_Flags>

### Movement types and the race

- A Movement Type (MOVT) holds walk and run speeds for forward, back, left and right, and rotation speeds in degrees for rotating in place and rotating while running. There is no separate rotate-while-walking speed. The page does not print vanilla numbers. H. <https://ck.uesp.net/wiki/Movement_Type>
- Sprinting is its own Movement Type; walking is the encumbered-player pace and running is faster. H. <https://ck.uesp.net/wiki/Movement_Type>
- A race sets Movement Types for walking, running, swimming, flying, sneaking and sprinting, and has acceleration, deceleration, angular acceleration and angular tolerance fields (no values on the page). H. <https://ck.uesp.net/wiki/Race>
- Race `Walks`, `Swims`, `Flies` flags: a race with only Swims (slaughterfish) cannot leave the water; a race without Swims cannot swim but may cross deep water without swimming. H. <https://ck.uesp.net/wiki/Race>
- `Tilt Front/Back` and `Tilt Left/Right` let non-bipeds pitch and roll to the ground (horses, spiders). H. <https://ck.uesp.net/wiki/Race>
- Advanced avoidance (velocity obstacles, smoother paths) works for bipeds only. H. <https://ck.uesp.net/wiki/Race>

### Navmesh path smoothing

- No CK page read this session states a smoothing method for creature paths. The only smoothing facts found: preferred-path triangles (Sandbox, Wander pages above) and bipeds-only advanced avoidance (Race page). Not confirmed: string-pulling, corner rounding radius. Treat our own smoothing as design (L).

## Cannot be confirmed

- Vanilla MOVT numbers (walk/run speeds, in-place turn rates) for any creature: the CK pages carry the fields, not the values. Would need the plugin data (MOVT and RACE records), which the repo's own rule says to read from plugin data.
- The package lists, sandbox radii and idle timers of mudcrab, horker, deer, skeever and slaughterfish: UESP's creature pages for Mudcrab and Horker (<https://en.uesp.net/wiki/Skyrim:Mudcrab>, <https://en.uesp.net/wiki/Skyrim:Horker>) list stats and spawns only. Not on UESP; also in the plugin data.
- Values of the `fSandbox*` game settings other than the meal and sleep hours.

## Per-species data

Basis: no species value below is a Skyrim number. Skyrim's structure (a sandbox radius leash, idle waits, walk pace, in-place turning) is cited above; magnitudes are design (L), scaled by body size and gait, with the Skyrim analogue named as the behaviour model. `legMinM` and `legMaxM` are the shortest and longest wander leg to a new point (the Sandbox/Wander `MinWanderDistance` idea); `turnDegPerS` is the in-place turn rate; swimmers' radius is water-bound (Race `Swims` only, <https://ck.uesp.net/wiki/Race>); hoverers follow Hover (<https://ck.uesp.net/wiki/Hover_(Procedure)>).

| species | wanderRadiusM | idleMinS | idleMaxS | legMinM | legMaxM | turnDegPerS | walkMps | gait | Skyrim analogue and basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| guar | 14 | 3 | 10 | 3 | 9 | 100 | 1.1 | walk | deer/goat herd grazer: sandbox with long grazing idles |
| alit | 12 | 3 | 9 | 3 | 8 | 90 | 1.2 | walk | bear/sabre cat idle-wander, bulkier turn |
| bog-blight | 8 | 2 | 6 | 2 | 6 | 80 | 0.9 | walk | chaurus-like slow ambient creeper |
| bog-dog | 16 | 2 | 6 | 4 | 12 | 180 | 1.8 | walk | wolf/dog sandbox, quick turn, short pauses |
| giant-wasp | 12 | 1 | 4 | 3 | 9 | 160 | 1.6 | walk | chaurus body: walker with brisk turns |
| crocodile | 10 | 6 | 18 | 3 | 10 | 70 | 1.0 | swim | mudcrab/slaughterfish: waterside lurker, long still idles |
| crow | 10 | 1 | 4 | 1 | 4 | 240 | 1.4 | walk | chicken/hawk ground hopper, rapid turn (flies in combat) |
| death-hopper | 7 | 2 | 6 | 2 | 6 | 200 | 1.3 | swim | skeever/slaughterfish: darting small swimmer |
| hackwing | 14 | 2 | 8 | 4 | 12 | 100 | 1.5 | hover | small dragon body: perched idles, hover legs |
| fellrunner | 18 | 2 | 6 | 5 | 14 | 160 | 2.2 | walk | wolf/deer runner: long legs, brisk walk |
| giant-leech | 6 | 3 | 9 | 1 | 4 | 60 | 0.5 | swim | slaughterfish, water-bound slow drifter |
| haj-mota | 24 | 5 | 14 | 6 | 20 | 50 | 1.4 | swim | horker/mudcrab: large water-bound cruiser |
| haynekhtnamet | 40 | 6 | 16 | 10 | 32 | 30 | 2.0 | swim | 9 m water-bound giant: horker scaled up, slow turn |
| hoarvor | 10 | 3 | 9 | 2 | 7 | 90 | 1.0 | walk | skeever/mudcrab ground ambler |
| jassa-red-slug | 5 | 4 | 12 | 1 | 3 | 60 | 0.3 | walk | mudcrab pace, shorter still |
| marsh-giant | 20 | 4 | 12 | 5 | 16 | 50 | 1.6 | walk | Skyrim giant sandbox at camp, heavy turn |
| marsh-rat | 8 | 1 | 4 | 2 | 6 | 220 | 1.5 | walk | skeever sandbox, twitchy pauses |
| miregaunt | 12 | 3 | 9 | 3 | 10 | 90 | 1.2 | walk | troll/ogre-like lumbering sandbox |
| mouth-plover | 9 | 1 | 4 | 1 | 4 | 240 | 1.3 | walk | chicken: peck-and-step ground bird |
| osheeja-gar | 28 | 5 | 14 | 6 | 22 | 45 | 1.5 | swim | horker/mudcrab scaled up, water-bound |
| sea-drake | 30 | 5 | 14 | 8 | 24 | 40 | 1.8 | swim | water-bound large swimmer, slow turn |
| slaughterfish | 12 | 1 | 4 | 3 | 10 | 150 | 1.6 | swim | slaughterfish: Swims-only, cannot leave water (Race page) |
| kaj-thux | 16 | 6 | 18 | 4 | 14 | 35 | 0.8 | slither | 8 m snake: slow body, long still idles |
| moon-adder | 5 | 3 | 10 | 1 | 4 | 120 | 0.5 | slither | 1 m snake: short bursts, quick coil turn |
| medusa | 10 | 5 | 15 | 2 | 8 | 60 | 0.7 | slither | 3 m snake: slow body, long idles |
| torchbug | 6 | 1 | 3 | 1 | 3 | 220 | 0.6 | hover | torchbug/butterfly: Hover with short hops |
| voriplasm | 8 | 3 | 9 | 1 | 5 | 70 | 0.5 | walk | slow oozer, mudcrab-like pace |
| wamasu | 20 | 4 | 12 | 5 | 16 | 70 | 1.8 | swim | water-bound mid-size swimmer |
| wisp | 8 | 2 | 6 | 1 | 5 | 180 | 0.6 | hover | wispmother/will-o-wisp: Hover drift, free turn |
| swamp-jelly | 6 | 3 | 8 | 1 | 4 | 90 | 0.4 | hover | floating drifter: Hover, tiny legs |

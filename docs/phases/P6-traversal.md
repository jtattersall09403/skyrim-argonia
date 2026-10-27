# P6: Climbing, ladders, swimming and diving, boats

**Goal.** Province-wide free climbing with stamina (BotW-like, old 0152), ladders, 3D swimming and diving with
Argonian breath rules, and sailable, ownable boats (Wind Waker sailing, horse-like ownership, old 0158/0159).

**Starting state.** P2 passed; P3's water and navmesh exist at least for the slice region; G3 confirmed
FreeClimb, SkyParkour (or not), EVG Animated Traversal and Underwater NG on the pinned runtime.

**Re-check before starting:** FreeClimb (its repo had one commit when researched), SkyParkour, EVG Animated
Traversal, Underwater NG and Sailable Ship versions on the pinned runtime.

**Read first.** Decision 0020; universal-modder's `port-a-mod` skill (for any fork) and field notes on climbing
(White Knuckle) and `porting-a-vehicle-semantic-traps` (boats); [skyrim-combat-traversal](../research/2026-10-27/skyrim-combat-traversal.md) §2–3;
[um-ghidra-lens](../research/2026-10-27/um-ghidra-lens.md) §4 (Faith Runner, AC1 Movement Rewritten, White
Knuckle note), §6 climbing and boats rows; imported `docs/design/world/76-stats-progression.md` §122;
`docs/design/research/` botw-climbing-system, skyrim-climbing-mod-survey, swim-climb-boat-implementation,
player-boats-as-horses; old decisions 0093, 0152, 0158, 0159; old phase docs 2.12 and 2.15 (imported).

## Work packages

### WP6.1 Climbing (FreeClimb as the base)
- FreeClimb (GPL-3.0-only; SKSE; free climbing on valid walls, sideways leap catches, push-away, let go, auto
  mantle, obstacle bypass, optional stamina drain) configured to the old rules: slope bands (walk below ~57°,
  then scramble, then climb), solid-mesh size limits, surface classes with wet grip (slip when wet), climb speed
  1.1 m/s × band(0.85–1.25), drain 7.5/s × band, burden drain multiplier ×0.85/×1.0/×1.35 (fast/mid/fat), mantle
  cost 18, ledge grab cost 8, hanging recovers 12% of normal stamina regen, climbing grants skill XP at 0.2 per
  metre, the scramble/slide band 57.3–70° between walking and climbing (76 ~963–966, botw-climbing-system),
  fall at zero stamina; walls
  under 10 m open to all, ~25 m a real climber, over 40 m a specialist (Athletics/Acrobatics/Agility); **no wall
  running** (old 0152), so FreeClimb's wall run is disabled.
- Where FreeClimb lacks a rule (wet slip, stamina by burden), add it: through its menu/API first, then a fork
  (GPL: our fork's source published, credited), then ArgoniaCore.
- SkyParkour for ledges and vaults if G3 showed it coexists with FreeClimb; otherwise FreeClimb's mantle only.
- Climb clips are FreeClimb's (Mixamo/Threepeat under their own terms): we require the mod, never copy clips.
- Study Faith Runner's vault heights and AC1 Movement Rewritten's climbable-edge model for any gap we must
  code ourselves (knowledge only).
- **Acceptance (L4):** a climbing course scenario (10 walls of each class, wet and dry, corners, overhang
  catches, mantles) passes; stamina drains at the formula's rate within 5%; the old province climbability survey
  (which walls are climbable) is re-run against our geometry and matches by class.

### WP6.2 Ladders
- EVG Animated Traversal markers placed by the generator wherever the old layouts had ladders and at every
  kit ladder mesh; ladder stamina add-on if it matches the rules.
- **Acceptance:** every placed ladder climbable in an L4 sweep.

### WP6.3 Swimming and diving
- Skyrim swimming (native) + Underwater NG (buoyancy from equipment, swim speed, Diving skill → mapped to our
  Athletics where possible, depth visuals and audio); swim sprint from the swim-sprint mod (Nexus 67028) if its
  permissions allow, else our own; stroke 2.8 m/s (the later owner-asked reference) scaled by Athletics (×0.5 →
  ×1.5, 76 §122), sprint-swim ×1.4 drains stamina,
  shoulder-depth entry 1.4 m; breath = 25 + 0.35 × Athletics + 0.25 × Endurance seconds; Argonians unlimited;
  the underwater contract (76 ~978–983): 30 s submerged open to all, 45 s competent, 60 s specialist, over 75 s
  only for Argonians, water-breathing spells or equipment; drowning damage; swim attacks (BFCO supports them); water as a
  stealth medium (submerged breaks sight, P4-WP4.17); no route requires being Argonian (old 0152 §4).
- **Acceptance:** L4 scenarios for breath per race and stats, a dive through a flooded passage, swim combat.

### WP6.4 Boats: sailing (ArgoniaBoats)
- Base: Sailable Ship VR and SE (ziher; modify and asset use with credit): a scripted helm with wind
  simulation. Rewrite its control model in SKSE as **Wind Waker sailing** (old 0159): the boat cruises at a
  speed toward the steered heading, faster with the wind astern; the player can turn the wind with a quick
  power/item/spell; a HUD wind mark; wind is the weather's.
- Known issues to fix rather than inherit: unstable deck walking at speed (move the player with the boat as a
  platform), unanimated sails (sourced animated sail meshes if any; else accept), getting stuck when saving at
  the helm (rest is the only save, so forbid rest/save at the helm), the 60 fps assumption (frame-time
  independent integration).
- Boats never travel over land (water check against the water records); wake and water response from the
  water shader's existing effects.
- Two classes first (old 2.15): the **dugout** (river, paddled) and the **sea hull** (sail); more classes later
  as config rows. Meshes from boat mods in the manifest (SFSS canoe, Sailboats Expanded, Rowboats CC BY-SA,
  Sailable Ship's ship).
- Crew: animation first, a pose fallback (old 2.15 rule).
- **Acceptance:** L4 scenarios: sail a triangle course with the wind from three directions; time per leg within
  10% of the model's prediction; no deck fall-through at full speed; dugout on a river reach.

### WP6.5 Boats: ownership like horses
- Bought, taken or found; owned; tied at moorings (the old mooring sockets); after rest, recovered to the last
  tied mooring; or fetched to the nearest mooring for 10% of price (minimum 5 gold); theft is an Owing entry
  (P4-WP4.17); passengers.
- Pattern references: Sailboats – Script Free Sailing EXPANDED (boat as a mount race; restrictive terms, so
  pattern only) and the Rowboats mod (CC BY-SA; code Unlicense).
- **Acceptance:** L4 scenarios for buy, moor, rest-recover, fetch fee, theft.

### WP6.6 Owner packets
Two packets: climbing + swimming course; boats (a sailing trip between two moorings and a river dugout run).

## Exit gate
Course scenarios green; owner packets with no open blocker; the parity notes for climbing (vs BotW rules) and
sailing (vs Wind Waker model) written.

## Risks and fallbacks
- **FreeClimb gaps** (it had one commit when researched; maintenance risk): fork early if needed (GPL).
- **Boat physics on Havok** misbehaves: keep the boat kinematic (scripted motion) and the player attached as a
  passenger rather than simulating buoyancy; Wind Waker's model is kinematic anyway.
- **Climbing on generated terrain** behaves differently from hand-made walls: tune slope bands on the province
  survey before content work.

## Deliberately out of scope
Mounts (cut, old 0042); boats chasing boats (cut, old 0026); wall running (old 0152); active buoyancy physics
(boats stay kinematic); levitation (P4-WP4.15).

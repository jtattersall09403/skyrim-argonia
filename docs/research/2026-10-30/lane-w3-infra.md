# Lane report: w3-infra (the 2.W3 gates, landings and signposts; Claywater's crime faction)

## Done

**1. Infrastructure placed.** `tools/argonia_world/routes/infra.py` writes 60 persistent refs into the WRLD
override's persistent cell (regions/api.py): 2 exit gates, 2 ferry landings, 16 signpost posts and 40 arms. None is
pending. Every z is on the final game ground (`place_build.GameGround`, as in f6177a7), no longer on the frozen 2.W1
array. The landings moved from 33.34/33.11 m to 32.30/31.89 m.

The design pieces resolve through `infra.DESIGN_PIECES`, then pieces.py and the preference rule:

| Piece | Mesh | Resolves to | Written as |
|---|---|---|---|
| `gate-road-closed` | `argonia/stockades/stockadegate01.nif` | KotM `CypressStockadePalisadeGate` (a Door) | our ACTI `ARG_ACTI_BorderGate` ("Border Gate", verb "Open") on the same mesh, so it never opens |
| `landing-argonian` | `argonia/mudhuts/tamu_wooddock01.nif` (player-boats-as-horses.md K1) | KotM `MudHutWalkway01` 01FA35 | the base record |
| `signpost` | `clutter/signage/roadsigns/roadsignpost.nif` (Claywater's waymark p1) | Skyrim.esm `RoadSignPost` 03AF9D | the base record |
| `signpost-arm` | `roadsignmedium01r.nif` (BMV, Claywater's p1-board2) | loose mesh | one ACTI per destination name (18) |

- **Sign text.** Skyrim's only text for a sign is the crosshair: a named ACTI shows its name when the player looks
  at it. The 16 posts are not looked at. Each arm is an ACTI named with its destination: the place's name, or for
  an exit node the city beyond it (Leyawiin, Tear). The activate verb is overridden to "To", so the crosshair reads
  "To Gideon". This is the Morrowind behaviour, where you look at an arm and read it.
  - The arms are yawed `bearing − 90°`. This assumes the vanilla R-board convention, where the board runs along
    the mesh's +x; I could not measure it because the mod meshes are not on the build VM.
  - The arms are stacked from 2.27 m down in 0.29 m steps (Claywater's board heights).
  - s10's still checks both of these.
- **The closed road (choice recorded).** Activating a gate shows the MESG `ARG_Msg_RoadClosed` ("The road beyond is
  closed.") as a notification.
  - The route is a hidden perk, `ARG_Perk_RoadClosed` (world id `hook.road-closed`). Its Activate entry is Run
    Immediately and Replace Default, conditioned on the gate's keyword `ARG_ClosedGate`. Its fragment
    `ARG_PRKF_RoadClosed.psc` is the single line `RoadClosed.Show()`, and the MESG is a script property.
  - ArgoniaCore's `EnsurePerks` gives the perk to the player (one line in engine.cpp).
  - The player is stopped by two things: the gate's collision, and 20 m further on the border REGN (2.W3 §a).
  - **Why not a trigger volume:**
    - it needs two writer features we lack: a placed primitive (XPRM) and a script with properties on the
      trigger's base;
    - it needs an OnTriggerEnter event script;
    - the barrier it would add is already made by the border wall.
  - **Why this route:** it reuses the rest and dialogue intercepts' writer and fragment pattern, and it is
    vanilla's barred-door behaviour (activate, read a line).
- **Writers (ArgoniaGen).**
  - New `SocialRecords.cs`: FACT and MESG, registered in `Generate.Run`.
  - `PerkRecords.cs`: object properties on the fragment script.
  - `CombatRecords.cs`: the NPC_ crime faction.
  - `intermediate.TYPE_ORDER` gains FACT and MESG.

**2. Claywater's crime faction.**
- New db rows:
  - `faction.claywater-station` ("Claywater Station", kind settlement);
  - `place_faction_presence` (claywater-station, seat).
- One town, not two: `culture.settlement.claywater-station` holds both the station-half and the landing-half
  groups.
- `place_build.town_faction` writes `ARG_Faction_ClaywaterStation` (0009C2), with flags Track Crime and Hidden
  from PC.
  - Its crime values come from the region's Owing (`owing.imperial-fringe`): murder 1000, assault 40, trespass 5,
    pickpocket 25, steal ×1.
  - Arrest and attack on sight are on. Escape and werewolf are 0, since there is no Owing rate for them yet (2.10).
- The four people (Livia, the poler, n1, n1-3) are members at rank 0, and it is their crime faction. The
  crocodile is not a member.
- The well-keeper's imported `imperial-legion-remnant` membership is not written yet: no FACT exists for the
  imported factions (that is 2.4 §c).

**3. World sample.**
- Stop 9 now uses the real gate. Its cell is 47,63, no longer the provisional -12,63, and its region is
  dunmer-north.tidal-delta.
- `s09-gate-message` is un-owed. It moves the player 3 m before `ARG_Ref_GateTearRoad`, faces the gate and presses
  E, then checks that the gate is enabled and the player has the perk. The reader checks the notice.
- The push step now starts 5 m before the gate. It checks that the player stays inside the border; the old ≥300
  units of travel no longer applies, because the gate blocks.
- `s10-sign-text` is un-owed. It puts the player before arm 0 of the Gideon sign, looking up at the board, and checks
  that the post and arm refs are enabled. The reader checks that the crosshair reads "To Archon".
- Regenerated with `tools/world_sample.py --write`, which changed the journey and the stop 9 scene.

## Measured
- `infra check`: 2 gates, 2 landings, 16 signposts, 40 arms; 0 errors. Every post, gate and landing is within
  0.5 m of the final ground, and every arm has text.
- `make plugin` twice: out/Argonia.esm sha256 9055540522b8… both times, and the plugin/ tree hash be6fe88f… both
  times.
- `make plugin-check`: regenerated twice identical, plugin/ current, round trip byte-identical.
- `make check`: CHECK GREEN, 361 passed in 130.7 s, ctest 32/32.
- New L1 tests:
  - `routes/tests/test_infra.py` (4). This includes a floating post and a blank arm, which fail on purpose.
  - `tests/test_town_faction.py` (3).
  - `test_people_records` now requires `factions` and `crimeFaction`.

## Owed
- **game-10, in game (L4):**
  - deploy the plugin, the DLL (the EnsurePerks line) and the new `ARG_PRKF_RoadClosed.pex`;
  - s09 gate message;
  - s10 sign still: arm direction and height, and the crosshair text;
  - crime tracked: steal in sight of a Claywater person, then `player.GetCrimeGold`, or
    `GetCrimeGoldNonviolent ARG_Faction_ClaywaterStation`.
- **The crosshair label.** An ACTI with no script has never been verified to show its prompt. If it does not, the
  arms need the perk route as well (a no-op fragment).
- **Placement.**
  - Signposts at place nodes stand at the place centre (for example, Stormhold's), so a built place may collide
    with its sign.
  - A junction post stands on the road centreline.
- **Text review.** The new labels "Border Gate", "Open" and "To" had no reader pass; the gate message and the arm
  names had one in 2.W3.

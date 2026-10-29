# w3-road-hops (draft, 2.W3 §b; owed L4)

**Checks:** each traced road leg is on the road surface end to end, and the two exit gates stand where the roads meet
the border.

- **Scene:** the base save. Step 0 teleports to the leg's first `road_point` and sets nothing about the road.
- **Per leg (23):** hop along `road_point` every 100 m by teleport. At each hop, read the player's z against the 2.W1
  probe height at that point, and the land texture under the player (the BC_ROAD or TRACK LTEX painted by
  `routes/paint.py`). Keep a still per hop at the play camera, looking along the leg.
- **Pass:** every hop stands on the leg's surface class, z is within 0.5 m of the probe, and nothing blocks the next
  hop (a tree or rock on the road means the CK generator's object list needs its road exclusion, 2.W4).
- **Gates:** at `gate.blackwood-road` (cell -62,12) and `gate.tear-road` (cell 47,63), a still once the pieces
  resolve, then a push outward as in `terrain-border-push`.
- **Finding to look at:** Tear Road Stage (the place) stands 3.4 km west of where the traced Tear road meets the
  border. The still at its hop says whether the paint or the place is off.
- **Fails if:** a hop off the surface, a hop under the ground or in water, a crash.

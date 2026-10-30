# damage-novice

Finding: the 10.8 bound was mis-derived; the engine and our rules agree. Nothing retuned.

- Blow (combat-wiring five-builds table): 24 x P 0.501 x S 0.90 = 10.82, the damage before the target's armour.
- The deserter (archetype D2, AR 31.5) mitigates AR/(AR + 135.6 + 0.6 x 24) = 0.1736 (body_incoming_damage uses reference_blow 24).
- Health loss = 10.82 x 0.8264 = 8.943; 2000 - 8.943 = 1991.06, the live read in lane-game-15 exactly.
- god-blow had the same omission: 36.0 x 0.8264 = 29.75, health 1970.25; bounds now 1969.7..1970.7.
- Fixed in tests/journeys/fight-damage-builds.yaml (novice 1990.5..1991.5). Difficulty is not in play (see the owed step).

"""nw-02 step 8: trees, plants, rocks, cliffs, seabed, water's-edge and road dressing placed and seated.

    python3 -m tools.newworld.place run [--force]   # the placement -> out/newworld/plugin/placed/flora (keyed; skips a match)
    python3 -m tools.newworld.place check           # the off-game checks of the placement -> placed/flora/check.json
    python3 -m tools.newworld.place render          # region/composition maps, canopy crops, seating slices
    python3 -m tools.newworld.place refs | edit | edits ...   # single placed things listed and edited (edits.py)

See place.py for the recipe and the shard format (read by NewWorld.cs and by tools/navmesh/placed.py); edits.py for
the edits of single things, applied over the placement into out/newworld/plugin/refs/flora.
"""

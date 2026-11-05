# Lane 1.15-r6-water-stands-5: fronds over the OBND's top, the river's near field, the stream's narrowest reach

(1) Evidence, read here: 04-river-s0 and s1 look through fronds filling the frame, lime water behind; s1 shows a channel
between banks through them. 05-stream-s1/s2 show a pool with a near-dark body but a far bank 15-25 m off (trunk, red
tree): not "no far bank" as briefed; s0 aims over dry land, water only at the right edge. 01-sea not re-read (out of scope here).

(2) Measures (round-6 stands). River (65000,-30046) facing 86: the fronds are King of the Murkmire's Bush01
(03A583, Plants\Tamira\New Plants\Bush01.nif), one 3.8 m along and 0.5 m off the aim, another 5.2 m off at 0.5 m.
Its canopy radius was 377.9 u (5.6 m) in the table, but its OBND height is -16..113 u (1.8 m) while the mesh stands
-185..438 u (8.3 m): the cylinder's top lay 1.0 m under the eye, so the line test (`lo <= eye z <= hi`) passed it.
Other plants within 6 m: lily pads 0B75A1 (27-35 m), gorse 14FAD6 (34-39 m), TropicalPlant01 (39-45 m), cypress 0E6796 (47 m).
Stream (-178131,-26983) facing 125, reach.580-2263 (width_m 9.5): the aim's footprint is wet 6.0-7.0 m only (the
aim crosses a 1 m corner of the water); widths across the reach within 200 m: 5.0 m narrowest (point 33, 162 m off),
28.5 m widest, 22.5 m at the nearest point.

(3) Fixes. canopy.py also lists forms whose mesh top reaches 15 % past the OBND's (z_u: mesh z0..z1); Build.shapes
takes the taller span (6 forms; data/canopy-radius.json re-measured, the measures' static key moves with it).
tall_near (nothing over 1 m within 4 m of the line to 15 m) is a hit for the river stand; far_bank_m (the aim's
footprint meets the far bank within STREAM_BANK_M 25 m) for the stream; the stream's subject is its reach's
narrowest point within 200 m (gen._narrowest, _reach_width_m), aimed across it (no flow gate). Palm OBNDs equal
their meshes (lane -4), so no palm-specific radii were needed: Bush01 is the frond plant.

(4) Clearance before/after (generator's line/canopy/grass, frame share):
- river: before 9/0/33 100 % (re-measured with frond heights: 10/2/32, tall 5, no far bank); after (74927,-26263)
  facing 113: 6/4/20, cover OVER, frame 93 %; tall_near 0 at the eye line.
- stream: before 1/0/31 31 % (tall 4, far bank 7.0 m); after (-169553,-31515) facing 110: 1/1/41, cover OVER,
  frame 35 %; far bank 8.0 m.
- tarn moved with the taller fronds: cell (-55,7) to (-55,13).
Open: no river or stream stand passes strict over 40 shores nor the 600 m widened search: Bush01's 8 m frond span lines
these banks. The kept stands are the best found and still warned (SHORT_OF_FRAME); the lever is the vegetation
lane (Bush01 off river and creek banks, or its scale), not the search. s0 showing the channel is unproven until L4.

Gate: refresh --only water-types ok, check 0 stale, journey_lint ok, run_journey --dry ok, 45 journeys tests pass, ruff clean.

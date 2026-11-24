# The 3D-generation cost experiment (owner call #94, 24 November 2026)

The question: can a cheaper generator than Tripo H3.1 give a model we would keep, and how many models would $90
buy? The same reference image of each of three things (the dugout canoe, the root hut, the glaive head) went once to
each of five cheaper routes on Fal, and later to Meshy 7.1. Every result is in the asset explorer under its thing as
"Other generators tried", ranked, scaled to the brief in true metres beside a 1.8 m person.

**The owner's verdict:** Tripo H3.1 is clearly the best across all three things, and it gives the best textures. Our
own shared material instead of the generator's texture looks worse to him; it stays on the page only as a comparison.

## What changed in this version of the note

The first version priced three routes wrongly: it read the Fal pricing tool's unit price as a price per run, and
recorded no endpoint ids or options. Every run has now been traced to its exact endpoint and options in Fal's request
history (the ids are in each asset record), and priced from that model's own Fal page as read on 24 November 2026.
Fal's history shows no charge per request, so these are list prices for the options used, not a bill.

| Route (endpoint, options used) | First note said | Fal's page says | Change |
|---|---|---|---|
| Trellis 2 (`fal-ai/trellis-2`, resolution 1024, texture 2048) | $0.05 | $0.30 (1024p; $0.25 at 512p, $0.35 at 1536p) | six times dearer |
| Hunyuan 3.1 rapid (`fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d`, no PBR) | $0.015 | $0.225 (+$0.15 with PBR) | fifteen times dearer |
| Hunyuan 2 mini turbo, textured (`fal-ai/hunyuan3d/v2/mini/turbo`, `textured_mesh`) | $0.24 | $0.08 | a third |
| Reference image, Nano Banana 2.1 at 2K | $0.12 | $0.059, or $0.063 as an edit | half |
| Trellis (`fal-ai/trellis`) | $0.02 | $0.02 | none |
| Idol max turbo (`speridlabs/idol/max/turbo`, no PBR) | $0.10 | $0.10 (+$0.10 with PBR) | none |
| Tripo H3.1 (`tripo3d/h3.1/image-to-3d`, texture, PBR, detailed texture) | $0.40 | $0.40 ($0.20 untextured, $0.30 standard texture) | none |
| Tripo P2 (`tripo3d/p2/image-to-3d`, detailed) | $1.20 | $1.20 | none |
| Meshy 7.1 (`meshy/v7.1/image-to-3d`, textured), new | none | $1.20 ($0.80 untextured) | new |

## What came back

Nineteen jobs: seventeen returned a model, two failed. Both failures were Hunyuan 3.1 rapid, which refused the canoe's
and the hut's reference images before running because they were over its 950 KB limit (1,204 KB and 2,083 KB). Fal
does not charge a request refused at its input.

| Route | Price per run | Canoe | Glaive head | Root hut |
|---|---|---|---|---|
| Tripo H3.1, detailed texture (the owner's pick) | $0.40 | kept, best | kept, best | kept, best |
| Meshy 7.1, textured | $1.20 | kept: clean, smoother and greyer, fainter adze marks | kept: truer grey core, shallower flaking | kept after clean-up: 384 loose pieces, more windows than the brief |
| Trellis | $0.02 | kept | thrown away (two spurs, not one) | kept after clean-up |
| Trellis 2 | $0.30 | kept | kept after clean-up | thrown away (shell full of holes) |
| Hunyuan 2 mini turbo, textured | $0.08 | thrown away (flat texture) | kept | thrown away (smooth roof, stray bits) |
| Hunyuan 3.1 rapid | $0.225 | failed (image too large) | kept: crisp flaking | failed (image too large) |
| Idol max turbo | $0.10 | thrown away (pointed bow) | kept after clean-up | kept after clean-up |
| Tripo H3.1, no texture asked | $0.20 | came back painted anyway: buys nothing | not tried | not tried |

## What $90 buys

Like for like with the run we made through Fal: H3.1 with standard geometry, a texture, the HD texture and PBR maps.
In Tripo's own web studio that is HD Generate (15 credits) + Texture Gen (+10) + HD Texture (+10) + PBR (+5) = 40
credits. In Meshy's web app, Meshy 7.1 textured is 25 credits on a paid plan (it starts at Ultra 2K) + texture (+10) =
35 credits. Both vendors' pricing pages were read on 24 November 2026 (supplied by the owner). Web-studio
subscription credits do not pay for API or CLI use (the owner confirmed this for Tripo), so a web-studio route means
someone generating in the studio by hand.

| Route | Sum per model | Models for $90 | Notes |
|---|---|---|---|
| Tripo H3.1 through Fal, as now | $0.40 + a $0.06 reference image = $0.46 | 195 (225 without the image) | runs from our tools, no subscription |
| Tripo web studio, Max plan ($90 a month, 25,000 credits) | 40 credits x $90 / 25,000 = $0.144 | 625 a month (1,250 in the first month with the new-user half-price coupon) | by hand in the studio; 8K textures included; unspent credits are lost at the month's end |
| Tripo web studio, Pro plan ($20 a month, 3,000 credits) | 40 x $20 / 3,000 = $0.27 | 75 a month; $90 is four and a half months | by hand |
| Tripo extra credits ($100 for 12,000) | 40 x $100 / 12,000 = $0.33 | 270 | on top of a plan |
| Meshy 7.1 through Fal | $1.20 | 75 | runs from our tools |
| Meshy web app, Premium ($40 a month, 3,000 credits) | 35 x $40 / 3,000 = $0.47 | 85 a month; $90 is two and a quarter months, about 190 | by hand |
| Meshy web app, Ultra ($100 a month, 8,000 credits) | 35 x $100 / 8,000 = $0.44 | 228 for $100 | by hand |
| The cheapest kept route per kind, through Fal | Trellis $0.02 for props and buildings; Hunyuan 2 mini $0.08 for weapon heads | about 3,000 (generation only) | the owner judged these worse than H3.1 |

Tripo's own figure on its page ("25,000 credits, about 1,660 models") counts a 15-credit untextured model, not the
textured one we make.

## What this changes

1. Tripo H3.1 with the detailed texture stays the generator for every kind of thing, as the owner ruled. Meshy 7.1 is
   close on the canoe and the glaive head but three times the price through Fal and worse on the hut.
2. At volume, Tripo's Max plan in the web studio gives the same model for about a third of Fal's price, but only by
   hand in the studio. Through Fal, $90 is about 195 models with their reference images.
3. Save every reference image as a JPEG under 700 KB before sending it, so every route accepts it.
4. Tripo's texture task takes a style reference image (+5 credits in the studio). That matters for making a family of
   models look alike, and is part of the consistency test.

## Buildings: asking for a dense enough texture

The root hut came back with 278.7 square metres of surface on one 4096-pixel texture: 183 pixels per metre, where
Skyrim's weathered wood is 420 to 830 (median 650). Tripo's own layout used about 56% of its picture. One atlas
covers, at 75% use:

| Atlas | At 420 px per m (wood's low end) | At 650 px per m (wood's median) |
|---|---|---|
| 4096 (4K) | 71 square metres | 30 square metres |
| 8192 (8K) | 285 square metres | 119 square metres |

So anything bigger than a canoe needs more than one 4K picture, and a hut-sized building needs one 8K atlas laid out
well, or several. What each route offers:

- **Through Fal** (`tripo3d/h3.1/image-to-3d`): `texture_quality` is only standard or detailed, and detailed came back
  4096 for both H3.1 and P2 on the hut. There is no 8K texture and no generating in parts. P2 has an `extreme`
  texture quality whose size is not documented; it was not tried. The Fal route therefore stays $0.46 a building,
  followed by `tools/newart/densify.py`, which relays the texture at 420 px per metre and adds fine grain along the
  painted strokes (free, about five minutes). It does not add the generator's own detail: close up, the painted look
  is the same, slightly sharper on doors and roots.
- **Tripo's web studio**: 8K textures are included on paid plans, and Generate in Parts (+30 credits) gives each part
  its own texture. A building is HD Generate 15 + Texture Gen 10 + HD Texture 10 + PBR 5 + Generate in Parts 30 =
  70 credits: $0.25 on the Max plan ($90 for 25,000 credits), $0.47 on Pro ($20 for 3,000). Three or four parts (walls,
  roof, roots or posts, door) each with its own 8K picture would, by the table above, reach 420 to 650 px per metre on a
  hut of this size (not yet tried).
  This is by hand in the studio.

**Recommendation.** A building whose surface is over about 70 square metres goes to Tripo's studio with the 8K texture
and Generate in Parts, at 70 credits ($0.25 on Max), so it arrives with its own detail at the game's density. Through
Fal (by tool, no subscription), it stays $0.46 and is finished with densify.py. Props under about 70 square metres
keep the current route.

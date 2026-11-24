# The 3D-generation cost experiment (owner call #94, 24 November 2026)

The question: can a cheaper generator than Tripo H3.1 give a model we would keep, and how many models would $90
buy? The same reference image of each of three things went once to each of five cheaper routes on Fal. Every
result is in the asset explorer as a version of its asset, beside the kept Tripo H3.1 version, so any two can be
turned side by side under one camera; each asset's record carries the table (stage "Cost experiment").

Prices are Fal's list prices as read on 24 November, not a bill: the Fal tools report results and timings but no
charge per request. Each route was tried once per thing, so every rate below rests on one to three results.

## What came back

Sixteen jobs: fourteen returned a model, two failed. Both failures were Hunyuan 3.1 rapid, which refused the
canoe's and the hut's reference images before running because they were larger than its 950 KB limit (1,204 KB
and 2,083 KB). That is our input, not the generator: a JPEG under about 700 KB would have gone through. Fal does
not normally charge for a request rejected at input, but that was not confirmed from a bill.

| Route | Price per run | Canoe | Glaive head | Root hut |
|---|---|---|---|---|
| Trellis | $0.02 | kept | thrown away (two spurs, not one) | kept after clean-up |
| Trellis 2 | $0.05 | kept | kept after clean-up | thrown away (shell full of holes) |
| Hunyuan 2 mini turbo, textured | $0.24 | kept after clean-up (flat texture) | kept | kept after clean-up |
| Hunyuan 3.1 rapid | $0.015 | failed (image too large) | kept, the best head | failed (image too large) |
| Idol max turbo | $0.10 | kept after clean-up | kept after clean-up | kept after clean-up |
| Tripo H3.1, bare shape | $0.20 | kept, with our shared material | not tried | not tried |
| Tripo H3.1, detailed texture (earlier, kept) | $0.40 | kept | kept | kept |

"Kept after clean-up" means a clean-up our tools already do: removing loose pieces, straightening, cutting
triangles. Nothing in the set needed hand modelling.

## The cheapest route we would keep, per kind of thing

| Kind | Cheapest kept route | Cost per kept model | Why it, and what to watch |
|---|---|---|---|
| Small solid prop (the canoe) | Trellis, $0.02 | $0.02 | One closed piece of 3,258 triangles, right outline and colour; softer texture than H3.1. Trellis 2 ($0.05) has the better texture if that matters. |
| Weapon head (the glaive) | Hunyuan 3.1 rapid, $0.015 | $0.015 (about $0.02 if one in four is refused and resent) | The crispest flaking of all seven heads, one closed piece. Needs a reference under 950 KB and a cut from 50,000 to about 12,000 triangles. |
| Building (the hut) | Trellis, $0.02, after clean-up | $0.02 | Door, windows, roots and roof all read; 13 loose pieces to remove. Idol max turbo ($0.10) is the richest hut if the extra cost buys a look you want. |

Across all three kinds, the cost per kept model by route was: Trellis $0.03 (2 of 3 kept), Trellis 2 $0.075 (2 of
3), Hunyuan 3.1 rapid $0.015 (1 of 1 that ran), Idol max turbo $0.10 (3 of 3), Hunyuan 2 textured $0.24 (3 of 3),
Tripo H3.1 detailed $0.40 (3 of 3).

## What $90 would buy

| Route mix | Generation cost per kept model | Kept models for $90 (generation only) | With one $0.12 reference image each |
|---|---|---|---|
| Tripo H3.1 detailed for everything, as now | $0.40 | about 225 | about 170 |
| Trellis for props and buildings, Hunyuan 3.1 rapid for weapon heads | about $0.03 | about 3,000 | about 600 |
| Trellis 2 for props, Hunyuan 3.1 rapid for weapons, Idol max turbo for buildings | about $0.07 | about 1,300 | about 470 |
| Two tries of the cheap mix per thing, the better one kept | about $0.06 | about 1,500 | about 500 |

With the cheap routes, generation stops being the cost that matters: the reference image ($0.12 at 2K) costs four
to eight times the model, and our time to look, shape and clean each one bounds the count long before $90 does. A
sensible budget is several cheap tries per thing from one reference image, keeping the best.

## What this changes

1. Use Trellis first for props and buildings and Hunyuan 3.1 rapid first for weapon heads; go to Tripo H3.1
   detailed only when the cheap result fails the look.
2. Save every reference image as a JPEG under 700 KB before sending it, so Hunyuan 3.1 rapid accepts it.
3. A "bare" Tripo H3.1 request still came back painted, so it buys nothing over the textured one for $0.20; our
   shared material can go on any route's shape instead.

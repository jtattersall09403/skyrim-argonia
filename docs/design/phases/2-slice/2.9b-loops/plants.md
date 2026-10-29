<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/plants.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9b plants: survey and node placements (lane 2.9b-p)

Survey written before the first measure; rows carry the elapsed time. Owner steer 1: author, assign and fill many more plant containers from what is already built.

## Survey (elapsed from lane start 18:40)

| step | finding | elapsed |
|---|---|---|
| slice ingredients the ecology grows | fauna-hazards.md:96-101 (Flora, CANON_EXPLICIT) names dragon's-tongue, somnalius fern, marshweed, blue moss canopies, "fields of ferns and flowered grasses", nirnroot. Rows with a node already: somnalius-frond, marshweed, hanging-moss, dried-flower-buds, rootland-mushroom, swamp-fungal-pod. New: nirnroot. The other Skyrim plants (canis root, deathbell, fly amanita, giant lichen, imp stool, jazbay, lavender, taproot, thistle, white cap) have no Black Marsh line in the dossiers, so they get no node. | 5 min |
| species with three LOD tiers (kit manifests, `lodLevels`) | nirnroot01 3 (interior-farmhouse-v1); floradragonstongue01/02 1 (xanmeer-kotm-v1; `lodRatios` lists two ratios but the GLB carries one level); florasomnaliusfern01 3 (interior-kotm-v1, not needed); meadowsweet clusters 1; floramushroom02/05/06 1. | 15 min |
| where the region grows each plant | the frozen scatter, which was compiled per region from the ecology: inside each slice place's radius and outside its vegetation clearance (ground-overlays.json) there are frozen ferns, blue moss, fungal pods, tall mushrooms and reed tufts of the node species. These instances are the region's own plants, so a plant socket on one of them needs no new piece and no publish. | 25 min |
| bundle placements already of a node-family species | reedmed1 (4 tiers) 2 at upriver and 5 at opening-work-camp, at the water's edge; espfernbrakencluster04 (4 tiers) 4 at upriver. These join marshweed and somnalius-fern in the record. | 30 min |

## Lore line per node kind

| node | lore line | species placed or socketed |
|---|---|---|
| node.somnalius-fern | fauna-hazards.md:98 "somnalius fern", :99 "fields of ferns" | frozen espfernbrakencluster01/05, espfernbraken01st, braken, fern01, fernlarge03; placed espfernbrakencluster04 |
| node.hanging-moss | fauna-hazards.md:99 "blue moss canopies" | frozen florahangingmoss02aaa/03aaa |
| node.marshweed | fauna-hazards.md:99 "marshweed (smoked)" | frozen reedsmall2; placed reedmed1 |
| node.swamp-fungal-pod | resource-nodes.json row (cites ecology-encounters-loot.md:36, a heading; no Black Marsh line names the pod: a gap for the record owner) | frozen floraswampfungalpod01 |
| node.rootland-mushroom | resource-nodes.json row (same weak cite) | frozen tr_oth_tallmush01 |
| node.nirnroot | fauna-hazards.md:101 "nirnroot"; UESP Lore:Nirnroot "a very rare plant that grows near water" (citing The Improved Emperor's Guide to Tamriel: Black Marsh) | placed nirnroot01, one, at the Greenspring spring |
| node.dragons-tongue | fauna-hazards.md:97 | none: no species with three LOD tiers (kit-build job) |
| node.mountain-flower | material-culture.md:153 | unchanged (reader: the cluster reads grey; material, not placement) |

## Plant sockets added (each `why` names the species, the frozen instance and the lore line)

| place | socket | species | x, z | lore |
|---|---|---|---|---|
| bog-iron-workings | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss03aaa | 2003.93 , 2564.4 | fauna-hazards.md:99 |
| bog-iron-workings | plant-somnalius-fern-1 | bmv:landscape/plants/espfernbrakencluster05 | 1971.76 , 2551.26 | fauna-hazards.md:98 |
| bog-iron-workings | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster05 | 1996.01 , 2585.65 | fauna-hazards.md:98 |
| bog-iron-workings | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 1992.1 , 2588.95 | fauna-hazards.md:98 |
| bog-iron-workings | plant-swamp-fungal-pod-1 | vanilla:plants/floraswampfungalpod01 | 1954.96 , 2553.8 | resource-nodes.json node.swamp-fungal-pod |
| bog-iron-workings | plant-swamp-fungal-pod-2 | vanilla:plants/floraswampfungalpod01 | 1968.9 , 2523.32 | resource-nodes.json node.swamp-fungal-pod |
| bog-iron-workings | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss02aaa | 1947.82 , 2531.14 | fauna-hazards.md:99 |
| claywater-station | plant-somnalius-fern-1 | bmv:landscape/plants/braken | 334.12 , 3020.66 | fauna-hazards.md:98 |
| claywater-station | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss03aaa | 327.16 , 3010.55 | fauna-hazards.md:99 |
| claywater-station | plant-somnalius-fern-2 | bmv:landscape/plants/fernlarge03 | 332.19 , 3050.87 | fauna-hazards.md:98 |
| claywater-station | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 296.52 , 3019.32 | fauna-hazards.md:98 |
| claywater-station | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss03aaa | 300.99 , 3003.35 | fauna-hazards.md:99 |
| greenspring | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss03aaa | 4773.67 , 1865.54 | fauna-hazards.md:99 |
| greenspring | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss03aaa | 4775.39 , 1869.63 | fauna-hazards.md:99 |
| greenspring | plant-somnalius-fern-1 | bmv:landscape/plants/espfernbrakencluster05 | 4768.73 , 1880.95 | fauna-hazards.md:98 |
| greenspring | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster05 | 4774.25 , 1876.59 | fauna-hazards.md:98 |
| greenspring | plant-somnalius-fern-3 | bmv:landscape/plants/fernlarge03 | 4729.78 , 1897.02 | fauna-hazards.md:98 |
| lighter-flotilla | plant-marshweed-1 | bmv:landscape/trees/reedsmall2 | 3825.45 , 6394.9 | fauna-hazards.md:99 |
| lighter-flotilla | plant-somnalius-fern-1 | bmv:landscape/plants/fern01 | 3831.31 , 6330.15 | fauna-hazards.md:98 |
| lighter-flotilla | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster05 | 3832.55 , 6325.9 | fauna-hazards.md:98 |
| lighter-flotilla | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 3852.19 , 6311.51 | fauna-hazards.md:98 |
| naga-highway-camp-active-north | plant-rootland-mushroom-1 | bmv:trdata/mushrooms/tr_oth_tallmush01 | 2321.73 , 4591.65 | resource-nodes.json node.rootland-mushroom |
| naga-highway-camp-active-north | plant-swamp-fungal-pod-1 | vanilla:plants/floraswampfungalpod01 | 2322.32 , 4585.31 | resource-nodes.json node.swamp-fungal-pod |
| naga-highway-camp-active-north | plant-somnalius-fern-1 | bmv:landscape/plants/espfernbrakencluster01 | 2295.85 , 4580.21 | fauna-hazards.md:98 |
| naga-highway-camp-active-north | plant-rootland-mushroom-2 | bmv:trdata/mushrooms/tr_oth_tallmush01 | 2324.88 , 4594.61 | resource-nodes.json node.rootland-mushroom |
| naga-highway-camp-active-north | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster01 | 2297.75 , 4575.55 | fauna-hazards.md:98 |
| naga-highway-camp-active-north | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 2345.94 , 4579.05 | fauna-hazards.md:98 |
| naga-highway-camp-active-north | plant-swamp-fungal-pod-2 | vanilla:plants/floraswampfungalpod01 | 2281.96 , 4558.72 | resource-nodes.json node.swamp-fungal-pod |
| naga-highway-camp-active-north | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss02aaa | 2265.5 , 4564.74 | fauna-hazards.md:99 |
| opening-work-camp | plant-somnalius-fern-1 | bmv:landscape/plants/espfernbrakencluster05 | 3948.7 , 1383.69 | fauna-hazards.md:98 |
| opening-work-camp | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster05 | 3945.66 , 1380.87 | fauna-hazards.md:98 |
| opening-work-camp | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 3943.48 , 1384.26 | fauna-hazards.md:98 |
| opening-work-camp | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss03aaa | 3929.2 , 1405.31 | fauna-hazards.md:99 |
| opening-work-camp | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss03aaa | 3923.46 , 1406.52 | fauna-hazards.md:99 |
| pearl-lots | plant-marshweed-1 | bmv:landscape/trees/reedsmall2 | 5398.75 , 4301.55 | fauna-hazards.md:99 |
| pearl-lots | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss02aaa | 5394.93 , 4284.28 | fauna-hazards.md:99 |
| pearl-lots | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss02aaa | 5375.38 , 4284.88 | fauna-hazards.md:99 |
| pearl-lots | plant-marshweed-2 | bmv:landscape/trees/reedsmall2 | 5345.56 , 4327.55 | fauna-hazards.md:99 |
| pearl-lots | plant-somnalius-fern-1 | bmv:landscape/plants/fern01 | 5346.0 , 4316.62 | fauna-hazards.md:98 |
| pearl-lots | plant-somnalius-fern-2 | bmv:landscape/plants/braken | 5420.37 , 4253.42 | fauna-hazards.md:98 |
| pearl-lots | plant-marshweed-3 | bmv:landscape/trees/reedsmall2 | 5326.48 , 4344.86 | fauna-hazards.md:99 |
| pearl-lots | plant-somnalius-fern-3 | bmv:landscape/plants/braken | 5420.99 , 4217.29 | fauna-hazards.md:98 |
| the-wamasu-shrine | plant-somnalius-fern-1 | bmv:landscape/plants/espfernbraken01st | 4726.51 , 945.76 | fauna-hazards.md:98 |
| the-wamasu-shrine | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbraken01st | 4732.45 , 938.54 | fauna-hazards.md:98 |
| the-wamasu-shrine | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbraken01st | 4737.94 , 926.92 | fauna-hazards.md:98 |
| upriver-hist-village | plant-hanging-moss-1 | bmv:landscape/plants/florahangingmoss03aaa | 3412.48 , 1424.74 | fauna-hazards.md:99 |
| upriver-hist-village | plant-somnalius-fern-1 | bmv:landscape/plants/braken | 3371.9 , 1447.83 | fauna-hazards.md:98 |
| upriver-hist-village | plant-somnalius-fern-2 | bmv:landscape/plants/espfernbrakencluster05 | 3367.84 , 1459.32 | fauna-hazards.md:98 |
| upriver-hist-village | plant-somnalius-fern-3 | bmv:landscape/plants/espfernbrakencluster05 | 3375.99 , 1467.4 | fauna-hazards.md:98 |
| upriver-hist-village | plant-hanging-moss-2 | bmv:landscape/plants/florahangingmoss03aaa | 3424.98 , 1385.39 | fauna-hazards.md:99 |
| greenspring | plant-nirnroot (host node-nirnroot, placed) | vanilla:plants/nirnroot01 | 4717.0 , 1863.6 | fauna-hazards.md:101; UESP Lore:Nirnroot |

Not done: rose-bone-waystation has one frozen node-species plant in reach, already socketed; voriplasm-vault's layout is open in a place-builder lane.

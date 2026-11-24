# New-art research for the lead, 2026-11-24 (read-only; nothing generated or bought)

Live docs: docs/research/new-art/PROPOSAL.md (the one doc to edit), cost-experiment.md, visual-consistency.md (evidence
for part C; still valid), tooling.md (prices, now partly contradicted below). PROPOSAL.md was last rewritten in b7589a403
(11:46 UTC), BEFORE the experiment (17c66b55b) and BEFORE the index landed (529786e3c), so it is stale in places.

## FINDINGS FIRST
1. The proposal did NOT move part C after E (PROPOSAL.md:308-323 order is A,B,C,D,E,F,G; section 6 options have no
   "A to E without C" cut). Missed.
2. The cost-experiment prices contradict Fal's pages read today. cost-experiment.md:21,23 and the "$90 buys ~600" table
   (lines 46-52) use Trellis 2 $0.05 and Hunyuan 3.1 rapid $0.015. Fal pages today: Trellis 2 "$0.25 for 512p, $0.30 for
   1024p and $0.35 for 1536p"; Hunyuan 3.1 rapid "$0.225 per generation" ($0.375 with PBR); tooling.md:133 and PROPOSAL.md:260-261
   still say $0.25 / $0.225. The explorer json (newworld/sources/art/dugout-canoe.json:292-358) records price_usd with no
   endpoint id, so the source of $0.05/$0.015 cannot be traced. Until traced, the "600 models" claim is UNVERIFIED and likely wrong
   for those two routes (Trellis $0.02 and Idol $0.10 not re-read except Trellis: "$0.02 per generation", VERIFIED).
3. Tripo's "plan credits cannot pay for the API" is PARTIAL: I could not open Tripo's help/pricing/terms (all 403). A search
   of Tripo's official help index returned "How do credits work?" with the line that Web App credits are not API credits, and
   a May 2026 third-party article says the same; CostBench (Tripo page paraphrase, checked 21 Nov) quotes Tripo: "API Pricing:
   Available for developers and companies, usage-based, and separate from consumer plans." Tripo's API page itself (read today)
   says "usage-based" and "1 credit = $0.01 USD". Which balance tripo-cli/MCP spends is not documented (unknown).
4. Meshy is not a cheaper route to H3.1-grade textures: its textured model costs 30 credits (35 at 8K) and a credit costs
   $0.0125-0.02 depending on plan, i.e. $0.375-0.60 per textured model, and Fal lists Meshy 6 at $0.80. It does have the best
   retexture endpoint for part C (style image, original UV kept, 2K/4K/8K).
5. The proposal's plan for generators ("replace the texture with shared repeating materials") has no way to pick which
   part gets which material: tools/newart/surface.py wrap() box-projects ONE material over the whole mesh from face normals.
   The owner's objection stands; part C below gives the options.

## A. AUDIT of the owner's comment 7129805179 (status: done / answered / half / missed)
Evidence lines are in PROPOSAL.md (P) unless named. "Answered" = said in P or the issue comment, nothing built.

| His words | Status | Evidence | Still owed |
|---|---|---|---|
| "door finder tool isn't great, try having agent pick/shade it by hand" | half | P:162-169 says it is dropped; but tools/newart/building.py:1-4,16 still auto-finds the door (largest flat patch); no by-hand tool; not tried on any model | build the hand-pick tool, rerun on the hut, check from side |
| "Cost $7.07 too expensive... work out how to do the full amount affordably" | half | cost-experiment.md exists; P:226-281 still reads as a plan ("about $5", "Fal out of credits" P:371,388) though the experiment ran | P cost section stale; prices contradicted (finding 2); no per-kind cost at scale that survives re-pricing |
| "Tripo plan/subscription - see below... compare options" | half | P:245-249 dismisses Max on a help page the agent could not open (tooling.md:111 says pricing page 403); experiment (cost-experiment.md:18-25) has no Tripo-plan or Meshy route | part B below: costed routes; a real test of the web-studio route |
| "alternative cheaper models through fal... tailored to complexity" | done | cost-experiment.md:18-40 | re-price (finding 2); owner has since ruled H3.1 best, so cheap routes only for what he accepts |
| "What experiment... few dollars... extrapolate" | done | cost-experiment.md; $-per-kept-model table 39-41 | n=1 per cell; no whole-weapon or hybrid-shaft run though P:264 promised "the glaive as one whole weapon" (absent from cost-experiment.md) |
| Custom shafts: socket matches head, "what do you think... try?" | half | P:171-184 recommends hybrid (answered); tools/newart/polearm.py is the hand pole only | nothing tried: no hand shaft with grip/wear, no generated-shaft comparison |
| "rule should be 'no moving parts'" | done | P:155-160 states it in his terms with coil/taut exceptions | check the three reference-image prompts follow it |
| "message to King of the Murkmire's author? no" | done | P:378-379; issue comment 7130540192 | none |
| Sick/dying Hist: "pretty sure we already had this covered" | answered | P:83 and comment cite the "sick Hist bark" block; the block is real: docs/design/blocks.md, newworld/places/jal-veesa/spaces/exterior/refs.jsonl and quests.jsonl mention it | "even for one or two drafted places": only Jal-Veesa confirmed; not checked that it renders |
| Plant swaps ok; no BM&V bamboo; be cautious | answered | P:290-293 (allowed, bamboo never placed) | nothing enforces "never place BM&V bamboo": no row found excluding it in newworld/sources/stock (grep shows only bamboo wood/bows) |
| Obsidian: use Xanmeer, recolours only for gaps | done | commit b5722260f; P:81 | none |
| Index: "haven't we done this? how does it work? if incomplete, crack on" | done, but doc stale | issue comment explains text-only; 529786e3c built the look index (19,385 models, CLIP, `search sheet`; docs/design/place-studio.md Search); have-get-make.md points to it | P:51-64 and P:25 still say "being built"; the promised acceptance test (each wrongly-called-missing item in top ten) has no recorded result: no such test in tools/tests/test_places_search_look.py or docs |
| "Root-grown hut - more than huts? more than one hut model?" | answered | P:336-351: seven building kinds, 2-3 variants each, 15-20 models | none beyond building them |
| "do we need a different word for larger multi-floor root-grown buildings?" | missed | P uses "hut", "house", "hall", "store" in a table (P:341-349) but never answers the naming question | give him the words (e.g. hut / grown house / longhouse / granary) and use them everywhere |
| "shops and inns and whatever other non-house buildings" | missed | only "a guild or a hostel" (P:345); no shop, inn, smithy, temple, shrine, hall of any kind | list non-house building types from the places' needs |
| Blender: "one session owns many things" | answered | P:122-134 warm daemon, family batches, 2-3 in parallel | nothing built (tools/newart has no daemon); fine as a plan |
| Studio actions "I would like to do things myself" | answered | P:219-224: each action as button and as look action | nothing built; no list of which first |
| Interior planning "measure more... think like a designer: bed? where? table? shelves? what on them? wall decor? linked to quests, what the room is for, who owns it, the place" | missed in P; half in research | P:148 and P:353-355 are one line; interior-dressing.md measures item/surface relations over 112 rooms (lines 108-162) and kit zones (195, 283) but not room-programme decisions, ownership, quest hooks | a room-design layer: per room type and owner, what it must/may contain, tied to the people, needs and quest rows |
| "Dressing rooms well... what about interiors that aren't houses?" | missed | interior-dressing.md:109 sample drops inns, guardhouses, cellars: "112 houses and huts" | measure inns, shops, temples, smithies, barracks, ruins, caves |
| "Tell me specifically how guidelines could not be read by machine... with links" | missed | P no longer says it; interior-dressing.md:49 names wiki.project-tamriel.com/wiki/Interior_Guidelines (403 to me again today); interiors.md:47 names tamriel-rebuilt.org/node/6845 and /node/6455 (Morrowind, unread); interior-dressing.md:303 "fetch from an unblocked machine" | give him those links and say the 403 is bot-blocking; ask him or the build VM browser to save the pages |
| "Is shared-texture right? Tripo textures look great... how know which bits are which material? is that what Tripo does anyway? recolour per material?" | missed in P; half in the explorer | P:186-192 unchanged; dugout-canoe.json:206 says "on this object the generated texture looks better"; owner has since ruled the shared texture worse | part C |
| "Why can generators not make cloth or leaves? is it leaves in Skyrim's engine?" | missed | P silent; the reason exists in nature-and-vessels.md:284: Skyrim foliage is alpha-cut cards, a generator makes one opaque mesh with a baked texture (so thin leaves thicken); cloth not covered | answer plainly: yes, Skyrim leaves are flat cut-out cards (alpha-test) so a solid tree mesh works as a distant or hero tree only; cloth must deform on a skinned body |
| "Hierarchy: you can approve level 0, 1 and 4 for me" | missed | P:204-208 still lists "you" for levels 0, 1, 4 | rewrite so he approves 2 and 3 only |
| "Do as much as possible off game... high confidence" | half | P:138-150 stage table is off-game but ends "In game: your check"; no statement of which differences off-game cannot catch | write the off-game check list and known blind spots; the vanilla ranges are not even measured yet (skyrim-asset-pipeline.md:263,276 "Real vanilla texel density" still a to-do) |
| "I don't understand: carpentry and masonry are a hand-designed snap-together kit of about 24 pieces..." | missed | the sentence is gone from P (grep "24" none); never explained; source is buildings.md:255,335 (Kit A, 24 pieces; grey-box three buildings) | one plain-English paragraph: a kit is a small set of standard wall/floor/roof pieces that snap on a grid so many buildings are built from them |
| "Buildings enter a place... seated on whatever the previous building was seated on (a platform)? design our buildings from the source places?" | half | P:353-356 repeats "source brought in whole, ours swapped in at adapting"; buildings-in-places.md:22,121 has `seat {mode, on}` and door anchoring (254) so seat-on-platform exists in the tool; but the design-from-source-places idea, with match-closeness vs reuse balance, is not addressed | answer both; say which source building types (platforms, stilts) our family must fit |
| Moss: "why would Bethesda have 1,017 things using a material not shipped?" | missed | the claim was deleted, not answered: it was in 02eafd61f PROPOSAL ("The file its moss material names... 1,017 vanilla statics"), absent in b7589a403 and every doc now (grep) | answer: records flagged "single pass" draw from their own colour so the file is never loaded (that is what the old text said about the flag) and the statics use snow/ash materials; mark UNVERIFIED until measured |
| "Move 'things genuinely missing' after D and E; do A-E (excl. C) first as minimal new art" | missed | see finding 1 | reorder; add "A,B,D,E" as the minimal option in section 6; and note D (new plant cards) and E need no generator |
| "reed or sedge clump set... we don't need this" | missed | P:315 still lists "reed, sedge and rice clump sets as hand-built cards" | delete |
| "'A walkable box, then a root-grown hut with a two-room interior...' more than a hut?" | answered by dropping | the phrase is gone; family table P:336-351 | covered by the naming row |
| "I'd like to see the workshop and proofs; will decide after rewrite" | done | P:31,362 | none |
| "Rewrite the plan whole and post an update" | done | b7589a403; comment 7130540192 (and 7131456436 for the experiment) | the later experiment is not folded into P |

Count: done 7, answered 4, half 7, missed 11 (of 29 rows). The previous agent's acknowledgement comment 7129839013 promised
every item; the ones missing are the ones that needed new writing rather than a one-line rule.

## B. GENERATOR MONEY (every price read on a page on 2026-11-24 unless marked)
Pages I could NOT open (403/404): tripo3d.ai/pricing, /terms, /help/credit/*, developers.tripo3d.com model pages,
meshy.ai/terms (404), wiki pages. Tripo web plan figures below are from CostBench/other third parties (marked 3P).

### Tripo
- API page https://developers.tripo3d.ai/en/pricing (read today): "1 credit = $0.01 USD"; image to 3D 20 credits no texture,
  30 standard; add-ons HD Texture +$0.10, Ultra Texture +$0.20, HD Geometry +$0.20, Quad +$0.05, Parts +$0.20; texture-only task
  Fast/Standard $0.10, HD $0.20, 8K Ultra $0.30; Image to Multiview $0.10; Segmentation $0.40; Smart Segmentation $0.55-0.85.
  Top-up presets $50/$100/$250, custom from $1. The page does not split by model version (H3.1 vs P2).
- Fal H3.1 page (read today): $0.20 untextured, $0.30 standard, $0.40 HD textures, +$0.20 detailed geometry, +$0.05 quad.
  So H3.1 on Fal = Tripo's own API list price ($0.40 HD): previous agent's "same per model" is VERIFIED. Tripo direct also
  offers things the Fal page lists no parameter for: 8K Ultra texture, multiview, parts, segmentation, texture-only retexture.
  Fal Tripo P2 (read today): $1.00 none, $1.10 standard, $1.20 detailed, $1.30 extreme.
- Plans (3P CostBench, checked 21 Nov; Tripo page 403): Free 200 credits (~13 models), Pro $20/mo or $240/yr, 3,000 credits (~200 models),
  Max $90/mo or $1,080/yr, 25,000 credits (~1,660 models), Team $110/user/mo. A search snippet of Tripo's own pricing page says
  Max "25000 credits (up to 1000 models)" and shows $89.9 monthly. "Unlimited 8K textures" only from a third-party review; Tripo's
  May blog gives "one free 8K texture trial". Free plan: public, non-commercial (3P, Tripo pricing recap Oct 2026).
- What a web-studio model costs in credits is UNKNOWN: 200 credits = 13 models implies 15 credits, but the API charges 30 for a
  standard-textured model and 40 for HD. At API credit costs, 25,000 credits = 833 standard or 625 HD models, not 1,660.
- Can subscription credits pay the API? Official help article title "How do credits work?" says web app credits are not API
  credits (search snippet only, page unread); Tripo API page: usage-based, separate. PARTIAL.
- Terms on ownership/automation: UNKNOWN (403). Third-party paraphrase: paid users get broader rights to inputs and outputs "subject
  to compliance and service authorization". Driving the web studio by browser agent is not addressed in anything I read: UNKNOWN.
- One month and cancel: $90 is quoted as the monthly rate (3P); cancel terms unread: UNKNOWN. The credits would be wasted if not
  spent in the month (monthly credits "reset" is Meshy's wording; Tripo's unread).

### Meshy
- https://www.meshy.ai/pricing (monthly billing, shown in GBP to me): Free 100 credits; Pro £16/mo 1,000 credits; Premium £32 3,000;
  Ultra £80 8,000; Studio £56 5,500 shared + £8/seat. Help article https://help.meshy.ai/en/articles/12062933: "Pro ($20/mo),Premium ($40/mo),Ultra ($100/mo)".
  API access is listed from Pro up ("API & MCP"); API rate 20 requests/second; API asset retention 3 days on Pro/Premium/Ultra.
- API credit costs https://docs.meshy.ai/en/api/pricing: image to 3D meshy-6 / meshy-7.1: 20 mesh only, 30 at 2K and 4K, 35 at 8K; lite 5 / 15;
  multi-image same; Retexture 10 credits at 2K/4K, 15 at 8K. "The Meshy API uses prepaid credits. Before you send API requests, buy
  API credits in your subscription settings." No page I read says whether the plan's monthly credits are spendable on API calls, or the
  dollar price of an API credit: UNKNOWN. Failed API tasks refunded (usage docs).
- Dollars per textured model if a credit is the plan's price per credit: Pro $20/1000 = $0.60; Premium $40/3000 = $0.40; Ultra $100/8000 = $0.375
  (8K: $0.44). $90 buys: Ultra month 266 (4K) or 228 (8K); two Premium months 200. Fal Meshy 6: "$0.8 per generation" = 112.
- Commercial: paid plans "Private", "full commercial use", "You own the output" (https://docs.meshy.ai/en/webapp/pricing); Free CC BY 4.0.
  Terms page 404: ownership beyond that unread.
- Texture resolution: 2K/4K/8K options (retexture doc); remove_lighting default true on meshy-6.

### Others
- Rodin/Hyper3D: Fal $0.40 a generation, sample textures 1024x1024 (read today). Direct (hyper3d.ai/pricing): Creator $30/mo ~60 models,
  no API; Business $120/mo ~416 models, full API ($0.29 a model if all used); direct credits $1.5 each. Credits-to-API link unstated.
- Hunyuan 3D on Fal: v3.1 pro $0.375 ("PBR, multi-view, custom face count each +$0.15"), v3.1 rapid $0.225 (+$0.15 PBR). Tencent direct
  ~$0.38 a model (3P, 3daistudio 1 Nov; unread primary).
- Trellis on Fal: Trellis $0.02; Trellis 2 $0.25/$0.30/$0.35 by resolution (tooling.md says textures 1024/2048/4096).

### $90 routes around H3.1 quality
| Route | Models per $90 | Fragile | Terms risk |
|---|---|---|---|
| H3.1 HD on Fal ($0.40) | 225 (187 with an $0.08 reference image each; 150 with HD geometry too) | none; Fal account out of credits earlier (#95); no 8K, no multiview parameter shown | Fal says "Commercial use" on Rodin; Tripo licence via Fal UNVERIFIED (tooling.md:19-20) |
| H3.1 on Tripo's own API ($0.40, or $0.30 standard) | 225 / 300; Ultra texture +$0.20 -> 150 | needs a new account and top-up (min $1; unknown credit expiry) | API outputs: Tripo claims commercial rights (tooling.md:114-116, snippet) |
| Tripo Max month ($90) in the web studio | 625-833 at API credit costs; 1,000 per Tripo snippet; 1,660 3P claim | agents drive a web page or a community plugin (tooling.md:60, 68 tools, unofficial); web credits may not pay CLI/MCP; hours-long task queues; month wasted if unused | UNKNOWN; automating the web app may breach terms (unread) |
| Tripo Pro month ($20) x4 | 800 at 3,000 credits each if 15 credits a model; 400 if 30 | same as Max | same |
| Meshy Ultra month ($100) / Premium x2 ($80) | 228-266 / 200 | API credits maybe separate pool; 3-day API file retention | owner of output on paid plans; terms unread |
| Meshy on Fal | 112 | none | none read |
| Rodin on Fal ($0.40) | 225 | 1024 textures | none read |

Verdict: nothing beats H3.1 at about $0.40 per kept model unless the Max web credit cost per model is under about 40 credits and the
web route is permitted. That one fact (credits charged per H3.1 HD/8K model in Tripo Studio, and whether a browser/CLI agent
may spend them) is the thing to find out, from a logged-in Tripo account or by asking Tripo support, before buying Max.

## C. CONSISTENCY WITHOUT DISCARDING THE TEXTURES
Evidence base: docs/research/new-art/visual-consistency.md (vendor material; no independent postmortem of a shipped AI 3D set exists in
what it found; no vanilla-matching recipe exists). New reads today: Tripo texture API (via Comfy/Alibaba/3daistudio mirrors, official
page unreadable), Meshy retexture docs, PartField.

What a Tripo texture is: one unique UV atlas per model (nothing like a tiled shared material), so texel density rises and falls with the
model's size (owner is right that our "constant pixels per metre" plan is a different thing). Skyrim uses small tiled textures plus
vertex-colour tint; 2K over 1/3/8/20 m = 2048/683/256/102 px/m (skyrim-asset-pipeline.md:45). Vanilla is mostly 512-1024 (Nexus mod
pages, snippet-level); the real vanilla density is not measured (skyrim-asset-pipeline.md:263).

| Method | Cost per model | Tool | Off-game check | Likely effect / evidence |
|---|---|---|---|---|
| 1. Per-material grade of Tripo's own albedo: split the atlas into regions, shift each region's Lab mean/std toward a palette taken from vanilla textures of that material | $0 (CPU) | numpy/skimage in tools/newart; regions by: (a) colour k-means on the albedo, (b) UV islands, (c) agent-painted face labels, (d) PartField or Tripo segmentation | line-up beside vanilla under the studio renderer + numbers: palette distance, value/saturation percentiles vs measured vanilla band | best fit to the owner's ask; Lab-space grade from palette preferred to per-channel histogram match (hue shifts; scikit-image docs); k-means on a generated albedo is cheap but mixes materials of the same colour; (c) is exact but is hand time |
| 2. Part segmentation for material masks | Tripo Generate Parts +$0.20 or Segmentation $0.40; PartField free (NVIDIA, class-agnostic feature clusters; needs a connected mesh, generated meshes often are not: PartSAM paper) | Tripo API, PartField on CPU/GPU | colour-coded part render, owner or agent checks 3-5 parts | gives which bits become which material; Tripo texture task accepts `part_names` from a segmentation task (3P mirrors, Alibaba docs: names like tripo_part_0) |
| 3. Anchor model as style reference for siblings | reference image generation $0.08 (Nano Banana 2 edit, up to 14 refs) + H3.1 $0.40 | Fal; Tripo multiview $0.10 | line-up of the family | Fal's own guide says reference editing "drifts after a few generations": always anchor to the approved hero, never the last sibling; no measured result on 3D sets anywhere |
| 4. Retexture from a style image | Meshy retexture 10-15 credits (~$0.13-0.20 at Premium/Ultra rates); Tripo texture $0.10-$0.30 | Meshy `image_style_url` (one of text/image/multiview), `enable_original_uv`, 2K-8K; Tripo `texture_model` (`style_image` only together with text; reference images only on Tripo-made models) | before/after turntable, geometry hash unchanged (Meshy doc does not state geometry is preserved: check) | repaints from a prompt so detail is the generator's, not ours; Meshy's doc warns "Textures may fit poorly when the image's object has a very different shape" |
| 5. Texel-density and map normalisation | $0 | Blender/numpy: resample atlas to target px/m, add normal strength, specular from roughness | numeric: px/m, size, normal mean | cheap and certain; but atlas density cannot be made constant by resampling alone: needs re-UV or UV-scale per island |
| 6. Shared detail normal/grime overlay | $0 | one tiling detail-normal and soot map multiplied over the atlas by UV island mask | line-up | Skyrim's own method for sameness; works only with segmented regions (method 2); tiled overlay on an atlas needs per-island UV scale |
| 7. Vertex-colour dirt (Skyrim style) | $0 | Blender vertex paint from curvature/AO + height | line-up in the studio renderer if it shows vertex colour (UNVERIFIED: pipeline doc asks it, skyrim-asset-pipeline.md:261) | matches vanilla; subtle; does not unify hue |
| 8. Shared repeating material (current plan) | $0 | surface.py wrap | owner has ruled it looks worse | no segmentation, so one material for the whole mesh |

How off-game approval holds in game (my inference, no source): game lighting and shaders change brightness, not hue relationships; so approve
palette distance, value/saturation band, px/m and a line-up beside vanilla pieces in one fixed renderer; keep a single in-game spot check per
family, as the owner has already accepted lighting risk.

### Recommended test, under $3, on the canoe, hut and glaive already in the explorer
1. Method 1 with 2(c)/(a): grade each H3.1 albedo (canoe: wood + lashing; hut: bark/root + thatch + door; glaive: stone + binding + shaft)
   toward a palette sampled from three vanilla neighbours per material; $0. Needs the vanilla palette/density measurement first (CPU
   job over the catalogue; also fixes the open to-do at skyrim-asset-pipeline.md:263). Pass test: palette distance falls, character (relief,
   wear pattern) unchanged, owner approves the line-up.
2. Method 4: Meshy retexture (or Tripo texture endpoint) of the already-cleaned hut mesh with the canoe's graded texture as style image;
   about $0.15-0.30 each, three tries under $1. Needs a paid Meshy month or a $1+ Tripo API top-up. Tests whether a retexture endpoint
   keeps geometry and gives sibling consistency.
3. Method 3 on the glaive: one anchor reference + Nano Banana 2 edit to make two sibling references ($0.16), then H3.1 HD twice ($0.80);
   total about $1; compare the three in one line-up. Optional extra: Tripo Generate Parts $0.20 on the hut to test method 2.

## Covered / not covered
Covered: PROPOSAL.md whole, cost-experiment.md, visual-consistency.md, the #94 owner comment and agent comments, git history of PROPOSAL.md,
tools/newart (building.py, surface.py headers), docs/research/new-art grep, Fal model pages (Tripo H3.1, P2, Meshy 6, Rodin v2, Trellis,
Trellis 2, Hunyuan 3.1 pro/rapid), Meshy pricing/API/retexture/usage/webapp pages, Tripo API pricing page, Rodin pricing, 3P: CostBench, 3daistudio,
aifreeapi, search snippets for Tripo help. Skipped/blocked: tripo3d.ai/pricing, terms, help pages, developers.tripo3d.com docs (403);
meshy.ai/terms (404); wiki.project-tamriel.com (403); Tencent and hyper3d API docs (not reached); fal-ai/hunyuan3d-v21 (404); Fal Meshy retexture
and Tripo texture on Fal (no page found); I did not run any ESM reader to test the moss claim.

# ADDENDUM (coordinator's three follow-ups), 2026-11-24

## 1. Interior guidelines with links
Rule followed: where a site refused an ordinary fetch I stopped. Every page below returned HTTP 403 to my fetch, so the quotes are
the SEARCH ENGINE's summaries of them, not text I read on the page; mark them as such. Nothing readable by me exists for Beyond Skyrim.

URLs for the owner to open himself (all refused me, all appear in search results):
- Project Tamriel (current rules): https://wiki.project-tamriel.com/wiki/Interior_Guidelines ; also .../Hlaalu_Interior_Guidelines, .../Indoril_Interior_Guidelines,
  .../Redguard_Reach_Interior_Guidelines, .../Daedric_Ruin_Guidelines (same host; the general page has a "Tapestries" section).
- Tamriel Rebuilt (older, marked outdated, point at the wiki above): https://tamriel-rebuilt.org/node/397 (Guidelines for Interior Showcases),
  /node/6845 (Hlaalu Interior Style Guide), /node/6042 (Daedric Ruin Style Guide), /node/6455 (Chimer Stronghold Style Guide),
  /forum/int-dev-cheatsheet, /node/379 (Interior Modding Tutorial), /old_forum/viewtopic.php?p=323938 (Interior Showcase Guidelines, 11 Aug 2014).
- Reviewer threads (what actually gets rejected): https://www.project-tamriel.com/viewtopic.php?t=2254 and ?t=3226; https://tamriel-rebuilt.org/node/5430, /node/6275, /node/10438
  (interior showcases with reviewer comments); https://tamriel-rebuilt.org/node/4475 (a review checklist headed "Clean / Northmarker / Fits Exterior / Illegal to Sleep Here / Lighting").
- Beyond Skyrim: no modder-facing interior guideline found by three searches; only player/UESP pages (e.g. https://en.uesp.net/wiki/Beyond_Skyrim:Cyrodiil/Houses, not fetched)
  and a Nexus author's note that Bruma's house interior tileset is "just 2 pieces" (already in interiors.md:45-46).

What the search summaries say (rules that would change our room planning), with the quoted words:
- Clutter amount is relative, not a number: "To know how much is enough, see other recent Tamriel Rebuilt or Project Tamriel interiors that are similar to the one
  you are making" (node/397, via search); showcases need "at least 10 Tamriel_Data items" beyond the furniture, and "Sufficiently clutter the interior".
  Change for us: our dressing checks should compare a room with its nearest similar rooms (same type, same class), which interior-dressing.md already measures over houses only.
- Social class: poor, middle-class and rich sets are not mixed without a reason; bandit/stronghold rooms "should look poor", using the cheap furniture set "wherever you can" (node/6455).
- Placement must look deliberate: items "in spots that make sense, so the placement doesn't appear arbitrary"; clutter on uneven surfaces is rotated to match the surface (a Velothi review).
- Floor space and navigation: Hlaalu guide section 3 "Asset Usage/Cluttering Guidelines", first subsection "Navigability and Floorspace" (heading seen; the rules text not seen);
  rugs and tapestries "largely subjective". Daedric guide warns against "a vast, empty room" and suggests copying a vanilla room's structure.
- Room programme by type (PTR wiki summaries): Daedric ruins normal rooms are 2x3, 3x3 or 3x4 pieces with about one light per room; hallways use Dunmer floor lamps, upper levels
  "standard yellow/orange" light, lower levels red lamps "to signal cultists". Indoril: "keep layouts as simple as possible", a few medium rooms in a line or round a hub.
  Hlaalu: a neutral brown ambient (80/60/40), main lights are floor lamps, candles, lanterns. Redguard Reach: underground can be more colourful; many-window rooms softer.
- Lighting: "Sunlight should be kept low, ... values between 10-25"; ambient colour chosen to fit the style, "compared with existing" interiors; fog for subtle colour;
  no "greenlight"; "your interior should look properly lit with no shaders and with default gamma/brightness". Light colour is meaningful: "Blue lights are reserved for mages and
  pink lights are reserved for brothels ... Replace these lights with normal yellow colour ones."
- What reviewers reject: "looks unlived in" compared with similar vanilla interiors; missing Northmarker; missing "Illegal to Sleep Here" on a building; missing pathgrid
  (Morrowind-era; for Skyrim the equivalent is navmesh); lights tied to the wrong meaning.
These are Morrowind-era rules (TR/PTR are Morrowind-in-Skyrim projects), so only the principles transfer: relative clutter, class consistency, meaningful light colour,
a room-type "programme", and review by comparison. Nothing here gives per-room-type contents lists (bed, table, shelves) - those must come from our own measurement of vanilla
non-house interiors (inns, smithies, temples, barracks), which interior-dressing.md:109 excluded.

## 2. Why generators cannot make cloth or leaves (checked on real meshes)
Short answer for the owner: he is not missing anything about the tree LOOKING good; it looks good because it is a solid sculpture. Skyrim does not draw leaves as solid
geometry, so the generated tree is the wrong KIND of object for the engine, though usable as a still one.

How a vanilla tree is built (measured here with niflod --info on files resolved through tools/places/assets/resolve.py, 2026-11-24):
- Vanilla `landscape/trees/reachtree01.nif` (Skyrim): root block BSLeafAnimNode; 3 drawn shapes. Trunk: 4,779 verts, 7,728 tris, opaque, bark texture
  (TundraDriftWoodBark01), no alpha. Two card shapes: 187 tris and 224 tris, each a set of flat alpha-cut leaf/branch cards (ReachTreeBranch01.dds) with NiAlphaProperty flags 4844
  (alpha TEST, threshold 45 and 70), vertex colours on, and shader flags2 with bit 29 set. Bit 29 is SLSF2_TREE_ANIM in nifly (~/.argonia/src/nifly/include/Shaders.hpp:114,
  "Enables vertex animation, flutter animation"); the trunk's flags2 has no bit 29. Collision: 179 convex-hull shapes in a list (trunk).
  So: the leaves are about 400 flat cut-out triangles total, painted with a leaf photo with transparent gaps; the trunk is solid; the sway is a shader effect driven by the
  leaf shape's vertex colours (the repo's vegetation-and-vessels-by-hand.md:80-95 records the same per file: "all five shapes tree-anim", vertex-colour amplitude; I did not re-derive
  what each colour channel means: UNVERIFIED beyond that note).
- Tropical Skyrim `landscape/trees/tropical/gkbjungletreenew1.nif` (the tree the game now uses for several records): BSLeafAnimNode root; trunk 6,048 verts / 2,016 tris opaque;
  card shapes 158, 212, 212 tris with alpha test (thresholds 45, 70, 70), vertex colours, flags2 570458161 (bit 29 set); one convex-hull collision; catalogue bounds height 2,498 units = 35 m.
  Total about 2,600 tris for a 35 m tree.
- Tree LOD: one billboard picture per tree base, rendered by TexGen from the model, from a hard-capped atlas of 256 slots: 169 used, 87 free
  (vegetation-and-vessels-by-hand.md:44, from out/newworld/plugin/map/lodplan.json build 20261111). docs/design/lod.md:29 says STAT trees of tree size also take a slot
  ("trees: TREE bases, and STAT trees at TexGen's size (bounds diagonal 512, height 256)"). So a static generated tree does not avoid the cap if it is tree-sized and should be seen from afar;
  a small or never-distant one needs none. Plants get no LOD by rule (lodplan.py:30-33).

What a Tripo/Hunyuan tree lacks: (1) leaf cards - it makes ONE opaque closed mesh with a baked picture, so foliage is a lumpy thick canopy with leaves painted on it, tens of thousands of
triangles instead of about 2,600 (cost-experiment.md quotes 50,000 raw for a glaive head; trees run larger); (2) no BSLeafAnimNode root or Tree_Anim flag, no vertex-colour sway map;
(3) no collision hull (needs one: the game does not read generated collision; collision authoring is the repo's first hard part, buildings.md:55); (4) no billboard (TexGen makes it
from the model; fine) and no LOD models.
What would it take to use one as a STATIC tree with no sway (a STAT record, not a TREE): decimate to a budget (e.g. under 10,000 tris), scale to size, write a NIF with a plain node root, one or two
shapes, DXT textures, a box or convex-hull collision, and a vanilla-style LOD model; no engine special case is needed. Hand-work cost: moderate; a few steps already exist in tools/newart
(shape.py clean/decimate). Quality trade: leaf detail reads as a solid blob from near, because Skyrim's own canopy gets its see-through breakup from alpha cards. From 30 m or in distant
view it passes. Better hybrid already in the repo's research (nature-and-vessels.md:288): generate only the trunk and roots, keep a vanilla/GKB card crown.
What usable at what cost: trunk/roots/stumps/knees - use as is after clean-up (little hand work); whole generated tree - usable as a static, non-swaying, mid-distance tree after
decimation and a collision hull; as a swaying forest tree, no without replacing the crown (card-building by hand, per tree, roughly an agent session each: UNMEASURED).

Cloth (measured on `armor/clothes/noblesseoblige/djerkin_1.nif`, a real worn garment from Valenwood.esp): root NiNode; 3 BSTriShape shapes (2,433 / 5,604 / 1,901 tris), each with a
BSDismemberSkinInstance, NiSkinData and NiSkinPartition (skinning to the body), and the file carries a 35-name "NPC ..." bone list (NPC Pelvis, Thigh, Calf, Clavicle, UpperArm, ForearmTwist1,
Finger bones, Head ...). Every vertex has weights to those bones; the game moves the garment by those bones. A generated garment is a static mesh with no weights, no bone list and no
partitions, usually on a posed figure, so it will not follow a walking, crouching or sword-swinging body (it stays in the air where it was loaded or the player sees it stretched
as unweighted). Race fit: one ARMO serves all ten playable races through ARMA records (wearables-by-hand.md:23-27): eight human races share a skeleton and body, Khajiit and Argonian share
`skeletonBeast`; body clothing is one mesh set for both sexes and all races, only headgear needs 3 to 4 variants. So the work is: reshape the garment to the shared body, then copy weights from the
nearest vanilla body/garment vertices (data transfer by nearest surface), check for tearing in poses, write the skinned NIF (the repo's wearables-by-hand.md:36-38 names writing a skinned NIF on
Linux as THE obstacle; PyNifly/headless Blender not yet installed). Rigid worn things are easy: horns, masks, circlets are one bone, one influence (wearables-by-hand.md:30-32), so a
generated mask or horn cap needs no weight painting. Cloth that flows (cape, skirt, loincloth) needs cloth-sim bones or extra weights: a hand job.
Usable of a generated garment: its shape as a REFERENCE or as geometry for armour plates (rigid-on-a-bone), not as a worn cloth outfit; a worn outfit costs a full skin transfer and fit check on
ten bodies each (hours of agent time per garment, tooling not yet built).

## 3. The "24-piece kit" in plain English
A kit is a small box of standard building parts, made once, that fit together like Lego. For an Argonian stilt house the box would hold about 24 parts: floor squares, a few lengths of
plank wall (one with a doorway, one with a window), a corner post, roof slopes and a ridge, stilt posts and beams, stair and ladder parts. Every part is sized in steps of the same fixed
grid (128 units, about the height of a person), so any part snaps against any other with no gap. You do not draw each house; you click parts together in the studio, and a small, a medium and a
big house come out of the same box. That is why the plan says "grey-boxed into three buildings": first the parts are plain grey boxes with no paint, three houses are snapped together to prove
the parts really fit and the houses are walkable, and only then do the parts get their wood and thatch look.
The reason to do it is that Skyrim itself is built this way (Bethesda made a few dozen wall, floor and roof pieces and built every Nordic house and fort from them), it keeps houses fitting
doors, stairs and floors exactly, and it needs few new models for many buildings; the cost is that houses look related, so the plan adds a handful of variants. A generated hut is the opposite
choice: one whole unique building, richer to look at, but each one is separate work to make fit the ground, doors and stairs. The plan uses the kit for plain carpentry buildings and generation for
the special root-grown ones. (Source: buildings.md:255 "Kit A ... about 24 pieces", :335 stage 2.)

Covered (addendum): TR/PTR/Beyond Skyrim searches and refused fetches (nine URLs), niflod --info on reachtree01.nif, gkbjungletreenew1.nif and djerkin_1.nif from the live asset stack,
nifly Shaders.hpp flags, repo docs cited · Skipped: any page those sites refuse (not worked around); no Beyond Skyrim source; sway vertex-colour semantics not re-derived.

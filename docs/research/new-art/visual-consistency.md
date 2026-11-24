# New art: visual consistency across a generated set (call #93, web lane). Researched 2026-11-24

Method: web search plus page fetches on 2026-11-24. Tripo blog/pricing pages, gamesbeat and Nexus pages returned 403, so
claims from them are SNIPPET (search-result text only). Almost every consistency write-up found is vendor marketing
(Tripo, Meshy, Scenario, Sloyd, Seeles, Virtuall); I found NO independent postmortem of a shipped AI 3D set that
reports consistency results. Nothing was generated or bought. Prices move; re-read before spending.

Live repo docs: docs/research/new-art/tooling.md (tools, prices, policy; section D has the fal image and 3D prices, not
repeated here) and PROPOSAL.md (pilot of three models). Nothing in the repo covers consistency. The doc to edit is
PROPOSAL.md (add the pilot's consistency checks to step 2); this file is the evidence behind it. universal-modder is
not on this machine (find / found no copy), so its recipes could not be read: UNVERIFIED whether they say anything.

## Findings first

1. The method every source converges on is the same: lock an art bible, lock reference images, change one variable per
   batch, review against reference, fix in the 3D/texture stage. No source gives numeric thresholds (Virtuall: "gives no
   numeric thresholds"). Numbers have to be ours. [Virtuall](https://virtuall.pro/blog/how-to-create-ai-game-assets-that-match-your-art-style)
2. Image-stage consistency is cheap on fal and multi-reference exists today (below). The weak link is not the image
   model; it is that image-to-3D models re-interpret colour and add baked light, so the look must be re-imposed at the
   texture stage. This is inference; vendor pages say the same in softer words (retexture, "keep geometry, replace albedo").
3. For matching an EXISTING 2011 game there is no published recipe at all (searched; nothing). Everything for section 7
   is my inference from generic tooling (histogram matching, texel density), flagged as such.
4. VLM-as-judge is documented as unreliable: judges invent image details and grade against them
   ([KOFFVQA, arXiv 2503.23730](https://arxiv.org/pdf/2503.23730); [MLLM-as-a-Judge, arXiv 2402.04788](https://arxiv.org/pdf/2402.04788)).
   A dev.to Meshy-to-Godot write-up (cited in tooling.md) saw a VLM hallucinate counts and use stale screenshots. So
   measured numbers gate; the VLM only lists things for a human to look at.
5. Training on Skyrim or mod-author textures is a permission trap: Nexus permissions default to "Ask me", AI-training
   permission needs written consent per author, and Nexus pledges mods will never be training data (below).
   Reference-only use of our own shots of vanilla is also unsettled. Avoid; use our own renders of our own models.

## 1. Style bible for an AI pipeline (what goes in it)

- Virtuall (vendor blog, undated): seven dimensions: shape language, proportions, palette, materials, detail density,
  lighting, world logic; plus a "never appear" list. References in four groups (hero, variation, material, negative),
  each logged with source, approver and whether cleared for prompting/training. A per-asset-type "generation blueprint"
  (category, function, style anchors, world and technical constraints, negative rules, review criteria). Review loop:
  small batches, one or two variables changed, score on silhouette/palette/materials/detail/world-fit/technical/compliance,
  record rejects as negative guidance. [link](https://virtuall.pro/blog/how-to-create-ai-game-assets-that-match-your-art-style)
- ClawHub "art-bible" skill (MIT-0, v1.0.0): eight sections; palette entries with role, hex/RGB/HSL, usage, "avoid";
  coverage tiers 70/25/5 percent; PBR roughness/metal table per material; material library table with texture size,
  tiling; per-engine limits; no standalone negative list. Fill-in template, not evidence it works.
  [link](https://clawhub.ai/toilanguyen2910/skills/art-bible)
- Seeles (SNIPPET): "lock the camera, palette, light direction, scale, tile size and material rules before generating
  batches"; extract exact hex from a locked canonical image. Layer.ai "reference sets" store reference images plus
  prompt fragments for team reuse (SNIPPET, [layer.ai/features/reference-sets](https://layer.ai/features/reference-sets)).
- Hierarchical prompt composition (global + faction + family + object brief): not found as a published, named method.
  The blueprint above is the nearest. UNVERIFIED as established practice; it is plain string composition and is ours to
  define as files (one YAML/JSON block per level, concatenated by a script).
- Tripo's blog pieces (style guides for packs, brand consistency, trim sheets, enforcing art direction) are 403; only
  titles and SNIPPETs read: shared style guide, curated reference library, material templates, folder structure;
  scripts that check every asset uses a master material list; packs drift in scale, pivots, materials, texture size,
  poly count, filenames.

## 2. Reference-image conditioning (on fal today)

| Route | Fal endpoint, limit, price | Notes |
|---|---|---|
| Nano Banana 2 edit | fal-ai/nano-banana-2/edit, up to 14 reference images, $0.06 (0.5K) / $0.08 (1K) / $0.12 (2K) / $0.16 (4K) (fetched page) | Page names no consistency feature, only "preserves what you do not ask to change" |
| Nano Banana Pro edit | fal-ai/nano-banana-pro/edit, $0.15 (snippet) | search result gave a conflicting "2 references" figure: UNVERIFIED |
| FLUX.2 edit family | flex: up to 10 refs, $0.05/MP; pro: up to 9 refs, about $0.03/MP; max: $0.07 first MP; dev: about $0.012/MP (snippets, sources disagree) | prompt "use style of reference image" appears on klein edit pages |
| FLUX.1 Kontext multi | fal-ai/flux-pro/kontext/multi, experimental multi-image; single Kontext pro $0.04 | multi price not found |
| FLUX Redux | fal-ai/flux-pro/v1.1/redux $0.05/MP, tagged style transfer; flux/dev/redux | image variation, weak for "same style, different object" (my view) |
| IP-Adapter | fal-ai/flux-general (LoRA + ControlNet + IP-Adapter + reference-only) | older mechanism |
| Midjourney --sref, Recraft custom style | not on fal in anything I found | UNVERIFIED on fal; outside our account anyway |

- Anchor-asset method: make one approved hero per family, feed it back as reference for siblings. Described in the
  vendor material as "hero reference set" and in Sloyd's Custom Style (one reference image defines the look, saved per
  category such as characters/props/environment; one example only, no measured results)
  ([Sloyd](https://www.sloyd.ai/en/blog/how-to-style-consistent)). fal's own guide says reference editing "drifts after a few
  generations", which is why it recommends fine-tuning for large sets
  ([fal guide](https://fal.ai/learn/devs/how-to-fine-tune-flux-with-the-api)). So: anchor to the approved hero each time,
  never to the previous sibling (my inference from the drift statement).
- Contact sheet: found only ComfyUI templates using Nano Banana to tile outputs (3x3 contact sheet, comfy.org hub); no
  write-up of "generate a line-up in one image, crop each, send to image-to-3D". Plausible, since one image shares
  one lighting and palette; UNVERIFIED in practice.
- Multi-view: Tripo H3.1 and Hunyuan v3 take several views (tooling.md D). Meshy docs recommend front/side/back/3-4
  views in one consistent style and about 1040 px input (third-party summary, not verified against Meshy).

## 3. LoRA fine-tuning for style

- fal's guide (fetched): FLUX.1 dev fast trainer fal-ai/flux-lora-fast-training $2.00 per 1,000 steps (is_style skips
  captioning); FLUX 3 Klein trainer $0.0043/step, $4.30 per 1,000; FLUX.2 dev trainer v2 $6.40 per 1,000. "A style is
  typically 9 to 50 images", minimum 4 for FLUX.1 fast; "consistency matters more than volume"; at least 1024 px, no
  compression artefacts. Fine-tune "when the style must hold across hundreds or thousands of images... or reference
  editing drifts"; otherwise use references. Klein inference $0.012/MP distilled.
- Scenario: style models from "even 10 images" (vendor help), Flux 2 custom training 10 to 15 images with captions;
  independent reviewer says 3D is not its strength ([help.scenario.com](https://help.scenario.com/en/articles/training-a-style-lora);
  [datastudios](https://www.datastudios.org/post/scenario-custom-trained-ai-game-asset-generation-style-consistency-and-pricing-explained)).
  Scenario retexture write-up: replace the albedo of a generated model with a Seedream-edited one, keep the UV layout,
  tweak normal/roughness; it does not cover trained styles or batches
  ([scenario.com](https://www.scenario.com/blog/scaling-3d-asset-libraries-ai-retexturing)).
- Legal side (explicit): Nexus announced 3 Nov 2026 mandatory AI disclosure, permission options for AI use and AI
  training with default "Ask me", written permission required for training/dataset use, and a pledge that hosted mods
  will never become training data ([PC Gamer](https://pcgamer.com/games/nexus-mods-takes-the-valve-approach-to-ai-generated-content-no-outright-bans-but-mandatory-disclosures);
  [GamingOnLinux](https://www.gamingonlinux.com/2026/11/nexus-mods-gets-stricter-on-ai-for-mods-but-no-outright-ban/);
  details of the permission setting partly still in development). Mod-author texture pages set their own terms; I found
  no ruling or Bethesda policy on training with Bethesda textures (Bethesda's only statement is the Creations ban on
  generative AI, 2023, tooling.md E). Conclusion: do not train on vanilla or mod textures or screenshots of them.
  A LoRA trained on our own approved hero renders is clean, but only worth it past about 50 assets (fal's own threshold).

## 4. Consistency at the 3D and texture stage

- Retexture tools: Meshy retexture takes exactly one of text prompt, one style image (image_style_url) or multiview
  images (the last needs meshy-7); enable_original_uv keeps the layout ([docs.meshy.ai/api/retexture](https://docs.meshy.ai/api/retexture)).
  Tripo texture endpoints (via third-party hosts): text OR reference image, style_image only alongside text; no
  fal-hosted Tripo texture endpoint found; Meshy retexture on fal returned 404 for the v5 page I tried (price UNVERIFIED).
  Meshy 7 (vendor advertorial, 13 Aug 2026) claims "geometric alignment" with reference art, multi-image input and
  retexturing; it says nothing about style consistency beyond that. Tripo "Stylization" is a style transfer on an
  existing model (SNIPPET, one source).
- Trim sheets and shared materials (Tripo blog SNIPPET): one atlas of common details tiled across models; obstacle is
  that generated UVs are baked per asset, so a re-UV step comes first; "master material, instance per asset". This is the
  route that maps best onto Skyrim, whose own assets use shared tiling textures (my inference).
- Geometry-only route: Tripo P2 "none" texture tier is $1.00 and H3.1 $0.20 (tooling.md D); a Blender script then
  applies our material set. Nobody found who published this for a game; my inference that it gives the strongest
  consistency because every albedo then comes from one source.
- Palette/LUT/histogram: skimage match_histograms works per channel when channel counts match
  ([scikit-image docs](https://scikit-image.org/docs/stable/auto_examples/color_exposure/plot_histogram_matching.html));
  per-channel matching can shift hue. No game-texture-specific source exists. Use a palette-sampled grade (k-means from
  reference tiles) in Lab space rather than raw per-channel matching: my inference.
- Texel density, normal strength, specular range, wear masks, polycount: no source found for AI sets specifically
  (UNVERIFIED); these are ordinary technical-art rules that a script can enforce.

## 5. Review and QA

- Studio habits that transfer (my inference from standard practice, not from a source): kit thinking (a limited set of
  pieces), colour script per region, material IDs, a master reference board, line-up under one rig. Seeles/Virtuall
  checklists give the same list in vendor form. Tripo SNIPPET: scripts check that every asset uses names from a master
  material list.
- Line-up render: Sloyd's check is "place the assets together in one scene"; Virtuall's is compare to hero and negative
  references, not "which looks best". Our version: Blender or in-engine line-up of the family beside four to six vanilla
  pieces under one rig.
- Automated checks that are cheap to write: mean/spread of value and saturation per albedo against the region's band;
  distance (e.g. Lab histogram or palette distance) to the target palette; texel density per metre; texture size;
  triangle count; material-name whitelist; bounding-box scale against a size chart. Thresholds must be calibrated on
  vanilla assets first (measure the vanilla spread, then allow that spread).
- VLM critique: see finding 4. Use it only to produce a questions list, never as a pass.
- Human gate (Virtuall: score each batch on a scorecard): once per family at the hero, once per batch at the line-up,
  never per asset after that.

## 6. Published examples (what exists)

- Meshy user stories (vendor-published, [meshy.ai/blog/solo-indie-dev-3d-platformer](https://www.meshy.ai/blog/solo-indie-dev-3d-platformer)): import to Blender, fix textures and poly count. No consistency evidence.
- Itch.io comment (SNIPPET, [itch.io/post/15923643](https://itch.io/post/15923643)): a developer stripped AI UI textures and audio before release after a player
  said the models looked out of place. Anecdote only.
- Sloyd: one art director, one dungeon, two styles from one reference each: the only worked set found, promotional.
- Gamesbeat piece "as game studios tighten budgets AI's next test is consistency" (403; SNIPPET) names style drift as a
  top reason AI content is reworked or discarded.
- Claude Code / blender-mcp: tooling.md covers StraySpark (five weapons, 2.7 h) and the Godot fish write-up; neither
  reports set-level consistency. I found no agent write-up on consistency. UNVERIFIED either way.

## 7. Matching an existing game (inference, no sources)

1. Sample from our own files: from vanilla and Tropical Skyrim diffuse maps of the same material class (rope, wood,
   hide, bone, stone), compute palette (k-means in Lab), value range and saturation percentiles. Store as hex tables
   per level. Reading textures locally for measurement is not training or redistribution, but record the intent.
2. Resolution: vanilla 2011 diffuse is mostly 512 to 2048 px; match by down-sizing generated textures to the same
   texels per metre as neighbours, then a slight blur and noise pass to avoid the over-clean AI look.
3. Convention: Skyrim wants diffuse plus normal plus specular (gloss in the normal alpha). Generators give PBR, so the
   conversion (roughness to specular/gloss) and normal strength must be fixed once and applied by script. The
   asset-pipeline report covers the NIF side.
4. De-light: use Tripo P2's delight option (tooling.md D) or a Blender bake; baked shadows read wrong in Skyrim's lighting.
5. Test beside neighbours in the engine's own lighting, in dim and bright weather: the only check that counts.

## Recommended method (ordered)

Well-evidenced (several vendor and fal sources agree): bible before batches; references in groups; one variable per
batch; fine-tune only for hundreds of images; compare to references; check technical readiness separately.
Inference (mine): everything marked below with (I).

0. Once, for the game: a bible file with Skyrim's measured palette bands, value/saturation ranges, texture sizes,
   specular and normal convention, texel density, wear rules, negative list ("clean sci-fi, glossy, saturated, PBR
   shine, Nordic motifs") (I for the measuring, evidenced for the contents). Level 0 is a pure data file.
1. Level 1, per culture/region/faction, once: a palette (about 6 to 8 hex), a material list (named, pointing to our
   shared textures), a shape-language sentence and three references from lore-grounded sources; one approved hero image.
2. Level 2, per family (tribe weapon set, tier): one anchor asset taken all the way into the game and approved by the
   owner; later siblings reference only that anchor plus the level 1 sheet (I, from fal's drift warning). Prompts are
   composed by a script: level 0 + level 1 + level 2 + object brief (I).
3. Images: Nano Banana 2 edit with up to 14 references at $0.08 (1K) per try; one line-up image per family when
   siblings share a scale (I, UNVERIFIED in practice); three views per object for 3D.
4. 3D: prefer geometry-only (Tripo P2 "none" $1.00 or H3.1 $0.20), then Blender script: decimate, re-UV, assign our
   shared materials or trim sheet, apply the region's grade, fix texel density (I). Use retexture-with-reference
   only where a unique pattern is needed.
5. Automatic gate (script, no VLM): value/saturation band, palette distance, texel density, texture size, triangles,
   material whitelist, size-chart scale. Thresholds calibrated on vanilla neighbours (I).
6. Human gate: owner looks at (a) the hero, (b) one line-up render of the family beside vanilla pieces, (c) in-game
   shot at the end of the pilot. VLM may list suspected faults for him; it never approves.
7. Do not train a LoRA now; revisit past about 50 assets, and then only on our own approved renders, never on game or
   mod textures. Tag all of it AI-Generated on Nexus (tooling.md E).

Covered: fal model pages (nano-banana-2/edit, fine-tune guide), Meshy API retexture, GitHub meshy-dev pipeline, ClawHub
art-bible, Virtuall, Sloyd, Scenario blog/help, scikit-image, Nexus policy coverage, VLM-judge arXiv papers, repo
tooling.md and PROPOSAL.md · Skipped: Tripo blog/pricing and gamesbeat (403), Reddit, Midjourney/Recraft, universal-modder
(not on disk), any generation or purchase (brief forbids).

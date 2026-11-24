# New art: external tooling research (call #93, lane: web). Researched 2026-11-24

All facts below were read from the cited pages on 2026-11-24 through a fetch tool that summarises pages; where a page
returned 403 (tripo3d.ai/pricing, Tripo help and blog pages, nexusmods.com pages, godisageek) the claim comes only from
search snippets and is marked SNIPPET. "UNVERIFIED" means no source found. Prices move often: re-read before spending.

Live repo docs on the topic: CLAUDE.md:22 (never make art except music made with Fal), decision 0006 point 5 ("We make
no art. Fal-made 2D art is allowed only if the owner asks for a specific small piece"), 0003:10 and 0015:20 (Fal-made
art counts as our original content), owner-rulings.md:989-991 (music with Fal allowed, boss track). Nothing in the repo
covers 3D generation. The doc to edit if the owner relaxes the rule: decision 0006 (amend point 5) plus the CLAUDE.md
"Never" line; no new file.

## Findings first

1. Policy is the hard edge. Bethesda Creations (paid/curated) bans generative AI outright; Nexus allows AI assets but
   requires disclosure labels from 2 Jan 2027. We ship free, as records pointing at player-downloaded assets (0003), so
   Creations is not our channel, but any generated mesh/texture makes our own mod "AI-Generated Content" on Nexus.
2. Tripo free tier is unusable: free outputs are public and Tripo keeps the IP; commercial rights need a paid plan
   (about $20/month Pro) or the API. Fal-hosted Tripo is pay per run with no subscription; the licence for outputs made
   via fal is UNVERIFIED (fal terms and Tripo API terms not read; ask/read before shipping).
3. Cheapest sensible 3D path on fal: Hunyuan3D v3.1 Rapid $0.225 (+$0.15 PBR) or Tripo H3.1 $0.30 standard texture. Best
   quality-per-cost for clean topology: Tripo P2 $1.10 (quad, up to 50k tris). Rodin $0.40, Meshy 6 $0.80, Trellis 2
   $0.25-0.35 (up to 4096 texture).
4. No published Skyrim write-up of AI mesh -> NIF exists (searched; nothing found). The route is GLB/FBX -> Blender
   (PyNifly, BadDogSkyrim) -> NIF, then NifSkope/houseCARL nif_inspect to check. Untested by anyone I could find.
5. Cleanup is real work: a tracked vendor-blog test of 5 weapons took about 2.7 h with Blender MCP versus 16-24 h manual;
   raw meshes were 18.9k-52.1k tris, no or chaotic UVs, vertex colours not materials, non-manifold edges. Simple
   symmetric shapes worked; thick blades, misshapen bosses, thin parts failed.
6. Most relevant tool for us already exists: universal-modder (rehan-remade) bundles the fal MCP and fal-generated
   art/3D recipes; its pipeline of fal -> 3D -> game is the nearest published match to the owner's plan.

## A. Skyrim / Bethesda modding agents (what exists, maturity, use to us)

| Tool | What | Maturity (evidence) | Help to us |
|---|---|---|---|
| houseCARL, Avick3110, Nexus SSE 181738 | Local C# MCP on Mutagen 0.54.4, reads MO2 profile, 31 tools, 7 skills; tools include housecarl_nif_inspect / nif_set (whitelisted NIF data values), asset_status, place_asset; skills for bulk records, dialogue, SKSE plugin authoring, facegen diagnostics (skillsmp.com/creators/avick3110/housecarl; claudskills.com/skills/housecarl; Nexus page itself 403, snippet) | skillsmp lists 14 skills, updated 2026-07-26; actively maintained | Already used. nif_inspect/nif_set is the post-conversion checker for a generated NIF (cannot author geometry). |
| Skyrim Forge, ShugokiFable (github.com/shugokifable/skyrim-forge; mcpmarket.com/server/skyrim-forge) | MCP running typed JSON jobs through xEdit, Creation Kit, Wrye Bash; transactional KYWD/GLOB/FLST/OTFT records; Papyrus compile; archive build; MO2 snapshot | 1 star, early | Low: overlaps houseCARL/Spriggit; Creation Kit automation (FaceGen, compile) might help. |
| Skyrim AI Toolkit, same author (mcpmarket.com/es/server/skyrim-ai-toolkit) | Installer bundling houseCARL, Spooky's AutoMod Toolkit, skill packs | 0 stars, no licence | None. |
| Skyrim Claude Code Modding Toolkit (gh.r-mj.com/7hr08ik/skyrim-opencode-toolkit mirror) | Knowledge base + skills + XEditLib.dll integration | Unverified beyond a search snippet | Possibly an xEdit-library route; not read. |
| SkyLink AI, Nexus SSE 175682 | SKSE plugin + MCP, 74 tools reading/changing LIVE game state | Page 403; snippet only | Runtime state reads / placement checks in game; overlaps our own harness. Unverified. |
| ModWrench (github.com/171county/modwrench) | MCP for Nexus/mod.io/Thunderstore search, load order, crash logs; 58 tools, 57 read-only | "Early, pre-1.0", 0 stars, 257 commits | Nexus search from an agent, but we already have tooling/nexus_search.py. |
| Mutagen MCP (mcpmarket.com/server/mutagen) | Mutagen-based ESM/ESP read/manage | Listing has errors (calls MCP "Modding Community Protocol") | None; we have Spriggit/Mutagen. |
| universal-modder, rehan-remade (skillsllm.com/skill/universal-modder) | Skills, `um` CLI, fal MCP, field notes: recon, reverse engineering, fal-generated art/3D/audio, in-game testing, showcase videos; Claude Code/Codex/etc; "almost any PC game"; 9,847 stars, 1,114 forks; scan passed 2026-10-01 | Popular; no Skyrim-specific recipe seen (examples: Terraria, GTA V, Elden Ring, ...) | Its fal 3D/art recipes are the closest template for the owner's pipeline. Read its source before copying. |
| PyNifly, BadDogSkyrim (github.com/BadDogSkyrim/PyNifly) | Blender add-on: import/export NIF for FO4, Skyrim LE/SE; Blender 3 and 4 (full testing on 4); animation import/export in development | Mature, the community standard; release/version for 2026 not verified | The conversion step GLB -> Blender -> NIF. No agent skill for it found. |
| blender-niftools-addon / NifSkope | Older NIF tooling | Not assessed | NifSkope for manual inspection. |

Searched and found nothing: any Claude skill or MCP for placing buildings or planning 3D locations in Skyrim cells
(only houseCARL place_asset, which is file-winner placement, not worldspace placement; our own tools cover that).
No r/skyrimmods thread surfaced (search tool does not index Reddit well): UNVERIFIED either way.

## B. 3D asset creation tooling

- tripo-mcp, VAST-AI-Research (github.com/VAST-AI-Research/tripo-mcp): "official", MIT, 233 stars, README says "alpha";
  needs Blender + Tripo Blender add-on, Claude Desktop or Cursor; text-to-3D into Blender. Last push April 2025 per
  ecosyste.ms (SNIPPET). Dated; not recommended.
- tripo-cli (developers.tripo3d.com/en/docs/cli.md): official, v0.9.0 table, `npm i -g tripo-cli`, Node 20+; `tripo make`,
  `tripo mcp --toolset full` runs it as an MCP server; `tripo make --dry-run` estimates cost; `tripo usage/balance`.
  A Hermes plugin page pins tripo-cli@0.11.1 and says 26 tools (multiview, texture, rig, retopology, segmentation) -
  tool list not on the official page: UNVERIFIED. Best current Tripo route for Claude Code.
- Tripo Studio MCP: no official one. Community: grinzero/tripo-studio-plugin (68 tools, needs a Tripo Studio account,
  targets Codex, 8K PBR, rig, Blender inspect; mcpmarket.com/server/tripo-studio; star count inconsistent) and
  Ador-able/tripo-studio-mcp (Codex, not official). A community `tripo-3d` skill installs into .claude/skills
  (skillsdirectory.com/skills/infometa-tripo-3d). Composio hosts a Tripo3D MCP (composio.dev/toolkits/tripo3d). All
  unvetted.
- blender-mcp, ahujasid (github.com/ahujasid/blender-mcp, now PyPI mcp-for-blender): socket add-on + MCP; viewport
  screenshots, Poly Haven, Sketchfab, Hyper3D Rodin, Hunyuan3D; 32-34k stars (Enterprise DNA, 26 Oct-14 Nov 2026).
  Also DeemosTech/blender-mcp-rodin-integration. This is the Blender clean-up driver.
- Meshy/Rodin/Hunyuan: reachable through fal (below) and through blender-mcp (Rodin, Hunyuan). No dedicated Claude Code
  skill examined beyond that.
- Fal itself: this session has the claude.ai fal connector (recommend_model, run_model, pricing tools); universal-modder
  also ships a fal MCP.

Write-ups (what worked / failed):
- StraySparkStudio, text-to-game-ready-asset with Blender MCP (strayspark.studio/blog/text-prompt-game-ready-asset-blender-mcp-ai):
  five weapons; cleanup = retopology 20 min, UV 15, materials 45, LOD 10, collision 10, export 5, review 30 (about 2.7 h
  total vs 16-24 h manual). Raw 18.9k-52.1k tris, bad UVs, vertex colours, up to 27 non-manifold edges; sword and dagger
  fine, axe edge too thick, hammer proportions off, shield boss and back grip poor. Vendor blog, one author.
- dev.to, Meshy -> Blender MCP -> Godot fish (dev.to/aleksandr_kossarev_e23623/...): 16 steps (import, orient, apply
  transforms, decimate, rig, weight, vision-check, export). Failed: auto-weights on thin fins/veils, axis mismatch,
  VLM hallucinated counts and used stale screenshots. 2-3 h first model, about 10 min after. Rigging-specific; we
  do static props.
- World Labs showcase (worldlabs.ai/ai-native-3d-pipelines): Claude Code orchestrating fal + Hunyuan 3D, Blender, Unreal;
  page 404 on direct fetch, only the search snippet read.
- Seeles.ai pages: vendor marketing; argue an agent cannot prove a model is game-ready. Treat as opinion.
- No write-up found for Claude Code + Fal images + Tripo + Blender + a Bethesda NIF. UNVERIFIED that the chain works
  end to end for Skyrim; each link is documented separately.

## C. Tripo, late 2026

- Versions: H3.1 = v3.1-20260211 (stable default; text, single image, multiview; PBR; quad FBX; clean low-poly for
  simple inputs), v3.0-20250812, v2.5-20250123 still selectable; texture version v3.5-20260815 default for v3.x
  (developers.tripo3d.com/en/models/v3-1). P2.0 launched 21 Sep 2026 after an August preview: native quad meshes, up to
  50,000 tris (25,000 quads), "Smart Mesh", Smart UV, Mesh Edit (regenerate a selected geometry region), multi-version
  output; text/image/multiview (voxelmatters.com; digitalproduction.com/2026/09/29; runtimewire.com). P1 earlier.
- Image / multiview: both exist on H3.1 and P2 (Comfy docs list TripoPSeries Image/Multiview nodes). Fal's Tripo H3.1 and
  P2 pages show single image only; multiview on fal Tripo not described (UNVERIFIED).
- Texture: quality fast / standard / detailed / extreme (8K) on H3.1; PBR flag (page does not itemise maps; Meshy lists
  base colour + metallic + roughness + normal for comparison); `delight` (lighting removal, default true on P2); UV
  export; auto_size to metres. Pixel resolution of "standard" not stated: UNVERIFIED.
- Polycount: H3.1 up to 1.5M faces (2M detailed geometry); quad capped 150k; default 10k quad; smart low-poly 500-20,000
  (500-10,000 quad). P2: 48-50,000, quad 25,000. Add-ons H3.1: detailed geometry +20 credits, quad +5, smart low-poly
  +10, generate in parts +20 (parts needs texture and PBR off).
- Segmentation/parts: "generate in parts" (H3.1) and semantic segmentation (August update blog). Rigging: yes (rig tasks
  by task_id). Texture re-generation/editing and stylisation: CLI lists texture, stylize, remesh post-steps; a texture
  EDIT tool not confirmed. Formats: GLB, FBX (quad), OBJ, USDZ via Studio (tripo-studio-plugin page).
- Time: about 40 s untextured, about 120 s textured (H3.1 page).
- Pricing, official API (developers.tripo3d.com, credits, CNY approx, 1 credit = CNY 0.07 per Alibaba page): H3.1 image to
  3D 14/21/28/35 credits for none/standard/detailed/8K (page prints "1.40/2.10..." in CNY); a Tripo blog says model
  generation 40-50 credits and credits about $1 per 100 (SNIPPET, conflicts). Treat official $ per run as UNVERIFIED;
  fal's figures below are firm.
- Subscription (SNIPPET only, tripo3d.ai/pricing 403): Free 200 credits/month (8 or 13 models per differing pages),
  Pro about $20/month (3,000 credits; $240 billed yearly per 3daistudio comparison, 1 Nov 2026; Tripo's own guide
  mentions $11.94 annual), Max about $89.9, Team about $109.9 (secondary source).
- Licence (SNIPPET, Tripo help/blog pages): Free plan models are public, CC BY 4.0 and Tripo retains all rights to
  inputs and outputs (Terms 5.2.1); paid plans: user holds all rights incl. commercial use, no training on them (Terms 5.2.2),
  private models. Tripo disclaims responsibility for copyright status of outputs. API: commercial rights claimed. For
  fal: UNVERIFIED.
- Weak spots: single image hides the back (Tripo's own limitations blog: hallucinated backs/undersides, multiview
  helps; "rarely print-ready"); StraySpark: thick edges, wrong proportions; fish write-up: thin fins/veils hard.
  Foliage alpha cards, symmetry, baked lighting (a `delight` option exists for exactly this), texel density on big
  objects: no independent source found. UNVERIFIED.

## D. Fal-hosted 3D models (per run, from fal model pages, 2026-11-24)

| Model (endpoint) | Price | Notes |
|---|---|---|
| Tripo P2 (tripo3d/p2/image-to-3d) | $1.00 none, $1.10 standard tex, $1.20 detailed, $1.30 extreme; PBR on by default; quad free | 48-50k tris; delight, auto_size, seeds; best topology |
| Tripo H3.1 (tripo3d/h3.1/image-to-3d) | $0.20 none, $0.30 standard, $0.40 detailed; +$0.20 detailed geometry, +$0.05 quad | face_limit 1k-2M; GLB or FBX(quad) |
| Tripo v2.5 | $0.20/$0.30/$0.40 | older |
| Hunyuan3D v3.1 Rapid | $0.225, +$0.15 PBR | single front image; GLB |
| Hunyuan3D v3 | $0.225 geometry, $0.375 normal (textured), $0.45 lowpoly; +$0.15 each for PBR / multiview / custom face count | multiview back/left/right supported; 40k-1.5M faces |
| Hunyuan3D v2 / turbo | $0.16 / $0.14 | |
| Trellis 2 | $0.25 (512), $0.30 (1024), $0.35 (1536) | texture 1024/2048/4096; remesh; GLB |
| Hyper3D Rodin v2 | $0.40; HighPack ($1.20 by my arithmetic) gives 4K textures | quad 4k-50k or tri 2k-500k; PBR/shaded; GLB, FBX, OBJ, USDZ, STL |
| Meshy 6 image to 3D | $0.80 | PBR maps, quad or tri, 100-300k polycount; GLB, OBJ, FBX, USDZ |
| TripoSR | $0.07 | fast, low fidelity |
Sources: fal.ai/models/<endpoint>/llms.txt pages. Fal page text conflicts for Hunyuan v2 ($0.16 vs $0.017 in a comparison
blurb) so the blurb was ignored.

Best at: Tripo P2 clean quads for stylised props; H3.1/Hunyuan cheap and detailed; Rodin and Meshy PBR-rich; Trellis cheap
with 4K textures. These are vendor-page claims, not a head-to-head test (no independent comparison read: UNVERIFIED).

Fal image models for references (prices per image):
- Nano Banana Pro $0.15 at 1K/2K, $0.30 at 4K (fal guide); Nano Banana 2 $0.08 at 1K (1.5x 2K, 2x 4K); Nano Banana
  (original) edit $0.039; FLUX.2 [pro] $0.03/megapixel; FLUX Kontext Max about $0.08 (aggregator); Recraft V3
  $0.04 raster; GPT Image 2 $0.005 (low, 1024x768) to $0.401 (high 4K).
- Background removal: Bria RMBG 2.0 $0.018 per image ($0.03 with a prompt) (fal page).
- Transparent background: dedicated generation of RGBA I did not verify; the safe route is a neutral flat background
  then RMBG. Multi-view turnarounds and set consistency: I found no price or evidence of a turnaround-specific model;
  edit models (Nano Banana, Kontext) taking the first image as reference are the usual method: UNVERIFIED for quality.
- Tripo H3.1 and Hunyuan3D v3 accept multiple views, so a front/back/side sheet is worth the extra images for
  hidden-back problems.

## E. Policy

- Nexus Mods, announced 3 Nov 2026 (pcgamer.com, gamesradar.com, videogameschronicle.com, 80.lv, gamingonlinux.com;
  nexusmods.com/news/14850 itself 403): no ban; mandatory disclosure on new uploads; labels AI-Generated (includes
  in-game AI-generated assets, code, voices, music, translations), AI-Assisted (limited AI, e.g. texture upscaling),
  AI Media (promo art); AI-assisted mods must say how and where; existing mods must comply by 2 Jan 2027, enforcement
  from then, ignoring staff can lead to restriction or removal; new permission options for AI use, AI training, forks,
  derivatives, default "Ask me"; users can hide AI content; Nexus will not train on or sell uploads. 2023 policy
  (SNIPPET): AI content not against the rules but removable on a credible rights-holder complaint.
  Effect on us: we must tick AI-Generated for any generated mesh/texture and for our Fal music already.
- Bethesda Creations (Dec 2023, insider-gaming.com/bethesda-skyrim-creation-mods-ai/): "Creations cannot contain anything
  produced with generative AI." Applies to the Creations platform; no 2025-26 revision found (UNVERIFIED). Provider
  agreement (bethesda.net) not read for AI clauses. Free Nexus distribution is outside Creations.
- Distribution: our plan ships records only, no assets (0003). A generated mesh we made would be our original content
  (0015:20 already says so for Fal art), so it could be shipped, subject to the fal/Tripo output licence being
  commercial-or-free-use compatible (UNVERIFIED for fal) and to Nexus labelling. Copyright in purely AI-generated output
  is uncertain in many jurisdictions; Tripo itself disclaims it. Not legal advice.
- Music precedent: the repo already ships Fal-generated music (owner-rulings.md:989-991; CLAUDE.md:22). Same labelling
  consequence on Nexus (AI-Generated covers music). The music rule's reason (we cannot source it otherwise) differs
  from 3D, where a Nexus asset usually exists, so keep the 3D carve-out narrow and per-asset.

## Realistic per-asset cost (3 image tries, 2 model tries per kept asset)

| Route | Images (3 tries) | Background removal (3) | 3D (2 tries) | Total per kept asset | Sources |
|---|---|---|---|---|---|
| Cheap: Nano Banana 2 1K + RMBG + Hunyuan3D v3.1 Rapid with PBR | 3 x $0.08 = $0.24 | 3 x $0.018 = $0.054 | 2 x $0.375 = $0.75 | about $1.04 | fal NB2, Bria page, Hunyuan page |
| Mid: Nano Banana Pro 2K + RMBG + Tripo H3.1 detailed | 3 x $0.15 = $0.45 | $0.054 | 2 x $0.40 = $0.80 | about $1.30 | fal NB Pro guide, H3.1 page |
| Good topology: Nano Banana Pro + RMBG + Tripo P2 standard quad | $0.45 | $0.054 | 2 x $1.10 = $2.20 | about $2.70 | P2 page |
| Multiview: 4 views x 3 tries NB Pro ($1.80) + Hunyuan v3 normal+PBR+multiview ($0.675) x2 | $1.80 | 4 x 3 x $0.018 = $0.22 | $1.35 | about $3.40 | v3 page |
| Rich: Rodin HighPack or Meshy 6 | $0.45 | $0.054 | 2 x $1.20 or 2 x $0.80 | about $2.90 or $2.10 | Rodin, Meshy pages |
Cleanup labour dominates: about 0.5 to 3 h of agent/Blender time per asset (StraySpark figures, simple props at the lower
end); Skyrim NIF conversion, collision and in-game test are not in these numbers and are unmeasured. Subscription route
(Tripo Pro about $20/month, 3,000 credits) is only worth it if per-run cost via the official API is lower than fal
(UNVERIFIED). A 100-asset set at the mid route is about $130 of generation; a small batch of 20 is about $26.

## Recommendations

1. Before any spend, read universal-modder's fal 3D recipes and run one trial asset via the fal MCP already connected
   (cost about $1-3), end to end to a loaded NIF; that settles the one unproven link (GLB -> PyNifly -> NIF -> in game).
2. Prefer fal-hosted runs over a Tripo subscription: pay per run, no public-by-default free tier; but read fal's and
   Tripo's output terms first and record them (decision 0015 licence tracking).
3. Use tripo-cli (official) over the dated tripo-mcp for Claude Code; use blender-mcp for the Blender cleanup.
4. Start with simple solid props (shape of the StraySpark sword and dagger), and send multiview sheets to avoid hidden
   backs.
5. If any asset ships, amend decision 0006 point 5 and the CLAUDE.md "Never" line, and plan for the Nexus AI-Generated
   label (deadline 2 Jan 2027 for existing mods, applies to our music already).

Covered: web only (fal.ai model pages, Tripo developer docs, GitHub/MCP directories, Nexus/Bethesda news coverage, repo
docs 0003/0006/0015/owner-rulings/CLAUDE.md) · Skipped: tripo3d.ai pricing/terms/help and nexusmods.com (403), Reddit
(not indexed), fal and Tripo legal terms (not found), any real generation or download (brief forbids spending).

# Audit of elder-souls-argonia: research, infrastructure, assets and agent workflow

Research date 2026-10-27 (read-only audit of `jtattersall09403/elder-souls-argonia`). Paths are in that repo.

## 1. Research bearing on an engine switch
- No OpenMW assessment exists. The only engine study is `docs/research/engine/godot-migration-assessment.md`
  (2026-10-01): stay on three.js, medium confidence; port estimate 45–75 agent sessions plus 15–30 owner
  walks; ~117k lines TS + 208k-line Python world pipeline at risk; agents confuse engine API versions; no GPU
  to check the real renderer.
- Decision 0122: WebGPU retired. 0084: frame budget measured against an M2 Mac and an Honor Magic V5.
- Climbing: `docs/research/combat-and-systems/skyrim-climbing-mod-survey.md` found FreeClimb (Nexus 193552),
  whose clips are Mixamo and Threepeat content (code GPL-3.0); EVG Animated Traversal and SkyParkour supply
  one-shots. `botw-climbing-system.md` gives the rule set (slope bands, stamina, 33-motion list); decision 0152
  makes climbing province-wide with no wall-run.
- Swim/boat mechanics: `swim-climb-boat-implementation.md`, `player-boats-as-horses.md` (boats follow
  Skyrim's horse model; "sourced assets, never designed"); decision 0159 (Wind Waker sailing, dugout and sea
  hull first).
- Souls mechanics: `dark-souls-poise-mechanics.md` and decisions 0031–0037 (equip load, i-frames). Engine
  neutral and reusable.

## 2. Infrastructure, costs, vault
- Old host: EC2 m7i.2xlarge (8 vCPU, 32 GiB), 250 GB gp3, eu-west-2, Ubuntu 24.04, VS Code tunnel, no inbound
  rule, secrets in `/workspaces/.es-secrets.env`, `idle-stop.sh` powers off 90 min after last activity plus a
  CloudWatch CPU alarm backstop. About $0.40/h compute plus ~$20/mo EBS: over $100/month at 8 h/day.
- Codespaces was tried and superseded (too small), but `docs/research/infrastructure/codespaces-migration-plan.md`
  is a good recipe: tiered restore, sha256-pinned toolchain, secrets handling.
- GPU: none on the dev box; SwiftShader under 10 fps; decision 0119 made RunPod the GPU lane (price stated
  before each pod via `agent_guard.py`, pods deleted after use, `pod_watch.py` stops orphans after 10 min).
  The harness (`tooling/gpu-lane/`) is three.js/WebGL/Chrome specific. Streaming play was never costed.
- Claude spend: no dollar totals in the repo; `docs/research/agent-ops/cost-reviews.md` and
  `session_tokens.py` price tokens at API rates (decision 0079). Sessions averaged 150–350 turns and 100M+
  cached tokens; Opus subagents cost about 2x the planner; cache reads are 95% of tokens but ~46% of dollars;
  cache writes ~48%.
- R2 vault snapshot: bucket `elder-souls-vault`, ~53 GiB in 76–85 parts, ~$0.60/mo; restore by rclone + tar +
  sha256 against a committed SHA256SUMS, tiered (base ~11 GiB, toolchain ~7 GiB, then per-mod parts). Also
  holds Claude transcripts.
- Pain points: the heightfield ladder lived only on one VM until snapshotted; 42 of 50 mod folders lacked a
  machine-readable Nexus fileId; Black Marsh & Valenwood (9 GB) is a manual ModDB download; Wine's wineboot
  hangs if a display is present; /tmp wiped at stop; repo 2.87 GB; SwiftShader useless for visuals.
- Vault: separate local-only repo `../elder-scrolls-asset-pipeline` (restored from R2). Skyrim LE vanilla Data
  2.98 GiB via DepotDownloader with the owner's Steam login; mod-sources ~30 GiB; toolchain pinned
  (`toolchain.json`): Wine 11.13 wow64, Windows Blender 4.4.3 + PyNifly V28.1.0 in a hand-built prefix,
  gltfpack, bsa tools. Reusable for Skyrim-as-host: the R2 snapshot and restore scripts, the vault inventory
  registry (`world/sources/assets/`, 27,929 rows), the Mixamo/Threepeat climbing sources. The NIF→GLB
  conversion is no longer needed when Skyrim itself renders the meshes.

## 3. Agent operating model
- Roster (`.claude/agents/`): planner (Fable), deliver (Opus), deliver-small (Sonnet), place-builder (Opus);
  find, run, check (Haiku); research and reader (Sonnet); dialogue-lane, dialogue-writer, voice-reader,
  corpus-reader (Sonnet). Skills (11): place, kit-build, kit-mining, composite-author, modular-runs,
  visual-look, journey-author, text-review, dialogue-write, routing-audit, cost-review.
- Cost controls (0079, 0118): model only in agent frontmatter, low effort, plan-first; hand-off marker at 300k
  context (100k Haiku); one deliverable per context; no sleeps/polls; every deliver brief has an Acceptance
  line; reports to disk with a 25-line return.
- Hooks (`docs/standards/hooks.md`): shell_guard, agent_guard, role_guard, job_guard.sh (memory-measured
  admission), review_gate, commit-msg guard (shared files, per-lane hunks via commit_hunks.py), lane_watch,
  tidy.
- Gate (0131): one `npm run check` ≤ 3 min, run only by the check agent; CI runs the same command.
- Testing ladder (0156): 1 data, 2 still, 3 motion, 4 headless play, 5 filmed pod strip (with a reason),
  6 owner walk. Lowest sufficient level wins.
- Transfers: the cost doctrine, brief template and Acceptance discipline, single gate, lowest-level-first
  ladder, hook concepts (shell/wait guards, memory-based job admission, scoped commits), decision records and
  PROGRESS rows with lane resume, idle-stop.sh.
- Does not transfer: gpu-lane, studio probes, packages/*, the wb.py place workbench, web typecheck/vitest gates,
  Pages deploy, kit_compress budgets.
- Observed failure modes: 950-turn sessions; planner bash-exploring (68% of context); hundreds of sleeps;
  twelve filming passes finding almost nothing (0156); "too slow, overcautious" and a growing gate (0106);
  pods lost with sessions; shared-file commit clashes; a false "no climbing loops" claim; orphaned pods;
  hand-built environments that had to be snapshotted; rule accretion in CLAUDE.md.

## 4. Licensing and asset distribution
- Stance (`docs/world/90-asset-strategy.md`:110, :167): personal project, "no per-asset permission gate";
  credits in README (69 entries); decision 0152 §2 waived licence reading because the build was "private,
  personal use, undistributed".
- `apps/world-studio/public` holds ~562 MB of converted Skyrim and mod assets, deployed to GitHub Pages.
  The owner confirms the old repo is private, but **a GitHub Pages site is publicly reachable even from a
  private repo** (unless on Enterprise), so those assets are public to anyone with the URL. Not in scope for
  skyrim-argonia, but noted for the owner.
- Mod authors' terms were not checked in the old project; some are ask-first (e.g. SkyParkour re-hosting "by
  explicit permission of tsptds"). Mixamo clips must not be repackaged as a standalone library.
- skyrim-argonia avoids all of this by shipping only code and original data, with players supplying the game
  and mods (decision 0003).

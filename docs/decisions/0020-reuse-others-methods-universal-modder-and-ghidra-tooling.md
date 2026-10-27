# 0020: Reuse other people's methods: universal-modder's skills, agents and field notes, and the agent-ready Ghidra tooling

**Status:** decided 2026-10-27 (owner: "We really don't want to reinvent the wheel in terms of methods when other
people have figured a lot out already").

## Context

- **universal-modder** (MIT, github.com/rehan-remade/universal-modder) packages tested methods as Agent Skills,
  three agent definitions, the `um` CLI and a knowledge base of field notes written by agents (122 games, 85
  technique notes), several by the same Claude model this project uses.
- The **NSA Ghidra repo itself ships no agent skills** (checked: no skills, CLAUDE.md, AGENTS.md or MCP). The
  agent-ready layer is third-party: **ReVa** (Ghidra extension designed for LLM agents, ships its own CLAUDE.md and
  AGENTS.md), **pyghidra-mcp** (headless, project-wide, recommended by universal-modder), **GhidraMCP**
  (LaurieWired, best known), plus the pattern of plain headless PyGhidra scripts on named functions (Faith Runner).

## Decision

1. **Vendor and use universal-modder's skills** in `.claude/skills/um/` (MIT licence and credit kept; adapted only
   where paths or this repo's rules require), and use them wherever they fit:

   | Skill | Used for | Phases |
   |---|---|---|
   | `share-field-notes` | **search the knowledge base before any system work** (the field notes are prior art) | every WP |
   | `game-recon` | fingerprinting Skyrim's install, loaders, saves; DSR's install and offline safety | P0, P1 |
   | `game-research-websearch` | archive-aware research of mods, tools and dead forum threads | all research |
   | `reverse-engineering` | DSR data and targeted native questions; Skyrim questions CommonLib does not answer; file formats | P1-S6/S7, P5 |
   | `game-automation` | launching and driving Skyrim and DSR, screenshots, input, recording | P1, P2-WP2.4, P5 |
   | `mod-any-game` | the overall loop (cheapest route, journal, slice, verify in the real game, record) | every system |
   | `mashup-mods` | cross-game rules: transplant a mechanic, parity documents, list every substitution | P5, P6 |
   | `port-a-mod` | porting open-licence mods we fork (FreeClimb, Chocolate Poise reference, Sailable Ship) | P5, P6 |
   | `asset-pipeline`, `fal-assets` | minor 2D UI art, icons, map, loading paintings | P4, P8 |
   | `publish-mod` | pre-release lint (no game files, no decompiled code, no keys), README, credits, AI disclosure | P10 |
   | `showcase-video` | owner packet clips and the release video | P7–P10 |

2. **Use its agent pattern**: its orchestrator / game worker / offline worker split maps onto ours (the planner;
   the one lane holding the GPU-box lock, the only one that touches the running game; build-VM lanes that study
   dumps and write generators against stubs). The orchestrator's habit of checking every "done" against logs and
   files is our planner's rule.
3. **Install and use the `um` CLI** on the build VM where it helps (`um kb search`, `um scan`, `um backup` for DSR
   saves, `um publish check`), adapting Windows-only commands to our Linux/Proton machines or skipping them.
4. **Read these field notes before the work they bear on** (each is cited in the matching phase): Skyrim:
   `rebuilding-a-cut-gatekeeper-with-generated-plugin-records…` (P4 quests/dialogue); DSR:
   `porting-dark-souls-remastered-enemies-into-elden-ring` (P5) and `portal-gun-prototype-via-dinput8-proxy-dll…`
   (P1-S6, DSR camera and proxy-DLL facts); techniques: `oracles-how-agents-know-a-mod-works`,
   `prove-your-replay-bench-can-fail…`, `when-the-first-real-run-fails-suspect-the-oracle…`,
   `driving-a-game-from-a-mod-side-command-file…`, `driving-real-games-safely`,
   `a-force-quit-pc-game-relaunch-wedges-as-an-unkillable-zombie`, `recording-game-footage`,
   `d3d12-frame-readback-buffers-only` (screenshot capture), `running-xedit-and-windows-modding-tools-on-linux`,
   `bethesda-plugin-record-format-esm-esp-esl`, `bethesda-esl-light-masters-and-plugin-archive-pairing`,
   `installers-load-order-and-loaded-code-checks`, `havok-hkx-chunked-packfile-family`,
   `collision-and-combat-bridging`, `bridge-contracts-ownership-units-and-lifecycle`, `choosing-a-mashup-route`,
   `rebuilt-guest-engine-inside-a-host`, `engine-recreation-measures-and-fidelity`,
   `evidence-levels-for-mashup-claims`, `publishing-reverse-engineering-research-what-to-scrub…` (our repo is
   public), `porting-a-vehicle-semantic-traps` (boats).
5. **Ghidra: use the agent-ready tooling, not raw chat.** Install pyghidra-mcp (headless) and ReVa as MCP servers
   on the build VM, bound to 127.0.0.1; follow ReVa's own agent docs; for repeatable questions write headless
   PyGhidra scripts on named functions (Faith Runner's `DecompileTargets`/`DumpAsm` pattern), seeded with the
   Address Library names database for Skyrim; all output stays in `$ARGONIA_PRIVATE` (decision 0010 §4).
6. **Prior art is a brief field.** Every build brief states what was searched (field notes, skills, mod source,
   open reimplementations) and what was reused; "built from scratch" needs a one-line reason.
7. **Giving back** (owner call **O-19**): when a port works, write a field note in universal-modder's format
   (scrubbed per its publishing note: no offsets, no decompiled code, no game files) and offer it to their knowledge
   base. Default: yes, after the owner sees it.

## Consequences

- P0-WP0.2 vendors the skills and agents; P0-WP0.4 installs `um`, pyghidra-mcp and ReVa; `brief_template.py` gains
  the "Prior art" field.

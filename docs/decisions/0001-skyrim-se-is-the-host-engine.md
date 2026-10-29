# 0001: Skyrim SE is the host engine; our own SKSE plugins carry the systems; HTML screens carry the Morrowind UI

**Status:** decided 2026-10-27 (owner: "I don't mind the idea of using Skyrim as host in theory", provided
Argonia keeps Morrowind's soul; owner asked to get cracking with it). Confirmed or reversed by the 0.2
chunks 0.3 and 0.4 of [Part 0](../phases/0-foundation/README.md) and the owner's verdict after the core loop ([1.7](../phases/1-core-loop/1.7-verdict.md)).

## Context

The owner wants Argonia playable with Morrowind's soul, DS1 combat, free climbing, boats, Skyrim-level
graphics, minimal new art, nothing shipped that players do not already own, built by agents for under
$100/month. Four engines were researched (evidence:
[engine-feasibility-and-openmw](../research/2026-10-27/engine-feasibility-and-openmw.md),
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md),
[skyrim-morrowind-soul](../research/2026-10-27/skyrim-morrowind-soul.md),
[skyrim-combat-traversal](../research/2026-10-27/skyrim-combat-traversal.md)).

| Option | Body (art, creatures, water, combat/climb substrate) | Soul (Morrowind systems) | Verdict |
|---|---|---|---|
| OpenMW fork | Expensive: Black Marsh art and creatures exist only as Skyrim mods (cross-game conversion forbidden by several authors, 1–3 days per creature); water is one plane per cell (fork); climbing and souls combat from scratch; scarce animations | Free (it is Morrowind) | Fallback |
| **Skyrim SE as host** | **Free**: the Skyrim-format art the project already uses, Mihail's creatures, placed swimmable water, mature combat/climb/swim mods with plugin APIs | Built as code: our SKSE plugins + HTML screens | **Chosen** |
| Stay on three.js | Already built, but phone frame rate, load time and water were the long poles; ships converted assets | Built | Out of scope here; the owner may continue it separately |
| Mudcrab / OpenMW ESM4 (engines reading Skyrim data) | Not playable yet | n/a | Watch as a long-term path |

The owner's no-new-art rule and agents' strengths decide it: art cannot be generated well by agents, code can.
Skyrim makes the body free and the soul a code problem.

## Decision

1. Argonia is a **Skyrim Special Edition total conversion**: our own master plugin, our own SKSE plugins,
   and a pinned list of third-party mods the player downloads.
2. **Sub-option tiers** (owner asked for them to be distinguished):
   - **S1, classic data mod**: plugin records, Papyrus, existing mods. Everything that can live here, lives
     here.
   - **S2, our own SKSE plugins** (CommonLibSSE-NG + Address Library) hooking the unmodified executable.
     The core of the project: stats/vastei/topics/conditions (ArgoniaCore), combat numbers
     (ArgoniaCombat, only for the combat gaps the mods leave: decision 0019), boats (ArgoniaBoats), the dev-only agent bridge (ArgoniaBridge).
   - **S3, targeted deep hooks**: only where S2 cannot deliver the soul: the Morrowind dialogue window,
     the topic-index journal, the local map, the sitting/persuasion/chargen screens and the HUD, drawn as
     HTML through PrismaUI. Raw-offset patches of SkyrimSE.exe are a last resort and need a decision record.
   - **S4, a different engine reading Skyrim data**: not now.
   - Note: the research report defined S3 as "deep reverse-engineered hooking"; this plan narrows S3 to
     replacement screens plus any unavoidable deep hook, because PrismaUI makes HTML screens the cheap form of S3.
   - **PrismaUI risk:** single author, restrictive licence. Pin its version early (0.3); every S3 screen keeps a
     fallback (an SWF of our own or the vanilla menu path, decision 0014 §7) so a PrismaUI failure degrades the
     look, never strands a quest.
3. **Fallback trigger.** If 0.3 cannot load our own SKSE plugin on the pinned runtime, or 0.4 cannot build
   and walk the Claywater block (navmesh and faces solved) after its listed fallbacks, stop and bring the
   owner a re-plan **on Skyrim** (the owner ruled out OpenMW on 2026-10-28): a different runtime pin, a
   different toolchain, or the Creation Kit as the generator.

## Consequences

- Skyrim is PC-only: phone and Mac play is by streaming (decision 0007).
- Players need Skyrim SE plus the dependency list; the version is pinned (decision 0002).
- Every gameplay system is reachable: the mapping of each to S1/S2/S3 is in [PLAN.md](../PLAN.md) §4.
- Vanilla Skyrim content must be kept away from the player (decision 0012).

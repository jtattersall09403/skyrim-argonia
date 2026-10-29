# Interior sun through windows on runtime 1.7.104

**Question** (2.W3 §a, decision 0026 §5). Which current mod or Community Shaders (CS) feature gives interior cells
window sunlight that follows the sun, and does it load on the pinned runtime 1.7.104?

**Method.** Repo notes (decision 0002, PLAN's graphics rows, old 0123), the CS repository through `gh` (releases, PRs,
issues, `src/Features/InteriorSun.{h,cpp}`), web search. Not fetched: the Nexus pages; deepwiki returned 429.

## Findings

| Candidate | What it does | Needs | On 1.7.104 | Notes |
|---|---|---|---|---|
| **CS Interior Sun** (feature 1-0-2) | Sun and moon cast real light and shadows into interiors, from the live sun direction of the weather system, so the patch moves with the hour. Only on opted-in cells: `InteriorSun.cpp:97` needs `IsInteriorCell`, `ShowSky`, `UseSkyLighting` and cell-flag bit 15. Can force two-sided rendering for unprepared meshes. PR #2319 (merged 2026-05-12) joins it to Volumetric Shadows. | CS, SKSE, Address Library, SSE Engine Fixes (hard dependency, issue #2724) | **Partial.** v1.9.0: "support Skyrim 1.7.99+" (PR #2674, 2026-08-28); last stable v1.9.1 (2026-09-24). Issue #2935 (2026-10-16): a 1.7.104 user on 1.9.1 with Engine Fixes 7.0.21 gets a launch error; closed without a fix shown. | Open source; a dependency the player installs, never shipped. |
| CS Volumetric Shadows / Lighting | Shadowed haze and shafts; in interiors they ride on Interior Sun. | CS | as above | The outdoor volumetrics of 0026 §5. |
| CS Skylighting, Light Limit Fix, Dynamic Cubemaps, SSGI/IBL | Sky occlusion, light count, reflections, indirect light. | CS | as above | None casts window sunlight. |
| ENB interior lighting | ENB's own renderer. | ENB | unchecked | Conflicts with CS (both replace the renderer; not verified); closed source. Ruled out. |
| Static beam meshes (ELFX-style light cones) | Fixed beams, faded by time and weather. | nothing | yes (plain records) | The owner-accepted fallback. |
| Window shadow / window light SKSE plugins | none maintained found | – | – | Unverified; not recommended. |

The time-of-day behaviour of Interior Sun is verified from source; loading on 1.7.104 is not (one failing user
report; the earlier crash cause, a hard-coded offset at `Hooks.cpp:1048` in issue #2678, was closed 2026-09-23 as
"not relevant anymore" without a confirmed fix).

## Recommendation

1. **Primary:** CS v1.9.1 with Interior Sun, plus Address Library (1.7.104 build), SKSE AE 2.3.1 and SSE Engine Fixes
   7.0.21, pinned by 0.3 and entered in the sourcing register when first used; proved in the 0.2 smoke run.
2. **Build side:** ArgoniaGen sets `ShowSky`, `UseSkyLighting` and bit 15 on each interior cell that has windows,
   from a per-cell column (the interior lighting template); windows need real openings, since the feature lights
   only what the sun reaches.
3. **Fallback** (CS fails on 1.7.104): a beam STAT per window, enabled by time of day through a condition on
   `GameHour` (a GLOB) and gated by weather; two or three yaw variants per window (morning, noon, evening) cover the
   sun's swing. Works on any runtime, no CS.
4. If CS fails on 1.7.104 and no fix ships, decision 0002's tie rule can move the pin to 1.6.1170, where CS is
   proven; that needs a decision record.

## The owed L4 check (tests/journeys/w3-interior-sun.md)

Two interiors with different window facings (a hall with several windows, a room with one), from a scene on the
base save; weather forced clear; stills at game hours 06, 12, 16, 20 set by console. The lit patch must move or
vanish between hours; a control still with bit 15 cleared shows no patch (so the check can fail); no crash in five
minutes; CS's log shows the feature loaded. On 1.7.104 first; if it fails, repeat on 1.6.1170 before any pin change.

Sources: [CS repository](https://github.com/community-shaders/skyrim-community-shaders),
[v1.9.1](https://github.com/community-shaders/skyrim-community-shaders/releases/tag/v1.9.1),
[PR 2674](https://github.com/community-shaders/skyrim-community-shaders/pull/2674),
[PR 2319](https://github.com/community-shaders/skyrim-community-shaders/pull/2319),
[issue 2678](https://github.com/community-shaders/skyrim-community-shaders/issues/2678),
[issue 2935](https://github.com/community-shaders/skyrim-community-shaders/issues/2935),
[issue 2724](https://github.com/community-shaders/skyrim-community-shaders/issues/2724),
[Address Library](https://www.nexusmods.com/skyrimspecialedition/mods/32444).

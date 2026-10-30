# 0010: Reuse first, in a fixed route order; the running game is the oracle; Ghidra is a scalpel

**Status:** decided 2026-10-27 (owner: "reuse as far as possible"; wants heavy use of the universal-modder /
Ghidra approach). Evidence: [um-ghidra-lens](../research/2026-10-27/um-ghidra-lens.md).

## Decision

1. **Route order for every feature** (universal-modder's "cheapest route first", adapted). Take the first that
   meets the feature's acceptance; record the route in the work package:
   1. **Data**: our plugin records, game settings, existing vanilla behaviour.
   2. **Existing mod as a player-downloaded dependency**, configured (and its API used).
   3. **Fork of an open-licence mod** (MIT/BSD/GPL with exceptions, licence obeyed, credited).
   4. **Our own Papyrus**.
   5. **Our own SKSE plugin code** (S2).
   6. **Our own deep hook or replacement screen** (S3).
   7. **Ask the owner** (never: make art beyond the decision 0006 exception, ship others' files, or copy
      decompiled game code; decompiling itself is a normal tool, decision 0003 §8).
2. **Study before building.** For each system, first read what owned games and existing mods already do:
   DS1R/DS3 data (combat), OpenMW source (Morrowind's formulas, dialogue filter semantics, disposition,
   persuasion: it is the readable Morrowind), Skyrim's own records (water, AI packages), mod source code
   where licences allow (FreeClimb GPL, Chocolate Poise MIT, Valhalla BSD-3, Precision/TDM/OAR/TrueHUD GPL with
   modding exceptions, SCAR MIT), and reference reimplementations (Faith Runner, AC1 Movement Rewritten,
   White Knuckle climbing note). Record findings in `docs/research/`.
3. **The running game is the oracle.** "Your reading of the code is not." Every behaviour claim is closed by
   an in-game check on the GPU box (testing level L4) with a check that can fail: trace replay, frame-window
   timestamps, state reads through the bridge, pixel or hash comparison, or the owner's checklist. Rules:
   prove the screenshot oracle is live (two frames differ), stop after 3 identical failures and diagnose,
   never let the thing under test own the test.
4. **Ghidra is a scalpel.** Used only for a named question the data, mod source and CommonLib headers cannot
   answer (example: how Skyrim computes submersion depth on placed water, if records do not show it).
   Method: headless Ghidra 12.x + PyGhidra scripts that decompile named functions (Faith Runner's pattern),
   seeded with the Address Library names database; MCP bridges (pyghidra-mcp, ReVa, GhidraMCP) only for
   interactive exploration. Output stays in `$ARGONIA_PRIVATE`, never in the repo; only derived facts are
   written down, with provenance.
5. **Parity documents.** Each port (combat, climbing, boats) keeps a parity table: feature, source value,
   our value, substitution and reason, check.
6. **universal-modder itself** (MIT) is vendored in 0.1 (its full skill set, agents and knowledge base: decision
   0020) as reference skills (`mod-any-game`,
   `reverse-engineering`, `game-automation`, the Bethesda playbook and the relevant field notes), adapted to
   this repo and credited; its safety rules (no anti-cheat titles, no DRM bypass, no redistribution) are
   ours too.

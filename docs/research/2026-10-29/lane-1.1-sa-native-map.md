# Lane report: 1.1 §a, the native map (paper lane)

Dated 2026-10-29. Deliverable: [native-map.md](../native-map.md). Test level L1 (doc completeness). The L4 proofs
belong to the 1.1 build lane, which runs §5's stubs as soon as the hands exist.

## Acceptance

| Item | Result |
|---|---|
| Every goal in `goals.md` has exactly one row | **pass**: 110 goals, 110 rows, 110 distinct ids, none missing, extra or duplicated (script output below) |
| Every Part 1 row names its L4 stub check | **pass**: 32 Part 1 rows name a stub, all 32 are defined in §5 with steps and the read that fails |
| Owner-call rows listed | **pass**: §1. No row is "none" on present evidence. Seven rows have losses the planner should raise with their chunk (G02.3, G05.2, G25.2, G27.3, G29.1, G36.1, G37.1) |
| `make check` green (links) | `tooling/check_links.py` exit 0; the full gate's result is in the hand-back message |

The count script (session scratchpad `tools/goals.py` + `tools/count.py`) assigns `Gss.n` = the n-th bullet
under the ss-th `###` of `goals.md`, then checks the map's rows (outside §5) and the row↔stub pairs:

```
goals in goals.md: 110; rows in map: 110; distinct row ids: 110
missing: none | extra: none | duplicated: none
Part 1 rows naming a stub: 32; stubs defined in §5: 32; row-stub pairs without a §5 definition: none
exit=0
```

## Findings that change the method (§4 of the map)

1. **The dialogue intercept has a route-1 option:** a player perk whose *Activate* entry has *Replace Default*
   (`BGSEntryPointFunctionDataActivateChoice.h:15-19`). The audit's guarded slot swap becomes the fallback, so 1.3 §b
   may not need 1.7.104 offsets at all.
2. **Vanilla skill and level gain go off by data:** AVSK `useMult` = 0 and `fXPPerSkillRank` = 0. The router only
   checks that `LevelUpMenu` never opens.
3. **One carrier actor value per hand** (P1) carries the score-and-curve maths into perk entry points, which keeps
   the 1.3 §a actor-value budget small.
4. **The ladder compiler links `skse/core`** (P5), so the formulas exist once.

## Owner addition

Nexus mod 28567 (a DS-style overhaul: poise, roll bands, bash-parry, riposte, backstab, backstep) is noted as a
candidate in G30.1, G30.2 and G32.1 and in the UNVERIFIED list. This lane did not read it; the planner's research
lane is evaluating it, and no route changed.

## skse/core left to us

Fifteen Part 1 modules (§6.1), about 3,800 lines with our own topic store and about 3,050 with the MorrowindRuntime
fork. Each has an interface sketch. Fourteen later modules are named with their chunk.

## Limits

- UESP and the CK wiki return 403 to fetches from this host, so the five web facts come from search excerpts.
  Engine claims are otherwise cited to CommonLibSSE-NG headers at `dec1be18`.
- 22 rows of UNVERIFIED claims are listed (§7), each with the stub or chunk that settles it.
- No research index entry was added: this lane may touch only its two files. The planner may list `native-map.md`
  in `docs/research/README.md`.

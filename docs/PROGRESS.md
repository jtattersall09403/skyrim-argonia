# Progress

One line per phase and, inside Phase 3, per block. Status: `todo`, `in progress (what is done; what is owed)`,
`done (the owner's issue)`, `blocked (why)`. Moved in the commit that changes it. Phases: [PLAN.md](PLAN.md).

| Phase | Status |
|---|---|
| [0](phases/0-play-machine.md) The play machine is back and vanilla Skyrim streams | done (2026-11-05 on a g6 spot; since 2026-11-07 the play machine is a g4dn.xlarge on demand in Paris eu-west-3b, i-003a8d8e08142cc5b, decision 0039, the g6 retired; setup green; Moonlight-Web paired; the owner's Steam login (#44); Skyrim 1.7.104.0, build 24914197, manifest read-only; the Creation Kit 1946180 for the Papyrus compiler; cards Argonia, Vanilla Skyrim, Desktop; no owner test by ruling, the Vanilla card is tried in the first walk) |
| [1](phases/1-stack-in-bmv.md) The stack, in BM&V as the default world | in progress (walk 3 fixes built and deployed 2026-11-08: the backstep clip cut at its first push, TrueHUD from the Combined preset, a Dark Souls backstab on a normal attack (our SKSE plugin), Skyrim music in BM&V's worlds; owed: the owner's walk, docs/owner-walk-checks.md section 5, and the pad checks of section 1) |
| [2](phases/2-first-act-on-paper.md) The first act on paper, the whole quest system adapted to BM&V, and the block set | done (2026-11-06; story #50) |
| [3](phases/3-building-blocks.md) The building blocks, proved once each | in progress (every step and checks A-D passed; "Block Test, the end" given an objective so the journal lists it, deployed 2026-11-08; owed: check 5.5) |
| [4](phases/4-first-act-built.md) The first act, built from the proven blocks | in progress (2026-11-08: built, read back and deployed (4d0b2d89): the opening MQ01 replaces the old start, MQ03-MQ05, Chainbreakers BC01-BC03 (BC02 in Blackrose's stone house), Night-Reed TG01-TG02, locals LQ25 and LQ30, the clean-up of every slice place; every read-back PASS, placecheck 120 placements and 395 models 0 failed; 119 people in the act's places talk, with rumours, warm and cool quest bands and after-quest greetings; owed: the owner's walk, issue #55, docs/owner-walk-checks.md sections 5 to 7) |
| [4a](phases/4a-talk-to-everyone.md) Talk to everyone in BM&V | in progress (recipe v2 is the skill talk-write: route directions, address by standing, BM&V-true facts, the naming rules; built for the act's places, 119 people in four worlds, talk_check 0 problems; next: the remaining settlements after the owner's walk of section 6) |
| [5](phases/5-scale.md) Scale | todo |
| [nw-01](phases/new-worldspace-plan/nw-01-map-extraction.md) New worldspace: Project Tamriel's Black Marsh map extracted and researched | done (2026-11-08: the map key, 258 places, 24 regions, 18 cultures, roads and borders, danger bands, terrain inputs, all in newworld/; the atlas https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g) |
| [nw-02](phases/new-worldspace-plan/nw-02-textures-plants-scatter-water.md) New worldspace: textured, planted, watered, navmeshed and with LOD, walkable in game | in progress (2026-11-08: road fixes and three studies running; the step table is in the phase file) |

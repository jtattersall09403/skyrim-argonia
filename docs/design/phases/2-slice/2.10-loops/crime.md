<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/crime.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: crime and the ledger (2.10 § Loops, lane 2.10-f)

Rule (decisions 0151 item 2, 0039, 0142; world/76 §124; lanes/2.10/briefs/rules.md):
a crime exists only when seen and is an entry on its region's Owing ledger,
assessed from `owing.json`; the entry clears itself after `amnestyHours` on the
lamp clock; every filed crime reaches faction standing with the witnessed
multiplier; striking a victim already hostile is self-defence and files nothing.
Eyes: none (data and numbers only).

Measures:

- `cd packages/game-core && npx vitest run src/crime src/combat/violenceHooks.test.ts src/ai/answeredViolence.test.ts`
- `cd packages/dialogue && npx vitest run`
- `cd packages/save && npx vitest run src/families/owing.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| fileCrime per kind (trespass, pickpocket, theft, assault, murder), seen | 5 of 5 filed, amount from the region row (theft perValue × value, at least min) | 5 of 5 (test row; owing.json rates are lane a's named blockers) | 2.8 s (29 tests, one run) | `crime/crime.test.ts` |
| fileCrime per kind, unseen (empty witnessIds) | 5 of 5 file nothing | 5 of 5, state unchanged | same run | `crime/crime.test.ts` |
| Amnesty: an entry older than amnestyHours clears as "amnesty"; one younger stays | 2 of 2 | 2 of 2 (71.9 h stays, 72 h clears at hour 172) | same run | `crime/crime.test.ts`; `crime-session.test.ts` |
| Standing: each kind reaches the victim's factions at weight × witnessed multiplier | 5 of 5 | 5 of 5 (-4, -10, -10, -40, -100), plus trespass with no victim on the assessor | same run | `crime/crime.test.ts` |
| Self-defence: a blow or killing on a victim already hostile files nothing; murder files on a kill of a non-hostile person | 2 of 2 | 2 of 2 (record hostile; fighting a prior blow) | same run | `crime/crime.test.ts`; `crime-session.test.ts` |
| Greetings: WorldState carries owing per region and the worst open crime; the owing greeting holds only with an open Owing in the region | every slice culture sheet | 51 of 51 culture sheets; 140 owing greetings re-conditioned onto `owingHere`, 47 reworded after the reader | 0.7 s (52 tests) | `dialogue/src/owing-greetings.test.ts` |
| Save: the owing family round-trips the ledger and refuses a wrong shape | green | green (round trip; 5 refusals) | 0.3 s | `save/families/owing.test.ts`; `crime-session.test.ts` seam |

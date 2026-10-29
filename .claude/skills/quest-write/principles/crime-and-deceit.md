# THEFT, FRAUD, SMUGGLING

Read with `general.md`. Evidence: `docs/research/2026-10-27/quest-shape-crime-and-deceit.md` (methods A to F).
A theft the player must **solve** also reads `investigation.md`.

## THEFT the player commits (a heist)

- **Problems, not puzzles:** at least three routes (sneak, bribe, disguise, distract, force), each with a
  visible requirement and a price; the player never has to read the designer's mind.
- **The plan is half the play.** Score, gather (three sources: bought, overheard, read), surveil (one fact
  only learnt on site), prep (change the odds: a bribed guard, a forged pass), operation.
- **Three plan texts** per target: complete, out of date, and one person's partial memory.
- **Guards know only what they saw or were told**; no global alarm.
- **Failure ladder:** noticed (a search), identified (a bounty or faction reaction), compromised (the item is
  moved, a partner turns). Each rung has a way back; no twist that scraps the plan.
- **Escape and aftermath:** who pursues and where they stop; what changes after 1, 3 and 10 days.
- **The owner has a visible loss**, so the theft means something.
- **Reward varies by route and cleanliness.**

## THEFT the player solves

- The true sequence first (who, when, how, what moved, where it is now), with any staged layer on top.
- A ledger: suspect, clue, source, what it rules out; 4 to 7 clues; each conclusion on two independent clues.
- A red herring with a stated fact that eliminates it; every suspect hides a secret that is not the crime.
- A wrong accusation is allowed, costs something in the world, and leaves the true culprit findable until a
  deadline stage.

## FRAUD

- Name the lie, its scale, who gains and who loses (a fraud has victims the player can meet).
- At least two records that must agree and one mismatch checkable by eye; arithmetic small enough to do in
  the head. The player compares; nothing is highlighted.
- Records are readable items or topics in distinct voices; one new rule of checking per stage.
- Confronting with the right records opens endings: expose, blackmail, join, let lie, each changing prices,
  faith or standing.

## SMUGGLING

- Cargo, its tell (smell, weight, noise, seal), origin, drop, two routes.
- Named inspectors with a method and ways past (bribe, hide, distract, forge, wait for the shift change); the
  shift change is a world fact in a topic.
- The cargo's nature is known or learnt before the point of no return; the player may drop, deliver or sell
  out to the authorities. If it is people, the player meets them before choosing.

## Record additions (`shapeData`)

- THEFT (commit): `score`, `sources` (3), `onSiteFact`, `planTexts` (3), `routes` (3+), `failureLadder` (3),
  `escape`, `aftermath` (1, 3, 10 days).
- THEFT (solve) and FRAUD: `ledger` (rows of suspect or record, clue, source, rules out), `redHerring`,
  `wrongAccusation`.
- FRAUD: `records` (2+), `mismatch`, `victims`.
- SMUGGLING: `cargo`, `tell`, `routes` (2), `checkpoints` (inspector, method, ways past), `cargoReveal`.

# DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE

Read with `general.md`. Evidence: `docs/research/2026-10-27/quest-shape-social.md`.

## All four

- **Groups are made of people who disagree.** Each party has at least two members who argue its case and
  one who privately doubts it; the player can talk to the doubter.
- **Reveal order makes a person grey.** Show a party's good case before the damning fact (the Bloody Baron
  sheltered Ciri before his abuse came out). Write a reveal-order table: every damning fact against every
  sympathetic one, numbered in the order the clues surface, whatever route the player takes.
- **The hardest party mirrors something the player is likely to value.**
- **Reputation is plural:** a ruling moves at least two standings in opposite directions.
- **No hidden meters and no single deciding stat or fact.** A failed attempt closes one route with a written
  line and opens another topic.
- **The world sets the deadline** (a funeral, a market day, the flood season), announced in talk and
  advancing without the player; the journal never says who was right.
- **Aftermath:** for each ending, three places within a day's travel change, one greeting changes, one new
  topic appears, one standing moves, one thing becomes impossible.

## DISPUTE

- A claim ledger: each party's basis (law, custom, deed, kinship), strength, weakness and price; each claim
  holds one true and one false or partial element.
- Three verdicts: side A, side B, and a settlement that costs the player, findable through clues alone.

## NEGOTIATION

- For each side: wants, will give, will never give.
- Leverage is named things or facts held by named people (a debt note, a witness, a harvest, a boat);
  gathering it is the middle of the quest. Information is currency: spent facts stay spent.
- Disposition without dice: each side voices two or three objections, each with an answer in the world
  (a document, a promise, a witness, a sacrifice); the journal lists the open objections.
- The agreed terms are written down in the journal and come back later.

## SUCCESSION

- At least three kinds of legitimacy in conflict (blood, the Hist's choice, a vote, a will, a deed).
- Each candidate has one real strength and one real fault; none is both legitimate and fit.
- A vote ledger: voters, what each wants and fears, what each knows of each candidate; each backer is won by
  one thing only.
- The inheritance carries a cost; the dead speak through documents, memory or custom.

## BONDAGE (the Owing, indenture, hierarchy): handle seriously

- A bondage sheet: the debt, the holder, the terms, the exit in law, the exit in practice, and what the bound
  person wants. They have knowledge, goals and the right to refuse help, with reasons.
- Show the bound person living a life inside the bond before the player knows.
- The system is the wrong, not one cruel man; holders have reasons, some sympathetic.
- **No counters, scores or rewards scaled by the number freed;** the freed are people, not currency.
- The player's rashness lands on the bound (Freedom Cry's retaliation); write the cost to the bound for every
  player act.
- Freedom has a cost and an aftermath for the freed person; small, slow resistance sits beside the big act.
- If the player cannot fully succeed, that limit is deliberate and explained. Not mapped one to one onto a
  real-world group.

## Record additions (`shapeData`)

- All four: `revealOrder`, `aftermath`, `deadline`.
- DISPUTE: `claims` (2+, each basis, true element, false element, price), `verdicts` (3).
- NEGOTIATION: `sides` (wants, gives, neverGives), `leverage`, `objections` (each with its answer).
- SUCCESSION: `legitimacies` (3+), `candidates`, `voteLedger`.
- BONDAGE: `bondageSheet`, `costToTheBound`.

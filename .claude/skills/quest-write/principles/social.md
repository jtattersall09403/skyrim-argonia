# DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE

Read with `general.md` (which holds the source tags' key). A social quest is still won by acts: the talk sets up
the stakes, and the player settles them with a lock, a key lifted, a fight, a persuasion, a thing brought. Law and
custom are background; no climax is a hearing or a table [OB vibe; OB skills].

## All four

1. **Groups are made of people who disagree.** Each side has at least two people who argue its case and one who
   privately doubts it; the player can talk to the doubter [SO P1].
2. **Reveal order makes a person grey.** Show a side's good case before its damning fact, whatever route the player
   takes (the Bloody Baron sheltered Ciri before his abuse came out) [SO P4; SO M4].
3. **The hardest side mirrors something the player is likely to value** [SO P5].
4. **People are not archetypes**: nobody stands for a whole group [SO P10].
5. **Standing is plural**: an outcome moves at least two standings in opposite directions (stored numbers, regard)
   [SO P3].
6. **No hidden meters and no single deciding check or fact.** A failed attempt closes one route with its written
   line and opens another topic [SO P8; SO A].
7. **Why now is told and found, never timed**: the people say what makes it matter now, and the state the player
   finds shows it; the journal never says who was right [SO P9; ES P13].
8. **The player stays a participant and owns a consequence they can name** [SO P2].
9. **Afterwards is found**: each outcome changes a greeting, opens a topic, moves a standing, and takes someone or
   something away (switched off while the player is elsewhere) [SO P6; SO M12].
10. **Pace by alternating talk, travel and risk**; too many talking stages together drags, and the purpose is
    restated when play runs long [SO P17].
11. **Two sides play differently**, and the map changes after the choice [SO P11].

## DISPUTE

1. **Each side's claim** rests on custom, a deed or kinship, with its strength, its weakness and its price, and holds
   one true and one false or partial element [SO M1].
2. **Three outcomes**: side A, side B, and a third way that costs the player, findable through clues alone. Each is
   reached by an act (the proof brought, the thing taken, the liar faced), never by a ruling [SO M2;
   OB vibe].

## NEGOTIATION

1. **For each side**: what it wants, what it will give, what it will never give [SO C].
2. **Leverage is a named thing or fact held by a named person** (a debt-knot, a witness, a boat, a secret); getting
   it is the middle of the quest, by lifting, stealing, fighting or persuading for it. Spent facts stay spent
   [SO M5; SO M6].
3. **Each side voices two or three objections, each answered in the world** (a thing shown, a promise, a witness, a
   sacrifice); a person yields when the stated objection is answered, never on a hidden roll [SO M8; SO M7].
4. **The terms come back later**: a stored number a later greeting or quest reads [SO C].

## SUCCESSION

1. **At least three kinds of right in conflict** (blood, the Hist's choice, a deed, the dead's wish) [SO C].
2. **Each candidate has one real strength and one real fault**; none is both rightful and fit [SO M10;
   SO A].
3. **Each backer is won by one thing only**, and that thing is an act: a deed done, a thing taken back, a rival faced,
   a persuasion [SO P12; SO M10].
4. **The inheritance carries a cost; the dead speak through memory, custom or a carved thing** [SO C].

## BONDAGE (the Owing, indenture, hierarchy): handled seriously

1. **The bond**: the debt, who holds it, what it grows by, the way out by custom, the way out in practice, and what
   the bound person wants. They have knowledge, goals and the right to refuse help, with reasons [SO M13].
2. **The bound person is met living a life inside the bond before the player knows it**: placed at their work, with
   topics of their own [SO P13].
3. **The system is the wrong, not one cruel person**; holders have reasons, some sympathetic [SO C].
4. **No counters, scores or rewards scaled by the number freed**; the freed are people, not currency [SO P15].
5. **The player's rashness lands on the bound**: write what each act costs them [SO P14; SO M14].
6. **Freedom has a cost and an afterwards for the freed person**; small, slow resistance sits beside the big act
   [SO P16].
7. **If the player cannot fully succeed, the limit is deliberate and explained**; not mapped one to one onto a
   real-world group [SO C].

## Record additions (`shapeData`)

- All four: `revealOrder`, `afterwards`; DISPUTE and SUCCESSION also `whyNow`.
- DISPUTE: `claims` (two or more: each basis, true element, false element, price), `outcomes` (three, each the act
  that reaches it).
- NEGOTIATION: `sides` (wants, gives, never gives), `leverage` (each thing or fact, who holds it, how it is got),
  `objections` (each with its answer in the world).
- SUCCESSION: `legitimacies` (three or more), `candidates`, `backers` (each: wants, fears, the one act that wins
  them).
- BONDAGE: `theBond`, `costToTheBound`.

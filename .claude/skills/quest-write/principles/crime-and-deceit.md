# THEFT, FRAUD, SMUGGLING

Read with `general.md` (which holds the source tags' key). A theft the player must **solve** also reads
`investigation.md`.

## THEFT the player commits (a break-in)

1. **A problem with several answers, not a path**: the prize sits behind a lock, a key someone carries, a keeper who
   can be talked round or paid, and someone who will fight; each way has a visible requirement and a price, and the
   player never has to read the designer's mind [CD P1; CD P12].
2. **Show the goal, not the way**: the marker is on the prize or its keeper; the ways in are told by people and seen
   on the spot [CD P3].
3. **Gathering is half the play.** Two or three people each give one piece: where it is kept, who carries the key,
   the keeper's weakness (a price, a fear, a debt). They do not all agree: one is right, one is out of date, one
   remembers half. One fact is learnt only on the spot, from what the player sees there (the box in the store, a
   second leaf under the first) [CD P2; CD MA].
4. **The prize is an owned thing behind a lock whose key a person carries**, so Skyrim's own crime system makes the
   tension: taken in sight of its owner or a guard it is a theft with a bounty; a bungled pickpocket turns the
   keeper on the player. The quest never checks whether the player was seen, and the job stays open whatever
   happened, because the hand-in asks only that the thing is held [CD P5; CD P11; MW §6.3].
5. **Failure becomes a complication, never the end of the job**: a broken pick is another try, a refused persuasion
   leaves the key and the fight, a death leaves the key on the body [CD P4; CD MA].
6. **Preparation changes the odds**: a key bought from a servant, a keeper softened by a gift, a watcher paid; each is
   a line that gives a thing or sets a stored number [CD MA; CD MC].
7. **An inside hand opens one way at a price**: a person with a weakness lets the player in and asks a favour that
   falls due later [CD MC].
8. **The theft has a victim the player can meet, and someone pays for it**: the keeper, the people who stayed, the
   player's own name. Say who, and what the player finds afterwards [CD P10; CD P5].
9. **The reward differs by route and by who was hurt** [CD P13].

## THEFT the player solves

1. **The true sequence first**: who, when, how, what moved, where it is now; with any staged layer on top (what
   the player first sees is a cover) [CD MD].
2. **The suspects**: for each, what points at them, what clears them, and a secret they hide that is not the crime;
   four to seven clues; each conclusion rests on two independent clues, a thing and a witness where possible
   [CD MD].
3. **A red herring with a stated fact that removes it** [CD MD].
4. **Confirm in a batch**: the person who hears the player's account says how many parts are right, not which (a
   stored number per part shown, read by their line) [CD MD; CD P6].
5. **A wrong accusation is allowed and costs something** in the world (a ruined name, a person gone, lost standing);
   the true culprit stays findable until the confrontation ends the quest [CD MD; CD P8].
6. **No oracle**: testimony and things only, nothing the period could not know [CD MD].

## FRAUD

1. **Name the lie, its scale, who gains and who loses.** A fraud has victims the player can meet [CD ME; CD A].
2. **The proof is a thing or a person, not a reading exercise**: the real seal beside the false one, the full sack
   beside the light one, the true relic, a witness who saw it done; or, where paper truly belongs, the one paper the
   liar keeps, which the player steals, swaps or burns. The player brings it; nothing is highlighted, and any sum is
   small enough to do in the head [CD P7; CD ME; OB vibe].
3. **Each step puts one new thing in the player's hands that the liar must answer** [CD ME].
4. **Facing the liar with the proof held opens the endings**: expose, take a share, join, let it lie; each changes
   prices, faith or standing [CD ME; CD P8].

## SMUGGLING

1. **The cargo, its tell (smell, weight, noise, seal), where it comes from and where it goes, and two ways through**
   [CD MF].
2. **Named people stand in the way**, each with a way past by skill: paid, persuaded, sneaked past (the crime system
   does the watching), a locked gate picked, or fought [CD MF; CD P11].
3. **The cargo's nature is known or learnt before the point of no return**; if it is people, the player meets them
   before choosing to deliver, drop or sell out [CD MF; CD A].
4. **After the delivery a result is seen** [CD MF].

## Anti-patterns

One corridor, one lock and a speech; a thieves' finale that is a dungeon with a boss; a twist that scraps the
player's plan; a journal that states the conclusion; a fraud without a victim; guards that share what they know at
once [CD A].

## Record additions (`shapeData`)

- THEFT: `theftMode` (`commit` or `solve`).
- THEFT (commit): `prize` (what and why it matters to whom), `kept` (where, under whose eye, the lock and its level,
  the key and who carries it), `tellers` (who tells the player which piece), `waysIn` (each way by skill and its
  price), `goesWrong` (what goes wrong on each way and what is still open after), `afterwards` (who pays, and what the
  player finds).
- THEFT (solve): `suspects` (each: what points at them, what clears them, their own secret), `redHerrings`,
  `confrontation`, `nodes`, `leads`.
- FRAUD: `lie` (what is false, who tells it, who gains), `victims`, `proof` (the thing or person, and how the player
  gets it), `confrontation`.
- SMUGGLING: `cargo`, `tell`, `waysThrough`, `watchers` (who stands in the way and the way past each), `cargoTruth`.

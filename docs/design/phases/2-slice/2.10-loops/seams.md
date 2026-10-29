<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/seams.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the 2.10 seams (lane 2.10-j)

A seam is the transition into and out of a 2.10 system inside a player's
journey. One row per seam, each a scripted headless session on the real
packages and the published slice data (`packages/scene/src/interact/seams-session.test.ts`,
the `2.10 seam sessions` block), each ending in a save round trip of the
families it touched into a fresh registry with equal state. Every row names
two owners (the system on each side); a red goes to both.

On demand only (`JOURNEY=1`): nothing here joins check.mjs, CI or a regular gate.
Run: `cd packages/scene && JOURNEY=1 npx vitest run src/interact/seams-session.test.ts -t "2.10"`.

Written before the first measure; results and elapsed filled from the first run (nine rows, one `it.todo`).

| Seam (owners) | Headless measure (bar) | Result | Elapsed |
|---|---|---|---|
| steal seen → ledger → greeting (2.10 d/f, 2.5 dialogue) | an owned thing taken while its owner is engaged files a theft through the walk's crime host; the ledger holds it; the dialogue world's `owingHere`/`worstCrime` reads it for the region; owing round-trips | green: theft filed under the owner's eyes, greeting `greeting.faction-an-xileel.crime`, owing restored equal | 26 ms |
| crime → faction standing (2.10 f, 2.8 factions) | a seen crime against a faction member lowers standing by the registry's weight; standing round-trips | green: reputation = theft weight x witnessed multiplier (-10), restored equal | 7 ms |
| resist → answered violence → clear → peaceful place (2.10 f, 2.7 answered violence) | resist at the stop files assault and turns the watch hostile (`answeredDisposition`); paying later settles the place (`placeCleared`) and the watch is peaceful; violence round-trips | green: resist files assault, the toll-holder and the watch turn hostile; paying settles the place; violence restored equal | 12 ms |
| custody → clock → people's day → progression (2.10 f, 2.4 people, 2.8 progression) | serve moves the lamp clock by amount × custodyHoursPerNushmeeko, catches the people up once at the wake minute, the custody post is the place spot, pending skill progress is forfeit; a person's block changes across the span; progression round-trips | RED (last clause only): clock +10.8 h = owed x hours-per-nushmeeko, post `socket.riverwalk.idle-toll-holder-work`, progress forfeit, a person's block moves, progression restored equal; serve's single `catchUp` is unobserved: `stealthRig.ts:460` passes no `catchUp` to `createInteractSession` | 24 ms |
| pick → Security use → rank (2.10 d, 2.8 progression) | a worthy pick reports a Security use to the progression store and the skill's progress rises; progression and locks round-trip | green: Chasepoint held-back pick raises Security xp and the use log; progression and locks restored equal | 8 ms |
| trap → effect stack → hit reaction (2.10 d, 2.9 magic, 2.7 combat) | an unprobed trap's open lands its effect on the player's timed stack through the hostile cast path, plays its family, and owes the flinch (`playerFlinch` queue); the timed stack and locks round-trip | green: crate trap fires `projectile`, flinch owed, poison on the timed stack; magic stack and locks restored equal | 7 ms |
| sneak → combat: eye → engaged → sheathed (2.10 b/c, 2.7 combat) | crouched and unseen the eye reads hidden; a blow from behind takes the band (`sneakAttack`), engages the struck, its alarm turns the rest; the eye reads detected; the hands sheathe by the runtime's step; inventory round-trips | green (the alarm call turns the rest suspicious, not engaged, by design): hidden, band taken, struck engaged, eye detected, sheathed by the step; inventory restored equal | 17 ms |
| pickpocket a key → open its lock (2.10 e, 2.10 d) | a lifted key opens its door's lock at the press with no screen (`openWithKey`); carried, inventory and locks round-trip | green: the lifted key opens `lock.riverwalk.door-1` at `requestLock` with no screen (the rig's `press` handles lids only, so the door press is called on the session); carried, inventory, locks restored equal | 8 ms |
| the save round trip of ledger, lock states, carried, zones and detection (2.10 a/d/e/f, save) | owing, locks, carried, standing and violence restore equal into a fresh registry; zones need no save (records); detection does not save (observers reset on load: a fresh walk's notices are empty) | RED (rig comparator only): every family restores equal (`toEqual`), observers empty after load, no zone or detection family; the journey `save` step reads false because `stealthRig.ts:401` compares `JSON.stringify` and violence's maps come back key-sorted | 13 ms |
| crouch → swim (2.10 b, 2.12 swim) | named gap: the water rows and the seam's close are 2.12's, which runs after 2.10 (`it.todo`) | named gap (`it.todo`): 2.12 closes it | - |

# Actions: what the player does

Read for every quest. Owner ruling (0017 §9): nearly every quest makes the player **use their skills**, in a
wide, creative variety of combinations; a chain of "talk to X, then Y, then Z" is not a quest. Evidence:
`docs/research/2026-10-27/quest-actions-and-skills.md` (its verb families, ten combination patterns, faction
profile method and variety measures; its thresholds are inferences, so they are starting values to tune).
Draft: P4-WP4.0 merges this with the old verb tags (`docs/design/quests/00-overview.md` §4) and each faction's
profile from 40-factions.

## Rules

1. **Every stage that is not an ending has at least one action** with its family, verb and skill (the record's
   `actions`, or `actions` on each of its `approaches`). Talking is an action only when it uses a skill:
   persuading, bargaining, intimidating, presenting evidence, lying, accusing.
2. **A quest uses at least two families,** and at least one stage offers approaches from different families
   (a talker, a thief, a fighter and a mage can each get through it).
3. **Families:** combat (melee, ranged, magic, boss, defend, ambush); stealth (sneak, pick a lock, pickpocket,
   disguise, plant, escape); observe (spy while hidden, examine, track, read); speech (persuade, bargain,
   intimidate, lie, present evidence, accuse); traversal (climb, swim, dive, pole or sail a boat, run, cross
   flood); acquire (find, take, gather, buy, steal); craft (alchemy, enchant, repair, forge); magic outside
   combat (detect, water-breathe, levitate, charm, summon); place (clear a cave or ruin, defend a spot, open a
   route). Black Marsh gives its own: diving flooded ruins, poling channels, climbing a Hist, tracking in mud.
4. **Combine and escalate:** later stages combine families the earlier ones taught (watch the route, then
   sneak in by it, then forge the ledger found there, then persuade the clerk with it).
5. **Faction lean:** a faction quest draws most of its actions from its profile (assassins: stealth and
   killing; thieves: stealth and theft; fighters: combat; mages: magic; detectives: observe and speech, with
   whatever the case needs), and each rank adds a verb.
6. **Variety is counted:** within a line or a region packet, no two quests share the same family pair as their
   main actions, and no verb is the main action of consecutive quests.
7. **Actions fit the person and the place:** the action a stage asks for follows from the truth (a body under
   water means a dive; a guarded store means a lock, a bribe or a distraction).

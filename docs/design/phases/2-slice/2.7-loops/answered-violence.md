<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/answered-violence.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: answered violence (2.7 § b, lane 2.7b4)

Rule (decision 0142 § 3): a blow is answered by the victim and kin; a
killing turns the whole place hostile until 2.10's amends
(`makeAmends(state, placeId)`); a victim already hostile to the player is
self-defence and no crime. Code: `packages/game-core/src/ai/answeredViolence.ts`.

**Kin** are the victim's household: the records sharing the victim's home
socket (`home.home.socketId`) or bed socket (`home.bed.socketId`), plus the
records of the place sharing a faction id with the victim. Witnesses who are
not kin only raise the alarm; their own fightFleeAlarm decides fight or flee
once the place turns.

Village: Claywater Station (`place.imperial-fringe.claywater-station`, 17
records: 7 people, 10 creatures, no watch, none of the three hostile
places). The overseer row uses Opening Work Camp
(`place.pirate-freeholds.opening-work-camp`), the slice's one household with
fight above flee.

Command for every row: `npx vitest run packages/game-core/src/ai/answeredViolence.test.ts packages/save`
Capture for every row: [test-output.txt](../../../../lanes/2.7/b-shots/violence/test-output.txt)
(15 passed). Reader checklist: the named test passes by its assertions.

| Measurement | Place | Who fought | Who fled | When the place turned | Capture |
| --- | --- | --- | --- | --- | --- |
| (a) strike n1 | Claywater Station | none | n1, n1-2, n1-3 (fight 20, flee 40); `stepReaction` mode `fleeing`; well-keeper witness only raises the alarm; the other 13 records calm | never | test-output.txt, "(a) a blow" |
| (a) strike overseer n3 | Opening Work Camp | n3, n3-2 (fight 60, flee 10), `coming`; the families calm | none | never | test-output.txt, "(a) a blow on an overseer" |
| (b) kill n1 | Claywater Station | the place's people by their rows (`coming` when fight ≥ flee); its creatures stay calm (wildlife is no party to a killing) | poler, n1-2, n1-3, n2, n2-2, well-keeper, `fleeing` | at the killing; `hostilePlaces` holds the place; Opening Work Camp unaffected | test-output.txt, "(b) a killing" |
| (c) strike then kill a hostile bog-dog; strike then kill a victim already fighting | Claywater Station; Opening Work Camp | no kin provoked | none | never; state unchanged | test-output.txt, "(c) striking, then killing" |
| (d) `makeAmends` | Claywater Station | none | none | place cleared; other places keep their provoked records | test-output.txt, "(d) makeAmends" |
| Save family `violence` v1 round-trip | n/a | n/a | n/a | n/a | test-output.txt, "violence save family" |
| Household strip (kin of a struck person, drawn or fled) | Claywater Station | n1, n1-2, n1-3 answer | n1, n1-2, n1-3 by their rows (flee) | `fleeing` to about 6 s, then `returning`; the village's other people were not framed | `lanes/2.7/b-shots/violence/household.png` (data `household.json`). Reader: kin run away across the frames and the seated villager stays calm (PASS); camera tracks the household (4 of 4 in frame every frame); PARTLY on breakage: runners look slightly airborne, the 10 s frame has a water artefact, n1-3 is hard to find|

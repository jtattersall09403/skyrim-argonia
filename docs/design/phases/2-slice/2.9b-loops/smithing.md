<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/smithing.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: smithing (2.9b, lane c)

One row per thing smithing must do. The numbers are the pure runtime
(`packages/crafting/src/smithing.test.ts`) and the headless station session
(`packages/scene/src/interact/crafting-session.test.ts`, "smithing at the
station"), which drives `createInteractSession`'s forge and temper verbs over
the real item rows, skills.json smithing (`temperGrades`, `temperPerGrade`),
curves.json use points, the 2.8 progression store and the inventory save
family. No GPU step: smithing has no new art.

Written before the first measure; results and elapsed filled after (`smithing.test.ts` 13 tests, 4 s; the station session 1 test, 4 s; game-core inventory and interaction 136 tests, 6 s).

| Row | Headless measure (bar) | Result | Elapsed |
|---|---|---|---|
| Forge gate | tier ≤ 1 + floor(effSmithing/14) at effSmithing 0, 13, 14, 27, 28 against tiers 1, 2, 3; refused above, `tier-too-high` | green: tiers 1,1,2,2,3; above refused `tier-too-high` (`tierForEffSkill`) | 4 s |
| Forge output | inputs leave, the output is carried at max condition, `{smithing, forge points}` reported | green: inputs out, output at condition max, `{smithing, 5}` | 4 s |
| Temper gates | grade g+1 only at effSmithing ≥ 25 / 55 / 80, at most 3, one material each | green: 24/54/79 refused `grade-gated`, 25/55/80 pass, grade 4 `max-grade`, 3 bars spent | 4 s |
| Temper stations | weapon at a grindstone, armour at a workbench, nothing else | green: wrong station refused, non-gear `not-temperable` | 4 s |
| Temper bonus | equipped grade-3 blade and cuirass at 1 + 3 × temperPerGrade of base | green: blade and cuirass at 1.24× base (temperPerGrade 0.08; the brief's "about 1.26" is 1.24 by the data) | 4 s |
| Band bound | grade 3 on each tier-1 set under every tier-2 base (§124) | **red by design, reported**: iron (0.85) at grade 3 is 1.054, over every tier-2 set (bone 0.90, bronze 1.00, steel 1.00, imperial 1.02); studded 0.992 and wood 0.93 over bone. Test pins the crossings; never retuned | 4 s |
| Instance rows | a tempered copy keeps its row and grade beside plain copies; a mend keeps the grade | green: copy 1 tempered beside copy 0; a new plain copy joins the plain row; repairStroke keeps the grade | 6 s |
| Station verbs | forge {forge, mend}, grindstone {temper}, workbench {temper, mend}; unlisted class mends | green: forge {forge, mend}, workbench {temper, mend}, grindstone {temper, mend} by lane a's data (the brief said {temper}); an unlisted class mends | 4 s |
| Mend unchanged | interact.test.ts mend case and its onSkillUse report | green: interact.test.ts mend case; only its activation shape gained `stationId`, `verbs` | 11 s |
| Skill rise | forging raises Smithing in the store, the sheet reads it, every report is kind forge/temper | green: forging raises Smithing in the 2.8 store, `live.skills.smithing` equals it, every report kind forge then temper (the hosts now file `skillUseReport`, no longer always repair) | 4 s |
| Save | temperGrade round-trips through the inventory family | green: inventory family JSON round trip equal, grade 1 kept | 4 s |

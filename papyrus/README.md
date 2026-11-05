# papyrus

Our Papyrus scripts: quest-stage fragments, alias and trigger scripts, and the glue a record cannot do
(PLAN Phase 2, block B5 settles the shapes). Compiled on the play machine by
`infra/gpu-box/records_jobs.sh papyrus` (the Creation Kit's compiler against its `Scripts.zip`, never committed);
the `.pex` files are build outputs and are sent by `infra/gpu-box/deploy.sh`.

| Script | What it does |
|---|---|
| `ARG_StartQuestScript.psc` | the seed of a start quest: on `OnInit`, fade to black and move the player to a marker. The fallback for the Black Marsh start if the Live Another Life addon route fails (PLAN Phase 1) |

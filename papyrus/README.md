# papyrus

Our Papyrus scripts: quest-stage fragments, alias and trigger scripts, and the glue a record cannot do
(PLAN Phase 3 settles the shapes). Compiled on the play machine by
`infra/gpu-box/records_jobs.sh papyrus` (the Creation Kit's compiler against its `Scripts.zip`, never committed);
the `.pex` files are build outputs and are sent by `infra/gpu-box/deploy.sh`.

| Script | What it does |
|---|---|
| `ARG_QF_MQ101.psc` | MQ101's fragment script in `Argonia.esp`'s MQ101 override: the engine starts MQ101 on a new game; stage 0 starts `ARG_Opening` and stops MQ101 (no Helgen) |
| `ARG_StartQuestScript.psc` | `ARG_Opening`'s script: the player to `ARG_OpeningMarker` on Lilmoth's dock, the race menu, the roughspun tunic and footwraps, stage 10's journal line (PLAN Phase 1, the start) |

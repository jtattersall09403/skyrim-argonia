# papyrus
Our Papyrus: generated quest-stage fragments and the glue the engine requires. Logic stays out of Papyrus (1.1); every script here is listed with why it is not C++.

Compiled on the game machine by `infra/gpu-box/papyrus-compile.ps1` (the CK's compiler, base sources from its `Scripts.zip`, never committed); the `.pex` files are build outputs.

| Script | What it does | Why Papyrus, not C++ |
|---|---|---|
| `ARG_StartQuestScript.psc` | new game: black screen, the player moved to the holding cell (0.4 §b) | it is the quest's own `OnInit`, the engine's hook for a start-game-enabled quest; three engine calls, no rule |

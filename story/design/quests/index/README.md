<!-- imported unchanged from elder-souls-argonia docs/quests/index/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# The quest index — why it exists, the taxonomy, the novelty rule

> Module of the quest/narrative master plan (see [../README.md](../README.md)).
> **Every agent authoring a new quest reads this file first.** The first plan's generated quest views that sat
> beside it are retired with that plan; the quests to scan are the line's and the place's own records.


## 47a. Why this index exists

Quests are authored packet by packet, by fresh agents. Without a shared view,
three regions will each get a smuggler-with-a-secret and a haunted ruin, and
nobody will notice until playtest. The full briefs live in
[the main plot](../lines/main-plot.md), [the faction plots](../lines/) and
[50-side-quests.md](../50-side-quests.md); reading all three before writing one
village quest is context bloat. **The index is the cheap summary layer**: one
row per quest, enough to spot a collision.

It used to be a hand-maintained table, which could not take eight region agents
at once and which nothing checked. It is now data plus a validator, which is
what [90-production-sequence.md](../90-production-sequence.md) always intended
for production stage Q1.

## 47b. The shape taxonomy

Every quest declares **one primary shape** (first in `shapes`) and up to two
secondary shapes. The taxonomy is deliberately about *premise*, not verb — the
verb tags (`COMBAT`, `DIVE`, `HEIST`) already exist in
[00-overview.md](../00-overview.md) §4 and answer a different question.

| Shape | The situation |
|---|---|
| `THEFT` | Something must be taken, or was taken |
| `MURDER` | Someone is dead and the question is who or why |
| `MISSING` | A person, thing or place has vanished; find it |
| `DISPUTE` | Two parties both have a real claim |
| `FRAUD` | Someone is lying at scale — records, trade, faith, insurance |
| `PREDATOR` | A creature or hazard threatens a community |
| `CONTAMINATION` | Disease, blight, poison, bad water, bad sap |
| `SMUGGLING` | Goods or people move where they shouldn't |
| `HAUNTING` | The dead, or something wearing their shape, will not settle |
| `RITE` | A ceremony must happen, or must be stopped, or has gone wrong |
| `SUCCESSION` | Who inherits an office, a name, a debt, a tree |
| `BONDAGE` | Someone is held — an Owing, an indenture, a hierarchy |
| `RECKONING` | An old crime surfaces and someone must answer for it |
| `EXPEDITION` | Reach somewhere dangerous and come back |
| `NEGOTIATION` | A deal, treaty, charter or price must be settled |
| `WONDER` | Something strange, with no faction stakes and no explanation |

## 47c. The novelty rule (binding on every new quest)

Before a brief is written, the authoring agent must:

1. **Scan the quests** of the line and of the place for the proposed quest's `shape`.
2. Apply the **collision test** — a proposed quest collides if it shares its
   **primary shape** with an existing quest *and* one of:
   - the same region packet;
   - the same faction line;
   - the same reversal (the twist is the same twist);
   - the same resolution set (the choices offered are the same choices).
3. On collision, do one of: **differentiate** (change the reversal, the
   claimants, the resolution, or the verb), **merge** into the existing quest
   as a stage or variant, or **drop** it and author something the index shows
   is missing.
4. **Declare the row's `touches` list** (shared NPCs, LOCs, STATEs, items,
   variables — read or write) and check tier direction per
   [the owner's bar ('Anyone can die')](../../owner-bar.md): a brief may not write anything
   owned by a higher tier.
5. **Add the row to the data in the same change** as the brief — to
   `world/sources/quests/local-<region>.json` for a region agent — then run
   `python3 -m worldgen.quests --check --sync` and
   `python3 -m worldgen.export_quest_index`.

Two supporting rules:

- **Shape budget per packet** *(strong default — a recorded one-line reason may
  depart from it)*: no primary shape may exceed **~20%** of a packet; nor may one
  appear in consecutive M/L quests. A packet whose rows are five `DISPUTE`s
  out of eight is rejected regardless of individual quality. The validator
  enforces this per **line** where a quest has one and per packet otherwise;
  a departure is recorded in the packet file's `budgetExceptions`; three
  are recorded today.
- **Cover the board.** Each packet introduces at least one shape new to that
  region, and includes at least one `WONDER`.

Validator support is specified in
[80-technical-architecture.md](../80-technical-architecture.md) §63 and
implemented in `tooling/world-generation/worldgen/quests.py`.

<!-- imported unchanged from elder-souls-argonia docs/decisions/0042-buildout-steers-and-engineering-standards.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0042 — Build-out steers, the ambitions batch, and the engineering standards

**Status** accepted · **Evidence** the
[systems audit](../research/combat-and-systems/game-buildout-systems-audit.md) ·
the standards' live statement is
[engineering-standards.md](../standards/engineering.md); read that, not this

Owner rulings on every item the build-out register held awaiting a ruling.

## 1. Hist-site communion powers — **KEPT**

Drinking sap at a **hero Hist** grants a **once-per-day power**, using the
existing power/effect-stack semantics — no new system, no new verb. Which power
depends on the tree; about ten trees, so it is a collectible reason to walk the
province.

**Race-neutral, as the owner's original constraint required:** anyone may drink.
Argonians get different flavour text and a dream, never different mechanics, and
no content is gated on being Argonian.

The powers are effect-stack data; each placed hero tree carries a stable id
and a power slot in its record.
This absorbs the "Hist systemic layer" ambition below — the dream harness is
already registered; the physiology simulation is not pursued.

## 2. The audit §4 ambitions batch — all ruled

| Ambition | Ruling |
|---|---|
| Drifting/floating settlements | **CUT** — a permanently moored raft village reads identically; quests already forbid relocating cities |
| Fire spreading in a wetland (`fireResponse`) | **CUT** — expensive simulation, wet province, nothing asks for it |
| River-pirate boat-encounter system | **CUT as a system** — pirates survive as shore ambushes (the no-boat-vs-boat rule already removed the interesting half) |
| Deferred boat tier (cargo/passengers/ownership/AI boats) | **DEFER** to build-out G3; **delete `BoatStorageSocket`** meanwhile (orphaned) |
| Boat nav constraints (bridge clearance, obstacles) | **KEEP — cheap**: an authoring rule, not a system. Bridges over navigable water get clearance; obstacle placement respects lanes |
| Mounts/horses | **CUT** — wrong province; swamp, water and boats are the traversal identity |
| Swamp-jelly husbandry | **CUT as a system**; survives as scenery and lore |
| Hist systemic layer (dreams/memory threads/sap physiology) | **DEFER**, folded into §1 above + the registered dream harness |
| Hist hero-site root motion / water + fog response | **KEEP as set dressing** at the ~10 hero sites — a bespoke effect, not a system |
| Per-culture combat doctrine / taboo / burial **expression** | **KEEP as content** — enemy loadouts, graveyard dressing, naming. Authoring, not code (the customs/standing *mechanic* was already adopted, 0039) |
| Festivals + ritual time gates | **DEFER** to build-out G3 — the calendar exists; cheap later, expensive now |
| Creature boat/tree use; moving root barriers | **CUT** |
| Wild wamasu (was blocking quest FG03) | **RULED: wild wamasu exist**, deep marsh only. FG03 stands unamended; a marquee apex predator |
| Era-aware data layering | **DELETE the promise** from the data-model docs — moot at a frozen 4E 201 |
| Demographics → language/clothing/food/religion expression | **KEEP as an authoring rule** |
| Tide-gated access gameplay | **CUT the gating** — the built tidal amplitude (~0.5 m) cannot carry a gated door. Tide stays visual/flavour |
| Orphaned `rootwormTransit` locomotion mode | **DELETE** (as recommended in the audit) |

## 3. Renderer code is extracted into packages

The game-runtime renderer that lived app-private in the studio (sky and
light, water, weather expression, terrain streaming, vegetation, character
driver) moves into shared packages, extracted as one unit first because its
import cycle is coupled by module-level singletons, and anything tuned under
the studio's paused clock is re-validated against `GAME_TIME_SCALE = 30`. The
package rule ([0038](0038-world-build-vs-game-buildout-seam.md)) has a
mechanical check (standard 8).

## 4. Polearms are sourced with their wiring

Clip sourcing for the kept polearm classes is done in the same pass as moveset
wiring, so auditioning and wiring are one playtest. Top source
([90 §74.3](../world/90-asset-strategy.md)): Animated Armoury (SSE 35978),
with Animated Heavy Armory (51100) and Skyrim Spear Mechanic (25146); until
then `spear`, `halberd` and `staff` borrow two-handed movesets.

## 5. The combat proving round

Sequenced after the numbers are calibrated: `tooling/stats-sim` runs every
enemy archetype against preset builds (heavy brawler, light dodger, archer,
caster, sneak) and flags outliers; the owner playtests only the flagged
cases plus one sample per feel category (fast swarmer, slow heavy, ranged,
one boss), about a dozen fights, with a preset-loadout picker. Bosses are
authored, not tuned; one boss prototype (Xal-Krona) sets the pattern.

## 6. Morrowind voice for all text → a register row and a standing rule

AI-written prose reaches for gravitas and produces constructions nobody writes
(owner's example: *"a root the story grew along is severed"*). TES prose is
plainer than people remember — short declaratives, concrete nouns, archaism
carried by vocabulary and idiom, not by twisted syntax.

Adopted, as a **three-stage requirement, not a late cleanup**:

1. a **voice research pass** deriving a rulebook from the actual TES corpus
   (register, sentence length, permitted archaism, per-culture and per-class
   speech, how *system* messages sound);
2. the rules **bind every text-producing agent** as an input, not a review;
3. an **independent voice-review agent** — separate from the writer by design,
   because a writer will not catch its own register — checks written text
   against the rulebook and proposes the specific edit.

Plus a **banned-constructions list** that grows whenever the owner spots one
(entry 1 is the example above), kept in
[quests/60 §45e](../quests/60-writing-and-lore.md). Standard 4 (one text
catalogue) is what makes stage 3 mechanically possible — the reviewer sweeps one
catalogue instead of hunting through code.

## 7. HUD and UI consistency — an explicit row, not folded into the shell

The owner asked whether consistent HUD/UI design was covered. It was not,
explicitly: the audit had a "menus, settings, accessibility" shell row and
scattered per-screen items (inventory, character sheet, journal, map, barter),
with no owner for **the design system they must share**. Now a register row of
its own: one token set, one component layer, one input model (mouse/touch/pad),
one Morrowind-derived visual language, defined **before** the second screen is
built. The inventory UI (already Morrowind-skinned and shipped) is the seed the
token set is extracted *from*.

## 8. The engineering standards

The standards, their enforcement and their checks are stated in
**[engineering-standards.md](../standards/engineering.md)**; this decision
made them binding. The typed condition and action vocabulary is
[quests/85](../quests/85-condition-vocabulary.md), which also defines the one
content-unit convention for letters, rumours, books, journal and dialogue.

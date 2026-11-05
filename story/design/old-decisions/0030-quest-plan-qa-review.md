<!-- imported unchanged from elder-souls-argonia docs/decisions/0030-quest-plan-qa-review.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0030 — Quest-plan rulings: tier protection, the rule voice, swimming, locks and the Last Warden

**Status** accepted · **Scope** `docs/quests/`

A nine-pass review of the quest plan (fun, factions and cast, assets,
scripting and builds, lore, consistency, guardrails, world fit, tier
protection) found the plan structurally sound; every finding was applied in
the quest docs. The findings register is
[archived](../research/archive/quest-qa-0030/0030-findings-register.md). These
are the rulings that bind quest authoring.

## Tier protection

Tier 0 (the main quest) may not be broken by anything. Tier 1 (faction lines)
may break each other, telegraphed ([40-factions](../quests/40-factions.md)
§29–30b). Tier 2 (side and local quests) may not break the tiers above,
least of all invisibly.

- Every brief declares what it `touches` (shared NPCs, locations, states,
  items, variables; read or write), and a validator rejects a write in the
  wrong tier direction.
- The main quest's branch-state variables are written by tier-0 stages only;
  other content keeps its own reputation, which tier 0 may read.
- No quest removes or consumes a topic or evidence id owned by a higher tier.
- A tier-1 principal who also serves as a faction desk is protected inside
  that line; a faction finale may change a shared principal's office, never
  their existence.
- Every NPC is player-killable; an essential death shows the doom warning and
  routes to a fail-forward; faction lines never *require* a protected
  principal's death.

## The rule voice

Rules are marked **hard rule**, **strong default** or **target**. The hard
rules (no new art, no scaling, chase and escort conversions, canon grounding,
traversal fallbacks) are absolute; taste heuristics are defaults or targets,
validated province-wide with tolerance. Agents use their own reasoning
inside them ([quests README](../quests/README.md)).

## Quests fit the built geography

Prefer changing the quest over the world. A quest names only roads, lanes,
stations and water the compiled data holds; a hidden navigable channel is
declared as one, never as a scheduled lane.

## Settled calls

1. **The main quest has 24 core quests.**
2. **Swimming is universal core traversal**: consumables cover any build;
   dry alternates are required only for boats and climbing.
3. **Tier-4 locks are explicit opt-in acts**, gating rewards and backers,
   never sanctuary endings.
4. **Shared principals keep their cross-links** between lines.
5. **Memory removal** draws only from topics without the `essential` flag.
6. **The rootworm is never seen**, permanently: tunnel mouths, displaced
   water, sound, a flank of animated root.
7. **The Last Warden is an ancient Xal-Krona** (Argonian Behemoth) on the
   vanilla werewolf-beast rig with BM&V meshes
   ([options](../research/quests-and-cast/last-warden-boss-options.md));
   Mihail's wamasu is an optional overworld legendary.
8. **The Many-Root line is interesting throughout**, not only at two quests.
9. **Act II races are stage-triggered**, never clock-triggered.

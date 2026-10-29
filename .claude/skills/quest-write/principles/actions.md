# Actions: what the player does, by skill

Read for every quest. Owner rulings (0024 §9, 2026-10-28): an action is **a use of one of the player's
skills** (long blade, axe, sneak, security, alchemy, armorer, speechcraft, athletics and the rest). That is
what makes a quest interesting: it uses and builds the character the player is making. Each skill can be used
in many ways (long blade against rats in a cellar, a giant in a ruin, the town watch on a bridge, a duellist
at dawn), and quests combine skills creatively. A chain of plain conversations is not a quest. Evidence:
`docs/research/2026-10-27/quest-actions-and-skills.md`.

## Actions first, then the quest is built round them

1. **Draw an action plan before the truth.** Run
   `python3 .claude/skills/quest-write/action_plan.py --profile <line key> --band <D0..D5>
   --shapes <SHAPE,...> --ledger <dir of quest records already in the line or packet>`. It proposes plans
   that follow the primary shape's beats (find, get there, the crux as two approaches, resolve) from
   `skill-uses.yaml` (skill, use, target, setting), weighted by the line's profile and steering away from
   what the ledger has already used. Pick one, adapt it, or write your own from the
   catalogue; record it as `actionPlan` with the reason.
2. **Then write the truth so the actions follow from it.** A dive needs something under water; a lock needs
   something worth locking; a duel needs someone with a grievance. The plausibility pass still applies: if an
   action does not follow from believable people and places, change the plan or the truth.
3. **Every stage that is not an ending has an action** (`skill`, `use`, target, setting), or offers
   approaches that each have one. Speech counts when it uses Speechcraft or Mercantile (persuade, intimidate,
   bribe, present evidence, accuse), not when it is only listening.
4. **Offer more than one build a way through** where the story allows: a stage a fighter, a thief, a mage and
   a talker can each pass, at different costs.
5. **Each use carries its `world` needs and its `system`** (`skill-uses.yaml`): the hostiles and their band,
   the lock and its level, the climbable face, the dive, the recipe become `things` rows, so the world is
   built to hold them; the system names the engine feature and chunk. A system marked DECISION has no chunk
   yet: do not build a stage on it alone.
6. **Escalate across a line:** later quests combine skills the earlier ones used, against harder targets and
   settings; each rank adds a use.
7. **Variety is steered, not capped.** The generator weights against repeats of the same skill, use, target
   and setting in a line or region packet; the reviewer flags sameness. There is no fixed quota.

## Profiles

`profiles.yaml` holds one profile per questline in `world/sources/quests/lines.json` (key = the line id's last
part: `shadowscales`, `night-reed`, `marsh-charter`, `sunken-archive`, `nisswo`, `many-root`, `reed-sail`,
`league-of-open-water`, `chainbreakers`, `thorn-ash-reed`, `umbriel-witness`, `rootworm-waykeepers`,
`salt-teeth`, `main`, `daedric`, `local`) and the planned `detectives` (decision 0025). Each is read from the
line's section of `docs/design/quests/40-factions.md` and its faction culture sheet, cited in `from`, and
weighs families, skills, targets and settings. A local quest takes `local` and leans by its place: its danger
band, its terrain (water, heights, ruins) and its people's work.

# Actions: what the player does, by skill

Read for every quest. Owner rulings (0017 §9, 2026-10-28): an action is **a use of one of the player's
skills** (long blade, axe, sneak, security, alchemy, armorer, speechcraft, athletics and the rest). That is
what makes a quest interesting: it uses and builds the character the player is making. Each skill can be used
in many ways (long blade against rats in a cellar, a giant in a ruin, the town watch on a bridge, a duellist
at dawn), and quests combine skills creatively. A chain of plain conversations is not a quest. Evidence:
`docs/research/2026-10-27/quest-actions-and-skills.md`.

## Actions first, then the quest is built round them

1. **Draw an action plan before the truth.** Run
   `python3 .claude/skills/quest-write/action_plan.py --line <line> [--profile <faction>] --band <D0..D5>
   --shapes <SHAPE,...> --ledger <dir of quest records already in the line or packet>`. It proposes varied
   plans from `skill-uses.yaml` (skill, use, target, setting), weighted by the line's or faction's profile and
   steering away from what the ledger has already used. Pick one, adapt it, or write your own from the
   catalogue; record it as `actionPlan` with the reason.
2. **Then write the truth so the actions follow from it.** A dive needs something under water; a lock needs
   something worth locking; a duel needs someone with a grievance. The plausibility pass still applies: if an
   action does not follow from believable people and places, change the plan or the truth.
3. **Every stage that is not an ending has an action** (`skill`, `use`, target, setting), or offers
   approaches that each have one. Speech counts when it uses Speechcraft or Mercantile (persuade, intimidate,
   bribe, present evidence, accuse), not when it is only listening.
4. **Offer more than one build a way through** where the story allows: a stage a fighter, a thief, a mage and
   a talker can each pass, at different costs.
5. **Each use carries its `needs`** (`skill-uses.yaml`): the hostiles and their band, the lock and its level,
   the climbable face, the dive, the recipe. They become `things` rows, so the world is built to hold them.
6. **Escalate across a line:** later quests combine skills the earlier ones used, against harder targets and
   settings; each rank adds a use.
7. **Variety is steered, not capped.** The generator weights against repeats of the same skill, use, target
   and setting in a line or region packet; the reviewer flags sameness. There is no fixed quota.

## Profiles

A line or faction profile weights skills (and may favour targets and settings). The Shadowscales lean to
sneak, short blade and marksman; the Night-Reed Chapter to sneak, security, acrobatics and mercantile; the
detectives to speechcraft, sneak and observation uses, with combat when a case turns; a fighters' line to the
weapon and armour skills; mages to the magic schools. These are starting weights in `profiles.yaml`;
P4-WP4.0 sets every faction's profile from its design in 40-factions and its culture sheet. A local quest
takes its weights from the place: its danger band, its terrain (water, heights, ruins) and its people's work.

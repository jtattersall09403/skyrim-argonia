"""Propose varied action plans for a quest from the skill-use catalogue (principles/actions.md).

Usage: python3 action_plan.py [--profile NAME] [--shapes SHAPE,...] [--band D2] [--ledger DIR]
                              [--plans 5] [--steps 4] [--seed N]

Weights each skill by the profile (profiles.yaml) and the shapes' favoured uses, and against what the quest
records in --ledger (the line or region packet so far) already use. Each plan mixes at least two skill
families and has one stage with alternative approaches from different families. A proposal, not a rule: the
quest writer picks, adapts or replaces it and records the choice as `actionPlan`.
"""
import argparse
import collections
import pathlib
import random
import sys

import yaml

HERE = pathlib.Path(__file__).parent
SHAPE_USES = {  # uses a shape tends to call for; weighted up, never required
    "MURDER": ["spy", "follow", "present-evidence", "interrogate", "accuse", "pick-a-lock", "identify-a-poison"],
    "MISSING": ["follow", "detect-life", "swim", "dive", "climb", "hunt"],
    "RECKONING": ["present-evidence", "interrogate", "open-a-strongbox", "raise-a-witness"],
    "THEFT": ["steal", "pick-a-lock", "sneak-past", "pickpocket", "plant", "disarm-a-trap"],
    "FRAUD": ["appraise", "present-evidence", "sell-a-forgery", "bribe"],
    "SMUGGLING": ["sneak-past", "bribe", "pole-or-sail-a-boat", "lie", "outrun"],
    "DISPUTE": ["persuade", "intimidate", "present-evidence", "duel"],
    "NEGOTIATION": ["bargain", "bribe", "persuade", "admire"],
    "SUCCESSION": ["persuade", "present-evidence", "duel", "protect"],
    "BONDAGE": ["sneak-past", "pick-a-lock", "bribe", "persuade", "outrun"],
    "PREDATOR": ["hunt", "set-a-trap", "brew-a-poison", "snipe", "fight"],
    "CONTAMINATION": ["brew-a-cure", "gather-ingredients", "cure-disease", "heal-the-sick", "dive"],
    "EXPEDITION": ["climb", "dive", "pole-or-sail-a-boat", "cross-a-flood", "water-breathe", "clear-a-place"],
    "HAUNTING": ["bind-a-spirit", "banish", "detect-life", "light-a-dark-place", "present-evidence"],
    "RITE": ["rite-without-iron", "make-an-item", "protect", "gather-ingredients"],
    "WONDER": ["climb", "dive", "levitate-to-a-ledge"],
}


def ledger_counts(folder):
    skills, uses = collections.Counter(), collections.Counter()
    for f in pathlib.Path(folder).glob("*.yaml") if folder else []:
        q = yaml.safe_load(f.read_text()) or {}
        for s in q.get("stages", []):
            acts = list(s.get("actions", [])) + [x for a in s.get("approaches", []) for x in a.get("actions", [])]
            for x in acts:
                skills[x.get("skill")] += 1
                uses[(x.get("skill"), x.get("use"))] += 1
    return skills, uses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="local")
    ap.add_argument("--shapes", default="")
    ap.add_argument("--band", default="D2")
    ap.add_argument("--ledger")
    ap.add_argument("--plans", type=int, default=5)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()

    cat = yaml.safe_load((HERE / "skill-uses.yaml").read_text())
    profile = yaml.safe_load((HERE / "profiles.yaml").read_text()).get(a.profile)
    if profile is None:
        print(f"no profile {a.profile!r} in profiles.yaml")
        return 1
    favoured = {u for s in a.shapes.split(",") if s for u in SHAPE_USES.get(s.strip().upper(), [])}
    used_skills, used_uses = ledger_counts(a.ledger)
    rng = random.Random(a.seed)

    fam_w, skill_w = profile.get("families", {}), profile.get("skills", {})
    fam_size = collections.Counter(spec["family"] for spec in cat["skills"].values())
    options = []  # (weight, skill, family, use)
    for skill, spec in cat["skills"].items():
        for use in spec["uses"]:
            # a family's weight is shared by its skills, a skill's by its uses
            w = fam_w.get(spec["family"], 1.0) / fam_size[spec["family"]]
            w *= skill_w.get(skill, 1.0) / len(spec["uses"])
            w *= 3.0 if use in favoured else 1.0
            w /= (1 + used_skills[skill]) * (1 + 2 * used_uses[(skill, use)])
            if w > 0:
                options.append((w, skill, spec["family"], use))

    def pick(exclude_families=(), exclude_skills=()):
        pool = [o for o in options if o[2] not in exclude_families and o[1] not in exclude_skills]
        o = rng.choices(pool, weights=[p[0] for p in pool])[0]
        target = None
        groups = cat.get("targetsFor", {}).get(o[3])
        if groups:
            group = rng.choice(groups)
            target = f"{group}: {rng.choice(cat['targets'][group])}"
        needs = cat["uses"].get(o[3], {}).get("needs", [])
        return {"skill": o[1], "family": o[2], "use": o[3], "target": target,
                "setting": rng.choice(cat["settings"]), "needs": needs}

    for n in range(1, a.plans + 1):
        steps, skills = [], set()
        for i in range(a.steps):
            if i == a.steps // 2:  # one stage with approaches from different families
                first = pick(exclude_skills=skills)
                second = pick(exclude_families={first["family"]}, exclude_skills=skills | {first["skill"]})
                steps.append({"approaches": [first, second]})
                skills |= {first["skill"], second["skill"]}
            else:
                s = pick(exclude_skills=skills)
                steps.append(s)
                skills.add(s["skill"])
        families = {x["family"] for s in steps for x in (s.get("approaches") or [s])}
        if len(families) < 2:
            continue
        print(f"## Plan {n} (profile {a.profile}, band {a.band}; families: {', '.join(sorted(families))})")
        for i, s in enumerate(steps, 1):
            for j, x in enumerate(s.get("approaches") or [s]):
                lead = f"{i}." if j == 0 else "   or"
                tgt = f" against {x['target']}" if x["target"] else ""
                print(f"{lead} {x['skill']}: {x['use']}{tgt}, {x['setting']}"
                      + (f" (needs: {'; '.join(x['needs'])})" if x["needs"] else ""))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

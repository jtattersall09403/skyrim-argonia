#!/usr/bin/env python3
"""Propose action plans for a quest from the skill-use catalogue (principles/actions.md).

Usage: python3 action_plan.py [--profile NAME] [--shapes SHAPE,...] [--band D2] [--line DIR]
                              [--plans 5] [--seed N]

A plan follows the primary shape's beats (find, get there, the crux, resolve; SHAPE_BEATS below): each beat
draws a skill use from that beat's pool, weighted by the profile (profiles.yaml: a line key such as
`many-root`, a line id `quest.line.many-root`, or a faction id), the secondary shapes' pools, and against what
the quest records in --line (the line or region packet so far) already use. The crux offers two approaches
from different skill families. Settings come from the use's allowed settings (skill-uses.yaml settingsFor),
the profile's favoured ones first; one target group is kept across the plan where the uses allow it.
Every plan printed mixes at least two skill families. A proposal, not a rule: the quest writer picks, adapts
or replaces it and records the choice as `actionPlan`.
"""
import argparse
import collections
import pathlib
import random
import sys

import yaml

HERE = pathlib.Path(__file__).parent
BEATS = ("find", "get there", "crux", "resolve")
SHAPE_BEATS = {  # per shape, a pool of uses per beat (skill-uses.yaml); the crux is offered as two approaches
    "MURDER": [["interrogate", "detect-life", "identify-a-poison", "test-a-sample"],
               ["pick-a-lock", "lift-a-key", "sneak-past", "persuade"],
               ["present-evidence", "interrogate", "pickpocket", "steal", "bribe", "intimidate"],
               ["accuse", "duel", "fight", "stand-a-hard-fight"]],
    "THEFT": [["bribe", "interrogate", "persuade", "detect-life"],
              ["sneak-past", "become-invisible", "water-breathe", "calm"],
              ["pick-a-lock", "open-a-strongbox", "lift-a-key", "steal", "pickpocket", "telekinesis"],
              ["bargain", "lie", "persuade", "duel"]],
    "FRAUD": [["read-an-enchantment", "test-a-sample", "judge-a-weapon", "interrogate"],
              ["pick-a-lock", "lift-a-key", "steal", "bribe"],
              ["present-evidence", "interrogate", "intimidate", "pickpocket"],
              ["accuse", "persuade", "bargain", "duel"]],
    "MISSING": [["interrogate", "persuade", "detect-life"],
                ["hunt", "sneak-past", "water-breathe", "fight"],
                ["clear-a-place", "pick-a-lock", "sneak-past", "calm"],
                ["persuade", "stand-a-hard-fight", "buy-out"]],
    "RECKONING": [["interrogate", "read-an-enchantment", "persuade"],
                  ["open-a-strongbox", "pick-a-lock", "water-breathe", "lift-a-key"],
                  ["present-evidence", "intimidate", "bribe", "pickpocket"],
                  ["accuse", "duel", "persuade"]],
    "DISPUTE": [["interrogate", "persuade", "detect-life"],
                ["steal", "pick-a-lock", "sneak-past", "lift-a-key"],
                ["present-evidence", "intimidate", "bribe"],
                ["persuade", "duel", "bargain"]],
    "NEGOTIATION": [["interrogate", "bribe"],
                    ["sneak-past", "clear-a-place", "lift-a-key", "steal"],
                    ["bargain", "bribe", "intimidate", "persuade"],
                    ["persuade", "duel", "buy-out"]],
    "SUCCESSION": [["interrogate", "read-an-enchantment"],
                   ["open-a-strongbox", "lift-a-key", "steal"],
                   ["present-evidence", "persuade", "bribe", "duel"],
                   ["persuade", "accuse", "stand-a-hard-fight"]],
    "BONDAGE": [["interrogate", "bribe", "persuade"],
                ["sneak-past", "pick-a-lock", "lift-a-key"],
                ["buy-out", "bribe", "intimidate", "open-a-strongbox", "steal"],
                ["duel", "persuade", "stand-a-hard-fight"]],
    "PREDATOR": [["hunt", "test-a-sample", "interrogate", "detect-life"],
                 ["sneak-past", "gather-ingredients", "fight"],
                 ["snipe", "calm", "kill-from-range", "frenzy"],
                 ["fight", "hunt", "stand-a-hard-fight"]],
    "CONTAMINATION": [["test-a-sample", "interrogate", "identify-a-poison"],
                      ["water-breathe", "gather-ingredients", "sneak-past"],
                      ["test-a-sample", "clear-a-place", "detect-life"],
                      ["persuade", "bargain", "present-evidence"]],
    "SMUGGLING": [["interrogate", "bribe"],
                  ["sneak-past", "become-invisible", "water-breathe", "bribe"],
                  ["pick-a-lock", "open-a-strongbox", "intimidate", "lie"],
                  ["accuse", "bargain", "duel"]],
    "EXPEDITION": [["interrogate", "bargain", "gather-ingredients"],
                   ["sneak-past", "fight", "water-breathe", "calm"],
                   ["clear-a-place", "water-breathe", "pick-a-lock", "telekinesis"],
                   ["stand-a-hard-fight", "fight", "persuade"]],
    "HAUNTING": [["interrogate", "detect-life", "read-an-enchantment"],
                 ["sneak-past", "pick-a-lock", "water-breathe"],
                 ["banish", "turn-the-dead", "present-evidence", "persuade"],
                 ["soul-trap", "turn-the-dead", "fight"]],
    "RITE": [["gather-ingredients", "interrogate"],
             ["sneak-past", "water-breathe", "fight"],
             ["smith-to-order", "gather-ingredients", "persuade"],
             ["persuade", "banish", "stand-a-hard-fight"]],
    "WONDER": [["detect-life", "read-an-enchantment"],
               ["water-breathe", "sneak-past"],
               ["read-an-enchantment", "telekinesis", "detect-life"],
               ["persuade", "calm"]],
}
GENERIC = 0.04  # weight of a use outside every pool of the beat


def stage_actions(stage):
    return list(stage.get("actions", [])) + [x for a in stage.get("approaches", []) for x in a.get("actions", [])]


def line_counts(folder):
    skills, uses = collections.Counter(), collections.Counter()
    for f in pathlib.Path(folder).glob("*.yaml") if folder else []:
        q = yaml.safe_load(f.read_text()) or {}
        for s in q.get("stages", []):
            for x in stage_actions(s):
                skills[x.get("skill")] += 1
                uses[(x.get("skill"), x.get("use"))] += 1
    return skills, uses


def find_profile(profiles, name):
    for key in (name, name.rsplit(".", 1)[-1]):
        if key in profiles:
            return key, profiles[key]
    for key, p in profiles.items():
        if isinstance(p, dict) and p.get("faction") == name:
            return key, p
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="local")
    ap.add_argument("--shapes", default="")
    ap.add_argument("--band", default="D2")
    ap.add_argument("--line", "--ledger", dest="line", help="a folder of the line's or packet's records so far")
    ap.add_argument("--plans", type=int, default=5)
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()

    cat = yaml.safe_load((HERE / "skill-uses.yaml").read_text())
    key, profile = find_profile(yaml.safe_load((HERE / "profiles.yaml").read_text()), a.profile)
    if profile is None:
        print(f"no profile {a.profile!r} in profiles.yaml")
        return 1
    shapes = [s.strip().upper() for s in a.shapes.split(",") if s.strip()]
    unknown = [s for s in shapes if s not in SHAPE_BEATS]
    if unknown:
        print(f"unknown shape(s): {', '.join(unknown)}; one of {', '.join(SHAPE_BEATS)}")
        return 1
    shapes = shapes or ["WONDER"]
    used_skills, used_uses = line_counts(a.line)
    rng = random.Random(a.seed)

    fam_w, skill_w = profile.get("families", {}), profile.get("skills", {})
    fav_settings, fav_targets = profile.get("settings", []), profile.get("targets", [])
    fam_size = collections.Counter(spec["family"] for spec in cat["skills"].values())
    by_use = collections.defaultdict(list)  # use -> [(skill, family, base weight)]
    for skill, spec in cat["skills"].items():
        for use in spec["uses"]:
            w = fam_w.get(spec["family"], 1.0) / fam_size[spec["family"]] * skill_w.get(skill, 1.0)
            w /= (1 + used_skills[skill]) * (1 + 2 * used_uses[(skill, use)])
            if w > 0:
                by_use[use].append((skill, spec["family"], w))

    def candidates(beat):
        pools = [(set(SHAPE_BEATS[s][beat]), 4.0 if i == 0 else 2.0) for i, s in enumerate(shapes)]
        out = []
        for use, rows in by_use.items():
            boost = max([m for pool, m in pools if use in pool] or [GENERIC])
            out += [(w * boost, skill, fam, use) for skill, fam, w in rows]
        return out

    def setting_for(use):
        allowed = cat.get("settingsFor", {}).get(use) or [k for k in cat["settings"] if k != "underwater"]
        fav = [s for s in allowed if s in fav_settings]
        return cat["settings"][rng.choice(fav if fav and rng.random() < 0.7 else allowed)]

    def target_for(use, held):
        """held: the (group, target) kept across the plan, so a plan has one antagonist where uses allow."""
        groups = cat.get("targetsFor", {}).get(use)
        if not groups:
            return None, held
        if held and held[0] in groups:
            return f"{held[0]}: {held[1]}", held
        fav = [g for g in groups if g in fav_targets]
        group = rng.choice(fav or groups)
        target = rng.choice(cat["targets"][group])
        return f"{group}: {target}", held or (group, target)

    def pick(beat, exclude_families=(), exclude_skills=(), held=None):
        pool = [o for o in candidates(beat) if o[2] not in exclude_families and o[1] not in exclude_skills]
        o = rng.choices(pool, weights=[p[0] for p in pool])[0]
        target, held = target_for(o[3], held)
        world = cat["uses"].get(o[3], {}).get("world", [])
        system = cat.get("useSystem", {}).get(o[3]) or cat["skills"][o[1]]["system"]
        return {"skill": o[1], "family": o[2], "use": o[3], "target": target, "setting": setting_for(o[3]),
                "world": world, "system": system}, held

    def tags(steps):
        uses = {x["use"] for s in steps for x in (s.get("approaches") or [s])}
        return [t for t, us in cat["verbTags"].items() if uses & set(us)]

    printed, tries = 0, 0
    while printed < a.plans and tries < a.plans * 40:
        tries += 1
        steps, skills, held = [], set(), None
        for beat in range(len(BEATS)):
            if BEATS[beat] == "crux":
                first, held = pick(beat, exclude_skills=skills, held=held)
                second, held = pick(beat, exclude_families={first["family"]},
                                    exclude_skills=skills | {first["skill"]}, held=held)
                steps.append({"approaches": [first, second]})
                skills |= {first["skill"], second["skill"]}
            else:
                s, held = pick(beat, exclude_skills=skills, held=held)
                steps.append(s)
                skills.add(s["skill"])
        families = {x["family"] for s in steps for x in (s.get("approaches") or [s])}
        if len(families) < 2:
            continue
        printed += 1
        print(f"## Plan {printed} (profile {key}, shapes {','.join(shapes)}, band {a.band}; "
              f"families: {', '.join(sorted(families))}; verb tags: {', '.join(tags(steps))})")
        for i, s in enumerate(steps):
            for j, x in enumerate(s.get("approaches") or [s]):
                lead = f"{i + 1}. {BEATS[i]}:" if j == 0 else "   or:"
                tgt = f" against {x['target']}" if x["target"] else ""
                print(f"{lead} {x['skill']}: {x['use']}{tgt}, {x['setting']} [{x['system']}]"
                      + (f" (world: {'; '.join(x['world'])})" if x["world"] else ""))
        print()
    if printed < a.plans:
        print(f"only {printed} of {a.plans} plans mixed two skill families; widen the profile")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

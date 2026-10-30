"""The combat wiring's rows (lane 1.6-wiring; docs/research/2026-10-30/combat-wiring.md): the route of every combat
quantity (`combat_wiring`), the mod settings stack.py writes at stage (`combat_mod_setting`), the GMSTs
(`game_setting` + `game_setting_combat`), the P1 carriers (`combat_carrier`), the ladder's combat block (`danger_band_combat`, 76 §128), the
weapon class numbers (`weapon_class_combat`), the constants, and the one archetype of 1.6 (npc, npc_statblock,
npc_fight_flee_alarm, combat_archetype).

DS1 numbers are never retuned for feel (decision 0014); every value 2.7 §b measures from DSR is a placeholder
here, tagged `GUESS:` (DSR owed) or `MOD:` (the mod's own value, kept until DSR says otherwise).

Idempotent: re-running upserts the same rows.  python3 -m tools.argonia_world.content.combat_wiring_rows
"""
from __future__ import annotations

from tools.argonia_world import db

# id, behaviour, quantity, route, writer, source, journey
WIRING = [
    ("w.damage.listed", "damage", "listed weapon damage (WEAP DATA damage)", "record", "generated", "sheet", "fight-damage-builds"),
    ("w.damage.position-strength", "damage", "where in the range the blow lands x the Strength term", "perk_entry", "runtime", "sheet", "fight-damage-builds"),
    ("w.damage.vanilla-skill", "damage", "Skyrim's own weapon-skill damage term, neutralised", "actor_value", "runtime", "sheet", "fight-damage-builds"),
    ("w.damage.difficulty", "damage", "Skyrim's difficulty damage multipliers, held at 1", "gmst", "generated", "owner", "fight-damage-builds"),
    ("w.damage.left-hand", "damage", "a left-hand weapon blow's position and Strength", "none", "runtime", "sheet", None),
    ("w.damage.critical", "damage", "riposte and backstab multiplier", "mod_setting", "mod", "dsr", "fight-archetype"),
    ("w.stamina.max", "stamina", "maximum stamina", "actor_value", "runtime", "sheet", "fight-damage-builds"),
    ("w.stamina.regen", "stamina", "stamina regeneration rate, in and out of combat", "gmst", "generated", "dsr", "fight-roll-burden"),
    ("w.stamina.regen-delay", "stamina", "delay before stamina regenerates after it is spent", "gmst", "generated", "dsr", "fight-roll-burden"),
    ("w.stamina.power", "stamina", "power attack stamina x skill band x burden x soft requirement", "perk_entry", "runtime", "sheet", "fight-damage-builds"),
    ("w.stamina.actions", "stamina", "light attack, block and stagger stamina costs", "mod_setting", "mod", "dsr", None),
    ("w.stamina.roll", "stamina", "roll stamina cost", "mod_setting", "data", "dsr", "fight-roll-burden"),
    ("w.guard.stability", "guard", "share of a blocked blow stopped (Block band, capped, plus the stack's blockStability)", "perk_entry", "runtime", "sheet", "fight-archetype"),
    ("w.guard.stamina", "guard", "guard stamina multiplier (Block band)", "runtime_hook", "runtime", "sheet", None),
    ("w.parry.window", "parry", "parry window start and end in the bash clip", "mod_setting", "data", "dsr", "fight-archetype"),
    ("w.roll.tier", "roll", "burden tier -> roll allowed (none when overloaded)", "runtime_hook", "runtime", "sheet", "fight-roll-burden"),
    ("w.roll.distance", "roll", "roll distance and recovery per burden tier", "runtime_hook", "runtime", "dsr", "fight-roll-burden"),
    ("w.iframes.duration", "iframes", "roll invulnerability window", "mod_setting", "data", "dsr", "fight-roll-burden"),
    ("w.iframes.tier", "iframes", "i-frames per burden tier", "runtime_hook", "runtime", "dsr", "fight-roll-burden"),
    ("w.poise.stagger", "poise", "poise pool and stagger (Modern Stagger Lock in A, DSC's pool in B and B2)", "perk_entry", "runtime", "dsr", None),
    ("w.armour.mitigation", "armour", "the player's mitigation AR/(AR + 135.6 + 0.6 x blow) at the reference blow", "perk_entry", "runtime", "sheet", "fight-damage-builds"),
    ("w.armour.vanilla", "armour", "Skyrim's own armour rating on our items, held at 0", "record", "generated", "sheet", "fight-damage-builds"),
    ("w.power.heavy", "power", "heavy blow over light blow (the class's motion values)", "none", "runtime", "dsr", None),
    ("w.archery.damage", "archery", "bow position term, no Strength", "perk_entry", "runtime", "sheet", None),
    ("w.archery.draw", "archery", "draw time and draw stamina", "none", "mod", "dsr", None),
    ("w.lockon.distance", "lockon", "lock-on range", "mod_setting", "data", "dsr", "fight-lock-on"),
    ("w.enemy.health", "enemy", "an archetype's health from its band and position", "record", "generated", "sheet", "fight-archetype"),
    ("w.enemy.damage", "enemy", "an archetype's light hit from its band and position", "perk_entry", "generated", "sheet", "fight-archetype"),
    ("w.enemy.armour", "enemy", "an archetype's mitigation of the reference blow from its band's AR", "perk_entry", "generated", "sheet", "fight-archetype"),
    ("w.enemy.level", "enemy", "an archetype's fixed level and its encounter zone (min = max)", "record", "generated", "sheet", "fight-archetype"),
]

# mod, file, section, key, value, wiring, provenance
SETTINGS = [
    ("elden-parry", "*EldenParry.ini", None, "fParryWindow_Start", "0.02", "w.parry.window",
     "MOD: Elden Parry 1.3 default; DSR parry window by shield class owed (2.7 §b)"),
    ("elden-parry", "*EldenParry.ini", None, "fParryWindow_End", "0.2", "w.parry.window",
     "MOD: Elden Parry 1.3 default; DSR parry window by shield class owed (2.7 §b)"),
    ("tk-dodge-re-addon", "skse/plugins/tk-dodge.toml", "Settings", "fIFrameDuration", "0.3", "w.iframes.duration",
     "GUESS: mod default 0.3 s; DSR roll i-frames by load owed (2.7 §b, the 13/11/9 question)"),
    ("tk-dodge-re-addon", "skse/plugins/tk-dodge.toml", "Settings", "fDodgeCost", "15.0", "w.stamina.roll",
     "GUESS: mod default 15; DSR roll stamina owed (2.7 §b), scaled by the ratio of maxima (2.7 §a)"),
    ("true-directional-movement", "mcm/config/truedirectionalmovement/settings.ini", "TargetLock",
     "fTargetLockDistance", "2000", "w.lockon.distance", "GUESS: mod default 2000 u; DSR LockCamParam range owed (2.7 §b)"),
]

_HELD = "OWNER: 76 §121.4 lethality knob at 1.0 (the difficulty setting comes later)"
GMSTS = [(f"fDiffMultHP{d}PC{t}", 1.0, "w.damage.difficulty", _HELD)
         for d in ("By", "To") for t in ("VE", "E", "N", "H", "VH", "L")]
GMSTS += [
    ("fCombatStaminaRegenRateMult", 1.0, "w.stamina.regen",
     "SHEET: one regen rate 12 + 0.24 x Agi in and out of combat (76 §121.2); DSR regen owed (2.7 §b)"),
    ("fDamagedStaminaRegenDelay", 1.05, "w.stamina.regen-delay",
     "GUESS: the sheet's 1.05 s (76 §121.2); DSR regen delay owed (2.7 §b)"),
]

# id, actor value (av-audit reserve order; Mutagen 0.54.4 has no names for the limb AVs 46-52, so the skill-advance
# AVs follow Energy), hand, entry point, wired, wiring
CARRIERS = [
    ("right.attack-damage", "VoicePoints", "right", "ModAttackDamage", True, "w.damage.position-strength"),
    ("right.power-stamina", "VoiceRate", "right", "ModPowerAttackStamina", True, "w.stamina.power"),
    ("body.incoming-damage", "Energy", "body", "ModIncomingDamage", True, "w.armour.mitigation"),
    ("body.block", "OneHandedSkillAdvance", "body", "ModPercentBlocked", True, "w.guard.stability"),
    ("left.attack-damage", "TwoHandedSkillAdvance", "left", "ModAttackDamage", False, "w.damage.left-hand"),
    ("body.incoming-stagger", "MarksmanSkillAdvance", "body", "ModIncomingStagger", False, "w.poise.stagger"),
]

LADDER_REF = "docs/design/world/76-stats-progression.md §128"
# band, health, light hit, AR, blows that kill you, level
LADDER = [("D1", (18, 28), (4, 14), (0, 18), 6, 1), ("D2", (27, 62), (24, 40), (18, 45), 4, 10),
          ("D3", (40, 90), (52, 92), (45, 80), 3.5, 20), ("D4", (50, 110), (120, 210), (80, 130), 3, 35),
          ("D5", (96, 205), (185, 320), (100, 170), 3, 50)]

CONSTANTS = [
    ("damage_unit", 24.0, "SHEET: listedDamage = motion x damageScale x 24 (76 §121.1)"),
    ("reference_blow", 24.0, "SHEET: the reference 24-damage blow at which AR 50 mitigates 25 % (76 §121.4)"),
    ("race_start_health", 50.0, "GUESS: Skyrim's playable races start at 50 health; read in game by fight-archetype"),
]

# The straight sword's class (1.3 §c). Light 1.0 so the steel sword lists 24 (76 §121.1); heavy at the ladder's
# ~2.4x (76 §128). DS1 motion values are measured in 2.7 §b.
CLASSES = [("longBlade", 1.0, 2.4, None, "GUESS: light 1.0, heavy 2.4 (76 §121.1, §128); DSR motion values owed (2.7 §b)")]

PLACE = "place.imperial-fringe.claywater-station"
ARCHETYPE = "npc.imperial-fringe.claywater-station.ambush-deserter"


def write(w) -> None:
    for i, b, q, r, wr, s, j in WIRING:
        w.upsert("combat_wiring", id=i, behaviour=b, quantity=q, route=r, writer=wr, source=s, journey=j)
    for m, f, sec, k, v, wi, p in SETTINGS:
        w.upsert("combat_mod_setting", mod=m, file=f, section=sec, key=k, value=v, wiring=wi, provenance=p)
    for e, v, wi, p in GMSTS:
        w.upsert("game_setting", edid=e, kind="float", value=v, chunk="1.6", why=f"combat wiring {wi}: {p}")
        w.upsert("game_setting_combat", edid=e, wiring=wi, provenance=p)
    for i, av, h, ep, wired, wi in CARRIERS:
        w.upsert("combat_carrier", id=i, actor_value=av, hand=h, entry_point=ep, condition_tab=None,
                 condition_keyword=None, wired=wired, wiring=wi)
    for band, hp, hit, ar, blows, lvl in LADDER:
        w.upsert("danger_band_combat", band=band, health_lo=hp[0], health_hi=hp[1], light_hit_lo=hit[0],
                 light_hit_hi=hit[1], ar_lo=ar[0], ar_hi=ar[1], blows_to_kill=blows, level=lvl, design_ref=LADDER_REF)
    for i, v, p in CONSTANTS:
        w.upsert("combat_constant", id=i, value=v, provenance=p)
    for c, lo, hi, poise, p in CLASSES:
        w.upsert("weapon_class_combat", weapon_class=c, motion_light=lo, motion_heavy=hi, poise_damage=poise,
                 provenance=p)
    w.upsert("npc", id=ARCHETYPE, kind="person", name="Deserter", role="ambusher", archetype="person.deserter",
             hostility="hostile", home_place_id=PLACE, doom_tier="none", status="provisional",
             notes="1.6's one archetype: a sword-and-shield Legion deserter on the Blackwood Road by the station, "
                   "fixed at D2 (soul contract C14); respawns on rest (1.5).",
             race="imperial", sex="male")
    w.upsert("npc_statblock", npc_id=ARCHETYPE, **{"class": "npc"}, band="D2", position=0.5,
             loadout="item.steel-sword+item.steel-shield", respawn="onRest", soul_trappable=False)
    w.upsert("npc_fight_flee_alarm", npc_id=ARCHETYPE, fight=100, flee=0, alarm=0)
    w.upsert("combat_archetype", npc_id=ARCHETYPE, race_form="013744:Skyrim.esm", face_template="0551C7:Skyrim.esm",
             weapon="item.steel-sword", shield="item.steel-shield",
             design_ref="docs/phases/1-core-loop/1.6-fight-on-the-stack.md (one archetype); 76 §128")


def main() -> int:
    w = db.open()
    write(w)
    print("combat wiring rows:", ", ".join(w.save()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

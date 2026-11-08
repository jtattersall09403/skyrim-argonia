"""Talk read-back (docs/design/talk.md): out/Argonia.esp against the talk tables, after `plugin.sh check` built it.

For every talker with written lines: each of their topics has one INFO gated GetIsReference to their placed ref (and
no other topic is), the two greetings gated on GetRelationshipRank with the player (< 1 a stranger, >= 1 a friend,
Skyrim's own Hello way); a talker whose name differs from the placed base's (`known_as`) has their ref overridden to a
base of our own carrying that name, templated on the old base; and the vendors we restock show their chest's stock.

Without the ESP (`--lines-only` runs these alone), the recipe's rules (docs/phases/4a-talk-to-everyone.md, recipe v2):
lines: every reply names only what its speaker's facts back; at most WARM_MAX warm address terms a person, none in
the stranger greeting; both greetings written. facts: a directions fact is a talk_route route; a lore-only fact makes
no physical claim the loaded world does not show (or contradicts); places carry the names the player sees. names
(35-cast.md section 54, 86-never-reuse-names.md): at most a third Verb-the-Noun names a settlement, an image once a
settlement, nothing from the never-reuse list, no canon name unless BM&V's base carries it, nothing Nordic.

    python3 -m tools.argonia_world.talk_check [--esp out/Argonia.esp] [--lines-only] [--settlement bmv.lilmoth ...]
"""
from __future__ import annotations

import argparse
import dataclasses
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world import db, esm

GET_IS_REFERENCE = 136
GET_STAGE = 58
QUEST_SOURCE = re.compile(r"^quest (ARG_\w+) stages? (\d+)(?:-(\d+))?;")    # 'stages A-B': heard while the quest runs
GET_RELATIONSHIP_RANK = 403     # Skyrim.esm's Hello INFOs: 148 gate on it with the player (>= 1 friend: 37 of them)
GREET = {"talk.greet-stranger": 4, "talk.greet-friend": 3}     # topic -> compare operator (< 1, >= 1)
WARM_MAX = 2
WARM = re.compile(r"(?i)\b(?:my (?:good |dear |old )?(?:friend|brother|sister|cousin)|friend|brother|sister|"
                  r"dear one|dearest|egg-kin|clutch-?mate)\b")

# Skyrim ingredient names a reply may say only when its speaker's own facts name them (owner ruling 2026-11-08: a
# plant stays only where BM&V places it, and a reply states only what its speaker's facts back).
INGREDIENTS = ("amanita", "parasol moss", "nightshade", "deathbell", "jazbay", "gleamblossom", "lavender", "juniper",
               "nirnroot", "lichen", "creep cluster", "glowing mushroom", "fungal pod", "mountain flower", "leek",
               "gourd", "thistle", "canis root", "frost mirriam", "snowberr")
_NAME = re.compile(r"(?<![.!?…] )(?<!^)\b[A-Z][A-Za-z]+(?:-[A-Za-z]+)*")
_SIDE = re.compile(r"\b(?:north|south|east|west)(?:-(?:north|south|east|west))* (?:side|edge|end)\b")


def unbacked(text: str, backing: str) -> list[str]:
    """What a reply names that its speaker's rows do not: a mid-sentence capitalised name, a Skyrim ingredient or a
    'south side'-style place, absent from `backing` (the speaker's facts and own row, as one string)."""
    back = backing.lower()
    out = [m.group(0) for m in _NAME.finditer(text) if m.group(0).lower() not in back]
    out += [i for i in INGREDIENTS if i in text.lower() and i not in back]
    out += [m.group(0) for m in _SIDE.finditer(text.lower()) if m.group(0) not in back]
    return out


def check_lines(w) -> int:
    """Every written reply's names, ingredients and sides against its speaker's facts and row; returns the count."""
    facts = {f.id: f.claim for f in w.rows("talk_fact")}
    bad = 0
    for t in w.rows("talker"):
        own = " ".join(facts[f.strip()] for tt in w.rows("talker_topic", talker=t.id)
                       for f in tt.facts.split(",") if f.strip() in facts)
        backing = own + " " + " ".join(str(v) for v in dataclasses.astuple(t))
        for ln in w.rows("talk_line", talker=t.id):
            miss = unbacked(ln.text, backing)
            if miss:
                bad += 1
                print(f"UNBACKED {t.id} {ln.topic} #{ln.ord}: {sorted(set(miss))}")
        lines = w.rows("talk_line", talker=t.id)
        if lines:
            warm = [(ln.topic, m.group(0)) for ln in lines for m in WARM.finditer(ln.text)]
            if len(warm) > WARM_MAX or any(tp == "talk.greet-stranger" for tp, _ in warm):
                bad += 1
                print(f"WARM {t.id} {t.known_as}: {len(warm)} warm address terms (max {WARM_MAX}, none to a "
                      f"stranger): {warm}")
            missing = set(GREET) - {ln.topic for ln in lines}
            if missing:
                bad += 1
                print(f"GREETING {t.id} {t.known_as}: no {sorted(missing)}")
    print(f"talk_check lines: {bad} problems (unbacked, warm address, greetings)")
    return bad


# --- facts: BM&V's world, not the lore's ----------------------------------------------------------------------------

# A physical thing a lore line may claim (a pattern over the claim), and the landmark kinds (talk_route) that show
# it in the loaded world; an empty set: nothing the census classes shows it, so a claim of it needs a cited ref.
PHYSICAL = {"ships?": {"ship", "wreck"}, "lighters?": {"boat", "rowboat"}, "boats?": {"boat", "rowboat", "ship"},
            "docks?": {"dock"}, "piers?": {"dock"}, "bridges?": {"bridge"}, "towers?": {"tower", "lighthouse"},
            "monument": {"statue"}, "statues?": {"statue"}, "xanmeer": {"ruin"}, "ruins?": {"ruin"},
            "mangroves?": {"bigtree"}, "hist (?:is|stands|grows|tree)|'s hist": {"hist"}, "stilts?": set(),
            "rice": set(), "padd(?:y|ies)": set(), "drakes?": set(), "crocodiles?": set(), "walls?": set(),
            "flotilla": {"boat", "rowboat"}}
# a negation a few words before the thing: "large ships cannot dock", "no lighters"
NEGATED = r"(?i)\b(?:no|not|cannot|can't|never|nor)\W+(?:\w+\W+){{0,3}}?(?:{w})\b"
FORM_KEY = re.compile(r"\b[0-9A-F]{6}\b")


def check_facts(w, settlements: list[str]) -> int:
    """Each fact of the settlements against the loaded world: routed directions, no lore-only physical claim the
    world does not show or contradicts, places by the names the player sees."""
    from tools.argonia_world import talk_route as tr
    names = tr.renames(w)
    W = tr.World(names=names)
    box = {}
    for t in w.rows("bmv_talker"):
        if t.settlement in settlements:
            b = box.setdefault(t.settlement, [t.x, t.y, t.x, t.y])
            b[:] = [min(b[0], t.x), min(b[1], t.y), max(b[2], t.x), max(b[3], t.y)]
    near = {s: [r for r in W.refs if r["lm"] and b[0] - 8192 <= r["x"] <= b[2] + 8192
                and b[1] - 8192 <= r["y"] <= b[3] + 8192] for s, b in box.items()}
    bad = 0
    for f in w.rows("talk_fact"):
        if f.settlement not in settlements:
            continue
        why = []
        if f.topic == "talk.directions" and not f.source.startswith("talk_route:"):
            why.append("directions not a talk_route route")
        elif f.topic == "talk.directions":
            why += [f"directions {p}" for p in tr.leg_problems(f.source, W)]
        if not FORM_KEY.search(f.source):
            low = f.claim.lower()
            for word, kinds in PHYSICAL.items():
                if not re.search(rf"\b(?:{word})\b", low):
                    continue
                seen = [r["key"] for r in near.get(f.settlement, []) if r["lm"][0] in kinds]
                if seen and re.search(NEGATED.format(w=word), f.claim):
                    why.append(f"contradicted: claims no '{word}', the world places {len(seen)} ({seen[0]})")
                elif seen:
                    why.append(f"lore-only physical claim '{word}': cite the ref that shows it ({seen[0]})")
                else:
                    why.append(f"lore-only physical claim '{word}' the world does not show")
        for old, new in names.items():
            if re.search(rf"\b{re.escape(old)}\b", f.claim):
                why.append(f"'{old}' is '{new}' to the player")
        if why:
            bad += 1
            print(f"FACT {f.id}: {'; '.join(why)}\n     {f.claim}")
    print(f"talk_check facts: {bad} problems")
    return bad


# --- names: 35-cast.md section 54 and 86-never-reuse-names.md ---------------------------------------------------------

IMAGES = {"water": r"water|shallow|rain|tide|river|pool|flood|wave|wade|swim|minnow|channel|current|stream",
          "reed": r"reed", "root": r"root", "stone": r"stone|rock|pebble", "shadow": r"shadow|shade|dark|night|lantern",
          "sky": r"cloud|sky|star|moon|sun", "boat": r"boat|oar|sail|hull", "blade": r"edge|blade|knife|sword",
          "eye": r"eye|sees|looks|watch|stare|peek", "hand": r"hand|lift|carr|fold|plait|weav"}
VERB_NOUN = re.compile(r"^[A-Z][a-z]+s-(?:[A-Z][a-z]+-)*[A-Z]?[a-z]+$")
NORDIC = re.compile(r"(?i)(son|sen|dottir)$|bj[oö]rn|ulf|grim|thor|sven|gunn|hild|stein|frey|sigur|ragn|vald|"
                    r"hroth|jarl|skald")
# Canon Argonians of the games (a nobody does not carry them); the lore files' hyphenated names are added.
CANON = {"deep-in-his-cups", "only-he-stands-there", "derkeethus", "nesh-deeka", "heita-meen", "na-kesh",
         "tsono-xuhil", "keshu", "nurwul", "nuetepa", "brand-shei", "shahvee", "scouts-many-marshes", "talen-jei",
         "keerava", "madesi", "wujeeta", "stands-in-shallows", "neetrenaza", "gulum-ei", "teeba-ei", "hides-his-heart",
         "hides-his-eyes", "veezara", "mere-glim", "dar-ma", "huleeya", "im-kilaya", "beem-ja", "xukas",
         "listens-by-smell", "lights-in-shadow", "drinks-ale"}


def never_reuse() -> set[str]:
    text = (db.REPO / "story/design/quests/86-never-reuse-names.md").read_text()
    out = set()
    for head in ("**Places:**", "**NPCs:**"):
        line = next((ln for ln in text.splitlines() if ln.startswith(head)), "")
        out |= {n.strip(" .").lower() for n in line[len(head):].split(",") if n.strip()}
    return out


def lore_names() -> set[str]:
    """Every hyphenated proper name the canon lore files carry (persons and places): not a nobody's name."""
    out = set()
    for p in (db.REPO / "story/lore").rglob("*.md"):
        if "extrapolation" not in p.parts:
            out |= {m.lower() for m in re.findall(r"\b[A-Z][a-z]+(?:-[A-Z][a-z]+){1,4}\b", p.read_text())}
    return out


def check_names(w, settlements: list[str]) -> int:
    banned, canon = never_reuse(), CANON | lore_names()
    bad = 0
    for s in settlements:
        people = [(t, w.get("bmv_talker", t.id)) for t in w.rows("talker")]
        people = [(t, c) for t, c in people if c and c.settlement == s]
        if not people:
            continue
        vn = [t.known_as for t, _ in people if VERB_NOUN.match(t.known_as)]
        if len(vn) * 3 > len(people):
            bad += 1
            print(f"NAMES {s}: {len(vn)} of {len(people)} Verb-the-Noun (max a third, {len(people) // 3}): {vn}")
        seen: dict[str, str] = {}
        for t, c in people:
            name = t.known_as
            own = (c.name or "").lower().replace(" ", "-") == name.lower().replace(" ", "-")
            why = []
            if name.lower() in banned:
                why.append("on the never-reuse list")
            if name.lower() in canon and not own:
                why.append("a canon name, not BM&V's base name")
            if NORDIC.search(name):
                why.append("Nordic element")
            for img, rx in IMAGES.items():
                if re.search(rf"(?i)(^|-)({rx})", name):
                    if img in seen and not own:
                        why.append(f"image '{img}' already in {seen[img]}")
                    seen.setdefault(img, name)
            if why:
                bad += 1
                print(f"NAME {s} {t.id} {name}: {'; '.join(why)}")
    print(f"talk_check names: {bad} problems")
    return bad


def check_rumours(w, pl, recs) -> int:
    """Each quest rumour (a talk.rumours fact whose source is 'quest ARG_X stage N; giver ...'): the quest is in the
    plugin, Start Game Enabled with N its start-up stage; the giver's opening INFO (a topic of the quest's own gated
    GetStage quest == N) exists; each talker citing the fact has an ARG_Talk_Rumours INFO gated to their ref carrying
    every GetStage condition of that opening, so it is offered only while the quest can start; and no talker is one of
    the quest's own people (a forced alias ref)."""
    quests = {r.edid: r for r in recs if r.sig == "QUST"}
    dial = {r.key: r for r in recs if r.sig == "DIAL"}

    def stages(r):  # [(quest key, op, value)] of the INFO's GetStage conditions
        return [(pl.form_key(struct.unpack_from("<I", d, 12)[0]), d[0] >> 5, struct.unpack_from("<f", d, 4)[0])
                for d in r.all("CTDA") if struct.unpack_from("<H", d, 8)[0] == GET_STAGE]

    def refs(r):
        return {pl.form_key(struct.unpack_from("<I", d, 12)[0]) for d in r.all("CTDA")
                if struct.unpack_from("<H", d, 8)[0] == GET_IS_REFERENCE}
    infos = [(dial.get(pl.form_key(r.parents[-1][1])), r) for r in recs if r.sig == "INFO"]
    bad = n = 0
    for f in w.rows("talk_fact"):
        m = QUEST_SOURCE.match(f.source or "") if f.topic == "talk.rumours" else None
        if not m:
            continue
        n += 1
        edid, start = m.group(1), int(m.group(2))
        why = []
        q = quests.get(edid)
        if q is None:
            print(f"RUMOUR {f.id}: {edid} not in the plugin")
            bad += 1
            continue
        flags = struct.unpack_from("<H", q.sub("DNAM"), 0)[0]
        idx = {struct.unpack_from("<H", d, 0)[0]: d[2] for d in q.all("INDX")}
        if m.group(3):  # a running line: stages A and B+1 are the quest's (BC02: the fire 20, the first ending 91)
            hi = int(m.group(3))
            if start not in idx or hi + 1 not in idx:
                why.append(f"stage {start} or {hi + 1} is not one of the quest's")
            gate = {(q.key, 3, float(start)), (q.key, 5, float(hi))}    # GetStage >= A, <= B
            for tt in w.rows("talker_topic", topic="talk.rumours"):
                if f.id not in [x.strip() for x in (tt.facts or "").split(",")]:
                    continue
                mine = [r for d, r in infos if d is not None and d.edid == "ARG_Talk_Rumours" and tt.talker in refs(r)]
                if len(mine) != 1:
                    why.append(f"{tt.talker}: {len(mine)} rumour INFOs")
                elif set(stages(mine[0])) != gate:
                    why.append(f"{tt.talker}: rumour gate {stages(mine[0])} is not {sorted(gate)}")
            print(f"RUMOUR {f.id}: {edid} stages {start}-{hi}" + (f"  PROBLEMS {'; '.join(why)}" if why else "  ok"))
            bad += bool(why)
            continue
        if not flags & 1:
            why.append("quest not Start Game Enabled")
        if start not in idx or not idx[start] & 2:
            why.append(f"stage {start} is not its start-up stage")
        own = [r for d, r in infos if d is not None and d.ref("QNAM") == q.key
               and (q.key, 0, float(start)) in stages(r)]
        if not own:
            why.append(f"no opening line of the quest gated on stage {start}")
        people = {pl.form_key(struct.unpack_from("<I", d, 0)[0]) for d in q.all("ALFR")}
        for tt in w.rows("talker_topic", topic="talk.rumours"):
            if f.id not in [x.strip() for x in (tt.facts or "").split(",")]:
                continue
            if tt.talker in people:
                why.append(f"{tt.talker} is one of the quest's own people")
            mine = [r for d, r in infos if d is not None and d.edid == "ARG_Talk_Rumours" and tt.talker in refs(r)]
            if len(mine) != 1:
                why.append(f"{tt.talker}: {len(mine)} rumour INFOs")
            elif own and not any(set(stages(o)) <= set(stages(mine[0])) for o in own):
                why.append(f"{tt.talker}: rumour gate {stages(mine[0])} lacks the opening's {stages(own[0])}")
        print(f"RUMOUR {f.id}: {edid} from stage {start}" + (f"  PROBLEMS {'; '.join(why)}" if why else "  ok"))
        bad += bool(why)
    print(f"talk_check rumours: {n} quest rumours, {bad} problems")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--esp", default="out/Argonia.esp")
    ap.add_argument("--lines-only", action="store_true", help="only the data checks (lines, facts, names; no ESP)")
    ap.add_argument("--settlement", action="append", help="the settlements whose facts and names are checked "
                    "(default: every settlement with a talker)")
    a = ap.parse_args()
    w = db.open()
    sets = a.settlement or sorted({w.get("bmv_talker", t.id).settlement for t in w.rows("talker")} - {None})
    nlines = check_lines(w) + check_facts(w, sets) + check_names(w, sets)
    if a.lines_only:
        print(f"talk_check: {nlines} problems")
        return 1 if nlines else 0
    pl = esm.Plugin.read(Path(a.esp))
    recs = pl.records()
    by_key = {r.key: r for r in recs}
    seen = Counter(r.key for r in recs)
    # the world (WRLD group label) or interior each record sits in, for the read-back over every world
    world_of = {r.key: next((pl.form_key(lab) for g, lab in r.parents if g == 1), "interior") for r in recs}
    worlds = Counter()
    dial = {r.key: r.edid for r in recs if r.sig == "DIAL"}
    topic_of = {}
    for t in w.rows("talk_topic"):
        topic_of["ARG_Talk_" + "".join(p.capitalize() for p in t.id.split(".")[1].split("-"))] = t.id
    gated = defaultdict(set)
    for r in recs:
        if r.sig != "INFO":
            continue
        edid = dial.get(pl.form_key(r.parents[-1][1]), "")
        if not edid.startswith("ARG_Talk_"):
            continue  # a quest's own topic gated on the same ref (LQ25, LQ30, MQ05) is not talk's
        topic = topic_of.get(edid, edid)
        for d in r.all("CTDA"):
            if struct.unpack_from("<H", d, 8)[0] == GET_RELATIONSHIP_RANK and edid == "ARG_Talk_Hello":
                op, v = d[0] >> 5, struct.unpack_from("<f", d, 4)[0]
                topic = next((g for g, o in GREET.items() if o == op and v == 1.0), f"Hello rank op {op} {v}")
        for d in r.all("CTDA"):
            if struct.unpack_from("<H", d, 8)[0] == GET_IS_REFERENCE:
                gated[pl.form_key(struct.unpack_from("<I", d, 12)[0])].add(topic)
    bad = nlines
    talkers = [t for t in w.rows("talker") if t.status in ("written", "built")]
    for t in talkers:
        c = w.get("bmv_talker", t.id)
        want = {tt.topic for tt in w.rows("talker_topic", talker=t.id)}
        got = gated.get(t.id, set())
        line = f"{t.id:32} {t.known_as:24} topics {len(got)}/{len(want)}"
        if got != want:
            line += f"  MISMATCH missing {sorted(want - got)} extra {sorted(got - want)}"
            bad += 1
        if t.known_as != c.name and not t.known_as.startswith("the "):
            ref = by_key.get(t.id)
            base = by_key.get(ref.ref("NAME")) if ref else None
            if base is None or base.zstr("FULL") != t.known_as or base.ref("TPLT") != c.npc:
                line += f"  NAME WRONG (ref {'overridden' if ref else 'not overridden'}, base {base.edid if base else None})"
                bad += 1
            elif seen[t.id] != 1 or seen[base.key] != 1:
                line += f"  DUPLICATE (ref x{seen[t.id]}, base x{seen[base.key]})"
                bad += 1
            else:
                worlds[world_of[t.id]] += 1
                line += f"  named: ref -> {base.edid} \"{base.zstr('FULL')}\" (template {c.npc})"
        print(line)
    for f in (r for r in recs if r.sig == "FACT" and r.ref("VENC")):
        chest = by_key.get(f.ref("VENC"))
        box = by_key.get(chest.ref("NAME")) if chest else None
        if box is None:
            print(f"{f.edid}: chest not ours"); bad += 1
            continue
        stock = [(pl.form_key(struct.unpack_from("<I", d, 0)[0]), struct.unpack_from("<i", d, 4)[0]) for d in box.all("CNTO")]
        print(f"{f.edid}: chest {chest.edid} -> {box.edid}: " + ", ".join(f"{k} x{n}" for k, n in stock))
    bad += check_rumours(w, pl, recs)
    print("talk_check names by world: " + ", ".join(f"{k} {n}" for k, n in sorted(worlds.items())))
    print(f"talk_check: {len(talkers)} talkers, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

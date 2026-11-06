"""Run: python3 -m tools.argonia_world.slice_ledger.slice (from the repo root).

Load the first story slice's ledger from slice_rows.py, with one clean-up per host place, and `wait` for the rest."""
import json, re
from tools.argonia_world.slice_ledger.slice_rows import ROWS, EXTRA_JAR, SOLDIERS, KEEP
from tools.argonia_world import db
w = db.load()
spirit = {json.loads(l).get("quest"): json.loads(l) for l in open(db.REPO / "story/design/quests/adaptation-spirit.jsonl")}
for t in ("quest_bmv_need", "quest_world_edit", "quest_prereq", "quest_host", "quest_adaptation", "world_edit_target"):
    w.con.execute(f'DELETE FROM "{t}"'); w.dirty.add(t)
KEEP_SHARED = {"we.door.rose-jail", "we.name.soulrest"}
w.con.execute("DELETE FROM world_edit WHERE id NOT IN (%s)" % ",".join("?" * len(KEEP_SHARED)), tuple(KEEP_SHARED))
w.dirty.add("world_edit")
w.update("world_edit", "we.door.rose-jail", settlement="bmv.blackrose", cell="000811:Dawnguard.esm",
         description="a door pair: a new door at BMN's 'Black Rose Jail' marker outside Blackrose into 01BlackRoseJail, "
                     "the Rose's lower levels; the interior's exit 1F5AE4 re-pointed to it; the old exterior door 1EEB70 "
                     "in BlackMarsh2 (-8,26) disabled", lore="story/lore/extrapolation/gap-register.md §8 QA4")
rows = {r["quest"]: r for r in ROWS}
JAR = re.compile(r"^(DLC1Gargoyle|Fox|Nord|HighElf|Skeleton|Draugr|DLC1SoulCairn|DLC2Lurker|DLC2Werebear|DwarvenCenturion|DLC2DwarvenBallista|DA03Barbas|DogCompanion|DLC1Husky|Dremora)")
OFFICIAL = re.compile(r"soldier|guard|captain|archer|mq101|legion|priest", re.I)
NAMED = re.compile(r"Member of the Night|Priestess of Arkay|Thalmor|Old Salty|Whiterun|CWCourier|BYOH|Rorikstead|SnowShod|Dremora", re.I)
NAGA_OFF = {"bmv.lilmoth"}
def jarring(r, s):
    race, name = r["race"] or "", r["name"] or ""
    extra = EXTRA_JAR.get(s)
    if r["id"] in KEEP:
        return False
    return bool(re.search(SOLDIERS, name) or r["record"] == "LVLN" or JAR.match(race) or (race.startswith("Imperial") and OFFICIAL.search(name))
                or NAMED.search(name) or (s in NAGA_OFF and race.startswith("BMNaga"))
                or (extra and re.search(extra, name + " " + race)))
Q = """SELECT p.id, n.id base, n.record, n.template, r.editor_id race,
       coalesce(n.name, '') || ' ' || coalesce(n.editor_id, '') name
       FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc LEFT JOIN bmv_race r ON r.id = n.race WHERE p.cell IN (%s) ORDER BY p.id"""
hosts = {}
for r in rows.values():
    for h in r["hosts"]:
        hosts.setdefault(h["settlement"], set())
        if h.get("cell"):
            hosts[h["settlement"]].add(h["cell"])
clean = {}
CELL_ONLY = {"bmv.blackmarshnorth.thorn1"}   # hosted only by the ship's cell
for s, cells in sorted(hosts.items()):
    own = set() if s in CELL_ONLY else set(w.values("SELECT cell FROM bmv_settlement_cell WHERE settlement = ?", s))
    near = set()
    for c in own:
        near |= set(w.values("""SELECT n.id FROM bmv_cell c JOIN bmv_cell n ON n.worldspace = c.worldspace
            AND abs(n.grid_x - c.grid_x) <= 1 AND abs(n.grid_y - c.grid_y) <= 1 WHERE c.id = ? AND NOT c.interior""", c))
    taken = set(w.values("SELECT cell FROM bmv_settlement_cell WHERE settlement <> ?", s))
    cs = own | cells | (near - taken)
    ph = ",".join("?" * len(cs))
    placed = w.query(Q % ph, *sorted(cs))
    gone = [p for p in placed if jarring(p, s)]
    gone_ids = {p["id"] for p in gone}
    fixed = [p for p in placed if p["id"] not in gone_ids and (p["record"] == "LVLN" or p["template"])]
    if not placed:
        continue
    eid = "we.clean." + s.split(".")[-1]
    clean[s] = eid
    w.insert("world_edit", id=eid, kind="creature_remove", settlement=s, cell=None,
             target=(gone or fixed or placed)[0]["id"],
             description=(f"the slice's clean-up of this place and its rooms: {len(gone)} placements set initially disabled "
                          f"in their own overrides (every Nord, Thalmor, vanilla Imperial official, skeleton, draugr-race walker, "
                          f"Soul Cairn shade, Lurker, werebear-race beast, gargoyle, Dremora, Dwemer construct, fox-race person, "
                          f"named vanilla horse, cow or dog, and the place's own extras), and {len(fixed)} templated placements "
                          f"that stay given a fixed level at the place's band (0006, 0035); the full list is world_edit_target"),
             race=None, band=None, lore="story/lore/topics/foreign-powers.md (no Thalmor or Imperial presence in 4E Black Marsh)")
    for p in gone:
        w.insert("world_edit_target", edit=eid, target=p["id"], what="disabled: " + p["name"].strip()[:80])
    for p in fixed:
        w.insert("world_edit_target", edit=eid, target=p["id"], what="fixed level: " + p["name"].strip()[:80])
# the road from Lilmoth to Blackrose: its vanilla Imperial officials go too (0006), one corridor edit for BC01
cor = w.query("""SELECT p.id, coalesce(n.name,'') || ' ' || coalesce(n.editor_id,'') name FROM bmv_placement p
    JOIN bmv_npc n ON n.id = p.npc JOIN bmv_race r ON r.id = n.race JOIN bmv_cell c ON c.id = p.cell
    WHERE c.worldspace LIKE '23D689%' AND c.grid_x BETWEEN 10 AND 31 AND c.grid_y BETWEEN -14 AND 3
      AND r.editor_id LIKE 'Imperial%'""")
cor = [p for p in cor if OFFICIAL.search(p["name"])]
w.insert("world_edit", id="we.clean.road", kind="npc_remove", settlement="bmv.blackrose", cell=None, target=cor[0]["id"],
         description=f"the road from Lilmoth to Blackrose (BlackMarsh 10..31, -14..3): {len(cor)} vanilla Imperial soldiers, archers and officers set initially disabled (0006); its swamp creatures stay, so BC01 is band 2",
         race=None, band=None, lore="story/lore/topics/foreign-powers.md (no Imperial presence in 4E Black Marsh)")
for p_ in cor:
    w.insert("world_edit_target", edit="we.clean.road", target=p_["id"], what="disabled: " + p_["name"].strip()[:80])
for r in rows.values():
    for e in r["new_edits"]:
        w.insert("world_edit", **{k: e.get(k) for k in ("id", "kind", "settlement", "cell", "target", "description", "race", "band", "lore")})
for (qid,) in w.query("SELECT id FROM quest"):
    if qid not in rows:
        rows[qid] = dict(quest=qid, verdict="wait", spirit=spirit[qid]["spirit"],
                         why="outside the first story slice (owner, 2026-11-06); adapted after the owner tries it")
for r in rows.values():
    live = r["verdict"] in ("keep", "adapt")
    w.insert("quest_adaptation", quest=r["quest"], verdict=r["verdict"], merged_into=r.get("merged_into"), spirit=r["spirit"],
             premise=r.get("premise") if live else None, changed=r.get("changed"), why=r["why"],
             band=r.get("band") if live else None, lore=r.get("lore") if live else None)
for r in rows.values():
    if r["verdict"] not in ("keep", "adapt"):
        continue
    for i, h in enumerate(r["hosts"]):
        w.insert("quest_host", quest=r["quest"], ord=i, settlement=h["settlement"], cell=h.get("cell"), edit=None, role=h["role"], what=h["what"])
    es = set(r["edits"]) | {x["id"] for x in r["new_edits"]} | {clean[h["settlement"]] for h in r["hosts"] if h["settlement"] in clean}
    for e in sorted(es):
        w.insert("quest_world_edit", quest=r["quest"], edit=e)
    for n in r["needs"] + r.get("needs_extra", []):
        w.insert("quest_bmv_need", quest=r["quest"], target=n["target"], what=n["what"])
    for p in r["prereqs"]:
        w.insert("quest_prereq", quest=r["quest"], needs=p["needs"], why=p["why"])
# line hubs of the slice's lines, current
L = lambda s: f"quest.line.{s}"
for line in ("main", "night-reed", "chainbreakers"):
    w.delete("line_hub", line=L(line))
HUB = {"main": [("bmv.helstrom", "2076BB:Black Marsh.esm", "seat", "the Veiled Reed in Helstrom; the hall where the empty seat is lodged"),
                ("bmv.lilmoth", None, "hub", "the opening at Dock1, the unmarked house"), ("bmv.hereguardplantation", None, "hub", "the Owing camp at the paddy edge"),
                ("bmv.village", None, "hub", "the first turned Hist, east of Lilmoth"), ("bmv.dock5", None, "hub", "Helstrom's river landing")],
       "night-reed": [("bmv.lilmoth", "16BF81:Black Marsh North.esp", "seat", "the Chapter under Pusbottom"), ("bmv.dock2", None, "hub", "Soulrest's dock and its fence")],
       "chainbreakers": [("bmv.blackrose", "15635D:Black Marsh.esm", "seat", "the Chainbreakers' house in Blackrose"),
                         ("bmv.blackrose", "000811:Dawnguard.esm", "hub", "the Rose's lower levels, outside the town"), ("bmv.dock2", None, "hub", "the broker's barge at Soulrest")]}
for line, hs in HUB.items():
    for i, (s, c, role, why) in enumerate(hs):
        w.insert("line_hub", line=L(line), ord=i, settlement=s, cell=c, edit=None, role=role, why=why)
print(w.save())

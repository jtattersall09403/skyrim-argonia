"""Map every stage of Act I's records to the block set (docs/design/blocks.md, 'Every stage of every act quest, mapped').

Run: python3 -m tools.argonia_world.slice_ledger.stage_blocks  (writes the table into docs/design/blocks.md between
its stage_blocks markers, from the story database, the one source; --print prints it instead)."""
import re, subprocess, sys
import yaml

QUESTS = ("mq01", "mq03", "mq04", "mq05")
TRIG = {"topicHeardFrom": "TR-topic", "inZone": "TR-zone", "inSettlement": "TR-zone", "npcAlive": "TR-death",
        "placeCleared": "TR-death", "counterAtLeast": "TR-death", "hasItem": "TR-acquire", "objectiveComplete": "TR-stage",
        "npcInCustody": "TR-death", "sceneEnded": "TR-scene"}
COND = {"questStage": "C-stage", "stageEverReached": "C-stage", "flag": "C-stage", "timeOfDay": "C-time",
        "hasItem": "C-item", "npcAlive": "C-alive", "skillAtLeast": "C-skill", "dispositionAtLeast": "C-global",
        "npcAtMark": "C-time", "goldAtLeast": "C-item", "detectedBy": "C-detected"}
EFF = {"grantTopic": "E-stage", "setFlag": "E-global", "enableRef": "E-enable", "disableRef": "E-enable",
       "applyLocalVariant": "E-enable", "startScene": "E-scene", "moveRef": "E-move", "setSchedule": "E-package",
       "giveItem": "E-item", "takeItem": "E-item", "giveGold": "E-item", "takeGold": "E-item",
       "setFactionRank": "E-faction", "grantServiceAccess": "E-faction", "changeStanding": "E-global",
       "changeSettlementStanding": "E-global", "addOwing": "E-global", "clearOwing": "E-global",
       "changeDisposition": "E-regard", "grantHistStep": "E-global", "setDoorAccess": "E-item"}
UNKNOWN = set()

def terms(o):
    return set(re.findall(r"'(\w+)':", str(o)))

def blocks(ts, table):
    out = set()
    for t in ts:
        if t in table:
            out.add(table[t])
        elif t not in TRIG and t not in COND and t not in EFF and t not in {"to", "when", "all", "any", "not"}:
            UNKNOWN.add(t)
    return out

def main():
    rows = []
    for q in QUESTS:
        y = yaml.safe_load(subprocess.run([sys.executable, "-m", "tools.argonia_world.quest_record", "export",
                                           "quest.main." + q], capture_output=True, text=True, check=True).stdout)
        ends = {e["id"]: e for e in y.get("endings", [])}
        into = {}
        for s in y["stages"]:
            for k in ("successors", "failForward"):
                for x in s.get(k) or []:
                    into.setdefault(x["to"], []).append(x.get("when"))
        for s in y["stages"]:
            w = into.get(s["id"], [])
            trig = blocks(set().union(*map(terms, w)) if w else set(), TRIG)
            cond = blocks(set().union(*map(terms, w)) if w else set(), COND) - {"C-alive"} | (
                {"C-alive"} if any("npcAlive" in str(x) for x in w) else set())
            fx = {"E-stage"} | blocks(terms(s.get("onEnter")), EFF)
            e = ends.get(s.get("endingId"))
            if e:
                fx |= blocks(terms(e.get("world")) | terms(e.get("rewards")), EFF)
                fx.add("TR-chain")
            trig_in = ", ".join(sorted(trig - {"TR-stage"})) or (("the new-game start (ARG_Opening)" if q == "mq01" else "TR-chain (the previous quest ends)")
                                                  if s["id"] == y["start"] else "-")
            if "TR-stage" in trig:
                trig_in += " (objectives done)"
            rows.append(f"| {q.upper()} {s['id']} | {trig_in} | {', '.join(sorted(cond)) or '-'} | {', '.join(sorted(fx))} |")
    out = ["| Quest stage | Trigger in | Conditions | Effects |", "|---|---|---|---|", *rows, ""]
    from tools.argonia_world import db
    w = db.load()
    for q in QUESTS:
        es = w.values("SELECT edit FROM quest_world_edit WHERE quest = ? ORDER BY edit", "quest.main." + q)
        out.append(f"- {q.upper()} stands on {len(es)} ledgered world edits: " + ", ".join(f"`{e}`" for e in es) + ".")
    if UNKNOWN:
        print("UNMAPPED:", sorted(UNKNOWN), file=sys.stderr)
        return 1
    text = "\n".join(out)
    if "--print" in sys.argv:
        print(text)
        return 0
    md = db.REPO / "docs/design/blocks.md"
    doc = md.read_text(encoding="utf-8")
    b, e = "<!-- stage_blocks:begin (generated; do not edit) -->", "<!-- stage_blocks:end -->"
    head, rest = doc.split(b, 1)
    md.write_text(head + b + "\n" + text + "\n" + e + rest.split(e, 1)[1], encoding="utf-8")
    print("wrote", md.relative_to(db.REPO))
    return 0

if __name__ == "__main__":
    sys.exit(main())

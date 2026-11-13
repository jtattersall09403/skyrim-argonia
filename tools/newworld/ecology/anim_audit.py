"""Ecology animation audit: can every creature our ecology stage places move on the New World card?

For every distinct `src` (plugin:editor id) of out/newworld/plugin/ecology/actors.json (the placed actors) and
every record of newworld/sources/ecology/bindings.json kinds (unplaced ones are reported but never fail), the
NPC_ is resolved (templates followed when it has no race of its own) to its RACE, and the race to what the game
needs to move it, each file resolved on the New World card (tools/places/assets/resolve.py):

- the skeleton nif (RACE ANAM) and the behaviour project (RACE MODL .hkx), with the character and behaviour
  files the project names, and the project folder's `Animations` clips;
- the body mesh (NPC or race skin, ARMO -> ARMA MOD2/MOD3): it must be skinned (a nif with no skin instance
  moves as one rigid mesh) and share bone names with the skeleton nif;
- the source plugin and its masters: each must be in the profile's load order;
- when the world file is given, the copy of the race in it (the world writer copies the race whole) must keep
  the source race's skeleton and project.

    python -m tools.newworld.ecology.anim_audit [--json OUT] [--esm PATH]

Exit 1 when a placed kind fails."""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ECO = REPO / "out/newworld/plugin/ecology"
ACTORS = ECO / "actors.json"
BINDINGS = REPO / "newworld/sources/ecology/bindings.json"
ESM = REPO / "out/newworld/plugin/ArgoniaNewWorld.esm"
MODLIST = Path.home() / ".argonia/stack/MO2/profiles/NewWorld/modlist.txt"
MODS = Path.home() / ".argonia/stack/MO2/mods"
DATA = Path.home() / "games/skyrimse/Data"
SIGS = {"NPC_", "RACE", "ARMO", "ARMA"}
SKIN_BLOCKS = {"NiSkinInstance", "BSDismemberSkinInstance", "BSSkin::Instance"}
RIG_MIN = 0.1     # shared share of the skeleton nif's names with the rig's .hkx: working pairs measure 0.19 to 0.9
_NAME = re.compile(rb"[A-Za-z0-9_ \[\]\.\-:]{3,64}")
_HKX = re.compile(rb"[A-Za-z0-9_ .\-\\/]{3,120}\.hkx", re.I)


def norm(path: str, root: str = "meshes") -> str:
    p = path.strip().replace("/", "\\").lower().lstrip("\\")
    return p if p.startswith(root + "\\") else f"{root}\\{p}"


def _n(*paths):
    return tuple((p or "").lower().replace("/", "\\") for p in paths)


def _wanted(h: str) -> bool:
    """A .hkx a project or character file names that the actor needs: character, behaviour or skeleton."""
    return h.lower().startswith(("characters", "behaviors")) or "skeleton" in h.lower()


def _z(d: bytes) -> str:
    return d.split(b"\0", 1)[0].decode("cp1252")


def nif_info(data: bytes) -> dict:
    """The header of a Skyrim SE nif: its block type names and string table (node names among them)."""
    try:
        nl = data.index(b"\n")
        off = nl + 1 + 4 + 1 + 4                         # version, endian, user version
        nblocks = struct.unpack_from("<I", data, off)[0]
        off += 4 + 4                                     # block count, user version 2
        for _ in range(3):                               # creator, export info 1 and 2
            off += 1 + data[off]
        ntypes = struct.unpack_from("<H", data, off)[0]
        off += 2
        types = []
        for _ in range(ntypes):
            n = struct.unpack_from("<I", data, off)[0]
            types.append(data[off + 4:off + 4 + n].decode("ascii", "replace"))
            off += 4 + n
        idx = struct.unpack_from(f"<{nblocks}H", data, off)
        off += 2 * nblocks + 4 * nblocks                 # block type indexes, block sizes
        nstr = struct.unpack_from("<I", data, off)[0]
        off += 8
        strs = []
        for _ in range(nstr):
            n = struct.unpack_from("<I", data, off)[0]
            strs.append(data[off + 4:off + 4 + n].decode("cp1252", "replace"))
            off += 4 + n
        return {"skinned": any(types[i] in SKIN_BLOCKS for i in idx), "strings": {s.lower() for s in strs}}
    except (ValueError, struct.error, IndexError):
        return {"skinned": None, "strings": set()}


def race_files(race) -> dict:
    """A RACE's skeleton (ANAM) and behaviour project (MODL .hkx) per sex, by its MNAM / FNAM sections."""
    out: dict[str, dict] = {"M": {}, "F": {}}
    sex = None
    for sig, d in race.subs:
        if sig in ("MNAM", "FNAM"):
            sex = sig[0]
        elif sex and sig == "ANAM":
            out[sex].setdefault("skeleton", _z(d))
        elif sex and sig == "MODL" and _z(d).lower().endswith(".hkx"):
            out[sex].setdefault("project", _z(d))
    return out


class Audit:
    def __init__(self, resolver, load, laid=None):
        """resolver: tools.places.assets.resolve.Resolver (or alike); load(name) -> esm.Plugin of the NPC_, RACE,
        ARMO, ARMA records; laid(plugin name) -> whether the card lays that plugin's files (None: not checked)."""
        self.R, self.load, self.laid = resolver, load, laid
        self._plug: dict[str, object] = {}
        self._idx: dict[str, dict] = {}
        self._keys: dict[str, dict] = {}
        self._nif: dict[str, dict | None] = {}
        self._hkx: dict[str, list[str] | None] = {}
        self._rig: dict[str, set[str] | None] = {}

    def plugin(self, name: str):
        if name not in self._plug:
            try:
                self._plug[name] = self.load(name)
            except (FileNotFoundError, OSError):
                self._plug[name] = None
        return self._plug[name]

    def npc(self, name: str, edid: str):
        p = self.plugin(name)
        if p is None:
            return None
        if name not in self._idx:
            self._idx[name] = {r.edid: r for r in p.records("NPC_") if r.edid}
        return self._idx[name].get(edid)

    def find(self, key: str):
        owner = key.split(":", 1)[1]
        p = self.plugin(owner)
        if p is None:
            return None
        if owner not in self._keys:
            self._keys[owner] = {r.key: r for r in p.records()}
        return self._keys[owner].get(key)

    def nif(self, path: str) -> dict | None:
        key = norm(path)
        if key not in self._nif:
            b = self.R.read(key)
            self._nif[key] = None if b is None else nif_info(b)
        return self._nif[key]

    def hkx_names(self, path: str) -> list[str] | None:
        key = norm(path)
        if key not in self._hkx:
            b = self.R.read(key)
            self._hkx[key] = None if b is None else sorted({m.group().decode("cp1252") for m in _HKX.finditer(b)})
        return self._hkx[key]

    def clips(self, project: str) -> int:
        """How many .hkx files the project's `Animations` folder holds on the card (loose and archived)."""
        pre = norm(project.rsplit("\\", 1)[0] if "\\" in project else project.rsplit("/", 1)[0]) + "\\animations\\"
        n = sum(1 for k in self.R.loose if k.startswith(pre) and k.endswith(".hkx"))
        loose = {k for k in self.R.loose if k.startswith(pre)}
        p2 = pre.replace("\\", "/")
        for _, arc in self.R.archives():
            n += sum(1 for k in arc.files if k.startswith(p2) and k.endswith(".hkx") and k.replace("/", "\\") not in loose)
        return n

    def effective(self, rec, depth=0):
        """The NPC_ that gives the race: itself, else its template's."""
        if rec.ref("RNAM") or depth > 4:
            return rec
        t = rec.ref("TPLT")
        nxt = self.find(t) if t else None
        return self.effective(nxt, depth + 1) if nxt is not None else rec

    def rig_strings(self, path: str) -> set[str] | None:
        """Every name-like string in a skeleton .hkx (its bone names among them)."""
        key = norm(path)
        if key not in self._rig:
            b = self.R.read(key)
            self._rig[key] = None if b is None else {m.group().decode("cp1252").lower() for m in _NAME.finditer(b)}
        return self._rig[key]

    def skins(self, rec, race, female: bool = False) -> list[str]:
        """The body meshes of the race: the NPC's skin, else the race's, through ARMO -> the ARMA that serve the
        race -> MOD2 (male) / MOD3 (female); every ARMA when none names the race."""
        sk = rec.ref("WNAM") or race.ref("WNAM")
        armo = self.find(sk) if sk else None
        armas = []
        for s, d in (armo.subs if armo is not None else []):
            if s == "MODL" and len(d) == 4:
                a = self.find(armo.plugin.form_key(struct.unpack("<I", d)[0]))
                if a is not None:
                    armas.append(a)
        mine = [a for a in armas if race.key in {a.ref("RNAM")} | {a.plugin.form_key(struct.unpack("<I", d)[0])
                                                                  for d in a.all("MODL") if len(d) == 4}]
        out = []
        for a in mine or armas:
            p = a.zstr("MOD3" if female else "MOD2") or a.zstr("MOD2")
            if p and p not in out:
                out.append(p)
        return out

    def kind_of(self, src: str) -> dict:
        name, edid = src.split(":", 1)
        out = {"src": src, "ok": False, "reasons": [], "notes": []}
        bad = out["reasons"]
        rec = self.npc(name, edid)
        if rec is None:
            bad.append("npc record not found in its plugin")
            return out
        out["plugin"] = name
        masters = list(self.plugin(name).masters)
        if self.laid is not None:
            if not self.laid(name):
                bad.append(f"source mod of {name} is not enabled on the card (its files are not laid)")
            out["masters_not_laid"] = [m for m in masters if not self.laid(m)]
        eff = self.effective(rec)
        rk = eff.ref("RNAM")
        race = self.find(rk) if rk else None
        if race is None:
            bad.append("race record not found")
            return out
        out["race"] = {"key": rk, "edid": race.edid}
        female = bool((eff.sub("ACBS") or b"\0\0\0\0")[0] & 1)
        out["female"] = female
        files = race_files(race)["F" if female else "M"]
        sk, prj = files.get("skeleton"), files.get("project")
        out["skeleton"], out["project"] = sk, prj
        sknif = None
        if not sk:
            bad.append("race names no skeleton")
        else:
            sknif = self.nif(sk)
            out["skeleton_on_card"] = sknif is not None
            if sknif is None:
                bad.append(f"skeleton not on the card: {sk}")
        out["project_on_card"] = None
        if not prj:
            bad.append("race names no behaviour project")
        else:
            names = self.hkx_names(prj)
            out["project_on_card"] = names is not None
            if names is None:
                bad.append(f"behaviour project not on the card: {prj}")
            else:
                base = prj.replace("/", "\\").rsplit("\\", 1)[0]
                refs: dict[str, bool] = {}
                todo = [h for h in names if _wanted(h)]
                while todo:                                    # the character file, then the behaviours it names
                    h = todo.pop()
                    if h in refs:
                        continue
                    sub = self.hkx_names(f"{base}\\{h}")
                    refs[h] = sub is not None
                    if sub and len(refs) < 40:
                        todo += [x for x in sub if x not in refs and _wanted(x)]
                out["project_refs"] = refs
                gone = sorted(h for h, ok in refs.items() if not ok)
                if gone:
                    bad.append("project names files not on the card: " + ", ".join(gone))
            out["clips"] = self.clips(prj)
            if not out["clips"]:
                bad.append(f"no animation clips under {prj.rsplit(chr(92), 1)[0]}\\Animations")
        pdir = prj.replace("/", "\\").rsplit("\\", 1)[0] if prj else ""
        rigs = {h: s for h in (out.get("project_refs") or {}) if "skeleton" in h.lower()
                and (s := self.rig_strings(f"{pdir}\\{h}")) is not None}
        if rigs and sknif is not None and sknif["strings"]:
            rig, rigset = max(rigs.items(), key=lambda kv: len(sknif["strings"] & kv[1]))
            out["rig_bones_matched"] = round(len(sknif["strings"] & rigset) / len(sknif["strings"]), 2)
            if out["rig_bones_matched"] < RIG_MIN:
                bad.append(f"skeleton nif matches {out['rig_bones_matched']:.0%} of the bone names of the project's "
                           f"{rig}: its animations cannot drive this skeleton, the mesh moves rigid")
        meshes = self.skins(eff, race, female)
        out["meshes"] = []
        for m in meshes:
            info = self.nif(m)
            row = {"path": m, "on_card": info is not None}
            if info is None:
                bad.append(f"body mesh not on the card: {m}")
            else:
                row["skinned"] = info["skinned"]
                if sknif is not None:
                    row["bones_shared"] = len(info["strings"] & sknif["strings"])
                if info["skinned"] is False:
                    bad.append(f"body mesh has no skin instance, it moves as one rigid mesh: {m}")
                elif sknif is not None and not row["bones_shared"]:
                    bad.append(f"body mesh shares no bone name with the skeleton: {m}")
            out["meshes"].append(row)
        out["ok"] = not bad
        return out


def esm_race_copies(esm: Path | str, audit_load) -> dict:
    """Source race key -> (skeleton, project) of the copy in the world file; the copies are matched to their source
    races by editor id (`ANW_<tag>_<source edid>`)."""
    p = audit_load(esm)
    copies = {}
    for r in p.records("RACE"):
        if r.own and r.edid:
            copies[r.edid] = {"edid": r.edid, **race_files(r)}
    return copies


def run(actors: dict, bindings: dict, audit: Audit, copies: dict | None = None) -> dict:
    """{kinds: {kind: {ok, placed, srcs: [...]}}, failing: [kind], srcs: n}."""
    placed: dict[str, set] = defaultdict(set)
    for a in actors.get("actors", []):
        placed[a["src"]].add(a["kind"])
    kinds: dict[str, list[str]] = defaultdict(list)
    for src, ks in placed.items():
        for k in ks:
            kinds[k].append(src)
    unplaced: dict[str, list[str]] = defaultdict(list)
    for k, v in bindings.get("kinds", {}).items():
        for src in v.get("records", []):
            if src not in placed:
                unplaced[k].append(src)
    cache: dict[str, dict] = {}

    def one(src):
        if src not in cache:
            row = audit.kind_of(src)
            if copies is not None and row.get("race"):
                cp = copies.get("ANW_" + row["race"]["edid"]) or next(
                    (v for e, v in copies.items() if re.fullmatch(r"ANW_[A-Za-z0-9]+_" + re.escape(row["race"]["edid"]), e)), None)
                side = (cp or {}).get("F" if row.get("female") else "M", {})
                row["copy"] = {"edid": cp["edid"], **side} if cp else None
                if cp and _n(side.get("skeleton"), side.get("project")) != _n(row.get("skeleton"), row.get("project")):
                    row["reasons"].append("the world file's copy of the race differs from the source race")
                    row["ok"] = False
            cache[src] = row
        return cache[src]

    out = {}
    for k in sorted(set(kinds) | set(unplaced)):
        rows = [dict(one(s), placed=True) for s in sorted(kinds.get(k, []))]
        rows += [dict(one(s), placed=False) for s in sorted(unplaced.get(k, []))]
        pl_bad = [r for r in rows if r["placed"] and not r["ok"]]
        out[k] = {"verdict": "fail" if pl_bad else "ok", "placed": bool(kinds.get(k)), "srcs": rows,
                  "reason": "; ".join(sorted({x for r in pl_bad for x in r["reasons"]}))}
    return {"srcs": len(cache), "failing": [k for k, v in out.items() if v["verdict"] == "fail"], "kinds": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", help="write the full report here")
    ap.add_argument("--esm", default=str(ESM), help="the world file, whose race copies are compared")
    ap.add_argument("--actors", default=str(ACTORS))
    ap.add_argument("--bindings", default=str(BINDINGS))
    a = ap.parse_args(argv)
    from tools.argonia_world.esm import Plugin
    from tools.newworld.ecology.census import plugin_path
    from tools.places.assets.resolve import Resolver

    def load(name):
        return Plugin.read(name if Path(name).exists() else plugin_path(name), SIGS)

    on = {ln[1:].strip().lower() for ln in MODLIST.read_text(errors="replace").splitlines() if ln.startswith("+")} \
        if MODLIST.exists() else None
    holders: dict[str, bool] = {}

    def laid(name):
        if name not in holders:
            holders[name] = (DATA / name).exists() or on is None or any(
                (m / name).exists() and m.name.lower() in on for m in MODS.iterdir())
        return holders[name]

    audit = Audit(Resolver(), load, laid)
    copies = esm_race_copies(a.esm, load) if a.esm and Path(a.esm).exists() else None
    res = run(json.loads(Path(a.actors).read_text()), json.loads(Path(a.bindings).read_text()), audit, copies)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(res, indent=1))
    for k, v in res["kinds"].items():
        print(f"{v['verdict']:4} {k:28} {'placed' if v['placed'] else 'unplaced':8} {v['reason']}")
    print(f"{res['srcs']} records, {len(res['failing'])} failing kinds: {', '.join(res['failing'])}")
    return 1 if res["failing"] else 0


if __name__ == "__main__":
    sys.exit(main())

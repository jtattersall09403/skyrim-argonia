"""Build the asset explorer's publishable folder. usage: python3 tools/newart/asset_explorer.py

Reads the asset records (newworld/sources/art/, in this checkout) and the workshop's outputs (out/newart/ of the MAIN
tree, found from git's common directory, so a lane in a worktree reads the same models), and writes a fresh folder
out/newart/explorer-site/ holding exactly what the page serves: index.html, data/catalog.json, the models of every
version and the pictures the stages show, each at its served path, every path canonical (no symbolic link anywhere),
and PUBLISH.json beside them: the page's url, the entry file, every served path with its size, the total, and the
paths served by the last build that this one no longer serves (to remove on publish). A lane builds; the lead
publishes the folder exactly as PUBLISH.json lists it.

It refuses to build when a version's web copy is missing or when a version is not at its brief's size in true metres
(every model and the 1.8 m person share one scene, so a model in a generator's own unit would be shown at a false size)."""
import json, shutil, subprocess, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
MAIN = Path(subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()).resolve().parent
RECORDS, WORK = ROOT / "newworld/sources/art", (MAIN / "out/newart").resolve()
SRC, SITE = WORK / "explorer", WORK / "explorer-site"           # SRC: where the making stages put web copies and pictures
URL = json.loads((HERE / "asset_explorer.json").read_text())["url"]


def size_faults(a: dict) -> list:
    """Each version measured against the brief's size rule; a fault names the version and the numbers."""
    rule, out = a.get("size", {}), []
    for v in a["versions"]:
        m = a["measures"].get(v["id"])
        if not m:
            out.append(f"{a['id']}.{v['id']}: no measures (run measure.py on its metres model)"); continue
        x, y, z = m["size_m"]; long, beam = max(x, z), min(x, z)
        if rule.get("rule") == "length":
            ok = abs(long / rule["length_m"] - 1) < 0.03 and abs(beam / rule["beam_m"] - 1) < 0.05; want = f"{rule['length_m']} m long, {rule['beam_m']} m across"
        elif rule.get("rule") == "across":
            ok = abs(long / rule["across_m"] - 1) < 0.06; want = f"about {rule['across_m']} m across"
        elif rule.get("rule") == "height":
            t = rule["weapon_m"] if y > 1.5 else rule["head_m"]; ok = abs(y / t - 1) < 0.03; want = f"{t} m tall"
        else:
            continue
        if not ok:
            out.append(f"{a['id']}.{v['id']}: {x:.2f} x {y:.2f} x {z:.2f} m, the brief says {want}")
    return out


def build() -> dict:
    assets, faults, served = [], [], {}
    for rec in sorted(RECORDS.glob("*.json")):
        a = json.loads(rec.read_text()); m = WORK / a["id"] / "measures.json"
        a["measures"] = json.loads(m.read_text()) if m.exists() else {}
        a["measures"] = {k: {kk: vv for kk, vv in v.items() if kk != "textures"} for k, v in a["measures"].items() if any(x["id"] == k for x in a["versions"])}
        faults += size_faults(a)
        for v in a["versions"]:
            served[f"models/{a['id']}.{v['id']}.gltf.json"] = None
        for s in a["stages"]:
            for f, _ in s.get("images", []):
                served[f"img/{f}"] = None
        assets.append(a)
    faults += [f"{p}: missing from {SRC}" for p in served if not (SRC / p).is_file()]
    if faults:
        raise SystemExit("asset explorer not built:\n  " + "\n  ".join(faults))
    old = json.loads((SITE / "PUBLISH.json").read_text()) if (SITE / "PUBLISH.json").exists() else {"files": {}}
    if SITE.exists():
        shutil.rmtree(SITE)
    cat = {"version": time.strftime("%Y-%m-%dT%H:%M"), "assets": assets}
    (SITE / "data").mkdir(parents=True)
    (SITE / "data/catalog.json").write_text(json.dumps(cat, indent=1).replace("<", "\\u003c"))
    shutil.copyfile(HERE / "asset_explorer_page.html", SITE / "index.html")
    for p in served:
        (SITE / p).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile((SRC / p).resolve(), SITE / p)   # real copies, never links
    files = {p.relative_to(SITE).as_posix(): p.stat().st_size for p in sorted(SITE.rglob("*")) if p.is_file()}
    links = [str(p) for p in SITE.rglob("*") if p.is_symlink()]
    assert not links and SITE.resolve() == SITE, f"links in the site: {links or SITE}"
    pub = {"url": URL, "root": str(SITE), "entry": "index.html", "built": cat["version"], "files": files, "total_bytes": sum(files.values()),
           "removed_since_last_build": sorted(set(old.get("files", {})) - set(files)),
           "how": "Publish index.html with every other path in files at its own path (root = this folder); remove the removed paths. Several publishes to the same url if over 64 MB."}
    (SITE / "PUBLISH.json").write_text(json.dumps(pub, indent=1))
    return pub


if __name__ == "__main__":
    p = build(); print(f"{len(p['files'])} files, {p['total_bytes'] / 1e6:.1f} MB, in {p['root']}; removed since last build: {len(p['removed_since_last_build'])}")

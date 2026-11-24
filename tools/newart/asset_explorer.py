"""Build the asset explorer page's folder: the catalogue from the asset records and each asset's measures, beside the
page. usage: python3 tools/newart/asset_explorer.py   (writes out/newart/explorer/; models and images are put there by
the making stages; publish index.html with the folder's data/, models/ and img/ files)."""
import json, shutil, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RECORDS, WORK, OUT = ROOT / "newworld/sources/art", ROOT / "out/newart", ROOT / "out/newart/explorer"

def build() -> dict:
    assets = []
    for rec in sorted(RECORDS.glob("*.json")):
        a = json.loads(rec.read_text()); m = WORK / a["id"] / "measures.json"
        a["measures"] = json.loads(m.read_text()) if m.exists() else {}
        for mm in a["measures"].values():
            mm.pop("textures", None)
        assets.append(a)
    cat = {"version": time.strftime("%Y-%m-%dT%H:%M"), "assets": assets}
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    (OUT / "data/catalog.json").write_text(json.dumps(cat, indent=1).replace("<", "\\u003c"))
    shutil.copy(Path(__file__).with_name("asset_explorer_page.html"), OUT / "index.html")
    return cat

if __name__ == "__main__":
    c = build(); print(f"{len(c['assets'])} asset(s), version {c['version']}, in {OUT}")

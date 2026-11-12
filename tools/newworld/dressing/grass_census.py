"""Census of every grass (GRAS) the New World load order offers, with its measured colour.

For each GRAS winner in the load order's grass-bearing plugins: its mesh, the mesh's first diffuse texture, the
texture's colour measured on its opaque pixels (alpha cut-out), its density, height range and whether its mesh and
textures resolve as the game resolves them (the assets audit's resolver). The colour family is the flower colour
when one shows: the largest hue family among saturated, non-green pixels that covers at least its FLOWER_MIN of
the opaque pixels (white counts as a family: bright, unsaturated); else the plant is a green (or straw/brown) grass.

    python -m tools.newworld.dressing.grass_census [--json OUT]

Writes newworld/sources/dressing/grass_census.json, a committed source (the input of the ground-colour check);
rerun it when a grass-bearing plugin of the load order changes."""
from __future__ import annotations

import argparse
import colorsys
import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "newworld/sources/dressing/grass_census.json"  # committed: regenerate when the load order's grasses change
# grass-bearing plugins of the New World load order, in load order (last wins)
PLUGINS = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Black Marsh.esm",
           "Black Marsh North.esp", "Valenwood.esp", "King of the Murkmire.esp", "DepthsOfSkyrim.esp",
           "Tropical Skyrim.esp", "FlowerFields.esp"]
# least share of opaque pixels for a flower family: the pale and warm families also tip dry grass, so they need more
FLOWER_MIN = {"yellow": 0.05, "white": 0.05, "orange": 0.05}
FLOWER_MIN_OTHER = 0.012
# hue families, degrees
HUES = [("red", 345, 360), ("red", 0, 15), ("orange", 15, 40), ("yellow", 40, 62), ("green", 62, 170),
        ("cyan", 170, 195), ("blue", 195, 250), ("violet", 250, 290), ("pink", 290, 345)]


def family(rgba: np.ndarray) -> dict:
    """rgba: (n, 4) uint8 pixels. Returns {family, flower_share, mean, shares}."""
    px = rgba[rgba[:, 3] > 127][:, :3].astype(np.float32) / 255.0 if rgba.shape[1] == 4 else rgba[:, :3] / 255.0
    if len(px) == 0:
        return {"family": "none", "flower_share": 0.0, "mean": "#000000", "shares": {}}
    mx, mn = px.max(1), px.min(1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    hsv = np.array([colorsys.rgb_to_hsv(*p)[0] for p in px[:: max(1, len(px) // 20000)]]) * 360
    sub = slice(None, None, max(1, len(px) // 20000))
    ss, vv = s[sub], mx[sub]
    shares: dict[str, float] = {}
    sat = (ss > 0.5) & (vv > 0.45)
    for name, lo, hi in HUES:
        if name == "green":
            continue
        shares[name] = shares.get(name, 0.0) + float(np.mean(sat & (hsv >= lo) & (hsv < hi)))
    shares["white"] = float(np.mean((ss < 0.15) & (vv > 0.8)))
    top = max(shares, key=shares.get)
    mean = px.mean(0)
    base = "green" if 70 <= colorsys.rgb_to_hsv(*mean)[0] * 360 < 170 else "straw"
    flowers = [k for k in shares if shares[k] >= FLOWER_MIN.get(k, FLOWER_MIN_OTHER)]
    top = max(flowers, key=shares.get) if flowers else top
    fam = top if flowers else base
    return {"family": fam, "flower_share": round(shares[top], 4), "mean": "#%02x%02x%02x" % tuple(int(x * 255) for x in mean),
            "shares": {k: round(v, 4) for k, v in shares.items() if v >= 0.005}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", type=Path, default=OUT)
    a = ap.parse_args(argv)
    from tools.argonia_world.esm import Plugin
    from tools.newworld.assets_audit import Audit, active_plugins, norm_asset
    from tools.places.assets.dds import decode
    from tools.places.assets.resolve import DATA, STACK, Resolver
    audit = Audit(Resolver(), active_plugins(STACK / "MO2/profiles/NewWorld"))
    res = audit.R
    plain_read = res.read

    def read(key: str):   # an asset-only mod laid under newworld-assets/<id> and not yet in the stack's install record
        b = plain_read(key)
        if b is None:
            for d in sorted(res.asset_mods.glob("*")) if res.asset_mods.is_dir() else ():
                f = res._find(d, key)
                if f:
                    return f.read_bytes()
        return b
    res.read = read
    win: dict[str, tuple[str, object]] = {}
    for name in PLUGINS:
        if (DATA / name).exists():
            for r in Plugin.read(DATA / name, {"GRAS"}).records("GRAS"):
                win[r.key] = (name, r)
    rows = []
    for key, (src, r) in sorted(win.items()):
        modl = r.zstr("MODL") or ""
        d = r.sub("DATA") or b""
        dens, smin, smax = (d[0], d[1], d[2]) if len(d) >= 3 else (0, 0, 0)
        height = struct.unpack_from("<f", d, 20)[0] if len(d) >= 24 else 0.0
        mesh = norm_asset(modl) if modl else ""
        tex = audit.nif(mesh) if mesh else None
        row = {"key": key, "edid": r.edid, "winner": src, "mesh": mesh, "density": dens, "slope": [smin, smax],
               "height_range": round(height, 3), "mesh_ok": tex is not None, "textures_ok": False, "family": "unknown"}
        if tex is not None:
            keys = [norm_asset(t) for t in tex]
            found = {k: audit.R.read(k) for k in keys}
            row["textures_ok"] = all(v is not None for v in found.values())
            diff = next((k for k in keys if found[k] and not k.endswith(("_n.dds", "_msn.dds", "_s.dds", "_g.dds"))
                         and not k.startswith("textures\\effects\\")), None)
            row["diffuse"] = diff
            if diff:
                try:
                    im = np.asarray(decode(found[diff]).convert("RGBA")).reshape(-1, 4)
                    row.update(family(im))
                except Exception as e:  # noqa: BLE001 - an undecodable texture is reported, not fatal
                    row["family"] = f"undecodable: {type(e).__name__}"
        rows.append(row)
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps({"grasses": rows}, indent=1))
    fams: dict[str, int] = {}
    for x in rows:
        fams[x["family"]] = fams.get(x["family"], 0) + 1
    print(f"grass census: {len(rows)} GRAS; families {fams}; incomplete {sum(not (x['mesh_ok'] and x['textures_ok']) for x in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

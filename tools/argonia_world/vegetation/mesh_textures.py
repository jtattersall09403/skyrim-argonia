"""Every texture a placed mesh names, and where on the player's machine it comes from (lane 1.15-r2-textures).

Round 1's stills showed Skyrim's missing-texture look (white and lavender plants, pale rock masses): a mesh our plugin
places named a texture no laid row supplies. stack.py's `keep` lays a kept mesh's textures only when its archive
holds them (keep_subset), so a texture missing from every source never fails the lay; this module makes it fail at L1.

    python3 -m tools.argonia_world.vegetation textures build --mo2 <MO2/mods> --vanilla <Skyrim Data>
        (machine-local, once per stack change: reads each candidate mesh's BSShaderTextureSet slots from the laid tree
        and the BSAs, lz4 for compressed BSAs, and writes MANIFEST: paths only, never a file's content)
    python3 -m tools.argonia_world.vegetation textures check      (L1: make check's world-data step)

The manifest holds, per non-vanilla object_form mesh, its row and its texture slots, and per texture the row (or
"vanilla") that supplies it, or null. The check fails when a placed form's mesh is not in the manifest, a keep row's
placed mesh is not under a keep glob, or a placed mesh's texture has no source and no keep glob, unless WAIVED names it (a missing
normal or glow map: the surface still shows its diffuse; a missing diffuse is never waived, lists.usable drops it).

MODS (lane 1.15-r3-mods): a base record's alternate texture sets replace a NIF shape's diffuse and normal with a
TXST's TX00/TX01. Round 2's lavender trunks, plants and ruin walls were Black Marsh.esm's TXSTs naming diffuses no
source ships. The manifest's "forms" holds each candidate form's sets (ArgoniaGen `alttex`: object_form, the build
cells' bases, the creature forms through their skins), and the check reads them like a mesh slot. A base in ALT_DROPPED
is resolved: ArgoniaWorld.esm overrides it with MODS dropped (AltTextures.cs), so the NIF's own textures draw; a base
in ALT_UNFIXABLE never is (lists.usable drops it).
"""
from __future__ import annotations

import fnmatch
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data" / "mesh-textures.json"  # beside dependencies.json: the laid stack, not world data
DEPS = ROOT / "data" / "dependencies.json"
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"
DIFFUSE = 0  # BSShaderTextureSet slot 0; 1 normal, 2 glow, 3 parallax, 4 env, 5 env mask, 6 tint, 7 specular
# Missing non-diffuse maps measured 2026-11-02 on the laid stack, absent from every row's archive: the mesh shows its
# diffuse with flat shading. Each entry is a texture path; the check fails on any miss not listed here.
WAIVED = {
    "textures/landscape/trees/bananabark1_n.dds": "BM&V flatpalm1 bark normal",
    "textures/landscape/trees/datepalmbark2_n.dds": "BM&V datepalm2 bark normal",
    "textures/landscape/trees/gkbpalmbark22_n.dds": "BM&V fanpalm1 bark normal",
    "textures/landscape/trees/treeoaktrunk_n.dds": "BM&V gorse bush trunk normal",
    "textures/pc_flora_str_tree_01tr2_n.dds": "BM&V tall mushroom stem normal",
    "textures/tr_ashswp_emppar01_n.dds": "BM&V emperor parasol branch normal",
    "textures/tr_ashswp_emppar02_n.dds": "BM&V emperor parasol branch normal",
    "textures/tr_ashswp_tree_n.dds": "BM&V emperor parasol branch normal",
    "textures/tr_flora_cupling_01_n.dds": "BM&V cupling normal",
    "textures/tr_flora_cupling_02_n.dds": "BM&V cupling normal",
    "textures/vurt_amanita3_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_bluecap01_g.dds": "BM&V Vurt mushroom glow",
    "textures/vurt_mushbottom_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_paragills512_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_parasol1_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_shcap022_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_shroomstem_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_shroomtop_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_shroomystem_n.dds": "BM&V Vurt mushroom normal",
    "textures/vurt_treebark04_n.dds": "BM&V Vurt mushroom normal",
    "textures/nor": "a truncated normal slot string in BM&V's kelp and coral grass and Depths of Skyrim's corals",
    "textures/landscape/trees/tundradriftwoodbranches01_n.ddstextures/": "BM&V gkbjungletreenew1: a broken normal string",
    "textures/landscape/trees/gkbjunglebranch10.dds": "BM&V gkbjungletreenew1: its glow slot (slot 2), not a diffuse",
    "textures/stingingnettel_dif_n.png": "BM&V stinging nettle: a .png normal the engine cannot read",
    "textures/g:/berkians folder/stuff for skyrim/landscaping/rocks/from_online_resource/rock_30_n.dds":
        "BM&V rock_30: an absolute author path; its diffuse is vanilla MountainSlab02",
    "textures/g:/berkians folder/stuff for skyrim/landscaping/rocks/from_online_resource/rock_33_n.dds":
        "BM&V rock_33: an absolute author path; its diffuse is vanilla MountainSlab02",
}

# Placed bases whose MODS names a diffuse no source ships (measured 2026-11-02, lane 1.15-r3-shader §1). ArgoniaWorld.esm
# overrides each with MODS dropped (terrain/world.py -> LandWorld.cs); the NIF's own slots are checked as for any mesh.
ALT_DROPPED = {
    "17BD20:Black Marsh.esm": "01tROPICAL2 (52,372 refs): TXST diffuse landscape/plants/TropicalPlant01.dds",
    "196181:Black Marsh.esm": "01largefern (50,856): ferny.dds; the NIF's ferny3.dds draws",
    "1B32DC:Black Marsh.esm": "01cypressmoss (8,722): vurt_bcmossbark01.dds",
    "0AA5F4:Black Marsh.esm": "01fortFlower (8,216): jgayleidleaftrim.dds, round 2's purple ruin walls",
    "17BCFD:Black Marsh.esm": "01TROPICAL11 (7,323): TropicalShrub05.dds",
    "0D85BB:Black Marsh.esm": "01mushroomDUPLICATE001 (4,629): abark2.dds",
    "1DE971:Black Marsh.esm": "altrstacked01 rock: sheomud01.dds",
    "1DE977:Black Marsh.esm": "altr16 rock: eressea bark0005.dds",
    "1B32D4:Black Marsh.esm": "tr_flora_cupling_04: pc_flora_hyac_petal.dds, abark2.dds",
    "1B32E0:Black Marsh.esm": "cypress5: vurtdeadbark.dds",
    "1B32CE:Black Marsh.esm": "tr_flora_acbranch_04: baobark.dds, pc_flora_blue_cap.dds",
    "1B32E4:Black Marsh.esm": "gkbjungletreenew12v3: EPineBark06Snow.dds",
    "1D3CC3:Black Marsh.esm": "vurt_morromushroom_01: five Vurt/PC diffuses",
    # creature forms: the skin ARMAs are overridden (AltTextures.Write), so the giant snake draws its own body.dds
    "000B76:King of the Murkmire.esp": "giant snake: Mihail's body3/body4.dds, absent (body.dds is laid)",
    "000C1E:King of the Murkmire.esp": "giant snake: body2.dds, absent",
    "000C31:King of the Murkmire.esp": "giant snake: body2.dds, absent",
    "00FF15:King of the Murkmire.esp": "giant snake: body3/body4.dds, absent",
}
# Bases whose lavender is not only MODS, never placed (lists.usable drops them; the check is red if one is placed).
ALT_UNFIXABLE = {
    "17BD15:Black Marsh.esm": "01mossDUPLICATE001: its NIF's shader carries Own_Emit with a cyan emissive (0, 0.73, 1) "
                              "x 1.5, so dropping MODS still draws it blue (lane 1.15-r3-shader §1)",
}


def norm(path: str) -> str:
    """A NIF texture string as the Data path the engine looks up (lower case, '/', under textures/)."""
    t = "".join(c for c in path.lower().replace("\\", "/") if c >= " ").strip()  # some strings carry control bytes
    if "/data/textures/" in t:  # an author's absolute path: the engine reads from after its Data folder
        t = t[t.rfind("/data/textures/") + len("/data/"):]
    return t if t.startswith("textures/") else "textures/" + t.lstrip("/")


def mesh_path(model: str) -> str:
    return "meshes/" + model.lower().replace("\\", "/")


# ---- reading (build only) ------------------------------------------------------------------------------------------
def texture_slots(nif: bytes) -> list[tuple[int, str]]:
    """(slot, path) of every non-empty slot of every BSShaderTextureSet in the mesh."""
    from tools.navmesh.nif import Nif
    n, out = Nif(nif), []
    for i, t in enumerate(n.types):
        if t != "BSShaderTextureSet":
            continue
        blk = nif[n.offsets[i]:n.offsets[i] + n.sizes[i]]
        o = 4
        for slot in range(struct.unpack_from("<I", blk, 0)[0]):
            ln = struct.unpack_from("<I", blk, o)[0]
            s = blk[o + 4:o + 4 + ln].decode("latin-1")
            o += 4 + ln
            if s:
                out.append((slot, s))
    return out


def _bsa(path: Path):
    """(lower path, size, offset) of each file in a v104/v105 BSA, the archive flags."""
    b = path.read_bytes()
    _, ver, off, flags, nf, _, _, tfn, _ = struct.unpack_from("<4sIIIIIIII", b, 0)
    rec = 24 if ver >= 105 else 16
    counts = [struct.unpack_from("<I", b, off + i * rec + 8)[0] for i in range(nf)]
    o, recs = off + nf * rec, []
    for c in counts:
        ln = b[o]
        d = b[o + 1:o + ln].rstrip(b"\0").decode("latin-1")
        o += 1 + ln
        recs += [(d, *struct.unpack_from("<QII", b, o + 16 * j)[1:]) for j in range(c)]
        o += 16 * c
    names = b[o:o + tfn].split(b"\0")
    return b, flags, [((d + "\\" + n.decode("latin-1")).lower().replace("\\", "/"), sz, fo)
                      for (d, sz, fo), n in zip(recs, names)]


def _bsa_file(b: bytes, flags: int, sz: int, fo: int) -> bytes:
    comp = bool(flags & 4) ^ bool(sz & 0x40000000)
    sz &= 0x3FFFFFFF
    if flags & 0x100:  # embedded names
        sz -= 1 + b[fo]
        fo += 1 + b[fo]
    if not comp:
        return b[fo:fo + sz]
    import lz4.frame  # build only: SSE compresses with lz4 frames
    return lz4.frame.decompress(b[fo + 4:fo + sz])


def candidate_forms(w) -> list[str]:
    """Every form a plugin of ours may place: the non-vanilla object_forms, the build cells' bases, the creature forms."""
    ks = {r["form_key"] for r in w.query("SELECT form_key FROM object_form WHERE mesh_source <> 'vanilla'")}
    ks |= {r["base"] for r in w.query("SELECT DISTINCT base FROM build_ref WHERE base IS NOT NULL")}
    ks |= {r["form_key"] for r in w.query("SELECT form_key FROM creature_form")}
    return sorted(k for k in ks if ":" in k)


def alt_scan(keys: list[str], data: Path, gen: Path = GEN, esm: Path | None = None) -> dict:
    """{form: [[shape, diffuse, normal], ...]} from ArgoniaGen `alttex` (the owning plugin's record, or `esm`'s)."""
    import os
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fl, out = Path(d) / "forms.txt", Path(d) / "alt.json"
        fl.write_text("\n".join(keys) + "\n")
        env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"))
        r = subprocess.run([str(gen), "alttex", "--data", str(data), "--forms", str(fl), "--out", str(out),
                            *(["--in", str(esm)] if esm else [])], capture_output=True, text=True, env=env, check=False)
        if r.returncode:
            raise SystemExit(f"textures: alttex failed: {(r.stdout + r.stderr)[-800:]}")
        raw = json.loads(out.read_text())
    return {k: [[s["shape"], norm(s["diffuse"]) if s["diffuse"] else None, norm(s["normal"]) if s["normal"] else None]
                for s in v["sets"]] for k, v in sorted(raw.items())}


def build(mo2: Path, vanilla: Path, out: Path = MANIFEST, gen: Path = GEN) -> dict:
    """Scan the laid stack (MO2 mods, each row's loose files and BSAs; vanilla BSAs) for every candidate mesh."""
    from tools.argonia_world import db
    w = db.open()
    want: dict[str, str] = {}
    for r in w.query("SELECT form_key, model, mod FROM object_form WHERE mesh_source <> 'vanilla' AND model IS NOT NULL"):
        want.setdefault(mesh_path(r["model"]), r["mod"])
    where: dict[str, tuple[str, Path, tuple | None]] = {}  # path -> (row, file or bsa, bsa record)
    for b in sorted(vanilla.glob("*.bsa")):
        for p, sz, fo in _bsa(b)[2]:
            where.setdefault(p, ("vanilla", b, (sz, fo)))
    for m in sorted(x for x in mo2.iterdir() if x.is_dir()):
        for f in sorted(m.rglob("*")):
            if not f.is_file():
                continue
            r = str(f.relative_to(m)).lower().replace("\\", "/")
            if r.endswith(".bsa"):
                for p, sz, fo in _bsa(f)[2]:
                    where[p] = (m.name, f, (sz, fo))
            else:
                where[r] = (m.name, f, None)
    cache: dict[Path, tuple] = {}
    meshes, sources = {}, {}
    for mp, row in sorted(want.items()):
        hit = where.get(mp)
        if hit is None:
            meshes[mp] = {"row": row, "laid": None, "slots": []}
            continue
        src, f, rec = hit
        if rec is None:
            data = f.read_bytes()
        else:
            if f not in cache:
                cache.clear()
                cache[f] = _bsa(f)[:2]
            data = _bsa_file(*cache[f], *rec)
        slots = [(s, norm(t)) for s, t in texture_slots(data)]
        meshes[mp] = {"row": row, "laid": src, "slots": sorted(set(slots))}
        for _, t in slots:
            sources[t] = where[t][0] if t in where else None
    forms = alt_scan(candidate_forms(w), vanilla, gen)
    for f in forms.values():
        for _, d, nm in f:
            for t in (d, nm):
                if t:
                    sources[t] = where[t][0] if t in where else None
    doc = {"about": "texture slots of each non-vanilla object_form mesh, each candidate form's MODS sets, and the row "
                    "that lays each texture (tools/argonia_world/vegetation/mesh_textures.py); paths only",
           "meshes": meshes, "forms": forms, "sources": dict(sorted(sources.items()))}
    out.write_text(json.dumps(doc, indent=0, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


# ---- the L1 check --------------------------------------------------------------------------------------------------
def load(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def incomplete(manifest: dict) -> set[str]:
    """Mesh paths with any slot no row supplies (a normal or glow map included). Owner play test 3, finding 5 ("a neon
    blue green", "washed out and pale"): a missing normal map draws with the engine's fallback, its specular alpha
    full, so leaves glare blue-green and bark goes pale; a missing glow map on a glow-flagged shader lights the shape
    (BM&V gkbjungletreenew1). The region lists place none of them (lists.usable); WAIVED stays for other placers."""
    src = manifest["sources"]
    return {mp for mp, m in manifest["meshes"].items() if any(src.get(t) is None for _, t in m["slots"])}


def untextured(manifest: dict) -> set[str]:
    """Mesh paths with a diffuse no row supplies: drawn as Skyrim's missing texture, so never placed (lists.usable).
    A mesh the stack does not lay (laid null) has no slots read, so it waits until a build has read it (a manifest
    built from a stack that lays it, e.g. after a wider keep), never placed unread."""
    src = manifest["sources"]
    return {mp for mp, m in manifest["meshes"].items()
            if m["laid"] is None or any(s == DIFFUSE and src.get(t) is None for s, t in m["slots"])}


def alt_gaps(manifest: dict, key: str) -> list[tuple[int, str]]:
    """(slot, texture) of a form's MODS sets that no row supplies: a diffuse always, a normal unless WAIVED."""
    src = manifest["sources"]
    return sorted({(s, t) for _, d, nm in manifest.get("forms", {}).get(key, ()) for s, t in ((DIFFUSE, d), (1, nm))
                   if t and src.get(t) is None and (s == DIFFUSE or t not in WAIVED)})


def untextured_forms(manifest: dict) -> set[str]:
    """Forms whose MODS draws a missing diffuse and that ArgoniaWorld.esm does not override (or cannot fix)."""
    return {k for k in manifest.get("forms", {})
            if k in ALT_UNFIXABLE or (k not in ALT_DROPPED and any(s == DIFFUSE for s, _ in alt_gaps(manifest, k)))}


def alt_problems(keys: list[str], manifest: dict, what: str = "") -> list[str]:
    out = []
    for k in keys:
        if k in ALT_UNFIXABLE:
            out.append(f"{k}{what}: placed, but {ALT_UNFIXABLE[k]}")
        elif k not in ALT_DROPPED:
            out += [f"{k}{what}: MODS slot {s} {t} has no source" for s, t in alt_gaps(manifest, k)]
    return out


def problems(placed: list[dict], manifest: dict, deps: dict, waive: bool = True) -> list[str]:
    """placed: object_form rows (model, mod, form_key) of every form the plugin places. waive=False (the region
    lists' flora, lane 1.15-r4-trees): no slot may miss, WAIVED or not."""
    keep = {d["id"]: d["keep"] for d in deps["mods"] if d.get("keep")}
    src, out = manifest["sources"], []

    def kept(t: str) -> bool:  # a keep glob lays it on the next deploy (another row's mesh may name it)
        return any(fnmatch.fnmatch(t, g) for globs in keep.values() for g in globs)
    for f in placed:
        mp = mesh_path(f["model"])
        m = manifest["meshes"].get(mp)
        if m is None:
            out.append(f"{f['form_key']} {mp}: not in the manifest (rebuild it: textures build)")
            continue
        if m["laid"] is None:
            out.append(f"{f['form_key']} {mp}: no row lays the mesh")
        if f["mod"] in keep and not any(fnmatch.fnmatch(mp, g) for g in keep[f["mod"]]):
            out.append(f"{f['form_key']} {mp}: not under {f['mod']}'s keep globs")
        for s, t in m["slots"]:
            if src.get(t) is None and not kept(t) and (s == DIFFUSE or not waive or t not in WAIVED):
                out.append(f"{f['form_key']} {mp}: slot {s} {t} has no source")
        out += alt_problems([f["form_key"]], manifest, f" {mp}")
    return out


def placed_forms(w) -> list[dict]:
    return w.query("SELECT DISTINCT f.form_key, f.model, f.mod FROM land_region_object o JOIN object_form f "
                   "USING (form_key) WHERE f.mesh_source <> 'vanilla' ORDER BY f.form_key")


def other_placed(w) -> dict[str, list[str]]:
    """The non-vegetation forms our plugins place, by what places them: the build cells' bases (Claywater's block)
    and the creature forms."""
    return {"build_ref": sorted({r["base"] for r in w.query("SELECT DISTINCT base FROM build_ref WHERE base IS NOT NULL")
                                 if ":" in r["base"]}),
            "creature": sorted(r["form_key"] for r in w.query("SELECT form_key FROM creature_form"))}


def check() -> int:
    from tools.argonia_world import db
    w = db.open()
    man = load()
    bad = problems(placed_forms(w), man, json.loads(DEPS.read_text(encoding="utf-8")), waive=False)
    for what, keys in other_placed(w).items():
        bad += alt_problems(keys, man, f" ({what})")
    from tools.argonia_world.vegetation import leaf_hue
    hues = leaf_hue.load()
    flora = {r["form_key"] for r in w.query("SELECT form_key FROM object_form WHERE role_id <> 'rock'")}
    bad += leaf_hue.problems([f for f in placed_forms(w) if f["form_key"] in flora], man, hues)
    for r in leaf_hue.vertex_report([f for f in placed_forms(w) if f["form_key"] in flora]):
        print("textures: report (not a red), red vertex colour:", r)
    for b in bad:
        print("textures:", b)
    misses = sorted({t for m in man["meshes"].values() for _, t in m["slots"] if man["sources"].get(t) is None})
    print(f"textures: {len(placed_forms(w))} placed forms, {len(man['meshes'])} meshes in the manifest, "
          f"{len(misses)} textures absent from every row ({sum(t in WAIVED for t in misses)} waived), "
          f"{len(man.get('forms', {}))} forms with MODS ({len(ALT_DROPPED)} overridden without it), "
          f"{len(hues)} diffuses' leaf hue measured, {len(bad)} problems")
    return 1 if bad else 0


def override_problems(read: dict) -> list[str]:
    """read: alt_scan of ALT_DROPPED from the built ArgoniaWorld.esm (its record first, else the owner's): no set may
    remain, so every base (or a creature's skin ARMA) is overridden there without MODS."""
    return [f"{k}: no record read" for k in sorted(ALT_DROPPED) if k not in read] + \
           [f"{k}: {len(read[k])} MODS sets still draw (no override, or MODS kept)" for k in sorted(ALT_DROPPED) if read.get(k)]


def overrides_readback(esm: Path, data: Path) -> int:
    bad = override_problems(alt_scan(sorted(ALT_DROPPED), data, esm=esm))
    for b in bad:
        print("textures overrides:", b)
    print(f"textures overrides: {len(ALT_DROPPED)} bases to override without MODS in {esm.name}, {len(bad)} problems")
    return 1 if bad else 0

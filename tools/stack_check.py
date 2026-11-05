"""Read-only check of the staged MO2 profile (no game run): SKSE DLL verdicts for a runtime,
plugin master order, and cross-mod file overrides.  Run: python3 -I tools/stack_check.py > report.md
"""
import argparse
import pathlib
import struct
import sys
from collections import defaultdict

BASE_MASTERS = ["skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm",
                "ccbgssse001-fish.esm", "ccqdrsse001-survivalmode.esl", "ccbgssse037-curios.esl",
                "ccbgssse025-advdsgs.esm", "_resourcepack.esl"]
RUNTIME = (1, 7, 104)
F_SIG, F_ADDRLIB, F_STRUCT = 1, 2, 4   # versionIndependence bits
FX_NOSTRUCT = 1                        # versionIndependenceEx bit
VERSION_DATA_SIZE = 848


def pack_runtime(major, minor, build):
    return (major << 24) | (minor << 16) | (build << 4)


def unpack_runtime(v):
    return f"{v >> 24}.{(v >> 16) & 255}.{(v >> 4) & 4095}"


def pe_exports(data):
    """Return {name: file_offset} for the export table (RVA mapped through the sections)."""
    if data[:2] != b"MZ":
        raise ValueError("not a PE file")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("no PE signature")
    nsec, = struct.unpack_from("<H", data, pe + 6)
    optsize, = struct.unpack_from("<H", data, pe + 20)
    opt = pe + 24
    magic, = struct.unpack_from("<H", data, opt)
    dd = opt + (112 if magic == 0x20B else 96)
    exp_rva, exp_size = struct.unpack_from("<II", data, dd)
    secs = []
    for i in range(nsec):
        o = opt + optsize + 40 * i
        vsize, va, rsize, raw = struct.unpack_from("<IIII", data, o + 8)
        secs.append((va, max(vsize, rsize), raw))

    def off(rva):
        for va, size, raw in secs:
            if va <= rva < va + size:
                return rva - va + raw
        raise ValueError(f"rva {rva:#x} outside sections")
    if not exp_rva:
        return {}
    e = off(exp_rva)
    nfunc, nnames, afn, anm, aord = struct.unpack_from("<IIIII", data, e + 20)
    names_off, ord_off, fn_off = off(anm), off(aord), off(afn)
    out = {}
    for i in range(nnames):
        nrva, = struct.unpack_from("<I", data, names_off + 4 * i)
        o = off(nrva)
        name = data[o:data.index(b"\0", o)].decode("latin1")
        idx, = struct.unpack_from("<H", data, ord_off + 2 * i)
        frva, = struct.unpack_from("<I", data, fn_off + 4 * idx)
        out[name] = off(frva)
    return out


def cstr(b):
    return b.split(b"\0", 1)[0].decode("latin1")


def parse_version_data(data, o):
    dv, pv = struct.unpack_from("<II", data, o)
    name = cstr(data[o + 8:o + 264])
    author = cstr(data[o + 264:o + 520])
    ex, ind = struct.unpack_from("<II", data, o + 772)
    compat = [c for c in struct.unpack_from("<16I", data, o + 780) if c]
    req, = struct.unpack_from("<I", data, o + 844)
    return dict(dataVersion=dv, pluginVersion=pv, name=name, author=author, ex=ex, ind=ind,
                compatible=compat, seRequired=req)


def judge(info, runtime=RUNTIME):
    """(verdict, reason) under SKSE 2.3.1 loader rules for a post-1.6.629 runtime."""
    rv = pack_runtime(*runtime)
    rs = ".".join(map(str, runtime))
    if info is None:
        return "unknown", "not an SKSE plugin (no SKSEPlugin_Version or _Query export)"
    if info.get("legacy"):
        return "refused", "SKSEPlugin_Query only: Query plugins are refused on AE runtimes"
    if info["dataVersion"] != 1:
        return "unknown", f"dataVersion {info['dataVersion']} not understood"
    if rv in info["compatible"]:
        return "loads", f"lists {rs} in compatibleVersions"
    ind = info["ind"]
    if not ind & (F_SIG | F_ADDRLIB):
        return "refused", f"no address-library/signature flag and {rs} not in compatibleVersions " \
                          f"({', '.join(unpack_runtime(c) for c in info['compatible']) or 'none'})"
    how = "address library" if ind & F_ADDRLIB else "signatures"
    if info["ex"] & FX_NOSTRUCT or ind & F_STRUCT:
        return "loads", f"{how}; struct-safe flag set"
    return "refused", f"{how} but no struct-layout flag and {rs} not in compatibleVersions"


def analyse_dll(path):
    data = pathlib.Path(path).read_bytes()
    try:
        exp = pe_exports(data)
    except (ValueError, struct.error) as e:
        return None, f"bad PE: {e}"
    if "SKSEPlugin_Version" in exp:
        info = parse_version_data(data, exp["SKSEPlugin_Version"])
        return info, ""
    if "SKSEPlugin_Query" in exp:
        return {"legacy": True, "name": "", "author": ""}, ""
    return None, ""


def tes4_masters(path):
    with open(path, "rb") as f:
        head = f.read(24)
        if head[:4] != b"TES4":
            raise ValueError(f"{path}: no TES4 record")
        size, flags = struct.unpack_from("<II", head, 4)
        body = f.read(size)
    if flags & 0x40000:
        import zlib
        body = zlib.decompress(body[4:])
    out, o = [], 0
    while o + 6 <= len(body):
        t = body[o:o + 4]
        n, = struct.unpack_from("<H", body, o + 4)
        if t == b"MAST":
            out.append(cstr(body[o + 6:o + 6 + n]))
        o += 6 + n
    return out


def read_modlist(profile):
    """Mods highest priority first, as MO2 writes them (so the first row wins)."""
    rows = [ln.strip() for ln in (profile / "modlist.txt").read_text().splitlines()]
    return [r[1:] for r in rows if r.startswith("+")]


def read_plugins(profile):
    return [ln.strip().lstrip("*") for ln in (profile / "plugins.txt").read_text().splitlines()
            if ln.strip() and not ln.startswith("#")]


def find_plugin(mods, order, name):
    for m in order:
        for f in (mods / m).iterdir() if (mods / m).is_dir() else []:
            if f.name.lower() == name.lower():
                return f
    return None


def master_check(mods, order, plugins, extra=()):
    """List of (plugin, [issues]); extra = absolute paths loaded after plugins.txt."""
    seen = set(BASE_MASTERS)
    rows = []
    items = [(p, find_plugin(mods, order, p)) for p in plugins] + [(pathlib.Path(p).name, pathlib.Path(p)) for p in extra]
    names = [n.lower() for n, _ in items]
    for n, path in items:
        if path is None or not path.exists():
            rows.append((n, [], ["file not found in any mod"]))
        else:
            masters = tes4_masters(path)
            issues = []
            for m in masters:
                if m.lower() in seen:
                    continue
                issues.append(f"{m} " + ("is later in the load order" if m.lower() in names else "is missing"))
            rows.append((n, masters, issues))
        seen.add(n.lower())
    return rows


def file_conflicts(mods, order):
    """{(winner, loser): [paths]}; order highest priority first, so the first row wins."""
    owner = {}
    pairs = defaultdict(list)
    for m in order:
        root = mods / m
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if not f.is_file() or f.name.lower() == "meta.ini":
                continue
            rel = f.relative_to(root).as_posix()
            key = rel.lower()
            if key in owner:
                pairs[(owner[key], m)].append(rel)
            else:
                owner[key] = m
    return pairs


def report(stack, argonia, runtime=RUNTIME):
    mods, profile = stack / "mods", stack / "profiles" / "Argonia"
    order = read_modlist(profile)
    L = [f"## 1. SKSE DLLs for runtime {'.'.join(map(str, runtime))} (SKSE 2.3.1 loader rules)", ""]
    by_name = defaultdict(list)
    for m in order:
        for d in sorted((mods / m).glob("SKSE/Plugins/*.dll")) if (mods / m).is_dir() else []:
            by_name[d.name.lower()].append((m, d))
    L += ["| DLL | mod (wins) | plugin name / version | verdict | reason |", "|---|---|---|---|---|"]
    refused = []
    for name, lst in sorted(by_name.items()):
        win_mod, win = lst[0]
        info, err = analyse_dll(win)
        v, why = judge(info, runtime) if not err else ("unknown", err)
        if v == "refused":
            refused.append(name)
        nm = (info or {}).get("name") or "-"
        pv = unpack_runtime((info or {}).get("pluginVersion", 0)) if info and not info.get("legacy") else ""
        extra = ""
        if len(lst) > 1:
            losers = []
            for m2, d2 in lst[1:]:
                i2, e2 = analyse_dll(d2)
                v2 = judge(i2, runtime)[0] if not e2 else "unknown"
                losers.append(f"{m2} ({v2})")
            extra = f" Shadows: {', '.join(losers)}."
        L.append(f"| {win.name} | {win_mod} | {nm} {pv} | {v} | {why}.{extra} |")
    L += ["", f"Refused: {', '.join(refused) or 'none'}.", "",
          "## 2. Masters (load order = plugins.txt, then Argonia.esp)", ""]
    rows = master_check(mods, order, read_plugins(profile), [argonia] if argonia and pathlib.Path(argonia).exists() else [])
    bad = [(n, i) for n, _, i in rows if i]
    L.append(f"{len(rows)} plugins checked; {len(bad)} with a problem.")
    for n, i in bad:
        L.append(f"- {n}: {'; '.join(i)}")
    L += ["", "## 3. Files laid by two mods (winner over loser = higher priority over lower)", ""]
    pairs = file_conflicts(mods, order)
    L += ["| winner | loser | files |", "|---|---|---|"]
    for (w, l), paths in sorted(pairs.items()):
        L.append(f"| {w} | {l} | {len(paths)} |")
    L.append("")
    for (w, l), paths in sorted(pairs.items()):
        key = [p for p in paths if p.lower().endswith((".dll", ".esp", ".esm", ".esl", ".hkx"))]
        if key:
            L.append(f"- {w} over {l}: " + ", ".join(key[:12]) + (f" (+{len(key) - 12} more)" if len(key) > 12 else ""))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", default=str(pathlib.Path.home() / ".argonia/stack/MO2"))
    ap.add_argument("--argonia", default=str(pathlib.Path(__file__).resolve().parent.parent / "out/Argonia.esp"))
    a = ap.parse_args(argv)
    sys.stdout.write(report(pathlib.Path(a.stack), a.argonia))


if __name__ == "__main__":
    main()

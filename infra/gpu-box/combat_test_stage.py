#!/usr/bin/env python3
"""Stage the 0.0 combat-test mods (combat-test-mods.json) into one game tree, outside the repo.

  combat_test_stage.py [--mods ~/.argonia/mods] [--out ~/.argonia/combat-test/stage]

Writes a Mod Organizer 2 instance: <out>/MO2/mods/<name>/ (one folder per mod, data-level), its Default
profile (modlist, plugins, load order: later mods in the list win), <out>/root (files beside SkyrimSE.exe:
the SKSE loader, inert unless launched) and <out>/MO2/tools/Pandora. Launching Skyrim from Steam stays vanilla;
launching SKSE through MO2 gives the modded game. FOMOD choices are fixed here, one line each, so the install is
repeatable. This is a throwaway test install (0.0 §d); the real stack is pinned in 0.3.
"""
import argparse
import pathlib
import shutil
import subprocess

HOME = pathlib.Path.home()

# FOMOD choices (folders relative to the archive root, copied into Data in this order).
FOMOD = {
    175129: ["Mandatory", "MCO"],  # DMCO: the MCO variant; we use SkySA for attacks, not MCO or DXP
    72347: ["Interface", "MCM", "Meshes", "Scripts", "SKSE", "Textures", "Nemesis_Engine/mod/colis",
            "Precision.esp"],  # Precision: required files, no compatibility patch
    53000: ["Data/*", "SkyrimSE/SKSE", "ESL/MCMHelper.esp", "Loose/*"],  # MCM Helper: SE, ESL, loose
}
SKSE_ONLY = {32444, 34705, 78159, 82395, 82737, 92109, 191697}


def unpack(archive, dest):
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["7z", "x", "-y", f"-o{dest}", str(archive)], check=True, capture_output=True)
    # Some zips store Windows paths ("Interface\\x.txt") as flat names; turn them into folders.
    for f in sorted(dest.rglob("*"), key=lambda x: -len(x.parts)):
        if "\\" in f.name:
            target = f.parent.joinpath(*[s for s in f.name.split("\\") if s])
            target.parent.mkdir(parents=True, exist_ok=True)
            if f.is_dir():
                shutil.copytree(f, target, dirs_exist_ok=True)
                shutil.rmtree(f)
            else:
                f.rename(target)


def copy_into(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def place(mod, src, data, root, tools):
    if mod == 30379:  # SKSE: loader and DLLs beside the game, its scripts into Data
        (base,) = [d for d in src.iterdir() if d.is_dir()]
        for f in base.iterdir():
            if f.suffix.lower() in (".exe", ".dll"):
                copy_into(f, root / f.name)
        copy_into(base / "Data", data)
    elif mod == 133232:  # Pandora is a tool; its output goes into Data when it runs
        copy_into(src, tools / "Pandora")
    elif mod in SKSE_ONLY:
        copy_into(src / "SKSE", data / "SKSE")
    elif mod in FOMOD:
        for part in FOMOD[mod]:
            if part.endswith("/*"):
                for f in (src / part[:-2]).iterdir():
                    copy_into(f, data / f.name)
            elif part.startswith("SkyrimSE/") or part.startswith("ESL/"):
                p = src / part
                copy_into(p, data / pathlib.Path(*pathlib.Path(part).parts[1:]))
            else:
                p = src / part
                if p.is_dir() and mod == 175129:
                    for f in p.iterdir():
                        copy_into(f, data / f.name)
                else:
                    copy_into(p, data / part)
    elif mod == 31390:
        copy_into(src / "data", data)
    elif mod == 47191:
        copy_into(src / "Elder Souls - Sword SE v2.1" / "Elder Souls - Sword 2.0", data)
    else:
        for f in src.iterdir():
            if f.name.lower() not in ("docs", "fomod"):
                copy_into(f, data / f.name)


def main():
    import json
    p = argparse.ArgumentParser()
    p.add_argument("--mods", default=str(HOME / ".argonia" / "mods"))
    p.add_argument("--out", default=str(HOME / ".argonia" / "combat-test" / "stage"))
    a = p.parse_args()
    spec = json.loads((pathlib.Path(__file__).parent / "combat-test-mods.json").read_text())
    out = pathlib.Path(a.out)
    shutil.rmtree(out, ignore_errors=True)
    mo2, root, work = out / "MO2", out / "root", out / "_unpacked"
    tools = mo2 / "tools"
    names = []
    for m in spec["mods"]:
        (archive,) = pathlib.Path(a.mods).glob(f"{m['mod']}-{m['file']}-*")
        src = work / str(m["mod"])
        unpack(archive, src)
        data = mo2 / "mods" / m["name"]
        data.mkdir(parents=True, exist_ok=True)
        place(m["mod"], src, data, root, tools)
        if m["mod"] not in (30379, 133232) or any(data.iterdir()):
            names.append(m["name"])
        print(f"staged {m['name']}")
    shutil.rmtree(work)
    names.append("Pandora Output")  # filled when Pandora runs; highest priority
    (mo2 / "mods" / "Pandora Output").mkdir(parents=True, exist_ok=True)
    prof = mo2 / "profiles" / "Default"
    prof.mkdir(parents=True)
    # MO2's modlist.txt lists the highest priority first.
    (prof / "modlist.txt").write_text("".join(f"+{n}\r\n" for n in reversed(names)))
    plugins = [f.name for n in names for f in sorted((mo2 / "mods" / n).iterdir())
               if f.suffix.lower() in (".esp", ".esl", ".esm")]
    (prof / "plugins.txt").write_text("".join(f"*{n}\r\n" for n in plugins))
    (prof / "loadorder.txt").write_text("".join(f"{n}\r\n" for n in plugins))
    (mo2 / "portable.txt").write_text("")
    print("plugins:", ", ".join(plugins))

if __name__ == "__main__":
    main()

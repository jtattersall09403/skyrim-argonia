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
import re
import shutil
import subprocess

HOME = pathlib.Path.home()

# FOMOD choices (folders relative to the archive root, copied into Data in this order).
FOMOD = {
    # TK Dodge RE: behaviour patch and INI (the DLL is the addon's), with dodging while sheathed (DS1 rolls with
    # anything in hand), the forward-dodge fix and dodging out of stagger under TDM
    56956: ["TK dodge re v0.55-rc3 DLL/Main/*", "TK dodge re v0.55-rc3 DLL/Sheathed Dodge/*",
            "TK dodge re v0.55-rc3 DLL/Forward dodge movement fix/*",
            "TK dodge re v0.55-rc3 DLL/Allow dodging when stagger - Directional Movement/*"],
    79598: ["Dynamic Dodge/Roll to cancel attack/Dynamic Dodge - TK Dodge RE-0.55-rc3/*"],  # rolls, steps, backstep
    72347: ["Interface", "MCM", "Meshes", "Scripts", "SKSE", "Textures", "Nemesis_Engine/mod/colis",
            "Precision.esp"],  # Precision: required files, no compatibility patch
    53000: ["Data/*", "SkyrimSE/SKSE", "ESL/MCMHelper.esp", "Loose/*"],  # MCM Helper: SE, ESL, loose
}
SKSE_ONLY = {32444, 34705, 78159, 82395, 82737, 92109, 191697}


def unpack(archive, dest):
    dest.mkdir(parents=True, exist_ok=True)
    if archive.suffix.lower() == ".rar":  # RAR5: p7zip cannot decode it
        subprocess.run(["unrar", "x", "-o+", "-inul", str(archive), str(dest) + "/"], check=True, capture_output=True)
    else:
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


# Skyrim's loose-file scan overruns a fixed MAX_PATH buffer on any path of 260+ characters under the game's Data
# folder (0xC0000409 at start-up, even in vanilla). The game's own prefix is 77 characters, so mod paths are capped.
GAME_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data" + "\\"
MAX_PATH = 259


def prune(data):
    """Drop OAR "put your <clip> file here.txt" placeholders (instructions, no function) and fail on long paths."""
    for f in list(data.rglob("*")):
        if f.is_file() and (f.name.lower().startswith("put your ") and f.suffix.lower() == ".txt"
                            or f.suffix.lower() in (".bat", ".pdb")):
            f.unlink()
    for d in sorted((x for x in data.rglob("*") if x.is_dir() and (x.name in ("BEIFEN",) or not x.name.isascii())),
                    key=lambda x: -len(x.parts)):
        shutil.rmtree(d, ignore_errors=True)  # Rim Parry's unused sound backups ("新建文件夹", "BEIFEN")
    for d in sorted((x for x in data.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    too_long = [f for f in data.rglob("*") if f.is_file() and len(GAME_DATA) + len(str(f.relative_to(data))) > MAX_PATH]
    if too_long:
        raise SystemExit(f"paths too long for Skyrim in {data.name}: {too_long[0].relative_to(data)}")


def copy_into(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


DATA_DIRS = {"meshes", "textures", "scripts", "skse", "interface", "sound", "music", "seq", "nemesis_engine",
             "pandora_engine", "mcm", "source", "strings", "video", "lodsettings", "grass", "shadersfx"}


def data_root(src):
    """Descend through single wrapper folders ("Payload Interpretor/", "Modern Stagger Lock/") to the data root."""
    root = src
    while True:
        items = [f for f in root.iterdir() if not f.name.startswith(".")]
        dirs = [f for f in items if f.is_dir()]
        if (len(items) == 1 and dirs and dirs[0].name.lower() not in DATA_DIRS
                and dirs[0].name.lower() != "data"):
            root = dirs[0]
        elif len(items) == 1 and dirs and dirs[0].name.lower() == "data":
            return dirs[0]
        else:
            return root


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
        root = data_root(src)
        for f in root.iterdir():
            if f.name.lower() not in ("docs", "fomod", "meta.ini") and not f.name.upper().startswith(("COPYING", "LICENSE", "CHANGES", "EXCEPTIONS", "README")):
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
        pattern = f"gh-{m['github'].replace('/', '_')}-{m['asset']}" if "github" in m else f"{m['mod']}-{m['file']}-*"
        (archive,) = pathlib.Path(a.mods).glob(pattern)
        key = m.get("mod") or m["github"].replace("/", "_")
        src = work / f"{key}-{m.get('file', 'gh')}"
        unpack(archive, src)
        data = mo2 / "mods" / m["name"]
        data.mkdir(parents=True, exist_ok=True)
        place(m.get("mod"), src, data, root, tools)
        prune(data)
        if m.get("mod") not in (30379, 133232) or any(data.iterdir()):
            names.append(m["name"])
        print(f"staged {m['name']}")
    shutil.rmtree(work)
    names.append("Pandora Output")  # filled when Pandora runs; highest priority
    (mo2 / "mods" / "Pandora Output").mkdir(parents=True, exist_ok=True)
    prof = mo2 / "profiles" / "Default"
    prof.mkdir(parents=True)
    # MO2's modlist.txt lists the highest priority first.
    (prof / "modlist.txt").write_text("".join(f"+{n}\r\n" for n in reversed(names)))
    # Elden Parry's window: Rim Parry needs a start above 0; its author's 0.02-0.2 s (stock, for the feel test).
    inis = [f for n in names for f in (mo2 / "mods" / n).rglob("EldenParry.ini")]
    if inis:
        ini = inis[-1]
        text = ini.read_text(errors="ignore")
        for k, v in (("fParryWindow_Start", "0.02"), ("fParryWindow_End", "0.2")):
            text = re.sub(rf"^{k}\s*=.*$", f"{k} = {v}", text, flags=re.M) if re.search(rf"^{k}\s*=", text, re.M) \
                else text + f"\n{k} = {v}\n"
        ini.write_text(text)
        print("elden parry window set in", ini.relative_to(mo2))
    # TK Dodge on the sprint key (the gamepad's right button, Option on a Mac), as DS1 rolls: a tap rolls, a hold
    # runs (owner, 2026-10-29). Its stock key is LB. The other settings stay stock.
    tomls = [f for n in names for f in (mo2 / "mods" / n).rglob("tk-dodge.toml")]
    if tomls:
        toml = tomls[-1]
        toml.write_text(re.sub(r"^bUseSprintKey\s*=.*$", "bUseSprintKey = true", toml.read_text(), flags=re.M))
        print("tk dodge on the sprint key in", toml.relative_to(mo2))
    plugins = []
    for n in names:  # later mods may ship the same plugin (Rim Parry's CTD fix): list each once, first place
        for f in sorted((mo2 / "mods" / n).iterdir()):
            if f.suffix.lower() in (".esp", ".esl", ".esm") and f.name not in plugins:
                plugins.append(f.name)
    (prof / "plugins.txt").write_text("".join(f"*{n}\r\n" for n in plugins))
    (prof / "loadorder.txt").write_text("".join(f"{n}\r\n" for n in plugins))
    (mo2 / "portable.txt").write_text("")
    print("plugins:", ", ".join(plugins))

if __name__ == "__main__":
    main()

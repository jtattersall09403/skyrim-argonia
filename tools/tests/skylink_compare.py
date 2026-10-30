"""L4, dev only: the rebuilt SkyLink AI (175682, our 1.7.104 build) beside ArgoniaBridge in one launch, the
comparable calls side by side (0.3 §a: SkyLink as a second oracle). Not collected by pytest; run in a game slot:

    python3 -u -m tools.tests.skylink_compare --save argoniariverwood

Lays SkyrimMCPPlugin.dll from MO2\\mods\\SkyLink (dev, rebuilt) into Data\\SKSE\\Plugins, launches to the menu with
our bridge as usual, then for each pair calls ours (timed from the build VM, through the tunnel) and SkyLink's pipe
(skylink.ps1, timed on the machine): ping, player, console, save then load, teleport to a cell. Then the game is
killed, SkyLink's DLL removed and the game relaunched clean. Results go to out/bridge/skylink.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from tools.bridge import REPO, Bridge, BridgeError

OUT = Path("out/bridge")
GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition"
SRC = r"C:\argonia\MO2\mods\SkyLink (dev, rebuilt)\SKSE\Plugins\SkyrimMCPPlugin.dll"
DST = GAME + r"\Data\SKSE\Plugins\SkyrimMCPPlugin.dll"
LOG = r"$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE\SkyrimMCPPlugin.log"


def skylink(b: Bridge, calls: list[dict], timeout_ms: int = 15000) -> list[dict]:
    """SkyLink's pipe, one connection for the list; each answer with its time on the machine."""
    local = OUT / "skylink-calls.json"
    local.write_text(json.dumps(calls))
    subprocess.run([b.machine.run, "put", str(local), "C:/argonia/logs/skylink-calls.json"], check=True,
                   capture_output=True, env=b.machine.env)
    subprocess.run([b.machine.run, "put", str(REPO / "infra/gpu-box/skylink.ps1"), "C:/argonia/infra/skylink.ps1"],
                   check=True, capture_output=True, env=b.machine.env)
    out = b.machine.ps(r"powershell -ExecutionPolicy Bypass -File C:\argonia\infra\skylink.ps1 "
                       rf"-CallsFile C:\argonia\logs\skylink-calls.json -TimeoutMs {timeout_ms}", timeout=120)
    rows = []
    for line in out.splitlines():
        ms, sep, body = line.partition("\t")
        if sep and ms.strip().isdigit():
            try:
                rows.append({"ms": int(ms), "reply": json.loads(body)})
            except json.JSONDecodeError:
                rows.append({"ms": int(ms), "reply": body[:300]})
    if len(rows) != len(calls):
        rows.append({"error": out.strip()[-800:]})
    return rows


def ours(b: Bridge, *args) -> dict:
    t0 = time.monotonic()
    try:
        r, err = b.call(*args), None
    except BridgeError as e:
        r, err = None, str(e)
    return {"ms": round((time.monotonic() - t0) * 1000), "ok": err is None,
            "said": err or json.dumps(r)[:300]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    b = Bridge()
    res: dict = {}
    b.machine.install()
    b.machine.helper("kill", timeout=90)
    b.machine.ps(f"Copy-Item '{SRC}' '{DST}' -Force; (Get-FileHash '{DST}').Hash")
    try:
        t0 = time.monotonic()
        b.launch()
        res["launch_s"] = round(time.monotonic() - t0)
        res["skylink_log_at_menu"] = b.machine.ps(f"Get-Content \"{LOG}\" -Tail 8 -EA SilentlyContinue")[-1500:]
        res["ping"] = {"ours": ours(b, "ping"), "skylink": skylink(b, [{"action": "ping"}])}
        res["load_base"] = ours(b, "load", a.save)
        time.sleep(3)
        res["player"] = {"ours": ours(b, "player"), "skylink": skylink(b, [{"action": "get_player_info"}])}
        res["console"] = {"ours": ours(b, "console", "player.getav", "health"),
                          "skylink": skylink(b, [{"action": "execute_command",
                                                  "params": {"command": "player.getav health"}}])}
        # save then load: SkyLink's save_game only queues the save (no wait); load_most_recent_save loads the newest
        s_ours = ours(b, "save", "compare-ours")
        l_ours = ours(b, "load", "compare-ours")
        time.sleep(3)
        sl = skylink(b, [{"action": "save_game", "params": {"saveName": "compare-skylink"}, "sleep": 4000},
                         {"action": "load_most_recent_save"}])
        time.sleep(12)  # SkyLink's load returns before the load ends
        res["save_load"] = {"ours": {"save": s_ours, "load": l_ours}, "skylink": sl,
                            "skylink_after": ours(b, "player")}
        res["teleport"] = {"ours": ours(b, "teleport", "cell", "QASmoke"),
                           "skylink": skylink(b, [{"action": "teleport", "params": {"cellId": "WhiterunBreezehome"}}])}
        time.sleep(6)
        res["teleport"]["skylink_after"] = ours(b, "player")
        res["skylink_log_end"] = b.machine.ps(f"Get-Content \"{LOG}\" -Tail 12 -EA SilentlyContinue")[-2500:]
    finally:
        b.machine.helper("kill", timeout=90)
        b.machine.ps(f"Remove-Item '{DST}' -Force -EA SilentlyContinue; Test-Path '{DST}'")
        (OUT / "skylink.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res, indent=1)[:6000])
        b.launch()  # back to the menu without SkyLink
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

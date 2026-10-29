#!/usr/bin/env python3
"""Make the owner's Moonlight-Web user the default user, so the page needs no second sign-in (owner, 2026-10-29).

Safe because Moonlight-Web listens on localhost only and is reached only through the Cloudflare Access gate, which
already admits only the owner. Run once after pairing (and after any reset of Moonlight-Web's user store).
"""
import json
import pathlib
import re
import subprocess
import time
import urllib.request

here = pathlib.Path(__file__).resolve().parent
env = dict(re.findall(r"^\s*([A-Z_]+)=(.*)$", (pathlib.Path.home() / ".argonia/secrets.env").read_text(), re.M))
ip = subprocess.run([str(here / "run.sh"), "ip"], capture_output=True, text=True, check=True).stdout.strip()
fwd = subprocess.Popen(["ssh", "-i", str(pathlib.Path.home() / ".argonia/keys/argonia-play"), "-o", "BatchMode=yes",
                        "-N", "-L", "18082:127.0.0.1:8080", f"Administrator@{ip}"])
try:
    time.sleep(3)
    cookie = {}

    def call(method, path, body=None):
        req = urllib.request.Request(f"http://127.0.0.1:18082/api{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **cookie})
        r = urllib.request.urlopen(req, timeout=30)
        if r.headers.get("Set-Cookie"):
            cookie["Cookie"] = r.headers["Set-Cookie"].split(";", 1)[0]
        return r.read()

    call("POST", "/login", {"name": env["STREAM_USER"].strip(), "password": env["STREAM_PASSWORD"].strip()})
    me = json.loads(call("GET", "/user"))
    uid = me.get("id") or me.get("user", {}).get("id")
    call("PUT", "/user/default", {"id": uid})
    print("default user set:", uid)
    cookie.clear()
    try:
        print("without signing in, /api/authenticate:", urllib.request.urlopen("http://127.0.0.1:18082/api/authenticate", timeout=30).status)
    except urllib.error.HTTPError as e:
        print("without signing in, /api/authenticate:", e.code)
finally:
    fwd.terminate()

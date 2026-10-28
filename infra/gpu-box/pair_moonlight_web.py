#!/usr/bin/env python3
"""Pair Moonlight-Web with Sunshine on the game machine (chunk 0.0 §c), through an SSH port-forward.

  pair_moonlight_web.py      creates the Moonlight-Web user (the first login becomes admin), adds the
                             localhost host and pairs it, answering Sunshine's PIN through Sunshine's API.
Credentials come from ~/.argonia/secrets.env (STREAM_USER, STREAM_PASSWORD); nothing is printed.
"""
import base64
import json
import pathlib
import re
import ssl
import subprocess
import time
import urllib.request

here = pathlib.Path(__file__).resolve().parent
env = dict(re.findall(r"^\s*([A-Z_]+)=(.*)$", (pathlib.Path.home() / ".argonia/secrets.env").read_text(), re.M))
user, pw = env["STREAM_USER"].strip(), env["STREAM_PASSWORD"].strip()
ip = subprocess.run([str(here / "run.sh"), "ip"], capture_output=True, text=True, check=True).stdout.strip()
fwd = subprocess.Popen(["ssh", "-i", str(pathlib.Path.home() / ".argonia/keys/argonia-play"), "-o", "BatchMode=yes",
                        "-N", "-L", "18080:127.0.0.1:8080", "-L", "47990:127.0.0.1:47990", f"Administrator@{ip}"])
try:
    time.sleep(3)
    # The session cookie is marked Secure, so it is carried by hand over the plain-HTTP forward.
    web = urllib.request.build_opener()
    cookie = {}

    def call(method, path, body=None):
        req = urllib.request.Request(f"http://127.0.0.1:18080/api{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **cookie})
        r = web.open(req, timeout=60)
        if r.headers.get("Set-Cookie"):
            cookie["Cookie"] = r.headers["Set-Cookie"].split(";", 1)[0]
        return r

    call("POST", "/login", {"name": user, "password": pw}).read()
    hosts = json.loads(call("GET", "/hosts").readline() or b"{}")
    print("hosts before:", json.dumps(hosts)[:300])
    found = re.findall(r'"host_id":\s*(\d+)', json.dumps(hosts))
    host_id = int(found[0]) if found else json.loads(call("POST", "/host", {"address": "localhost"}).read())["host"]["host_id"]
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    auth = base64.b64encode(f"{user}:{pw}".encode()).decode()
    hdr = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    def sunshine(method, body=None):
        req = urllib.request.Request("https://127.0.0.1:47990/api/pin", method=method, headers=hdr,
                                     data=json.dumps(body).encode() if body is not None else None)
        return json.loads(urllib.request.urlopen(req, context=ctx, timeout=30).read())

    for old in sunshine("GET")["pairings"]:  # stale requests from earlier attempts
        sunshine("DELETE", {"pairing_id": old["id"]})
    resp = call("POST", "/pair", {"host_id": host_id})
    first = resp.readline().decode()
    pin = json.loads(first)["Pin"]
    pairing_id = None
    for _ in range(15):  # Sunshine lists the request once Moonlight-Web's pairing reaches it
        pending = sunshine("GET")["pairings"]
        if pending:
            pairing_id = pending[0]["id"]
            break
        time.sleep(1)
    if not pairing_id:
        raise SystemExit("Sunshine shows no pending pairing")
    result = sunshine("POST", {"pairing_id": pairing_id, "pin": pin, "name": "moonlight-web"})
    print("sunshine:", result)
    print("pair result:", resp.read().decode()[:300])
finally:
    fwd.terminate()

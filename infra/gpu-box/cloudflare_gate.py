#!/usr/bin/env python3
"""The sign-in gate for the stream pages (chunk 0.0 §c; owner ruling 2026-10-28): a named Cloudflare tunnel from
the game machine, fronted by Cloudflare Access so only the owner's email gets in (one-time code by email).

  cloudflare_gate.py check       verify the token, the zone and the login methods; change nothing
  cloudflare_gate.py apply       create or update one tunnel per play machine (machines.conf), their hostnames
                                 (play-<label>. ...), DNS and the Access apps (idempotent); tokens to secrets.env as
                                 CLOUDFLARE_TUNNEL_TOKEN_<LABEL>; install one on its machine with `tunnel <machine>`
  cloudflare_gate.py tunnel M    install machine M's own tunnel connector (cloudflared service) over run.sh
  cloudflare_gate.py worker      deploy the play switch (infra/cloudflare/play-switch.js) on play., dcv. and sunshine.
                                 with the machine and its schedules; needs AWS_SWITCH_KEY_ID / AWS_SWITCH_SECRET

Reads CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_DOMAIN and GATE_EMAIL from ~/.argonia/secrets.env and
writes CLOUDFLARE_TUNNEL_TOKEN back there; nothing secret is printed. The machine opens no web port: cloudflared
dials out. WebRTC video still flows directly over UDP 40000-40020, which only accepts streams negotiated through
the gated page.
"""
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

SECRETS = pathlib.Path.home() / ".argonia" / "secrets.env"
TUNNEL = "argonia-play"
# hostname prefix -> (service on the game machine, extra ingress rules before it)
ROUTES = {
    "play": ("http://localhost:8080", [("/argonia-metrics.*", "http://localhost:8091")]),
    "dcv": ("https://localhost:8443", []),
    "sunshine": ("https://localhost:47990", []),   # Sunshine's own page: the PIN for pairing the Moonlight app
}
HOST_RECORD = "host"   # host.<domain>: the machine's public IP for the Moonlight app (DNS only; the Worker keeps it)


def secrets():
    return dict((k, v.strip()) for k, v in re.findall(r"^\s*([A-Z_]+)=(.*)$", SECRETS.read_text(), re.M))


env = secrets()
ACCT, DOMAIN, EMAIL = env["CLOUDFLARE_ACCOUNT_ID"], env["CLOUDFLARE_DOMAIN"], env["GATE_EMAIL"]


def cf(method, path, body=None):
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {env['CLOUDFLARE_API_TOKEN']}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["result"]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path}: {e.code} {e.read().decode()[:400]}")


def zone_id():
    zones = cf("GET", f"/zones?name={DOMAIN}")
    if not zones:
        raise SystemExit(f"zone {DOMAIN} not found for this token")
    return zones[0]["id"]


def check():
    print("token:", cf("GET", "/user/tokens/verify")["status"])
    print("zone:", DOMAIN, "found" if zone_id() else "missing")
    idps = cf("GET", f"/accounts/{ACCT}/access/identity_providers")
    print("login methods:", ", ".join(i["type"] for i in idps) or "none (one-time PIN is the default)")
    org = cf("GET", f"/accounts/{ACCT}/access/organizations")
    print("zero trust team:", org.get("auth_domain"))


def save_secret(key, value):
    text = SECRETS.read_text()
    line = f"{key}={value}"
    text = re.sub(rf"^\s*{key}=.*$", line, text, flags=re.M) if re.search(rf"^\s*{key}=", text, re.M) \
        else text.rstrip("\n") + "\n" + line + "\n"
    SECRETS.write_text(text)


def machines():
    """The play machines from machines.conf: [(machine, label, region)]; the label names its origin host
    (play-<label>.<domain>) and its tunnel token: a label=<x> column, else "paris"."""
    out = []
    for line in (pathlib.Path(__file__).resolve().parent / "machines.conf").read_text().splitlines():
        f = line.split("#")[0].split()
        if f and f[0] != "name":
            out.append((f[0], next((x[6:] for x in f[3:] if x.startswith("label=")), "paris"), f[1]))
    return out


def origin(prefix, label):
    """A play machine's own hostname for a gated page: play-paris.<domain>. Only the Worker on play. uses it."""
    return f"{prefix}-{label}.{DOMAIN}"


def tunnel(zid, name, hosts, rules):
    """Create or update one named tunnel with ROUTES on the given hostnames (rules: every host it answers, each
    served as its prefix's route), CNAMEs to it for hosts ({prefix: host}), and return its connector token."""
    tunnels = cf("GET", f"/accounts/{ACCT}/cfd_tunnel?name={name}&is_deleted=false")
    tid = tunnels[0]["id"] if tunnels else cf("POST", f"/accounts/{ACCT}/cfd_tunnel",
                                               {"name": name, "config_src": "cloudflare"})["id"]
    ingress = []
    for host in rules:
        service, extra = ROUTES[host.split(".")[0].split("-")[0]]
        for path, svc in extra:
            ingress.append({"hostname": host, "path": path, "service": svc})
        rule = {"hostname": host, "service": service}
        if service.startswith("https://localhost"):
            rule["originRequest"] = {"noTLSVerify": True}  # DCV's and Sunshine's self-signed certificates on localhost
        ingress.append(rule)
    ingress.append({"service": "http_status:404"})
    cf("PUT", f"/accounts/{ACCT}/cfd_tunnel/{tid}/configurations", {"config": {"ingress": ingress}})
    for host in hosts.values():
        rec = {"type": "CNAME", "name": host, "content": f"{tid}.cfargotunnel.com", "proxied": True}
        have = cf("GET", f"/zones/{zid}/dns_records?name={host}")
        if have:
            cf("PUT", f"/zones/{zid}/dns_records/{have[0]['id']}", rec)
        else:
            cf("POST", f"/zones/{zid}/dns_records", rec)
    print("tunnel", name, "routes:", ", ".join(rules))
    return cf("GET", f"/accounts/{ACCT}/cfd_tunnel/{tid}/token")


def apply():
    zid = zone_id()
    # play., dcv. and sunshine. are the owner's addresses; the Worker on them forwards each request to the play
    # machine on its own hostnames (play-paris., ...), one tunnel per machine. The shared names keep a CNAME (a Worker
    # route needs a proxied record) to the first machine's tunnel.
    first = None
    for name, label, _ in machines():
        hosts = {p: origin(p, label) for p in ROUTES}
        # the first tunnel also keeps the owner's names: a machine on that connector serves
        # them if the Worker passes a request straight through
        rules = list(hosts.values()) + ([f"{p}.{DOMAIN}" for p in ROUTES] if first is None else [])
        tok = tunnel(zid, name, hosts, rules)
        save_secret(f"CLOUDFLARE_TUNNEL_TOKEN_{label.upper()}", tok)
        first = first or name
    tid = cf("GET", f"/accounts/{ACCT}/cfd_tunnel?name={first}&is_deleted=false")[0]["id"]
    for prefix in ROUTES:
        host = f"{prefix}.{DOMAIN}"
        rec = {"type": "CNAME", "name": host, "content": f"{tid}.cfargotunnel.com", "proxied": True}
        have = cf("GET", f"/zones/{zid}/dns_records?name={host}")
        if have:
            cf("PUT", f"/zones/{zid}/dns_records/{have[0]['id']}", rec)
        else:
            cf("POST", f"/zones/{zid}/dns_records", rec)
    print("dns: the owner's names on", first, "(the Worker forwards them)")

    policies = cf("GET", f"/accounts/{ACCT}/access/policies")
    pol = next((p for p in policies if p["name"] == "argonia-owner"), None)
    body = {"name": "argonia-owner", "decision": "allow", "include": [{"email": {"email": EMAIL}}],
            "session_duration": "720h"}
    pid = cf("PUT", f"/accounts/{ACCT}/access/policies/{pol['id']}", body)["id"] if pol \
        else cf("POST", f"/accounts/{ACCT}/access/policies", body)["id"]
    # The play switch reads each machine's heartbeat (/argonia-metrics/activity) on its schedule and forwards the
    # owner's requests to a machine's own hostnames, with no person signed in there: an Access service token. Its
    # secret is shown once and kept in secrets.env.
    tokens = cf("GET", f"/accounts/{ACCT}/access/service_tokens")
    tok = next((x for x in tokens if x["name"] == "argonia-heartbeat"), None)
    if not tok or "CF_HEARTBEAT_ID" not in secrets():
        if tok:
            cf("DELETE", f"/accounts/{ACCT}/access/service_tokens/{tok['id']}")
        tok = cf("POST", f"/accounts/{ACCT}/access/service_tokens", {"name": "argonia-heartbeat", "duration": "8760h"})
        save_secret("CF_HEARTBEAT_ID", tok["client_id"])
        save_secret("CF_HEARTBEAT_SECRET", tok["client_secret"])
    hb = next((p for p in policies if p["name"] == "argonia-heartbeat"), None)
    body = {"name": "argonia-heartbeat", "decision": "non_identity", "include": [{"service_token": {"token_id": tok["id"]}}]}
    hbid = cf("PUT", f"/accounts/{ACCT}/access/policies/{hb['id']}", body)["id"] if hb \
        else cf("POST", f"/accounts/{ACCT}/access/policies", body)["id"]
    apps = cf("GET", f"/accounts/{ACCT}/access/apps")
    hosts = {f"{p}.{DOMAIN}": p == "play" for p in ROUTES}
    hosts |= {origin(p, label): True for _, label, _ in machines() for p in ROUTES}
    for host, token_ok in hosts.items():
        app = next((a for a in apps if a.get("domain") == host), None)
        allow = [{"id": pid, "precedence": 1}] + ([{"id": hbid, "precedence": 2}] if token_ok else [])
        body = {"name": f"argonia {host.split('.')[0]}", "domain": host, "type": "self_hosted", "session_duration": "720h",
                "policies": allow, "app_launcher_visible": False}
        if app:
            cf("PUT", f"/accounts/{ACCT}/access/apps/{app['id']}", body)
        else:
            cf("POST", f"/accounts/{ACCT}/access/apps", body)
    print("access: only the owner's email signs in, sessions last 30 days; the switch's token reads play. and the machines' names.")


NIGHT_STOP = "0 3 * * *"  # 03:00 UTC: 03:00 UK in winter, 04:00 in summer


def worker():
    import uuid
    src = (pathlib.Path(__file__).resolve().parents[1] / "cloudflare" / "play-switch.js").read_text()
    meta = {"main_module": "play-switch.js", "compatibility_date": "2026-10-01", "bindings": [
        {"type": "secret_text", "name": "AWS_KEY_ID", "text": env["AWS_SWITCH_KEY_ID"]},
        {"type": "secret_text", "name": "AWS_SECRET", "text": env["AWS_SWITCH_SECRET"]},
        {"type": "plain_text", "name": "NIGHT_STOP", "text": NIGHT_STOP},
        {"type": "plain_text", "name": "NAME", "text": machines()[0][0]},
        {"type": "plain_text", "name": "ORIGIN_LABEL", "text": machines()[0][1]},
        {"type": "plain_text", "name": "REGION", "text": machines()[0][2]},
        {"type": "plain_text", "name": "DOMAIN", "text": DOMAIN},
        {"type": "secret_text", "name": "CF_TOKEN", "text": env["CLOUDFLARE_API_TOKEN"]},
        {"type": "plain_text", "name": "CF_ZONE", "text": zone_id()},
        {"type": "plain_text", "name": "HOST_NAME", "text": f"{HOST_RECORD}.{DOMAIN}"},
        {"type": "secret_text", "name": "CF_ACCESS_ID", "text": env["CF_HEARTBEAT_ID"]},
        {"type": "secret_text", "name": "CF_ACCESS_SECRET", "text": env["CF_HEARTBEAT_SECRET"]}]}
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"metadata\"\r\nContent-Type: application/json\r\n\r\n"
            f"{json.dumps(meta)}\r\n--{b}\r\nContent-Disposition: form-data; name=\"play-switch.js\"; "
            f"filename=\"play-switch.js\"\r\nContent-Type: application/javascript+module\r\n\r\n{src}\r\n--{b}--\r\n")
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/workers/scripts/argonia-play-switch",
                                 method="PUT", data=body.encode(),
                                 headers={"Authorization": f"Bearer {env['CLOUDFLARE_API_TOKEN']}",
                                          "Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"worker upload: {e.code} {e.read().decode()[:400]}")
    cf("PUT", f"/accounts/{ACCT}/workers/scripts/argonia-play-switch/schedules",
       [{"cron": "*/10 * * * *"}, {"cron": NIGHT_STOP}])
    zid = zone_id()
    have = {r["pattern"] for r in cf("GET", f"/zones/{zid}/workers/routes")}
    for prefix in ("play", "dcv"):
        pattern = f"{prefix}.{DOMAIN}/*"
        if pattern not in have:
            cf("POST", f"/zones/{zid}/workers/routes", {"pattern": pattern, "script": "argonia-play-switch"})
    print("play switch deployed on", ", ".join(f"{p}.{DOMAIN}" for p in ROUTES), "with schedules every 10 min and", NIGHT_STOP)


def install_tunnel():
    """Machine sys.argv[2]'s connector: cloudflared as a Windows service with its own tunnel's token (one tunnel per
    machine, so two machines up at once never share one). The token goes over SSH, never printed."""
    import subprocess
    name = sys.argv[2]
    label = next(lab for n, lab, _ in machines() if n == name)
    tok = secrets()[f"CLOUDFLARE_TUNNEL_TOKEN_{label.upper()}"]
    ps = ("$c='C:\\argonia\\cloudflared.exe'; "
          "Get-ScheduledTask -EA SilentlyContinue | ? { $_.TaskName -like '*cloudflared*' } | Disable-ScheduledTask | Out-Null; "
          "if (Get-Service cloudflared -EA SilentlyContinue) { Stop-Service cloudflared -Force -EA SilentlyContinue; & $c service uninstall 2>&1 | Out-Null; Start-Sleep 2 }; "
          f"& $c service install {tok} 2>&1 | Out-Null; Set-Service cloudflared -StartupType Automatic; Start-Service cloudflared -EA SilentlyContinue; "
          "(Get-Service cloudflared).Status")
    run = pathlib.Path(__file__).resolve().parent / "run.sh"
    print(name, "cloudflared:", subprocess.check_output([str(run), "--machine", name, "ps", ps], text=True).strip().splitlines()[-1])


if __name__ == "__main__":
    {"check": check, "apply": apply, "worker": worker, "tunnel": install_tunnel}[sys.argv[1] if len(sys.argv) > 1 else "check"]()

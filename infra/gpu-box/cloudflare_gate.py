#!/usr/bin/env python3
"""The sign-in gate for the stream pages (chunk 0.0 §c; owner ruling 2026-10-28): a named Cloudflare tunnel from
the game machine, fronted by Cloudflare Access so only the owner's email gets in (one-time code by email).

  cloudflare_gate.py check       verify the token, the zone and the login methods; change nothing
  cloudflare_gate.py apply       create or update the tunnel, its routes, DNS and the Access apps (idempotent)
  cloudflare_gate.py worker      deploy the play switch (infra/cloudflare/play-switch.js) on play. and dcv., with
                                 its schedules; needs AWS_SWITCH_KEY_ID / AWS_SWITCH_SECRET in secrets.env

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


def apply():
    zid = zone_id()
    tunnels = cf("GET", f"/accounts/{ACCT}/cfd_tunnel?name={TUNNEL}&is_deleted=false")
    tid = tunnels[0]["id"] if tunnels else cf("POST", f"/accounts/{ACCT}/cfd_tunnel",
                                               {"name": TUNNEL, "config_src": "cloudflare"})["id"]
    save_secret("CLOUDFLARE_TUNNEL_TOKEN", cf("GET", f"/accounts/{ACCT}/cfd_tunnel/{tid}/token"))
    ingress = []
    for prefix, (service, extra) in ROUTES.items():
        host = f"{prefix}.{DOMAIN}"
        for path, svc in extra:
            ingress.append({"hostname": host, "path": path, "service": svc})
        rule = {"hostname": host, "service": service}
        if service.startswith("https://localhost"):
            rule["originRequest"] = {"noTLSVerify": True}  # DCV's own self-signed certificate on localhost
        ingress.append(rule)
    ingress.append({"service": "http_status:404"})
    cf("PUT", f"/accounts/{ACCT}/cfd_tunnel/{tid}/configurations", {"config": {"ingress": ingress}})
    print("tunnel", TUNNEL, "routes:", ", ".join(f"{p}.{DOMAIN}" for p in ROUTES))

    for prefix in ROUTES:
        host = f"{prefix}.{DOMAIN}"
        rec = {"type": "CNAME", "name": host, "content": f"{tid}.cfargotunnel.com", "proxied": True}
        have = cf("GET", f"/zones/{zid}/dns_records?name={host}")
        if have:
            cf("PUT", f"/zones/{zid}/dns_records/{have[0]['id']}", rec)
        else:
            cf("POST", f"/zones/{zid}/dns_records", rec)
    print("dns: CNAMEs to the tunnel")

    policies = cf("GET", f"/accounts/{ACCT}/access/policies")
    pol = next((p for p in policies if p["name"] == "argonia-owner"), None)
    body = {"name": "argonia-owner", "decision": "allow", "include": [{"email": {"email": EMAIL}}],
            "session_duration": "720h"}
    pid = cf("PUT", f"/accounts/{ACCT}/access/policies/{pol['id']}", body)["id"] if pol \
        else cf("POST", f"/accounts/{ACCT}/access/policies", body)["id"]
    # The play switch reads the machine's heartbeat (/argonia-metrics/activity) on its schedule, with no person
    # signed in: an Access service token, allowed on play. only. Its secret is shown once and kept in secrets.env.
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
    for prefix in ROUTES:
        host = f"{prefix}.{DOMAIN}"
        app = next((a for a in apps if a.get("domain") == host), None)
        allow = [{"id": pid, "precedence": 1}] + ([{"id": hbid, "precedence": 2}] if prefix == "play" else [])
        body = {"name": f"argonia {prefix}", "domain": host, "type": "self_hosted", "session_duration": "720h",
                "policies": allow, "app_launcher_visible": False}
        if app:
            cf("PUT", f"/accounts/{ACCT}/access/apps/{app['id']}", body)
        else:
            cf("POST", f"/accounts/{ACCT}/access/apps", body)
    print("access: only the owner's email may sign in, sessions last 30 days; the heartbeat token reads play.")


NIGHT_STOP = "0 3 * * *"  # 03:00 UTC: 03:00 UK in winter, 04:00 in summer


def play_region():
    """argonia-play's region from machines.conf (#27)."""
    for line in (pathlib.Path(__file__).resolve().parent / "machines.conf").read_text().splitlines():
        f = line.split()
        if f and f[0] == "argonia-play":
            return f[1]
    return "eu-west-2"


def worker():
    import uuid
    src = (pathlib.Path(__file__).resolve().parents[1] / "cloudflare" / "play-switch.js").read_text()
    meta = {"main_module": "play-switch.js", "compatibility_date": "2026-10-01", "bindings": [
        {"type": "secret_text", "name": "AWS_KEY_ID", "text": env["AWS_SWITCH_KEY_ID"]},
        {"type": "secret_text", "name": "AWS_SECRET", "text": env["AWS_SWITCH_SECRET"]},
        {"type": "plain_text", "name": "NIGHT_STOP", "text": NIGHT_STOP},
        {"type": "plain_text", "name": "REGION", "text": play_region()},
        {"type": "secret_text", "name": "CF_TOKEN", "text": env["CLOUDFLARE_API_TOKEN"]},
        {"type": "plain_text", "name": "CF_ZONE", "text": zone_id()},
        {"type": "plain_text", "name": "HOST_NAME", "text": f"{HOST_RECORD}.{DOMAIN}"},
        {"type": "secret_text", "name": "CF_ACCESS_ID", "text": env["CF_HEARTBEAT_ID"]},
        {"type": "secret_text", "name": "CF_ACCESS_SECRET", "text": env["CF_HEARTBEAT_SECRET"]},
        {"type": "plain_text", "name": "ACTIVITY_URL", "text": f"https://play.{DOMAIN}/argonia-metrics/activity"}]}
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


if __name__ == "__main__":
    {"check": check, "apply": apply, "worker": worker}[sys.argv[1] if len(sys.argv) > 1 else "check"]()

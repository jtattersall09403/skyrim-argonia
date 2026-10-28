#!/usr/bin/env python3
"""The sign-in gate for the stream pages (chunk 0.0 §c; owner ruling 2026-10-28): a named Cloudflare tunnel from
the game machine, fronted by Cloudflare Access so only the owner's email gets in (one-time code by email).

  cloudflare_gate.py check       verify the token, the zone and the login methods; change nothing
  cloudflare_gate.py apply       create or update the tunnel, its routes, DNS and the Access apps (idempotent)

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
}


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
    apps = cf("GET", f"/accounts/{ACCT}/access/apps")
    for prefix in ROUTES:
        host = f"{prefix}.{DOMAIN}"
        app = next((a for a in apps if a.get("domain") == host), None)
        body = {"name": f"argonia {prefix}", "domain": host, "type": "self_hosted", "session_duration": "720h",
                "policies": [{"id": pid, "precedence": 1}], "app_launcher_visible": False}
        if app:
            cf("PUT", f"/accounts/{ACCT}/access/apps/{app['id']}", body)
        else:
            cf("POST", f"/accounts/{ACCT}/access/apps", body)
    print("access: only the owner's email may sign in, sessions last 30 days")


if __name__ == "__main__":
    {"check": check, "apply": apply}[sys.argv[1] if len(sys.argv) > 1 else "check"]()

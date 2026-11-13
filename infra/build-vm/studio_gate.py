#!/usr/bin/env python3
"""The place studio's sign-in gate: a named Cloudflare tunnel from the build VM (argonia-build) to the studio on
localhost:8765, at studio.<domain>, behind Cloudflare Access for the owner's email only. The same shape as the
play machine's gate (infra/gpu-box/cloudflare_gate.py), whose API helper, zone and owner policy it reuses.

  studio_gate.py apply    create or update the tunnel, its route, the DNS record and the Access app (idempotent);
                          the connector token goes to secrets.env as CLOUDFLARE_TUNNEL_TOKEN_STUDIO
  studio_gate.py prove    a stranger gets the Access login; a short-lived service token gets the studio's index
                          page, through the play switch (infra/cloudflare/play-switch.js, which starts the build
                          machine for the owner when it is stopped), and is refused the switch's owner-only status;
                          the token and its policy are deleted again before it returns
  studio_gate.py url      print the studio's address

Nothing secret is printed. The VM opens no port: cloudflared dials out (infra/build-vm/studio-tunnel.service)."""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "gpu-box"))
import cloudflare_gate as gate  # noqa: E402

TUNNEL = "argonia-build"
HOST = f"studio.{gate.DOMAIN}"
SERVICE = "http://localhost:8765"


def owner_policy() -> str:
    pol = next((p for p in gate.cf("GET", f"/accounts/{gate.ACCT}/access/policies") if p["name"] == "argonia-owner"),
               None)
    if pol:
        return pol["id"]
    body = {"name": "argonia-owner", "decision": "allow", "include": [{"email": {"email": gate.EMAIL}}],
            "session_duration": "720h"}
    return gate.cf("POST", f"/accounts/{gate.ACCT}/access/policies", body)["id"]


def app_body(policies: list[dict]) -> dict:
    return {"name": "argonia studio", "domain": HOST, "type": "self_hosted", "session_duration": "720h",
            "policies": policies, "app_launcher_visible": False}


def find_app():
    return next((a for a in gate.cf("GET", f"/accounts/{gate.ACCT}/access/apps") if a.get("domain") == HOST), None)


def apply() -> None:
    zid = gate.zone_id()
    acct = gate.ACCT
    tunnels = gate.cf("GET", f"/accounts/{acct}/cfd_tunnel?name={TUNNEL}&is_deleted=false")
    tid = tunnels[0]["id"] if tunnels else gate.cf("POST", f"/accounts/{acct}/cfd_tunnel",
                                                    {"name": TUNNEL, "config_src": "cloudflare"})["id"]
    ingress = [{"hostname": HOST, "service": SERVICE}, {"service": "http_status:404"}]
    gate.cf("PUT", f"/accounts/{acct}/cfd_tunnel/{tid}/configurations", {"config": {"ingress": ingress}})
    # Access first, so the name never answers ungated
    pid = owner_policy()
    app = find_app()
    body = app_body([{"id": pid, "precedence": 1}])
    if app:
        gate.cf("PUT", f"/accounts/{acct}/access/apps/{app['id']}", body)
    else:
        gate.cf("POST", f"/accounts/{acct}/access/apps", body)
    rec = {"type": "CNAME", "name": HOST, "content": f"{tid}.cfargotunnel.com", "proxied": True}
    have = gate.cf("GET", f"/zones/{zid}/dns_records?name={HOST}")
    if have:
        gate.cf("PUT", f"/zones/{zid}/dns_records/{have[0]['id']}", rec)
    else:
        gate.cf("POST", f"/zones/{zid}/dns_records", rec)
    gate.save_secret("CLOUDFLARE_TUNNEL_TOKEN_STUDIO", gate.cf("GET", f"/accounts/{acct}/cfd_tunnel/{tid}/token"))
    print(f"studio: https://{HOST} -> {TUNNEL} -> {SERVICE}; Access: the owner's email only")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(headers: dict | None = None, path: str = "/"):
    op = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(f"https://{HOST}{path}", headers={"User-Agent": "argonia-studio-gate"} | (headers or {}))
    try:
        with op.open(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read(4096).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(4096).decode(errors="replace")


def prove() -> int:
    code, hdr, _ = fetch()
    loc = hdr.get("Location", "")
    stranger = code in (302, 303) and "cloudflareaccess.com" in loc
    print(f"stranger: HTTP {code} -> {loc.split('?')[0] or '(no redirect)'}: "
          f"{'the Access login' if stranger else 'NOT GATED'}")
    acct = gate.ACCT
    tok = gate.cf("POST", f"/accounts/{acct}/access/service_tokens", {"name": "argonia-studio-prove", "duration": "8760h"})
    pol = gate.cf("POST", f"/accounts/{acct}/access/policies",
                  {"name": "argonia-studio-prove", "decision": "non_identity",
                   "include": [{"service_token": {"token_id": tok["id"]}}]})
    app = find_app()
    ok = switch = refused = False
    try:
        gate.cf("PUT", f"/accounts/{acct}/access/apps/{app['id']}",
                app_body([{"id": owner_policy(), "precedence": 1}, {"id": pol["id"], "precedence": 2}]))
        for _ in range(12):  # a new token and policy take a little while to reach the edge
            code, hdr, body = fetch({"CF-Access-Client-Id": tok["client_id"],
                                     "CF-Access-Client-Secret": tok["client_secret"]})
            ok = code == 200 and "<" in body
            if ok:
                break
            time.sleep(10)
        title = body.split("<title>")[1].split("</title>")[0] if "<title>" in body else body[:60]
        switch = {k.lower(): v for k, v in hdr.items()}.get("x-argonia-switch") == "studio"
        print(f"signed-in (service token): HTTP {code}, page title {title!r}, "
              f"{'through the play switch' if switch else 'NOT through the play switch'}")
        scode, _, sbody = fetch({"CF-Access-Client-Id": tok["client_id"], "CF-Access-Client-Secret": tok["client_secret"]},
                                "/argonia/status")
        refused = scode == 403 and "only the owner" in sbody
        print(f"the switch's status, not the owner: HTTP {scode}: {'refused' if refused else 'NOT REFUSED'}")
    finally:
        gate.cf("PUT", f"/accounts/{acct}/access/apps/{app['id']}", app_body([{"id": owner_policy(), "precedence": 1}]))
        gate.cf("DELETE", f"/accounts/{acct}/access/policies/{pol['id']}")
        gate.cf("DELETE", f"/accounts/{acct}/access/service_tokens/{tok['id']}")
        left = [t for t in gate.cf("GET", f"/accounts/{acct}/access/service_tokens") if t["name"] == "argonia-studio-prove"]
        print("prove token removed" if not left else "WARNING: prove token still present")
    print(json.dumps({"stranger_gets_login": stranger, "token_gets_studio": ok, "through_switch": switch,
                      "switch_refuses_others": refused}))
    return 0 if stranger and ok and switch and refused else 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "url"
    if cmd == "apply":
        apply()
    elif cmd == "prove":
        sys.exit(prove())
    else:
        print(f"https://{HOST}")

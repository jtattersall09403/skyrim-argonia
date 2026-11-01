#!/usr/bin/env python3
"""The standby pool (1.8 §7): the machines with pool=<label> in machines.conf, kept on one build, chosen by spot
placement score by the play page (infra/cloudflare/play-switch.js) and by agents here.

  pool.py status          each standby: state, build, behind main or not, score, who holds it (stream / agent job)
  pool.py pick            print the machine an agent's in-game job should take: a running one nobody streams on and
                          no other job holds, else the stopped one with the best score; never one the owner streams on
                          (job_guard.sh run --gpu, with no machine named, uses it)
  pool.py stamp <machine> tag the build just deployed (deploy.sh, at DEPLOY OK): argonia-build=<the last commit that
                          changed anything but the records (NOT_BUILD)>, and argonia-build-utc=<its commit time> when
                          it is main's history and the tree is clean there, else 0
                          (a lane's build: the play page treats that machine as behind until a pool deploy)
  pool.py behind          print the standbys whose build is not main's HEAD (pool_deploy.sh deploys to them)
"""
import fcntl
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
JOBS = pathlib.Path.home() / ".argonia" / "jobs"
SECRETS = pathlib.Path.home() / ".argonia" / "secrets.env"


def pool():
    out = []
    for line in (HERE / "machines.conf").read_text().splitlines():
        f = line.split("#")[0].split()
        lab = next((x[5:] for x in f[3:] if x.startswith("pool=")), None)
        if f and lab:
            out.append({"name": f[0], "label": lab, "region": f[1]})
    return out


def aws(region, *args):
    return json.loads(subprocess.check_output(["aws", "ec2", "--region", region, "--output", "json", *args], text=True))


def describe(m):
    r = aws(m["region"], "describe-instances", "--filters", f"Name=tag:Name,Values={m['name']}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped")
    i = r["Reservations"][0]["Instances"][0]
    tags = {t["Key"]: t["Value"] for t in i.get("Tags", [])}
    zone = i["Placement"]["AvailabilityZone"]
    return {**m, "id": i["InstanceId"], "state": i["State"]["Name"], "type": i["InstanceType"], "zone": zone,
            "build": tags.get("argonia-build"), "build_utc": tags.get("argonia-build-utc")}


def score(m):
    try:
        r = aws(m["region"], "get-spot-placement-scores", "--instance-types", m["type"], "--target-capacity", "1",
                "--region-names", m["region"], "--single-availability-zone")
        zid = aws(m["region"], "describe-availability-zones", "--zone-names", m["zone"])["AvailabilityZones"][0]["ZoneId"]
        s = [x["Score"] for x in r["SpotPlacementScores"] if x["AvailabilityZoneId"] == zid]
        return s[0] if s else max((x["Score"] for x in r["SpotPlacementScores"]), default=None)
    except subprocess.CalledProcessError:
        return None


def beat(m):
    """The machine's heartbeat through its own tunnel hostname (None if off or silent)."""
    env = dict(re.findall(r"^\s*([A-Z_]+)=(.*)$", SECRETS.read_text(), re.M))
    req = urllib.request.Request(f"https://play-{m['label']}.{env['CLOUDFLARE_DOMAIN'].strip()}/argonia-metrics/activity",
                                 headers={"User-Agent": "argonia-pool", "CF-Access-Client-Id": env["CF_HEARTBEAT_ID"].strip(),
                                          "CF-Access-Client-Secret": env["CF_HEARTBEAT_SECRET"].strip()})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except Exception:
        return None


def fresh(b):
    """A beat from the last 12 minutes (idle-stop writes one every 5); an older one says nothing about now."""
    import datetime
    try:
        t = datetime.datetime.fromisoformat(b["utc"].replace("Z", "+00:00")[:26] + "+00:00" if "." in b["utc"] else b["utc"].replace("Z", "+00:00"))
    except (TypeError, KeyError, ValueError):
        return False
    return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() < 720


def streamed(b):
    return bool(b) and fresh(b) and any(w.startswith("stream") for w in b.get("why", []))


def locked(name):
    """Does a job hold this machine's job_guard lock now?"""
    f = JOBS / ("gpu.lock" if name == "argonia-play" else f"gpu-{name}.lock")
    if not f.exists():
        return False
    with open(f) as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(h, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


# What a deploy carries: everything but the records, the agents' tooling and journeys, and the pool's and gate's own
# files. A commit only there leaves every standby current.
NOT_BUILD = [":!docs", ":!*.md", ":!.claude", ":!tooling", ":!tests/journeys", ":!Makefile", ":!infra/cloudflare",
             ":!infra/build-vm", ":!infra/stream-client", ":!infra/gpu-box/pool.py", ":!infra/gpu-box/pool_deploy.sh",
             ":!infra/gpu-box/machines.conf", ":!infra/gpu-box/cloudflare_gate.py", ":!infra/gpu-box/setup.ps1"]


def build_of(rev):
    """The last commit at or before rev that changed what a deploy carries: two deploys of the same code match."""
    return subprocess.check_output(["git", "-C", str(REPO), "log", "-1", "--format=%h", "--abbrev=12", rev, "--", ".",
                                    *NOT_BUILD], text=True).strip()


def main_head():
    # origin's main: a worktree's local main (or a main tree with another session's edits) lags it
    subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin", "main"], capture_output=True)
    return build_of("origin/main")


def status():
    head = main_head()
    for m in map(describe, pool()):
        b = beat(m) if m["state"] == "running" else None
        held = ", ".join(b.get("why", [])) if b else ""
        print(f"{m['name']:16} {m['label']:8} {m['state']:9} build {m['build'] or '-':12} "
              f"{'current' if m['build'] == head else 'BEHIND main ' + head}  score {score(m)}"
              f"{'  job lock held' if locked(m['name']) else ''}{'  (' + held + ')' if held else ''}")


def pick():
    ms = list(map(describe, pool()))
    free = []
    for m in ms:
        if m["state"] in ("running", "pending"):
            b = beat(m) if m["state"] == "running" else None
            if not streamed(b) and not locked(m["name"]):
                free.append((0, 0, m))     # warm and free: no boot to wait for
        elif m["state"] == "stopped" and not locked(m["name"]):   # a queued job's machine is not free either
            free.append((1, -(score(m) or 0), m))
    if not free:   # every standby busy: queue behind the job that will finish first is unknowable; take the best score
        free = [(2, -(score(m) or 0), m) for m in ms if not streamed(beat(m) if m["state"] == "running" else None)]
    if not free:
        sys.exit("pool: every standby is streamed on or busy with another job")
    print(sorted(free, key=lambda x: (x[0], x[1]))[0][2]["name"])


def stamp(name):
    m = next(x for x in pool() if x["name"] == name) if any(x["name"] == name for x in pool()) else None
    if not m:
        return   # not a standby: nothing to keep in step
    git = lambda *a: subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
    sha = build_of("HEAD")
    clean = not git("status", "--porcelain", "--untracked-files=no", "--", ".", *NOT_BUILD).stdout.strip()
    on_main = git("merge-base", "--is-ancestor", "HEAD", "origin/main").returncode == 0
    utc = git("show", "-s", "--format=%cI", sha).stdout.strip() if clean and on_main else "0"
    if utc != "0":
        utc = subprocess.check_output(["date", "-u", "-d", utc, "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip()
    i = describe(m)["id"]
    subprocess.check_call(["aws", "ec2", "create-tags", "--region", m["region"], "--resources", i, "--tags",
                           f"Key=argonia-build,Value={sha}{'' if clean else '+dirty'}", f"Key=argonia-build-utc,Value={utc}"])
    print(f"pool: {name} has build {sha}{'' if clean else '+dirty'} ({'main' if utc != '0' else 'not main: behind'})")


def behind():
    head = main_head()
    for m in map(describe, pool()):
        if m["build"] != head:
            print(m["name"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "status":
        status()
    elif cmd == "pick":
        pick()
    elif cmd == "stamp" and len(sys.argv) > 2:
        stamp(sys.argv[2])
    elif cmd == "behind":
        behind()
    else:
        print(__doc__)
        sys.exit(2)

#!/usr/bin/env python3
"""The owner inbox: one GitHub issue per owner check or owner call (chunk 0.0 §a).

Agents post through this tool only, and it posts through the `inbox` workflow, so every post comes from
github-actions[bot] and GitHub notifies the owner (it never notifies anyone of their own actions, and the build VM's
`gh` is signed in as the owner). Every agent post carries AGENT_MARK; the wake workflow and the readers here skip
marked text, so only the owner's own words count. Status lives in the repo, not in issues.

Issues the owner opens follow one cycle (CLAUDE.md): acknowledge with how it will be actioned (--ack), then comment
what was done and close (--done). --pending lists owner issues not yet acknowledged.

  owner_inbox.py --setup                                  labels and part milestones (idempotent)
  owner_inbox.py --post check|call --title T --body-file F [--part 0]
  owner_inbox.py --comment N --body-file F
  owner_inbox.py --ack N --body-file F                    "Acknowledged" + how it will be actioned
  owner_inbox.py --done N --commit SHA [--body-file F]    what was done, then close
  owner_inbox.py --close N --commit SHA                   close an agent check or call once its answer is recorded
  owner_inbox.py --unread [--peek]                        owner comments and issues since the last read
  owner_inbox.py --pending                                owner-opened issues with no acknowledgement yet
  owner_inbox.py --new-since 2026-10-28T18:00:00Z [--quiet]   exit 0 if the owner wrote since then, else 1
  owner_inbox.py --hook                                   for the PostToolUse hook: at most every 4 minutes, tell the
                                                          working agent about unread owner items and missing acks
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time
import uuid

REPO = "jtattersall09403/skyrim-argonia"
OWNER = "jtattersall09403"
AGENT_MARK = "<!-- argonia-agent"
ACK_MARK = "<!-- argonia-ack -->"
LABELS = {
    "owner-check": ("0e8a16", "Owner check: play something"),
    "owner-call": ("d93f0b", "Owner call: decide something"),
}
PARTS = {
    "0": "Part 0: Foundation",
    "1": "Part 1: The core loop",
    "2": "Part 2: The slice",
    "3": "Part 3: The game shell",
    "4": "Part 4: Build out sideways",
}
READ_MARK = pathlib.Path.home() / ".argonia" / "state" / "inbox-read"


def gh(*args, data=None):
    out = subprocess.run(["gh", *args], input=data, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:3])} failed: {out.stderr.strip()}")
    return out.stdout


def api(path, method="GET", fields=None, paginate=False):
    args = ["api", path, "-X", method]
    if paginate:
        args.append("--paginate")
    if fields is None:
        return json.loads(gh(*args) or "null")
    return json.loads(gh(*args, "--input", "-", data=json.dumps(fields)) or "null")


def setup():
    have = {lab["name"] for lab in api(f"repos/{REPO}/labels?per_page=100")}
    for name, (colour, desc) in LABELS.items():
        if name not in have:
            api(f"repos/{REPO}/labels", "POST", {"name": name, "color": colour, "description": desc})
    have = {m["title"] for m in api(f"repos/{REPO}/milestones?state=all&per_page=100")}
    for title in PARTS.values():
        if title not in have:
            api(f"repos/{REPO}/milestones", "POST", {"title": title})
    print("labels and milestones ready")


def dispatch(op, find, **inputs):
    """Run the inbox workflow (posts as github-actions[bot]) and wait for the item carrying our nonce."""
    nonce = uuid.uuid4().hex[:12]
    fields = {"ref": "main", "inputs": {"op": op, "nonce": nonce, **{k: str(v) for k, v in inputs.items() if v}}}
    api(f"repos/{REPO}/actions/workflows/inbox.yml/dispatches", "POST", fields)
    for _ in range(45):  # the run takes 15-40 s
        time.sleep(3)
        url = find(nonce)
        if url:
            return url
    raise SystemExit(f"inbox workflow did not post within 135 s (nonce {nonce}); see the inbox workflow runs")


def post(kind, title, body, part):
    def find(nonce):
        for i in api(f"repos/{REPO}/issues?state=all&sort=created&direction=desc&per_page=10"):
            if nonce in (i.get("body") or ""):
                return i["html_url"]
    print(dispatch("post", find, title=title, label=f"owner-{kind}", milestone=PARTS[part], body=body))


def comment(number, body, op="comment"):
    def find(nonce):
        for c in api(f"repos/{REPO}/issues/{number}/comments?per_page=100"):
            if nonce in (c.get("body") or ""):
                return c["html_url"]
    print(dispatch(op, find, number=number, body=body))


def owner_items(since):
    """The owner's own comments and opened issues (not agent posts), oldest first."""
    found = []
    for c in api(f"repos/{REPO}/issues/comments?since={since}&per_page=100", paginate=True):
        if c["user"]["login"] != OWNER or AGENT_MARK in (c["body"] or "") or c["created_at"] <= since:
            continue
        number = int(c["issue_url"].rsplit("/", 1)[1])
        issue = api(f"repos/{REPO}/issues/{number}")
        if any(lab["name"] in LABELS for lab in issue["labels"]) or issue["user"]["login"] == OWNER:
            found.append((c["created_at"], number, issue["title"], c["body"], c["html_url"], "comment"))
    for i in api(f"repos/{REPO}/issues?state=all&since={since}&per_page=100", paginate=True):
        if ("pull_request" not in i and i["user"]["login"] == OWNER and i["created_at"] > since
                and AGENT_MARK not in (i.get("body") or "")):
            found.append((i["created_at"], i["number"], i["title"], i.get("body") or "", i["html_url"], "new issue"))
    return sorted(found)


def unread(peek):
    since = READ_MARK.read_text().strip() if READ_MARK.exists() else "2026-10-01T00:00:00Z"
    found = owner_items(since)
    for at, number, title, body, url, kind in found:
        print(f"--- {kind} #{number} {title} ({at}) {url}\n{body}\n")
    if not found:
        print(f"nothing from the owner since {since}")
    elif not peek:
        READ_MARK.parent.mkdir(parents=True, exist_ok=True)
        READ_MARK.write_text(found[-1][0] + "\n")
    p = pending()
    if p:
        print("NOT YET ACKNOWLEDGED (run --ack):", ", ".join(f"#{n} {t}" for n, t in p))


def pending():
    """Open issues the owner opened that carry no agent acknowledgement."""
    out = []
    for i in api(f"repos/{REPO}/issues?state=open&creator={OWNER}&per_page=100", paginate=True):
        if "pull_request" in i or AGENT_MARK in (i.get("body") or ""):
            continue
        comments = api(f"repos/{REPO}/issues/{i['number']}/comments?per_page=100")
        if not any(ACK_MARK in (c.get("body") or "") for c in comments):
            out.append((i["number"], i["title"]))
    return out


def hook():
    """Claude Code PostToolUse hook: remind the working agent of the owner's new words (throttled, never fails)."""
    stamp = READ_MARK.parent / "inbox-hook-checked"
    try:
        if stamp.exists() and time.time() - stamp.stat().st_mtime < 60:
            return
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        since = READ_MARK.read_text().strip() if READ_MARK.exists() else "2026-10-01T00:00:00Z"
        items, waiting = owner_items(since), pending()
    except (SystemExit, Exception):
        return
    if not (items or waiting):
        return
    lines = [f"{kind} on #{n} {title}: {url}" for _, n, title, _, url, kind in items]
    lines += [f"#{n} {title} has no acknowledgement yet" for n, title in waiting]
    note = ("The owner has written in the inbox. Before continuing, run `python3 tooling/owner_inbox.py --unread`, "
            "read every item, acknowledge each owner-opened issue now with `--ack N` (a short description of how it "
            "will be actioned), and later post what was done and close it with `--done N --commit SHA`.\n- "
            + "\n- ".join(lines))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--setup", action="store_true")
    g.add_argument("--post", choices=["check", "call"])
    g.add_argument("--comment", type=int)
    g.add_argument("--ack", type=int)
    g.add_argument("--done", type=int)
    g.add_argument("--close", type=int)
    g.add_argument("--unread", action="store_true")
    g.add_argument("--pending", action="store_true")
    g.add_argument("--new-since")
    g.add_argument("--hook", action="store_true")
    p.add_argument("--title")
    p.add_argument("--body-file")
    p.add_argument("--part", default="0", choices=PARTS)
    p.add_argument("--commit")
    p.add_argument("--peek", action="store_true", help="with --unread: do not mark as read")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()
    body = pathlib.Path(a.body_file).read_text().rstrip() if a.body_file else ""
    if a.hook:
        hook()
    elif a.setup:
        setup()
    elif a.post:
        if not (a.title and body):
            p.error("--post needs --title and --body-file")
        post(a.post, a.title, body, a.part)
    elif a.comment:
        comment(a.comment, body)
    elif a.ack:
        if not body:
            p.error("--ack needs --body-file: a short description of how it will be actioned")
        comment(a.ack, f"**Acknowledged.** {body}\n\n{ACK_MARK}")
    elif a.done or a.close:
        if not a.commit:
            p.error("--done and --close need --commit")
        n = a.done or a.close
        text = f"**Done** in {a.commit}. {body}" if a.done else f"Answer recorded in {a.commit}. Closing."
        comment(n, text, op="close")
    elif a.unread:
        unread(a.peek)
    elif a.pending:
        for n, t in pending():
            print(f"#{n} {t}")
    elif a.new_since:
        found = owner_items(a.new_since)
        if not a.quiet:
            for at, number, title, _, url, kind in found:
                print(f"{kind} #{number} {title} {at} {url}")
        sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()

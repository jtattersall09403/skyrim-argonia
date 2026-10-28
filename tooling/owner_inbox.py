#!/usr/bin/env python3
"""The owner inbox: one GitHub issue per owner check or owner call (chunk 0.0 §a).

Agents post through this tool only. Every agent post carries AGENT_MARK, because the build VM's `gh` is signed in
as the owner's account: the wake workflow and the readers here skip marked comments, so only the owner's own words
count as replies. Status lives in the repo, not in issues.

  owner_inbox.py --setup                                  labels and part milestones (idempotent)
  owner_inbox.py --post check|call --title T --body-file F [--part 0]
  owner_inbox.py --comment N --body-file F
  owner_inbox.py --unread [--peek]                        owner comments since the last read (then marks them read)
  owner_inbox.py --new-since 2026-10-28T18:00:00Z [--quiet]   exit 0 if the owner commented since then, else 1
  owner_inbox.py --close N --commit SHA                   close with a link to the commit that records the answer
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

REPO = "jtattersall09403/skyrim-argonia"
OWNER = "jtattersall09403"
AGENT_MARK = "<!-- argonia-agent -->"
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


def milestone_number(part):
    for m in api(f"repos/{REPO}/milestones?state=all&per_page=100"):
        if m["title"] == PARTS[part]:
            return m["number"]
    raise SystemExit(f"no milestone for part {part}: run --setup")


def post(kind, title, body, part):
    issue = api(f"repos/{REPO}/issues", "POST", {
        "title": title,
        "body": f"{body.rstrip()}\n\n{AGENT_MARK}\n",
        "labels": [f"owner-{kind}"],
        "assignees": [OWNER],
        "milestone": milestone_number(part),
    })
    print(issue["html_url"])


def comment(number, body):
    c = api(f"repos/{REPO}/issues/{number}/comments", "POST", {"body": f"{body.rstrip()}\n\n{AGENT_MARK}\n"})
    print(c["html_url"])


def owner_comments(since):
    """Owner comments (not agent posts) on owner-labelled issues, oldest first."""
    found = []
    for c in api(f"repos/{REPO}/issues/comments?since={since}&per_page=100", paginate=True):
        if c["user"]["login"] != OWNER or AGENT_MARK in (c["body"] or "") or c["created_at"] <= since:
            continue
        number = int(c["issue_url"].rsplit("/", 1)[1])
        issue = api(f"repos/{REPO}/issues/{number}")
        if any(lab["name"] in LABELS for lab in issue["labels"]):
            found.append((c["created_at"], number, issue["title"], c["body"], c["html_url"]))
    return sorted(found)


def unread(peek):
    since = READ_MARK.read_text().strip() if READ_MARK.exists() else "2026-10-01T00:00:00Z"
    found = owner_comments(since)
    for at, number, title, body, url in found:
        print(f"--- #{number} {title} ({at}) {url}\n{body}\n")
    if not found:
        print(f"no owner comments since {since}")
    elif not peek:
        READ_MARK.parent.mkdir(parents=True, exist_ok=True)
        READ_MARK.write_text(found[-1][0] + "\n")


def close(number, commit):
    comment(number, f"Answer recorded in {commit}. Closing.")
    api(f"repos/{REPO}/issues/{number}", "PATCH", {"state": "closed"})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--setup", action="store_true")
    g.add_argument("--post", choices=["check", "call"])
    g.add_argument("--comment", type=int)
    g.add_argument("--unread", action="store_true")
    g.add_argument("--new-since")
    g.add_argument("--close", type=int)
    p.add_argument("--title")
    p.add_argument("--body-file")
    p.add_argument("--part", default="0", choices=PARTS)
    p.add_argument("--commit")
    p.add_argument("--peek", action="store_true", help="with --unread: do not mark as read")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()
    body = pathlib.Path(a.body_file).read_text() if a.body_file else ""
    if a.setup:
        setup()
    elif a.post:
        if not (a.title and body):
            p.error("--post needs --title and --body-file")
        post(a.post, a.title, body, a.part)
    elif a.comment:
        comment(a.comment, body)
    elif a.unread:
        unread(a.peek)
    elif a.new_since:
        found = owner_comments(a.new_since)
        if not a.quiet:
            for at, number, title, _, url in found:
                print(f"#{number} {title} {at} {url}")
        sys.exit(0 if found else 1)
    elif a.close:
        if not a.commit:
            p.error("--close needs --commit")
        close(a.close, a.commit)


if __name__ == "__main__":
    os.environ.setdefault("GH_REPO", REPO)
    main()

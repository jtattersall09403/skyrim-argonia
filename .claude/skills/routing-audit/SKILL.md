---
name: routing-audit
description: Audit a part folder's chunk briefs the way a fresh agent would read them. Checks that every Read-first route resolves, that Starting state matches the tree, and reports contradictions and stale claims before building. Run at each part start and over the routed set at a part close.
---

# Routing audit

`make check` catches the mechanical part (links, the decisions index). This is the judgement part: a router row
pointing at a retired system, a deleted script still recommended, one list counted two ways, a dead chunk id, a
brief written as if the codebase were a blank slate.

## Modes
- **Part start** (the first chunk's delivering agent; ten minutes): steps 3 and 5 only. List mismatches before
  building, then rewrite that brief's Starting state in place, under twenty lines.
- **Part close** (a fresh `research` agent): all steps over every brief in the part folder
  (`docs/phases/<n>-<part>/`).

## Steps
1. **Walk the route literally.** CLAUDE.md "Session start", PROGRESS, the schedule (`docs/phases/README.md`),
   the part README, the chunk brief, then every file its Read-first names. Collect every path first and resolve
   them in one batch (`ls`, one `git log -3 --name-only -- <paths>`); list what exists, what is missing, what the
   brief asks to build that already exists. Past about 60k tokens of route, name the items that carry nothing.
2. **Belief set.** Number every rule, number, target and prohibition the route makes a fresh agent hold, each
   with file and section.
3. **Starting state against the tree.** What exists, what is red, what the brief assumes but is missing.
4. **Contradictions.** Two passages disagreeing on a rule, number, path or chunk id; superseded decisions cited
   as live; drifted copies. Quote both with file and section, say which wins (decisions over briefs, CLAUDE.md
   over all, supersession banners) and what an agent would get wrong. Also list decisions newer than the brief.
5. **Skills and agents.** For each `.claude/skills/*` and `.claude/agents/*`, check every path, command and
   decision it names still exists and says what it relies on. Report skill · pointer · what changed; do not
   rewrite it during the audit.
6. **Report the whole set, then fix once**, ranked by how badly it would mislead, with a rewrites list per file
   naming the passage that wins. A closing agent rewrites the next brief's Starting state.

Output: route · belief set · Starting state (verified) · contradictions ranked · stale pointers · rewrites.
Terse, evidence first.

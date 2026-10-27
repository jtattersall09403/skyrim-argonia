# P10: Release and the owner's permanent setup

**Goal.** Anyone who owns Skyrim SE can install and play Argonia from a public release that contains only our
files, with the dependency list fetched from its sources; and the owner has a durable, cheap way to play.

**Starting state.** P8 passed; P9 at M1 (early access) or M2 (full release).

**Read first.** Decisions 0002, 0003, 0006 §7, 0012; [legal-and-sourcing.md](../legal-and-sourcing.md);
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md) §4.

## Work packages

### WP10.1 Release artifacts
- CI builds `Argonia.esm`, our BSAs (our files only), our DLLs (release configuration: ArgoniaBridge excluded),
  PrismaUI views, the fonts (Pelagiad with its OFL licence), the installer; `no_assets.py` checks the release
  file list; artifacts attached to a GitHub release with checksums.
- **Acceptance:** the release contains no file outside the allowlist; a fresh Windows install and a fresh
  Linux/Proton install both reach the opening.

### WP10.2 Install paths for players
- **Installer** (`installer/install.py`, Windows and Linux): checks the Skyrim exe version (decision 0002) and
  refuses others with a link to the downgrade guide; fetches or locates every manifest mod (Nexus API for Premium
  users, otherwise a guided manual download list); verifies hashes; deploys into a clean profile; runs Pandora;
  installs Argonia; runs a short self-check.
- **Wabbajack modlist** (and **Jackify** for Linux users) as the one-click path: built from the manifest; tested
  from scratch.
- **FOMOD** package of our own files for Mod Organizer 2 users who manage their own stacks (documented as
  unsupported if they add other mods).
- **Acceptance:** three clean installs (installer on Windows, Wabbajack on Windows, Jackify on Linux) reach the
  opening.

### WP10.3 Documentation
- Player docs: requirements (Skyrim SE at the pinned version, disk space, a clean profile), the **downgrade
  guide** (Steam depot rollback to the pin), install steps for each path, controls (keyboard/mouse and gamepad),
  known issues, how to report bugs (GitHub issue template).
- Credits: every dependency and its authors, the sourcing register's credit lines, Pelagiad, Transbot9
  (CC BY-NC 4.0 apron data), CC music, universal-modder (MIT), forked mods with their licences.
- The Creation Kit EULA's required notice that the mod is not made, distributed or supported by ZeniMax/Bethesda;
  non-commercial terms; no affiliation with Tamriel Rebuilt or Beyond Skyrim (O-13).
- AI disclosure (Nexus rules since 2026-07-31): code, text and some 2D art made with AI.
- **Acceptance:** docs reviewed by `text-review`; links checked.

### WP10.4 Nexus page
- Page text, screenshots (our own captures), requirements list, permissions section (our files: open licence
  of the owner's choice for code; data and text terms), AI tags, links to the repo and the release.
- **Owner step:** the owner publishes from their account.

### WP10.5 The owner's permanent setup
- A golden AMI of the GPU box (pinned Skyrim, stack, Argonia, Selkies), saves on S3, a one-click start (a
  bookmark to a small "start my game" Lambda URL or an AWS console shortcut), idle-stop, cost per hour
  confirmed; the build VM can be stopped between development bursts.
- **Acceptance:** the owner starts a session from the phone with one tap and plays within 3 minutes; monthly
  cost of play-only use reported.

### WP10.6 After release
- Bug triage process (issue template → planner triage → fix lanes → patch release); runtime-pin moves only by
  decision record; dependency updates only after the full smoke and journeys pass.

## Exit gate
Release published; three install paths verified; owner's one-tap play works; P10 check-in with costs.

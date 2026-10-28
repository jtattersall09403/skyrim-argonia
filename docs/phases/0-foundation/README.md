# Part 0: Foundation

**Goal.** By the end of this part:
- agents on the build VM can brief, build, check and commit safely;
- every assumption the architecture rests on has passed a go/no-go spike;
- the pinned stack installs onto a fresh GPU box by script;
- agents and the owner reach any place through **the studio** (decision
  [0022](../../decisions/0022-the-studio-boots-into-any-place.md));
- records come out of the generator pipeline;
- the owner has played in the studio through the stream on the phone and the Mac.

**What this part is not.** It builds no game system beyond what a spike needs. Spike code lives in `spikes/`
unless a spike says its output becomes the real component. A spike that grows into a system is a defect: stop
and move the work to Part 1.

## Starting state

The repo holds docs only: the plan, the decisions, research, the owner brief and the accounting. The owner's
setup steps are in [infra/README.md](../../../infra/README.md):
- an AWS budget alert;
- the `argonia-build` m7i.xlarge spot instance (Ubuntu 24.04, 120 GiB gp3, no inbound rules, SSM role
  `argonia-build-ssm`);
- a VS Code tunnel `argonia-build`;
- Claude Code logged in inside `tmux`;
- `gh` authenticated, and the repo cloned to `~/skyrim-argonia`.

If any of these is missing, 0.1's first check-in asks for it.

## Chunk table

| Id | Chunk | Depends on | Lane-able beside |
|---|---|---|---|
| 0.1 | [Bootstrap: repo, ways of working, build VM, import](0.1-bootstrap.md) | — | — |
| 0.2 | [The GPU box and the go/no-go spikes G1–G10](0.2-spikes.md) | 0.1 | 0.3 §a, §b |
| 0.3 | [The pinned stack, permissions and the installer](0.3-stack-and-installer.md) | 0.2 G3 | 0.4, 0.5 |
| 0.5 | [The record pipeline, the quarantine and the immersion inventory](0.5-pipeline-quarantine-inventory.md) | 0.2 G4 | 0.3 |
| 0.4 | [The bridge, the studio and the two runners](0.4-bridge-studio-runners.md) | 0.2 G1, G4, G5, G8, G10 (so after 0.2 closes); 0.5 §a, §b | 0.3 |

0.5's quarantine journey and inventory reachability run on the 0.4 game runner when it lands; until then they run
as G1-bridge scripts.

## Part 0 exit (the owner signs)

- G1–G10 passed, or the owner accepted a gate's documented fallback in writing. Decisions 0001, 0002, 0004,
  0007 and 0014 carry the measured facts.
- A fresh GPU box reaches a passing smoke scene through `installer/install.py` with no manual step beyond the
  documented downloads.
- The studio boots into a scene within its 0.4 targets. Its panel teleports between the G4 sample place and the
  proving ground, changes time and weather, shows the overlays, and files a "report here" finding.
- The core runner and the game runner both pass the 0.4 sample journey. A deliberately broken journey fails on
  both, with a readable reason.
- `make check` is green in CI and on the build VM, and regenerating the sample world twice gives no diff.
- **Owner check:** the owner opens the studio on the phone (folded and unfolded) and on the Mac, walks the
  sample place, teleports, and rules on stream feel and text readability. The check-in carries:
  - the gate evidence, the costs so far and the re-estimate of Parts 1–4;
  - the O-3 (runtime pin) ask, and O-6 (Nexus Premium) if 0.1 left it open.

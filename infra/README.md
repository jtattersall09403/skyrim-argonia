# Infrastructure

What runs where, and how to rebuild it. Decision [0008](../docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md) holds the budget (AWS under $150 a month since the owner raised it on 2026-11-10). Update this file in place when anything changes.

## Machines

| Name | Role | Where and type | Notes |
|---|---|---|---|
| `argonia-build` | Claude Code agents, mod staging | eu-west-2 (London), m7i-flex.xlarge **on demand**, Ubuntu 24.04, 120 GiB gp3 | run about 8–10 h a day: idle-stop after 20 min, `tooling/agent_stop.sh` when done, wake.yml on an owner comment; VS Code tunnel `argonia-build`; SSM as break-glass; no inbound rules |
| `argonia-play` | Skyrim SE on Windows Server 2022, streamed to the owner | eu-west-3b (Paris), g4dn.xlarge **on demand** (~$0.80/h), i-003a8d8e08142cc5b, 150 GiB gp3 ([0039](../docs/decisions/0039-the-play-machine-is-a-g4dn-on-demand.md)) | No image or snapshot kept (the g6 and its image retired 2026-11-07). Recreate with `gpu-box/create.sh`, then `gpu-box/setup.ps1` and `gpu-box/stack.py` |

Build-VM agents assume frequent interruption: every job is resumable (`tooling/job_guard.sh`), work is committed small, and `build-vm/resume.sh` plus `prompts/resume.md` restart the session after a stop.

## The mod stack

`mods/dependencies.json` lists every mod. `gpu-box/stack.py fetch` finds each archive in this order: local `~/.argonia/mods`, then `s3://argonia-private-050977237313/mods/`, then the Nexus API (key in `~/.argonia/secrets.env`). Then `stack.py` stages, pushes to the play machine, and `gpu-box/stack.ps1 on` switches the stack on. Game and mod files are never committed (decision 0003).

## The owner's play path

1. `play.<domain>` sits behind Cloudflare Access (owner's email only; `gpu-box/cloudflare_gate.py`).
2. The Worker `cloudflare/play-switch.js` starts the machine if it is stopped.
3. Moonlight-Web and Sunshine (`gpu-box/moonlight-web.ps1`, `sunshine-apps.json`) stream it, with our touch pad `argonia.js` (`stream-client/`: `src/`, `build.sh`, `deploy.sh`, `install.ps1`).
4. The owner picks a card, "Argonia" or "Vanilla Skyrim" (`gpu-box/make-cards.ps1`), which runs `stack.ps1 play-modded`.
5. `gpu-box/saves-sync.ps1` copies saves to the saves bucket every 5 minutes.
6. `gpu-box/idle-stop.ps1` stops the machine after 15 minutes idle.

## The owner's studio path

1. `studio.<domain>` sits behind Cloudflare Access (owner's email only; `build-vm/studio_gate.py`), a tunnel to the studio on the build VM.
2. The same Worker, `cloudflare/play-switch.js`, is routed on the studio's page: if the build VM is stopped it checks the owner's sign-in, tags the instance `argonia-studio-start` and starts it; the page turns into the studio when it answers.
3. At boot `build-vm/resume.sh` reads that tag and resumes no agent for a studio start.
4. The VM stops itself as always: the studio's Awake job, then the owner's CPU alarm, about 30 minutes after the last tab closes.

## Setup scripts

- Build VM: `build-vm/install.sh` installs `idle-stop.sh` (timer, 20 minutes idle), `resume.sh` (at boot), `watchdog.sh` and `owner-wake.sh`; `setup.sh` and `smoke.sh` check it.
- Play machine: `gpu-box/create.sh` (launch), `setup.ps1` (stages), `run.sh` (SSH from the build VM), `display.ps1`, `gpu-bind.ps1`, `vdd-boot.ps1`, `sunshine-prep.ps1`, `pair_moonlight_web.py`.
- Recreating the play machine, in order: `gpu-box/create.sh` (on demand by default; `AMI=<our image>` to launch from an image), `run.sh setup all` (skip from an image), `run.sh setup redist` once Skyrim is on disk (DirectX June 2010, the VC++ runtimes and Media Foundation: without them the game stops at a missing XINPUT1_3.dll, 2026-11-06), `stream-client/deploy.sh` (our page and the heartbeat collector: without it the Worker finds no heartbeat and stops the machine 30 minutes after every start, as it did three times on 2026-11-05/06), `cloudflare_gate.py tunnel argonia-play`, `pair_moonlight_web.py` and `default_user.py`, the Administrator's auto sign-in (`setup.ps1 -Stage autologon -Password <GAME_WINDOWS_PASSWORD>`: without a signed-in session Sunshine can start no card), then `stack.py install`.

## Accounts and secrets

- AWS Budget `argonia-monthly`: $100, alerts at 50/80/100%. IAM role `argonia-build-ssm` on the build VM; the `argonia-agent` policy is in [OWNER-SETUP](OWNER-SETUP.md).
- Secrets live only in `~/.argonia/secrets.env` on the build VM (mode 600, never in the repo): Nexus API key, Cloudflare tokens, Fal key.
- Steam: the owner's account, logged in once on the play machine with Steam Guard, offline mode; updates off for the pinned Skyrim (decision 0002, build 24914197, runtime 1.7.104.0).
- Never reset the play machine's Windows password: Windows drops Steam's saved sign-in.
- The domain and Cloudflare account are the owner's (about $10 a year, outside the AWS budget).

# Owner setup: what only the owner can do

For the owner, and for any agent helping the owner set up (including a Claude session in another account). Work
down the list. Each item says where it is done and how to confirm it. **Never paste a secret into chat, an
issue, a commit or this file.** Secrets go only into `~/.argonia/secrets.env` on the build VM, edited in the VS
Code browser editor. The file is mode 600 (`chmod 600 ~/.argonia/secrets.env`) and lives outside the repo.

Status: **[x]** done, **[ ]** to do, **[~]** waiting on AWS or someone else. The planner keeps this file current.

## Already done (2026-10-27 to 28)
- [x] AWS budget alert `argonia-monthly` ($100).
- [x] Build VM `argonia-build` (m7i.xlarge spot, London), with the IAM role `argonia-build-ssm`.
- [x] The VS Code tunnel `argonia-build`.
- [~] GPU spot quota: "All G and VT Spot Instance Requests", eu-west-2. The applied value was 0; an increase to 8
  was requested on 2026-10-28. Confirm in AWS console → Service Quotas → Amazon EC2. It needs at least 4 for one
  g6.xlarge.

## Before chunk 0.0 starts
- [ ] **Claude Code and GitHub on the build VM** (setup step 4):
  1. In the VS Code terminal, start a tmux session: `tmux new -s argonia` (later, `tmux attach -t argonia` gets
     back to it).
  2. Install Claude Code: `curl -fsSL https://claude.ai/install.sh | bash`, then open a new terminal tab and check
     with `claude --version`. Log in by running `claude` and following the browser prompt with the Max account.
  3. Run `gh auth login`.
  4. Clone the repo: `git clone https://github.com/jtattersall09403/skyrim-argonia ~/skyrim-argonia`.
  5. Set git config: `user.name`, and the owner's email.
- [ ] **The secrets file.** Run `mkdir -p ~/.argonia && touch ~/.argonia/secrets.env && chmod 600 ~/.argonia/secrets.env`,
  then open it in the VS Code editor and add these lines, one per line, as `NAME=value`:
  - `NEXUS_API_KEY`: Nexus Mods → profile → Site preferences → API keys → personal API key (Premium account).
  - `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_ENDPOINT`: the old project's Cloudflare R2 credentials.
    These are in the owner's password manager, or in `/workspaces/.es-secrets.env` on the stopped old machine (see
    chunk 0.1 §e for the safe way to copy them).
  - `OLD_REPO_TOKEN`: a fine-grained GitHub token with read-only Contents access to
    `jtattersall09403/elder-souls-argonia` only. Create it at GitHub → Settings → Developer settings →
    Fine-grained tokens.
  - `FAL_KEY`: fal.ai dashboard → API keys. This is for the agents' Fal access on the build VM; the owner's Fal
    MCP connection elsewhere is separate.
- [ ] **Add the Creation Kit to the Steam library:** Steam → search "Skyrim Special Edition: Creation Kit" → add
  (free with Skyrim SE).
- [ ] **Steam Guard on the phone, ready:** the agent will ask for one login approval when it installs Steam on
  the game machine, and later for Dark Souls Remastered and Morrowind downloads.

## Asked by the agent during 0.0 (not needed in advance)
- [ ] Attach the EC2 permission policy the agent writes to the build VM's role (the JSON comes in the 0.0 owner
  issue).
- [ ] The GitHub-to-AWS trust (OIDC) for "wake on reply". The agent writes the role and its exact trust policy;
  the owner creates it in IAM in one paste and adds its ARN as a repo variable.
- [ ] A Steam login through the game stream (Steam Guard approval).

## Confirm when done
The planner runs `tools/owner_setup_check.sh` (written in 0.0). It checks that each secret name is present
without printing any value, that `gh` and the AWS role work, and that the quota is at least 4. It ticks the
boxes above.

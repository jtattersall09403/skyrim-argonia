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
- [x] GPU spot quota "All G and VT Spot Instance Requests", eu-west-2: 8 vCPUs, approved 2026-10-28. That is one
  g6.2xlarge or two g6.xlarge. A rise to 16 is requested only when parallel game copies are needed.

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

## During setup, after step 4 (about 15 minutes)

### Step 5: the agent's AWS permissions
AWS console → IAM → Roles → `argonia-build-ssm` → Add permissions → Create inline policy → JSON. Paste the
policy below and name it `argonia-agent`. It lets the agent create, start and stop only machines tagged
`project=argonia` in London, use `argonia-*` S3 buckets, and read costs and quotas. If the agent later needs
something this does not allow, it asks in an owner issue with the exact addition.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "Read", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:Describe*", "servicequotas:GetServiceQuota", "servicequotas:ListServiceQuotas",
                "ce:GetCostAndUsage", "ce:GetCostForecast", "pricing:GetProducts"]},
    {"Sid": "CreateInLondon", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:RunInstances", "ec2:RequestSpotInstances", "ec2:CreateVolume", "ec2:CreateTags",
                "ec2:CreateLaunchTemplate", "ec2:CreateLaunchTemplateVersion", "ec2:CreateSecurityGroup",
                "ec2:CreateKeyPair", "ec2:ImportKeyPair"],
     "Condition": {"StringEquals": {"aws:RequestedRegion": "eu-west-2"}}},
    {"Sid": "ManageOwnMachines", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:RebootInstances", "ec2:TerminateInstances",
                "ec2:ModifyInstanceAttribute", "ec2:CreateImage", "ec2:AttachVolume", "ec2:DetachVolume",
                "ec2:ModifyVolume", "ec2:DeleteVolume", "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupIngress", "ec2:AuthorizeSecurityGroupEgress",
                "ec2:RevokeSecurityGroupEgress", "ec2:DeleteSecurityGroup"],
     "Condition": {"StringEquals": {"aws:ResourceTag/project": "argonia"}}},
    {"Sid": "Buckets", "Effect": "Allow",
     "Action": ["s3:CreateBucket", "s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
     "Resource": ["arn:aws:s3:::argonia-*", "arn:aws:s3:::argonia-*/*"]},
    {"Sid": "GameMachineRole", "Effect": "Allow", "Action": "iam:PassRole",
     "Resource": "arn:aws:iam::*:role/argonia-play-*"}
  ]
}
```

### Step 6: wake on reply (GitHub → AWS, no stored keys)
1. IAM → Identity providers → Add provider → OpenID Connect. Provider URL
   `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`. Skip this if it already exists.
2. IAM → Roles → Create role → Custom trust policy. Paste the trust policy below, replacing `ACCOUNT_ID` with
   your 12-digit account id (top right of the console). Name the role `argonia-github-wake`.

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"},
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                          "token.actions.githubusercontent.com:sub": "repo:jtattersall09403/skyrim-argonia:ref:refs/heads/main"}
       }
     }]
   }
   ```

3. Give that role one inline policy, `wake-build-vm`. It can only start the build VM and look it up:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {"Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*"},
       {"Effect": "Allow", "Action": "ec2:StartInstances", "Resource": "*",
        "Condition": {"StringEquals": {"aws:ResourceTag/Name": "argonia-build"}}}
     ]
   }
   ```

4. Copy the role's ARN. Go to GitHub → the repo → Settings → Secrets and variables → Actions → Variables → New
   variable, named `AWS_WAKE_ROLE_ARN`, with the ARN as its value. (It is not secret: it only works from this
   repo's main branch.)
5. Check that the build VM has the tag `Name = argonia-build` (EC2 → the instance → Tags).
6. In the VS Code terminal, run `gh auth refresh -s workflow`, so the agent can push the workflow file.

The agent writes the workflow itself. It runs only for comments by `jtattersall09403`, never for its own. One
run at a time, so a second comment queues. It only starts the existing machine and never creates one.

### Step 7: Steam on the build VM (game data for the tools)
The build VM needs Skyrim SE's own data files (read-only, for our record generator), Dark Souls Remastered (for
measuring) and Morrowind (for reference facts). In the VS Code terminal:

```bash
sudo add-apt-repository -y multiverse && sudo dpkg --add-architecture i386 && sudo apt update
sudo apt install -y steamcmd
steamcmd +@sSteamCmdForcePlatformType windows +force_install_dir ~/games/skyrimse +login YOUR_STEAM_NAME +app_update 489830 validate +quit
```

It asks for your password and a Steam Guard code once, then remembers the login. Then:

```bash
steamcmd +@sSteamCmdForcePlatformType windows +force_install_dir ~/games/dsr +login YOUR_STEAM_NAME +app_update 570940 validate +quit
steamcmd +@sSteamCmdForcePlatformType windows +force_install_dir ~/games/morrowind +login YOUR_STEAM_NAME +app_update 22320 validate +quit
```

If an app id is refused, the agent finds the right one; it is not worth your time.

### Step 8: start the work
In the tmux session: `cd ~/skyrim-argonia && claude`, then say **"start chunk 0.0"**.

## Left for chunk 0.0 (one moment, at the start of your play session)
- [ ] Log in to Steam on the Windows game machine through the stream (password and Steam Guard, about 3
  minutes). The Creation Kit, Skyrim and the mods are then installed there by the agent.

## Confirm when done
The planner runs `tools/owner_setup_check.sh` (written in 0.0). It checks that each secret name is present
without printing any value, that `gh` and the AWS role work, and that the quota is at least 4. It ticks the
boxes above.

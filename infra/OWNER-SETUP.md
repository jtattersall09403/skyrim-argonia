# Owner setup: what only the owner can do

Never paste a secret into chat, an issue, a commit or this file. Secrets go only into `~/.argonia/secrets.env` on the build VM (mode 600, outside the repo). Status: **[x]** done, **[ ]** to do.

## Done
- [x] AWS budget alert `argonia-monthly` ($100).
- [x] Build VM `argonia-build` (m7i-flex.xlarge persistent spot, London, role `argonia-build-ssm`, tags `Name=argonia-build`, `project=argonia`).
- [x] VS Code tunnel `argonia-build`, signed in with GitHub (open `https://vscode.dev/tunnel/argonia-build` with the same GitHub account).
- [x] Claude Code, `gh` and the repo on the build VM (tmux session `argonia`).
- [x] `NEXUS_API_KEY` in `secrets.env` (Nexus profile, Site preferences, API keys; Premium).

## Starting the build VM
EC2 (London) -> Instances -> `argonia-build` -> Instance state -> Start; wait for 2/2 checks. After an interruption: `tmux new -s argonia -c ~/skyrim-argonia`, then `claude --continue`.

## To do when recreating the play machine
- [ ] GPU spot quota "All G and VT Spot Instance Requests" in **eu-west-3 (Paris)**: at least 4 vCPUs (one g6.xlarge).
- [ ] The agent runs `gpu-box/create.sh`, `setup.ps1`, then `stack.py`. Log in to Steam on the machine through the stream (password and Steam Guard, about 3 minutes, once). Skyrim SE must be the pinned build (decision 0002).
- [ ] Never reset the Windows password; if you change it, do it signed in, with the old one.

## Cloudflare (the sign-in gate and play switch)
- [ ] Cloudflare account with the domain; tokens in `secrets.env`. The agent runs `gpu-box/cloudflare_gate.py` to put `play.<domain>` behind Access (your email only) and deploys the Worker `cloudflare/play-switch.js`, which starts the machine when you open the page.
- [ ] The Access service token and AWS IAM user for the Worker (start/stop of the play machine only) are created once; the agent lists the exact steps in an owner issue.
- [ ] The studio's address starts the build machine through the same Worker. Its IAM user `argonia-play-switch` needs one more inline policy, `studio-start` (IAM, Users, argonia-play-switch, Add permissions, Create inline policy, JSON): start the build machine and write one tag on it, nothing else. Describing instances it can do already.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "StartTheBuildMachine", "Effect": "Allow", "Action": "ec2:StartInstances",
     "Resource": "arn:aws:ec2:eu-west-2:050977237313:instance/i-0aec57899356eb8bc"},
    {"Sid": "MarkAStudioStart", "Effect": "Allow", "Action": "ec2:CreateTags",
     "Resource": "arn:aws:ec2:eu-west-2:050977237313:instance/i-0aec57899356eb8bc",
     "Condition": {"ForAllValues:StringEquals": {"aws:TagKeys": ["argonia-studio-start"]},
                   "Null": {"aws:TagKeys": "false"}}}
  ]
}
```
  The agent checks it with `node infra/cloudflare/test/studio_live.mjs` (dry runs; both lines say "would succeed").

## Keys
- [x] Nexus API key (above). The agent fetches mods from `~/.argonia/mods`, then `s3://argonia-private-050977237313/mods/`, then Nexus.
- [ ] `FAL_KEY` in `secrets.env` only if 2D art is needed (fal.ai dashboard -> API keys).

## Build-VM agent permissions
IAM -> Roles -> `argonia-build-ssm` -> inline policy `argonia-agent`. It lets agents create, start and stop only machines tagged `project=argonia` (London and Paris), use `argonia-*` buckets, and read costs and quotas.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "Read", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:Describe*", "servicequotas:GetServiceQuota", "servicequotas:ListServiceQuotas",
                "servicequotas:RequestServiceQuotaIncrease",
                "ce:GetCostAndUsage", "ce:GetCostForecast", "pricing:GetProducts"]},
    {"Sid": "Create", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:RunInstances", "ec2:RequestSpotInstances", "ec2:CreateVolume", "ec2:CreateTags",
                "ec2:CreateLaunchTemplate", "ec2:CreateLaunchTemplateVersion", "ec2:CreateSecurityGroup",
                "ec2:CreateKeyPair", "ec2:ImportKeyPair"],
     "Condition": {"StringEquals": {"aws:RequestedRegion": ["eu-west-2", "eu-west-3"]}}},
    {"Sid": "ManageOwnMachines", "Effect": "Allow", "Resource": "*",
     "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:RebootInstances", "ec2:TerminateInstances",
                "ec2:ModifyInstanceAttribute", "ec2:AttachVolume", "ec2:DetachVolume",
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

## Wake on reply (GitHub to AWS, no stored keys)
Role `argonia-github-wake` trusts GitHub's OIDC provider for `repo:jtattersall09403/skyrim-argonia:ref:refs/heads/main` and may only describe instances and start the one tagged `Name=argonia-build`. Its ARN is the repo Actions variable `AWS_WAKE_ROLE_ARN`. The workflow runs only for the owner's comments. Details are in the role's trust and inline policies in IAM.

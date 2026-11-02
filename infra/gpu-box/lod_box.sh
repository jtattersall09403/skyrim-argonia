#!/usr/bin/env bash
# The object LOD on an on-demand GPU box (g6.xlarge, Paris's own type) from the round-3 image of Paris (it holds the
# terrain and TexGen outputs): no spot interrupt can cut DynDOLOD's uncheckpointable run, and the GUI driving works
# as on Paris (the GPU-less box showed every window without a title). Terminated at the end; ~1 h on-demand.
# Needs the on-demand G quota (L-DB2E81BA, 0 vCPU until the owner's request of 2026-11-02 lands): with --when-quota
# it polls the quota every 10 minutes and runs once it allows a g6.xlarge (4 vCPU), skipping if Paris archived first.
#   lod_box.sh [--when-quota]
set -u
cd /home/ubuntu/skyrim-argonia
if [ "${1:-}" = --when-quota ]; then
  while :; do
    [ -f ~/.argonia/lod-steps/argonia-play/objlod-archived ] && { echo "object LOD already archived: no box needed"; exit 0; }
    quota=$(aws service-quotas get-service-quota --region eu-west-3 --service-code ec2 --quota-code L-DB2E81BA --query 'Quota.Value' --output text 2>/dev/null || echo 0)
    [ "${quota%.*}" -ge 4 ] 2>/dev/null && { echo "on-demand G quota ${quota%.*} vCPU in eu-west-3 $(date -u +%H:%M): launching the box"; break; }
    sleep 600
  done
fi
cd /home/ubuntu/skyrim-argonia
R=eu-west-3; AMI=ami-0b3ddccee05837aed; NAME=argonia-play-3
q() { aws ec2 --region $R --output text "$@"; }
ID=$(q describe-instances --filters Name=tag:Name,Values=$NAME Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId')
if [ "$ID" = None ] || [ -z "$ID" ]; then
  TAGS="{Key=Name,Value=$NAME},{Key=project,Value=argonia},{Key=argonia-clone-of,Value=argonia-play},{Key=temporary,Value=lod-box-2026-11-02}"
  ID=$(q run-instances --image-id $AMI --instance-type g6.xlarge --subnet-id subnet-077a9641bc87135e0 --security-group-ids sg-0617ac75f5e8c5e92 \
    --iam-instance-profile Name=argonia-play-ssm --metadata-options HttpTokens=required \
    --tag-specifications "ResourceType=instance,Tags=[$TAGS]" "ResourceType=volume,Tags=[$TAGS]" --query 'Instances[0].InstanceId') || exit 3
  echo "launched $NAME $ID (on-demand g6.xlarge) $(date -u +%H:%M)"
else echo "reusing $NAME $ID"; q start-instances --instance-ids "$ID" >/dev/null 2>&1 || true; fi
echo "$ID" > ~/.argonia/jobs/lod-box2.id
aws ec2 wait instance-running --region $R --instance-ids "$ID" && echo "running $ID $(date -u +%H:%M)"
export ARGONIA_PLAY=$NAME
sha12=$(sha256sum out/ArgoniaWorld.esm | cut -c1-12); m=~/.argonia/lod-steps/$NAME/$sha12; mkdir -p "$m"
for s in prepare terrain texgen; do echo "on the image (Paris, 13:51)" > "$m/$s"; done
infra/gpu-box/run.sh up || exit 3
infra/gpu-box/run.sh ps 'Disable-ScheduledTask -TaskName argonia-idle-stop -EA SilentlyContinue | Out-Null; Get-Process SkyrimSE,skse64_loader,DynDOLOD*,TexGen* -EA SilentlyContinue | Stop-Process -Force; "idle-stop off, game killed"'
infra/gpu-box/run.sh put infra/gpu-box/stack.ps1 infra/gpu-box/bridge.ps1 infra/gpu-box/lod.ps1 C:/argonia/infra/ && echo "helpers pushed"
if timeout 4500 infra/gpu-box/lod.sh run resources dyndolod collect && infra/gpu-box/lod.sh archive; then
  mkdir -p ~/.argonia/lod-steps/argonia-play; date -u +%FT%TZ > ~/.argonia/lod-steps/argonia-play/objlod-archived
  echo "OBJECT LOD ARCHIVED FROM THE BOX $(date -u +%H:%M)"
else echo "OBJECT LOD FAILED ON THE BOX"; fi
aws ec2 terminate-instances --region $R --instance-ids "$ID" --query 'TerminatingInstances[0].CurrentState.Name' --output text
echo "box $ID terminated $(date -u +%H:%M)"

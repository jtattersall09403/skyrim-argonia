#!/usr/bin/env bash
# Move the owner's play machine to a new type or region from an image (1.8; the moves of 2026-10-31 by hand were
# lane-g6-move.md and lane-paris.md). Launches the new machine as argonia-play-new (or $NAME); the cut-over (tags, machines.conf,
# the tunnel, the Worker's REGION) follows in the lane, after the proof.
#   play_move.sh <ami> <ami-region> <type> <subnet> [region]     region defaults to eu-west-2
# 1. waits for the image; copies it into <region> when it lives elsewhere (~25 min for 150 GB);
# 2. a persistent spot <type>, stop on interruption, in <subnet>, the play security group and argonia-play-ssm,
#    tagged Name=argonia-play-new and project=argonia; idempotent (an argonia-play-new is reused);
# 3. first boot: the NVIDIA L4 is often unbound on new hardware (CM_PROB_REINSTALL): pnputil adds the store's
#    nvgridsw_aws.inf and the machine reboots; nvidia-smi must then name the GPU.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
export PATH="$HOME/.local/bin:$PATH"
AMI=${1:?usage}; AR=${2:?usage}; TYPE=${3:?usage}; SUBNET=${4:?usage}; R=${5:-eu-west-2}
SG=sg-0c73f686853568ced; PROFILE=argonia-play-ssm; NAME=${NAME:-argonia-play-new}  # NAME=... for the agents' machine
log() { echo "[$(date -u +%T)] $*"; }
log "waiting for $AMI in $AR"; aws ec2 wait image-available --region "$AR" --image-ids "$AMI" \
  || aws ec2 wait image-available --region "$AR" --image-ids "$AMI"
if [ "$AR" != "$R" ]; then
  name=$(aws ec2 describe-images --region "$AR" --image-ids "$AMI" --query 'Images[0].Name' --output text)
  have=$(aws ec2 describe-images --region "$R" --owners self --filters "Name=name,Values=$name" --query 'Images[0].ImageId' --output text)
  if [ "$have" = None ]; then
    AMI=$(aws ec2 copy-image --region "$R" --source-region "$AR" --source-image-id "$AMI" --name "$name" \
      --tag-specifications 'ResourceType=image,Tags=[{Key=project,Value=argonia}]' --query ImageId --output text)
    log "copying as $AMI"
  else AMI=$have; log "copy exists: $AMI"; fi
  for i in 1 2 3 4; do aws ec2 wait image-available --region "$R" --image-ids "$AMI" && break; done
fi
log "image $AMI available in $R"
ID=$(aws ec2 describe-instances --region "$R" --filters "Name=tag:Name,Values=$NAME" \
  Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId' --output text)
if [ "$ID" = None ]; then
  ID=$(aws ec2 run-instances --region "$R" --image-id "$AMI" --instance-type "$TYPE" --subnet-id "$SUBNET" \
    --security-group-ids "$SG" --iam-instance-profile Name=$PROFILE \
    --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=persistent,InstanceInterruptionBehavior=stop}' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=project,Value=argonia}]" \
      "ResourceType=volume,Tags=[{Key=Name,Value=$NAME},{Key=project,Value=argonia}]" \
    --query 'Instances[0].InstanceId' --output text)
  log "launched $ID ($TYPE, $SUBNET)"
fi
aws ec2 wait instance-running --region "$R" --instance-ids "$ID"
run="$here/run.sh --machine $NAME"
$run up  # waits for SSH
if ! $run ps 'nvidia-smi -L' 2>/dev/null | grep -q GPU; then
  log "GPU unbound: rebinding the driver and rebooting"
  $run ps 'pnputil /add-driver C:\Windows\INF\oem81.inf /install | Out-Null; Restart-Computer -Force' || true
  read -t 60 < /dev/zero 2>/dev/null || true
  $run up
fi
$run ps 'nvidia-smi -L'
log "$NAME $ID up from $AMI; next: deploy, prove, cut over"

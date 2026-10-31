#!/usr/bin/env bash
# Clone a game machine into another one (owner, 2026-10-29: "as many game machines as you need").
#   clone.sh [--from argonia-play] [--new-image | --image ami-...] argonia-play-N [instance-type] [az]
# Run it under the new machine's lock; it waits on the image (tens of minutes the first time):
#   tooling/job_guard.sh run --gpu=argonia-play-2 clone-play-2 -- infra/gpu-box/clone.sh argonia-play-2
#
# 1. The image: the newest available image of the source tagged argonia-image=<source>, else (or with --new-image)
#    a new one taken with --no-reboot, so the source keeps running (a little disk slowdown while it snapshots).
# 2. The machine: persistent spot, stop on interruption, the source's type and AZ unless given, tags Name and
#    project=argonia, security group argonia-play-clone: SSH from the build VM only and egress inside the VPC only.
#    So a clone never streams or answers to the internet, its copy of the gate's tunnel cannot connect, and Steam
#    stays offline.
# 3. First boot: the tunnel connector is disabled (it carries the source's token), the Windows name becomes the
#    machine name (ARGONIA-PLAY-N) and it reboots; it is left running for the proof,
#    ARGONIA_PLAY=<name> python3 infra/gpu-box/stack.py menu, then infra/gpu-box/run.sh --machine <name> stop.
# Idempotent: an existing machine of that name is reused, and each step skips what is already done.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
here=$(cd "$(dirname "$0")" && pwd)
R=eu-west-2
VPC=vpc-8dfe71e5
FROM=argonia-play; NEW_IMAGE=0; AMI_GIVEN=
while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM=$2; shift 2 ;;
    --new-image) NEW_IMAGE=1; shift ;;
    --image) AMI_GIVEN=$2; shift 2 ;;  # a named London image (the source has moved region, #27)
    *) break ;;
  esac
done
NAME=${1:?usage: clone.sh [--from argonia-play] [--new-image] argonia-play-N [type] [az]}
case "$NAME" in argonia-play-[0-9]*) ;; *) echo "clone names are argonia-play-<n>" >&2; exit 2 ;; esac
log() { echo "[$(date -u +%T)] $*"; }
q() { aws ec2 "$@" --region $R --output text; }
live='Name=instance-state-name,Values=pending,running,stopping,stopped'

read -r SRC SRC_TYPE SRC_AZ <<<"$(q describe-instances --filters "Name=tag:Name,Values=$FROM" "$live" \
  --query 'Reservations[0].Instances[0].[InstanceId,InstanceType,Placement.AvailabilityZone]')"
[ "$SRC" != None ] || { echo "no machine $FROM" >&2; exit 1; }
TYPE=${2:-$SRC_TYPE}; AZ=${3:-$SRC_AZ}

ID=$(q describe-instances --filters "Name=tag:Name,Values=$NAME" "$live" --query 'Reservations[0].Instances[0].InstanceId')
if [ "$ID" = None ]; then
  # 1. The image.
  AMI=${AMI_GIVEN:-None}
  [ -n "$AMI_GIVEN" ] || [ $NEW_IMAGE = 1 ] || AMI=$(q describe-images --owners self --filters "Name=tag:argonia-image,Values=$FROM" \
    Name=state,Values=available,pending --query 'sort_by(Images,&CreationDate)[-1].ImageId')
  if [ "$AMI" = None ] || [ -z "$AMI" ]; then
    stamp=$(date -u +%Y%m%dT%H%MZ)
    tags="{Key=Name,Value=$FROM-$stamp},{Key=project,Value=argonia},{Key=argonia-image,Value=$FROM}"
    AMI=$(q create-image --instance-id "$SRC" --no-reboot --name "$FROM-$stamp" \
      --description "argonia clone source ($FROM, no reboot)" \
      --tag-specifications "ResourceType=image,Tags=[$tags]" "ResourceType=snapshot,Tags=[$tags]" --query ImageId)
    log "image $AMI from $FROM (no reboot)"
  fi
  for i in $(seq 1 480); do
    s=$(q describe-images --image-ids "$AMI" --query 'Images[0].State')
    [ "$s" = available ] && break
    [ "$s" = failed ] && { echo "image $AMI failed" >&2; exit 1; }
    [ $((i % 20)) = 1 ] && log "image $AMI: $s"
    read -t 15 < /dev/zero 2>/dev/null || true
  done
  [ "$s" = available ] || { echo "image $AMI not ready after 2 h" >&2; exit 1; }

  # 2. The security group and the machine.
  BUILD_IP=$(hostname -I | awk '{print $1}')
  SG=$(q describe-security-groups --filters Name=group-name,Values=argonia-play-clone Name=vpc-id,Values=$VPC \
    --query 'SecurityGroups[0].GroupId')
  if [ "$SG" = None ]; then
    SG=$(q create-security-group --vpc-id $VPC --group-name argonia-play-clone \
      --description "argonia-play clones: SSH from the build VM only; egress inside the VPC only" \
      --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=argonia-play-clone},{Key=project,Value=argonia}]" \
      --query GroupId)
    q authorize-security-group-ingress --group-id "$SG" \
      --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$BUILD_IP/32,Description=build-vm}]" >/dev/null
    q revoke-security-group-egress --group-id "$SG" --ip-permissions 'IpProtocol=-1,IpRanges=[{CidrIp=0.0.0.0/0}]' >/dev/null
    q authorize-security-group-egress --group-id "$SG" \
      --ip-permissions 'IpProtocol=-1,IpRanges=[{CidrIp=172.31.0.0/16,Description=vpc-only}]' >/dev/null
    log "security group $SG"
  fi
  SUBNET=$(q describe-subnets --filters Name=vpc-id,Values=$VPC Name=availability-zone,Values="$AZ" --query 'Subnets[0].SubnetId')
  TAGS="{Key=Name,Value=$NAME},{Key=project,Value=argonia},{Key=argonia-clone-of,Value=$FROM}"
  ID=$(q run-instances --image-id "$AMI" --instance-type "$TYPE" --subnet-id "$SUBNET" --security-group-ids "$SG" \
    --iam-instance-profile Name=argonia-play-ssm \
    --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=persistent,InstanceInterruptionBehavior=stop}' \
    --metadata-options HttpTokens=required \
    --tag-specifications "ResourceType=instance,Tags=[$TAGS]" "ResourceType=volume,Tags=[$TAGS]" \
      "ResourceType=spot-instances-request,Tags=[$TAGS]" \
    --query 'Instances[0].InstanceId')
  log "launched $NAME $ID ($TYPE, $AZ) from $AMI"
  # The clone holds what was pushed to the source, so stack.py push starts from the source's record.
  sent="$HOME/.argonia/stack/push/sent.json"
  [ "$FROM" = argonia-play ] || sent="$HOME/.argonia/stack/push-$FROM/sent.json"
  if [ -f "$sent" ]; then mkdir -p "$HOME/.argonia/stack/push-$NAME"; cp -n "$sent" "$HOME/.argonia/stack/push-$NAME/"; fi
  aws ec2 wait instance-running --region $R --instance-ids "$ID"
fi
# The AWS-side idle backstop, keyed to this instance (idle-stop.ps1 inside Windows comes with the image).
"$here/alarm.sh" "$NAME"

# 3. First boot.
export ARGONIA_PLAY=$NAME
"$here/run.sh" up
host=$(echo "$NAME" | tr '[:lower:]' '[:upper:]')
out=$("$here/run.sh" ps "Get-Service cloudflared* -EA SilentlyContinue | % { Stop-Service \$_.Name -Force -EA SilentlyContinue; Set-Service \$_.Name -StartupType Disabled }
Get-ScheduledTask -EA SilentlyContinue | ? { \$_.TaskName -like '*cloudflared*' } | Disable-ScheduledTask | Out-Null
Get-Process cloudflared -EA SilentlyContinue | Stop-Process -Force
Set-Content C:\\argonia\\state\\machine.txt '$NAME' -Encoding ascii
if (\$env:COMPUTERNAME -ne '$host') { Rename-Computer -NewName '$host' -Force | Out-Null; 'RENAMED' } else { 'NAMED' }" | tr -d '\r')
echo "$out"
if grep -q RENAMED <<<"$out"; then
  "$here/run.sh" ps 'Restart-Computer -Force' >/dev/null 2>&1 || true
  read -t 45 < /dev/zero 2>/dev/null || true
  for i in $(seq 1 24); do "$here/run.sh" ps hostname >/dev/null 2>&1 && break; read -t 10 < /dev/zero 2>/dev/null || true; done
fi
log "$NAME is $("$here/run.sh" ps hostname | tr -d '\r') at $("$here/run.sh" ip)"

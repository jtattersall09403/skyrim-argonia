#!/usr/bin/env bash
# 1.8 (one-off, kept for the record and a rerun): both game machines to g5.xlarge spot in Stockholm (eu-north-1), from the London image. Run after the owner's
# IAM edit. Launches argonia-play-sto (the owner's, stream ports open) and argonia-play-2 (the agents', clone.sh:
# no tunnel). The cut-over (tags, machines.conf for argonia-play, the Worker) follows after the proof.
set -euo pipefail
cd /home/ubuntu/skyrim-argonia
R=eu-north-1; SRC_AMI=ami-07415d5dbbde06bc2; TYPE=g5.xlarge; AZ=eu-north-1b
log() { echo "[$(date -u +%T)] $*"; }
q=$(aws service-quotas get-service-quota --region $R --service-code ec2 --quota-code L-3819A6DF --query Quota.Value --output text)
if [ "${q%.*}" -lt 8 ]; then
  aws service-quotas request-service-quota-increase --region $R --service-code ec2 --quota-code L-3819A6DF --desired-value 16 \
    --query 'RequestedQuota.Status' --output text || true
  log "quota $q: increase to 16 requested"
fi
# the owner's security group: London's play rules (stream ports), SSH opened per call by run.sh
VPC=$(aws ec2 describe-vpcs --region $R --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 describe-security-groups --region $R --filters Name=group-name,Values=argonia-play Name=vpc-id,Values=$VPC --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = None ]; then
  SG=$(aws ec2 create-security-group --region $R --vpc-id $VPC --group-name argonia-play --description "argonia-play: stream ports; SSH from the build VM per call" \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=argonia-play},{Key=project,Value=argonia}]' --query GroupId --output text)
  perms=$(aws ec2 describe-security-groups --region eu-west-2 --group-ids sg-0c73f686853568ced --query 'SecurityGroups[0].IpPermissions[?FromPort!=`22`]' --output json)
  aws ec2 authorize-security-group-ingress --region $R --group-id $SG --ip-permissions "$perms" >/dev/null
  log "security group $SG"
fi
# machines.conf before any run.sh call on these names
grep -q '^argonia-play-sto ' infra/gpu-box/machines.conf || echo 'argonia-play-sto    eu-north-1 public' >> infra/gpu-box/machines.conf
grep -q '^argonia-play-2 ' infra/gpu-box/machines.conf || echo 'argonia-play-2      eu-north-1 public' >> infra/gpu-box/machines.conf
# the London agents' machine keeps its disk under another name until retired
aws ec2 create-tags --region eu-west-2 --resources i-051031ffad81280bb --tags Key=Name,Value=argonia-play-2-london-g6 || true
SUBNET=$(aws ec2 describe-subnets --region $R --filters Name=vpc-id,Values=$VPC Name=availability-zone,Values=$AZ --query 'Subnets[0].SubnetId' --output text)
# the owner's machine (copies the image, launches, binds the GPU, warms the disk)
NAME=argonia-play-sto SG=$SG infra/gpu-box/play_move.sh $SRC_AMI eu-west-2 $TYPE $SUBNET $R
AMI=$(aws ec2 describe-images --region $R --owners self --filters Name=name,Values=argonia-play-20261031-london-g6-2xl --query 'Images[0].ImageId' --output text)
# the agents' machine, the same type and image
infra/gpu-box/clone.sh --region $R --from argonia-play-sto --image $AMI argonia-play-2 $TYPE $AZ
log "DONE: argonia-play-sto and argonia-play-2 up in $R"

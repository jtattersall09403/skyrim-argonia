#!/usr/bin/env bash
# The AWS-side backstop for the game machine (owner call #6): stop it when there has been no streaming traffic for
# 30 minutes, even if Windows hangs. A stream sends several hundred MB per 5 minutes; an idle desktop a few MB.
#   infra/gpu-box/alarm.sh
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
R=eu-west-2
ID=$(aws ec2 describe-instances --region $R --filters Name=tag:Name,Values=argonia-play \
  Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId' --output text)
aws cloudwatch put-metric-alarm --region $R --alarm-name argonia-play-no-stream \
  --alarm-description "Stop argonia-play after 30 minutes with under 20 MB out per 5 minutes (no stream client)" \
  --namespace AWS/EC2 --metric-name NetworkOut --dimensions "Name=InstanceId,Value=$ID" \
  --statistic Sum --period 300 --evaluation-periods 6 --threshold 20000000 \
  --comparison-operator LessThanThreshold --treat-missing-data notBreaching \
  --alarm-actions "arn:aws:automate:$R:ec2:stop"
echo "alarm argonia-play-no-stream set on $ID"

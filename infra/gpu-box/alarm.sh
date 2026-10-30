#!/usr/bin/env bash
# The AWS-side backstop for a game machine (owner calls #6, #13), stopping it even if Windows hangs. Inside Windows
# the scheduled task argonia-idle-stop (idle-stop.ps1, carried by the image) stops it after 15 idle minutes.
#   infra/gpu-box/alarm.sh [argonia-play | argonia-play-N]
# argonia-play: no streaming traffic for 30 minutes (a stream sends hundreds of MB per 5 min; an idle desktop a few).
# A clone is headless and has no tunnel heartbeat, so its backstop is CPU: under 3% average for 45 minutes.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
R=eu-west-2
NAME=${1:-argonia-play}
ID=$(aws ec2 describe-instances --region $R --filters "Name=tag:Name,Values=$NAME" \
  Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId' --output text)
[ "$ID" != None ] || { echo "no machine $NAME" >&2; exit 1; }
if [ "$NAME" = argonia-play ]; then
  aws cloudwatch put-metric-alarm --region $R --alarm-name argonia-play-no-stream \
    --alarm-description "Stop argonia-play after 30 minutes with under 20 MB out per 5 minutes (no stream client)" \
    --namespace AWS/EC2 --metric-name NetworkOut --dimensions "Name=InstanceId,Value=$ID" \
    --statistic Sum --period 300 --evaluation-periods 6 --threshold 20000000 \
    --comparison-operator LessThanThreshold --treat-missing-data notBreaching \
    --alarm-actions "arn:aws:automate:$R:ec2:stop"
  echo "alarm argonia-play-no-stream set on $ID"
else
  aws cloudwatch put-metric-alarm --region $R --alarm-name "$NAME-idle" \
    --alarm-description "Stop $NAME after 45 minutes under 3% CPU (headless clone; backstop to idle-stop.ps1)" \
    --namespace AWS/EC2 --metric-name CPUUtilization --dimensions "Name=InstanceId,Value=$ID" \
    --statistic Average --period 300 --evaluation-periods 9 --threshold 3 \
    --comparison-operator LessThanThreshold --treat-missing-data notBreaching \
    --alarm-actions "arn:aws:automate:$R:ec2:stop"
  echo "alarm $NAME-idle set on $ID"
fi

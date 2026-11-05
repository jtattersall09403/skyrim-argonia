#!/usr/bin/env bash
# Create the Windows game machine `argonia-play` from the build VM (chunk 0.0 §b). Idempotent: if a non-terminated
# argonia-play exists it prints it and exits. Bash, not PowerShell, because it runs on the Linux build VM; the
# Windows side is setup.ps1, run over SSH.
#
#   infra/gpu-box/create.sh [instance-type] [region] [az]     default g6.xlarge in eu-west-3b: the region and zone
#   are chosen by the spot placement score (decision 0008: whichever European region interrupts least at a similar
#   price; Paris euw3-az2 scored 9 against London's 1 on 2026-11-05). The region's default VPC is used; machines.conf
#   must name the machine in that region afterwards (run.sh reads it) and `cloudflare_gate.py worker` re-points the Worker.
#   MARKET=ondemand   an on-demand machine instead of persistent spot (owner, 2026-11-05: g4dn.xlarge on demand, guaranteed)
#   AMI=ami-...       launch from our own image of a set-up machine (Steam login, Skyrim, the Creation Kit, the stack)
#                     instead of a fresh Windows Server; setup.ps1 is then not needed
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
TYPE="${1:-g6.xlarge}"
R="${2:-eu-west-3}"
AZ="${3:-eu-west-3b}"
VPC=$(aws ec2 describe-vpcs --region $R --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
# The machine is reached on its public address: SSH is opened to the build VM's public IP (run.sh up refreshes it).
BUILD_IP=$(curl -s --max-time 5 https://checkip.amazonaws.com || hostname -I | awk '{print $1}')
KEY="$HOME/.argonia/keys/argonia-play"
TAGS="{Key=Name,Value=argonia-play},{Key=project,Value=argonia}"

existing=$(aws ec2 describe-instances --region $R \
  --filters Name=tag:Name,Values=argonia-play Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PrivateIpAddress]' --output text)
if [ -n "$existing" ]; then echo "exists: $existing"; exit 0; fi

# SSH key: ours, generated here, never leaves ~/.argonia.
mkdir -p "$(dirname "$KEY")"; chmod 700 "$(dirname "$KEY")"
[ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N '' -C argonia-build -f "$KEY"
# No EC2 key pair: Windows AMIs refuse ed25519 ones, and the key goes in through user-data below.

# Security group: SSH from the build VM only. Stream ports are opened by stream-access.sh.
SG=$(aws ec2 describe-security-groups --region $R --filters Name=group-name,Values=argonia-play Name=vpc-id,Values=$VPC \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = None ]; then
  SG=$(aws ec2 create-security-group --region $R --vpc-id $VPC --group-name argonia-play \
    --description "argonia-play: SSH from the build VM; stream ports from the owner" \
    --tag-specifications "ResourceType=security-group,Tags=[$TAGS]" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --region $R --group-id "$SG" \
    --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$BUILD_IP/32,Description=build-vm}]" >/dev/null
fi

SUBNET=$(aws ec2 describe-subnets --region $R --filters Name=vpc-id,Values=$VPC Name=availability-zone,Values="$AZ" \
  --query 'Subnets[0].SubnetId' --output text)
[ -n "${AMI:-}" ] || AMI=$(aws ec2 describe-images --region $R --owners amazon \
  --filters 'Name=name,Values=Windows_Server-2022-English-Full-Base-*' \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)

# First boot: OpenSSH server with our key for the Administrator, PowerShell as its shell. Nothing secret here.
PUB=$(cat "$KEY.pub")
USERDATA=$(mktemp); trap 'rm -f "$USERDATA"' EXIT
cat > "$USERDATA" <<EOF
<powershell>
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Content -Path C:\ProgramData\ssh\administrators_authorized_keys -Value '$PUB' -Encoding ascii
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F'
New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell -Value 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -PropertyType String -Force
Set-Service sshd -StartupType Automatic; Start-Service sshd
New-NetFirewallRule -Name sshd-build -DisplayName 'SSH from build VM' -Protocol TCP -LocalPort 22 -RemoteAddress $BUILD_IP -Action Allow
</powershell>
<persist>false</persist>
EOF

if [ "${MARKET:-spot}" = ondemand ]; then MARKET_OPTS=(); else
  MARKET_OPTS=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=persistent,InstanceInterruptionBehavior=stop}'); fi
launch() {
  aws ec2 run-instances --region $R --image-id "$AMI" --instance-type "$TYPE" --subnet-id "$SUBNET" \
    --security-group-ids "$SG" "$@" \
    "${MARKET_OPTS[@]}" --instance-initiated-shutdown-behavior stop \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=150,VolumeType=gp3,DeleteOnTermination=true}' \
    --metadata-options HttpTokens=required \
    --user-data "file://$USERDATA" \
    --tag-specifications "ResourceType=instance,Tags=[$TAGS]" "ResourceType=volume,Tags=[$TAGS]" \
      "ResourceType=spot-instances-request,Tags=[$TAGS]" \
    --query 'Instances[0].InstanceId' --output text
}
# The instance role is optional (SSM break-glass); launch without it if it does not exist.
ID=$(launch --iam-instance-profile Name=argonia-play-ssm 2>/dev/null || launch)
echo "launched $ID ($TYPE, $AZ); waiting for it to run"
aws ec2 wait instance-running --region $R --instance-ids "$ID"
aws ec2 describe-instances --region $R --instance-ids "$ID" \
  --query 'Reservations[].Instances[].[InstanceId,PrivateIpAddress,PublicIpAddress,IamInstanceProfile.Arn]' --output text

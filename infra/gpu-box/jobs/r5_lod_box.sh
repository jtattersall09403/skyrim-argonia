#!/usr/bin/env bash
# Round 5's object LOD on an on-demand g6.xlarge (the owner's G quota landed 2026-11-03): Paris spot was reclaimed
# mid-DynDOLOD twice today (18:34, 22:23) and the owner ruled (17:41, 2026-11-02) not to try that again on Paris. An
# image of Paris's stopped disk (build 7f4d0004 deployed, terrain and TexGen outputs on it) launches as argonia-play-3,
# runs resources, DynDOLOD and collect, archives the LOD to S3 (every deploy of this ESM lays it), terminates itself and
# deletes its image and the old round-3 one (nothing stale kept). Every end wakes the agent. Under job_guard --gpu=argonia-play-3.
set -u; cd /home/ubuntu/skyrim-argonia
R=eu-west-3; SRC=i-06e8da597eb5fceab; NAME=argonia-play-3; OLD_AMI=ami-0b3ddccee05837aed
q() { aws ec2 --region $R --output text "$@"; }
fail() { echo "BOX: $1 $(date -u +%H:%M)"; infra/build-vm/agent-wake.sh "round 5 LOD box FAILED: $1. Read ~/.argonia/jobs/r5-lod-box.log; Paris's r5-close10 waits on this box's rc."; exit 3; }
echo "== wait for Paris stopped $(date -u +%H:%M)"
for i in $(seq 1 60); do s=$(q describe-instances --instance-ids $SRC --query 'Reservations[0].Instances[0].State.Name'); [ "$s" = stopped ] && break; sleep 15; done
[ "$s" = stopped ] || fail "Paris never stopped ($s)"
stamp=$(date -u +%Y%m%dT%H%M)
AMI=$(q create-image --instance-id $SRC --name "argonia-play-r5-$stamp" --description "argonia-play with the round-5 close build 7f4d0004, terrain+TexGen outputs (2026-11-03)" \
  --tag-specifications "ResourceType=image,Tags=[{Key=project,Value=argonia},{Key=argonia-image,Value=argonia-play},{Key=temporary,Value=lod-box-2026-11-03}]" --query ImageId) || fail "create-image"
echo "== image $AMI creating $(date -u +%H:%M)"; echo "$AMI" > ~/.argonia/jobs/r5-lod-box.ami
for i in $(seq 1 160); do s=$(q describe-images --image-ids $AMI --query 'Images[0].State'); [ "$s" = available ] && break; [ "$s" = failed ] && fail "image failed"; sleep 30; done
[ "$s" = available ] || fail "image not available after 80 min"
echo "== image available $(date -u +%H:%M)"
ID=$(q describe-instances --filters Name=tag:Name,Values=$NAME Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[0].Instances[0].InstanceId')
if [ "$ID" = None ] || [ -z "$ID" ]; then
  TAGS="{Key=Name,Value=$NAME},{Key=project,Value=argonia},{Key=argonia-clone-of,Value=argonia-play},{Key=temporary,Value=lod-box-2026-11-03}"
  ID=$(q run-instances --image-id $AMI --instance-type g6.xlarge --subnet-id subnet-077a9641bc87135e0 --security-group-ids sg-0617ac75f5e8c5e92 \
    --iam-instance-profile Name=argonia-play-ssm --metadata-options HttpTokens=required \
    --tag-specifications "ResourceType=instance,Tags=[$TAGS]" "ResourceType=volume,Tags=[$TAGS]" --query 'Instances[0].InstanceId') || fail "run-instances (on-demand g6.xlarge)"
  echo "launched $NAME $ID (on-demand g6.xlarge) $(date -u +%H:%M)"
else echo "reusing $NAME $ID"; q start-instances --instance-ids "$ID" >/dev/null 2>&1 || true; fi
echo "$ID" > ~/.argonia/jobs/r5-lod-box.id
aws ec2 wait instance-running --region $R --instance-ids "$ID" && echo "running $ID $(date -u +%H:%M)"
export ARGONIA_PLAY=$NAME
sha12=$(sha256sum out/ArgoniaWorld.esm | cut -c1-12); m=~/.argonia/lod-steps/$NAME/$sha12; mkdir -p "$m"
for s in prepare terrain texgen; do echo "on the image of Paris ($stamp)" > "$m/$s"; done
infra/gpu-box/run.sh up || fail "box never answered"
infra/gpu-box/run.sh ps 'Disable-ScheduledTask -TaskName argonia-idle-stop -EA SilentlyContinue | Out-Null; Get-Process SkyrimSE,skse64_loader,DynDOLOD*,TexGen*,LODGen*,Texconv* -EA SilentlyContinue | Stop-Process -Force; "idle-stop off, tools clean"'
infra/gpu-box/run.sh put infra/gpu-box/stack.ps1 infra/gpu-box/bridge.ps1 infra/gpu-box/lod.ps1 C:/argonia/infra/ && echo "helpers pushed"
ok=0
if timeout 5400 infra/gpu-box/lod.sh run resources dyndolod collect && infra/gpu-box/lod.sh archive; then ok=1; date -u +%FT%TZ > ~/.argonia/lod-steps/argonia-play/objlod-archived-r5-close; echo "OBJECT LOD ARCHIVED FROM THE BOX $(date -u +%H:%M)"
else echo "OBJECT LOD FAILED ON THE BOX $(date -u +%H:%M)"; fi
q terminate-instances --instance-ids "$ID" --query 'TerminatingInstances[0].CurrentState.Name'; echo "box $ID terminating $(date -u +%H:%M)"
if [ $ok = 1 ]; then  # nothing stale kept: this image and the round-3 one, with their snapshots
  for a in $AMI $OLD_AMI; do snaps=$(q describe-images --image-ids $a --query 'Images[0].BlockDeviceMappings[].Ebs.SnapshotId'); q deregister-image --image-id $a && for sn in $snaps; do q delete-snapshot --snapshot-id $sn && echo "deleted $a $sn"; done; done
  infra/build-vm/agent-wake.sh "round 5 LOD box DONE: object LOD archived; Paris's r5-close10 (deploy lays it, rest stops, saves) runs on."
else fail "DynDOLOD/collect/archive on the box (image $AMI kept for a resume)"; fi

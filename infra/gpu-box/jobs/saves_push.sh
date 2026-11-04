#!/usr/bin/env bash
# After region_saves.py: the region saves were written under an agent job, so saves-sync lists them as agent saves and
# never pushes them, and while the job holds the machine it pushes nothing at all (2026-11-04 00:22-00:53: eight pushes
# 'kept on this machine', the pool still held the 2nd's saves). Take them off that list and push them deliberately, so the shared copy (s3 pool/) carries them to whichever standby
# the owner's play page starts (owner, 2026-11-02: "with the saves available for me").
set -eu
cd /home/ubuntu/skyrim-argonia
export ARGONIA_PLAY=${ARGONIA_PLAY:-argonia-play}
infra/gpu-box/run.sh ps '$f = "C:\argonia\state\saves-agent.txt"; if (Test-Path $f) { $keep = Get-Content $f | Where-Object { $_ -notmatch "^Argonia (Coastal|Deep|Flooded|Interior|Northern|Rootland|Tidal|Western|Claywater)" }; Set-Content $f $keep }; Get-ChildItem "C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves" -Filter "Argonia *.ess" | % { $_.Name }'
infra/gpu-box/run.sh ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\saves-sync.ps1 push -Deliberate "^Argonia (Coastal|Deep|Flooded|Interior|Northern|Rootland|Tidal|Western|Claywater)"; Get-Content C:\argonia\logs\saves-sync.log -Tail 5'
aws s3 ls s3://argonia-saves-050977237313/pool/ | grep -c "Argonia " || true

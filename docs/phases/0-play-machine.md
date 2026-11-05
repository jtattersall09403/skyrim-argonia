# Phase 0: the play machine is back and vanilla Skyrim streams

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

- Pick the region: the spot placement score and interruption band for a g6.xlarge in London and Paris (and any
  other European region at a similar price); the least-interrupted wins. Recreate `argonia-play` there
  (create.sh, setup.ps1: driver, Steam, MO2, Sunshine, Moonlight-Web, the tunnel; machines.conf and the Worker
  updated to the region). The owner logs Steam in once; Skyrim is pinned to build 24914197.
- The play page starts it, the vanilla card runs, saves sync, idle-stop stops it.
- **Owner test:** none, first test is after phase 1

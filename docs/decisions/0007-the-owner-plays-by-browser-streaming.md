# 0007: The owner plays by browser streaming from an AWS GPU machine

**Status:** decided 2026-10-27. Playability, controls and latency are measured first of all, in 0.0 (gate G0), on vanilla Skyrim; re-measured with the full stack in 0.2 (G2).

## Context

The owner plays on an Honor Magic V5 phone and a MacBook Air M2 on which nothing can be installed. Skyrim is
PC-only, so native phone play is impossible with Skyrim as host (with OpenMW it would have been possible; the
owner said native was "an option" to compare, not a requirement). The owner's own idea was a GPU VM streaming
to a browser, which also gives seamless saves across devices.

## Decision

1. The game runs on an on-demand **AWS GPU instance in London** (g6.xlarge L4 preferred for modded Skyrim
   and AV1/H.264 NVENC; g4dn.xlarge T4 for lighter agent test runs; g5.xlarge A10G if L4 spot is scarce),
   chosen by the 0.0 and 0.2 benchmarks (G0, G2).
2. **Selkies** (linuxserver.io build) streams the desktop to a browser tab over WebRTC, with WebSocket/TCP-443
   mode for networks that block UDP (likely the work Mac's). Moonlight-Web + Sunshine is the alternative if
   Selkies' latency or controls disappoint.
3. Access is behind authentication (Selkies basic auth plus a random URL path at minimum; preferably an AWS
   security group limited to the owner's IPs when known), never open to the world.
4. Saves live on the GPU machine's disk and are backed up to S3 after each session; both devices see the same
   game. The machine stops itself after 15 minutes idle (no stream client and no agent job).
5. **Controls:** a Bluetooth gamepad with the phone (browser Gamepad API), keyboard and mouse on the Mac.
   Touch-only play is not a goal; if the owner wants it, Selkies'/Moonlight-Web's touch overlay is evaluated in
   3.4.
6. Expected latency (estimates, research hosting-streaming §6): ~70–125 ms on home Wi-Fi, ~85–150 ms on 5G,
   worse on 4G. Parrying is harder but workable on Wi-Fi. No gameplay numbers are retuned for latency
   (DS1 timings stand, decision 0004); if the owner finds it unplayable the options are: AV1 at lower bitrate,
   a closer region (none closer than London), a native Windows PC or Steam Deck later.

## Consequences

- One target platform for agents to test (Linux + Proton on the GPU box), which is the same box the owner plays
  on: what the agents test is what the owner plays.
- Video compression smears dense foliage and water; the 0.0 measurement records the bitrate the owner accepts.
- Data use is ~3–4 GB/hour; on mobile data the owner should prefer Wi-Fi.

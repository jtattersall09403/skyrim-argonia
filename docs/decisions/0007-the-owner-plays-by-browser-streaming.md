# 0007: The owner plays by browser streaming from an AWS GPU machine

**Status:** decided 2026-10-27; the machine is the g4dn.xlarge of [0039](0039-the-play-machine-is-a-g4dn-on-demand.md).

## Context

The owner plays on an Honor Magic V5 phone and a MacBook Air M2 on which nothing can be installed. Skyrim is
PC-only, so native phone play is impossible. The owner's own idea was a GPU machine streaming to a browser, which
also gives seamless saves across devices.

## Decision

1. The game runs on the on-demand AWS GPU machine `argonia-play` ([0039](0039-the-play-machine-is-a-g4dn-on-demand.md)).
2. Sunshine streams the desktop to Moonlight-Web in a browser tab, behind Cloudflare Access; a card launches the game.
3. Access is behind authentication, never open to the world.
4. Saves live on the machine's disk and are backed up to S3 after each session; both devices see the same game.
   The machine stops itself after 15 minutes idle (no stream client and no agent job).
5. **Controls:** a Bluetooth gamepad with the phone (browser Gamepad API), keyboard and mouse on the Mac.
   Touch-only play is not a goal.
6. Latency is estimated at about 70 to 125 ms on home Wi-Fi and 85 to 150 ms on 5G, worse on 4G. No gameplay
   numbers are retuned for latency; if the owner finds it unplayable the options are a lower bitrate, a native
   Windows PC or a Steam Deck later.

## Consequences

- One target platform for agents to test, which is the same machine the owner plays on: what the agents test is
  what the owner plays.
- Video compression smears dense foliage and water.
- Data use is about 3 to 4 GB an hour; on mobile data the owner should prefer Wi-Fi.

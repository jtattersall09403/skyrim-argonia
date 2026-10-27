# Cloud dev VM and GPU game streaming: cost report

Research date 2026-10-27, carried over from the planning conversation. Spot prices come from DoIT's tracker and
change hourly, so re-check them in the AWS console before relying on them.

## 1. AWS

**CPU dev VM (eu-west-2)**
- t4g.large: on-demand $0.0752/hr, spot $0.0091/hr ([doit](https://www.doit.com/compute/compute/aws/eu-west-2/t4g.large)).
- m7g.large: on-demand $0.0944/hr, spot $0.0282/hr ([doit](https://www.doit.com/compute/compute/aws/eu-west-2/m7g.large)).
- m7g.xlarge: on-demand $0.1887/hr, spot $0.0536/hr.
- Graviton (arm64) is about 20% cheaper than x86. **Superseded for this project:** the Skyrim toolchain
  (Wine for xEdit, PapyrusCompiler, msvc-wine, BSArch, xLODGen) needs x86, so the build VM is x86
  (decision 0008).
- t4g is burstable: agents running at full CPU around the clock exhaust its credits. m7g/m7i give steady
  performance.
- With spot, set the interruption behaviour to "stop" so the disk survives a reclaim.

**GPU instances: spot (lowest AZ) / on-demand, per hour**

| | eu-west-2 | eu-west-1 | us-east-1 |
|---|---|---|---|
| g4dn.xlarge (T4) | $0.192 / $0.615 | $0.338 / $0.587 | $0.295 / $0.526 |
| g5.xlarge (A10G) | $0.481 / $1.277 | $0.646 / $1.123 | – |
| g6.xlarge (L4) | $0.361 / $1.022 | n/a | $0.472 / $0.805 |

Sources: [g4dn eu-west-2](https://www.doit.com/compute/compute/aws/eu-west-2/g4dn.xlarge),
[g5 eu-west-2](https://www.doit.com/compute/compute/aws/eu-west-2/g5.xlarge),
[g6 eu-west-2](https://www.doit.com/compute/compute/aws/eu-west-2/g6.xlarge).
All three have NVENC and support OpenGL and Vulkan. London is the lowest-latency region for a UK user.

**Storage and other charges**
- gp3 in eu-west-2 is $0.0928/GB-month ([aws-pricing](https://aws-pricing.com/eu-west-2.html)). Paid while
  the instance is stopped.
- EBS snapshots are about $0.053/GB-month in London. Restoring from a snapshot is slow at first.
- A public IPv4 address costs about $0.005/hr while attached. Internet egress is about $0.09/GB after
  100 GB/month free; a stream uses about 3–4 GB per hour.
- Start/stop takes 1–2 minutes; per-second billing with a 60-second minimum.

**AWS MCP servers for Claude Code** ([AWS Builder](https://builder.aws.com/content/39tZA5QHRDqisSTJj9dsuKV8ZZW/improving-your-aws-development-workflow-on-claude-code-with-mcp-servers))
- Managed AWS MCP, preview: `claude mcp add --transport stdio aws-mcp -- uvx mcp-proxy-for-aws@latest https://aws-mcp.us-east-1.api.aws/mcp`
- Also `awslabs.cloudwatch-mcp-server` and other awslabs servers.
- Give it a least-privilege IAM role (for example: start/stop only instances with a given tag).

## 2. Alternatives

- **RunPod**: pods from about $0.22–0.89/hr; network volume $0.07/GB-month; official MCP server
  (`claude mcp add --transport http runpod -s user https://mcp.getrunpod.io/`). **Blocker for play:** no inbound
  UDP and no /dev/net/tun, so WebRTC game streaming fails
  ([NVIDIA forum](https://forums.developer.nvidia.com/t/running-isaac-sim-in-a-browser-on-tcp-only-clouds-runpod-webrtc-livestream-cant-work-heres-a-novnc-approach-that-does/376664)).
- **Vast.ai**: RTX 3090 from about $0.21/hr; supports UDP port mapping and has a Selkies desktop template
  with TURN ([docs](https://docs.vast.ai/linux-virtual-desktop)). Third-party hosts; variable reliability.
  The fallback if AWS ever fails us.
- **Azure NV6ads_A10_v5**: $0.454/hr on-demand, spot about $0.084/hr, but only 1/6 of an A10 and scarce.
- **Google Cloud**: T4 $0.35/hr on-demand plus VM; spot 60–91% off.
- **Lambda** A10 $1.29/hr (too expensive). **Modal**: serverless, no display; fine for GPU CI, not play.
- **Paperspace**: prices unconfirmed. **Shadow PC**: Windows, native client only; no browser client, so
  no good for the locked-down Mac. **GeForce NOW**: catalogue games only.
- Hetzner is excluded by the owner.

## 3. Browser streaming stacks (nothing installed on the client)

- **Selkies** (linuxserver.io build): best fit. WebRTC with NVENC from a Linux X11 desktop; 30–100 ms
  measured in Chrome by one 2025 deployment ([e-INFRA](https://blog.e-infra.cz/blog/witcher-in-browser/)).
  WebSocket mode needs only TCP 443; WebRTC needs one UDP mux port with a TCP-443 fallback
  ([docs](https://docs.linuxserver.io/selkies/user-guide/webrtc/)). On AWS with a public IP and the UDP
  port open, no TURN server is needed. Use WebSocket/TCP-443 mode on the work MacBook (corporate networks
  often block UDP). Gamepads via the browser Gamepad API.
- **Moonlight-Web** + Sunshine ([GitHub](https://github.com/linckosz/moonlight-web)): WebRTC with WSS
  fallback, gamepad, touch trackpad and virtual keyboard on mobile. Lower latency; younger project.
- **Neko**: WebRTC, built for sharing a browser rather than gaming. **KasmVNC**: TCP only, higher latency.
  **Parsec** web client: Windows hosts only.

## 4. Software rendering for CI

Xvfb with Mesa llvmpipe (OpenGL) or lavapipe (Vulkan) gives single-digit fps on 2–4 vCPUs: enough for
scripted screenshots and logic tests, not for performance work. Pixel output differs slightly from a real
GPU. **For Skyrim this does not apply:** Skyrim under Proton/DXVK needs a real GPU, so all in-game tests run on
the GPU box.

## 5. EULA considerations

- The Steam Subscriber Agreement licenses "personal, non-commercial use" and is silent on which machine runs
  it ([SSA](https://store.steampowered.com/agreement)). Running your own copy on your own VM and streaming to
  yourself fits that. Do not let other people use the stream; no commercial use.
- Practical risks: Steam Guard prompts from a datacentre IP; online/anti-cheat titles (not relevant here).

## 6. Latency estimates (owner asked for streaming vs native comparison)

Typical cloud-gaming ranges, not measured on this setup. Measure in Phase 1.

| | Native | Streamed, home Wi-Fi | Streamed, 5G | Streamed, 4G |
|---|---|---|---|---|
| Network round trip to AWS London | – | 10–25 ms | 25–50 ms | 40–80 ms |
| Encode, decode, browser buffering | – | 25–45 ms | 25–45 ms | 30–60 ms |
| Game's own frames (60 fps) | 35–55 ms | 35–55 ms | 35–55 ms | 35–55 ms |
| **Total** | **~35–55 ms** | **~70–125 ms** | **~85–150 ms** | **~105–195 ms** |

Against a 0.1–0.29 s parry window: on Wi-Fi parrying is harder but workable; on 4G it becomes unreliable.
Video compression smears dense foliage, rain and water ripples (exactly Argonia's scenery). Streaming uses
3–4 GB/hour. With Skyrim as the host there is no native phone option (Skyrim is PC-only), so streaming is the
only route for both the phone and the Mac (decision 0007).

# Stream and combat stack for chunk 0.0 (re-check of 2026-10-28)

Research date 2026-10-28. This answers the 0.0 brief's "Re-check before starting" list and its §c and §d.
Sources are GitHub API reads, Nexus API v1/v2 reads (Premium key), AWS docs, and two AWS API reads made from
the build VM. Facts marked **verify** are not yet proven on our machine.

## Recommendations

1. **Runtime: stay on Steam 1.7.104.0.** It is what our download has (exe version 1.7.104.0, Steam build
   24914197). SKSE 2.3.1 and Address Library v13 support it. Ersh's mods (Precision, TDM, TrueHUD, OAR) and the
   doodlum "universal support" ports were rebuilt for 1.7.99+ in late August 2026. **We do not need a
   downgrade for the combat test.** Whether to pin 1.7.104 for good is a decision-0002 question; it is not
   settled here.
2. **SKSE now refuses old plugins on 1.7.99+.** It disables any address-library plugin built before
   2025-05-26 without the new `AddressLibraryV5` flag, with the message "must be recompiled for new address
   library" (skse64 `PluginManager.cpp`). So every DLL in the stack has to be a build from after August 2026.
   TK Dodge RE's own DLL (2023), IFrame Generator RE (2022), AMR (2022) and Payload Interpreter (2023) will
   **not load** as uploaded. Each has a rebuilt replacement, listed below.
3. **Dodge: DMCO plus Dodge Framework NG, not TK Dodge RE.** TDM's author warns that TK Dodge's direction is
   hard-coded to the input and goes wrong under TDM, and recommends Distar's dodge on his framework, which is
   DMCO. Dodge Framework NG (14 Oct 2026) makes DMCO load on 1.7.99 and 1.7.104. I-frames come from IFrame
   Generator RE AE Support 1.03.2. The fallback is TK Dodge RE with its 1.7.99+ replacement DLL (TK Dodge RE
   Addon 3.3.0).
4. **Moveset: SkySA 1.9.4 with Elder Souls – Sword 2.0 (MikeN1ke).** It is hand-animated by a professional
   animator. It is "inspired by" Dark Souls, not ripped (its credits name tktk1's rig), so it passes decision
   0004. It needs only behaviour files, AMR (the 1.7.104 port) and OAR, which reads DAR folders. TDM's page
   names SkySA as a good pairing. Attack-MCO 1.6.0.6 is the fallback: it has a SkySA-to-MCO converter, MCO
   Universal Support (1.7.99+) and a Payload Interpreter 1.7.104 port.
5. **Stamina-driven attacks: "OAR-added Stamina Cost for Most Actions" v5.** It is OAR config files only, with
   no DLL, so it does not depend on the runtime. Vanilla power attacks already cost stamina, and DMCO charges
   stamina for dodges.
6. **Behaviour engine: Pandora 5.0.0-beta, not Nemesis.** It can run unattended. Write
   `Pandora_Engine/ActiveMods.json` (the cache it saves after a successful run), then launch with
   `--auto_run --auto_close -o "<output mod>"` (`--tesv` if the path differs). It is still a GUI app, so it
   needs the logged-on desktop session. FNIS is not used.
7. **Stream host: Sunshine stable v2026.914.233613 rather than Apollo.** Apollo's last release is v0.4.6
   (2025-07-13). Its last commit was a security backport on 2026-05-21, so it is effectively dormant. Sunshine
   is GPL-3.0 and active (pre-releases appeared on 2026-10-28). Use the free ViGEmBus path for the Xbox 360 pad
   (see the Windows Server notes below). Sunshine's new Virtual HID Broker is paid ($14.99 a year or $49.99
   lifetime, for 5 machines).
8. **Browser client to fork: MrCreativ3001/moonlight-web-stream v3.0.1** (2026-10-26, GPL-3.0-or-later). It
   already has a stats module, gamepad with rumble, touch-to-mouse modes and a WebSocket fallback.
   **linckosz/moonlight-web is a different project** (see §1.2). It is its own capture/encode host with a
   built-in virtual display. It is worth a look as a fourth setup, but it is not the fork.
9. **DCV: 2026.0-24952 (13 Oct 2026).** It is free on EC2. It brings its own virtual display (IDD), and its web
   client does gamepad and touch. **But:** the web client is documented for *desktop* browsers only, and it has
   no QUIC (TCP/WebSocket only). On the Magic V5, treat it as "try it and record", not as a supported route.
10. **Driver: the AWS NVIDIA *gaming* driver** from `s3://nvidia-gaming/windows/latest/` (us-east-1), with
    the `vGamingMarketplace=2` registry value and the 2026 certificate. GRID is for professional
    visualisation and is not needed. **Our current IAM cannot list that bucket (AccessDenied)**, so the game
    machine's role needs read access.
11. **Instance: g5.xlarge stays the default.** It is the only one under 5% interruptions in eu-west-2 on
    Windows (§3).

## 1. Browser streaming from an AWS Windows GPU host

### 1.1 Moonlight-Web: MrCreativ3001/moonlight-web-stream (the one to fork)

- Repo: https://github.com/MrCreativ3001/moonlight-web-stream. 736 stars, last push 2026-10-26, not a fork,
  not archived.
- **Latest release: v3.0.1, 2026-10-26** (a DNS fix). v3.0.0 came out on 2026-10-22. v3 replaced
  moonlight-common-c with moonlight-common-rust ("could make older … Sunshine servers unsupported", so use
  current Sunshine) and openssl with rustls (regenerate self-signed certificates). v3 also moved the WebSocket
  endpoint to `/api/host/stream/web_socket`.
  Releases: https://github.com/MrCreativ3001/moonlight-web-stream/releases/tag/v3.0.1
- **Licence: `GPL-3.0-or-later`** (Cargo.toml and package.json; GitHub's API reports GPL-3.0).
- **Where it runs: on the Windows game machine next to Sunshine.** Release assets include
  `moonlight-web-x86_64-pc-windows-gnu.zip`; Linux, macOS and Docker builds also exist. The README's setup adds
  the host as `localhost` and pairs it with a Sunshine PIN. It could run elsewhere and reach Sunshine over the
  network, but running on the same box is simplest.
- **Transport and ports:**
  - The web UI and API default to port 8080. Use HTTPS with our own certificate: the Gamepad API, Keyboard
    Lock and WebCodecs (needed for the WebSocket path) all require a secure context.
  - WebRTC media uses a configurable UDP range (`WEBRTC_PORT_RANGE`, for example `40000:40010`).
  - STUN defaults to Google's servers. TURN can be added via `ice_servers` or `ice_server_script`.
  - With an AWS public IP and the UDP range open in the security group, no TURN server is needed.
  - **WebSocket transport** runs over the same HTTPS port, as a fallback for UDP-blocking networks. It drops
    video in bursts, using delay measured against the lowest round trip (PR #184).
  - Sunshine's own ports (47984–48010) stay local.
- **Gamepad:** Gamepad API, with rumble through `vibrationActuator` (`web/stream/input.ts`). Its controller
  state send interval can be overridden.
- **Touch:**
  - A "Touch Mode" setting maps touch to the mouse (relative, follow, point-and-drag). There is a virtual
    keyboard and a touchpad flag.
  - **There is no on-screen virtual gamepad.** Our touch layer adds one by feeding the existing gamepad
    pipeline.
- **Stats we can log:** `web/stream/stats.ts` polls every 100 ms when stats are on. It collects:
  - from WebRTC `getStats()` inbound video: `decodeTimePerFrameMs`, `currentFps`, `framesDecoded`,
    `framesDropped`, `packetsLost`, `packetsReceived`, `nackCount`, `pliCount`, `fecPacketsReceived`, codec,
    resolution and jitter;
  - on the WebSocket path: `rttMs`, `rttVarianceMs` and relay round trips.

  The WebRTC path does not report RTT. Our fork adds it from `candidate-pair.currentRoundTripTime`, and posts
  all of these to the game machine. Source:
  https://github.com/MrCreativ3001/moonlight-web-stream/blob/main/web/stream/stats.ts

### 1.2 linckosz/moonlight-web ("MoonlightWeb", moonlightweb.top): a different product

- https://github.com/linckosz/moonlight-web. Created 2026-06-22, 153 stars, last push 2026-10-28. Latest release
  **v0.4.0 (2026-10-18)**. Licence GPL-3.0. C++17/Qt 6.11.
- The README says the two projects are separate. This one **captures and encodes the PC it is installed on
  itself**, with no Sunshine and no pairing (it can also pair with Sunshine, Apollo or Wolf).
- Features:
  - NVENC zero-copy;
  - WebRTC with automatic WSS fallback;
  - touch trackpad, and Xbox/PS pads with rumble;
  - a signed "MoonlightWeb Virtual Display" for headless PCs;
  - a perf-stats overlay.
- Ports: 443/tcp, 80/tcp, and 48550–48573/udp for media.
- **Caveat:** official builds send stream "shape" metrics to `metrics.moonlightweb.top` and check for updates
  through a relay. Turn this off with `MW_NO_TELEMETRY=1` or `update_relay_enabled:false`.
- It is a possible fourth setup if Sunshine plus a virtual display is troublesome. It is younger, and it is not
  what the brief forks.

### 1.3 Sunshine vs Apollo

| | Sunshine (LizardByte) | Apollo (ClassicOldSong) |
|---|---|---|
| Latest stable | **v2026.914.233613** (2026-09-15); pre-releases v2026.1028.* (2026-10-28) | **v0.4.6** (2025-07-13); v0.4.7-alpha.1 (2025-08-12) |
| Activity | Active | Last commit 2026-05-21 (security backport) |
| Licence | GPL-3.0 (virtual-HID driver: "LizardByte Source-Available"; libvirtualhid: MIT) | GPL-3.0 |
| Virtual display | None built into Windows; use the GPU's own head or an IDD | Built-in **SudoVDA** IDD; matches the client's resolution and refresh rate per client |
| Virtual gamepad on Windows | ViGEmBus fallback (free: Xbox 360 and DS4), or the paid Virtual HID Broker (more pad types, Raw Input keyboard and mouse) | ViGEmBus |
| Windows Server | ViGEmBus installer refuses Server; install it manually | README: "Windows Server requires manual installation for gamepad support" |

- Sources:
  - Sunshine releases https://github.com/LizardByte/Sunshine/releases/tag/v2026.914.233613
  - Sunshine `docs/getting_started.md` (Windows gamepad section)
  - libvirtualhid blog https://app.lizardbyte.dev/2026-08-16-introducing-libvirtualhid-and-virtual-hid-driver/
  - Apollo https://github.com/ClassicOldSong/Apollo
- **Headless on AWS:**
  - AWS says the gaming driver supports "a single 4K display per GPU" in WDDM mode. Community AWS setups (for
    example https://github.com/tomgrice/cloudgamestream-sunshine, which targets g4dn.xlarge on Server 2019)
    capture that head directly. **Verify** that Sunshine sees a display after the driver is licensed, with the
    Microsoft Basic Display Adapter disabled.
  - If it does not, install an IDD. Apollo's SudoVDA is one, as part of Apollo. The other is
    VirtualDrivers/Virtual-Display-Driver (MIT, https://github.com/VirtualDrivers/Virtual-Display-Driver). Its
    README targets Windows 10/11 and "headless servers"; Server support is **unverified**.
  - The DCV IDD would also give Sunshine a screen, but only while a DCV session holds it. Do not rely on that.
- **Pick Sunshine.** Apollo's one advantage, SudoVDA, matters less on a single-client cloud box with a fixed
  resolution, and Apollo has stalled.

### 1.4 Windows Server gotchas (apply to every host)

- **The Xbox 360 controller driver (xusb) is not installed on Windows Server.** The DCV docs give the fix:
  1. get "XBOX 360 Controller For Windows" from the Microsoft Update Catalog;
  2. run `expand <cab> -F:* .`;
  3. run `pnputil /add-driver <inf> /install`.

  Source: https://docs.aws.amazon.com/dcv/latest/adminguide/enable-gamepad.md
- **The ViGEmBus installer blocks Windows Server on purpose.** The maintainer closed the request as "Not gonna
  happen", and ViGEmBus is now archived (last release v1.22.0, 2023-11-02). Install the driver manually with
  pnputil or devcon from the release package. Source: https://github.com/nefarius/ViGEmBus/issues/153
- Both must be in place before the X2s can reach Skyrim through Sunshine or DCV.

### 1.5 Amazon DCV

- **Latest: DCV 2026.0-24952, 13 Oct 2026.** Server 24952, web viewer 24952, Windows client 13455. New in this
  release: gamepad on the macOS client and a new native macOS client; Amazon Linux 2 support was dropped.
  Source: https://docs.aws.amazon.com/dcv/latest/adminguide/doc-history-release-notes.html
- **Licence on EC2: free.** No licence server is needed. The instance role needs `s3:GetObject` on
  `arn:aws:s3:::dcv-license.eu-west-2/*`, and Windows needs IMDS access. (The Windows Server RDS CAL point
  covers admin use and is handled by AWS's licence-included AMI.)
  Source: https://docs.aws.amazon.com/dcv/latest/adminguide/setting-up-license.html
- **Virtual display:** on Windows Server 2019+ with DCV 2023.1+, the **Indirect Display Driver is bundled**,
  so a GPU box with no monitor works. The web client's resolution is capped at 1920×1080 by default
  (`web-client-max-head-resolution`). Source:
  https://docs.aws.amazon.com/dcv/latest/adminguide/setting-up-installing-winprereq.html
- **Web client** (https://docs.aws.amazon.com/dcv/latest/userguide/client-web.md):
  - Chrome, Firefox, Edge and Safari, latest three versions, "across all major desktop operating systems".
    **Android is not listed.**
  - WebCodecs in Chrome/Edge 94+.
- **Feature table** (https://docs.aws.amazon.com/dcv/latest/userguide/client-features.md):
  - web client **QUIC: no**;
  - **gamepad: yes**: Xbox 360 or DS4 emulation, needs server 2025.0+ and the "Gamepad driver" install option;
  - **touchscreen: yes** (Firefox, Edge, Chrome).
- **Metrics:**
  - The web client shows frame rate and network latency.
  - The server exposes Windows performance counters per connection (average and minimum round trip) and per
    session (sent and dropped frames per second, display latency). The agent can log these on the host.
  - Source: https://docs.aws.amazon.com/dcv/latest/adminguide/dcv-server-connections.html

### 1.6 The AWS NVIDIA driver for Windows

- Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/install-nvidia-driver.html and
  https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-gaming-driver.html
- **Use the gaming driver.**
  - It is "optimised for gaming, updated frequently", runs in WDDM mode, and supports NVENC and DirectX.
  - It is offered for G4dn, G5, G6, G6e, G7 and G7e.
  - GRID (Quadro vWS, four 4K displays) is for professional visualisation, and its bucket is
    `ec2-windows-nvidia-drivers`. It is not needed.
- **Fetch (PowerShell with AWS Tools):**
  1. Get the objects under `Get-S3Object -BucketName nvidia-gaming -KeyPrefix windows/latest -Region us-east-1`.
  2. Copy each one with `Copy-S3Object`.
  3. Run the installer that matches the OS.

  The prefix `windows` lists every version. **Our build-VM credentials got AccessDenied listing
  `nvidia-gaming` and `ec2-windows-nvidia-drivers`.** The game machine role needs `AmazonS3ReadOnlyAccess`, or
  ListBucket and GetObject on those buckets.
- **Licensing steps:**
  1. Registry (driver 527.27+): set `HKLM\SYSTEM\CurrentControlSet\Services\nvlddmkm\Global`,
     `vGamingMarketplace` (DWORD) = `2`. Use 64-bit PowerShell; the AWS Tools shell is 32-bit and fails.
  2. Certificate (driver 591.59+): download
     `https://nvidia-gaming.s3.amazonaws.com/GridSwCert-Archive/GridSwCert_2026_03_02.cert` to
     `C:\Users\Public\Documents\GridSwCert.txt`. Drivers 576.80–581.80 use `GridSwCertWindows_2025_07_01.cert`.
  3. Reboot.
  4. `nvidia-smi.exe -q` should show "NVIDIA Cloud Gaming … Licensed".
- A custom AMI must be sysprepped for the gaming driver to work.
- Note: G7 is **not offered in eu-west-2**; only g7e.2xlarge and larger are (too big). g6f (fractional GPU) is
  GRID-only.

## 2. Skyrim SE souls-like stack for the combat test

### 2.1 Runtime

- Our copy: `~/games/skyrimse/SkyrimSE.exe`, file version **1.7.104.0**. Steam appmanifest build 24914197,
  LastUpdated 2026-10-28.
- Bethesda shipped 1.7.99 on 20 Aug 2026, then 1.7.104. That is the latest Steam build as far as SKSE knows.
- SKSE site (https://skse.silverlock.org/): "Current Anniversary Edition build 2.3.1 (game version 1.7.104)". A
  2026-08-14 banner warned of the update. The "1.9.32" on that page is classic Skyrim.
- The plugin gate is described in Recommendation 2 (source:
  https://github.com/ianpatt/skse64/blob/master/skse64/PluginManager.cpp).

### 2.2 Recommended set (Nexus SSE; all downloadable through the API)

The Nexus API with our key reports `is_premium: true`. `download_link.json` works (tested on Precision; 7 CDNs;
rate limit about 20,000 a day). All IDs are on https://www.nexusmods.com/skyrimspecialedition/mods/<id>. "1.7.x
OK" means the uploader states 1.7.99+ support, or the file has no DLL.

| # | Mod (id) | File id, name, version, date | 1.7.x OK | Needs / notes |
|---|---|---|---|---|
| 1 | SKSE64 (30379) | 795992 "SKSE64 Steam" 2.3.1, 2026-08-27 | yes, for 1.7.104 | root install |
| 2 | Address Library (32444) | 795954 "All in One (1.7.104.0)" v13, 2026-08-27 | yes | |
| 3 | SkyUI (12604) | 749043 SkyUI 6.11, 2026-05-05 | no DLL (SWF/Papyrus) | page lists 1.5.97/1.6.1170/1179; **verify** the MCM opens |
| 4 | MCM Helper (53000) | 795510 v1.6.3, 2026-08-26 | yes | needs SkyUI 6+ |
| 5 | Pandora Behaviour Engine Plus (133232) | 813165 v5.0.0-beta, 2026-10-01 | tool | GPL-3.0; headless via `ActiveMods.json` + `--auto_run --auto_close -o` |
| 6 | Open Animation Replacer (92109) | 798222 v3.2.1, 2026-08-31 | yes | + Animation Queue Fix (82395) 798212 v1.0.2 (recommended) |
| 7 | Precision (72347) | 798533 v2.0.6, 2026-09-01 | yes (2.0.5 "support runtime 1.7.99+") | Pandora patch "very strongly recommended"; needs MCM Helper, SkyUI; AMR optional (recoils) |
| 8 | True Directional Movement (51614) | 798770 v2.3.1, 2026-09-01 | yes (2.3.0) | TrueHUD for the reticle; optional headtracking Pandora patch |
| 9 | TrueHUD (62775) | 798218 v1.1.10, 2026-08-31 | yes | |
| 10 | Dodge – MCO (DMCO) (175129) | 733265 v2.1.21, 2026-03-20 | its DLL no; replaced by #11 | Pandora; BDI; IFrame Generator |
| 11 | Dodge Framework NG – 1.7.x Update (195352) | 820221 "DodgeFramework NG 1.0.0", 2026-10-14 | yes (1.7.99, 1.7.104) | overwrites DMCO's DLL; Apache-2.0; adds a "require stamina" toggle |
| 12 | IFrame Generator RE AE Support (82737) | 794617 v1.03.2, 2026-08-24 | yes | gives the roll its i-frames |
| 13 | Behavior Data Injector Universal Support (78159) | 794609 v0.13.0.4, 2026-08-24 | yes | needed by DMCO |
| 14 | AMR – Skyrim 1.7.104.0 Update (191697) | 805238 "AMR 1.5.4 Skyrim 1.7.104", 2026-09-14 | yes | full replacer for AMR 50258 (whose 2022 DLL will not load) |
| 15 | (SGC) SkySA (31390) | 203059 v1.9.4, 2021-05-12 | behaviour only + ESP | needs AMR, DAR (OAR reads DAR folders), Nemesis or Pandora; set `fInitialPowerAttackDelay=0.1–0.15` |
| 16 | Elder Souls – Sword 2.0 SE (47191) | 217554 v2.1, 2021-07-30 | animations only | load after SkySA, then run Pandora; souls-style sword set, hand-made |
| 17 | OAR-added Stamina Cost (179721) | 751119 v5, 2026-05-11 | OAR configs only | attack, block and action stamina costs |
| 18 | SSE Display Tweaks (34705) | 797175 v0.5.25, 2026-08-29 | yes ("AE 1.6.xxx, 1.7.xx") | Precision recommends it for havok at high fps; cap the frame rate for the stream |

- **Behaviour generation:**
  - Pandora is required: SkySA, Elder Souls, DMCO, and the Precision and TDM patches.
  - No FNIS. TK Dodge RE says FNIS is incompatible, and BFCO calls FNIS outdated.
  - Pandora reads "almost all" of the Nemesis format, so SkySA's 2021 Nemesis patch is the main risk.
    **Verify** it in `Engine.log`.
- What it gives:
  - roll i-frames: DMCO + IFrame Generator;
  - lock-on: TDM;
  - stamina-driven attacks, blocks and dodges: #17 + DMCO;
  - committed souls-style sword attacks: SkySA + Elder Souls;
  - real hit detection: Precision.

### 2.3 Fallbacks and what to avoid

- **TK Dodge route** (if DMCO misbehaves):
  - TK Dodge SE (15309), file 315866 "TK Dodge For RE" v3.18 (meshes only);
  - TK Dodge RE (56956), file 402680 v0.55-rc3, 2023-07-01. It supplies the behaviour patch; its DLL will not
    load;
  - **TK Dodge RE Addon (125238), file 800181 v3.3.0, 2026-09-04**, "only works for Skyrim 1.7.99+". It
    replaces the TK Dodge RE DLL; SKSE Menu Framework (120352) v3.18 is optional for its menu;
  - IFrame Generator RE AE (82737).

  TK Dodge RE's INI has `iFrameDuration`, which it passes to the behaviour graph as `TKDR_IframeDuration`.
  Caveat: TDM warns that TK Dodge's direction can be wrong under TDM.
- **Avoid on 1.7.104:**
  - TK Dodge Redux 3.6.2 (160098, built June 2026) and TK Dodge NG Redux (156666, unmaintained). Both predate
    1.7.99, and Redux is Pandora-only.
  - The unofficial Precision port (189664), now superseded by Precision 2.0.6.
  - The original AMR (50258) and Payload Interpreter (65089) DLLs.
  - SSE Engine Fixes: its 7.0.21 beta says "1.7.99 only". It is not needed for this test.
- **MCO route** (if SkySA fails under Pandora):
  - Attack – MCO (175044), file 732907 v1.6.0.6, 2026-03-19. It ships behaviours and a SkySA-to-MCO converter.
  - MCO Universal Support (85491), file 794640 v1.0.1, 2026-08-24 (1.7.99).
  - Payload Interpreter 1.7.104 Update (192679), file 809282 v2, 2026-09-22. It is DLL only, so the original
    65089 is installed for its behaviour files.
- **BFCO 3.100.11** (117052, file 808124, 2026-09-20) supports 1.7.104 (3.100.8). It is the most featured
  option, but it adds AMR, Payload Interpreter, MCM Helper, DMK (174499), XPMSSE (1988) and BFCO-format
  movesets. That is too much for one feel test.
- **Moveset permission** (decision 0004): skip packs ripped from DS3 or Elden Ring whatever their Nexus page
  says. Elder Souls' credits thank FromSoftware's animators as inspiration; the animations are MikeN1ke's own
  work on tktk1's rig. Nothing here is committed or shipped.

## 3. eu-west-2 Windows spot prices (AWS API, 2026-10-28)

From `aws ec2 describe-spot-price-history --product-descriptions Windows` and the public Spot Advisor feed
(https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json):

| Type | Spot $/h by AZ | Interruption rate (Advisor) | Saving vs on-demand |
|---|---|---|---|
| g4dn.xlarge (T4) | 2a 0.2458, 2b 0.2455, 2c 0.2455 | 10–15% | 68% |
| g5.xlarge (A10G) | 2a **0.3117**, 2b 0.4019 | **<5%** | 75% |
| g6.xlarge (L4) | 2a 0.2865, 2b 0.2868, 2c 0.4578 | 5–10% | 64% |

g5.xlarge in eu-west-2a stays the default. The main agent re-queries before launch.

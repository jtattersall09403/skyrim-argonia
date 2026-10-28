# The owner's brief (from the founding conversation, 2026-10-27)

What the owner asked for, in their own terms, plus every ruling they gave while the plan was being made.
Every line here is accounted for in [ACCOUNTING.md](ACCOUNTING.md). When this file and a later owner ruling
disagree, the later ruling wins and this file is updated in place.

## 1. What the owner wants to end up with

Something they can **play**, that is:

1. **Set in Argonia** (Black Marsh), with the stories, quests and places authored for the three.js version
   (repo `jtattersall09403/elder-souls-argonia`).
2. **Morrowind's soul.** Originally "mostly the Morrowind engine, for dialogue, quests, inventory, UI, etc.,
   adapted to our needs (content, colour themes, changes to the stats and progression system)". Restated once
   Skyrim became the host, as must-haves:
   - weapon and item classes matching Morrowind;
   - UI like Morrowind's;
   - dialogue like Morrowind's: branching topic structure, UI, writing style;
   - attributes and stats like Morrowind's;
   - levelling up like the one authored for the three.js game: resting and the **vastei** system. The owner is
     **open to merging vastei into Skyrim's attributes, levelling and perks** ("we would probably need to audit
     and mod the perks");
   - **no quest markers on maps**: quest givers give directions that are written in the journal and followed
     like verbal directions;
   - a Morrowind-style journal;
   - a Morrowind-style map;
   - cuirass, pauldrons and the other separate armour pieces ("not essential but nice to have");
   - a custom HUD.
3. **Dark Souls combat**, "hooked up to" the Morrowind-based stats and progression model ("we've already done a
   lot of the thinking on that in the argonia repo"). Source: originally DS3 (because ds3-open-re looked like
   relevant tooling); the owner **prefers Dark Souls 1 Remastered**, which they own. **Ruling: match DS1 for
   timings.**
4. **Free climbing and traversal**: "anything that's broadly like free climbing would be fine" (reference: the
   Mirror's Edge parkour-in-Skyrim video).
5. **Player-controlled boats** (research the best source).
6. **Skyrim SE or Dark Souls 3 level graphics** generally, including modern features such as volumetric or
   pseudo-volumetric fog and lighting.
7. **Minimal new art**: UI elements and minor tweaks only. Mostly extract and adapt from Morrowind (and mods
   modernising it), Skyrim SE, Dark Souls 1 or 3, and community mods "like we have been doing for skyrim so
   far". **Fal** (the owner has the MCP) may be used to make minor new art elements if needed.
8. **Reuse as far as possible**: "I really don't want to sink hundreds of dollars into this. The tools exist,
   the engine elements exist, we're just combining them in new ways and then our value add is the new
   arrangement, story, quests, setting."
9. **Distribution**: playable only if you own the base game(s). Nothing shipped that we are not supposed to
   ship (Mudcrab is the cited example of the model). The owner owns **Skyrim SE, Morrowind GOTY, Dark Souls 3
   and Dark Souls Remastered** on Steam, and other games "if relevant".
10. **Devices**: playable on the **Honor Magic V5** phone and a **MacBook Air M2**. Nothing can be installed on
    the Mac (a work machine). Open to workarounds. The owner's idea: assets and engine on a GPU VM, streamed on
    demand to a browser on phone or Mac, which also gives seamless saves across both. The owner asked for a
    comparison of streaming vs native phone play, with latency estimates.
11. **Argonia is free.** No commercial use.
12. **Immersion**: "It will be very immersion breaking for there to be Nordic design elements sneaking into
    our Black Marsh game." Wanted:
    - the Morrowind font throughout (the **Pelagiad** OpenMW version);
    - **new music**;
    - a **full audit of UI and art elements** and a complete overhaul, or tweaks to all of them so they fit the
      Black Marsh context;
    - "There will be a lot of scale to this, tonnes of elements, so we will need a good agentic approach to
      ensuring we cover everything 100%."

## 2. How it gets built

1. **All coding by Claude Code**, mostly autonomously, running on an affordable **AWS** instance. Max
   infrastructure budget **$100/month**. Not Hetzner ("very un-user-friendly").
2. Claude must be able to **test its own work in a realistic, reliable loop**, on AWS or a GPU service
   (RunPod or others were to be researched; the GPU provider must have good Claude Code compatibility, e.g. an
   MCP like RunPod's).
3. Subscription options under consideration: a **20x plan** doing a lot in parallel for ~60 h/week, or a **5x
   plan** spread over ~120 h/week (cheaper VM, cheaper subscription, less per week). The 20x plan has 4x the
   5-hour-window usage of 5x but only about double the weekly usage.
4. "As cheaply as possible."
5. The owner wants **heavy use of the universal-modder / Ghidra approach** ("people are getting great super fast
   results using them and I'm keen to learn from that experience"), applied to every system, including water.
   Repos cited: [ds3-open-re](https://github.com/garyttierney/ds3-open-re),
   [ghidra](https://github.com/NationalSecurityAgency/ghidra),
   [universal-modder](https://github.com/rehan-remade/universal-modder),
   [Ghidrust](https://github.com/oofz/Ghidrust), [Mudcrab](https://github.com/Mudcrab-Team/mudcrab). Anything
   else from Skyrim can come from Mudcrab's work where useful.
6. **New repo**: `jtattersall09403/skyrim-argonia`, **public** ("it holds us to account to make sure we never
   put anything in it that we shouldn't"). The old repo stays untouched; the owner may continue the three.js
   version separately.
7. The plan is written for the future Claude Code agent and must be complete: "every detail needs to be
   accounted for, either you are deliberately leaving it out or you're putting it in", and no petering out in
   later parts.

## 3. Rulings given during planning

| Date | Ruling |
|---|---|
| 2026-10-27 | Forget the earlier three.js-era goals as constraints; the repo is context, not rules. |
| 2026-10-27 | Skyrim as host is acceptable "in theory" provided Argonia keeps Morrowind's soul (list in §1.2). |
| 2026-10-27 | Distinguish Skyrim-as-host sub-options (classic mod vs deeper engine work). |
| 2026-10-27 | DS1 (Remastered) is the combat reference; **match DS1 for timings**. |
| 2026-10-27 | **Pin the Skyrim version.** |
| 2026-10-27 | Pelagiad font throughout; new music; full immersion audit; Fal allowed for minor art. |
| 2026-10-27 | New public repo `skyrim-argonia`; old repo left alone. |
| 2026-10-27 | AWS region **London (eu-west-2)**. The old m7i.2xlarge build box is stopped. |
| 2026-10-27 | Native phone play was "an option" to compare, not a requirement; streaming is acceptable. |
| 2026-10-27 | Use **Tropical Skyrim** (the SSE version, [Nexus SSE 78044](https://www.nexusmods.com/skyrimspecialedition/mods/78044); original [Nexus 33017](https://www.nexusmods.com/skyrim/mods/33017)) as the source for any base-Skyrim game assets: where we would use a vanilla Skyrim asset, use Tropical Skyrim's version. |
| 2026-10-27 | The owner works on the build machine through **VS Code in the browser** (vscode.dev tunnel). |
| 2026-10-27 | **Crossbows and thrown weapons are back in** (Morrowind's Marksman). |
| 2026-10-27 | **Our own original UI** for most major screens and **our own HUD**, like the old repo's, looking nothing like Skyrim's (decision 0017). |
| 2026-10-27 | The $100/month cap is for AWS infrastructure only. |
| 2026-10-27 | The owner can add the **Creation Kit** from Steam (decision 0018). |
| 2026-10-27 | Use universal-modder's and the Ghidra ecosystem's agent skills and methods wherever useful: "we really don't want to reinvent the wheel" (decision 0020). |
| 2026-10-28 | Keep the old "fast focused loops with eyes, for features and seams" way of working and its ladder (cheapest reliable check first), updated for the new infrastructure (decision 0021). |
| 2026-10-28 | The lane that builds a feature subset tests the feature **and its joins** in the same loop; no separate seam loops (decision 0021 §2). |
| 2026-10-28 | **Journeys are headless only**: getting an agent to play the game for more than a few seconds was buggy and produced harness and capture issues rather than findings (decision 0021 §3). |
| 2026-10-28 | A **studio**: something agents can drive headless and the owner can play, to drop in and teleport around the world without going through the new-game flow (decision 0022). |
| 2026-10-28 | **First, test that vanilla Skyrim can be streamed** from the AWS GPU instance to the phone and the MacBook browser, with phone controls that work (touch, and a GameSir gamepad); if that fails or is too laggy, nothing else is worth doing (chunk 0.0, gate G0). |
| 2026-10-28 | The old repo's dialogue and quest tests need overhauling: many, not all, are bad; review them against the design before reusing any (0.1 test review; 2.5, 2.12). |
| 2026-10-28 | Estimate in **agent time**, from evidence (the old repo: 16 Aug to 26 Oct 2026, 8,271 commits; Part 2 systems landed hours to a day apart), never in human coding time. |
| 2026-10-28 | **Agents stop only** when their work is complete, when a critical blocker needs the owner, or at a handover the owner asked for. No working ahead past an owner gate. |
| 2026-10-28 | **Owner inbox done properly:** one GitHub issue per owner check or owner call (issue forms, assigned to the owner, milestones per part), closed when answered; status lives in the repo. **Wake on reply:** an owner comment starts the stopped build VM through a GitHub Action (owner-only, idempotent, no duplicate machines, short-lived AWS credentials, nothing long-running in Actions), and the agent reads every new owner comment, whatever it says. |
| 2026-10-28 | **Latency and stream health are logged automatically** in every play session (our own stream client page, an in-frame input marker); the owner never records anything by hand. |
| 2026-10-28 | **Controls:** keyboard and mouse on the Mac; on the phone either the GameSir X2s (USB-C clip, used folded and unfolded, usually unfolded) or on-screen touch. **The whole game must be playable by touch**; reuse what is good from the old repo's touch controls. The Moonlight Android app may be installed on the phone as an option. |
| 2026-10-28 | **The game machine runs Windows** (spot GPU instance; the Windows licence cost is approved); the build VM stays Linux. Parallel game copies are added when loops queue, not spiked in advance. |
| 2026-10-28 | **No OpenMW fallback**: problems on Skyrim are fixed on Skyrim. |
| 2026-10-28 | **houseCARL** (Nexus SSE 181738, GPL-3.0) is the agents' standard tool for reading and diagnosing the load order (overrides, conflicts, assets, NIFs, archives, the SKSE layer, Nexus update checks), run on the Windows game machine under Mod Organizer 2. Our plugin is still generated from our data. |
| 2026-10-28 | **After G3, pause for the owner's combat test** of the souls-like mods out of the box, from a minimal studio (straight into a vanilla bandit camp). DS1 measurement (G6) and timing work (G9) run only if that test shows they are needed. |
| 2026-10-28 | **New animations may be made and shipped** where the modding scene has a gap, matched to Dark Souls by measurement and side-by-side comparison; FromSoftware's animation data is never converted or shipped. |
| 2026-10-28 | **Quests are a core system** (only left out of Part 1's thread because they are low host risk). |
| 2026-10-28 | The 0.1 old-repo review must carry over **the end goals for every system** (for example Morrowind's magic schools and spells, levitation included), keeping the goals and dropping the three.js implementation; mods, lore and lore extrapolation, stats and progression, CLAUDE.md, agents and skills each get a keep / adapt / leave verdict. The old dialogue UI is a foundation to improve, not a finished product. |
| 2026-10-28 | **Rivers:** use Skyrim's own water; sloped river sections become flat reaches with rapids and falls, regrading the terrain locally, unless research finds a usable sloped-water method. |
| 2026-10-28 | Plan in **parts** as the old repo did (slice places and systems first, then the new-game flow, then the sideways build-out), but critically reviewed for this host and rewritten as one consistent plan, not a patchwork (decision 0023). |
| 2026-10-27 | The old project's combat and animations were "quite bad and buggy": do not reproduce them. Combat is Dark Souls-like, **as close as possible to DS1 Remastered's numbers, system and feel**, wired to our stats (decision 0019). |
| 2026-10-27 | Study **OpenMW's window layouts and contents** to improve our own UI, which "still needs some work"; design the UI holistically with "eyes on" transitions in focused loops, so moving between screens is never jarring (e.g. the skill constellations) (decision 0017 §7–8). |
| 2026-10-27 | Skyrim's own UI symbols (e.g. the sneak eye) should be **loaded from the player's local Skyrim files**, not redrawn. The **trim flourishes** were made by the owner with ChatGPT and are fine to use. |

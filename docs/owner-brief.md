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
   later phases.

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
| 2026-10-27 | The old project's combat and animations were "quite bad and buggy": do not reproduce them. Combat is Dark Souls-like, **as close as possible to DS1 Remastered's numbers, system and feel**, wired to our stats (decision 0019). |
| 2026-10-27 | Study **OpenMW's window layouts and contents** to improve our own UI, which "still needs some work"; design the UI holistically with "eyes on" transitions in focused loops, so moving between screens is never jarring (e.g. the skill constellations) (decision 0017 §7–8). |
| 2026-10-27 | Skyrim's own UI symbols (e.g. the sneak eye) should be **loaded from the player's local Skyrim files**, not redrawn. The **trim flourishes** were made by the owner with ChatGPT and are fine to use. |

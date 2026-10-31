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
   timings.** **2026-10-29: map each DS1 behaviour to a tuned mod or to our own build of DS1's system,
   and decide how much to rebuild from that map** (decision 0019).
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
   ship (Mudcrab is the cited example of the model). The owner owns **Skyrim SE, Dark Souls 3 and Dark Souls
   Remastered** on Steam (Morrowind only on a lost CD, so it is not used: corrected 2026-10-28), and other games "if relevant".
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
| 2026-10-28 | **After 0.2, pause for the owner's combat test** of the souls-like mods out of the box, from a minimal studio (straight into a vanilla bandit camp). DS1 measurement (2.7 §b) and timing work (2.7 §e) run only if that test shows they are needed. |
| 2026-10-28 | **New animations may be made and shipped** where the modding scene has a gap, matched to Dark Souls by measurement and side-by-side comparison; FromSoftware's animation data is never converted or shipped. |
| 2026-10-28 | **Quests are a core system** (only left out of Part 1's thread because they are low host risk). |
| 2026-10-28 | The 0.1 old-repo review must carry over **the end goals for every system** (for example Morrowind's magic schools and spells, levitation included), keeping the goals and dropping the three.js implementation; mods, lore and lore extrapolation, stats and progression, CLAUDE.md, agents and skills each get a keep / adapt / leave verdict. The old dialogue UI is a foundation to improve, not a finished product. |
| 2026-10-28 | **Rivers:** use Skyrim's own water; sloped river sections become flat reaches with rapids and falls, regrading the terrain locally, unless research finds a usable sloped-water method. |
| 2026-10-28 | **Dark Souls animation reference (owner accepts the risk):** agents may use universal-modder's methods to derive DS1's animations as private reference (code or data that reproduces them), kept in `$ARGONIA_PRIVATE`, never committed or shipped, used only to compare and to learn how the motion was built. Our own Skyrim clips are authored independently and checked against that reference; the reference's keyframes are never copied into our clips. |
| 2026-10-28 | **Blender headless with Python** is the animation and mesh-tool route (the old repo's method); a Blender MCP server only if it proves better for a task. |
| 2026-10-28 | **SkyLink AI** (an SKSE plugin and MCP server with 74 tools for live game state: teleport, time, weather, quests, inventory, hit and other events, console with output, Papyrus calls, screenshots, save/load, load order) is evaluated in 0.3 as the base of the agent bridge, dev-only and never shipped; its cheat tools (god mode and the like) are never used in journeys or exposed in the studio panel (decision 0022). |
| 2026-10-28 | Rivers: flat reaches with frequent small rapids (and falls where the data has real drops), terrain regraded in the river corridor; agreed. |
| 2026-10-28 | **Blender: explore first, then codify.** Agents work interactively and exploratively in Blender (through a Blender MCP server, looking at what they make), and turn a sequence into a headless Python pipeline only once it is proven and needs repeating. |
| 2026-10-28 | **Build versus reuse audit:** before building any planned component, search for an existing tool or mod that already does it (SkyLink AI showed how much exists). One audit across every planned component in 0.1, then a prior-art check in every brief. |
| 2026-10-28 | **Cheats and shortcuts are allowed:** agents and the studio may use god mode, item grants, teleports, quest-stage setting and the like whenever that makes something else easier to prove or test. (Testing practice, not a ruling: the action actually under test still goes through the real game path, so a shortcut never hides the thing being checked.) |
| 2026-10-28 | SkyLink AI may be used for development; it is never redistributed, modified or otherwise. |
| 2026-10-28 | **Correction of old 0149:** it meant that combat must be part of the normal game (draw your sword anywhere and fight), not a separate "fight mode" picked from a dropdown or URL; it was never a ban on debug shortcuts. In Skyrim this holds by construction. |
| 2026-10-28 | **Setup does the one-time AWS and Steam steps** (the agent's IAM policy, the GitHub wake role, Steam downloads on the build VM); only the Steam login on the Windows game machine is left for 0.0. |
| 2026-10-28 | **One combat test** in the 0.0 play session (stock souls-like mods), not a second pause after G3. |
| 2026-10-28 | **0.3 §e runs once** (unattended, timed), not three times. 0.4's sample block includes groundcover, scatter and trees. |
| 2026-10-28 | **Agent time for Part 0 is expected to be about 12 hours** (owner's estimate, taken as the target and measured). |
| 2026-10-28 | **Re-plans:** method changes are applied and recorded without asking; a goal change becomes an owner call; plan reviews are done as one interactive review of the whole plan, never piecemeal summaries. |
| 2026-10-28 | **tes4skyrim** (MIT, pre-alpha, 2026: navmesh from collision, TES5 records from Python, LOD driving, dialogue and quest conversion) is the foundation to build on for those pieces when we reach them, alongside Mutagen, DotRecast, houseCARL and the rest (`docs/research/2026-10-28/prior-art-world-to-skyrim.md`); we do not start those from scratch. |
| 2026-10-28 | **UI goals, in order:** (1) Morrowind-style dialogue, branching topics, Morrowind-level topic counts per person, customisable persuasion; (2) a Morrowind-style pause menu with its several windows, draggable and resizable on desktop and remembered ("I loved that"); (3) one coherent design system for the whole game, thematic for Argonia, no accidental Nordic touches; (4) it looks good, worked through with the owner, using modern styling Skyrim's UI mods brought. **The approach is open** (the old three.js UI, Skyrim's UI, OpenMW's, or anything else): the UI agent reasons over the options and chooses with the owner (decision 0017, spike 1.2 §0). |
| 2026-10-28 | **Every system is built natively, not just places** (magic, stealth, crime, enemy AI and the rest): the old repo is "the guide for what goals we were *aiming for*"; none of them reached good enough, and the three.js approaches were hacky. Each goal is met with Skyrim's engine and existing tools first, "use them in better ways". The old rule code is goal evidence only; spike 1.1 §a maps goals onto Skyrim instead of choosing how to run the old code (decision 0026). |
| 2026-10-28 | **Places are rebuilt natively, the Skyrim way, from day one**, for Claywater Station and every place after it: "Really don't want to reverse engineer that whole bad patchy buggy system." The old project gives content (heightfield, designs, people, the layouts as a guide); none of its machinery (decision 0026). |
| 2026-10-28 | **Water** is Skyrim's own, tuned with Community Shaders; the old water's look is not reproduced. **Mist and volumetric light** come from Community Shaders, weather fog and placed mist. Interior sun through windows that tracks the sun is researched first; **static light beams are acceptable** if nothing better exists. |
| 2026-10-28 | **Navmesh by tes4skyrim's method first**, with the Creation Kit's generator as the check and fallback. |
| 2026-10-28 | **People carry over from the old repo** (placement, authoring, routines, services), with their dialogue rewritten by the new skills. **Whole-body templates**, never faces alone: faces and bodies mismatched before. The risk "a piece has no match in Skyrim" is dropped: every piece came from Skyrim or its mods. |
| 2026-10-28 | **tes4skyrim's MorrowindRuntime** (OpenMW's dialogue engine and script interpreter ported into SKSE, with topics, hyperlinks, disposition and persuasion) is audited in 0.1 §j as the likely base for our dialogue; 1.3 §b tries it first. |
| 2026-10-28 | **Auto-restart and auto-resume come first in 0.0** (the owner was already interrupted by a spot reclaim during setup). |
| 2026-10-28 | Plan in **parts** as the old repo did (slice places and systems first, then the new-game flow, then the sideways build-out), but critically reviewed for this host and rewritten as one consistent plan, not a patchwork (decision 0023). |
| 2026-10-27 | The old project's combat and animations were "quite bad and buggy": do not reproduce them. Combat is Dark Souls-like, **as close as possible to DS1 Remastered's numbers, system and feel**, wired to our stats (decision 0019). |
| 2026-10-27 | Study **OpenMW's window layouts and contents** to improve our own UI, which "still needs some work"; design the UI holistically with "eyes on" transitions in focused loops, so moving between screens is never jarring (e.g. the skill constellations) (decision 0017 §7–8). |
| 2026-10-27 | Skyrim's own UI symbols (e.g. the sneak eye) should be **loaded from the player's local Skyrim files**, not redrawn. The **trim flourishes** were made by the owner with ChatGPT and are fine to use. |
| 2026-10-27 | Dialogue must read "as if they were Morrowind lines", adapted to Black Marsh; the old written dialogue lines are poor and are not models; the dialogue skill starts from scratch (0024). |
| 2026-10-27 | No personification, no verbless "a dead man, under the stone lip" fragments, no dangling modifiers, nothing opaque to the player; British English punctuation; held-back information must say so; banned constructions live in one extensible list (0024, `dialogue-write/bans.yaml`). |
| 2026-10-27 | Speakers and players can each be any of the ten races; address and manner vary by player race, faction and rank (0024, `dialogue-write/voices.md`). |
| 2026-10-27 | Quests, places, dialogue, characters and facts must be consistent first time, by how they are written, not by test-and-tweak loops; quest writing and review skills, with principles per quest type from research (0024). |
| 2026-10-28 | Nearly every quest has "action" (use of the player's skills), varied and creatively combined, led by faction profile; no talk-to-X-then-Y quests. Skill output must fit what the engine needs, settled at the right point in the plan. The old repo's main quest, factions and quest system are the foundation, improved not replaced (0024 §8–9, 0.1 §i). |
| 2026-10-27 | Add a detectives' faction, rival to the assassins and thieves, its line escalating from petty crime to a grand murder-mystery finale, grounded in lore and the lore extrapolation; planned now, built at the right point (0025). |
| 2026-10-28 | The writing skills made on a side branch are brought in (0.1) and their use is built into the chunks that write quests and dialogue (1.3, 2.5, 2.12, 3.3, 4.1–4.3). |
| 2026-10-29 | **The owner plays entirely in third person.** The souls-like test and Argonia's combat, camera and HUD are designed and tested for the third-person camera. |
| 2026-10-29 | **Parry, riposte and backstab are required** for anything called souls-like, the 0.0 combat test included (Rim Parry and Execution, Nexus 114366, as before). |
| 2026-10-29 | **Combat: how far existing mods go first.** "We shouldn't build it unless we *need* to": the combat part is a deep dive into how far existing mods get with slight tweaks (e.g. the backstab on a single press, not block-then-attack), and only what genuinely needs building is built (decision 0019 revised). |
| 2026-10-29 | **Correction: not mods only.** "Map out what we can do with mods (including tuning them) and what we need to build fully from DS1's system… make informed decisions about how much of it we need to rebuild." The combat map (2.7) gives each DS1 behaviour a verdict: mod tuned, mod tweaked, or built from DS1 (decision 0019). |
| 2026-10-29 | **0.1 starts in parallel with 0.0's close-out** (owner, confident G0 will pass), in a second session: 0.1 keeps to its own paths (`tooling/`, `.claude/`, the import); the 0.0 session keeps `infra/` and the game machine; both pull with rebase before committing. |
| 2026-10-29 | **The order of importance** (opening the 0.1 session): (1) the world and the places; (2) quests, storyline, people; (3) combat closer to DS1; (4) the stats and progression model; (5) UI and dialogue. "If we only delivered the first two to high quality… with combat based on the soulslike mod stack, that wouldn't be a bad achievement." Build order need not follow it blindly: the planner was asked to think through what must come early (vastei? the UI?) and was given "license to completely change our plan" (decision 0027). |
| 2026-10-29 | **Critical review of the plan and of the old ways of working:** the plan was written by another agent and "probably not perfect yet"; the old repo was "pretty hacky" and "burned through tokens like crazy"; the 0.0 session's cheaper way of working may be better; adopt some old ways (rtk, some subagent types) but think it through (0027 §7–9, ways-of-working §6). |
| 2026-10-29 | **More Morrowind-like mods are welcome** as dependencies (Magic Expanded 133435 named), and permissively licensed UI mods may be adapted or used as a foundation for the UI (Dear Diary 23010, Wood and Paper 44174, Oblivion-like Loading Menu 38708 named); an "easy" early UI (restyle, Pelagiad) with the big overhaul later is acceptable (0027 §5). |
| 2026-10-29 | **Reply on #11:** climbing, swimming and boats go in the base mod stack from the start (FreeClimb 193552, Swimming Extensions 189821, Sailable Ship VR and SE 72070 for the MVP, then test and decide whether to build on it); Dear Diary's permissions allow it ("very permissive"); **our HUD should be early**; **the map early too**, a parchment chart in Dear Diary's style with the province outline, major roads and the major cities (Gideon, Soulrest, Lilmoth, Blackrose, Archon, Stormhold, Thorn) roughly sketched even where unrevealed, "a rough sketch map that you fill in by exploring"; stage two of the UI analyses OpenMW for what to use or be inspired by (the old Morrowind-like UI "was a bit so-so"); the licence recommendation agreed; the Morrowind corpus came from UESP so need not be private; Nexus Premium held (`NEXUS_API_KEY`); the R2 lines are in the secrets file (0027 §4–5, 0015, 0028, 1.2, 2.W4). |
| 2026-10-29 | **The land is Tropical Skyrim, built natively:** "The old repo recreated a load of stuff for how we built the land and placed everything on it and frankly it didn't work brilliantly." Terrain, textures, grass, trees, vegetation, rocks, scatter from Tropical Skyrim, not Black Marsh & Valenwood; use Skyrim's inbuilt systems and engine as much as possible, asking what must be told to the game and what it does by itself (decision 0028). |
| 2026-10-29 | **Stage one also recolours and rethemes lightly** (borders, UI elements) to the Black Marsh theme and retitles the main menu **"Argonia"** in place of Dear Diary's "Skyrim"; **later, a custom desktop shortcut with its own icon**, as Third Age: Total War launches from its own shortcut, to signal a total overhaul (1.2 §a, 3.4 §b). |
| 2026-10-29 | **0.0 fixes owed:** the dodge roll rolls in place without moving ("something has been implemented completely wrong"); install Dynamic Dodge Animation 79598 as intended with its requirements 50258 and 92109, 8-way rolls and the backstep when stationary; dodge on B only (not LB too); LB is block; RT is the heavy attack; lock-on on the right stick click (0.2 §c). |
| 2026-10-29 | **0.2–0.5 reviewed:** no time budgets; 0.2's spikes duplicated Part 1, so Part 0 is re-cut as one sequence; no installer for players now; a Starting state is the state now; the studio replaced by SkyLink and the console; journeys keep eyes; reuse existing tools before building harness (decision 0029). |
| 2026-10-29 | **A relational data model from day one:** "like 3NF or something and interlinked with primary keys… single sources of truth for everything"; the quest skills edited to match; planned early in Part 0, not built yet (decision 0030, 0.4 §0). |
| 2026-10-29 | **Unattended runs:** the owner wants to say "deliver up to and including 1.x" and have the planner orchestrate and delegate; the plan names which owner moments block (phases/README § Running unattended). |
| 2026-10-29 | **AWS cap:** October's spend (over the cap) is explained by the old project's costlier working in the month's first four weeks; the $100/month cap binds from November 2026 (0008). |
| 2026-10-29 | **The gamepad follows DS1 Remastered on Switch, by button position:** roll on the right button, R1/R2 light and heavy, L1 block, L2 parry (L1 + R1 is fine while the parry mod needs it), with Skyrim's menu, journal and wait adapted onto spare buttons. |
| 2026-10-29 | **Combat mod 28567 trialled as combat group B** beside the 0.0 stack (group A), switchable both ways; its permissions are fine for our use (owner). Group B's makeup, and whether Dynamic Dodge's 8-way rolls and Rim Parry's riposte join it, follow the evaluation (`docs/research/2026-10-29/combat-mod-28567.md`). |
| 2026-10-29 | **Permissions for every dependency mod are obtained** by the owner (O-5 and O-17 complete); the 49 drafted requests are not sent. |
| 2026-10-29 | **Parallel game machines are authorised**: whatever works best for parallelism (more machines, or more games on one), within the cost rules. |
| 2026-10-29 | **Mod 60199 (Morrowind attributes and skills) is the sheet's foundation** (permissions confirmed by the owner); its UI is restyled to our theme and UI system. |
| 2026-10-29 | **The dependency list is slimmed to what is genuinely needed** (98 rows was more than expected); every row must name the chunk that uses it. |
| 2026-10-29 | **Water is designed, never a thoughtless fallback**: rivers authored as stepped flat reaches with rapids and falls; insignificant puddles may be dropped by design; the simplest native Skyrim method that looks good wins. |
| 2026-10-29 | **The parchment chart follows the old repo's map**, which the owner liked. |
| 2026-10-29 | **In-game checks are a small, smart sample** that covers most pitfalls, not exhaustive walks. |
| 2026-10-29 | **SkyLink AI**: if our bridge gives trouble, follow SkyLink's approach as closely as possible (it worked on an earlier runtime). |
| 2026-10-30 | **Part 1 checks are headless component checks**, not playthroughs: no agent plays the quest start to finish; the building blocks and their connections are proven by state and event reads (the quest runtime's stages, the "journal updated" notice at each stage and clue, the dialogue topics granted, completion). The first-place journey is re-cut that way. |
| 2026-10-30 | **The look of the place is the owner's call** ("if you've used Tropical Skyrim and the selected mods for everything you'll be fine"); agents check Nordic tells, not feel. |
| 2026-10-30 | **The soak runs last**, after everything else, once; never as an automated or regular gate. |
| 2026-10-30 | **The planner owns** the world map fix, the screen technology choice (1.2 §0), the crocodile working in game, and the Dark Souls Combat trial (combat groups B/B2); all are in the goal. NPC sleep uses Skyrim's native way. |
| 2026-10-30 | **A creature from a mod is used as its mod designed it**: KotM's crocodile is a water ambusher, so it lives in the shallows and attacks waders, not overridden to walk. |
| 2026-10-30 | **Quest features are system-wide and native first**: the journal-updated notice (the engine's own HUD message) and thing hooks (activate/read sets a fact) serve every quest; LF83 is only the first user. |
| 2026-10-30 | **Standing permission: agents may always start and stop the game machines** ("you always have permission to do this"); a stop is never a reason to wait. |
| 2026-10-30 | **The soak is dropped** unless the owner asks for it. **Each game-machine slot runs a whole batch** of checks, not one at a time. |
| 2026-10-30 | **Decompile whenever it would be useful** (games, mod scripts, mod menus, DLLs). Game decompiles stay private and inform our own code; a mod's decompiled code may be adapted when its author or licence permits, credited (0003 §8). The stat sheet stays ours; ESLA is a pattern source. |
| 2026-10-30 | **Interiors may look Nordic**: Claywater station house (and any borrowed interior) is fine with a Nordic look; exteriors must be Tropical Skyrim, and an interior uses Tropical Skyrim's version where one exists, else vanilla as it is. (Given before; recorded late.) |
| 2026-10-30 | **Test our integration, not other modders' work**: an in-game check proves what we made (a creature present, in the right place, alive, configured; a mod wired and loaded), never behaviour a human modder built and tested (the crocodile attacking, a dodge's feel). A check must be able to fail for a reason about our work. |
| 2026-10-30 | **In-game checks are simple and in real places**: no test arenas; use real locations (Claywater and the province). The four fight checks are simplified. The one-hour road walk is dropped. |
| 2026-10-30 | **Every in-game check runs in one batch**, with the checks most likely to crash run last so they cannot block the others. |
| 2026-10-30 | **Distant terrain (LOD) is made the native Skyrim way** (the Creation Kit's own LOD generation), not with community tools. |
| 2026-10-30 | **Frame rate (#16)**: the owner plays the shaders-on and shaders-off cards once the work is finished, then decides on the machine type. |
| 2026-10-30 | **Up to 3 game machines, only when needed** (#13; the console steps done): agents reason over whether another machine gives a substantial speed or efficiency gain over one; never three by default. **Streaming stays on one machine**: argonia-play is the only one the owner streams from; extra machines are headless test machines, never in the owner's Moonlight hosts. |
| 2026-10-30 | **Agents check interactively, with eyes**: fast targeted checks are driven by an agent one action at a time, reading state and stills, adapting to variance (NPC movement, fades); what works is kept as a journey and re-driven live when red. Never long interactive playthroughs (whole quests, complicated sequences). Replaces the older 'no agent plays by looking' line, which overreached. |
| 2026-10-30 | **Respawn**: after death and after rest some enemy types respawn; each enemy record says whether it does; enemies in clearable places respawn after death or rest **until the whole place is cleared**, then never again (owner's correction, 2026-10-30: the earlier reading 'never' was the planner's error). The vastei pile stays, with a native Skyrim visual (e.g. from magic). Old-repo rulings apply (respawn-rulings.md). Old decisions: 0031 (respawn on rest; `untilCleared` reinstated for clearable places), 0037 §3, 0144, 76 §126. |
| 2026-10-30 | **LOD: keep the community tool's result** (xLODGen terrain, 33 min, automatic). Replaces the 'native CK LOD' row above; the CK run is cancelled. Re-run in the CK only if the community result looks really bad AND there is reason to believe the CK would be better. |
| 2026-10-30 | **#16: move the play machine to a g6.xlarge** (about $0.04/h more is fine), cloned from the image; London first, then another European region for latency; retire the old machine and its disk so nothing is charged twice. **The frame bar is revised**: median 60 fps best, 50 fps acceptable; 95% of frames at or above 45 fps when the median is above 50; 1% lows of 25–30 fps acceptable if unavoidable. |
| 2026-10-30 | **The loop is: check everything, then diagnose everything, then build and deploy all the fixes together, then check again** (one batch, parallel diagnosis, one deploy per round). |
| 2026-10-30 | **NPC movement is not checked in game**: walking, wandering and swimming are the base engine's own work, so the NPC-walk, NPC-sandbox and NPC-swim checks are dropped. |
| 2026-10-30 | **Machine move after things work**: get everything working on the current g4dn first, then move for frame rate. Approved: g6.xlarge in London, Paris or Ireland, or g5.xlarge at $0.31/h, whichever is available (the owner requested a G spot quota of 16 in eu-west-3 and eu-west-1). No standing retry loop. |
| 2026-10-30 | **Respawn on rest covers our own actors only** (planner, applying 0012): the rest roster is limited to our plugins' actors. **Owner (#18): the game is set only in Argonia; Skyrim's province and landmass are not in it, so vanilla actors are irrelevant; respawn follows our authored rules.** |
| 2026-10-30 | **No 'restart at this size' button**: folding or unfolding mid-session keeps the picture size until the game next starts. |
| 2026-10-30 | **Magic is mostly covered by the Morrowind spells mod** (Magic Expanded, 133435): reuse it rather than build magic. |
| 2026-10-30 | **Fix, don't defer**: anything fixable is fixed, with more rounds overnight, so the owner gets something fixed and complete in the morning; 'known issues' only for what truly cannot be fixed in time, each with why. Replaces the planner's time-box. |
| 2026-10-30 | **UI review means fix**: every screen (the dialogue window above all) is seen in game, reviewed, and every major issue fixed and re-reviewed, not only photographed. |
| 2026-10-30 | **Checks cover only what we built**: base-Skyrim behaviour is not checked (weather, swimming, enemies equipping and using their kit, NPC movement). The w3-weather-stills and water-swim checks are dropped; crash-prone checks run once, not three times. |
| 2026-10-30 | **Claywater has a trader**: the station keeper (Livia, the well-keeper) is the place's general trader; her trade service is wired the native way (vendor faction, merchant chest, a barter topic in our dialogue). |
| 2026-10-31 | **O-2 answered**: the owner is on the 20x subscription now. Open calls O-4, O-9, O-11, O-16 posted as issues #20–#23. |
| 2026-10-31 | **O-9 (#21): armour pieces stay as base Skyrim has them** (no separate pauldrons or gauntlets); the owner will look for mods later. |
| 2026-10-31 | **O-11 (#22): dialogue stays unvoiced text, but keep Skyrim's voiced barks** (the out-of-conversation lines people say aloud as you pass, in combat, idles), using Skyrim's own voice types per race; each bark's words still pass the Nordic review (0012), so lines naming Skyrim places, people or events are filtered out. |
| 2026-10-31 | **O-16 (#23): one rest banks one pending level** (the old 76 text). |
| 2026-10-31 | **#25: the agent may copy the game machine's image to Paris and Ireland** (permission added); used only if London has no g6/g5 when a machine is needed. |
| 2026-10-31 | **O-4 (#20): perks stay invisible for now**, but keep a visible Morrowind-style perk layer possible later: nothing may block it (the engine perk layer stays intact and addressable; the sitting and vastei spending keep room for a perk choice). The owner decides after playing. |
| 2026-10-31 | **#26: no traffic alarm on the play machine**; the play switch's heartbeat, idle-stop.ps1 and the night and 8 h stops stop it when idle. The argonia-play-no-stream alarm is deleted and alarm.sh no longer creates it. |
| 2026-10-31 | **#27: the play machine moves to Paris now** (g6 spot placement score 9 vs London's 4–6), the play switch redeployed for the new region (owner's OK on #27). |
| 2026-10-31 | **Agents are woken by and act on GitHub issues and comments from the owner only** (the repo is public). The planner's reply watch, the inbox tool and the wake workflow count only the owner's login without the agent marker; anyone else's text is ignored. |
| 2026-10-31 | **Round two runs one chunk per session, started by the owner with "deliver <id>"** (1.8–1.17, then 1.7; Part 1 README, the deliver skill). Agents do no substantive work between chunks; records move in the same commits as the work. The first play test's findings are in docs/research/2026-10-31/owner-playtest-1.md. |
| 2026-10-31 | **The play machine must not be interrupted often; the owner will pay a bit more, not on-demand.** 1.8 makes an evidence-based call (interruption bands, placement scores, prices, latency) before anything is switched. |
| 2026-10-31 | **#30: the play machine moves to a g6.2xlarge spot in London** (option A: the same L4 card the owner found fast in Paris, capacity score 9 in euw2-az3, band 5–10%, ~$0.49/h, ~$39 a month at 50 h with the disk). Built from a fresh image of Paris; Paris kept stopped a day as the fallback (decision 0008). Ireland has no g6. |
| 2026-10-31 | **#29: yes: the play page retries a refused start by itself for up to 2 minutes, showing "starting…".** |
| 2026-10-31 | **The GitHub "play"/"stop" comment switch is removed** (owner: "pointless"); the play page starts and stops the game machine. wake.yml keeps only waking the build VM on an owner reply. |
| 2026-10-31 | **Agents test on the same machine type the owner plays on** (owner: "obviously"): the agents' game machine is a g6.2xlarge from the play machine's image, in the same London zone; the old London g6.xlarge (argonia-play-london) is retired once its disk is kept. |
| 2026-10-31 | **The machine bar (owner; agents make the implementation calls to meet it):** (1) the owner plays on a machine under $0.50/h that meets the frame-rate and latency targets and is rarely interrupted; (2) agents test on the same machine type, also rarely interrupted; (3) agents estimate the owner's streamed experience (touch and viewports on the phone, the GameSir pad, desktop mouse and keyboard) cheaply and reliably enough to trust; latency may be estimated; (4) no duplication. Met by: g6.2xlarge London 2b for both (play_move.sh moves both to the cheapest L4 slot with capacity if the spot price passes $0.50); the stream-feel check (drive.mjs on the agents' machine, owner's network delay from their logged sessions). |
| 2026-10-31 | **The stream-feel sweep is an ability, not a regular test:** agents run it when the owner asks (the full sweep), or for only the device, input and screen their change reaches. |

# Legal and sourcing

Not legal advice. This is the line the project draws, from the research (um-ghidra-lens §5,
assets-creatures §3, skyrim-tooling §4, engine-feasibility §3) and decisions 0003, 0004, 0006.

## 1. What each source may contribute

| Source | May contribute | Must not contribute |
|---|---|---|
| **Skyrim SE** (owner-owned; players own it) | Runtime use of its records and archives from the player's install; our plugin masters it; knowledge from reading its records | Any of its files in the repo or a release (meshes, textures, sounds, voice `.fuz`, music, plugins, strings), converted or not |
| **Skyrim mods** (Nexus, ModDB) | Runtime use as player-downloaded dependencies, referenced from our plugin; open-licence code used or forked under its licence (GPL/MIT/BSD/CC, with credit) | Their files in the repo or a release unless their licence allows redistribution in a derivative and the sourcing register records it |
| **Morrowind GOTY** (owner-owned) | Knowledge: formulas, GMSTs, dialogue filter semantics, UI layout; OpenMW's GPL source as the readable reference | Any Morrowind file or text in the repo (the Morrowind dialogue exemplar corpus stays private) |
| **Dark Souls Remastered / DS3** (owner-owned) | Knowledge: measured timings and numbers written into our golden table with provenance | Params, TAE, AI Lua, animations, meshes, decompiled code, retail offsets; FromSoft-derived Nexus movesets |
| **Pelagiad** | Bundled (SIL OFL) with its licence | — |
| **Transbot9 All-Tamriel heightmap** | Apron terrain (CC BY-NC 4.0, credited, non-commercial) | Commercial use |
| **Fal** (owner's account) | Minor 2D art (icons, UI ornaments, paintings, map base) and possibly music (decision 0006) with prompt/model recorded | Use alongside a dependency whose terms forbid AI-made content, unless that author clears it |
| **universal-modder** | Vendored skills and notes (MIT, credited) | — |

Bandai Namco's EULA forbids reverse engineering and derivative works; reading and measuring our own copy for
knowledge is the low-risk part; copying is excluded. Bethesda's Creation Kit EULA: personal, non-commercial,
for use with the product, for owners of authorised copies; ZeniMax receives a licence to the mod; a "not made,
distributed or supported by ZeniMax" notice is required (P10). SKSE-style plugins have been tolerated for over
ten years. Steam: personal, non-commercial use; streaming one's own copy to oneself fits; no one else uses the
owner's stream. DRM is never bypassed (no Goldberg or similar emulators).

## 2. Permissions to request (owner call O-5; drafts in P2-WP2.2)

| Author / mod | Why we need it | Terms as researched |
|---|---|---|
| dalecallen1987, Black Marsh & Valenwood (ModDB) | the house style: 12.8k NIFs (architecture, swamp trees, creatures) | no permissions stated; bundles third-party resources (Mihail creatures; one `swamp house.nif` reportedly from Sniper: Ghost Warrior 2) |
| Soolie, Tropical Skyrim (Nexus 33017) and the SSE port's author (Nexus SSE 78044) | the base-asset layer (decision 0006 §8) | "must contact me and obtain permission… using its contents in your own mod"; bundles GKB Green Trees, Muppetpuppet's Moonpath foliage/creatures, Tamira's New Plants, Birds of Skyrim, lookout21 textures |
| MihailMods | crocodiles, wamasu, voriplasms, naga, river trolls, guars… | "not allowed to convert to other games" (not our case: we use them in Skyrim); "usually authorizes" when asked |
| pancake0723, King of the Murkmire (SSE 190459) | Saxhleel clothing, Murkmire bodies, wamasu robe | free for free mods **that do not make use of AI**; no plugin redistribution; no voice use |
| NorthwindBlue, DarthVitrial, Argonian Xanmeer Tileset (SSE 181193) | Argonian ruins (85 modular meshes) | ask |
| Sign of Cipactli author (Here There Be Monsters, 35933) | Argonian architecture, Kothringi/Xanmeer/Legion/Naga armour, creatures | confirm the URL; ask |
| Tamriel Worldspaces – Argonia author (Nexus 118678) | our heightfield's origin | ask (we ship derived heights in our plugin) |
| Every manifest row whose terms say "ask", or forbid AI | per row | per row |

Until a reply arrives, a mod may be used in private development on the owner's own machines (the owner owns or
has downloaded it); it may not be listed as a public dependency in a release without clearance.

## 3. The sourcing register

`data/sourcing-register.json`: one row per dependency and per asset we choose to use from it: source URL, file
ids, version, hash, licence text summary, AI clause, permission status and evidence (link to the reply), credit
line, which of our records use it. Every change that uses a new asset adds its row in the same commit (old
project rule). The release credits are generated from it.

## 4. Fal-made content

Each Fal output gets a register row: prompt, model id, date, our file path, the dependencies it appears beside
(to catch AI-clause conflicts). Fal output is our own file and may be committed if it is 2D UI art under the
size allowlist.

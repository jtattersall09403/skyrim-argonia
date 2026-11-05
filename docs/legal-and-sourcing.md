# Legal and sourcing

Not legal advice. This is the line the project draws (decisions 0003, 0006, 0015).

## 1. What each source may contribute

| Source | May contribute | Must not contribute |
|---|---|---|
| **Skyrim SE** (owner-owned; players own it) | Runtime use of its records and archives from the player's install; our plugin masters it; knowledge from reading its records | Any of its files in the repo or a release |
| **Skyrim mods** (Nexus, ModDB), BM&V included | Runtime use as player-downloaded dependencies, referenced from our plugin; open-licence code used or forked under its licence (GPL/MIT/BSD/CC, with credit) | Their files in the repo or a release; use against their stated terms |
| **Morrowind** (the owner's copy is a lost CD; not used as a game) | Knowledge: dialogue structure and style, from the old notes and OpenMW's GPL source | Its files or text |
| **Fal** (owner's account) | Minor 2D art if ever needed, with prompt and model recorded | Use beside a dependency whose terms forbid AI-made content |

Bethesda's Creation Kit EULA: personal, non-commercial, for owners of authorised copies; a "not made,
distributed or supported by ZeniMax" notice is required on release. Steam: personal use; streaming one's own
copy to oneself fits; no one else uses the owner's stream. DRM is never bypassed.

## 2. Permissions

The owner holds permission from the authors of the mods used (ruled 2026-10-29: "permissions for every dependency
mod are obtained by the owner"). Black Marsh & Valenwood (dalecallen1987, ModDB) states no permissions and
bundles third-party resources (Mihail creatures among them); King of the Murkmire's terms forbid use in mods
made with AI; the owner confirmed BM&V's permissions on 2026-11-01. A new mod is used in private development
on the owner's machines at once; it is listed as a public dependency of a release only with clearance, recorded
in the register.

## 3. The sourcing register

`mods/sourcing-register.json`: one row per dependency: source URL, file ids, version, hash, licence summary,
AI clause, permission status and evidence, credit line. Every commit that first uses a mod adds its row. The
release credits are generated from it.

## 4. Our own licence

GPL-3.0-or-later for code and CC BY-NC-SA 4.0 for our original content (decision 0015); third-party files keep
their own licences.

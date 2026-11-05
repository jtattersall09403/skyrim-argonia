# mods

The mod stack Argonia plays on: vanilla Skyrim SE 1.7.104.0 (Steam build 24914197, SKSE 2.3.1), plus the rows of
`dependencies.json`. No archive is ever committed (decision 0003); they live in `~/.argonia/mods` and the private
cache `s3://argonia-private-050977237313/mods/`.

## The manifest

`dependencies.json` holds one row per mod: id, name, group, source (Nexus mod/file, GitHub release, or `vault`
for a manual download held only in the private cache), version, why, the licence and permission fields, and the
archive's sha256. Groups: `core` (script extender, fixes, frameworks, USSEP, the TDM/TrueHUD lock-on), `combat`,
`traversal` (FreeClimb), `magic` (Magic Expanded), `world` (Black Marsh & Valenwood, the default world), `start`
(Alternate Start), `dev` (houseCARL, laid only with `--dev`). Row order is load order; `plugins` lists the result.
A `check` field is an open question to answer before the row is trusted. `sourcing-register.json` records every
mod and tool we depend on.

## How a mod reaches the play machine

1. `infra/gpu-box/stack.py fetch [--record]`: each archive from `~/.argonia/mods`, else the S3 cache, else the
   Nexus v1 API (`NEXUS_API_KEY` in `~/.argonia/secrets.env`). `--record` writes a new row's sha256.
2. `stack.py stage`: unpack each row into the MO2 profile, apply its FOMOD picks and ini settings.
3. `stack.py push`: send changed mod folders and the profile to `C:\argonia\MO2` on argonia-play.
4. `stack.ps1 on` on the machine lays the profile over bare Data (`off` is the exact undo);
   `stack.py install` runs all of it, then Pandora, the animation-data patch and the main-menu check.

## Combat: the collection, out of the box

The combat group is Nexus collection xyf1u3 "Soulsborne Combat"
(https://www.nexusmods.com/games/skyrimspecialedition/collections/xyf1u3), one row per mod, with these changes
for 1.7.104: DAR is replaced by Open Animation Replacer (it reads DAR folders), Nemesis by Pandora, Address
Library is v13 for 1.7.104, AMR and Payload Interpreter carry their 1.7.104 DLL rebuilds, USSEP is the current
4.3.9c. Stop On Slash and Elden Counter are AE-era DLLs: confirm each loads on 1.7.104 (`stack.py menu` lists
every DLL's load) or find the 1.7.x build.

## Shutting vanilla down

The vanilla-shutdown list in `docs/decisions/0012` is the spec for PLAN Phase 1's "shut the vanilla systems down"
step; that phase writes `mods/allowed-quests.json`, the quests that may still run (the mods' controller and MCM
quests, Live Another Life's, BM&V's), and proves the rest stopped.

## Staging notes (Phase 1, 2026-11-05)

- Row order is load order and masters must precede dependants: SkyUI sits before MCM Helper (stage refuses the other order).
- AMMCO: the Distar/Default edit is staged (walk-pace speeds); see the row's `install_note`. SmoothCam: FOMOD default lays the .esp only. Sweep Attacks: nested Data folder, one standalone ESP.
- `stack.py stage` result: 51 mods, 21 plugins, 5993 files (53 rows; two rows are not in the play profile).

# Phase 1: what is left before the owner's walk

Ticked as each step is done (owner, 2026-11-06). The phase's brief is [1-stack-in-bmv.md](../1-stack-in-bmv.md).

## The install (`stack.py install` on the play machine)

- [x] Stage the profile on the build VM: 52 mods, 22 plugins, 51,278 files
- [x] Prove BM&V complete: all 45,272 files of both archives laid
- [x] Close any running game so its files can be replaced
- [x] Send BM&V to the machine (21 GB in 1 GB parts, joined there into one archive)
- [x] Unpack BM&V into its mod folder: all 45,272 files laid
- [x] Unpack the rest of that batch (the mods with non-ASCII file names included)
- [x] Send and unpack the remaining changed mods: 2 of 54 had changed (bmv, xpmsse)
- [x] Send the profile (load order, plugin list), the tools and the root files (SKSE's loader)
- [x] Reset Skyrim's Data folder to vanilla (`stack.ps1 off`)
- [x] Run Pandora on the machine: 21 behaviour files from 10 mods (it now runs over SSH; the desktop session it used
  to need does not exist on a freshly booted machine)
- [x] Patch the animation data Pandora leaves out: 12 dodge clips added; pandora-output and Data match

## After the install

- [x] Compile our two scripts on the machine with the Creation Kit's compiler: 2 succeeded, 0 errors, 0 warnings
- [x] Build `Argonia.esp`; deploy it with `Argonia.ini` and the compiled scripts; lay the profile into Data (our files
  now laid by `stack.ps1 on` itself, so Data is checkable before a launch)
- [x] Read back, never running the game:
  - [x] every laid file hashed against the manifest: 54 of 54 archives, 51,278 files, 0 bad, 0 unrecorded
  - [x] Pandora patched exactly the 10 mod components that ship behaviour patches (the dodge mod ships animations only)
  - [x] the compile log is clean and each script is laid, byte-identical to the build
  - [x] `Argonia.esp` enabled and last in `plugins.txt`, its ini beside it, all byte-identical to the build
- [x] Post the owner's walk issue: both cards, Vanilla Skyrim then Argonia (#49)

## Before the walk (added 2026-11-06)

- [x] The heartbeat collector installed (without it the play page stopped the machine 30 minutes after each start)
- [x] Auto sign-in of the Administrator at boot (owner-approved: Sunshine could start no card without a session)
- [x] Skyrim's ini files made from the game's presets (the launcher never ran on this machine; every card failed)
- [ ] **In progress:** warm the Community Shaders cache to the main menu (owner's request), and read every DLL's load in SKSE's log
- [ ] Tell the owner on #49 the machine is ready


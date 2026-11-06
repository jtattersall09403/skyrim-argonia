# Phase 1: what is left before the owner's walk

Ticked as each step is done (owner, 2026-11-06). The phase's brief is [1-stack-in-bmv.md](1-stack-in-bmv.md).

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
- [ ] **In progress:** run Pandora on the machine to build the behaviour files (up to 15 minutes)
- [ ] Patch the animation data Pandora leaves out (so rolls move, not play in place)

## After the install

- [ ] Compile our two scripts on the machine with the Creation Kit's compiler (the start quest, the intro override)
- [ ] Build `Argonia.esp`; deploy it with `Argonia.ini` and the compiled scripts; lay the profile into Data
- [ ] Read back, never running the game:
  - [ ] every laid file hashed against the manifest (`stack.py verify`)
  - [ ] Pandora's output holds the collection's behaviours
  - [ ] the compile log is clean and each script exists
  - [ ] our plugin last in `plugins.txt`, its ini beside it
- [ ] Post the owner's walk issue: both cards, Vanilla Skyrim then Argonia

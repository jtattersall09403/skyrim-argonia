# Journal: LOD for ARG_Province (chunk 2.W4 §c)

What was tried, measured and learned for the LOD job (`infra/gpu-box/lod.sh`, `lod.ps1`), so nothing is lost at a
hand-off. The lane report is `docs/research/2026-10-30/lane-2.W4-lod.md`; the player's step is
`installer/steps/lod.md`.

## 2026-10-30: the tools, their flags, and the job (lane 2.W4-lod)

- **The tools and their hosts.** xLODGen beta 132 is on GitHub (`sheson/xLODGen` releases, `xLODGen.132.7z`).
  DynDOLOD 3.00 Alpha-217 and DynDOLOD Resources SE 3.00 Alpha-59 are on Nexus (68518 and 52897). dyndolod.info/Downloads
  names Nexus as the official host. All three are manifest rows with `profile: pipeline` and `install: tool`, so
  `stack.py stage` never lays them. `lod.sh tools` fetches them through stack.py's fetcher, checks the sha256,
  unpacks them and lays them under `C:\argonia\tools\<id>`. That is not `MO2\tools`, which every `stack.py push`
  wipes and replaces.
- **Licences.** DynDOLOD and its resources are CC BY-NC-SA 4.0, and the exes are MPL 1.1 as xEdit derivatives
  (`DynDOLOD-LICENSE.txt`). xLODGen is xEdit-based (MPL 1.1). Nothing of the tools or their output is shipped
  (0014 §4), so no permission is needed. If LOD were ever shipped, it would carry BY-NC-SA.
- **DynDOLOD Resources is a FOMOD.** Only `00 DynDOLOD Core Files - Required` is needed (Meshes, Textures, Scripts,
  Interface). The job links its Meshes and Textures into Data for the run and copies them into the generated mod.
  Its Scripts serve dynamic LOD, which the job does not make.
- **The flags for unattended use** (all three tools are xEdit builds; the switch table is read from the exes'
  strings and checked against xEdit 4.1.6's source):
  - `-sse`: the game mode (or the exe's name).
  - `-o:"<dir>\"`: the output folder (never Data, a mod folder or Overwrite).
  - `-d:"<Data>\"`, `-p:"<Plugins.txt>"`, `-m:"<My Games ini folder>\"`: the data, load order and INI.
  - `-autoload`: skips the plugin selection list (xEdit `xeInit.pas`; in both DynDOLODx64 and xLODGenx64).
  - `-autoexit`: closes when a scripted run ends. Not used: it does not get past the options dialog.
  - `-lodgen`: the LODGen tool mode (xLODGen also takes it from its exe name).
  - **No switch picks a worldspace, a preset or Start.** In xEdit's source, `mniNavGenerateLODClick` builds the
    options dialog (`TfrmLODGen`) and calls `ShowModal` with no unattended branch. Only Tamriel (0x3C) is checked
    by default, or the single worldspace if there is one. DynDOLOD's and TexGen's own windows (wizard, Advanced,
    Low/Medium/High, OK, Start, Exit TexGen, Save & Exit) are likewise GUI only. The dyndolod.info Command Line
    Argument page lists paths only. A Step forum answer agrees: "GUI settings can't be passed on the command line".
  - So **each GUI step is a named blocker for headless use**: the options dialog has no command-line equivalent.
    The job does not click like a person. `lod.ps1` drives the dialog by window messages in the desktop session:
    BM_CLICK, BM_GETCHECK, LB_SETCURSEL plus WM_CHAR space on the TCheckListBox, and WM_GETTEXT on the message
    memo. It finds each control by class and caption, dumps every window to the log before touching it, and stops
    on any unknown pop-up. Sky-Claw issue #661 proved the same route on DynDOLOD Alpha-209 through UI Automation
    (Advanced, OK, Save and Exit; Start, Exit TexGen).
- **The settings persist** in `%LOCALAPPDATA%\Skyrim Special Edition\Plugins.SSEviewsettings` under
  `[SSE LOD Options]` (xLODGen README), apart from the worldspace checks. A seeded file could replace most clicks
  once the keys are read from a first run.
- **The profile.** `stack.py stage` now always lists `Argonia LOD (generated)` (just below pandora-output) and keeps
  it from deletion. `push` never sends it, and `stack.ps1 verify` counts its files as machine-made, as it does
  Pandora's. So `make deploy` keeps the LOD on the machine, and `lod.ps1 prepare` empties it for a fresh run.
- **The machine:** argonia-play is a g4dn.xlarge with 16 GB and 4 vCPU, the player-PC proxy the 0014 §4 rule names.

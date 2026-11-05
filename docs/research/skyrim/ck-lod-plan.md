# CK LOD generation for ARG_Province: the most automatic route (read-only research, 2026-10-30)

## Live docs and the one to edit
Covered by: `docs/research/journals/lod.md` and `lane-2.W4-lod.md` (xLODGen/DynDOLOD route, window-message driver `infra/gpu-box/lod.ps1`),
`docs/decisions/0018` (CK interface = files, switches "where they exist", GUI automation), `docs/research/2026-10-28/prior-art-world-to-skyrim.md:86`
(CK steps named, unverified). This note SUPERSEDES the tool choice in lod.md/lod.ps1 after the 2026-10-30 owner ruling (CK native LOD).
Doc to edit: `docs/research/journals/lod.md` (add a CK section; drop xLODGen/DynDOLOD rows when the CK route is proven). `installer/steps/lod.md` follows.

## Findings
1. **No CK command-line switch for LOD is documented anywhere I could reach. FALSE for `-GenerateLOD`, `-GenerateWorldspaceLOD`, `-GenerateLODTextures`.**
   Switch lists found (gamesas thread "creationkit.exe command line parameters"; a CK-wiki talk list; ck.uesp "How to generate voice files by batch"):
   `-OptimizeMasterFile -ExportDialogue -GenerateLips[:plugin] -GenerateSingleLip -ExportFaceGenData -TagifyMasterfile -ExportText -CompileTextExport
   -DelocalizeMasterfile -SaveDefaultPlugin -CheckInPlugin -DumpNeededFiles -OptimizeDLC -GenerateSEQ -GenerateWarnings -BuildShaderList -Install`.
   No LOD name. CKPE README and wiki (Home, FAQ, Loader, Plugin) document no switches; CKPE is configured by `CreationKitPlatformExtended.ini`.
   Caveat: ck.uesp.net, skyrimck.uesp.net and the Nexus forum returned HTTP 403 to fetches, so the UESP "Command Line Arguments" page itself was not read
   (I did not work around the block); the list comes from search snippets of it. Strings in the real CreationKit.exe could settle it (below, step 0).
   Fallout 4's CK has extra switches (precombine/previs), none for LOD.
2. **LOD is the CK's GUI: World > World LOD** (CK wiki "Creating a Custom Worldspace with LOD"; Hoddminir blog 2012; Nexus threads). The dialog picks the
   worldspace and the kinds: terrain meshes and textures, "Generate Statics Objects" (object LOD), Tree. The LOD-data options exist only for a worldspace with no parent
   (CK wiki "World Menu"). So the most automatic route is the lod.ps1 route: start CK, load plugin, then drive the dialog by window messages (Win32 controls: BM_CLICK, BM_GETCHECK, WM_GETTEXT),
   logging every window and stopping on an unknown pop-up (planner ruling, journals/lod.md). UI Automation (records_jobs.ps1 ckload) is the fallback.
3. **Inputs the CK needs** (CK wiki; Hoddminir; Nexus "new worldspace" thread):
   - `Data\LODSettings\ARG_Province.lod` (ours: `infra/gpu-box/lodsettings.py`, 16 bytes: SW x,y int16; stride, min 4, max 32 int32). Without it nothing shows in game (Hoddminir).
   - Plugin set loaded with masters; ArgoniaWorld.esm active (it holds the worldspace; Argonia.esm is its dependant). CK may mark an ESM active (navmesh_ck.ps1 relies on it; UNPROVEN here). Load both and set Argonia.esm active only if you need its REFRs; the objects LOD reads REFRs of every loaded plugin.
   - Object LOD needs each model's LOD NIF (`*_lod.nif`/`_lod_flat.nif` beside the model, or the base record's LOD model fields), and the CK's source TGA/LOD textures (Hoddminir: "source" TGAs for landscape; a Nexus thread had static-object LOD erroring until LOD meshes were extracted from the Meshes BSA). Tree LOD needs `_lod_flat.nif` per tree (CK wiki Talk).
   - Render window enlarged in `SkyrimEditorPrefs.ini` (CK wiki: needed for the background texture process; I did not get the key names, take from the wiki or the first run).
   - Old LOD output cleared first (CK wiki).
4. **Outputs** (Hoddminir; CK wiki): `Meshes\Terrain\arg_province\*.btr` (levels 4, 8, 16, 32; all needed, 32 builds the world map), `Textures\Terrain\arg_province\*.dds` (+ `_n`), object LOD `.bto` under `...\Objects`, tree LOD `.btt` under `...\Trees` (names of the last two UNVERIFIED; confirm on the first run).
5. **Pitfalls.** CK worldspace-wide operations crash often: reports that generating worldspace LOD/PreVis "reliably crashes" the CK (Nexus 2020), with the workaround of loading a small interior cell first and generating with that loaded (Nexus). Restarting after a crash resumes; "Clear Scratch Files" cleans partials (Hoddminir). Crash right on Generate for some terrain texture options (CK wiki talk World Menu). Trees beyond +/-32 cells from origin: the CK cannot make them (Hoddminir) - check our cell range vs the origin. CKPE (SSE 1.5.73.0 build, with Address Library `CKPEBins\version-<ver>.bin`) is the standard stability fix; no source says it fixes LOD, so treat it as needed-but-unproven. Our dependencies.json has no CKPE row; the CK itself is on the game machine (ckload works). CK writes via a 32-bit-style memory budget in the original, SSE CK is 64-bit; no number found. A 16x16 test world took "several hours" in the CK (Hoddminir, 2012 hardware); one forum quote says terrain generation uses all cores (secondhand).
6. **Time on 4 vCPU g4dn.xlarge: no measured or sourced figure for SSE.** Planning estimate only: 2 to 8 h for terrain+objects+trees, dominated by object LOD and textures (our stride is in `lodsettings.py` output; scale by cells). First run is the measurement; record it in lod.md. Run under the GPU lock via `job_guard.sh run --gpu lod`.

## Commands
- Step 0 (cheap check that kills or confirms any switch): on the game machine,
  `powershell -c "Select-String -Path 'C:\...\CreationKit.exe' -Pattern '-Generate' -Encoding ascii -AllMatches | % Matches | % Value | sort -u"` (and with `-Encoding unicode`). Read-only; run once with the next batch. If a LOD switch exists, replace the dialog drive with it.
- Otherwise there is no single command: `CreationKit.exe` (via `ckpe_loader.exe` if CKPE is laid) started with no arguments, working dir = game folder, `CreationKitCustom.ini` as in records_jobs.ps1 (file log on), then the dialog drive below.

## Draft PowerShell step (for infra/gpu-box/lod.ps1, new `-Step cklod`; helpers Say/Dump/Find-Control/Click/Set-Check/Watch-Popups/Main-Window/Measure-Run from lod.ps1:77-177)
```powershell
'cklod' {
  $Game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'; $Data = "$Game\Data"
  $keep = 'C:\argonia\lod\kept'; New-Item -ItemType Directory -Force $keep | Out-Null
  # 1. lay: the .lod, the world plugin, our ini; set aside what stood there (navmesh_ck.ps1 pattern, restored in finally)
  Copy-Item C:\argonia\records\in\ArgoniaWorld.esm $Data -Force
  New-Item -ItemType Directory -Force "$Data\LODSettings" | Out-Null
  Copy-Item C:\argonia\lod\in\ARG_Province.lod "$Data\LODSettings\ARG_Province.lod" -Force
  Remove-Item "$Data\Meshes\Terrain\arg_province","$Data\Textures\Terrain\arg_province" -Recurse -Force -EA SilentlyContinue  # clear old LOD
  "[General]`r`nbAllowMultipleMasterLoads=1`r`n[Log]`r`nbEnableFileLog=1`r`nsFileName=C:\argonia\lod\logs\ck-lod.log`r`n" |
    Set-Content "$Game\CreationKitCustom.ini" -Encoding ascii
  $p = Start-Process "$Game\CreationKit.exe" -WorkingDirectory $Game -PassThru   # ckpe_loader.exe if CKPE is laid
  try {
    # 2. Data dialog: tick ArgoniaWorld.esm (+ Argonia.esm), Set as Active File on ArgoniaWorld.esm, OK  (records_jobs.ps1 ckload UIA code)
    # 3. wait for load: the log stops growing 20 s (ckload); then File > open a small interior cell (crash workaround, Nexus)
    # 4. World > World LOD  (WM_COMMAND of the menu item, or UIA; dump every window first: Dump $p 'worldlod')
    $dlg = Find-Control $p 'World LOD' '' 120
    Pick-World $p            # select ARG_Province in the dropdown (lod.ps1:110)
    foreach ($t in 'Terrain','Generate Statics Objects','Tree') { Set-Check $p $t $true }   # captions UNPROVEN: survey first
    Click $p 'Generate'
    Measure-Run $p { -not (Find-Control $p 'Generate' '' 1) }   # done when the progress window closes; Watch-Popups stops on unknown
    # a crash: relaunch and press Generate again (resumes); cap at 3 relaunches, then fail with the log tail
  } finally {
    Stop-Process -Id $p.Id -Force -EA SilentlyContinue
    Remove-Item "$Data\ArgoniaWorld.esm","$Game\CreationKitCustom.ini" -Force -EA SilentlyContinue
    # collect to C:\argonia\lod\out\{Meshes,Textures}\terrain\arg_province, then the Data copies are removed so the CK output is not shipped (0014)
  }
  "cklod OK"
}
```
Wrapper: `lod.sh survey ck` (start CK, dump the World LOD dialog's controls, kill it) comes first, as `lod.sh survey` did for xLODGen; control names above are guesses until then.

## Verification
- Files: `.lod` present; `Meshes\Terrain\arg_province\arg_province.{4,8,16,32}.<x>.<y>.btr` counts match `ceil(stride/level)^2` for covered blocks (L1 count test from lodsettings.py numbers); matching `Textures\Terrain\arg_province\*.dds` and `_n.dds`; non-empty `Objects` (.bto) and `Trees` (.btt); CK log has no error lines.
- In game (L4): the `lod.sh still` vantage (highest ground within 8 cells of Claywater, cell -53,3, facing NW at noon, 30 s) with LOD files laid in a profile: still must show terrain beyond the loaded grid (uGridsToLoad=5 default) with textured land, not purple/black/blank; compare against a no-LOD still from the same spot to prove the oracle is live. Check `_n` presence by flat lighting.
- Owner ruling says the output is made on the player's machine and never shipped (0014); the installer step is this script's Windows half.

## Risks
CK crash on Generate (resume and retry, small-cell workaround); dialog captions unknown; generated master as active file unproven; missing `_lod` NIFs for our Tropical Skyrim-derived statics make object LOD empty or erroring; CK terrain LOD textures use vanilla landscape tint (xLODGen exists to fix snow and mismatches); 16 GB RAM on the box; unknown run time; no switch means a GUI-driven installer step on the player's PC, which is fragile on other machines (record as the cost of the native-CK ruling).

## Recommendations
- Run step 0 (strings of the real CreationKit.exe) in the next game-machine batch; it is the only way to close the switch question since the UESP pages are blocked to me.
- Survey the World LOD dialog first (`lod.sh survey ck`), then the run, last in the batch (crash-prone, per the owner's ruling).

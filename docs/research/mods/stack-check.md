# Stack check (staged profile, read from files, game not run)

Made by `python3 -I tools/stack_check.py` on the build VM, 2026-11-05, over ~/.argonia/stack/MO2 (53 mods, 19 plugins) and out/Argonia.esp. Rules: SKSE 2.3.1 PluginManager, runtime 1.7.104 packed 0x01070680; the loader reads SKSEPlugin_Version (flags: signatures, address library, struct layout) and refuses Query-only DLLs on AE. The struct-layout bit positions are from SKSE's PluginAPI.h as remembered, so a verdict is a read of the file, not a game run. Modlist is MO2 order (first row wins).

## 1. SKSE DLLs for runtime 1.7.104 (SKSE 2.3.1 loader rules)

| DLL | mod (wins) | plugin name / version | verdict | reason |
|---|---|---|---|---|
| AnimationMotionRevolution.dll | amr-1.7.104 | AnimationMotionRevolution 1.5.4 | loads | signatures; struct-safe flag set. Shadows: amr (loads). |
| AnimationQueueFix.dll | animation-queue-fix | AnimationQueueFix 1.0.2 | loads | signatures; struct-safe flag set. |
| CommunityShaders.dll | community-shaders | CommunityShaders 1.9.1 | loads | signatures; struct-safe flag set. |
| ConsoleUtilSSE.dll | consoleutilsse-ng | ConsoleUtilSSE 1.6.1 | loads | signatures; struct-safe flag set. |
| CrashLogger.dll | crash-logger | CrashLogger 1.27.0 | loads | signatures; struct-safe flag set. |
| dTryHitStop.dll | stop-on-slash-1.7 | dTryHitStop 2.2.1 | loads | signatures; struct-safe flag set. Shadows: stop-on-slash (refused). |
| EldenCounter.dll | elden-counter-1.7 | EldenCounter 1.3.1 | loads | signatures; struct-safe flag set. Shadows: elden-counter (refused). |
| EngineFixes.dll | engine-fixes | EngineFixes 7.0.0 | loads | signatures; struct-safe flag set. |
| FreeClimb.dll | freeclimb | FreeClimb 0.2.67 | loads | lists 1.7.104 in compatibleVersions. |
| Fuz Ro D'oh.dll | fuz-ro-doh | Fuz Ro D'oh 2.6.1004 | loads | lists 1.7.104 in compatibleVersions. |
| MCMHelper.dll | mcm-helper | MCMHelper 1.6.3 | loads | signatures; struct-safe flag set. |
| msdia140.dll | crash-logger | -  | unknown | not an SKSE plugin (no SKSEPlugin_Version or _Query export). |
| OpenAnimationReplacer.dll | open-animation-replacer | OpenAnimationReplacer 3.2.1 | loads | signatures; struct-safe flag set. |
| PapyrusUtil.dll | papyrusutil | PapyrusUtil 0.0.0 | loads | lists 1.7.104 in compatibleVersions. |
| PayloadInterpreter.dll | payload-interpreter-1.7.104 | PayloadInterpreter 1.0.0 | loads | signatures; struct-safe flag set. Shadows: payload-interpreter (loads). |
| po3_PapyrusExtender.dll | po3-papyrus-extender | powerofthree's Papyrus Extender 6.5.2 | loads | lists 1.7.104 in compatibleVersions. |
| po3_SpellPerkItemDistributor.dll | spid | Spell Perk Item Distributor 7.0.0 | loads | signatures; struct-safe flag set. |
| po3_Tweaks.dll | po3-tweaks | powerofthree's Tweaks 1.17.1 | loads | signatures; struct-safe flag set. |
| SKSEMenuFramework.dll | skse-menu-framework | SKSEMenuFramework 3.14.0 | loads | signatures; struct-safe flag set. |
| SmoothCam.dll | smoothcam | SmoothCam 0.0.1 | loads | signatures; struct-safe flag set. |
| SSEDisplayTweaks.dll | ssedisplaytweaks | SSEDisplayTweaks 0.0.81 | loads | signatures; struct-safe flag set. |
| TrueDirectionalMovement.dll | true-directional-movement | TrueDirectionalMovement 2.3.1 | loads | signatures; struct-safe flag set. |
| TrueHUD.dll | truehud | TrueHUD 1.1.10 | loads | signatures; struct-safe flag set. |

Refused: none.

## 2. Masters (load order = plugins.txt, then Argonia.esp)

20 plugins checked; 0 with a problem.

## 3. Files laid by two mods (winner over loser = higher priority over lower)

| winner | loser | files |
|---|---|---|
| amr-1.7.104 | amr | 1 |
| elden-counter-1.7 | elden-counter | 1 |
| payload-interpreter-1.7.104 | payload-interpreter | 1 |
| stop-on-slash-1.7 | stop-on-slash | 1 |

- amr-1.7.104 over amr: SKSE/Plugins/AnimationMotionRevolution.dll
- elden-counter-1.7 over elden-counter: SKSE/Plugins/EldenCounter.dll
- payload-interpreter-1.7.104 over payload-interpreter: SKSE/Plugins/PayloadInterpreter.dll
- stop-on-slash-1.7 over stop-on-slash: SKSE/Plugins/dTryHitStop.dll

## Findings

- No DLL is refused and no master is missing or out of order; no fix to make.
- Each of the four shadowed pairs (amr, elden-counter, payload-interpreter, stop-on-slash) is won by the 1.7 build. The shadowed 1.6-era Elden Counter and Stop On Slash are the refused ones, so the 1.7 rows must stay above them; the old rows can be dropped (a row to drop, not done).
- msdia140.dll (Crash Logger) is a support DLL, not a plugin.
- No loose file is laid by two mods beyond those four DLLs: no .esp/.esm/.hkx overrides.
- Address Library: versionlib-1-7-104-0.bin is staged (address-library mod), so the address-library DLLs have their bin.

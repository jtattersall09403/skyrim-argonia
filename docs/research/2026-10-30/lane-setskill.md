# lane setskill

`dev-set SetSkill <skill> <value>` (e.g. `longBlade 5`) is live.

- Core rule: `seam::set_skill` (skse/core/src/seam.cpp) clamps to 0..skill_cap (100); unit-tested in test_seam.cpp.
- ArgoniaCore native `SetSkill`, script class **ArgoniaDev** (skse/ArgoniaCore/papyrus/ArgoniaDev.psc), compiled and registered only under
  `ARGONIA_DEV_NATIVES`, which ArgoniaCore/CMakeLists.txt defines only when `NOT ARGONIA_RELEASE` (windows-dev). It then
  mirrors the skills, rewrites the combat carriers and signals the facts, as SetAttribute does.
- Release proof: skse/check.sh (inside make check) fails if SetSkill is in ArgoniaCore.psc, if natives.cpp has more than
  the two guarded blocks, if it appears in any other ArgoniaCore source, or if the define is not under `NOT ARGONIA_RELEASE`.
  The release install list names no ArgoniaDev.psc. (windows-release was not built here.)
- Bridge: dev.cpp allows SetSkill (test_dev.cpp); ep_dev.cpp dispatches it to ArgoniaDev.
- Journey: fight-damage-builds novice-blow sets LB 5 (damage 10.8 +-0.5 from 2000 health), god-blow LB 100 (36.0 +-0.5);
  the owed `builds-long-blade` step is folded into them. `run_journey.py --dry`: ok. make check: CHECK GREEN.

Build windows-dev (job setskill-build4, ctest 33/33 on the box), in the box's tree, not deployed:
- C:\argonia\skse\out\windows-dev\dist\SKSE\Plugins\ArgoniaCore.dll (1733120 bytes)
- C:\argonia\skse\out\windows-dev\dev\SKSE\Plugins\ArgoniaBridge.dll (928768 bytes)

Game-13 must also compile ArgoniaDev.psc: `infra/gpu-box/records_jobs.sh papyrus` (it compiles skse/ArgoniaCore/papyrus/)
and deploy ArgoniaDev.pex beside ArgoniaCore.pex (dev mod folder only; never ship it).

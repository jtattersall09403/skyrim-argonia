# Machine moves lose nothing

The owner, 2026-10-31: the xLODGen distant terrain made on the g4dn existed only in that machine's MO2 folder,
and went when the machine was terminated in the move to the g6. "We may have to move machines again in future.
We must lose nothing in such moves."

## The rule (CLAUDE.md)

Nothing lives only on a machine. Anything a game machine makes that the repo can't rebuild in minutes is archived
to the private bucket when it is made, by the job that makes it. No machine is stopped for good, terminated,
re-imaged or replaced until `infra/gpu-box/machine_inventory.sh --machine <name>` reports nothing unarchived.

## What the inventory checks

`infra/gpu-box/machine_inventory.sh --machine <name>` is read-only: one `Get-ChildItem` listing over `run.sh ps`,
then S3 listings on the build VM. The raw listing is kept in `out/inventory/<name>.tsv` (`--replay` classifies it
again). It prints each thing only that machine has, with `archived` or `UNARCHIVED`, and exits 1 while anything is
UNARCHIVED.

| Kind | What is listed | Archived when |
|---|---|---|
| mod | an MO2 mod folder named in neither `data/dependencies.json` nor `combat-test-mods.json` (their archives are in the private bucket's `mods/`) and not built by deploy (Argonia SKSE, SkyLink (dev, rebuilt)) | for "Argonia LOD (generated)": the private bucket's `lod/` holds a tar of its size (`lod.sh archive`, run by the job that makes it); any other mod: add it to the manifest |
| save | a save that isn't ours (not argoniabase\*, ArgoniaRest, ArgoniaSuspend, quick- or autosave) | the machine's `saves.sh backup` latest.zip (or the legacy `saves/latest.zip`) has it at the same size; `run.sh stop` runs the backup |
| ck | a Creation Kit or records-job output in `C:\argonia\records\out` other than the Papyrus compile (deploy rebuilds that) | the build VM's `out/gpu` holds a file of that name and size (fetched back) |
| state | a `C:\argonia` folder that deploy, setup.ps1 or our tools don't make | never by itself: archive it, make it a `setup.ps1` step, or record why it isn't needed |
| scratch | a loose `C:\argonia` file (an agent's one-off script) | not counted; deleted or kept with the image |

Hand-made machine setup (a driver bind, firewall rules, a scheduled task) can't be seen by a listing: it is a step in
`setup.ps1`, never only a manual fix. Things the repo rebuilds in minutes (the plugin, the SKSE DLLs, Papyrus,
scenes, the base save, the manifest's mods) are not listed; `deploy.sh` and `stack.py push` make them again.

## A move, in order

1. Run `machine_inventory.sh` on the old machine. Archive anything it lists as UNARCHIVED, or record why it isn't
   needed in the move's lane report.
2. Make the new machine from the newest image, deploy, and restore the archives (`lod.sh restore`, saves).
3. Prove the owner's path on the new machine (the card, our ESMs loaded, a still).
4. Run the inventory on the old machine once more, then retire it. Its image goes only after the new machine has
   run for a day.

## The build VM's disk

The owner pays for the build VM's disk by its size (120 GB gp3, about $11 a month), so it must never need to grow.
`tooling/disk.sh report` shows what fills it, by kind; `tooling/disk.sh tidy` frees what the bucket can give back:

- **Lane worktrees** (`~/wt-*`, one per agent lane, about 0.6 GB each): one idle for 3 hours (no process inside,
  nothing changed) is archived to `s3://argonia-private-…/worktrees/<name>/` and removed. The archive holds its
  `out/` (run dirs, batches, stills; built plugins excepted), its untracked files, any uncommitted edits and a bundle
  of any commits not on origin/main. Evidence a doc cites as `wt-<name>/out/…` is at that prefix, same path.
  `tooling/worktree.sh` runs the tidy before it makes each new lane (`NO_TIDY=1` skips it).
- **Mod archives** (`~/.argonia/mods`, 16 GB): `stack.py evict` deletes each local archive once the bucket's
  `mods/` holds it with the manifest's hash; `stack.py fetch` takes it back from the bucket in minutes.

Kept on purpose: the staged mods (`~/.argonia/stack/MO2`; stack push and the UI theme build read them), the owned
games (`~/games`: Skyrim SE data for ArgoniaGen, DSR for measuring), the main tree's `out/`.

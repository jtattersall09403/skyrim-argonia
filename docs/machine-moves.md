# Machine moves lose nothing

The owner, 2026-10-31: the xLODGen distant terrain made on the g4dn existed only in that machine's MO2 folder,
and went when the machine was terminated in the move to the g6. "We may have to move machines again in future.
We must lose nothing in such moves."

## The rule (CLAUDE.md)

Nothing lives only on a machine. Anything a game machine makes that the repo can't rebuild in minutes is archived
to the private bucket when it is made, by the job that makes it. No machine is stopped for good, terminated,
re-imaged or replaced until `infra/gpu-box/machine_inventory.sh --machine <name>` reports nothing unarchived.

## What counts

| Kind | Example | Where it is archived |
|---|---|---|
| Long tool outputs | xLODGen terrain LOD (about 30 min), Creation Kit outputs | `lod.sh archive`: the private bucket, keyed by the input hash |
| Saves the owner made | `Saves\*.ess` that aren't ours (not argoniabase) | `saves.sh backup` (run by `run.sh stop`) |
| Hand-made machine setup | a driver bind, network or firewall settings, a scheduled task | a step in `setup.ps1`, never only a manual fix |
| Stack mods not from the manifest | an MO2 mod folder that `stack.py` doesn't know | `stack.py`'s manifest, or archived beside it |

Things the repo rebuilds in minutes (the plugin, the SKSE DLLs, Papyrus, scenes, the base save) are not archived;
`deploy.sh` makes them again.

## A move, in order

1. Run `machine_inventory.sh` on the old machine. Archive anything it lists, or record why it isn't needed.
2. Make the new machine from the newest image, deploy, and restore the archives (`lod.sh restore`, saves).
3. Prove the owner's path on the new machine (the card, our ESMs loaded, a still).
4. Run the inventory on the old machine once more, then retire it. Its image goes only after the new machine has
   run for a day.

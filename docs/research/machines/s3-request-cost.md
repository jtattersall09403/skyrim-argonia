# S3 request cost: EUW2-Requests-SIA-Tier1 ($1.54, 1-3 Nov 2026)

Culprit: `tooling/disk.sh archive()` (lines 38-40), run by `tooling/worktree.sh:11` (`disk.sh tidy`) on every new lane.
It does `aws s3 sync "$wt/out" ... --storage-class STANDARD_IA` (one PUT per file) and `aws s3 cp --recursive --storage-class STANDARD_IA`.
Nothing else in the repo passes a storage class (grep of infra/ tooling/ tools/ ~/.argonia/scripts).

## Evidence
- `aws s3api list-objects-v2` on s3://argonia-private-050977237313/worktrees/: 85,791 objects, 5.74 GB, ALL StorageClass STANDARD_IA.
  Every other object (mods 104, lod 5, shadercache 4, machines 6, private bucket; saves bucket 136) is STANDARD.
- LastModified of the current worktrees/ objects: 31 Oct 57,863; 1 Nov 24,169; 2 Nov 3,759. Per-lane: wt-items 8,762, wt-lscr 8,132, wt-g20 6,953, wt-chart 5,856, wt-menus3 5,625, wt-records 5,433, wt-ledger 5,432 ... (many lanes, 2-9k files each: YAML dumps under out/check, stills, run dirs).
- Only ~28k of those PUTs fall on 1-3 Nov. The rest of the ~150k is not visible: overwritten or deleted objects, re-archives of a re-created lane (sync re-PUTs changed files), and lifecycle transitions (billed in the same Tier1 line) cannot be seen with this role.
- Role argonia-build-ssm is denied s3:GetLifecycleConfiguration, GetBucketVersioning, ListObjectVersions, ListAllMyBuckets, so the bucket lifecycle and versioning are UNKNOWN. Needs the owner/admin role (or add those read actions).

## Other writers (all STANDARD, none is the culprit)
| writer | what | objects/run | frequency |
|---|---|---|---|
| infra/gpu-box/saves.sh:24-25 | saves.zip as stamp and latest | 2 | per backup (at stop, manual) |
| infra/gpu-box/lod.sh:139 | one lod.tar, twice (key, latest) | 2 | per LOD job |
| infra/gpu-box/shader_cache.sh:35 | one tar | 1 | per push |
| infra/gpu-box/archive_state.sh:27 | one tar per state file | few | on demand |
| infra/gpu-box/machine_inventory.sh:38-40 | only ls/cp download (reads) | 0 PUT | on demand |
| ~/.argonia/scripts/archive_samples.sh:6 | `s3 sync` terrain-sample dirs (one PUT per file, Standard) | 1 per file | one-off 2 Nov |
| stack.py / fetch_vault.py | head-object / mods download | 0 PUT | on demand |
No periodic or per-minute S3 writer exists: no timers (systemctl list-timers shows only OS timers), no crontab; pool.py/spot-watch/owner_watch not found writing to S3 (no s3 string in them).
I did not find pool.py beat/stamp or spot-watch.ps1 touching S3 in the grep.

## Root fix
1. disk.sh: replace the per-file sync of out/ with one tarball: `tar -C "$wt" --exclude='*.esm' --exclude='*.esp' --exclude='*.bsa' -czf "$tmp/out.tgz" out` (honour --no-follow-symlinks) and upload with the other three small files: ~4 PUTs per lane instead of 2-9k. Drop `--storage-class STANDARD_IA` (IA has a 128 KB minimum billable object size and 30-day minimum; the PUT is $0.01/1000 vs $0.005 Standard). A single tgz of several hundred MB is fine in either class.
2. Existing 85,791 objects: pack once (download-less is impossible) or just delete the YAML/stills of dead lanes; a lifecycle expiry on worktrees/ (e.g. 30 days) stops storage growth. Deleting is free of request charges for DELETE; do not add a lifecycle TRANSITION rule (each transition is another Tier1 request).
3. archive_samples.sh: same tar-first rule (one-off, already ran).
Check after: `aws s3 ls s3://argonia-private-050977237313/worktrees/ --recursive --summarize` should grow by ~4 objects per archived lane.

Covered: infra/, tooling/, tools/ (grep), ~/.argonia/scripts, live bucket listings and storage classes · Skipped: Cost Explorer itself and CloudTrail/S3 metrics (no permission), lifecycle and versioning (AccessDenied), pool.py/spot-watch internals beyond the grep.

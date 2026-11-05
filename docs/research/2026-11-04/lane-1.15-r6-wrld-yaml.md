# 1.15-r6-wrld-yaml: why plugin-check said plugin/Argonia/ was stale after make plugin

- The one differing file was the Argonia.esm WRLD override's persistent refs (map markers, bridge steps): Z/X/Y of 3 refs, taken from `GameGround()` over out/terrain (regions/api.py), so they move whenever the ground is rebuilt.
- Found: out/build/yaml (00:03) and out/check/a/yaml (00:39) both differed from plugin/Argonia/ (23:01) in exactly those 3 Positions (e.g. 4631.53 vs 4631.89).
- Cause: the `yaml-copy` stage was keyed by the ESM's sha in out/stages, which every worktree shares, while plugin/ is per tree. One tree's build wrote the key, the next tree's `make plugin` skipped the copy and left its plugin/ at the old ground (also the "unchanged" early exit never looked at plugin/).
- Fix: `sync_yaml` in tools/ArgoniaGen/pipeline.py compares plugin/Argonia/ with out/build/yaml and copies when they differ, on the full and the unchanged path; test `test_sync_yaml_follows_the_trees_not_a_shared_stage_key`.
- Measured: `make plugin` then `make plugin-check` green on the unchanged main tree. Residual risk: the ground moving mid-gate (the unit tests run terrain stages concurrently) is not guarded here.

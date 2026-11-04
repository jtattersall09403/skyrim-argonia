# 1.15-r6-shader-cache-gpu: the shader cache keyed by GPU

- Cause: deploy's "shader cache" step (infra/gpu-box/shader_cache.sh) keyed on the shader sources, CS DLL and settings only. The round-6 clone (T4, imaged from Paris's L4 disk) carried the L4's key and cache, read "current", and CS recompiled on every launch (287 s to the menu).
- Cache location: `Data\ShaderCache` under the Skyrim install (CS's compiled cache; stack.ps1 never touches it); the machine's key is `Data\ShaderCache\argonia-shader.key`. Whether CS itself stamps the GPU is not read from its log here; the clone shows the cache did not carry over, so the key now includes it.
- Key: `<12 hex shaders>-<6 hex of "name, driver_version">` from `nvidia-smi --query-gpu=name,driver_version` over run.sh ps (SHADER_GPU overrides). Dry T4 sample: 3a0e18452369-3ec449.
- Archive: `s3://argonia-private-050977237313/shadercache/<key>.tar` (the LOD bucket); `save` archives after a green launch when none exists for the key, `ensure` lays it when the machine's key differs.
- `shader_cache.sh dry` prints gpu, key, machine key, archive path, decision. `shader_cache.py decide` is the tested lay/skip rule (tooling/tests/test_shader_cache.py, 7 pass).
- deploy.sh needed no change (it calls ensure/save). Not run on the game machine; shellcheck and ruff are not installed here (bash -n clean).

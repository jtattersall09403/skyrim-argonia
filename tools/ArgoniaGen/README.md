ArgoniaGen: .NET 10 + Mutagen 0.54.4 data tool (writes Skyrim records from `world/`; reads only for now).
Run: `dotnet run --project tools/ArgoniaGen -- counts --data ~/games/skyrimse/Data` (needs `bash tooling/toolchain/setup.sh` first).
Commands so far: `counts` (record count per major type, ten largest, Skyrim.esm opened read-only as SkyrimSE).

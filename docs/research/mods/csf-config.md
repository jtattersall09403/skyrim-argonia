# Custom Skills Framework config (1.12 §4)

Source: github.com/Exit-9B/CustomSkills (MIT), read 2026-10-31: `docs/schema/CustomSkill.json`, `skill.json`,
`defs.json` and `src/CustomSkills/Settings.cpp` (the loader).

- Files: `Data/SKSE/Plugins/CustomSkills/*.json`; the file stem is the group. The stem `SKILLS` is the vanilla Skills
  menu, so our one file `SKILLS.json` puts all 27 skills in it. Root: `version` 1, `skills` (array).
- A `skills` item is either a vanilla name (Alchemy, Alteration, Block, Conjuration, Destruction, Enchanting,
  HeavyArmor, Illusion, LightArmor, Lockpicking, Marksman, OneHanded, Pickpocket, Restoration, Smithing, Sneak,
  Speechcraft, TwoHanded, ...; those keep the vanilla tree) or a skill object.
- Skill object: `id`, `name`, `description`, then GLOBs as `"Plugin.esm|HexLocalId"`: `level`, `ratio` (0 to 1),
  `legendary`, `color` (RGB, white 0xFFFFFF), `showLevelup`; `experienceFormula` (unused: ArgoniaCore owns gain);
  `nodes` (max 127): each `{perk: "Plugin|id", x, y, links}`; the first node is required even with no perks.
- **No AVIF record is needed.** `ReadSkillDef` creates the ActorValueInfo with the engine's factory and builds its
  perk tree from `nodes`. Argonia.esm therefore holds, per CSF skill, 5 float GLOBs + 1 placeholder PERK
  (`tools/argonia_world/csf_records.py`); the brief's "AVIF carrying a tree" does not exist in CSF's design.
- `ParseForm` reads the id as hex and looks it up by file name, so the local (8-bit-masked) id works for an ESM.
- Laid by `infra/gpu-box/stack.py` as the mod `argonia-csf` from `data/csf/`.
- Unproven in game: that the one-node placeholder tree opens in the Skills menu and the placeholder perk cannot be
  taken (it is level 100); the log line to read is CSF's own `CustomSkills.log` (parse errors, "Error reading skill
  configs").

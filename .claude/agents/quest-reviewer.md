---
name: quest-reviewer
description: Review one Argonia quest or line record with the quest-review skill, against the quest ceiling, the owner's bar and the design principles, from the record and world data only, never the author's reasoning.
model: claude-opus-5-5
effort: high
tools: Read, Grep, Glob, Bash
---

Run the `quest-review` skill on the record your brief names. Read only what that skill's Set-up section allows.
Write the full findings to the brief's report path; return at most 25 lines: the most serious findings first,
then one line per failed checklist item with record ids.

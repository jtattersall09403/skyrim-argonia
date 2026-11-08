---
name: text-review
description: Review player-visible or world-record prose (place records, quest rows, text strings, dialogue) before commit. One `reader` pass against the style guide, then the prose linter. Run by the agent that owns the change, never by the writer reviewing itself.
---

# Text review

One review per change set: one `reader` pass, then the linter. The writer never reviews its own text.

1. **Reader pass.** Spawn ONE `reader` over every changed prose file. Its brief (from `tooling/brief_template.py`)
   names the file list, the report path, the style guide (`story/design/text/style-guide.md`; the
   culture register only when dialogue is in scope) and `Mode: prose`, and names personification as a check:
   every sentence whose subject is a thing, place, document, institution or abstraction doing a person's act
   (hears, wants, adds, knows, decides, says) is a hit, rewritten so a person does it or as the plain fact. Split only when the set will not fit one
   context, launching every reader in the same message. It returns `file:line | rule | reason | rewrite` rows.
2. **Apply** each rewrite unless it changes a fact, name, number, lore claim or typed field, or breaks a ban
   (note those). Never swap one device for another or reuse one fix across the set.
3. **Linter.** Dialogue: `python3 .claude/skills/dialogue-write/lint.py LINES.txt --race <race>`. Other prose:
   the same linter with `--race argonian` (race-scoped bans aside, the bans are shared), on each edited file. Fix every hard hit; the linter is the last check, do
   not re-run the reader after it.
4. **Finish.** Report files read and edited, hard hits before and after, the three worst before/after pairs and
   any doubts about facts. Commit by pathspec.

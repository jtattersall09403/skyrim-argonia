---
name: text-review
description: Review player-visible or world-record prose (place records, quest rows, text strings, dialogue) before commit. One `reader` pass against the style guide, then the prose linter. Run by the agent that owns the change, never by the writer reviewing itself.
---

# Text review

In the quest path ([quest-system](../quest-system/SKILL.md)) this follows dialogue-write and comes before the paper playtest of the written quest; its truth reader runs again once the quest is built.

One review per change set: one `reader` pass, the truth pass for quest and talker text, then the linter. The writer never reviews its own text.

1. **Reader pass.** Spawn ONE `reader` over every changed prose file. Its brief (from `tooling/brief_template.py`)
   names the file list, the report path, the style guide (`story/design/text/style-guide.md`; the
   culture register only when dialogue is in scope) and `Mode: prose`. For dialogue and journal text the brief names
   these checks, each a hit with a rewrite:
   - personification: a thing, place, document, institution or abstraction doing a person's act (hears, wants, adds,
     knows, decides, says);
   - a question or demand put to the player with no reply topic listed beside the line;
   - an offer, hand-over or promise with no `sets` listed beside the line;
   - a fact two speakers of the same place and stage window both state;
   - a noun for a place, prop or scene that is not in the quest's hosts and things;
   - a pronoun that disagrees with the person's listed sex; a person named by role where a name is listed;
   - a prompt that is a bare label, not a sentence the player would say;
   - a sentence that does not parse on a slow read (a verb doubled, a referent missing).

   Dialogue is reviewed as a table from the database, one row per line with its speaker, place, stage window, prompt,
   reply topics and `sets`, grouped by place, never as bare text files. Split only when the set will not fit one
   context, launching every reader in the same message. It returns `file:line | rule | reason | rewrite` rows.
2. **Truth pass** (quest and talker text, once the plugin is built). Read the forms back
   (`plugin.sh questform-read out/questform-read`), then per quest or settlement build the input with
   `python3 -m tools.argonia_world.truth_brief <quest id | settlement id> --out BRIEF.md`: every line, journal entry,
   objective (and a talker's stated trade) beside the surroundings sheet of its speaker and of each person or thing
   it names (`python3 -m tools.argonia_world.surroundings <ref or id>`: what stands there by what it reads as, the
   ground, the water, who is near and whether they move, what the game does not do). Spawn one fresh `reader` per
   quest or place, never the writer, all in one message, each told to read BRIEF.md and do what it asks. It writes
   `story/design/quests/review/truth/<quest>.md`: every claim about the place, a thing's position, someone's work, an
   event in progress or a game system that the sheet does not support, and every thing placed by "us" or "here"
   instead of by something fixed, each with the sheet's fact and a true rewrite. Fix each at its source, one way
   only: the line (through dialogue-write's change of a line), or, where the words should stand and the change is
   inside the quest ceiling's world edits (a person standing, a thing on a surface, moved a few steps), the
   placement. Note under each row how it was fixed, or why it stands.
3. **Apply** each rewrite unless it changes a fact, name, number, lore claim or typed field, or breaks a ban
   (note those). Never swap one device for another or reuse one fix across the set.
4. **Linter.** Dialogue: `python3 .claude/skills/dialogue-write/lint.py LINES.txt --race <race>`. Other prose:
   the same linter with `--race argonian` (race-scoped bans aside, the bans are shared), on each edited file. Fix every hard hit; the linter is the last check, do
   not re-run the reader after it.
5. **Finish.** Report files read and edited, hard hits before and after, the three worst before/after pairs and
   any doubts about facts. Commit by pathspec.

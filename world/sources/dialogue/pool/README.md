# Dialogue pool

The only home of a fact a line states (decision 0139): the canonical answer
per topic and condition set. One file per topic class, `<topic-class>.json`
(`local role faction people region rumour newcomer quest service`), plus
`greetings.json` for the pool greetings. Topics live in
`../topics.json`, the glossary and its load-bearing nouns in
`../glossary.json`.

A file is `{schemaVersion: 1, domain: "dialogue-pool", topicClass, entries}`;
each entry is a content unit (standard 11, quests/85 § C):

| field | meaning |
| --- | --- |
| `id` | `pool.<topic-slug>.<slug>`; the class fallback is `pool.fallback.<class>` |
| `type` | `dialogue` (`greeting` in `greetings.json`) |
| `speaker` | `null`: pool lines are authorless |
| `keys.topic` | the topic answered (absent on a fallback) |
| `words` | the line; compiled to `text.dialogue.<id>` in the catalogue |
| `available` | quests/85 § A conditions, all must hold; their count is the specificity |
| `onDelivered` | quests/85 § B actions |
| `factIds` | the facts stated, ids in `../facts.json` (`{id, says, cues}`: what the fact is and the words that show a line states it); required on newcomer, faction and role lines, each cue in the words; the player learns them on delivery |
| `links` | the topics the line opens |
| `fallbackFor` | on the one unconditional line per class that answers any topic of it |

Greetings carry `fallback: true` on the one unconditional pool greeting.

Add entries only with `python3 -m worldgen.dialogue_pool add --file <file>
--entries <json>` (locked, re-read, refuses an existing id); never rewrite a
file from an in-memory copy. Compile with `python3 -m worldgen.dialogue_lines --write --pool` (cwd
`tooling/world-generation`); gate with `dialogue_gates.py`. A changed pool
line changes its hash, so every override derived from it reads `stale`
until rewritten.

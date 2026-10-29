# Voices of the ten races

Any speaker and any player can be any of the ten playable races. Each card gives the measured Morrowind
baseline (from `$ARGONIA_PRIVATE/dialogue/morrowind/morrowind-full.json`: share of contractable phrases contracted,
mean sentence length, self-reference) and how we use it. Numbers are measurements, not quotas; a person's
own sheet (formality, chattiness, backstory) moves them. Look up example lines by race in the corpus; do not
paste them into the repo.

| Race | Contracted | Sentence | Self | Address and manner |
|---|---|---|---|---|
| Argonian | 30% (almost all in anger or combat) | 6.2 words | "we" in about 1 of 5 self-references | Others by race name; Argonians as kin; non-Jel speakers are ojel. Earnest, not wry. Full sentences. |
| Dunmer | 46% | 8.2 (longest) | I | "Outlander" for anyone not Dunmer, by far their commonest address; formal service phrasing. |
| Imperial | 85% | 7.7 | I | "Citizen" to Imperials; polite service formulas; colonial and official in Black Marsh. |
| Khajiit | 18% | 5.4 | Third person: "this one", "Khajiit knows" | "Friend"; their own idiom; rarely contract. |
| Nord | 89% | 5.3 | I | Blunt, hearty greetings. No Skyrim references at all (decision 0006: no Sovngarde, Dragonborn, dragons, Skyrim places). |
| Breton | 90% | 4.4 (shortest but one) | I | Brisk and busy; "friend". |
| Altmer | 87% | 4.9 | I | Cool and superior. |
| Bosmer | 88% | 4.9 | I | Casual; "stranger". |
| Orc | 46% | 4.1 (shortest) | I | Blunt and few words. |
| Redguard | 87% | 6.5 | I | Brusque when busy; "greetings"; plain. |

## Speaker and listener

- **The race name a speaker uses** for the player is the speaker's word, not always ours: Argonian speakers
  in Morrowind call Imperials "Cyrodil". `[player race]` renders through `race-names` (a per-speaker-race
  table, to build in 1.3 and 2.5); until then write the word the speaker would use.
- **Write listener variants only where the line changes.** A greeting or a line with an address term needs a
  variant per listener group the speaker treats differently (at least: same race, and others). A topic
  answer about the weather needs none.
- **What a speaker thinks of the player's race** comes from the culture sheets (the speaker's opinion with a
  lean per race), never from the writer's guess. Black Marsh history the sheets should carry: Dunmer slaving
  (House Dres) and the Argonian invasion of Morrowind; the Empire's roads and garrisons; Khajiit and
  Argonians as fellow outsiders in Morrowind.
- **Faction and rank:** same faction, greet by `[player rank]` and share what members share; rival faction,
  colder and less on faction topics; stranger, the default.

# world/sources/dialogue

The dialogue layer on the people records (phase 2.5, decision 0139). Data model rows: [docs/world/98-data-model.md](../../../docs/world/98-data-model.md) (culture sheet, stance, pool line, override).

| Path | What | Schema | Written by |
|---|---|---|---|
| `cultures/province.json` | the province node | `culture-sheet.v1` | by hand, lore-cited |
| `cultures/regions/*.json`, `cultures/peoples/*.json`, `cultures/factions/*.json` | region, people (race x upbringing), faction and office nodes | `culture-sheet.v1` | by hand (lanes 2.5a1b, 2.5a2) |
| `cultures/settlements/<place-slug>.json` | a place's settlement, life group and household nodes | `culture-sheet.v1` | by hand, per place |
| `stance/<place-slug>.json` | each person's stance per topic class and voice sheet | `stance.v1` | drafted by the composer, set in the place review |

## The hierarchy

province > region > people > faction > office > settlement > group > household.
Each sheet names its `parent`: region, people and faction under the
province; office under its faction; settlement under its region; group
under its settlement; household under a group or the settlement. Ids are
`culture.<level>.<slug>`: a people is `culture.people.<race>-<upbringing>`,
an office `culture.office.<faction-slug>.<rank>`. A group or household lists
its `members` (npc ids).

Every trait is `{text, source}`: `source` is a `world/sources/lore/` dossier
path (optionally with an anchor) or `inferred`. Stock opinions carry a `lean`
from -2 (hostile) to 2 (devoted). Topic classes: `place work people faction
hist empire trade danger rumour directions`. The province holds an opinion
on every class, so every person has a value for each.

## The composer and the gate

    cd tooling/world-generation
    python3 -m worldgen.dialogue_compose --place <place-id>   # draft stance/<slug>.json
    python3 -m worldgen.dialogue_sheets                      # structure gate
    python3 -m worldgen.dialogue_sheets --complete           # plus a sheet for every slice node

The composer walks a person's chain (province, region of the home place,
people, each faction and office, settlement, any group and household that
lists them), takes each topic's opinion from the most specific node that
holds one, and draws deviations at the most specific node's
`deviationRate`, deterministically from the ids, with `reason: null` for
the review to fill. Upbringing comes from the person record's `upbringing`
field; without it the draft is `port` or `tribal` for an Argonian (by the
home place's catalogue type) and `marsh-born` for anyone else. Correct a
person by setting the record field. A row marked `reviewed: true` is never
rewritten.

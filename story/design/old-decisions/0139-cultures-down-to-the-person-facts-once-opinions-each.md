<!-- imported unchanged from elder-souls-argonia docs/decisions/0139-cultures-down-to-the-person-facts-once-opinions-each.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0139 Cultures down to the person: facts once, opinions each, no two people a sentence alike

**Decision (owner).** Dialogue is Morrowind-shaped in its
mechanics (topics, conditions, knowledge, disposition, a scored
persuasion) and layered in its voice from culture down to the person.
Every fact lives once, in a pool line keyed by topic and condition set,
so nobody is ever silent and lore has one home. Every person has a
personality: a typed stance per topic class composed from the culture
sheets above them (province, region, people, faction and office,
settlement, life group, household) with named deviations at a planned
rate per group, and a checkable voice sheet with one quirk. A person's
own lines are overrides rendered from stance, sheet and the pool fact,
one person at a time; an override may differ from its pool line in
opinion and voice, never in fact. Opinions may be shared, since people
agree in life; sentences may not: no two speakers in the province carry
the same sentence, and the catalogue gates it. The slice writes overrides
for every placed person so the owner can judge distinctness; Part 4 sets
the override ratio per packet from that evidence. The province, region,
people and faction sheets are filled wide now; settlement and group
sheets per place. Voice acting is out; barks are text.

**Why.** Agents make writing cheap, so cost was never the reason to share
lines. What does not scale is sameness (one model writing thousands of
"unique" voices converges on one voice, the failure
[0043](0043-text-quality-workstream.md) guards against) and fact drift
(thousands of versions of one fact, all to change when lore changes).
Both are structural, so the structure answers them: facts in one place,
opinion as data a reviewer can see spread across a village before a line
exists, voice as a sheet a reader can check a line against, and
sameness judged over the whole catalogue by panels of cheap readers,
one lens each; the linter catches exact patterns only and is never the
bar. Morrowind's own engine composes voice from
conditions rather than storing a script per person
([research](../research/text-and-voice/speech-register-model-morrowind.md));
the layered register model ([standards/text/culture-registers](../standards/text/culture-registers.md))
already composes race, upbringing, region and faction; this decision adds
the settlement and group levels, the stance, and the gates. The player
senses a culture only through the people who carry it: the same topic
asked across a village shows the norm and its dissenter; the next region
changes greeting, oath and grievance together.

**Consequences.**
- [2.5](../phases/2-slice/2.5-dialogue.md) carries the plan: the culture
  and stance layer first, the runtime, then the pool and every slice
  person's lines with the gates.
- New home tables in [world/98](../world/98-data-model.md): culture
  sheet, stance, pool line, override, with the knowledge state as a save
  family.
- The condition vocabulary ([quests/85](../quests/85-condition-vocabulary.md))
  becomes typed code in the dialogue package; [2.11](../phases/2-slice/2.11-quests-journal-map.md)
  extends it, never re-implements it.
- The text-review skill grows into reader panels with one lens each
  (tells, voice, personality, variety, culture, blind mix against a
  Morrowind corpus, Morrowind feel, drift, particular, blind grouping)
  on the cheapest model that can read, plus one long-context reader
  that takes the whole corpus in one sitting for what no per-place read
  can see; every fault they find becomes a
  worded row the next panel carries, and the style rules are rewritten
  in the same batch as the lines.
- Helstrom's people are 4.1b; nothing in 2.5 may need a different
  approach for three hundred or for three thousand.

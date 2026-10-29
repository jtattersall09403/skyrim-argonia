<!-- imported unchanged from elder-souls-argonia docs/decisions/0143-anyone-may-explain-restatement-is-near-verbatim-only.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0143 Anyone may explain in their own words; restatement is near-verbatim wording only

**Decision (owner review item H; planner ruling, 2.6).** Any speaker may
explain a term, a fact or a place in their own words. Who explains, and
how fully, follows the person: personality (chatter and traits), faction
and race make one helpful and another curt. No cap counts how many people
explain a thing.

- Deleted: the province gate `corpus.explainers` and
  `EXPLAINERS_PER_REGION` (one full explainer per region), the plan's
  `regionExplainers` and per-fact `explainers`, `RESTATE_SPEAKERS` and the
  `style.restatement` gate (a fact restated by at most two speakers), the
  packet's "who explains which term" section and the skill's "Explain a
  term once" rule.
- `corpus.restatement` now reds only **near-verbatim wording across
  speakers**: a sentence of six words or more that shares a run of six
  words, or half its 4-word runs, with another speaker's sentence anywhere
  in the corpus or with a pool line (`dialogue_corpus.near_verbatim`). The
  same meaning in different words is green.
- The writer's own `check` holds them to the same: a sentence copying
  another speaker's or the pool's wording is a red.

**Why.** The owner's review asked for helpful speakers who explain so a
newcomer understands; the cap made most people allude or hand the player
on, which read as evasive and drove the hand-off loops. What the closing
read actually objected to was copied wording (the Riverwalk cove sentence
near-verbatim to its pool line, the ojel gloss repeated word for word),
which the near-verbatim test catches; the old by-meaning test also red
every answer that merely used the fact's noun.

**Paraphrase ruling.** `corpus.paraphrase` (at most two speakers per topic give a pool line's facts, by shared nouns) is deleted with its test: anyone may explain, and its copy-in-order case is already `corpus.restatement`.

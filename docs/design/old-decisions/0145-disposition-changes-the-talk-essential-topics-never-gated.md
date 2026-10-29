<!-- imported unchanged from elder-souls-argonia docs/decisions/0145-disposition-changes-the-talk-essential-topics-never-gated.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0145 Disposition changes the talk; quest-essential topics are never gated

**Decision (owner ruling 2026-10-19, 2.7).** The owner drove a person to
disposition zero and they talked as before. Disposition and scripted state
beat every other layer of a line (speech-register model § 6; the Morrowind
corpus, `docs/research/text-and-voice/morrowind-dialogue-corpus.md:124-133`).

1. **Three bands, one line.** A greeting or topic answer carries `words`
   (the plain middle band) and may carry `variants: {low, high}`. The
   runtime picks the telling by the speaker's disposition through
   `speakerDispositionAtLeast` (`packages/dialogue/src/select.ts`
   `DISPOSITION_BANDS`): below 30 `low`, 70 or above `high`, else the plain
   line; a missing variant falls back to the plain line.
   - **low:** a refusal or brush-off in the person's own voice and culture
     ("Save your breath" shape), never a generic snarl.
   - **mid:** the plain answer.
   - **high:** the warm telling: a tip, a name, an offer.
   The variant is the same line: same facts, links and effects; the writer's
   sample voice carries into all three.
2. **Quest-essential topics are never gated.** A quest record lists the
   topics it cannot proceed without (`essentialTopics`,
   `world/sources/quests/README.md`; 2.11's briefs fill them). No line on an
   essential topic carries a disposition condition; its `low` is a cold
   telling that still gives the fact or the hand-off. `dialogue_gates`
   reds a disposition condition on an essential topic everywhere, and a
   missing variant only in a lines file marked `"variantsReady": true`, so
   places turn strict one at a time as the corpus round writes them.
3. **Recovery always exists.** The disposition record
   (`packages/economy/src/disposition.ts`) has a floor of 0: no person rests
   below it. Each day a person drifts 5 points toward their place's norm
   (neutral 50), from below and from above. A gift is valued through the
   one price contract (0141) and moves at least 1 point, at most 20; all a
   person's gifts together move them at most 30 a game day. The talk
   screen's Give a gift button hands over a bag item (the thing leaves the
   bag only when the cap lets it warm them). 2.10's amends act
   on standing. Zero is a cold spell, never a dead end.
4. **The walk test.** The dialogue walk asks every essential topic each
   person answers at disposition 0 (the floor) and reds when it gives a
   different line than at 50, the class fallback, or no words.

**Why.** Morrowind's people refuse, warm and help by disposition; the
ruling asks the same. Gating the fact itself would strand quests, so only
the telling changes on an essential topic, and the floor keeps every
person reachable.

**Consequences.** The dialogue-write skill writes low and high beside each
greeting and non-essential answer; the result schema carries them
(`dialogue_rewrite`, `"scope": "variants"` for frozen people); world/98
records the shape. The worked sample is Xuth-Ra's greeting at the Pearl
Lots.

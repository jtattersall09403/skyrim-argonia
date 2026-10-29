# General principles (every quest)

Binding for `quest-write` and `quest-review`. Evidence: `docs/research/2026-10-27/quest-design-open-world-rpg.md`
(OW) and `quest-design-elder-scrolls.md` (ES); numbers in brackets are their principle numbers.

## The premise and the truth

1. **Believable people.** Say the premise in one sentence, then for each person ask what they know and what a
   sensible person in their place would do. If they would act otherwise, change the truth (OW methods).
2. **Truth first, as physical events.** Who, where, when, how, why, before any stage. Every clue, rumour and lie
   follows from it (OW methods).
3. **One honest account, false ones that clues refute.** No betrayal by a quest-giver and at most one
   coincidence, unless the record says why (ES 11).
4. **Every giver has a motive** from the nine: knowledge, comfort, reputation, serenity, protection,
   conquest, wealth, ability, equipment (OW 6). Record it in `cast[].wants`.

## The trail

5. **Three clues per conclusion**, in at least two forms (line, thing, place, behaviour), and never fewer
   because one seems obvious (OW 1).
6. **Two kinds of clue.** Concept clues say what happened; leads say where to go next. Tag each clue
   `concept` or `lead`. Every stage the player reaches offers at least three leads out, and is reachable by at
   least three, so the player is never stuck (OW 3, 4).
7. **Three solutions for every chokepoint** (a locked door, a name, a person who must be met), each of a
   different kind: a check, a document, a second route, a person, the culprit's own behaviour (OW 2).
8. **The player deduces or decides; nobody hands over the answer.**
9. **The player can always act on what they have worked out, and always knows why they are asked to act**
   (OW 12).

## The world and the player

10. **The world does not wait.** Quest people and things exist before the quest starts, can be met, killed or
    taken early, and each way to ruin the quest has a failure stage that says so in the journal (ES 5, 6).
11. **Directions in words.** Each place to reach: a starting point the player has seen, a bearing in the
    world's terms, a distance in effort, a landmark visible on the way and one that confirms arrival, a sign
    of going too far, and the other route if swimming, climbing or a boat changes it. A giver who does not
    know the way names someone who does (ES 1, 2; threat-and-journey directions method).
12. **The journal follows the imported journal design** (old repo; 2.12 §b). Each entry the quest writes
    carries the directions given and the facts still needed, and reads correctly whatever order the clues
    came in (ES 3).
13. **Topics carry the thread.** Each clue is a keyword another person can answer; topics unlock by stage, so
    a conversation unfolds rather than dumps; a spent topic answers briefly (ES 4).
14. **Urgency is stated.** Say in dialogue why this matters now and what happens if the player waits (ES 13).
15. **Danger is fixed and warned of.** Two independent signs before any place above the band around it.

## Choices, consequences, rewards

16. **No single right answer.** At least two endings, each with a virtue and a cost (OW 8).
17. **Consequences are visible and some are delayed.** Every ending records where the player will see it: a
    changed place, greeting, topic or price (OW 9).
18. **Offer the obvious option**, then make it cost (OW 10).
19. **Rewards serve autonomy, competence and relatedness** (OW 18): they fit the route taken, prove mastery,
    or bind the player to people. Proportionate to risk; tied to the story.
20. **Signal over noise.** Important facts arrive in one focused moment; no three people repeat the same
    summary; cut detail that does no work (OW 11, 19).
21. **No plain fetch, kill or delivery** without a discovery or a turn.
22. **Vary the places.** No staging room or set dressing reused across quests (ES 12).

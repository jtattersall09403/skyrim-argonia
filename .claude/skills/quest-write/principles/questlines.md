# Questlines: the main line, a faction's line, local and Daedric lines

The craft of a line of quests, for the story writer and for every quest writer before any quest of a line. Read with
`general.md` (which holds the source tags' key); the line's quests then follow their own shape files. A worked line
written to this sheet: [chainbreakers](../../../../story/design/quests/lines/chainbreakers.md).

## How a line holds together

1. **A line is a story with a shape, not a job list**: one governing story and one governing way of acting (the
   faction's skills). Each quest is a slice of that story [QL P1; QL F1].
2. **Stakes climb, and the climb is earned.** Each quest is a different kind of job in a different place (a
   break-in, an errand into danger, a judgement among people, an aftermath walked into, a ruin of the dead, the last
   lock); scale rises from one household to many people to what a whole place becomes. No filler between ranks
   [QL P3; QL P4; QL A].
3. **Seeds are planted early and paid off.** For each thing the finale reveals, two clues in earlier quests (one in a
   small quest, one in another line's work) and a decoy meaning; a player who read only the journal could reach it
   [QL F8; QL P11].
4. **A turn at about half to two-thirds through** reverses something and makes earlier quests read differently;
   the line names which [QL F9; QL P11].
5. **The patron has something to hide.** The premise card says what the faction lies about, and the hidden spine
   says what its leader does not tell; the player finds it, and decides what to do with it [QL F1; QL F2].
6. **A recurring cast carries the weight**: a mentor, a peer, a rival inside, an antagonist outside, an informant,
   and the antagonist met by the second rank. Each speaks in at least three quests before the turn and holds one
   contested belief [QL P6; QL F6].
7. **The faction is made of people who disagree**, rooted in one local history and one contested ideal, and it
   competes with each other faction for a reason [QL P7; QL F3; SO P1].
8. **Choice weight comes from a person the player has mixed feelings about**: show their kindness before their
   fault [QL P12].
9. **Rivalry has teeth**: a standing per faction (a stored number), a lockout where the rival map says so, a
   hostility the player can trigger [QL P8; QL F7].
10. **Urgency is shown by what the player finds, never by a timer** [QL P10; QL A].
11. **The finale is a hard choice or a hard place, using the line's skills in their richest form**: the last locked
    box among armed keepers; the key handed to one of four people, each with a case; the truth and public justice
    parting. Never a staged sequence, and never the same verb as every job before (a thieves' line does not end on a
    dungeon boss) [QL P2; QL F11; QL A].
12. **Leading comes only at the finale, and costs something**; the leader post is never a milestone [QL P5].
13. **A mid-line misjudgement**: one quest lets the player act on the wrong person, costs standing and does not end
    the line [QL F10].

## What carries between quests

14. **No multiplying branches.** Earlier choices and endings colour later quests and never change their stages: a
    stored number per ending is read by greetings and single lines; only the finale's choice carries into the world
    after the line [OB shape].
15. **What carries**: the rank, the journal, the stored numbers, who is alive, the things the player holds, and what
    the player knows. A later quest reads sensibly whatever the earlier ones left [OB shape; QL F13].
16. **The hub reacts**: for each rank and ending, changed greetings, topics, prices, and who greets coldly [QL F12;
    QL A].
17. **The line survives being abandoned**: the world is consistent if the player stops at any rank [QL F13].

## The line record

A line (faction, main or Daedric) is a line record, or a story document like the worked example, before any of its
quests is a quest record. Fill every field; no quest text before fields 1 to 9 are complete [QL F14].

1. **Premise card**: the governing question, the governing skills, the cost of joining, what the faction wants
   from the player, what it lies about [QL F1].
2. **Hidden spine**: the line's truth (what happened, who, why, in order; the physical and spoken proofs; who knows
   what). Each quest's `truth` is a slice of it [QL F2].
3. **Local root**: one local history and one contested ideal, and why it competes with each other faction, grounded
   in the lore with sources [QL F3].
4. **Rank ladder (five to seven)**: title, entry test (standing plus a skill or a task, never time alone), what it
   unlocks, and one new skill use per rank from the line's profile, combined with the earlier ones in later quests
   [QL F4; AS CP].
5. **Quest table**: id, rank, kind of job, the skill it asks most, places, seeds planted, who appears. No two
   consecutive quests share a kind; one per rank breaks the pattern (all talk, no talk, a case that cannot be fully
   solved) [QL F5].
6. **Cast sheet** [QL F6]. 7. **Rival map**: each other faction's attitude, one shared quest, one conflict, the
   standing effect, any lockout and what makes it hostile [QL F7]. 8. **Seeding table** [QL F8]. 9. **The turn**
   [QL F9]. 10. **The misjudgement** [QL F10]. 11. **The finale** [QL F11]. 12. **Hub reaction** [QL F12].
   13. **Abandon path** [QL F13]. 14. **Authoring order**: spine, ladder, cast, seeding, quest table, then each quest
   record, `quest-review` of the line and of each quest, then briefs and dialogue [QL F14; QL P14].

## Line types

- **Faction lines**: as above. Joining one closes another only where the rival map says so; the line never forces
  the player to stay [QL P8].
- **The main quest** ("The Eye and the Root"): any build can finish it, each quest by at least two ways on different
  skills; urgency is told and shown by consequence; every objective has a marker and directions in words; the
  factions are part of its story; its three endings (CUT, CLAIM, MEND) each change what the player meets afterwards
  [OB skills; OB shape; QL P9; QL P10].
- **Local quests**: one place's people and facts; a hook, two lines of enquiry, a discovery, a decision, a visible
  consequence; they never write what a faction or the main quest owns [ES P15; OW P9].
- **Daedric and oddity lines**: `otherworldly.md`; each quest stands alone and expresses its patron [OT P16].

## The detectives' line

A civic, evidence-first order between the assassins and the thieves, whose cases start from what those two leave
behind (bodies, missing things) [QL D; IN D].

- **Escalate by widening the unknown**: a petty theft with one unknown; a missing person with a trail; a murder with
  a closed cast; an old case implicating a respected figure; a grand murder whose cases link [IN D].
- **Teach investigation in stages**: examine a place, ask about a word, refute a statement with a thing held,
  compare two statements, follow a lead, accuse; the journal lists what is learnt and what is still open [QL D].
- **One desk per rank**, each with its own senior and partner and tone; one case per desk breaks the pattern [QL D].
- **Seed the culprit and three proofs before the first case**: one in a petty case, one in a thieves' job, one in an
  assassins' contract; two decoys guilty of something else [QL D].
- **The finale may reveal a guilty person too powerful to name**: the player chooses to leak, bargain or bury it
  [QL D].

## Anti-patterns

Leader in a handful of quests; promotion by repeated filler; a finale solved by the same act as every job; every
quest ending in the same kind of fight; a hub that does not react; a turn with no earlier clues; an antagonist met
only at the end; rival factions as set dressing; a countdown; a skill taught by a speech instead of a job that needs
it; a line that cannot be left [QL A].

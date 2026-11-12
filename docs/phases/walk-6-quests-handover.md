# Walk 6 (quests) handover: the owner's feedback and the brief for the session that delivers it

Written 2026-11-12 by the session that delivered nw-03b and nw-04, at the owner's ask: "queue up a new Fable planner
agent to deliver everything from that to start after you have finished and terminated your own session". This file is
that session's brief. The owner tested the rebuilt opening and the start of the main quest on the Argonia (Black Marsh
& Valenwood) card: "Some of it mechanically kind of worked but frankly overall it was a complete mess."

## The owner's feedback, in their own words (tmp/walk-6-quests-feedback.md, 2026-11-12)

The screenshots it names are on the build machine: `tmp/image copy 12.png` (the extra dock and the sunken hut) and
`tmp/image copy 13.png` (the journal entry). `tmp/` is not committed.

# Quests
* A random extra bit of dock and what looks like maybe a sunken hut have been placed on the original dock. The extra bit of dock cuts across it and its rope fence blocks the NPCs! And the hut is like sunken in the ground/water. See tmp/image copy 12.png. 
* I got as far as the camp fire and then it came up with the next milestone, and this in my journal: tmp/image copy 13.png. But none of this happened! None of what it says in that journal entry. And there is no burning hut to rescue anyone from. The gang are all just walking back to the ship, apart from mee-tuja who is doing a weird crouching thing. Deesh-Duun is just standing by the end of the dock. When I talk to her and say "who are you" she says "I am Deesh-Duun, the huts are burning and I am under the boards", which is quite simply untrue. And talking to her surely counts as 'reaching' her, but nothing happened when I did that. Throughout all of this the two 'cutters' just stood there by the campfire. And the music was the normal calm exploration music the whole time. 
* Weirdly then after walking around a bit (I swam around the new sunken hut and then got back on land), it then came up with the quest milestone saying "bring deesh-duun to the shore west of the camp" . Then I walked with her to the shore and a few people suddenly appeared, and the journal updated to the stuff about the sunken fish trap and the sap...and bizarrely the thing I referred to before as a sunken hut suddenly transformed into a house! Still intersecting with the dock...
* Basically all of this is a total, total mess. I think we're going to need to completely alter our plans with regards to our quest system. Clearly agents cannot handle properly implementing skyrim level scripting for quests and a Helgen-like new game flow. We should massively dial down our ambition. Let's have nothing more complicated than Morrowind-level scripting for all of our quests, and do much less world-editing for each quest. I did like the opening barge area for the opening of this game so we can keep that. But none of the rest of it worked. How about when you come out of the barge's door, the guy there automatically starts some dialogue with you and it's a bit more like Morrowind's opening - you've found yourself in this work gang, but he doesn't have your name on his list, as far as he's concerned you don't owe anyone here and he wants to get rid of you. He tells you if you want work to go to (place x) and speak to (person y), and then that person inducts you into the faction for the main quest.
* And review everything else for all the quests and stories and factions that we've authored so far. I want to keep the spirit of what we intended, but massively row back the scripting amibition. Nothing higher than Morrowind level (research what that means in practice and record it somewhere it will be noticed and used, like in the skills or whatever). I won't have time to playest every single quest in this game, I need to be confident that our building blocks work and that the scripting requirement for everything is simple enough that they will all just work. I also think we are going to need quest markers on the map and in-game (like in skyrim) for objectives and things you need to pick up or interact with or whatever because I just don't think we can rely completely on agent-written directions in dialogue.
* By the way we should make it so anyone in our game can die. And if a person dies who is essential for the main quest, you get a message like you did in Morrowind (the one about the thread of prophecy being severed, but adapted for our game), so you can reload an earlier save if you want but you don't have to.
* The whole thing was also incredibly confusing and as a new player with no context I really had no idea what was going on. I think we need something to guard against and test this, but without playing the game. How about as part of the quest building kit we have an off-game fast harness that a fresh agent (you choose the type) can 'play' as if they are a player with no context? Essentially like pen and paper user testing. They should role play as someone playing the game and feed back on how it feels in general and what's confusing or makes no sense. The harness should read from what we have got built for our actual game and give them the sequence of things and they reason and take actions and then see what happens next, and feed back as they go (and you are able to see what their 'thinking' was so you can see what was intuitive and what wasn't). You should reason through how to make this work really well for proving/testing what we need. They key things really are (a) it's a fresh agent role playing as a player - if they're starting a new game then they have no context about our game (other than that it's an elder scrolls game set in argonia, and they've played skyrim before); if you're testing a later quest then give them a reasonable amount of context that you'd expect a player to have built up by that point. And (b) this is about testing the quest progression and story and the dialogue around it and characters, not navigation or visuals or combat or anything. So the agent should 'see' things like the quest text that comes up on the screen for milestones, the journal entries, probably some basic stuff that would be available to the player like their own map co-ordinates and the co-ordinates of their active quest markers and what those markers are - like a place or a person or whatever (so they can reason about where to go and what to do next). They should be able to take various simple actions like talking to people, choosing dialogue topics, seeing the dialogue results. Sometimes quests will require more complex in game actions like picking locks and doing combat; you'll need the harness to have some simple way for them to be able to broadly choose what to do but basically skip the complicated bits (like if a quest is supposed to send them to a cave to fight a snake, then the key thing to test is does the player intuitively find out that this is what they're supposed to do, and what happens afterwards, not really the fight itself). Does this make sense? I've kind of specced it poorly, I need you to do some proper design and implementation work on this. The harness really needs to be simple so we don't just get bogged down in harness errors rather than testing what actually needs to be tested. The current quest and story is super impenetrable and you just don't know what's going on as it happens and that needs fixing (in addition to all the scripting mess).

## What this asks for, as deliverables

Every item is owed. Plan it critically first (the owner wants plans challenged and costs weighed), record each
ruling in docs/owner-rulings.md, and post any call that is truly the owner's as an owner issue.

1. **A new scripting ceiling: nothing above Morrowind level.** Research what Morrowind-level quest scripting means
   in practice (journal index set by dialogue results and simple triggers, topic and greeting conditions on journal
   index, item counts, faction rank and disposition, death counts, simple local scripts, no scenes, no packages
   that march people about, no staged set pieces) and what the Skyrim equivalents are with our proven blocks
   (docs/design/blocks.md). Write it where it will be used: the quest-write and quest-review skills, the block set,
   docs/design/quests-on-a-world.md, as clean recipes. A check in the gate refuses a quest that uses anything above
   the ceiling.
2. **The opening, redone small.** Keep the barge. When the player comes out of the barge's door the man there
   starts the conversation himself: the player is in this work gang but is not on his list, owes nobody here, and he
   wants rid of them; for work he sends them to a named place and person, who inducts them into the faction that
   carries the main quest. Remove the opening's world edits that did not work (the extra dock across the original
   dock with its rope fence, the hut sunk in the water that later turns into a house, the burning huts, the marches).
3. **Every quest, story and faction authored so far, reviewed and rowed back** to that ceiling, keeping the spirit,
   with much less world editing per quest. The owner will not play every quest: the building blocks must be few,
   proven and simple enough that every quest built from them just works.
4. **Quest markers** on the map and in the world, as Skyrim has them, for objectives and for things to pick up or
   use. Directions in dialogue stay but are not relied on.
5. **Anyone can die.** If a person essential to the main quest dies the player gets a message as Morrowind did
   (the thread of prophecy severed), in our own words for our game, and may load an earlier save or carry on.
6. **The paper playtest harness.** An off-game harness, part of the quest kit, in which a fresh agent plays as a
   player with no context (told only that this is an Elder Scrolls game set in Argonia and that they have played
   Skyrim), or with the context a player would have by a later quest. It reads what is actually built (the plugin's
   quests, stages, journal text, objectives and markers, dialogue topics and their conditions and results), shows
   the agent what the player would see (objective text, journal entries, their position and their active markers'
   positions and what each marks), lets them take simple actions (go to a marker or a place, talk to someone,
   choose a topic, pick up or use a thing) and abstracts the hard parts (a fight, a lock) as a choice with an
   outcome. The agent says what they think is going on as they go, and their reasoning is kept so the lead can see
   what was clear and what was not. It tests quest progression, story, dialogue and character, not navigation,
   visuals or combat. It must be simple enough that it does not become its own source of faults. Design it properly
   first; then use it on the new opening and the first quests, fix what confuses, and add it to the quest recipe.
   The owner added three points on the harness the same evening (2026-11-12), in their words:
   - "It's essential that the version it's 'playing on paper' is actually the game version. I don't want to overdo
     specify this as I think you will do it better than me but so you know what I mean? If it just tests what the
     author *says* will happen in game that's not much good if that then doesn't actually happen in game."
   - "Rather than *just* being a test that is run on a built quest, is there a way we can have it like...integrated
     somehow in the process of actually authoring and building them in the first place? So we don't have to spend
     ages building a bunch of quests wrong, then time testing them with this new harness, then time fixing, then
     testing again... Etc."
   - "I also think it shouldn't become a regularly running 'gate' or part of a test suite as it will be somewhat
     probabilistic and also presumably quite slow to run."

   The previous session's reading, for you to challenge:
   - **It plays the built records, never the author's account.** The harness's world is derived by a deterministic
     reader from the built plugin (the ESP read back, or the Spriggit YAML it is built from, whichever the read-back
     already proves equal): quest stages and their conditions, objectives and their targets, aliases, dialogue
     topics with their conditions and result fragments, journal text, markers, who stands where. The quest record
     and the writer's notes are not an input. Where the plugin holds a script fragment, the reader models only what
     the Morrowind-level ceiling allows (set stage, give or take an item, move or enable a thing, change a faction
     or a global), which is one more reason for the ceiling: anything the reader cannot model is a fault reported by
     the reader, not something the playtester is told happened. The deterministic part (what state follows what
     action) is code with unit tests; only the player is an agent.
   - **It is part of authoring, at each step where a change is cheap.** The same state machine runs on the quest
     record before anything is built (the record compiled to the same intermediate form the plugin reader emits),
     so a fresh-agent playthrough reads the quest as designed before dialogue is written; again after dialogue;
     and once on the built plugin, where the reader also diffs the built form against the designed form and names
     every difference. One representation, three moments, so "built wrong" is caught by the diff and "confusing"
     by the player, each as early as it can be.
   - **It is not a gate.** The deterministic parts (the reader, the designed-against-built diff, the ceiling check)
     are fast and belong in `make check`. The agent playthrough is run by the quest's author as a step of the
     recipe (at the three moments above, and again only when the quest's player-facing flow changes), its
     transcript and findings kept beside the quest; it is never in the test suite and never blocks a commit.
   Two more from the owner, later the same evening:
   - "Make sure that the agent playing the paper version has a broad enough brief that it can use it's own
     initiative - don't overly restrict it into only looking for certain things, invite it to think for itself and
     give general feedback as well as the specific stuff. Like what does it think about how the quest is feeling,
     does it understand what's going on, how fun does the quest feel, does it want to find out what happens next,
     does everything make sense, what's it's overall open ended feedback and take? That sort of thing."
   - "I would also be interested in having an artefact that allows me to visually and textually see agents'
     playtest runs and explore them to see what happened and what their feedback was etc. not just text, somehow
     kind of nicely visual as well, be creative."

   Reading: the playtester's brief is a role, not a checklist. It is told who it is and what it can do, asked to
   think aloud as a player would at every step (what it believes is going on, what it wants, why it chooses what
   it chooses), and at the end to give its own open take in its own words: how the quest felt, whether it
   understood it, whether it was fun, whether it wants to know what happens next, what made no sense, anything
   else it noticed. A few standing questions may be asked after that take, never before, so they do not steer it.
   Different players are worth running (a careful reader, an impatient one who skips dialogue, one who wanders).
   And an owner-facing artifact (published with the Artifact tool, private to the owner, readable on a phone)
   that shows each run as something to explore: the path the player took through the quest as a visual track
   (stages reached, where they went on the map, who they spoke to, where they stalled or guessed), the player's
   thinking beside each step, what the game showed them at that moment, and their closing take; runs of the same
   quest side by side, so it is plain where different players diverged or all got lost. Its data comes from the
   kept transcripts, so every new run appears without the page being rewritten. Design it as a real piece of
   work (the artifact-design and dataviz skills), not a log viewer.
7. **Why the last build went wrong**, in a short record: the stage that fired at the camp fire with a journal entry
   describing things that had not happened; Deesh-Duun's line that was untrue; talking to her not counting as
   reaching her; the cutters standing still; the calm music; the objective that fired later after swimming about;
   the hut that appeared. Each fault's cause, so the new ceiling and checks are known to rule its class out.

## What the previous session leaves that touches this

- Dialogue: the Morrowind find step (one Haiku corpus-find agent per topic group) had been skipped by almost every
  writer run since 2026-11-08 and is now enforced; writers are started by the orchestrating lane, never through an
  intermediate driver agent (a writer two levels down cannot start agents). Directions are written in words, never
  counts of paces (linter rule B13, talk_check reads them back). All 403 flagged talk lines and 25 quest rows of
  the BM&V version were rewritten on 2026-11-12; see docs/phases/4a-talk-to-everyone.md and section 11 of
  docs/owner-walk-checks.md. Most unflagged dialogue was still written without the find step.
- Directions lack landmarks at the source: of 57 rewritten direction lines checked on 2026-11-12, 31 name a
  landmark; for 9 of 20 spot-checked lines the route facts given to the writer held no landmark at all. Enriching
  the route data with named buildings and features (and the quest markers of deliverable 4) is yours to weigh.
- The play machine: never deploy while the owner is streaming (a deploy on 2026-11-12 had to be stopped);
  infra/gpu-box/deploy.sh has no stream check of its own unless a later commit added one. Shader caches are kept per
  card (commit ff995e27).
- The new world (nw-03b: ecology, regional distinctiveness, music; nw-04: source places) is a separate line of
  work: read docs/PROGRESS.md for its state and leave it alone unless the owner's walk feedback on it arrives.
- Models and lanes: the lead plans and orchestrates; delivery lanes are Opus 5.5 at medium effort, code review is
  forced Fable 5.2 at medium (owner, 2026-11-10). Unattended, end each turn with a few-letter code; owner-facing
  text goes out as owner issues in plain English.

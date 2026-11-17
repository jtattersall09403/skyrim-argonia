You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I am a hunter freed from the Owing at Ashgate Landing by Vosh-Leera, root-herald of Jal-Veesa. I picked Sithis' beard at Reed-Sill Weir without a fight and gave it to Weeltul, the tree-minder. It only warms the pool. Jal-Veesa's Hist is dying: dry dark bark, closed scar, cooling egg-pool. Nobody knows why, and trees are sickening along the river. I received the Hist's blessing and 50 gold. Vosh-Leera told me privately that she serves the Toh-Reel-Ka, the Secret Warriors of the Xeech-Leel, who rule the province. They exist to stop another Umbriel-type disaster. They use friendless strangers like me as cheap spies. She wants me back at her House in Jal-Veesa for a second task, which I have not yet taken. I carry 50 gold and two lockpicks. Unknowns: why the trees are sick, and what the second task is. Weeltul has topics on the sap, the scar and Umbriel that I have not asked about.


This version of the game is played in words. You see the game only through one command, `play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  play 'look'                     where you are, who and what is here, the doors, the quest markers
  play 'journal'                  your journal entries, objectives, what each marker points at, what you carry
  play 'go <place | person | thing | marker N>'   travel there (no need to walk the way)
  play 'talk <person>'            start a conversation: the topics you can pick
  play 'say <topic or its number>'   pick a topic while talking; add pass or fail when the game asks for a check
  play 'take <thing>'   play 'use <thing or door>'   play 'read <thing>'
  play 'fight <who> win|lose'     you choose how a fight ends (losing means you load your last save)
  play 'pick <lock> win|fail'   play 'pickpocket <person> win|fail'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening and why you do this next. For example:
  play 'look' --think 'I have just arrived. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. Where the quest offers a choice of how it ends, you mean to take this one: e-comfort.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Jal-Veesa.
People: Vosh-Leera (quest marker)
Doors: Door to Vosh-Leera's House

*** Quest started: The First Dream ***
Journal: Vosh-Leera has a second task for me. I'm to ask her for it in her house in Jal-Veesa.
Objective: Ask Vosh-Leera for her second task. (marker: Vosh-Leera)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. You know nothing else about this game.

This version of the game is played in words. You see the game only through one command, `/tmp/ptb-wr5d686_/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-wr5d686_/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-wr5d686_/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-wr5d686_/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-wr5d686_/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-wr5d686_/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-wr5d686_/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-wr5d686_/play 'take <thing>'   /tmp/ptb-wr5d686_/play 'use <thing or door>'   /tmp/ptb-wr5d686_/play 'wait'
  /tmp/ptb-wr5d686_/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-wr5d686_/play 'pick <lock> win|fail'   /tmp/ptb-wr5d686_/play 'pickpocket <person>'   /tmp/ptb-wr5d686_/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-wr5d686_/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

Stop when the quest you are on ends, when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-wr5d686_/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. After that the game asks you a few short questions; answer them in one reply with /tmp/ptb-wr5d686_/play answers '...'. Then stop.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: Off the Pier
Journal entry (Off the Pier): I woke in the hold of a work barge with no memory of how I came aboard. A man with a roll waits outside the hold's door. I'm to speak to him.
New objective: Speak to the man at the hold's door.

You are at Barge Pier.
People: Gang Boss (a person)
Things: nothing of note
Doors: Barge Hold Door

Gang Boss walks up to you and speaks.
Gang Boss: "Your name is not on my roll. You owe nobody here, so get off my pier. Want work? Find Sample-Contact at the Sample House in Lilmoth."
Objective completed: Speak to the man at the hold's door.
Journal entry (Off the Pier): The man with the roll says my name is not on it and I owe nobody here. If I want work, I'm to find Sample-Contact at the Sample House in Lilmoth.
New objective: Find Sample-Contact in Lilmoth.
Gang Boss has nothing more to say to you.

Play.

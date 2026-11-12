You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far: you came to Soulrest's dock looking for work. A Khajiit trader, S'Tabi, sent you to Tilts-The-Jug, who keeps the Night-Reed Chapter's desk there. To test you, she had you take back a necklace a dock thief, Keeps-What-Floats, had stolen from a Chapter Lookout, without harming him; you got it out of his strongbox and she paid you. She sent you by the coast ship to Lilmoth, down a trapdoor north of Pusbottom, where Bent-Spine, the Chapter's fence, took you in as a Lookout of the Night-Reed Chapter, a thieves' guild. He said he has work for you.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-6167rcx1/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-6167rcx1/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-6167rcx1/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-6167rcx1/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-6167rcx1/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-6167rcx1/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-6167rcx1/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-6167rcx1/play 'take <thing>'   /tmp/ptb-6167rcx1/play 'use <thing or door>'   /tmp/ptb-6167rcx1/play 'wait'
  /tmp/ptb-6167rcx1/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-6167rcx1/play 'pick <lock> win|fail'   /tmp/ptb-6167rcx1/play 'pickpocket <person>'   /tmp/ptb-6167rcx1/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-6167rcx1/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

Stop when the quest you are on ends, when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-6167rcx1/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. After that the game asks you a few short questions; answer them in one reply with /tmp/ptb-6167rcx1/play answers '...'. Then stop.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: The Drowned Lockbox
Journal entry (The Drowned Lockbox): Bent-Spine, the Night-Reed Chapter's fence, has work for me now that I am a Lookout. I'm to ask him about it, in the Chapter's inner room under Lilmoth.
New objective: Ask Bent-Spine about the work he has.

You are in Lilmoth Dungeon (the Night-Reed Chapter).
People: Bent-Spine (a person)
Things: nothing of note
Doors: none

Play.

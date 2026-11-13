You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. You know nothing else about this game.

This version of the game is played in words. You see the game only through one command, `/tmp/ptb-ivg1qzhc/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-ivg1qzhc/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-ivg1qzhc/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-ivg1qzhc/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-ivg1qzhc/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-ivg1qzhc/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-ivg1qzhc/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-ivg1qzhc/play 'take <thing>'   /tmp/ptb-ivg1qzhc/play 'use <thing or door>'   /tmp/ptb-ivg1qzhc/play 'wait'
  /tmp/ptb-ivg1qzhc/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-ivg1qzhc/play 'pick <lock> win|fail'   /tmp/ptb-ivg1qzhc/play 'pickpocket <person>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-ivg1qzhc/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-ivg1qzhc/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: No Name on the Work Roll
Journal entry (No Name on the Work Roll): I woke in the hold of a ship, moored at a pier west of Lilmoth in Black Marsh, among a gang of Argonians I do not know. I'm to go up the stairs and out of the door to the pier, and speak to the man who stands there.
New objective: Speak to Buys-The-Months on the pier beside the ship.

You are at Lilmoth.
People: Buys-The-Months (an Argonian man)
Things: nothing of note
Doors: none

Buys-The-Months walks up to you and speaks.
Buys-The-Months: "I am Buys-The-Months, a broker. This is my pier, below Hereguard Plantation. Lilmoth lies a fair way east along the shore. That ship is mine. The water at Lilmoth is too shallow for a ship her size, so she lies here. The Argonians in her hold are an Owing gang. Each of them works off months of work owed for a debt or a wrong. I keep those months written on my work roll, and I hire the gang out to unload the lighters, the cargo boats, at Lilmoth's dock. You came down the estuary with them, but you are on no line of my roll. You owe me nothing, so I cannot hire you out. You are no affair of mine. Get off my pier."
Topics:
  1. Who are you?
  2. Where can I find work, then?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. You know nothing else about this game.

This version of the game is played in words. You see the game only through one command, `/tmp/ptb-4unrnggy/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-4unrnggy/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-4unrnggy/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-4unrnggy/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-4unrnggy/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-4unrnggy/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-4unrnggy/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-4unrnggy/play 'take <thing>'   /tmp/ptb-4unrnggy/play 'use <thing or door>'   /tmp/ptb-4unrnggy/play 'wait'
  /tmp/ptb-4unrnggy/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-4unrnggy/play 'pick <lock> win|fail'   /tmp/ptb-4unrnggy/play 'pickpocket <person>'   /tmp/ptb-4unrnggy/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-4unrnggy/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a wandering player. You poke at everything, talk to everyone you meet and ask them about anything on offer, and you follow your curiosity as much as the quest. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-4unrnggy/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: No Name on the Work Roll
Journal entry (No Name on the Work Roll): I woke in the hold of a ship, moored at a pier west of Lilmoth in Black Marsh, among a gang of Argonians I do not know. I'm to go up the stairs and out of the door to the pier, and speak to the man who stands there.
New objective: Speak to Buys-The-Months on the pier beside the ship.

You are in Ship, Lilmoth.
People: Wuleen-Sei (a person); Ux-Xeek (a person); Dives-Without-A-Rope (a person)
Things: nothing of note
Doors: none

Play.

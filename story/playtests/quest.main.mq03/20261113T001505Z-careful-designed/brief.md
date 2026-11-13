You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far, from your journal: From "No Name on the Work Roll": I woke in the hold of a ship, moored at a pier west of Lilmoth in Black Marsh, among a gang of Argonians I do not know. I'm to go up the stairs and out of the door to the pier, and speak to the man who stands there. Buys-The-Months, the broker, holds his gang's Owing, the months of work they owe. I am on no line of his roll, so he will not keep me. He says Nesh-Deeka, a guest at Salts-The-Catch's house south of the second big ship off Lilmoth's dock, pays for work. I'm to find her there, east along the shore. A woman with a knotted cord killed Nesh-Deeka's courier at the gang's camp the night it burned, took his satchel and let me live. Nesh-Deeka serves the Veiled Reed, the state's quiet service, and wants a hand whose name is on no roll. I'm to hear her out and say whether I will work for the Reed. I took work with the Veiled Reed, and Nesh-Deeka put fifty gold in my hand. She has told me the first work the Reed wants of me. Why the woman with the knotted cord let me live, I still do not know.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-s_rhyjhh/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-s_rhyjhh/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-s_rhyjhh/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-s_rhyjhh/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-s_rhyjhh/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-s_rhyjhh/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-s_rhyjhh/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-s_rhyjhh/play 'take <thing>'   /tmp/ptb-s_rhyjhh/play 'use <thing or door>'   /tmp/ptb-s_rhyjhh/play 'wait'
  /tmp/ptb-s_rhyjhh/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-s_rhyjhh/play 'pick <lock> win|fail'   /tmp/ptb-s_rhyjhh/play 'pickpocket <person>'   /tmp/ptb-s_rhyjhh/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-s_rhyjhh/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-s_rhyjhh/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

Your game goes on. You are a male Argonian.
Journal (The Cutters' Jar): Nesh-Deeka gave me the Veiled Reed's first work. Dives-Without-A-Rope, one of the broker's gang, carried off a jar of sap that the cutters dropped at the burnt camp. Nesh-Deeka wants it to learn what the cutters wanted. I'm to ask Dives-Without-A-Rope for the jar in the ship's hold at the pier west of Lilmoth.
Objective: Ask Dives-Without-A-Rope for the jar, in the ship's hold.

You are in Ship, Lilmoth.
People: Argonian Dock Worker 1 (an Argonian woman); Aragonian Vliiager (an Argonian woman); Argonian Dock Worker 2 (an Argonian woman)
Things: Lockpicks; Dives-Without-A-Rope's Lockbox
Doors: none

Play.

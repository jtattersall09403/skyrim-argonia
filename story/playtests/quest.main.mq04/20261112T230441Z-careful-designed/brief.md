You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far, from your journal. From "No Name on the Work Roll": I woke in the hold of a ship at a pier west of Lilmoth, in Black Marsh, among a gang of Argonians I do not know. Buys-The-Months, the broker who holds the gang's Owing, the months of work they owe, has no line for me on his roll. I owe him nothing, so he will not keep me. He says a woman called Nesh-Deeka, a guest at Salts-The-Catch's house in Lilmoth, pays for work from anyone off his ship. Nesh-Deeka serves the Veiled Reed, the ruling state's quiet service. The gang carried me off the bank the night their camp burned, she says, when a woman with a knotted cord killed her courier, took his satchel and let me live. She wants a hand nobody can claim. I took work with the Veiled Reed. Nesh-Deeka put fifty gold in my hand and told me what the Reed wants first. Why the woman with the knotted cord let me live, nobody has told me yet. From "The Cutters' Jar": Dives-Without-A-Rope, one of the broker's gang, carried aboard a jar of sap the cutters dropped at the burnt camp. I talked her round, and she gave me the key to her lockbox in the ship's hold. I put a drop of the cutters' sap on my tongue at Nesh-Deeka's table. She wrote down what I said while it held me: the ship's hold, roots grown up through its deck, a door nobody built, a dry voice without words. She cannot say what it means. She has word that the Hist of Low-Reed Village, east of Lilmoth, has turned its face. You are standing in Salts-The-Catch's house with Nesh-Deeka.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-j7rgc0al/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-j7rgc0al/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-j7rgc0al/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-j7rgc0al/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-j7rgc0al/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-j7rgc0al/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-j7rgc0al/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-j7rgc0al/play 'take <thing>'   /tmp/ptb-j7rgc0al/play 'use <thing or door>'   /tmp/ptb-j7rgc0al/play 'wait'
  /tmp/ptb-j7rgc0al/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-j7rgc0al/play 'pick <lock> win|fail'   /tmp/ptb-j7rgc0al/play 'pickpocket <person>'   /tmp/ptb-j7rgc0al/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-j7rgc0al/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-j7rgc0al/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: The Tree That Turned Its Face
Journal entry (The Tree That Turned Its Face): Nesh-Deeka has word that the Hist of Low-Reed Village, a stilt village east of Lilmoth along the shore, has turned its face. She wants to know whether the cell that cut the cutting's roots at the burnt camp did this too. I'm to go to Low-Reed Village and speak to Hires-By-The-Season, the root-herald, who speaks for the village to strangers.
New objective: Speak to Hires-By-The-Season, the root-herald of Low-Reed Village.

You are in Salts-The-Catch's House, Lilmoth.
People: Salts-The-Catch (a person); Nesh-Deeka (a person)
Things: nothing of note
Doors: none

Play.

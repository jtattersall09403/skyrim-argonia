You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far, from your journal. From "No Name on the Work Roll": I woke in the hold of a ship at a pier west of Lilmoth, in Black Marsh, among a gang of Argonians I do not know. The broker on the pier had no line for me on his roll and sent me to Nesh-Deeka at Salts-The-Catch's house in Lilmoth. Nesh-Deeka serves the Veiled Reed, the ruling state's quiet service. The gang carried me off the bank the night their camp burned, she says, when a woman with a knotted cord killed her courier, took his satchel and let me live. I took work with the Veiled Reed. From "The Cutters' Jar": I got a jar of sap the cutters dropped at the burnt camp and put a drop on my tongue at Nesh-Deeka's table. She wrote down what I said while it held me: the ship's hold, roots grown up through its deck, a door nobody built, a dry voice without words. She has word that the Hist of Low-Reed Village, east of Lilmoth, has turned its face. From "The Tree That Turned Its Face": At Low-Reed Village the root-herald said the Hist shut eleven nights ago and the eggs in its pool died; the village blamed Pays-Late, the tree-minder. Pays-Late told me the truth: the Hist's root was cut, its sap drawn off and the cut sealed with his own gum, and he hid it, fearing the blame. I took the jars of the Hist's sap from two men on a dry rise north of the leech water, each with a knotted cord at the wrist, like the woman who burned the gang's camp. I gave the jars to Pays-Late on one condition, that he tells the root-herald himself that he found the cut and hid it. The cell drew this tree's sap into jars, as it drew the cutting's. What does it want with it? You are standing in Salts-The-Catch's house in Lilmoth with Nesh-Deeka.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-lw6w30cc/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-lw6w30cc/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-lw6w30cc/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-lw6w30cc/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-lw6w30cc/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-lw6w30cc/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-lw6w30cc/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-lw6w30cc/play 'take <thing>'   /tmp/ptb-lw6w30cc/play 'use <thing or door>'   /tmp/ptb-lw6w30cc/play 'wait'
  /tmp/ptb-lw6w30cc/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-lw6w30cc/play 'pick <lock> win|fail'   /tmp/ptb-lw6w30cc/play 'pickpocket <person>'   /tmp/ptb-lw6w30cc/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-lw6w30cc/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-lw6w30cc/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: Helstrom Behind Its Marsh
Journal entry (Helstrom Behind Its Marsh): I have seen a Hist cut at the root, and its sap in the cell's jars. I'm to tell Nesh-Deeka at Salts-The-Catch's house in Lilmoth what I found at Low-Reed Village.
New objective: Tell Nesh-Deeka at Salts-The-Catch's house in Lilmoth what happened at Low-Reed Village.

You are in Salts-The-Catch's House, Lilmoth.
People: Salts-The-Catch (a person); Nesh-Deeka (a person)
Things: nothing of note
Doors: none

Play.

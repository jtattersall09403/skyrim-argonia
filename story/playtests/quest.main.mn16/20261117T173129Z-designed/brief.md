You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I now hold two seal-stones: Blackrose and Gemin (taken from the drowned hall; nobody there would talk, and I did not need to fight). About 350 gold, Reel-Ka armour, rapier, 2 lockpicks, 3 paralysis poisons, sap jar, keystone, eye-setting. The Gemin tablet says: the Eye used in place at the Root strengthens every tree; lifted from its place it cuts every tree off from every other and the weak die alone. The king sealed it so no one hand could do either alone. Still needed: third stone from the deepest hall of Vorannuhl (boat, near Noota Nara). Then the Kings Gate under Teku-Sul Spire (dive from Bell Station). Rivals: the Unbound (who drain trees) and the Collector Ennodius Vanin at Blackrose. Open: why the Unbound drain trees, what moans in the Fort Chalkmoth cellar, how Nesh-Deeka knows about the Unbound. Do not lift the Eye.


This version of the game is played in words. You see the game only through one command, `play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  play 'look'                     where you are, who and what is here, the doors, the quest markers
  play 'journal'                  your journal entries, objectives, what each marker points at, what you carry
  play 'go <place | person | thing | marker N>'   travel there (no need to walk the way)
  play 'talk <person>'            start a conversation: the topics you can pick
  play 'say <topic or its number>'   pick a topic while talking; add pass or fail when the game asks for a check
  play 'take <thing>'   play 'use <thing or door>'   play 'read <thing>'
  play 'fight <who> win|lose'     you choose how a fight ends (losing means you load your last save)
  play 'pick <lock> win|fail'   play 'pickpocket <person> win|fail'
  play 'choose <button label or number>'   pick a button when a message box offers choices
  play 'name <your name>'         answer when the game asks your name

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening and why you do this next. For example:
  play 'look' --think 'I have just arrived. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: turn.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Velothi-Ruin-23-M73.
People: Hesh-Var (quest marker); Sarpa Raider; Plague-Dead of Vorannuhl
Doors: Door to Vault of the Household (locked)

*** Quest started: The Deepest Hall ***
Journal: The Eye of Argonia is the old priest-kings' jewel. It sits at the Root, under the sea below Teku-Sul Spire, where the roots of every Hist meet; used there, it can heal every sick tree. The last king shut it behind the Kings' Gate, which opens only with three seal-stones. The third seal-stone lies in the vault of Vorannuhl's deep halls, behind a door of bronze. Sarpa raiders shelter in the outer yard, and one of them, Hesh-Var, carries the bronze key. I'm to get the key: lift it from him unseen, or kill him and take it.
Objective: Get the Bronze Key of Vorannuhl from Hesh-Var in the outer yard. (marker: Hesh-Var, Vorannuhl)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

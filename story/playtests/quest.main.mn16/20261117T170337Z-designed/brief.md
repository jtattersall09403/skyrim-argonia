You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: Notes: I work for the Toh-Reel-Ka as a Reel-Ka. I hold two of three seal-stones (Blackrose Prison and Gemin) and the Warden Vault Key. Gemin stone taken with no fight. The Tablet of the Kings says the Eye at the Root, used where it sits, strengthens every Hist tree; lifted, it cuts all trees from each other and the weak die. So use it in place, never lift it. Still to get: the Vorannuhl stone (deepest hall, boat near Noota Nara). Then dive from Bell Station off Lilmoth to the Teku-Sul gate. Open questions: the Fort Chalkmoth cellar moan and key, how Nesh-Deeka knows the Unbound, why Cuts-the-Old-Knot seals trees she drains (she may want the Eye lifted).


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game.

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
Journal: The third seal-stone lies in the vault of Vorannuhl's deep halls, behind a door of bronze. Sarpa raiders shelter in the outer yard, and one of them, Hesh-Var, carries the bronze key. I'm to get the key: lift it from him unseen, or kill him and take it.
Objective: Get the Bronze Key of Vorannuhl from Hesh-Var in the outer yard. (marker: Hesh-Var, Vorannuhl)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

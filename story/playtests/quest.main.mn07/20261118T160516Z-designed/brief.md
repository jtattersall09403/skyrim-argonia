You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I am Tarin, thief and Voh-Vastei of the Toh-Reel-Ka. I paid Ovinius Calo in Gideon, pickpocketed the smuggler boss key at Gideon South Watch, took the old silver setting and the Collectors note (Ennodius Vanin, an Imperial relic-hunter after the Eye for twenty years). Nesh-Deeka read the ship name inside: the Pale Harvest, a Company freighter sunk in Hatandros Bight, east coast south of Thorn, with a Gideon dealer stock aboard. She paid 100 gold, so I have about 430 gold, plus the setting, the note, lockpick, armour and Hist blessing. The Unbound asked after the glass Eye in Gideon a month ago; she says we listen. Next lead: the wreck at Hatandros Bight. Still unknown: Cuts-the-Old-Knot, seal paste, Xeech-Leel, Umbriel.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: fight.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Wreck of the Pale Harvest.
Doors: Door to The Pale Harvest
A quest marker points to Drowned Captain, at The Pale Harvest.
A quest marker points to Ysan Jetty, at Ysan.
A quest marker points to Captain's Strongbox, at The Pale Harvest.

*** Quest started: The Pale Harvest ***
Journal: Nesh-Deeka sent me to the wreck of the Pale Harvest in Hatandros Bight, a short swim out from Ysan's jetty. I need to get into the hold, where the drowned crew walk, and open the captain's strongbox. I may fight them, or steal past them and pick its lock, a hard one; the captain carries its key. The drowned attack whoever they see, so a quiet player who is seen has a fight on their hands.
Objective: Open the captain's strongbox in the wreck of the Pale Harvest. (marker: Captain's Strongbox, Drowned Captain, Ysan Jetty)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

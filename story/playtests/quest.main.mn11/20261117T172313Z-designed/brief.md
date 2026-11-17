You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I work for Nesh-Deeka in Helstrom and am now Toh-Wo, Secret-Speaker, second rank, reporting to her officer Never-Writes-Twice. At Vicrium Ah-Zish key did not reach my pack despite persuasion and 100 gold (gold was unchanged), so I went through the old adit and took the knights map from the strongbox. The map shows seven towers in the sea and the Grey Tooth crag, the seamark of Skeith Isle, reached by boat to Archon and Arorha. Nesh-Deeka said this is a step towards the Eye of Argonia at the Root and that the Unbound had not reached Vicrium; she said only we listen. I carry the rapier, about 950 gold, lockpicks, Grey Seal x3, Pale Harvest key and other items, the disc, keystone and eye-setting. Never-Writes-Twice warned me of Cuts-the-Old-Knot, once of the order, mad on sap, killed her minders. Still unknown: what the Root and Eye are, how the order listens, why the Unbound seal trees, the seven towers, and the Collector Ennodius Vanin. Next: Skeith Isle, the Unbound, the Collector.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: sneak.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.
Map marker added: Grey-Tooth

You are at The Grey Tooth.
People: Collector's Hireling; Collector's Hireling; Collector's Hireling
Things: Vanin's Rubbing (quest marker)
Doors: Door to Grey Tooth Cave (quest marker)

*** Quest started: The Grey Tooth ***
Journal: Never-Writes-Twice read the parchment map from Vicrium and named the tooth-shaped crag: the Grey Tooth, the seamark of Skeith Isle. The Collector's hired men are camped at the foot of its goat-path and dig in a small cave on its north face. The order hunts the Eye of Argonia, the old kings' jewel that can heal every sick Hist, which lies at the Root, the place under the sea where the roots of every Hist meet. I'm to find out what they found in the Grey Tooth Cave. I may fight them or slip past them.
Objective: Find what the Collector's men found in the Grey Tooth Cave. (marker: Door to Grey Tooth Cave, Vanin's Rubbing)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

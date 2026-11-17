You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: My notes so far. I'm a stranger freed from an Owing reed gang (the Owing is the marsh's sentence of owed work) to work for the Toh-Reel-Ka, the secret warriors of the Xeech-Leel, who rule Black Marsh. The order was made after Umbriel (when the An-Xileel used Lilmoth's mad Hist to bring a flying city down on the marsh) so that no tree, or anyone allied with a tree, can do it again. A Hist is a great grey tree every village is built round, with its eggs in a pool at its foot; its sap brings visions. The trees are falling sick: their sap scars close up, the bark darkens and the egg-pools cool.

The Unbound, a cult of tribeless Argonians led by Cuts-the-Old-Knot, drain the trees' sap and then seal the scar with a grey paste. I found out at Eurydike that the paste is a paralysis poison. My question, which I wrote in my journal: if they want the sap, why seal the tree afterwards? If she wanted the trees dead she could just kill them. We think she brews the sap into a draught strong enough to kill the beast that guards the Root, where every tree's roots meet under the sea. There, behind a gate the old kings sealed, lies the Eye of Argonia, the priest-kings' jewel; used where it sits it could heal every tree. The order wants me to find it first and use it there.

The hunt so far: a fake glass Eye in Gideon led to its old setting at the South Watch (a relic-hunter called the Collector, Ennodius Vanin, got there first and left me a polite note); a ship's name in the setting led to the wreck of the Pale Harvest and a Kothringi keystone; the Chime-Keepers' elder at Toklea told me, for raising her family's grave-stake at Zul-Etha, that it opened the knight-captain's tomb at Eurydike; the bronze disc there bore the mark of Vicrium mine, and in Vicrium's lower galleries I found an old map of seven towers standing in the sea and a crag like a tooth on an island.

My handler Nesh-Deeka, in Nesh-Deeka's House in Helstrom, always knows more than she should about where the Unbound have been; asked how, she says "we listen" and changes the subject. After Vicrium she made me a Toh-Wo, the second rank, and passed me to her officer, Never-Writes-Twice, who stands at the back of the same house. Never-Writes-Twice told me Cuts-the-Old-Knot was one of the order's own who went mad on sap and killed her minders. She knows the crag on the map: the Grey Tooth, the seamark of Skeith Isle. I'm to go there; boats run to Archon and on to Arorha on Skeith Isle.


This version of the game is played in words. You see the game only through one command, `play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  play 'look'                     where you are, who and what is here, the doors, the quest markers
  play 'journal'                  your journal entries, objectives, what each marker points at, what you carry
  play 'go <place | person | thing | marker N>'   travel there (no need to walk the way)
  play 'talk <person>'            start a conversation: the topics you can pick
  play 'say <topic or its number>'   pick a topic while talking; add pass or fail when the game asks for a check
  play 'take <thing>'   play 'use <thing or door>'   play 'read <thing>'
  play 'fight <who> win|lose'     you choose how a fight ends (losing means you load your last save)
  play 'pick <lock> win|fail'   play 'pickpocket <person> win|fail'

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

You are at The Grey Tooth.
People: Collector's Hireling; Collector's Hireling; Collector's Hireling
Things: Vanin's Rubbing (quest marker)
Doors: Door to Grey Tooth Cave (quest marker)

*** Quest started: The Grey Tooth ***
Journal: Never-Writes-Twice read the parchment map from Vicrium and named the tooth-shaped crag: the Grey Tooth, the seamark of Skeith Isle. The Collector's hired men are camped at the foot of its goat-path and dig in a small cave on its north face. I'm to find out what they found in the Grey Tooth Cave. I may fight them or slip past them.
Objective: Find what the Collector's men found in the Grey Tooth Cave. (marker: Door to Grey Tooth Cave, Vanin's Rubbing)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

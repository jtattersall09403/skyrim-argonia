You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: Notes: Down into Vicrium done. At Vicrium, Ah-Zish dialogue said it gave me the key (persuade, then 100 gold) but nothing reached my pack, so I went through the Old Lower Adit and took the Old Parchment Map from the Knights Strongbox; a smuggler was there but I did not fight. I gave it to Nesh-Deeka in Helstrom, who named me Toh-Wo, Secret-Speaker (second rank), paid 200 gold and gave me Toh-Wo Rapier. I now report to her officer Never-Writes-Twice, who identified the crag as the Grey Tooth, seamark of Skeith Isle, reached by boat to Archon and Arorha. She warned me off Cuts-the-Old-Knot, a former order member gone mad on sap who killed her minders. I carry the rapier, lockpicks, Grey Seal paralysis poison x3, bronze disc, Old Silver Setting, Unbound note, keystone, and about 850 gold (the 100 for the key may or may not have been taken). Next: go to Archon and Arorha and take a boat to Skeith Isle for the Eye of Argonia, which heals every tree and lies at the Root under the sea. Open questions: where the seven towers are, why the Unbound drain trees, how the order knows things (we listen).


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
Journal: Never-Writes-Twice read the parchment map from Vicrium and named the tooth-shaped crag: the Grey Tooth, the seamark of Skeith Isle. The hired men of the Collector, Ennodius Vanin, an Imperial relic-hunter who hunts the Eye too, are camped at the foot of its goat-path and dig in a small cave on its north face. She wants to know what they found in the Grey Tooth Cave. I may fight them or slip past them; if they see me, they will fight.
Objective: Find what the Collector's men found in the Grey Tooth Cave. (marker: Door to Grey Tooth Cave, Vanin's Rubbing)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

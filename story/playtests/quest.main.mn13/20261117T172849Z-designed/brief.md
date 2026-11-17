You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I am Toh-Wo, Secret-Speaker, working for Nesh-Deeka under Never-Writes-Twice in Helstrom. Quest The Grey Tooth done: the Collector Vanins rubbing at the Grey Tooth cave led me to the wreck of the Stormwidow on Skeith Isle. I killed three Unbound scouts there and took the kings marker stone, which shows seven towers with one cut deeper. I gave the stone to Never-Writes-Twice and she paid 100 gold. The towers are the drowned spires off Lilmoth; the divers of Bell Station, an islet east of Lilmoth reached by boat from Lilmoth, will know which one. Next step: go to Bell Station. The order hunts the Eye of Argonia at the Root, where all Hist roots meet. The Unbound (Cuts-the-Old-Knot) seal tree scars with a paste of grey caps and dried root after drawing sap; I carry the Recipe for the Seal and 3 Unbound Seals, plus the rapier, about 1050 gold, lockpicks, 3 Grey Seals, Pale Harvest key, disc, keystone and eye-setting. Tah-Leesh, a wounded Unbound scout left alive at the wreck, said Cuts-the-Old-Knot tells the order to ask what moans in the cellar of Fort Chalkmoth (Archwarden fort, Chixathe Mesa above Noota Nara). Never-Writes-Twice calls it nothing, but I mean to check it myself. Still unknown: what the Root and Eye really are, what moans in the cellar, and the Collector, who is hunting the Eye too.


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
Map marker added: Bell-Station

You are at Bell Station.
People: Meer-Tasi (quest marker); Sees-Below (quest marker)

*** Quest started: The Kings' Gate ***
Journal: Never-Writes-Twice says the marked tower is one of the drowned spires off Lilmoth, and the divers of Bell Station will know which. This is the hunt of my order, the Toh-Reel-Ka, the Xeech-Leel's secret warriors. The Toh-Reel-Ka hunt the Eye of Argonia, the old kings' jewel that can heal every sick Hist, which lies at the Root, the place under the sea where the roots of every Hist meet, before the Unbound, the tribeless cult of Cuts-the-Old-Knot, can reach it. My own errand to Fort Chalkmoth may wait or come first. I'm to ask Meer-Tasi, the steward of Bell Station, on an islet east of Lilmoth, which tower the stone marks.
Objective: Ask Meer-Tasi, the steward of Bell Station, which tower the marker stone shows. (marker: Meer-Tasi, Sees-Below)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I set the three seal-stones in the Kings' Gate (they stay there) and it opened. With Cuts-the-Old-Knot I killed the hydra Guardian of the Root in Guardian's Hall. Its body holds treasure, which I have not looted. A door at the hall's far end leads to the Root and the Eye of Argonia. The final choice is still mine: use the Eye in place (heals every tree, dreams continue) or lift it (ends the dreams, about three in ten trees die, the order breaks). I promised Cuts nothing about the Eye. Her claims about the sap-fed dreamers in the Fort Chalkmoth cellar and Never-Writes-Twice lying are unverified. I carry Eye-Setting, Keystone, Grave-Stake, 3 Paralysis Poison, Sap-Jar, Order-Pike, Reelka armour, Rapier, Bronze Key, Bronze Disc, Parchment Map, Unbound-Note, 2 lockpicks, 1650 gold.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. Where the quest offers a choice of how it ends, you mean to take this one: e-give.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Sunken-Ruin-23-M112.
A quest marker points to The Eye of Argonia, at The Root.
Nobody and nothing of note is here.

*** Quest started: The Eye ***
Journal: The Root is where the roots of every Hist meet. The Eye of Argonia, the old kings' jewel, sits among them: used where it sits, it heals every tree; lifted, it parts them for good. Beyond the guardian's hall lies the Root, where the roots of every Hist meet, and the Eye of Argonia sits among them. I'm to go to the Eye and decide what to do with it.
Objective: Go to the Eye of Argonia in the Root's chamber. (marker: The Eye of Argonia)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

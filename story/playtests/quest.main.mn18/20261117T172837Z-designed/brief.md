You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: Notes: I took the three seal-stones (Blackrose, Gemin, Vorannuhl) to Never-Writes-Twice in Helstrom. She made me Ka-Deelith of the Toh-Reel-Ka and gave me the pike, gauntlets and boots. At the sunken ruin (Teku-Sul) Cuts-the-Old-Knot met me without stones. She says the order keeps sap-fed dreamers in the Fort Chalkmoth cellar and sees the marsh through them, and that Never-Writes-Twice kept the key and lied. I chose to believe her and not fight her. She will fight the guardian beside me past the gate. I still carry the stones, Eye-Setting, Keystone, gold, poison and the rest. Next is to set the stones in the Kings' Gate. The final choice is mine at the Eye: use it in place (heals every tree, dreams continue) or lift it (ends the dreams, about three in ten trees die, the order breaks). I promised Cuts nothing about the Eye. I could not verify her claims. Unknown: what the guardian is and what is truly in the Fort Chalkmoth cellar.


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

You are at Sunken-Ruin-23-M112.
Doors: The Kings' Gate (locked) (quest marker)

*** Quest started: The Guardian ***
Journal: Beyond the Kings' Gate lies the Root, where the roots of every Hist meet, and the Eye of Argonia, the old kings' jewel, sits there. I'm to set the three seal-stones in the empty sockets of the Kings' Gate.
Objective: Set the three seal-stones in the Kings' Gate. (marker: The Kings' Gate)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: Grey Tooth quest done. The Grey Tooth cave niche was empty; a rubbing said the stone went to the Stormwidow, beached on Skeith Isle south-west shore. I took the Kings Marker Stone from its ballast crate (Unbound scouts were there; a wounded scout, Tah-Leesh, did not fight). I also took the Unbounds Recipe for the Seal, signed C.: grey caps and dried root ground into paste, numbs, pressed into the scar after the drawing. I still carry it. I gave the stone to Never-Writes-Twice in Helstrom and got 100 gold. She says the seven towers are the drowned spires off Lilmoth in Benthic Yobesh; the divers of Bell Station, an islet east of Lilmoth reached by boat from Lilmoth, know which tower is marked. Tah-Leesh said Cuts-the-Old-Knot tells the Toh-Reel-Ka to ask what moans in the cellar of Fort Chalkmoth (Archwarden fort, Chixathe Mesa above Noota Nara). Never-Writes-Twice dismissed it, which I find suspicious. Next: Bell Station for the tower, or Fort Chalkmoth first. The Collector Vanin is also digging ahead of us.


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
Map marker added: Fort

You are at Fort Chalkmoth.
People: Sakeeus-Wan (quest marker); Sarpa Raider; Sarpa Raider; Sarpa Raider
Doors: Door to Fort Chalkmoth Keep (locked); Door to Fort Chalkmoth Guardroom (quest marker)

*** Quest started: The Cellar Door ***
Journal: Never-Writes-Twice says Fort Chalkmoth is a fort like any other, but a wounded Unbound scout told me to ask what moans in its cellar. This is my own errand, not the order's; the hunt waits at Bell Station and either may come first. Fort Chalkmoth is the Archwardens' fort on the Chixathe Mesa above Noota Nara. I'm to get into the fort and see its cellar: the wall captain at the gate may let me in, or I may find another way in unseen.
Objective: Get into Fort Chalkmoth's keep, by the wall captain's leave or unseen. (marker: Sakeeus-Wan, Door to Fort Chalkmoth Guardroom)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

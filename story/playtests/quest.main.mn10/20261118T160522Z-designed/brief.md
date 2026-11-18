You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I am Tarin, thief of Nesh-Deeka house in Helstrom. I have about 850 gold, the Kothringi Keystone, the Old Silver Setting, my gear, 3 Grey Seal paralysis poisons from the Unbound packs, and the Knight-Captain Bronze Disc. I opened the tomb at Eurydike quietly and gave the disc to Nesh-Deeka. She says the pick-and-tower mark is Vicrium, an old ochre and alum mine in the clay country behind Seafalls in Okuwun Rahei, in the east. The knights kept a strongbox there. This is the trail to the Eye of Argonia, which lies at the Root under the sea and can heal every tree. The Unbound are ahead of us. They drain trees and then seal the scar with the grey paralysis paste, and nobody can say why. Nesh-Deeka says it does not matter, but it nags at me. She knows the Unbound moves because "we listen", and she does not say who listens. Still unknown: Cuts-the-Old-Knot, Xeech-Leel, Umbriel and Ennodius Vanin. Next: go to Vicrium.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: key.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Vicrium.
People: Ah-Zish (quest marker); Crocodile
Doors: Door to Lower Galleries (locked); Old Lower Adit

*** Quest started: Down into Vicrium ***
Journal: Nesh-Deeka knew the mark on the knight-captain's disc: Vicrium, an old mine behind Seafalls, where the knights kept a strongbox. I should go there and ask at the mine; Ah-Zish is its gallery-boss.
Objective: Ask Ah-Zish, the gallery-boss of Vicrium, about the knights' strongbox. (marker: Ah-Zish)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: Notes: I work for Nesh-Deeka (Toh-Reel-Ka, Helstrom). The elder Hums-the-Long-Note of Toklea told me, in return for her family grave-stake (I raised it from the Zul-Etha drowned chest without fighting the crocodiles, and gave it to her), that the Kothringi Keystone opens the knight-captain tomb at Eurydike, a roofless Kothringi hall just north of Gideon. The captain was buried with what marked the kings road to the Root. Nesh-Deeka knows the Unbound have been asking Gideon diggers about Eurydike; she says we listen, and told me to hurry. She paid me 100 gold, so I have about 700. I still carry the keystone, Pale Harvest strongbox key, Old Silver Setting, The Collector note, smuggler key. Next: go to Eurydike near Gideon and open the tomb before the Unbound and the Collector (Ennodius Vanin). Unknown: what the Root and the Eye really are, and how Nesh-Deeka knows what she knows.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: turn.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Eurydike.
People: Restless Knight; Unbound Digger
Things: Unbound Pack (quest marker); Knight-Captain's Tomb Chest
Doors: Door to Knight-Captain's Tomb (locked)

*** Quest started: The Knights' Tomb ***
Journal: Nesh-Deeka sent me to Eurydike, the roofless hall of the Kothringi knights north of Gideon, to open the knight-captain's tomb with the keystone; the knights once guarded the kings' road to the Root, the place under the sea where every Hist's roots meet and the Eye of Argonia lies. The knights' dead walk the barracks wing, and the Unbound got there before me. I'm to search the Unbound's packs by their fire on the way to the tomb. I may fight, slip past, or turn the dead with Restoration.
Objective: Search the Unbound's packs in Eurydike's barracks wing. (marker: Unbound Pack)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

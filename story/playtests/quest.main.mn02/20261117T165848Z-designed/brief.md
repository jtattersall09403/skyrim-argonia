You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: What I know so far (stand-in for MN01's notes, written from MN01's design until MN01's own run passes):

- I woke in the hold of a work barge moored at Ashgate Landing, a reed-cutters' camp on the river west of Loriasel, in
  Black Marsh. I was sent there to serve the Owing: months of owed work given in place of a cell. Nobody there knew me.
- Okeeh, the gang's cook, asked my name and my trade. I told her I was a hunter (Archery, Sneak, Light Armor, Alchemy
  and One-Handed each came a little easier). I carry two lockpicks.
- Dralin Uveran, the Dunmer gang-master, met me on the landing. My name was struck from his roll this morning on an
  order brought by Vosh-Leera, the root-herald of Jal-Veesa (a root-herald speaks for a town's elders and its tree to
  outsiders). I owe no months. He doesn't know why she wants me and is sour about losing a cutter.
- I'm to go east up the road to Vosh-Leera's House in Jal-Veesa. On the way, at Reed-Sill Weir (the first camp on the
  road, where it meets the creek), Jal-Veesa's tree-minder wants Sithis' beard, a grey moss hanging over the creek
  below the weir. There are crocodiles under the weir: I can fight them, shoot them from the log walk on top of the
  weir, or keep out of their sight.
- A Hist is one of the great thinking trees of Black Marsh: tower-tall, pale grey bark, roots standing out of the water,
  a pool of eggs at its foot. Every Argonian village is built round one; if it dies, no egg there hatches again.
- Jal-Veesa is the Sedge-Wardens' town of stilt houses round a pool; the tall grey tree in the pool at the middle is
  its Hist, which has looked poorly lately.


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

You are at Outpost-M11-M63.
People: Young Crocodile; Young Crocodile
Things: Sithis' Beard (quest marker)

*** Quest started: The Dry Tree ***
Journal: Dralin Uveran sent me east up the road to Vosh-Leera, the root-herald of Jal-Veesa, who had me freed. On the way, Jal-Veesa's tree-minder wants Sithis' beard, a grey moss hanging over the creek below Reed-Sill Weir. Crocodiles lie under the weir. I can fight them, shoot them from the log walk on top of the weir, or keep out of their sight. I'm to pick the moss.
Objective: Pick Sithis' beard below Reed-Sill Weir. (marker: Sithis' Beard)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

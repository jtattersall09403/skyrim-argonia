You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: My notes so far. I came up the river on an Owing barge to cut reed at Ashgate Landing (the Owing is the marsh's sentence: months of owed work instead of a cell), but my name was struck off the gang's roll on an order from Vosh-Leera, the root-herald of Jal-Veesa. She works for the Toh-Reel-Ka, the "Secret Warriors" of the Xeech-Leel, who rule Black Marsh. The order was made after Umbriel, when the An-Xileel used Lilmoth's mad Hist to call a flying city down on the marsh; it exists so no tree, and no one allied with a tree, can do that again. They recruit strangers with no ties like me because we are useful and cheap.

A Hist is a huge grey tree that every Argonian village is built round; its eggs lie in a pool at its foot and its sap shapes hatchlings and brings visions. Trees are falling sick: the scar where the minder draws sap closes, the bark darkens, the egg-pool cools. Jal-Veesa's tree is sick. I drank a cup of sap and had a vision that led me to Teel-Fen Weir, where the young tree's scar was sealed with a grey paste, and to a hide where three of the Unbound (a cult of tribeless Argonians who drain sap) kept jars of sap. Their note sent me to Karsh-Naal Camp, where I freed Sesk, a Naga who drew sap for them. She named their leader, Cuts-the-Old-Knot, said the sap is for a draught to do with "the Eye", and called the grey paste "the seal".

Vosh-Leera sent me by the rootworm to the order's handler, Nesh-Deeka, in her house in Helstrom. I got a jar of stolen sap off an Unbound go-between there and she made me a Voh-Vastei, the order's first rank (I got light armour and 200 gold). She told me the Eye of Argonia is the old priest-kings' jewel, cut from Hist amber, lying at the Root (where all the trees' roots meet, under the sea) behind a gate the old kings sealed; used there it could heal every tree. We think Cuts-the-Old-Knot's draught is to kill whatever guards the Root. The order wants me to find the Root first and use the Eye where it sits. Her one lead: an "Eye of Argonia" is for sale in Gideon. The rootworm goes there from Helstrom's city tree. I'm to go to Gideon.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: talk.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Gideon.
People: Ovinius Calo (quest marker)
Things: Eye of Argonia (Glass)
A quest marker points to Rootworm Landing (Helstrom), at Helstrom.

*** Quest started: The Glass Eye ***
Journal: Nesh-Deeka made me a Voh-Vastei of the Toh-Reel-Ka and gave me my first lead: someone in Gideon's market is selling an "Eye of Argonia". I'm to ride the rootworm from Helstrom's city tree to Gideon and find the dealer who sells it. Nesh-Deeka says Gideon's dealers tell the truth for a little persuasion or a few coins, and keep their papers in their pockets.
Objective: Find the dealer selling the Eye of Argonia in Gideon's market. (marker: Ovinius Calo, Rootworm Landing (Helstrom))

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

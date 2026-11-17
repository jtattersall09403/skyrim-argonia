You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: I am Toh-Wo, now Reel-Ka of the Toh-Reel-Ka, in Helstrom. The Kings Gate quest is done: Teku-Sul Spire off Lilmoth has a great gate to the Root with three sockets, guarded by the ghost of Sul-Xeeth. The three seal-stones are at Blackrose Prison (warden vault, easiest), Gemin (flooded vaults) and Vorannuhl (deepest hall, worst). Never-Writes-Twice ordered me to take all three before the Unbound; markers are set. Fort Chalkmoth cellar (what moans there) is still unchecked. Still unknown: what the Root and Eye truly are, and who the Collector is. I carry the rapier, about 1350 gold, lockpicks, 3 Grey Seals, 3 Unbound Seals, Recipe for the Seal, Pale Harvest key, disc, keystone, eye-setting, Reel-Ka cuirass and helm. I need waterbreathing for dives unless my Argonian blood suffices.


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: guest.

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you are expected to do next and where, what options you have, and whether there is any word, name, person or thing you do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with   play 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your commands, give the same notes with
  play end '...'
and stop.

---
Your game has just begun. This is what you see:

A new game.

You are at Blackrose-Prison.
People: Corvus Ulvius (quest marker); Blackguard Heir
Doors: Door to Raj-Kaal's Hall
Corvus Ulvius walks up to you and speaks.
Corvus Ulvius: Corvus Ulvius, outside the gate. Tells: this is the Rose, and the Blackguards' heirs born in it hold it now; strangers who walk in are killed on the walls. He lets a stranger in as a guest three ways: 300 gold to him, words good enough to move him, or a duel with him, fists and steel, until one yields. A guest walks the yard and the hall and nobody touches them. Anyone who climbs the walls without his leave is fair game, and anyone who kills him has the whole Rose to fight. If the player asks what they want inside, he says the raj-kaal Okaz-Teel keeps the old warden's vault in his hall and the key on his belt, and he already has a buyer for what lies in it, the Imperial in the hall. Offers topic.mn14-toll, topic.mn14-persuade and topic.mn14-duel as answers. Does: nothing.

*** Quest started: The Thief's Stone ***
Journal: I serve the Toh-Reel-Ka, the secret warriors of the Xeech-Leel who rule Black Marsh. We hunt the Eye of Argonia: a great jewel the old priest-kings cut from Hist amber, the hardened sap of the trees. It lies at the Root, a chamber under the sea below Teku-Sul Spire where the roots of every Hist in the marsh meet, and it binds them together; used where it sits, it can pour strength into every sick tree. The last king shut the Root behind the Kings' Gate, which opens only with its three seal-stones. Never-Writes-Twice sent me after the three seal-stones. A dead thief's stone lies in the warden's vault at Blackrose Prison, whose people, the Blackguards' heirs, attack strangers on sight. Their gate-captain stands outside the gate. I'm to get in: as a guest past the gate-captain (a toll, words or a duel), unseen past the walls, or by force.
Objective: Get into Blackrose Prison; the gate-captain stands at the gate. (marker: Corvus Ulvius, Blackrose Prison)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you already know: My notes so far. I'm a stranger freed from an Owing reed gang to work for the Toh-Reel-Ka, the secret warriors of the Xeech-Leel, who rule Black Marsh; the order exists so that no Hist tree, or anyone allied with one, can bring another Umbriel (when the An-Xileel used Lilmoth's mad tree to call a flying city down on the marsh). Hist are the great grey trees every village stands round, with eggs in pools at their feet. They are falling sick: their sap scars seal shut and their pools cool. The Unbound, a cult of tribeless Argonians led by Cuts-the-Old-Knot, drain the sap and seal the scars with a paralysis poison (I learned the recipe at the Stormwidow). My open question: why seal a tree you drain, when she could just kill it? Her sap goes into a draught to kill the guardian of the Root, where all the trees' roots meet, and where the Eye of Argonia lies behind the old kings' gate. The order wants me to use the Eye there to heal the trees.

I've followed the hunt from a glass Eye in Gideon to a wreck, a Kothringi keystone, a tomb at Eurydike, Vicrium mine's map, and the Grey Tooth on Skeith Isle, where the Collector (Ennodius Vanin, a relic-hunter) had dug first; the marker stone from the wreck of the Stormwidow showed a drowned tower off Lilmoth. A wounded Unbound scout told me to ask what moans in the cellar of Fort Chalkmoth. Never-Writes-Twice, my officer (at the back of Nesh-Deeka's House in Helstrom), says it's a fort like any other and that Cuts-the-Old-Knot was one of theirs who went mad on sap and killed her minders. I went to see: in the fort's store were jars of Hist sap from Jal-Veesa, though the fort has no tree; the gaoler said "They sleep, and they dream. That is all they do down there"; behind the locked cellar door something moans, and its key isn't in the fort. Nesh-Deeka always knows more than she should about the Unbound and won't say how.

At Bell Station the steward named the tower: Teku-Sul Spire. I dived down; inside there's air, and a great gate with three empty sockets. The ghost of a priest of the old kings said a seal-stone belongs in each, and named where each was taken: a thief's cell in Blackrose Prison, the flooded vaults of Gemin, and the deepest hall of Vorannuhl. Never-Writes-Twice made me a Reel-Ka, the third rank (heavier armour, free beds in the Archwardens' forts, 300 gold) and ordered me to take all three stones before the Unbound do. All three places are marked; I can do them in any order. Blackrose is reached by boat; Gemin is a walk across the marsh from Jal-Veesa (rootworm); Vorannuhl is near Noota Nara (boat).


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

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. Never try to test or break the game. The game expects a character of your build to favour this way through where there is a choice: pick.

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
Journal: The Eye of Argonia is the old priest-kings' jewel. It sits at the Root, under the sea below Teku-Sul Spire, where the roots of every Hist meet; used there, it can heal every sick tree. The last king shut it behind the Kings' Gate, which opens only with three seal-stones. Never-Writes-Twice sent me after the three seal-stones. A dead thief's stone lies in the warden's vault at Blackrose Prison, whose people, the Blackguards' heirs, attack strangers on sight. Their gate-captain stands outside the gate. I'm to get in: as a guest past the gate-captain (a toll, words or a duel), unseen past the walls, or by force.
Objective: Get into Blackrose Prison; the gate-captain stands at the gate. (marker: Corvus Ulvius, Blackrose Prison)

The game pauses. Answer these four questions from what the game has shown you, in your own words, numbered, in one command: answer '1. ... 2. ... 3. ... 4. ...'
1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Play.

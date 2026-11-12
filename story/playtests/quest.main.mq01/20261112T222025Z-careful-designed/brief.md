You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. You know nothing else about this game.

This version of the game is played in words. You see the game only through one command, `/tmp/ptb-kytdx757/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-kytdx757/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-kytdx757/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-kytdx757/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-kytdx757/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-kytdx757/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-kytdx757/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-kytdx757/play 'take <thing>'   /tmp/ptb-kytdx757/play 'use <thing or door>'   /tmp/ptb-kytdx757/play 'wait'
  /tmp/ptb-kytdx757/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-kytdx757/play 'pick <lock> win|fail'   /tmp/ptb-kytdx757/play 'pickpocket <person>'   /tmp/ptb-kytdx757/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-kytdx757/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

Stop when the quest you are on ends, when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-kytdx757/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. After that the game asks you a few short questions; answer them in one reply with /tmp/ptb-kytdx757/play answers '...'. Then stop.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.
Quest started: No Name on the Work Roll
Journal entry (No Name on the Work Roll): I woke in the hold of a ship at a pier west of Lilmoth, in Black Marsh, among a gang of Argonians I do not know. I'm to go up the stairs and out onto the pier, where the man who keeps the gang's work roll stands.
New objective: Speak to Buys-The-Months on the pier beside the ship.

You are at Lilmoth.
People: Namorine (a person)
Things: nothing of note
Doors: none

Namorine walks up to you and speaks.
Namorine: "[not yet written; the gist:] Buys-The-Months, on the pier. Spoken first: he walks up to the player as they step off the ship onto the pier and says it (force-greet, open at MQ01 stage 10 only: he walks up again each time until the player asks about work); the same line is this topic if the player speaks first. Tells, in a few sentences: this is the pier at Hereguard Plantation, west of Lilmoth, where big ships can lie, which Lilmoth's shallows cannot take, and that is his ship; everyone in its hold works off an Owing, months of work owed for a debt or a wrong, and he holds their months on his work roll; the player came aboard off the bank at the burnt camp, and no line of his roll is theirs; they owe him nothing, so he cannot hire them out, and he wants them off his pier. Checks: nothing. Does: nothing."
Topics:
  1. Who are you?
  2. Where can I find work, then?

Play.

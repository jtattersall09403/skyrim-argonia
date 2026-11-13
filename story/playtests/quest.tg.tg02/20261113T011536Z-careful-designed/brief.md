You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far, from your journal: From "A Dry Hand in a Wet City": Tilts-The-Jug, who keeps the Night-Reed Chapter's desk, gave me three lockpicks to see how I work. Keeps-What-Floats, a dock thief west of her door, took a sleeping Lookout's necklace of blue jaspers and keeps it in a strongbox under the eaves north-west of the house. I'm to take it back without harming him; Sits-By-The-Water knows his habits. I took the Blue Jasper Necklace out of Keeps-What-Floats's strongbox. I'm to bring it to Tilts-The-Jug inside the house on Soulrest's dock, behind the door beside S'Tabi. I gave Tilts-The-Jug the Blue Jasper Necklace, and because Keeps-What-Floats came to no harm, she paid me a hundred gold. I'm to take the coast ship from Soulrest's dock to Lilmoth, go down the trapdoor north of Pusbottom at the edge of the deep water and speak to Bent-Spine. I went down through the trapdoor north of Pusbottom to the Night-Reed Chapter under Lilmoth, and Bent-Spine, the Chapter's fence, took me in as a Lookout. Tilts-The-Jug had set me to take a stolen necklace back from Keeps-What-Floats without harming him, and what became of him is now part of how she and the Chapter think of me.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-t2z07286/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-t2z07286/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-t2z07286/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-t2z07286/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-t2z07286/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-t2z07286/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-t2z07286/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-t2z07286/play 'take <thing>'   /tmp/ptb-t2z07286/play 'use <thing or door>'   /tmp/ptb-t2z07286/play 'wait'
  /tmp/ptb-t2z07286/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-t2z07286/play 'pick <lock> win|fail'   /tmp/ptb-t2z07286/play 'pickpocket <person>'   /tmp/ptb-t2z07286/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-t2z07286/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-t2z07286/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

Your game goes on. You are a male Argonian.
Journal (The Drowned Lockbox): Bent-Spine, the Night-Reed Chapter's fence, has work for me now that I am a Lookout. I'm to ask him about it, in the Night-Reed Chapter under Lilmoth, down the trapdoor north of Pusbottom.
Objective: Ask Bent-Spine about the work he has.

You are in The Night-Reed Chapter, Lilmoth.
People: Bent-Spine (an Argonian man)
Things: nothing of note
Doors: none

Play.

You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. You came to Blackrose, a town in Black Marsh, looking for work, and found Never-Sold, who keeps the Chainbreakers' house there. The Chainbreakers buy out Owings, debts paid in work. She sent you to Rows-For-Another, eleven years on an Owing of four months for a damaged estate boat. Rows-For-Another would not wait for a buy-out; you talked her into going down the channel out of the estate's reach, knowing the estate's men would be rougher with the next one held. You told Never-Sold, who would not undo it but said the next one held would pay for it. You are back in Never-Sold's house.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-er4kldpy/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-er4kldpy/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-er4kldpy/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-er4kldpy/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-er4kldpy/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-er4kldpy/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-er4kldpy/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-er4kldpy/play 'take <thing>'   /tmp/ptb-er4kldpy/play 'use <thing or door>'   /tmp/ptb-er4kldpy/play 'wait'
  /tmp/ptb-er4kldpy/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-er4kldpy/play 'pick <lock> win|fail'   /tmp/ptb-er4kldpy/play 'pickpocket <person>'   /tmp/ptb-er4kldpy/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-er4kldpy/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long as your journal holds an active objective or something new has started; check the journal after each ending. Stop only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-er4kldpy/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. Then stop; you may be asked a few short questions afterwards.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.

You are in House, Blackrose.
People: Never-Sold (a person)
Things: nothing of note
Doors: none

Play.

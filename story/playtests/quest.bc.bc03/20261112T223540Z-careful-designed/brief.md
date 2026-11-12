You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you know how its quests, journal, map markers and dialogue menus work. What you know so far, from your journal: You came to Blackrose, a town in Black Marsh, looking for work, and found Never-Sold, who keeps the Chainbreakers' house there. She sent you to free Rows-For-Another, who had worked eleven years on an Owing (a debt paid in work) assessed at four months for a damaged estate boat. You paid the estate's steward the Owing's first price from Never-Sold's coin; he struck her page from the estate's book, and by custom the Owing is closed. You gave Never-Sold the page. You are back in her house.


This version of the game is played in words. You see the game only through one command, `/tmp/ptb-52ioil3g/play`, which you run with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  /tmp/ptb-52ioil3g/play 'look'                     where you are, who and what is near you, the doors
  /tmp/ptb-52ioil3g/play 'journal'                  your quests: journal entries and active objectives
  /tmp/ptb-52ioil3g/play 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  /tmp/ptb-52ioil3g/play 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  /tmp/ptb-52ioil3g/play 'talk <person>'            start a conversation: their greeting and the topics you can pick
  /tmp/ptb-52ioil3g/play 'say <topic, answer or its number>'      pick a topic or an answer while talking
  /tmp/ptb-52ioil3g/play 'take <thing>'   /tmp/ptb-52ioil3g/play 'use <thing or door>'   /tmp/ptb-52ioil3g/play 'wait'
  /tmp/ptb-52ioil3g/play 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  /tmp/ptb-52ioil3g/play 'pick <lock> win|fail'   /tmp/ptb-52ioil3g/play 'pickpocket <person>'   /tmp/ptb-52ioil3g/play 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you make of what is happening, what you want, and why you are doing this next. For example:
  /tmp/ptb-52ioil3g/play 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: You are a careful player. You read every line people say and every journal entry, you think about what you have been told before you act, and you like to understand who people are and why. Play as yourself, a real player meeting this game for the first time: follow what interests you, form your own opinions about the people and the story, and do not try to test or break the game.

Stop when the quest you are on ends, when you are truly stuck (say why in your last --think), or when the game says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  /tmp/ptb-52ioil3g/play end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, whether you want to know what happens next, what made no sense, and anything else you noticed or would want. After that the game asks you a few short questions; answer them in one reply with /tmp/ptb-52ioil3g/play answers '...'. Then stop.

---
Your game has just begun. This is what you see:

A new game. You are a male Argonian.

You are in House, Blackrose.
People: Never-Sold (a person)
Things: nothing of note
Doors: none

Play.

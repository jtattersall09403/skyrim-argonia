# Music: the Black Marsh soundtrack

The new world has its own music. It is one score: the same instruments, the same production and one short tune of
our own run through all of it. Each piece still has its own speed, key, lead instrument and mood. The score follows
the plan of a classic open-world score: one main theme, eight exploration pieces, seven battle pieces and three short
stings. Each piece takes one track of the Morrowind score as its reference **for feel**: how it sounds, how it flows
and the mood it sets (pace, pulse, metre, mode, texture, which instruments carry it, where the drums come in, its
shape over time, its dynamics).

Not allowed, ever: transcribing or reproducing a melody or chord sequence (not even described note by note); giving
any Morrowind audio to a generator or analysing an unowned copy (no cover, remix, continuation or style transfer);
naming Morrowind, its composer, a track title, a game or an artist in a generation prompt. The mapping piece ->
reference -> feel lives on this page and in `newworld/sources/music/pieces.json` (`reference`, `feel`); the prompts
are only the shared palette plus each piece's own brief (`style` + `axes`), and a unit test holds that line
(`tools/tests/test_newworld_music.py`).

## The shared palette (in every prompt, word for word)

- **Instruments:** breathy cane reed flutes, plucked wooden tongue drum and thumb piano, hollow log drums, bone and
  wooden clackers, conch-shell horns, low bowed strings over a deep held drone, and a low wordless choir that hums
  and throat-sings. No words, no synths, no electric guitar, no drum kit.
- **Production:** warm, spacious, a humid reverb like a canopy at night, organic, cinematic.
- **The call (our motif):** four notes. Up a perfect fourth, down a half step, down a whole step, then hold. Every
  piece states it at least once, on its own lead instrument.
- **The anchor:** the owner's *Black Marsh Overture* (main-theme slot): 2 min 22 s; starts quiet and dark, builds
  over the first 40 s to full and bright, stays full to about 2 min 5 s, then eases off. The other pieces sit with it.

## Pieces, references and feel

The reference is one track of the game's soundtrack, its title and length checked against the soundtrack's public
track list (Steam store listing of the official soundtrack, 20 tracks). Its feel is written from public descriptions
only (sources below), in plain musical terms.

| Slot | Reference (length) | Feel of the reference | Our piece (brief) |
|---|---|---|---|
| theme | Nerevar Rising (1:54) | stately, about 70 BPM; a lone simple line restated with more instruments each time, growing in volume and scope to a climax on full strings and brass; light and ethereal, not heavy | **owner's Overture** |
| explore-mist | Silt Sunrise (3:11) | slow, free pulse; opens like an orchestra tuning, scattered held tones gathering like a sunrise; a calm spacious middle; ends over busy string ostinati and brass-like interjections | 60 BPM, A minor; held tones gather, thumb-piano middle, churning string figures and conch at the end |
| explore-canopy | Over the Next Hill (3:04) | walking pace in 4; a dark low opening on held bass chords opens into a brighter, ambient field theme; woodwind over light plucked strings | 84 BPM, E dorian; dark bowed-bass opening, then cane-flute walking theme over plucked strings |
| explore-river | The Road Most Travelled (3:15) | flowing, about 76 BPM, a syncopated lilt in the tune; rich layered strings with a solo cello; long crescendos and decrescendos | 76 BPM, G mixolydian; solo cello over layered low strings, two broad arcs |
| explore-hist | Blessing of Vivec (3:16) | slow and austere; a jagged, unflowing solo cello lead; light and dark, major and minor, high and low held in balance | 56 BPM, C minor; humming choir and drone, the call sung softly (round-1 take kept: closest by the proxies) |
| explore-coast | Peaceful Waters (3:06) | slow to moderate, gently rocking; light flute texture, reflective; a warm swell in the middle, a quiet close | 72 BPM, F major, rocking 6/8; reed flute over soft strings, middle swell with log drum and choir |
| explore-highland | Caprice (3:28) | light and playful; a 3-against-4 cross-rhythm in string ostinati; a choir interlude; dissolves into woodwinds alone | 96 BPM, B dorian; plucked cross-rhythm ostinati, choir interlude, reed flutes alone at the end |
| explore-night | Darkened Depths (0:51) | brief, ominous underscore: low held tones, dark, quiet, unresolved | 54 BPM, almost no pulse, F sharp minor; low flute, drone, distant throat-singing; one slow swell |
| explore-rain | Shed Your Travails (3:13) | restful, about 66 BPM; strings and woodwinds in dialogue; an ethereal wordless female choir in the middle; ends on glistening high string tremolo and a fading flute | 66 BPM, D dorian; thumb-piano and flute dialogue, airy high choir, string tremolo and lone flute to close |
| battle-ambush | Ambush (2:33) | fast; a driving violin ostinato with syncopated accents; ABA with a calmer middle | 140 BPM, D minor; driving low strings, log drums, conch call; tense quiet middle, driving return |
| battle-hunt | Hunter's Pursuit (2:17) | fast, relentless; stacked open fourths and fifths in high brass over driving strings | 132 BPM, E minor; string ostinato and hand drums, conch in open fourths and fifths |
| battle-deep | Bright Spears Dark Blood (2:06) | fast, energetic; flowing violin lines over strong percussion; continuous motion | 126 BPM, C sharp minor; flowing string runs over giant drums, dark conch swells |
| battle-skirmish | Dance of Swords (2:13) | fast; rapid descending violin ostinato figures with syncopated counter-rhythms; booming drums against one or two soloists | 150 BPM, A minor; falling string figures, wooden counter-rhythms, reed flute and fiddle soloists |
| battle-war | Drumbeats of the Dunmer (2:03) | stripped back; minimalist repeating drum rhythms that want a resonant, forceful sound; few instruments above | 120 BPM, G minor; repeating war-drum patterns, massed wordless chant |
| battle-water | Stormclouds on the Battlefield (2:11) | sparse, repetitive rhythmic writing; dark, brooding, surging | 128 BPM, B minor; churning gourd and wood rhythm, swirling strings, surges |
| battle-last | Knight's Charge (2:05) | its opening seconds announce the fight; bold, driving, building tension | 136 BPM, F minor; bold opening hit, driving drums and strings, choir swells to a climax |
| sting-levelup | none: an excerpt of our own Overture, as Skyrim cuts its level-up sting from its main theme | Skyrim's level-up tracks (mus_levelup_01-03 in Skyrim - Sounds.bsa, measured): 18.7-19.3 s, a steady body, the peak at 12.0-12.9 s, 20 dB down within 2.0-2.3 s of it, under -40 dB by 16.8-18.6 s | the Overture 1:59.6-2:18.6 (19.0 s): its closing statement into the final chord at 13.8 s, ringing out under a 3.5 s fade; alternatives B 0:25.7-0:45.2 and C 0:33.6-0:52.2 in pieces.json `excerpt_alternatives` |
| sting-death | Fate's Quickening (0:17) | a short jingle, falling and mournful | the call slowed on low flute over a fading drone (round-1 take kept) |
| sting-discovery | The Prophecy Fulfilled (1:11) | angelic choir and a high solo voice; a starry-eyed sense of wonder | thumb-piano and airy choir rising into the call |

### Sources for the feel

- Steam store page of the official soundtrack (track titles and lengths):
  store.steampowered.com/app/451410/The_Elder_Scrolls_III_Morrowind_Soundtrack/
- VGMO (Video Game Music Online), review of the Special Edition soundtrack: vgmonline.net/elderscrolls3/
- RPGFan, music review of the Special Edition soundtrack:
  rpgfan.com/music-review/the-elder-scrolls-iii-morrowind-special-edition-soundtrack/
- Kotaku, "Morrowind Really Did Have The Best Elder Scrolls Music, Didn't It" (the score's pizzicato strings and
  English-horn melodies, lighter and more playful than its successor; Silt Sunrise as an orchestra tuning, a rising,
  churning sun)

UESP's music page and the Discogs listings sit behind a bot check; they were not read.

## How it was made

Model: Google Lyria 3.5 through fal.ai (`google/lyria-3.5`), $0.10 a generation, 44.1 kHz stereo, up to about three
minutes; fal's terms give the requester the outputs for commercial use. Each prompt is the piece's `axes` plus the
shared `style`, with timed sections (`[0:00-0:50] ...`) for the shape over time. Request ids and result files are
kept in `newworld/sources/music/manifest.json` (take `t1` is round 1; `t2`..`t4` round 2), so nothing is paid twice.

Round 2 made two or three new takes of each of the 18 pieces (38 generations, $3.80; round 1 was $1.90) and kept the
best take of each by computable proxies against its brief: length, pulse (onset autocorrelation; it reads battle
pieces at half time), loudness by tenth of the piece against the reference's shape, spectral centroid (brightness)
and onset density. Each piece's kept take and its numbers are in `pieces.json` (`kept`, `measured`). 16 pieces took a
new take; explore-hist and sting-death kept round 1's. The round-1 takes stay in the bucket under `nw/music/round1/`.

Stings: the model writes about a minute even when asked for 15 s, so each sting is briefed as a clear opening gesture
of about 10 s, and the cut is a phrase end picked by onset analysis in the 8-12 s window (the quietest half second
with the fewest note onsets; `cut_s` in `pieces.json`), then a 2 s fade.

## The slots, and how the owner swaps in his own file

Every role is a **slot**: one fixed file, `music/argonia/<slot>.wav`. The game's music records point at slots, never
at pieces, so swapping a file needs no record change.

To put your own music in a slot:

1. Name the file after the slot, for example `explore-mist.mp3`. Accepted: `.wav`, `.mp3`, `.flac`, `.m4a`.
2. Upload it to `s3://argonia-private-050977237313/nw/music/owner/`.
3. Run `python3 tools/newworld/music/soundtrack.py build` on the build machine, then `stack.py stage` on the play
   machine.

The tool converts every slot to 44.1 kHz 16-bit stereo WAV at the same loudness (-16 LUFS integrated, peaks under
-1.5 dB), cuts stings at their `cut_s`, cuts an `excerpt` slot (sting-levelup) from the file in its `of` slot at its `start_s`-`end_s` with its fades, and uses your file in place of ours. Our piece stays in the bucket (`ours/`)
as the alternative: delete your file and build again to go back. `soundtrack.py check` lists each slot and whether
it holds our piece or your file. The theme slot holds the owner's Overture now, and the level-up sting is cut from it at every build: to hear another cut, copy one of `excerpt_alternatives` over `excerpt` in pieces.json and build again.

Loudness: -16 LUFS is a common game-music level, not yet measured against Skyrim's own tracks (their archive is on
the play machine only and was not read while the owner may be playing). Format: the engine plays `.wav` music
tracks; WAV is shipped (about 500 MB). A move to `.xwm` would be a conversion step at deploy on the play machine.

## In game (Bethesda's way, decision 0034)

Measured on Skyrim.esm (2026-11-12): a region names its exploration music type in its sound data (REGN RDMO, for
example the fall forest region -> MUSExploreForestPine); a separate world names a fallback type on the worldspace
(Solstheim's ZNAM); an exploration type cycles single tracks with 30 s silent spacers between them; day tracks carry
`GetCurrentTime >= 6 AND <= 20`, night tracks `>= 22 OR <= 5`; combat, death and level-up are default-object types
(MUSCombat, MUSSpecialDeath, MUSSpecialSuccess) and discovery the four MUSDiscovery types, none of which can be set
per world.

Ours (`tools/ArgoniaPlugin/NewWorldMusic.cs`, data `newworld/sources/music/records.json`, ids in the idspace row
`music`):

- one MUST per slot, file `Data\Music\argonia\<slot>.wav`;
- one exploration type per atmosphere class (a copy of Skyrim's marsh type): the class's day pieces (06:00-20:00),
  then explore-night and explore-hist (20:00-06:00), each followed by Skyrim's silent spacer;
- each of the 24 regions names its class's type; the worldspace names blackwater-swamp's as the fallback;
- the battle pieces join MUSCombat (battle-last and battle-deep also MUSCombatBoss), the stings join
  MUSSpecialDeath and MUSSpecialSuccess, each with `GetInWorldspace(new world) == 1`; every Skyrim track in those
  types gets `GetInWorldspace(new world) == 0` put first, so Skyrim's music is not heard
  in the new world and is unchanged everywhere else. No plugin of the NewWorld profile overrides these records, so
  Skyrim.esm's are the load order's winners and the templates;
- discovering a place plays Skyrim's own discovery stings (the four MUSDiscovery types are left as they are);
  the slot sting-discovery stays in the pack, unused.

| Class (regions) | Day exploration |
|---|---|
| blackwater-swamp (banujha-basin, ultherus-swamp, tulmek-washes, blackwood) | mist, hist, rain |
| green-marsh (okuwun-rahei, nushara-bayou, lake-ulaish, barsaebica) | rain, canopy, mist |
| river-corridor (nha-enasa, valley-of-storms) | river, canopy |
| rainforest (murkwood, arnesian-jungle) | canopy, hist, river |
| highland (chixathe-mesa, aunike-ridge) | highland, river |
| coast-east, coast-south, coast-west (hatandros-bight, padomaic-ocean, benthic-yobesh, cape-percar, sea-of-mists, kotherra-mangroves, topal-bay) | coast, river, mist |
| island (althii-archipelago, aphon-isle, skeith-isle) | coast, highland |

`tools/newworld/assets_audit.py` resolves a MUST's `Data\Music\...` path under `music\` (not `sound\`), so the
readback gate checks every track file against the staged pack.

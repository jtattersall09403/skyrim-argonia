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
| music-levelup | the stock level-up music type, measured traits only | Skyrim's level-up music type (DOBJ LUMS -> MUSC 03B565 MUSSpecialSuccess): a soft, sustained, wide chord wash with no drums or beat, level for eight seconds, swelling gently to one peak two thirds through and gone by 19 s (measurements below) | round-5 take t8, 19 s cut from 4.5 s with a 6 s exponential fade from 13 s, at its own quieter level (`target_lufs` -19); alternatives: takes t11 and t10, and the owner-rejected Overture excerpt 1:59.6-2:18.6 |
| sting-levelup (approved by the owner, 2026-11-12) | the stock level-up sound, feel and shape only | what the player hears at a level-up (measured): the UI sound UILevelUp (SOUN 057B45 -> SNDR 057B44, UI_LevelUp.wav, 10.3 s file): about 4 s of body (peak at 2.8 s), then about 4 s of decay (-38 dB at 6.5 s, -47 dB by 8 s); the music type is the separate, longer layer (music-levelup) | round-4 take t5: from near silence a swell into one bright arrival at 2.6 s, cut at 7.1 s with a 4 s fade from 3.1 s. Every candidate must pass two measured tests: it starts at a phrase start (200 ms RMS at least 12 dB under the following second) and it rises (loudness and brightness climb, the peak 2.5-4.5 s in and 8 dB or more over the first 0.5 s). Alternatives in pieces.json `alternatives`: the Overture's opening 0:00.1-0:09.1 (its only passing moment) and take t6 |
| sting-death | Fate's Quickening (0:17) | a short jingle, falling and mournful | the call slowed on low flute over a fading drone (round-1 take kept) |
| sting-discovery | The Prophecy Fulfilled (1:11) | angelic choir and a high solo voice; a starry-eyed sense of wonder | thumb-piano and airy choir rising into the call; cut at its first 4.0 s, then faded out to the quietest point between 4.0 and 7.5 s (5.28 s; `fade_from_s`, `cut_s`) |

Level-up has two parts, as Skyrim's does: the UI sound UILevelUp (SNDR 057B44, our sting-levelup, 8 s) and the
level-up music type MUSC 03B565 (our music-levelup, 19 s, joined to the type for the new world only). The sting
plays when the HUD's LEVEL UP notice appears; the music type plays when the level-up menu (choose Health, Magicka or
Stamina) opens ([level-up audio](../research/skyrim/level-up-audio.md)).

### Skyrim's level-up music, measured

Read from the player's own `Skyrim - Sounds.bsa` in memory (decoded by ffmpeg, nothing written out, nothing given to a
model), 2026-11-12:

| track | length | LUFS | LRA | envelope | centroid | onsets/s | percussive share | pitched frames | side/mid |
|---|---|---|---|---|---|---|---|---|---|
| MUS_LevelUp_01 | 19.3 s | -13.0 | 11.9 LU | level ~10-15 dB under peak from 0.5 s, swell from 8.5 s, peak 13.0 s, -20 dB 2.5 s later, silent by 19 s | 1311 Hz | 0.57 | 0.12 | 66%, held (median step 0 semitones) | 0.90 |
| MUS_LevelUp_02 | 19.1 s | -14.3 | 10.5 LU | level ~8-13 dB under, steady climb from 8 s, peak 12.0 s, -20 dB in 3.0 s | 1200 Hz | 0.37 | 0.20 | 58%, held | 1.04 |
| MUS_LevelUp_03 | 18.7 s | -13.4 | 10.5 LU | level ~9-11 dB under, climb from 8.5 s, peak 12.0 s, -20 dB in 2.5 s | 1218 Hz | 0.53 | 0.11 | 58%, held | 0.92 |

Brightness sits at 1100-1600 Hz through the body and falls to 100-400 Hz only in the tail. For comparison, Skyrim's
exploration tracks measure -23.1 (day 01), -23.6 (day 02) and -21.7 (night 01) LUFS; their loudest 3 s reach -14.6
to -18.4 against -8.0 to -10.0 for the level-up tracks. So the level-up music is about 9 LU louder than Skyrim's
normal music, not quieter, and 2-3 LU louder than our -16 LUFS slots.

In plain words: a soft, slow, sustained and very wide chord wash with no drums, no beat and no tune to follow, sitting
level for eight seconds, swelling gently to one peak two thirds through (12-13 s), then falling away in under three
seconds and gone by 19 s. It is ambient in character but not quiet in level: played louder than the exploration
music, so it reads as a calm, full affirmation rather than an event.

Ours (round 5, 12 takes at $0.10, one declined by the model's content checker) was briefed from these traits only.
Lyria writes about a minute whatever the brief says, so each take is cut to 19 s at the start whose envelope best
matches Skyrim's mean over 0-13.5 s, with a 6 s exponential fade from 13 s shaped like Skyrim's tail. A take passes
when that cut is within 5 dB mean of Skyrim's envelope, peaks at 10.5-14 s, has at most 1.5 onsets a second, a
centroid of 810-1680 Hz and a percussive share of at most 0.25. Three passed: t8 (kept: shape 2.8 dB, 0.63 onsets/s,
971 Hz, percussive 0.02, side/mid 0.79), t11 (3.0 dB, 1.32, 937 Hz) and t10 (4.6 dB, 1.11, 899 Hz). Ours are
darker (about 900-970 Hz against 1250) and have less percussive energy than Skyrim's; every Lyria take was darker.
The slot is built to -19 LUFS (`target_lufs`): Skyrim's ratio would put it at -7 LUFS, louder still, so the
owner's ear (the -16 excerpt was too loud) sets it 3 LU under our music; `check` measures it against its own target.

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

1. Name the file after the slot, for example `explore-mist.mp3`. A slot with an `excerpt` in pieces.json is cut
   from the file of its `of` slot at its times: change them there to choose another cut. Accepted: `.wav`, `.mp3`, `.flac`, `.m4a`.
2. Upload it to `s3://argonia-private-050977237313/nw/music/owner/`.
3. Run `python3 tools/newworld/music/soundtrack.py build` on the build machine, then `stack.py stage` on the play
   machine.

The tool converts every slot to 44.1 kHz 16-bit stereo WAV at the same loudness (-16 LUFS integrated, peaks under
-1.5 dB; a slot's own `target_lufs` sets a deliberately quieter one), cuts stings at their `cut_s` with the fade out from their `fade_from_s` (else the last 2 s), cuts an `excerpt` slot from the file in its `of` slot at its `start_s`-`end_s` with its fades, and uses your file in place of ours. Our piece stays in the bucket (`ours/`)
as the alternative: delete your file and build again to go back. `soundtrack.py check` lists each slot and whether
it holds our piece or your file, and measures every slot of the built pack: a slot more than 3 LU off its target (-16 LUFS or its
`target_lufs`) or peaking less than 6 dB over that target fails, and `build` ships nothing while any slot fails. The tools use the system ffmpeg
(`/usr/bin/ffmpeg`; `FFMPEG` names another). The theme slot holds the owner's Overture now. To hear an alternative of a slot, copy one of its `alternatives` in pieces.json into the slot and build again.

Loudness: -16 LUFS is a common game-music level; Skyrim's exploration tracks measure -21.7 to -23.6 LUFS and its
level-up tracks -13.0 to -14.3 (above). Format: the engine plays `.wav` music
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
- the battle pieces join MUSCombat (battle-last and battle-deep also MUSCombatBoss), the death sting joins
  MUSSpecialDeath and the discovery sting the four MUSDiscovery types, each with `GetInWorldspace(new world) == 1`; every Skyrim track in those
  types gets `GetInWorldspace(new world) == 0` put first, so Skyrim's music is not heard
  in the new world and is unchanged everywhere else. No plugin of the NewWorld profile overrides these records, so
  Skyrim.esm's are the load order's winners and the templates;
- level-up, in Skyrim's two parts: the UI sound UILevelUp (SNDR 057B44; Skyrim.esm is the load order's winner),
  heard when the level-up notice appears, plays the short slot sting-levelup from
  `Data\Sound\fx\argonia\sting-levelup.wav` (the pack carries that copy beside its music file); the level-up music type
  (MUSSpecialSuccess), heard when the level-up menu opens, plays the longer slot music-levelup, Skyrim's tracks kept out.

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

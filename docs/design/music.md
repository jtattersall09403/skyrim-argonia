# Music: the Black Marsh soundtrack

The new world has its own music. It is one score: the same instruments, the same production and one short tune of
our own run through all of it. Each piece still has its own speed, key, lead instrument and mood. The score follows
the plan of a classic open-world score: one main theme, eight exploration pieces, seven battle pieces and three short
stings. Each piece takes one track of the Morrowind score as its reference **for feel only**: pace, pulse, how full
or sparse it is, which kinds of instrument carry it, how it grows and falls away, its mood.

Not allowed, ever: transcribing or reproducing a melody or chord sequence, giving any Morrowind audio to a generator
(no cover, remix, continuation or style transfer), and naming Morrowind, its composer or its track titles in a
generation prompt. The reference mapping lives on this page only. The prompts hold only our own description.

## The shared palette (in every prompt, word for word)

- **Instruments:** breathy cane reed flutes, plucked wooden tongue drum and thumb piano, hollow log drums, bone and
  wooden clackers, conch-shell horns, low bowed strings over a deep held drone, and a low wordless choir that hums
  and throat-sings. No words, no synths, no electric guitar, no drum kit.
- **Production:** warm, spacious, a humid reverb like a canopy at night, organic, cinematic.
- **The call (our motif):** four notes. Up a perfect fourth, down a half step, down a whole step, then hold. Every
  piece states it at least once, on its own lead instrument.
- **The anchor:** the owner's *Black Marsh Overture* (main-theme slot). Measured by feel: 2 min 22 s, 48 kHz; starts
  quiet and sparse (about -21 dB RMS, dark: spectral centroid near 670 Hz), builds over the first 40 s to full
  (about -14 dB, centroid about 1,350 Hz), stays full and bright (about 1,500 Hz) from 60 s to 125 s, then eases off
  at the end. Notes come densely once it opens up (onset share 0.7). The other pieces sit with it: they have the
  same slow opening into a full middle, battle pieces sit at its full-section brightness, and exploration pieces sit
  at its opening darkness.

## Pieces, references and region use

Feel references are described in plain musical terms. Morrowind's tracks are not on any machine we hold and are
never downloaded, so each reference is described by role and general character, never by note.

| Slot | Role | Feel reference (Morrowind) | Our piece: tempo, key, lead, mood |
|---|---|---|---|
| theme | main theme | the main title: a lone line that grows into a broad, stately full ensemble with choir | **owner's Overture**; our alternative take: 70 BPM, D dorian, reed flute then low strings, awe |
| explore-mist | exploration | the slowest, sparsest exploration track: long held tones, wide space | 60, A minor, thumb piano, hushed |
| explore-canopy | exploration | an easy-walking exploration track: gentle pulse, woodwind melody, warm | 84, E dorian, cane flute, curious |
| explore-river | exploration | a flowing, hopeful track: strings in long phrases over moving accompaniment | 76, G mixolydian, cello, journeying |
| explore-hist | exploration | a reverent, mysterious track: soft sustained choir and drone | 56, C minor, humming choir, sacred |
| explore-coast | exploration | the brightest, most open track: swaying pulse, brass-like calls | 90, F major, conch and flute, open |
| explore-highland | exploration | a lonely, stark track: few instruments, wide leaps | 66, B phrygian, folk fiddle, vast |
| explore-night | exploration | a dark, warm, uneasy track: low register, quiet throughout | 58, F sharp minor, bass reed flute, uneasy |
| explore-rain | exploration | a tender, melancholy track: two instruments in dialogue | 72, D dorian, thumb piano and flute, tender |
| battle-ambush | battle | a sudden, percussive battle track: drums first, short stabs | 140, D minor, log drums and conch, danger |
| battle-hunt | battle | a driving chase: string ostinato, relentless pulse | 128, E minor, low strings, predatory |
| battle-deep | battle | a heavy, slow-hitting battle track: low brass weight | 100, C sharp minor, giant drums, monstrous |
| battle-skirmish | battle | the quickest battle track: light, nimble, high woodwinds | 150, A minor, shrill reed flute, frantic |
| battle-war | battle | a martial, heroic battle track: massed voices and war drums | 120, G minor, wordless choir, defiant |
| battle-water | battle | a chaotic, churning battle track: swirling runs | 132, B minor, swirling strings, chaotic |
| battle-last | battle | the most desperate battle track: builds to a full climax | 136, F minor, full ensemble, last stand |
| sting-levelup | sting | the level-up flourish: short, bright, rising | the call on conch and flute, D major, 12 s |
| sting-death | sting | the death cue: short, falling, mournful | the call slowed on low flute, D minor, 12 s |
| sting-discovery | sting | the discovery cue: short, wondering | thumb piano and choir into the call, A major, 12 s |

Each region plays the exploration pieces of its atmosphere class; every region plays all seven battle pieces and the
stings. At night every region adds explore-night and explore-hist.

| Class (regions) | Day exploration |
|---|---|
| blackwater-swamp (banujha-basin, ultherus-swamp, tulmek-washes, blackwood) | mist, hist, rain |
| green-marsh (okuwun-rahei, nushara-bayou, lake-ulaish, barsaebica) | rain, canopy, mist |
| river-corridor (nha-enasa, valley-of-storms) | river, canopy |
| rainforest (murkwood, arnesian-jungle) | canopy, hist, river |
| highland (chixathe-mesa, aunike-ridge) | highland, river |
| coast-east, coast-south, coast-west (hatandros-bight, padomaic-ocean, benthic-yobesh, cape-percar, sea-of-mists, kotherra-mangroves, topal-bay) | coast, river, mist |
| island (althii-archipelago, aphon-isle, skeith-isle) | coast, highland |

## How it was made

Model: Google Lyria 3.5 through fal.ai (`google/lyria-3.5`), $0.10 a generation, 44.1 kHz stereo, up to about three
minutes; fal's terms give the requester the outputs for commercial use. Each prompt is the piece's own line plus
the shared palette, call and production words (`newworld/sources/music/pieces.json`). Request ids are kept in
`newworld/sources/music/manifest.json`, so a restart reads results by id and never pays twice. One take per piece,
kept after these checks: no clipping after normalising, no silence of 3 s or more, length, and no sung words (the
model's lyric output holds section markers only). Spend: $1.90 for 19 pieces.

## The slots, and how the owner swaps in his own file

Every role is a **slot**: one fixed file, `music/argonia/<slot>.wav`. The game's music records point at slots, never
at pieces, so swapping a file needs no record change.

To put your own music in a slot:

1. Name the file after the slot, for example `explore-mist.mp3`. Accepted: `.wav`, `.mp3`, `.flac`, `.m4a`.
2. Upload it to `s3://argonia-private-050977237313/nw/music/owner/`.
3. Run `python3 tools/newworld/music/soundtrack.py build` on the build machine, then `stack.py stage` on the play
   machine.

The tool converts every slot to 44.1 kHz 16-bit stereo WAV at the same loudness (-16 LUFS, peaks under -1.5 dB),
cuts stings to 12 s with a 3 s fade, and uses your file in place of ours. Our piece stays in the bucket (`ours/`) as
the alternative: delete your file and build again to go back. `soundtrack.py check` lists each slot and whether it
holds our piece or your file. The theme slot holds the owner's Overture now.

## In game (Bethesda's way, decision 0034)

Skyrim gives each region an exploration music type (a region's sound data names a MUSC), carries combat music on
its own type, and plays level-up, death and discovery cues from the default music types. Solstheim gives a separate
world one type on the worldspace. Ours: one music type per atmosphere class (day), one shared night type, one combat
type with the seven battle slots, and the three stings on the default level-up, death and discovery types for the
new world only. Vanilla Skyrim's music is not heard in the new world (decision 0012).

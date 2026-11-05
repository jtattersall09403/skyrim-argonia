<!-- imported unchanged from elder-souls-argonia docs/research/text-and-voice/skyrim-voice-barks.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Skyrim voice barks: what the archive holds, the path to Opus, feasibility

**Verdict: feasible, and it is an owner step.** The voice archive is not in
the vault: `../elder-scrolls-asset-pipeline/skyrim-source/Data/` holds
Skyrim.esm, Update.esm and the Animations, Interface, Meshes, Sounds and
Textures BSAs, and no `Skyrim - Voices_en0.bsa`. A search of the filesystem
for `*Voices*.bsa` came back empty. The plugin data is on hand, so we have
the line inventory below. The clips wait on the archive (§ Owner steps).

## What fits: the walk-by topics

Skyrim's ambient lines are DIAL records whose subtype (SNAM) is `HELO`
(a greeting as the player passes), `IDLE` (talk to no one) or `GBYE` (the
closing line). No DIAL in Skyrim.esm uses `GREE`: the click-to-talk
greeting is a branch topic, not a bark. Read from the INFO records and
their CTDA conditions by `tooling/audio-pipeline/audio_pipeline/voice_barks.py`
(output `plugin-counts.json`):

| | hello | idle | goodbye |
|---|---|---|---|
| INFO records, all | 5287 | 576 | 986 |
| generic (no `GetIsID`, Skyrim-only quests out), any voice | 623 | 34 | 43 |

Excluded as Skyrim-only: civil war, carriages, marriage, followers, Thalmor,
Dark Brotherhood, festival quests, plus every INFO conditioned on one
named speaker (`GetIsID`, function 72). City quests (DialogueMarkarth and
others) are almost all speaker-specific, so they drop out with them.

Lines per voice type in the generic pool. `explicit` counts lines
conditioned on that voice type (`GetIsVoiceType`, function 426, with
FormLists expanded). `candidates` adds the any-voice lines. Skyrim records
an any-voice line only for the voice types its quest's speakers use, so
`candidates` is an upper bound until the archive confirms which files
exist.

| voice type | explicit hello / goodbye | candidates hello / idle / goodbye | est. seconds | est. Opus 24 kbps |
|---|---|---|---|---|
| MaleArgonian | 13 / 0 | 604 / 21 / 35 | 3236 | 9.7 MB |
| FemaleArgonian | 13 / 0 | 604 / 21 / 35 | 3233 | 9.7 MB |
| MaleDarkElf | 6 / 2 | 597 / 21 / 37 | 3223 | 9.7 MB |
| FemaleDarkElf | 10 / 3 | 601 / 21 / 38 | 3272 | 9.8 MB |
| MaleNord | 16 / 3 | 607 / 21 / 38 | 3259 | 9.8 MB |
| FemaleNord | 71 / 2 | 662 / 21 / 37 | 3591 | 10.8 MB |
| MaleEvenToned (Imperial) | 24 / 2 | 615 / 21 / 37 | 3252 | 9.8 MB |
| FemaleEvenToned | 18 / 2 | 609 / 21 / 37 | 3251 | 9.8 MB |
| MaleKhajiit | 25 / 8 | 616 / 21 / 43 | 3317 | 10.0 MB |
| FemaleKhajiit | 30 / 8 | 621 / 21 / 43 | 3336 | 10.0 MB |
| MaleOrc | 15 / 1 | 606 / 21 / 36 | 3242 | 9.7 MB |
| FemaleOrc | 12 / 1 | 603 / 21 / 36 | 3235 | 9.7 MB |
| MaleGuard | 55 / 0 | 646 / 21 / 35 | 3544 | 10.6 MB |
| MaleCommoner | 12 / 2 | 603 / 21 / 37 | 3242 | 9.7 MB |

The sizes are **estimates**: duration = 0.4 s a line + words / 2.6, encoded
as Opus mono at 24 kbps (3 KB/s). The real figure is measured when the
archive lands. The shipped set is a curated subset, never the pool. Most
of the any-voice hello lines are guard lines (DialogueGuardsGeneral, 280
INFOs) full of Skyrim holds and jarls. After the Black Marsh cut
(design § Exclusions), expect about 80 to 150 voiced lines per voice type. Budget:
**1.5 MB per voice type**, streamed per place, about 12 MB for the
slice's eight voice types.

Skyrim's friendliness axis is `GetRelationshipRank` (function 403, -4 to
4). The Argonian relationship greetings come in pairs on it: MaleArgonian
"Ours is to smile at your passing, friend." (rank >= 1, INFO 000225EB),
FemaleArgonian "It annoys us. What does it want to take from us now?"
(rank <= -1, 000225E5). Time of day is a condition on the GameHour global
("Good morning.", 000142C2). The listener's race is `GetPCIsRace`
("What do you want, lizard?", 00087939, Nord voices).

## The pipeline

1. **Pick by record.** Choose the rows from `plugin-counts.json` and
   the INFO ids, never by filename.
2. **Locate the file.** The INFO decides the clip. Skyrim stores it at
   `sound/voice/skyrim.esm/<voicetype>/<quest>_<topic>_<INFO formid>_<response>.fuz`,
   where quest and topic are editor ids cut to fit (UESP, Skyrim Mod: Voice
   files). `pipeline/bsa.py` `BSAArchive.read` pulls it from the archive.
3. **Unwrap.** A `.fuz` is `FUZE`, version, lip size, the lip data, then
   the xWMA. Strip the header to get the `.xwm`; the lip data is dropped.
4. **Decode and encode.** `tooling/audio-pipeline/audio_pipeline/codec.py`
   already decodes xWMA through ffmpeg's `xwma` demuxer and encodes Opus in
   WebM (0094). Voice uses mono at 24 kbps, a one-shot, no loop padding.
5. **Ship.** One sound set per row, `voice.<voicetype-kebab>.<bark-id>`, in
   the audio manifest beside its provenance (source hash, INFO id), and the
   bark row's `clip.soundSet` names it.

## Licence position

These are vanilla assets from the owner's own copy. They are the same
category as the meshes, textures and `Skyrim - Sounds.bsa` clips we already
ship under [world/90](../../world/90-asset-strategy.md) and
[world/57](../../world/57-audio-soundscape.md) §107: sourced, credited and
hashed, never made. "Voice acting is out"
([quests/00](../../quests/00-overview.md)) rules out recording new voices.
Vanilla clips are sourced audio, and 2.5 already allows "sourced audio
only where it exists". Credit line for the root README § Credits when the
first clip lands: *Voice clips: The Elder Scrolls V: Skyrim Special Edition,
Bethesda Game Studios, `Skyrim - Voices_en0.bsa`, from the owner's licensed
copy.*

## Owner steps

Pick whichever is easier. Both need about 2 GB of free disk (the archive is
about 1.6 GB).

**A. Copy from an installed Steam game (simplest).** If Skyrim Special
Edition is installed on any machine, upload
`<Steam>/steamapps/common/Skyrim Special Edition/Data/Skyrim - Voices_en0.bsa`
to `../elder-scrolls-asset-pipeline/skyrim-source/Data/`, then reply
"voices in".

**B. DepotDownloader in the codespace.** It needs your Steam login and
Steam Guard code typed into the prompt by you. They never go into the repo
or a file an agent reads.

```bash
mkdir -p ~/dd && cd ~/dd
curl -L -o dd.zip https://github.com/SteamRE/DepotDownloader/releases/latest/download/DepotDownloader-linux-x64.zip
unzip -o dd.zip && chmod +x DepotDownloader
printf 'regex:^Data/Skyrim - Voices_en0\\.bsa$\n' > voices.txt
./DepotDownloader -app 489830 -filelist voices.txt -username <your-steam-login> -dir ~/dd/skyrim
# it prompts for the password, then the Steam Guard code from your phone
cp "$HOME/dd/skyrim/Data/Skyrim - Voices_en0.bsa" /workspaces/elder-scrolls-asset-pipeline/skyrim-source/Data/
```

App 489830 is Skyrim Special Edition. `-filelist` picks the file from
whichever depot carries it (the English voice archive is in the English
language depot), so you do not need a depot id. Reply "voices in" when
the copy lands.

## After the archive lands

Extract one voice type end to end as the proof (FemaleArgonian, the slice's
largest group with the male voice). Measure the real KB per clip against
the estimate above, write the credit line and the sourcing-register row,
then curate per voice type against the design's bands.

<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/clips.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9 loop survey: each cast style (lane 2.9c2)

Clips: rig pack `magic`, ids in `lanes/2.9/c2-ids.md`. Data measure:
`node apps/combat-sandbox/scripts/measure-cast-clips.mjs` (under job_guard).
Each row's measure must be green before the strip goes to a reader.

| # | Measure (command) | Bar | Last result | Elapsed |
|---|---|---|---|---|
| 1 | every style × hand × phase id in the manifest and its pack (`node packages/character-assets/verify.mjs`) | 39 ids, 0 unpacked | green: 21 packs verified, 39 CAST_* | 2 s |
| 2 | sourcing: register row `source.vanilla-cast-clips`, README credit, per-HKX sha256 | 32 hashes, credit present | green (8899e4bdb) | n/a |
| 3 | layer bones per clip (`measure-cast-clips.mjs`, tracks) | the casting side's arm, hand and fingers; spine, neck and head only in a dual cast | 24 per hand, 53 dual; castLayer.ts takes them (side-last names; one-hand casts leave the torso to the stance and re-anchor the clavicle, 599c10c19): green | 40 s |
| 4 | charge length = tier cast seconds (`visual:check -- cast`, `evaluateCast`) | charge phase within 1 frame of the tier | 0.834 s for novice 0.8, 1.234 s for healing 1.2 (one 30 Hz sample): green | 2 min group |
| 5 | release on the frame the projectile leaves | the release starts on the fired frame at its throw | aimed R/L and dual start at 0.167/0.15/0.167 s (manifest playbackStartTime), age 0 on the fire frame: green | 2 min group |
| 6 | no pop at the seams: the scene's worst local per-frame step of any player bone at a clip switch (`visual:check -- cast` telemetry `visualFrames`), against the incoming clip's own fastest step (`measure-cast-clips.mjs`, "release own step") | the stock 90° gate, and a seam step no more than the incoming clip's own step + 10° | side-change seams 15-28° (were 64-70°: the arm a side change picks up snapped from the stance; it now fades in, 599c10c19); releases 68° aimed R (clip's own 105°), 49° aimed L (own 44°, within +10), 59° dual (own 83°), 64° self L (own 64°); spine2 never in any scene's worst six: green | 2 min group |
| 7 | contact with the stance: sole planar drift over the scene | ≤ 2 cm, base animation IDLE | 0.13-0.19 cm in all five scenes, IDLE throughout: green | 2 min group |
| 8 | both hands | _R then _L clips in order, dual once | layer clip order matches in all five scenes: green | 2 min group |

## Reader checklist (one strip per style: aimed, stream, self, ward, dual)

1. The casting hand is the one the spell is in, and the other arm keeps the stance.
2. Charge: the hand gathers and comes up; there is no snap at the charge's end.
3. Hold: the charged hand stays readied (aimed, self) or keeps pouring or blocking (stream, ward).
4. Release: the throw (aimed), the press to the body (self), or the drop back to ready (stream, ward) reads clearly.
5. The spine and shoulders do not pop where the layer comes in or goes out.
6. The feet stay planted; no sliding or sinking.
7. Dual: both hands move together and mirror.

## Reader verdict (pod strips lanes/2.9/c2-strips/, full read lanes/2.9/c2-reader.md)

Build: the 599c10c19 layer (one-hand casts leave the torso to the stance,
clavicle re-anchor, side-change fade-in), profile camera on the one-hand scenes.

| Scene | Verdict | Defect |
|---|---|---|
| cast-aimed | partly | the throw reads (flash, arm forward), both hands; charge pose small and hard to read |
| cast-stream | partly | the cyan pour and the drop to ready read; the held pour is small |
| cast-self | partly | chest glow reads; the release lifts the arm out and up, not a press |
| cast-ward | partly | raised hand and ring read as a shield; pose small |
| cast-dual | not judged | the dual scene has no camera orbit, so the hands are hidden from behind |
| aimed charge (4.33 s clip over 0.8 s) | green | rushed but no jitter or snap; no clip change or loop point needed |

No spine pop and no foot slide in any scene.

## Re-shoot (2.9b4): side close-ups, reader `lanes/2.9/b4-reader.md`

All five styles were shot from the side with `--closeup` and
`VISUAL_STILLS` (the figure fills the frame), in one local capture job, strips
`lanes/2.9/b4-shots/styles/<scene>-strip.png`. The dual scene's orbit cue was
not added: a readied spell turns the body with the look stick, so an orbit
moves the body rather than the camera; the side close-up frames both hands
instead.

| scene | verdict | worst |
|---|---|---|
| aimed | green | the flash is small |
| stream | green | the pour is a faint wisp; charge and hold differ mainly in reach |
| self | partly | the release lifts the hand overhead, not in toward the body; hold and release look alike |
| ward | partly | the hold is a forward reach and the ward a thin streak, not a raised shield |
| dual | partly | the after frame has not returned to idle; the left hand marker hides behind the body |

The self, ward and dual items are queued in `lanes/2.9/b4-report.md` (for the polish backlog), not blockers:
each plays its vanilla clip readably.

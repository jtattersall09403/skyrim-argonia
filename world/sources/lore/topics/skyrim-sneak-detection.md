# Skyrim and Oblivion sneak and detection

**Scope.** How detection works in Skyrim (per observer or shared), what feeds it, what sneak
and witnessed kills do to bystanders, and where Oblivion differs. A game-systems source for
the stealth design (decision 0002: mechanics, not world state; no 4E 201 claim is made).

**Source.** UESP, fetched 2026-10-20 through the MediaWiki API (action=query, raw wikitext):
`Skyrim:Sneak`, `Skyrim:Stealth`, `Skyrim:Crime`, `Oblivion:Sneak`. The Creation Kit wiki
(`ck.uesp.net`, `creationkit.com`) was unreachable (Cloudflare challenge); `Detection` there is
only a redirect to a category. UESP does NOT document alarm propagation, so those parts are
tiered below.

**Era and confidence (decision 0002).** Skyrim (4E 201) and Oblivion (3E 433) engine
behaviour. Confidence: CANON_EXPLICIT for what UESP states (quoted); EXTRAPOLATED for
propagation, marked as engine knowledge not on UESP: re-verify before designing against it.

## 1. Per observer or shared — CANON_EXPLICIT + EXTRAPOLATED

- **Per observer.** UESP's formula names a "Noticer" and a "Sneaker" and computes distance per
  pair: "Detection Value = -15 + (Sound factor + Visual factor + Noticer skill factor) *
  (1 - distance/2500)^2 + (Noticer skill factor - Sneaker Skill factor)" (`Skyrim:Sneak`
  § Remaining Undetected). Each actor therefore has its own value. Followers are separate too:
  "Followers' chances of being detected are calculated separately from yours, based on their
  sneak skill and armor" (`Skyrim:Sneak` § Followers).
- **Memory per observer.** "An enemy that was previously alerted to your presence (even if your
  reticle indicated only a slightly open eye) will remember this, and is more likely to spot you
  again" (same page).
- **The eye aggregates.** The reticle states are "A flat horizontal line means you are
  completely hidden. A slightly open eye means an enemy thinks a target may be near. A
  half-open eye means the enemy is actively searching for you. An open eye means the enemy knows
  where you are or can see you." "DETECTED" flashes when an enemy "has spotted you and is
  moving to attack you"; "HIDDEN" flashes "once all enemies that had previously been alerted are
  no longer aware" (`Skyrim:Sneak` § Skill Usage). UESP does not say "highest across actors";
  the wording ("all enemies... no longer aware") implies the worst state wins. Tier: CANON_DERIVED.
- **Four states.** Hidden, caution ("may be near"), searching, detected/combat: the icon's four
  stages are the observer states.
- **No shared awareness on sight.** One NPC noticing you does not by itself make others
  detect you: others are tested each on their own cone, light and noise. The spread is by
  *behaviour*, not by sharing the number:
  - Witnessed assault: "Witnesses to assault will cry out to alert other NPCs, and call for
    guards" (`Skyrim:Crime` § Overview, Assault).
  - Combat pulls in allies: EXTRAPOLATED (engine knowledge, not on UESP): an actor entering
    combat with you triggers its faction mates and friends within hearing/range to join
    ("assistance" faction setting); they begin in search, then combat. Followers "are very likely
    to storm in and attack" once detected (`Skyrim:Sneak` § Followers).
  - Children "report it to the nearest adult" (`Skyrim:Crime` intro).
  - Dialogue barks ("I thought I heard something") mark the caution state; the alarm is the
    shout when combat starts.

## 2. Inputs — CANON_EXPLICIT (`Skyrim:Sneak`)

Designer's list; constants for the unmodded game:

| Input | Fact |
|---|---|
| Base | fSneakBaseValue = -15 |
| Distance | ((fSneakMaxDistance - distance)/fSneakMaxDistance)^fSneakDistanceAttenuationExponent; max 2500 units, exponent 2 |
| Sound | Sound factor = ((12 + armor weight/2) x (2 if running) x Muffle + 2 x ActionSound) x (1 if sneaker has LoS to noticer, else 0.3). fSneakEquippedWeightBase 12, Mult 0.5, RunningMult 2, ActionMult 2, SoundsMult 1, SoundLosMult 0.3. Zero when not moving |
| Muffle | Muffled Movement perk 0.5, Silence perk 0.0 (full); Muffle effect applies to the whole movement value |
| Actions | spells and shouts (unless Quiet Casting), any weapon swing larger than a dagger; drawing and sheathing are not heard |
| Visual | cone of vision ("if you fall within it, you are more likely to be detected"); can be blocked by items; light ("you are more visible in brighter light"); a spell glowing in the hand adds light, enchant aura does not; invisibility helps sight only, "does not influence enemies' ability to hear you" |
| Skill | "the Sneak skill ... does not reduce your sound factor or visual factor; it reduces the Noticer's skill factor"; Stealth perk makes you 20/25/30/35/40% harder to detect |
| History | previously alerted actors detect more easily |

UESP gives no numbers for the visual and light terms ("Visual factor"), nor the noticer's
skill factor; treat as CANON_DERIVED from the formula only.

## 3. Kills and witnesses — CANON_EXPLICIT (`Skyrim:Sneak`, `Skyrim:Crime`)

- Sneak attacks need an unaware target: x2 fists, bows, two-handed; x3 one-handed melee and
  daggers; Backstab x6; Deadly Aim (bow) x3; Assassin's Blade (dagger) x15. "The very acts
  involved in preparing for and attacking can result enemies detecting you, and ... you
  [then] receive no sneak attack bonus."
- Not a kill: "If a sneak attack does not kill an enemy, you will become more easily detectable,
  and your victim will usually start looking for you." A second sneak attack is possible if the
  eye is not yet fully open.
- Witnessed: "Enemies who witness the attack (by sight or by sound) are also likely to be
  alerted to your presence, even if the victim was killed." A silent unseen kill leaves others
  unalerted; bow kills let you relocate behind cover and "continue with another sneak attack".
- Crime: "Remaining undetected while committing a crime will allow you to escape punishment."
  "If you are detected, you can still wipe out a bounty if you kill all the witnesses to the
  crime before they are able to report you." "Most living creatures can witness crimes, including
  horses, farm animals, and hostile bandits." Murder (killing a non-hostile NPC) is 1000 bounty;
  assault is witnessed and cried out.
- Bodies: there is no "body found" alarm in UESP's text. What exists is a guard
  line ("Confronted by a guard when a dead body has been discovered nearby") and a 10-gold
  "Disturbing the Jarl's peace" for loitering near a dead body in a city (`Skyrim:Crime`).
  Bounty is per hold and reported to guards by the witness.

## 4. Oblivion differences — CANON_EXPLICIT (`Oblivion:Sneak`, `Skyrim:Sneak` Notes)

Oblivion has Sneak as one skill including pickpocketing (Skyrim splits it); sneak XP is 0.75 per
second moving unseen with someone nearby (Skyrim also levels while stationary). Sneak
multipliers are 4x (Novice) or 6x for one-handed and hand-to-hand, 2x or 3x for ranged;
two-handed weapons and spells get no bonus (Skyrim's x2 for two-handed). Mastery perks:
Journeyman ignores the boot-weight penalty, Expert ignores the running penalty, Master ignores
armor on an undetected attack. Boots matter ("barefoot makes the least noise"); Chameleon is a
partial invisibility (Invisibility 100%, ends on attack). Multiple melee sneak attacks work "for
as long as the enemy does not have you targeted"; a victim shot unseen "doesn't start looking for
you until hit"; an unwitnessed instant kill leaves you "exempt from suspicion", even next to a
guard. Detection is a single chance roll against you, not a per-observer value plus eye icon.

## 5. Crime, jail and pickpocketing numbers (mined 2026-10-21 for 2.10a)

**Source.** UESP MediaWiki API, fetched 2026-10-21: `Morrowind:Crime` (revid 3630850),
`Morrowind:Sneak` (revid 3543294), `Skyrim:Pickpocket` (revid 3581319). Era: Morrowind
(3E 427) and Skyrim (4E 201) mechanics, not world state (decision 0002). CANON_EXPLICIT.

| Crime (Morrowind) | Bounty |
|---|---|
| Theft | the item's value |
| Trespassing (unlocking an owned lock, untrapping too) | 5 gold |
| Pickpocketing | 25 gold |
| Assault | 40 gold |
| Murder | 1000 gold |

- Jail: "1 day for each 100 gold of your Bounty (with a minimum of 1 day)"; each day
  served moves one random skill (most -1; Security and Sneak +1).
- Guards confront on sight above 1000, attack at 5000. Resisting arrest: the guard attacks.
- Our use: world/76 §124 assesses crime in nushmeekos, not gold; no passage yet converts
  these gold figures or the jail rate into nushmeekos and custody hours, so
  `owing.json` carries them as blockers for the owner.

**Sneak use (Morrowind).** `Morrowind:Sneak` (revid 3543294) skill summary: "Successful Pick Pocket: +2.0", "Avoid Notice: +0.25". Our use (`stats/skillUse.ts` `pickpocket`, `avoidNotice`; world/76 §120.2 Sneak row): a lift nobody caught pays 2.0; Avoid Notice pays 0.25 a second while crouched inside an unengaged observer's view cone, range and line of sight, unseen (CANON_DERIVED: UESP gives no check interval, so one award a second).

**Pickpocket.** Morrowind gives no numeric formula on UESP ("determined by the value of
the item(s), your Sneak level, detection state ... and your target's Sneak level";
effectively capped at 56%). Skyrim (`Skyrim:Pickpocket`, GMSTs): chance = 15 + Sneak -
target Sneak/4 - gold/10 - 4 x item weight (+ perks), MaxChance 90, MinChance 0;
Detected -25. Our rows (`pickpocket.json`): base 15 + Sneak sampled at Sneak 0, 20, 40,
60, 75 and capped 90; target spot 0.25 a point; 4 a kilogram at each weight class's top
edge (1, 5, 10 kg); 1 per 10 gold at each value band's lower edge (CANON_DERIVED).

## Consumers

Stealth and detection design for the studio slice. Not yet wired; the design record should
cite this file and say which parts it copies (per-observer value, four states, worst-state
icon) and which it invents.

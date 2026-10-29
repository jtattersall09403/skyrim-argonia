<!-- imported unchanged from elder-souls-argonia docs/decisions/0039-source-game-crosscheck-triage.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0039 — Source-game systems: what Argonia adopts and cuts from Morrowind and Skyrim

**Status** accepted · **Evidence**
[source-game systems cross-check](../research/combat-and-systems/source-game-systems-crosscheck.md)
(UESP-mined audit of Morrowind's and Skyrim's systems)

## Ownership and theft (the Morrowind visibility model)

The `owner` slot is optional; unowned objects are the norm outside
settlements and taking them is never theft. **A theft bounty exists only if
the act is witnessed.** **No stolen flag on possessed items, ever**: once you
have it, nobody can tell where it came from; no lawful-merchant refusal, no
laundering through a fence. Confiscation applies only to goods a witness
record ties to a crime. A "fence" is a no-questions buyer and contraband
outlet, flavour only.

## Rulings

- **Traversal magic: every Morrowind family stays**: levitation, water
  walking, Mark and Recall, telekinesis, Open, Detect, and Intervention as
  shrine networks. Flavour is race-neutral: nothing load-bearing assumes an
  Argonian player. Dungeon and underwater design account for levitation with
  Morrowind's own tools (cost, duration, slow speed, magicka, Dispel).
- **No survival layer.** Danger comes from encounter frequency and
  difficulty, disease and venom, never atmospheric attrition: no hunger,
  heat or wet, no survival item field. Counterplay is the cure and resist
  alchemy and effect economy. Guide services stay as travel flavour.
- **Rest and inns**: wait and rest are separate verbs; no camping inside
  settlements (wait only; resting in town needs an owned or rented bed);
  beds have quality tiers (module 76 §126).
- **No chronic corprus-style condition.** Hist-site communion powers are an
  open design slot, taken only if simple, reusing the powers semantics and
  effect stack, and race-neutral in completability (an Argonian advantage is
  fine; a race-gated progression path is not).
- **Customs and standing**: per-settlement custom rules cost standing, not
  bounty; a capped outsider-standing track; a favours ladder with
  relationship ranks.
- **No bleedout.** Story-essential NPCs get no extra protection; the doom
  warning and reload are the whole model
  ([0030](0030-quest-plan-qa-review.md)). Hand-to-hand knockout follows
  Morrowind's fatigue-drain shape.
- **Reprisals**: Owing enforcers and hired thugs find you, courier-delivered
  and escalating with debt and notoriety, including traceable
  interrupt-on-rest attacks. **The Owing ledger is per city or region**; where
  an uncleared bounty exists, guards stop you and the resolution verbs
  apply.
- **Fishing** only if its animations are a cheap sourcing job.
- **Pilgrimage circuits** are quest content, not a system (a nudge sits in
  the Nisswo line, [quests 40](../quests/40-factions.md) §35).

## Adopted

Ownership on every placed ref, crafting stations with `STATION` sockets,
Fight / Flee / Alarm with a 72-hour Owing amnesty, deed counters
(`deedCountAtLeast`), player-state overlays, a faction reaction matrix, a
creature statblock class (NPC souls are untrappable), encounter templates,
a courier channel, shrine blessings, staged disease, a diegetic character
creation template, dungeon anchor sockets, contraband, cursed-offering,
attire-signal and donation flags, creature merchants, urban water taxis.

## Cut

Player vampirism and lycanthropy (a vampire stays as content), player house
construction (a steward's pay-for-service pattern stays), shouts, swappable
birthstones, an apex roaming threat, marriage and adoption, a generic
killmove layer, projectile interception, requestable tavern musicians and
tavern brawls unless a quest wants one.

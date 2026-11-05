<!-- imported unchanged from elder-souls-argonia docs/decisions/0157-the-marsh-does-what-the-lore-says.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0157 — The marsh does what the lore says

Status: accepted (owner, 2026-10-23). From the audit of the 170
loading-screen facts against the game
([research/lore-facts-audit/](../research/lore-facts-audit/README.md)).

## The problem

The loading screen tells the player that the wamasu spits lightning, that
Hist sap is made into rubber for insulated wamasu prods, that pahnjees
mask a living scent from bog blights, that the Great Burn ran through
peat, that xanmeers are trapped mazes. The game did none of it: the
wamasu only bit, sap rubber did not exist, scent was the creatures' and
never the player's, traps fired only on `open`. A fact the player reads
and then never meets is a promise broken in the first loading screen.

## The rulings

1. **Creatures do what the lore says.** A creature's ranged or spell
   attack is a `creatureCasters` row in `hostile-loadouts.json` (the
   wisp's Absorb Health is the precedent); the wamasu spits shock.
2. **One hazard-volume record** serves every "stand here and it lands on
   you" fact: shape, effect, condition (in water, on ground, on touch),
   lifetime, source (a creature, a place, a hit). Burning peat, fleshfly
   swarms, voriplasm pools and dragon's tongue's touch are rows of it.
3. **Peat is the ground already called peat.** The terrain's land cover
   has a peat class (`material.peat`: footsteps, detection and arrow
   response already read it); no patch is painted or recorded apart.
   Fire spells and fire arrows landing on peat ground light a standing
   fire there, a hazard volume that damages whoever moves into it,
   enemies included. No spread ([0042](0042-buildout-steers-and-engineering-standards.md) §2 holds); the burn's
   size and lifetime are derived, never invented.
4. **Shock into water.** Water is ordinary water. A shock spell or shock
   arrow that strikes it, or a shock attack made by a creature standing
   in it (the wamasu's), shocks every actor in that water within the
   attack's area, the player included.
5. **Effect arrows.** Fire arrows are crafted (arrows, a wrap and a
   lore-grounded incendiary); other elements by enchanting a stack,
   Morrowind's ammo rule (ammo joins the enchantable kinds, cast on
   strike). The element rides the stack instance, never a row per
   material and element.
6. **Marsh materials and harvests.** Hist-sap rubber makes insulated
   gloves, boots and the telescoping wamasu prod (`resistShock`);
   Stormhold crystals work as soul gems (filled ones enchant, hollow ones
   hold corruption); every creature-harvest row is filled (a wide load),
   moon-adder venom to daril among them.
7. **The player is an outsider, and the Hist can be earned.** An
   Argonian character is lukiul (hatched abroad), who canonically cannot
   hear the Hist. Hearing has three steps, saved, granted only by a quest
   action ([0149](0149-the-studio-plays-the-game-no-modes-flags-or-switches-for-game-actions.md)):
   **touched** (granted in MQ01 when the camp's Hist loses its clutch
   with the player beside it; the sap-dreams from MQ03 are its voice;
   resting beneath a Hist's boughs soothes, a rest bonus), **heard** (the canon Trials of the
   Burnished Scales at Hissmir; a hand on bark tells the player the
   hidden places nearby and the danger of the land around), and
   **sap-speaker** (late main quest; communion and the spore-call, 4.5).
   Sap is a risky drink: on an outsider it is bloodlust (strength up,
   personality down, nobody will talk to you), and too much is
   sap-poisoning by stages (gold tongue, bark scale). Tree-minders'
   blessings stay as 2.6 built them.
8. **The slice stand-in retires itself.** In the slice a Root Steward of
   Hissmir, who canonically cannot refuse a comer, gives the Trial at
   Greenspring. Its quest record names the canon Trials quest it stands
   in for; the quest validator reds once Hissmir is built while the
   stand-in still grants. The switch is a gate, never a memory.
9. **Calendar and weather are quest data.** A calendar condition (month,
   day, season) and a set-weather action. Festivals come later as data
   only, Daggerfall's holidays: prices, stock, services, a rumour, an
   optional world rule; no crowds or staged rites until a quest needs
   one.
10. **Grave-stakes have a home record** and read like a document.
11. **The player has a scent.** A scent multiplier on the effect stack;
    pahnjees, eel slime and a mud wallow lower it; heart-mud slows the
    feet.
12. **Traps and puzzles the mods placed work.** The slice's Teeth of
    Sithis cells carry their mod's pressure plates, trigger boxes,
    swinging blades, spike beds, poison gas, a flamethrower, levers,
    pull chains and a lever-and-pillar puzzle; they go live with their
    triggers (step, tripwire, lever) and physical damage. What a trap or
    puzzle is wired to is read from the plugin data (linked references,
    activate parents, script property values); the logic is rebuilt as
    data, never taken from Papyrus code. Other xanmeers' puzzles follow
    in 4.5 by the same reading.
13. **Argonian speech never names the Daedra** (a lint on the Jel
    registers).
14. **The loading screen shows the region the player will be in** when
    it completes: its deck holds that region's facts plus every
    province-wide fact (history and the Hist in general), never another
    region's; the discovery banner names the region.

## Out

Floods and any water-level change (the water is hard-won; a `P3 final`
optional row at most), food spoilage, new playable races, sport and
instrument minigames (new animation), spreading fire.

## Where each lands

| Ruling | Phase |
|---|---|
| 1–6, 11, 12, 13 | [2.9c](../phases/2-slice/2.9c-marsh-specials.md), after 2.12 and before 2.15 ([0158](0158-boats-and-sound-before-the-save-loop.md)) |
| 7 (records, sap, rest), 8, 9, 10, 14 banner | [2.11](../phases/2-slice/2.11-quests-journal-map.md) |
| 14 loading screen | lane `loading-region`, 2026-10-23 |
| the Hist's voices and whispers | [2.14](../phases/2-slice/2.14-sound-and-music.md) |
| Argonian characters lukiul; the touched step in MQ01 | [3.3](../phases/3-shell/3.3-character-creation.md), [3.4](../phases/3-shell/3.4-the-opening.md) |
| pottery as crafting (kiln, clay, washtongue; the kiln makes alchemy apparatus), xanmeer puzzle rooms, festivals, rootworm travel, Dead-Water skull traps, the canon Trials at Hissmir | [4.5](../phases/4-buildout/4.5-systems-depth.md) and the packet that builds Hissmir |

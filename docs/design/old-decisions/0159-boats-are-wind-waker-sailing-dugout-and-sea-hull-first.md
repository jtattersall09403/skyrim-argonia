<!-- imported unchanged from elder-souls-argonia docs/decisions/0159-boats-are-wind-waker-sailing-dugout-and-sea-hull-first.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0159 — Boats sail like The Wind Waker; the dugout and the sea hull first

Status: accepted (owner, 2026-10-23). Shapes 2.15 inside the order set by
[0158](0158-boats-and-sound-before-the-save-loop.md); answers the owner
calls the boats research left open
([player-boats-as-horses](../research/combat-and-systems/player-boats-as-horses.md)
Recommendations 4, 5 and 8).

## The problem

The 2.15 brief built every boat class the slice water allows, each with
its own crew pose, before the owner had said how a boat should feel. The
research found no rowing, paddling or helm clip anywhere, no reed-canoe
hull, and priced boat theft as a gold bounty that the Owing model
([0151](0151-stealth-crime-and-locks-ship-whole-pickpocket-is-the-one-gamble.md))
does not have.

## The rulings

1. **The slice builds two classes: the dugout and the sea hull.** They
   are the furthest apart (a seated paddled canoe on creeks; a standing
   helm under sail on the coast), so the system they prove covers the
   rest. The skiff and the river boat are typed and priced now and built
   in 4.5. The reed canoe is dropped: no hull for it is sourced. A class
   is cut for want of a model only after a sourcing crawl (vault, mods by
   the Nexus API, vanilla) proves the absence from data.
2. **One sailing system; a class is a config.** Speed, turning, wind
   response, draught, reach rules and crew pose are catalogue values on
   `BoatClass`; 4.5's classes add rows, never code.
3. **Sailing is The Wind Waker's.** The boat goes where it is steered at
   a cruise speed; the wind fills the sail and adds speed with it astern.
   The wind is the weather's wind
   ([0032](0032-phase8c-weather-implementation-shape.md): weather owns the
   wind), the one the vegetation, waves, smoke and ambience already read.
   The research studies how The Wind Waker does it and any open three.js
   sailing work worth taking (licence, source and credit recorded like an
   asset).
4. **The player can turn the wind.** A power, an item or a cheap
   Alteration spell, whichever the lore grounds best (the research
   decides, sources cited); one quick action and a direction pick on a
   small screen of its own, never a slow ritual, because it is used
   often. It turns the world's wind through the weather, so everything
   that reads the wind swings with it. While sailing, an unobtrusive HUD
   mark shows the wind's direction.
5. **Crew animation is tried, then falls back.** One focused loop
   authors paddle and helm animation, judged by `reader` agents; if the
   readers find it very bad after two iterations, it stops and the boat
   uses a sourced pose: seated on the bench in the dugout, standing at the
   helm on the sea hull, the paddle or oars still, the hull steered as an
   `EcctrlVehicle`. This is the owner's exception to "we never make
   animations", for boats only.
6. **A lost boat comes back to the last mooring you tied it at.** A tied
   boat stays tied for any absence. One left adrift or beached is moved
   after a rest to the last mooring the player tied it at (if never tied,
   where it was bought, found or taken), or fetched by a boat-keeper for
   10 percent of its price, minimum 5 gold. Every boat the player owns is
   marked on the map. There is no "home mooring" the player sets.
7. **Taking a boat is theft on the Owing ledger** (0151), witnessed or
   not by 2.10's rules; never a gold bounty, never a stolen flag
   ([0039](0039-source-game-crosscheck-triage.md)).
8. **No owner stop for the mooring map.** The agent checks the mooring
   network in a fast focused loop (dry-season depth for each accepted
   class, connected water, a real jetty or bank, a lore reason, a
   `reader` on a map still); the owner sees it in the deployed build.

## Consequences

- No boathouse is placed in the slice; the socket kind stays for the
  first packet that needs one.
- 4.5 gains a boats row: the skiff and the river boat, cargo, passengers,
  repair and boarding against crewed boats.
- The sea hull needs a real run of coast between slice places; the brief
  makes that a measured check before the hull is built.

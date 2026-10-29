# Lighter Flotilla: design record

Place `place.mercantile-coast.lighter-flotilla`, type houseboat-flotilla.
This record covers the walk-12 fix rounds; the layout's `note` ops say why
each piece stands where it does.

## Site

The lighter crews of the Mercantile Coast live aboard their hulls on a
timber pier on piles. The pier runs from the bank out to the Alten Meerhleel
trade ship, which lies here between runs. A short landing stage crosses the
reed shallows from the Lilmoth track to the bank. The lighter takes
passengers and cargo out to the anchorage; four plank ferries, moored for
good, serve as market stalls.

## Intent

- Purpose, in a crew member's words: "We live where the work is: the ship,
  the lighter and the road all meet at our pier."
- Mood: busy (cargo on the decks, stalls on the rafts), worn (posts, ropes,
  patched hulls), welcoming after dark (lanterns where the crews step off).
- What stays with a visitor: from afar, the trade ship's masts over the reeds; at the
  threshold, the stage on the bank and the long pier; at the heart, the hulls
  roped along both sides of the pier, with the ship's sign over the water.
- Night: three lanterns light the ship's deck, fore to aft. More lanterns
  stand on the pier where the crews step off. Each one is lit from 17:30 to
  06:30.

## Walk-through

1. Far: the masts over the reeds from the Lilmoth track.
2. Approach: the landing stage over the shallows; it ends on the bank.
3. Threshold: the pier foot, a few steps east on firm ground.
4. Heart: the pier, with the hulls roped on both sides and the market rafts.
5. Goal: the trade ship's sign, the stairs over her rail, her lit deck.
6. Exit: the lighter at the outer end, roped to its post for the anchorage run.

## Brief (fix-round rows)

| Thing | Purpose | Kit piece | Rule or lore |
|---|---|---|---|
| Ship's sign | names the ship from the pier | kotm blackwood sign | `mount --hang --bracket` on the aftcastle's planked wall, `measure` hang pass |
| Deck lanterns | light to work by on the ship after dark | candlelanternwithcandle01 | gate `lights.deck` (6 m) |
| Pier lanterns | light where the crews step off their bows | candlelanternwithcandle01 | a floating hull carries no deck lantern yet |
| Mooring posts and ropes | each hull is held to the pier | tamu_woodpole01, dockropestr01 | `wb.py rope`; a floating hull is held by its tether |
| Landing stage | the track meets the bank | dockstrent02 run | ends on the bank; no mined dock corner joins it to the pier |

## Known answers

- The dock corner (dockcorsol01) has one mined leg, +x. Its +y leg has a
  single plugin placement, below the two-placement bar. With the mined leg
  on the pier, the corner sits on the pier foot (3832.8, 6358) and its other
  leg runs north into the bank, where the next deck would lie 0.7 m under
  the ground. With the mined leg on the stage, the stage runs south into
  water 0.3 to 0.6 m deep and ends 17 m east of the track. So the stage
  ends on the bank and the walk crosses firm ground to the pier foot.
- The lighter floats on its tether, so it has no rigid plank. The crew step
  down from the pier onto its low deck, which is within 1 m of the pier.

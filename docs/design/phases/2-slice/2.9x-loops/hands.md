<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/hands.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the hands (2.9x lane j)

A hand holds one of a weapon, a shield, a torch or a spell, equipped
through the one hand API (`packages/game-core/src/inventory/hands.ts`
`equipHand`). The quick belt holds hand-equippable things and hand swaps; a
press rotates the thing into a hand, displacing what was there
(`inventory/belt.ts` `useBeltSlot`, `swapHands`). Casting is the spell
hand's use button (`combat/castCycle.ts`); nothing casts from the belt.

The number is `packages/scene/src/interact/hands-session.test.ts`, driven
through the item session (bag and belt) and the magic link (the pause
deck's magic window) as the hosts wire them. One headless run, 9.2 s wall
(tests 10 ms).

| transition | how it is driven | assertion | state |
|---|---|---|---|
| inventory equip (weapon) | `items.equip(sword, "mainHand")` | right hand holds the sword | green |
| magic-window equip (spell) → cast | pause deck `onHand("off", fireball)`, then hold the left cast button | left hand holds the spell; it fires from the left hand; the sword hand fires nothing | green |
| rotate belt → shield | shield on belt slot 1, press | left hand holds the shield, the spell displaced; the sword stays | green |
| rotate belt → spell → cast | spell on belt slot 2, press, cast | right hand holds the spell, the sword displaced; it fires | green |
| rotate hand swap → weapon and spell | `rememberHands`, shield pressed in, `swapHands` | right sword, left spell again | green |
| save round trip | inventory snapshot out and back | hands and belt equal | green |
| sheathe and draw with a spell in hand | drawn false, then true | the spell stays in the hand and casts after the draw | green |

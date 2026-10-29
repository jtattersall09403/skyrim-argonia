# The Wamasu Shrine (Shrine of Haynekhtnamet), `place.dunmer-north.the-wamasu-shrine`

The Wamasu Shrine is a type 6 shrine of family `rite` and kind `beast-offering-shrine`. The shrine has no entrance. The record size is null. The size is set from the type recipe, which gives a footprint radius of 20 m, a count band of 2-5 and a complexity of trivial. This design is part A of three, from walk 11, wave 3.

## Site

- **Record** (`world/sources/catalogue/places-dunmer-north.json`, the record's block): why: a wamasu of
  Shadowfen received offerings to stop the seasonal flooding. Four villages send offerings each wet season
  in rotation. The offerings are increasingly practical (tools, salt) and the older villagers find this
  embarrassing. The site is "on the bank above the pond which the creature is held to inhabit, at the highest point
  reached by the flood". Vibe: one dressed stone shelf, otherwise bare; green-black water, corroded iron,
  salt white, scorch marks; "the shelf gets struck; the offerings nearest the water are the most burnt";
  ozone before the water is seen; a crackle that is not a fire. Occupants: none; D3 in the pond below.
  Sockets: `scene.the-wamasu-shrine.the-bank`, `evidence.the-wamasu-shrine.the-scorched-shelf`. Quest LD65
  Offerings Against the Flood (`world/sources/quests/local-dunmer-north.json`).
- **Ground** (`world/sources/sites/dossiers/the-wamasu-shrine.md`): the record's point (4735, 825) is a
  42 deg mountain face at 190 m, 4 % buildable, with no water within 20 m. The pond that the record names lies 115 m
  south. It is a black pond (level 157.89 m, `wb ground`) at x 4690-4725, z 905-940 and a second pool and its
  headwater channel lie east of it. A track runs along the strip of bank between them (bank 158.4-158.8 m,
  0.5-0.9 m over the water). The slope is under 6 deg on the strip and over 30 deg everywhere off it.
- **Siting**: the shrine stands on that bank strip at about (4727, 938), on the track. No other way reaches the bank.
  The four villages bring their offerings along the track. This moves the place 115 m from its record point.
  The move is an owner-level call, filed as a REQUEST row (positionM to the bank) and named in the packet. The build
  continues on it because the record's own siteAdvantages put the shelf on the pond bank.
- **Lore**: UESP "Lore:Wamasu" and "Lore:Haynekhtnamet". The Argonians of Shadowfen worshipped the wamasu
  Haynekhtnamet and left it offerings to keep back the seasonal floods
  (`world/sources/lore/topics/ecology-encounters-loot.md`:202). Wamasu breathe lightning and electrify whole
  ponds (`argonia-4e201-state.md`:584, `fauna-hazards.md`:126), which accounts for the scorch and the ozone.
- **Nearby**: the single published shrine nearby is the Tag House (`place.imperial-penal-south.rose-bone-waystation`:
  HTBM half pavilion, keeper hut, bone chimes, candle line, Argonian skulls). This place repeats none of it.

## Intent

Visitors come to the shrine nervously. They leave something useful and go quickly. The place reads as a working bargain with a dangerous creature in the water. It does not read as a temple. One old dressed stone stands on the bank. The stone is loaded with iron tools, salt and cord. Everything nearest the water is blackened. The shrine has no residents. The mountain face behind blocks the view. The black pond lies in front. The creature responds to the offerings. Ash scorch marks the water end of the shelf. Five tally stones mark the years that the shelf has held the flood.

Villagers tended the shrine with offerings this year and last, according to the condition line of the record. The shrine is not abandoned.

## Walk-through

1. **Approach** over the bank from the north-east, off any road. The pond opens on the right as black
   water. The pale dressed stone on the bank is the first made thing in sight.
2. **Arrival.** The stone shelf stands with its back to the water. Salt, iron ingots and a net lie
   on it. A shovel and a pitchfork stand upright beside it. A painted urn stands at its dry end. Two floor
   candles, one at each end, give the only light at night.
3. **The tally**: five small clusters of pebbles lie in a loose row along the bank edge west of the shelf,
   one cluster for each year that the flood held.
4. **The edge.** Shed wamasu scales and a gnawed bone lie at the waterline and the ash scorch marks the
   water end of the shelf.
5. **Leave** by the way of the approach. Nothing else stands on the bank.

## Palette

The palette is stone, iron, salt and bone. Nothing is woven and nothing is thatched. The whole palette of the Tag House is wicker, thatch and bone chimes. The shelf is the Ayleid dressed block `arblock01` from ruin-monumental-v1. It is the single dressed stone on a bare mountain bank. It is older than the villages. The offerings come from the works kit and are salt, iron ingots and a net for cord. Tools stand planted upright in the bank beside the shelf. The tally is a row of five pebble clusters. Each cluster holds one to three Shores of Skyrim shore rocks, which are `shorerock06`, `01` and `07`, each 0.07-0.14 m. The 1.4 m `rocks02` pieces serve as a path of boulders. The `cookingstone01` piece serves as stone basins. The leavings of the wamasu are the HTBM shed scales and a gnawed bone at the waterline. The `ashpile01` scorch lies beside the shelf.

## Brief

| Thing | Purpose | Kit piece | Rule or lore pointer |
|---|---|---|---|
| Offering shelf | promise thing-shrine, evidence socket; walk stage 2 | `ayleidkit:.../exterior/arblock01` (2.73 x 2.73 x 0.91 m, fit dug-in) | record vibe.materials, siteAdvantages |
| Offerings on the shelf (2 salt, ingots, pot, ore bucket, net, candle) | vibe.silhouette, why.pressures (practical offerings); stage 2 | works-v1 `saltpile`, `ingotsiron01`, `castironpotmedium01`, `orebucket_iron`, `fishnet01`; settlement-mud `argoniancandle01` | mounted unmined on the shelf top (plan under 0.6 m) |
| Planted tools (shovel, pitchfork) | why.pressures: tools in place of symbols; stage 2 | works-v1 `shovel01`, `pitchfork01` | ground props |
| Offering sack and bucket | container socket (lore fragment, materials) | `miscsacklarge`, `bucket01` | record contents.loot |
| Tally stones (5) | "a tally of flood years"; stage 3 | `shores:shoresofskyrim/shorerock06`, `01`, `07` (ground, 1-3 per mark; stacking needs a policy row) | propSeatRule |
| Struck tree | cut: the stick tree takes a direct fit and the scan found no legal cell on the bank (904 measured, 0 legal; deltaRule/slopeRule). The scorch on the shelf carries the strike | — | scan round-1 |
| Leavings (shed scales, storm scales, one bone, ash scorch) | wamasu leavings at the waterline; stage 4 | HTBM `clutter/wamasuscales`, `wamasustormscales` (kitted into ruin-monumental-v1 this slice); `vanilla:clutter/bones/bloodybone`, `vanilla:effects/ashpile01` | sourcing register row 2026-10-04 |
| Wamasu (slot n1) | occupant n1, danger 3; it hauls out on the bank edge | npc socket + two `stand` idle sockets on the dry bank edge | record occupants |
| No path | off the network: no registered route reaches the bank; the approach is `fromDirection` north-east | approach only | walkRule off_network |
| Light | two floor candles, one at each end of the shelf (2.2 m stand, too tall to mount; light row in settlement-mud-v1) | `argoniancandle01` | lights.density, 1 kind |

The magnitude bar is null. The count band is 2-5, with one structure, the shelf. The shrine has no building, no door and no interior. The creative calls that differ from the register are as follows. Tools are planted upright as offerings. A row of set stones is the tally. The burnt bare tree is the strike mark.

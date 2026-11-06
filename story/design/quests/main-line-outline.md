# The Eye and the Root: the adapted outline (Acts I to V)

This is the source for the main quest's Acts II to V. Act I's four records (MQ01, MQ03, MQ04, MQ05, in
`story/data/db/`) are the source for Act I; this file reads only what they hand on. The authored design,
[30-main-quest.md](30-main-quest.md), is history: its cast, thesis and ending families stand where this file keeps
them, and its branch-state model, reward tracks and per-quest table are replaced here.

Rules this outline is written to: the planner's rulings in [review/act1.md](review/act1.md), "The whole main line,
round 1" (B1 to B5, N1 to N5), and the owner's ruling of 2026-11-06 ([owner-rulings](../../../docs/owner-rulings.md)):
keep the treasure hunt, the spies and the spirit; more Black Marsh, more exciting, less bureaucratic; law and
custom only as background; choices do not multiply; every quest uses the player's skills; nothing harder to script
than an average Skyrim quest; no procedural climax.

Line-wide rules:
- **One carried choice.** Each quest below plays the same whatever came before. A quest may hold one local choice;
  its result is colour (a line, a body, a letter) and never changes a later quest's stages. Only the finale's CUT,
  CLAIM or MEND carries forward, into the closing scene and the world's end states.
- **Act I's flags** (`flag.mq04.adopted`, `flag.mq05.reed-exposed`) are read for one line of colour at most, or not
  at all.
- **Deaths** use the standard fail-forward (30-main-quest §23): every principal is killable; a fallback sender or
  document carries the stage. The Eye cannot be lost.
- **Rewards are fixed per quest** and nothing is levelled against the player (decision 0035). Where a reward has no
  item row yet it is marked "row needed".
- **Places** are BM&V's own (census ids, `docs/research/bmv/census.md`) or a recorded need. No main quest stands in
  a faction seat or a slice quest's place (Pusbottom is TG02's, the Blackrose Jail cell 01BlackRoseJail is BC02's,
  Soulrest's dock is TG01's and BC03's, Helstrom's landing is LQ25's, the basin at Helstrom's gate is LQ30's,
  Longmont and Gallows Rock are the Shadowscales'). Helstrom is the seat only: the player returns there between
  acts; no quest after MQ05 is played in it.

## Act I: the camp burns (records; read, not changed)

**Hook:** an Owing gang's camp burns, a woman takes the courier's satchel and decides the player is not worth
killing, and that night a clutch dies in the egg.

MQ01 No Name on the Work Roll, MQ03 A Dead Prisoner's Use, MQ04 The Tree That Turned Its Face, MQ05 Helstrom Behind
the Thorns (being reworked whole). What Act I hands on, on every ending: the player is the Reed's deniable hand,
has seen Cuts-the-Old-Knot, dreams the ring of trees and the unbuilt door, knows the cell cut a Hist's root to take
its sap, and stands in Helstrom having met Kaska-Meen and Ei-Tuja (one may be dead) and walked past the empty, swept
Scalded Throne. The handler is Nesh-Deeka; if she died, Never-Writes-Twice, already in the Reed's house since MQ03,
sends the Act II hook in her place (the sender line, N5).

## Act II: the hunt (four quests)

**Hook:** someone is selling the Eye of Argonia, the king's jewel nobody has seen, and the cell that burned the
camp means to buy it.

- **MQ07 The First False Eye.** At Murkwood's Bandit Dock (`bmv.murkwoodext`, BlackMarsh2, with Murkwood Verge's
  house `01CabinInt2` as the sale room) smugglers sell a jewel they call the Eye to rival buyers, one of them a
  courteous collector who withdraws at the last moment and leaves the player a polite note (Opens-the-Last-Door,
  unnamed). The stone is glass; its old setting is real and carries a cut route-cipher. Skills: sneak or
  pickpocket to lift the setting from the strongroom chest (lockpicking), or speech to buy a look; then a fight or
  a swim out from the dock when the smugglers find it gone. Choice: take the setting yourself, or leave it on the
  cult's buyer and tail him by boat (sneak); both end at the cell's safehouse, with the setting in hand. Reward:
  the setting (quest item) and the Collector's note.
- **MQ08 The Unbound Root.** The tail or the buyer's mark leads to the cell's safehouse in Swampy Cave
  (`01Goblincave`, BlackMarshNorth site). Inside: the cell's people, its sap jars, and the first plain sight of what
  the cult wants: a Mnemic Egg (story/lore/topics/hist-and-sap.md), which only a dead Hist leaves, and the Eye, to
  open a door they have dreamed of. Skills: sneak or blade through the cell (non-lethal route by the back water,
  swimming); alchemy to read the jars. No choice. Reward: the cell's chest (fixed loot, row needed) and the first
  name of the cult, the Unbound Root.
- **MQ09 The Map Beneath the Old Rose.** The setting's cipher points to an explorer who died in the Rose with an Eye
  route-tablet. Not the Rose BC02 uses: BM&V's unused old Black Rose in the far west of BlackMarsh (`gg`,
  `therose`, `mountainpass`; cell BlackRoseold; no actors, no doors), a ruin the marsh took back. The tablet lies
  in the flooded cells below. Need: one interior for the cells (a reused BM&V cave interior, candidate `01Cavern`
  at `bmv.castle`, with a new door pair at the old Rose). Skills: climbing (FreeClimb) over the fallen walls,
  swimming and breath in the flooded tier, a fight with what nests there (the marsh's own creatures; no draugr).
  No choice. Reward: the tablet and a fixed find in the explorer's cell (row needed).
- **MQ10 The Auction of Drowned Things.** The last of the three leads, and the act's end (N1). Salvage divers at
  Tear's ship landing (BlackMarshNorth 25,19, BM&V's Tear markers; attached to no settlement) are working a wreck
  whose cargo holds a lens-frame matching the setting; Ahnjazzi, a Khajiit underwriter, has bought the salvage
  rights and the Collector is asking the same questions. Need: a sunken hull placed in the water by the landing
  (statics only) with one air pocket. Skills: swimming (dive first, past the slaughterfish), or speech or
  pickpocket to take it off the divers' raft. Last stage: setting, tablet and lens-frame fitted together at
  night show one place, a Xanmeer drowned off the coast, and the same night word comes that a second Hist has
  been cut, at Murkwood Verge, where the player was in MQ07 (one fixed place, B1; need: a tribal Hist at Murkwood
  Verge, story/lore/topics/hist-placement.md "one per tribal settlement"). That tree dies; the cult has its Egg.
  No choice. Reward: fixed (Ahnjazzi's fee if the dive was the player's, row needed).

## Act III: the spies (four quests)

**Hook:** the Eye is in the player's hand, the cult has an Egg, and the Reed wants the one person the cult has
noticed to walk into it carrying the jewel as bait.

- **MQ16 A Key Without a Lock.** The drowned Xanmeer off the coast (canon gives an underwater xanmeer, Lakemire,
  story/lore/topics/ecology-encounters-loot.md; need: the interior, recorded before Act III is fitted, B5). Skills:
  swimming and air pockets, climbing the Hist-chamber shaft, a light alignment, one guardian fight; the Collector's
  hired divers race the player in (a fight, or sneak past). On touching the Eye the sap-dream comes unbidden: the
  ring of trees, the door. No choice. Reward: the Eye of Argonia.
- **MQ18 A Sermon Against Roots.** Opening stage: Nesh-Deeka (fallback Never-Writes-Twice) sends the player in with
  the Eye as bait. The Unbound Root gathers in the abandoned temple's undercroft (`bmv.abondedtemple`, BlackMarsh2
  13,25, interior `01aundergroundcell`); the preacher is the Collector, Opens-the-Last-Door, who knows the player
  and says nothing. His sermon names the state's real abuse. Skills: speech to hold the cover in the private
  interview (a skill check, not a trust meter); if it fails, the house turns on the player (at most six hostiles)
  and the way out is the undercroft's far door north (BM&V's book door to BlackMarshNorth -12,1; need: its book base
  swapped for a hatch) or a fight to the front. Both outcomes reach the same next stage. No choice. Reward: the
  cult's mark (quest item) and the Reed's pay (fixed gold).
- **MQ20 Dreams for Sale.** The Collector shows the player what the Reed hides: it buys sap-dreams and holds the
  dreamers to mine them. Nesh-Deeka was caught altering the dreamers' files to free them, and Never-Writes-Twice's
  honest word has put her among them. A break-in and rescue (B2), no files: the Reed's dream-house near Thorn
  (`bmv.blackmarshnorth.thorn1`, where BM&V keeps guards and prisoners; need: a door to BM&V's doorless Darklight
  Tower `01Tower`, 1,013 refs, as the house). Skills: sneak or lockpicking in, a fight or illusion past the
  keepers, and getting the dreamers out by the water (swimming). If Nesh-Deeka died earlier, the dreamers alone,
  and her cell holds her last letter. Choice: free Nesh-Deeka with the dreamers, or leave her (she knows the Reed
  best); colour only: freed, she leaves the province and writes once at the end. Reward: fixed (row needed).
- **MQ21 The Black Sap House.** The cult's laboratory in Sharpslope Cave (`01templecave`, BlackMarshNorth site),
  where it has been waking the Egg with sap and volunteers, one of whom volunteered twice. Skills: alchemy to know
  what the pools are doing, sneak or blade through, swimming by the underwater way. Last choice (the lie, B2):
  Never-Writes-Twice asks where the sap house is. Tell her the truth and her raid comes while the player is still
  inside, and the player gets the volunteers out through the fire; lie and the cult moves the Egg, and the raid
  falls on the reed-cutters' camp the player named, where the player is standing when it comes. Either way the
  raid is played, someone pays on screen, the Egg is gone toward the door, and Act IV starts the same. Reward:
  fixed (row needed).

## Act IV: the marks and the road (three quests)

**Hook:** the Eye shows marks no one else can see, and the only living hand that knows the wards on them is the
last Shadowscale, who has vanished.

- **MQ23 Marks Only the Eye Can See.** One route chain (B1). The Eye lights marks at BlackMarshNorth's waterfalls
  (`bmv.blackmarshnorth.waterfalls`), the ruin at `ruin12` and the drowned marsh (`marsh`); the wards on the last
  mark need a Shadowscale's knowledge. The player tracks the single vanished survivor (B4; the order's last living
  member dies in 4E 201, story/lore/topics/sithis-nisswo-shadowscales.md): at each site he is already gone, and
  the player reads which way from what the place gives up, then finds his hide at the lizardmen's shack
  (`bmv.blackmarshnorth.lizardmen`). Skills: climbing to the marks, sneak and detection to read the trail, swimming
  between sites; at the hide, speech to have the wards from him, or a fight (his notes carry them). He dies this
  year either way: of his wounds after he speaks, or by the player's hand. No one hunts the player. Reward: his
  blade (fixed, row needed).
- **MQ26 The Root of Accord.** The last mark opens the old roots beneath the northern marsh (BM&V's `01underdark`
  and `01Underdarkmiddle`, entered at BlackMarshNorth -9,15 and -20,22; need: their book doors swapped for root
  hatches). Not a desk (B2): a flooded root-ruin where the carved tableaux and one guardian show the twist: the Root
  of Accord began as a bond freely given by selected Hist and was later made compulsory. The cult's grievance is
  real; its severance is indiscriminate. Skills: swimming, climbing, one guardian fight; the Eye reads the carvings.
  No choice. Reward: the consent carving's rubbing (quest item; it weakens the Last Warden in MQ29) and a fixed
  find (row needed).
- **MQ27 The Road No Map Keeps.** The crossing of the deep basin to the Lost City, guided by Walks-Against-Current,
  who leads and is never escorted (the guide waits at the far side of every swim and climb). It leaves from the
  tribe village's way toward Helstrom (`bmv.tribe`) and goes by Temple Pass (`bmv.templepass`), not by Helstrom's
  gate (LQ30) or landing (LQ25). Skills: swimming, climbing, sneak past or fight the basin's fixed predators,
  alchemy against the poison, shelter at two or three fixed camps. No choice. Reward: the guide's boat as a fixed
  return route.

## Act V: the city and the door (two quests)

**Hook:** the door from the dreams is real, it stands in the Lost City, and Cuts-the-Old-Knot is already inside
with the Egg.

- **MQ29 The City Beneath the First Rain.** The Eye opens the Lost City (need: a home, recorded before Act III is
  fitted, B5; the lore reviewer ruled BM&V's Dwemer pyramid ruins out as they stand). A multi-layer Xanmeer: flooded
  ways, root walls, the cult's rearguard, and its climax the Last Warden, the Xal-Krona bound to the Accord's
  consent. Skills: swimming, climbing, sneak or fight the rearguard, then the boss. The consent rubbing (MQ26)
  weakens the Warden, never releases it (B2): the fight is always fought. No choice. Reward: fixed treasure (rows
  needed).
- **MQ31 The Door That Was Promised.** The sanctuary at the Root, the door from the dreams. Cuts-the-Old-Knot stands
  at the door on every path (B1), mid-rite with the Egg. Two ways through, both always open: speech (a high Speech
  check with the consent rubbing) or a hard, fair duel. Fail-forward: if she is dead before this, Opens-the-Last-Door
  holds the door. Then the line's one choice, each an act at the Root, not a hearing:
  - **CUT**: pour the Egg into the Root and complete the severance; the selected Hist fall silent and the cult is
    the marsh's most feared power, and the player's.
  - **CLAIM**: set the Eye in the Root's socket and close the door to everyone else; the bearer who commands the
    Lost City walks out with a claim to the empty throne that others back for what the jewel means to them.
  - **MEND**: give the Egg back to the Root unbroken, and with the Eye read the old consent back into it, so the bond
    is again one each tree may refuse.
  The closing scene and the end states follow from the choice (old MQ32, folded in, N3): a few fixed swaps in
  Helstrom (the throne hall for CLAIM), Low-Reed Village and the trees the player touched, a letter or two (Nesh-
  Deeka's if freed), and the custodians of MEND named only there. Reward: fixed per ending (rows needed).

## The finale choice and what it carries

CUT, CLAIM or MEND at MQ31, chosen after the door is won by speech or duel. It is the line's only carried state:
it sets the closing scene, the end states in Helstrom, Low-Reed Village and the trees the player touched, and the
one-line reactions of the people who survive. No earlier choice gates any of the three; every player can take any
of them.

## What changed from 30-main-quest and why

1. Cut: §20's trust variables, paths and custody table; §24b's four reward tracks and tier locks; §24.4's "offers
   only what accumulated state has enabled"; §21b.3's wrong-mark lead; MQ15's variant per lead city; the
   carry-forward clauses of MQ20, MQ25 and MQ27. Rewards are fixed per quest; the second Hist is one fixed place
   (Murkwood Verge); Cuts-the-Old-Knot holds the door on every path (B1).
2. MQ22's two reports cut: the lie is MQ21's last choice and its victim the raid the player stands in. MQ20 is a
   break-in and rescue, no files. MQ25's council is background only and no longer a quest. MQ26 is a flooded ruin,
   not an archive desk. The consent evidence weakens the Last Warden but never releases it. MEND is an act at the
   Root; custodians appear only in the closing scene (B2).
3. MQ05 is reworked whole by its own ruling; this outline reads only what it hands on (B3).
4. No living Shadowscales hunt the player: MQ23 tracks the single vanished survivor, who dies in 4E 201 (B4).
5. MQ14 (Archon's lighthouse) and MQ13 (Pusbottom, TG02's place) dropped: the three leads are MQ07, MQ09 and MQ10.
   Gideon and Stormhold homes struck: MQ07 at Murkwood's Bandit Dock, MQ20 near Thorn. The sunken Xanmeer (MQ16)
   and the Lost City (MQ29) are recorded needs (B5, N2).
6. Act II opens on MQ07's false Eye; MQ06 cut; the triangulation is MQ10's last stage, so MQ15 is cut (N1).
7. Helstrom is the seat only; MQ09 leaves BC02's Blackrose cells for the old Rose; MQ10 leaves Soulrest's dock for
   Tear's landing; MQ27 leaves by Temple Pass, not LQ30's gate; one MQ23 route chain (N2).
8. Talk-only quests cut or given skill stages: MQ06, MQ15, MQ22, MQ25 cut; MQ32's epilogue folded into MQ31's
   ending; MQ18's cover is a Speech check with a played failure (N3).
9. The act split (30-main-quest §22) now matches the line spirit below: 17 quests, I 4, II 4, III 4, IV 3, V 2 (N4).
10. The Eye's two statements reconciled in story/lore/eye-of-argonia.md: it grants no kingship by any power of
    its own; CLAIM's backing is what people believe the king's jewel means (N5). The owner's ruling: more Black
    Marsh (Murkwood, Tear, the north's caves and roots instead of offices), less bureaucratic (no reports, files,
    council or desk), every quest won with skills.

## For the data

The planner applies this to `quest.line.main` in `line_spirit` and `line_spirit_beat` (source unchanged in form;
add this file to it).

```yaml
line_spirit:
  line: quest.line.main
  promise: >-
    A nobody pulled out of a burnt camp, owed to no one, becomes the spy the Veiled Reed can deny and the
    treasure-hunter who finds the Eye of Argonia before the Unbound Root does: through smugglers' docks, a drowned
    prison, a wreck, a sunken Xanmeer and the lethal basin to the Lost City and the door in the sap-dreams, where
    the player holds the jewel and chooses what Black Marsh keeps.
  core: >-
    A hunt and a spy story in the marsh: every quest is a place to reach, a thing to find, a cut tree to read, a
    cell to outrun or outfight, won with the player's own skills. The Hist and the sap are the mystery; the cult's
    grievance is real and its severance indiscriminate; the Reed's secrets have victims. Law, custom and the
    state's paper stay in the background.
  free: >-
    Which BM&V cell or building hosts a beat, within this outline's places and recorded needs; names of minor
    people; routes and boats; set dressing; levels and placements (nothing levelled against the player). Choices
    do not multiply: each quest works the same whatever came before; only the finale's CUT, CLAIM or MEND carries
    forward.
  source: >-
    story/design/quests/main-line-outline.md; story/design/quests/30-main-quest.md §16, §18, §19, §23, §24;
    story/design/quests/review/act1.md (the whole main line, round 1); story/lore/eye-of-argonia.md;
    story/lore/topics/hist-and-sap.md; story/lore/topics/labour-and-bondage.md;
    story/lore/topics/sithis-nisswo-shadowscales.md
line_spirit_beat:
  - ord: 0
    beat: >-
      Act I (MQ01 to MQ05, records): the Owing barge and the camp's burning, Cuts-the-Old-Knot taking the courier's
      satchel and sparing the player; a Hist turns its face and its clutch dies; the burnt camp read at dawn and the
      Reed's offer; the first sap-dream (a ring of trees, a door not built, a voice); the cut tree at Low-Reed
      Village and the cell's camp across the leech water; Helstrom behind its thorns, past the empty, swept
      Scalded Throne
  - ord: 1
    beat: >-
      Act II, the hunt (MQ07 to MQ10, outline): a false Eye sold at Murkwood's Bandit Dock, its real setting lifted
      under the Collector's eye; the cell's safehouse and the cult's want of a Mnemic Egg; a route-tablet in the
      flooded cells of the old Rose; a lens-frame dived from a wreck at Tear; the three together place a drowned
      Xanmeer, and the same night the Hist at Murkwood Verge is cut and dies
  - ord: 2
    beat: >-
      Act III, the spies (MQ16 to MQ21, outline): the Eye taken from the drowned Xanmeer and its unbidden dream; the
      player sent into the cult's sermon with the jewel as bait, where the preacher, the Collector Opens-the-Last-
      Door, knows them and says nothing; the Reed's dream-house broken open and its dreamers, and perhaps Nesh-
      Deeka, brought out; the cult's sap house, and a raid the player stands in, on the place they told the truth
      or lied about
  - ord: 3
    beat: >-
      Act IV, the marks and the road (MQ23 to MQ27, outline): marks only the Eye can see, and the last Shadowscale
      tracked from one to the next and found dying; the old roots under the northern marsh show the Root of Accord
      began as a bond freely given; Walks-Against-Current leads the crossing of the deep basin
  - ord: 4
    beat: >-
      Act V, the city and the door (MQ29 to MQ31, outline): the Eye opens the Lost City and its Last Warden, who
      is fought on every path; at the door from the dreams Cuts-the-Old-Knot stands with the Egg, talked down or
      beaten in a hard fair duel; the player ends it CUT, CLAIM or MEND at the Root, and a closing scene shows
      Helstrom, Low-Reed Village and the trees the player touched
```

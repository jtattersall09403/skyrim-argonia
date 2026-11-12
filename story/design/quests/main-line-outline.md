# The Eye and the Root: the adapted outline (Acts I to V)

This is the source for the main quest's Acts II to V. Act I's four records (MQ01, MQ03, MQ04, MQ05, in
`story/data/db/`) are the source for Act I; this file reads only what they hand on. The authored design,
[30-main-quest.md](30-main-quest.md), is history: its cast, thesis and ending families stand where this file keeps
them, and its branch-state model, reward tracks and per-quest table are replaced here.

Rules this outline is written to: the planner's rulings in [review/act1.md](review/act1.md), "The whole main line,
rounds 1 to 6" (each B1 to B5, N1 to N5), and the owner's ruling of 2026-11-06 ([owner-rulings](../../../docs/owner-rulings.md)):
keep the treasure hunt, the spies and the spirit; more Black Marsh, more exciting, less bureaucratic; law and
custom only as background; choices do not multiply; every quest uses the player's skills; no procedural climax. And
the owner's of 2026-11-12: nothing above Morrowind-level scripting, the closed list in
[walk-6-quests](../../../docs/phases/walk-6-quests.md) ("The ceiling"), with each set piece rowed back as
[review/walk6-ceiling.md](review/walk6-ceiling.md) records.

Line-wide rules:
- **One carried choice.** Each quest below plays the same whatever came before. A quest may hold one local choice;
  its result is colour (a line, a body, a letter) and never changes a later quest's stages. Only the finale's CUT,
  CLAIM or MEND carries forward, into the closing message and the world's end states.
- **Act I's flags** (`flag.mq01.reed-joined` and `flag.mq03.tasted` are set on every play; `flag.mq05.minders-hold`,
  `flag.mq05.nisswo-read`; `flag.mq04.adopted` and `flag.mq04.reconciled` are set on every play) are read for one
  line of colour at most, or not at all.
- **Deaths.** Every principal is killable. Where a fallback sender or a document can carry the stage, it does
  (30-main-quest §23); a person the line cannot go on without is named by the quest, and their death fails it and
  shows the main quest's message once. The Eye cannot be lost.
- **At the ceiling.** A stage moves only by a line picked, a thing taken or used, or a death. Nobody is led,
  followed or chased; nothing is timed; nothing burns, floods or appears where the player can see it: such events
  have already happened and are found, or are told. A dream is a message box when the player takes the sap or the
  jewel. A gathering speaks through one person. Places are BM&V's as they stand: nothing is built for a quest.
- **Rewards are fixed per quest** and nothing is levelled against the player (decision 0035). Where a reward has no
  item row yet it is marked "row needed".
- **Places** are BM&V's own (census ids, `docs/research/bmv/census.md`) or another existing place of the load
  order; nothing is built. No main quest stands in
  a faction seat or a slice quest's place (Pusbottom is TG02's, the Blackrose Jail cell 01BlackRoseJail is BC02's,
  Soulrest's dock is TG01's and BC03's, Helstrom's landing is LQ25's, the basin at Helstrom's gate is LQ30's,
  Longmont and Gallows Rock are the Shadowscales'). Helstrom is the seat only: the player returns there between
  acts; no quest after MQ05 is played in it.

## Act I: the burnt camp (records; read, not changed)

**Hook:** an Owing gang's camp has burned in the night, and a woman with a knotted cord let the player live; the
player woke after the fire and hears of it. Nothing of it is staged.

MQ01 No Name on the Work Roll, MQ03 The Cutters' Jar, MQ04 The Tree That Turned Its Face, MQ05 Helstrom Behind Its
Marsh (MQ04 starts when MQ03 ends at stage 90). What Act I hands on: every player is in the Veiled Reed at rank 0,
its deniable hand; carries Nesh-Deeka's page of the dream (the ship's hold with roots grown through its deck in a
ring like trees, a door nobody built, a dry voice without words); knows the cell cuts a Hist's roots and draws its
sap into jars it brings; has only heard of the woman with the knotted cord, Cuts-the-Old-Knot, never seen her; and
stands in Helstrom having met Kaska-Meen and Ei-Tuja (one may be dead) and walked past the hall of the empty, swept
Scalded Throne. There is no sworn or declined split and nobody was saved at the camp. The handler is Nesh-Deeka, at
Salts-The-Catch's house; she is one the line cannot go on without, and if she dies the main quest fails with the
thread-severed message (`flag.main.thread-severed`).

## Act II: the hunt (four quests)

**Hook:** someone is selling the Eye of Argonia, the king's jewel nobody has seen, and the cell that burned the
camp means to buy it.

- **MQ07 The First False Eye.** At the Bandit Dock, on the open ground and the buildings of its own place, smugglers
  have a jewel they call the Eye for sale. Their chief says who has come to buy: the cell, and a courteous collector
  who has already withdrawn and left the player a polite note with him (Opens-the-Last-Door, unnamed). The stone is
  glass; its old setting is real and carries a cut route-cipher. Skills: sneak, lockpicking or pickpocket to take
  the setting from the strongroom chest, which moves the quest; the smugglers stand at their posts and fight as
  guards do if they catch the player, and the way out is a fight or a swim. No choice. The cult buyer's mark, left
  with the setting, names the cave where the cell hides: no tail, no boat. Reward: the setting (quest item) and the
  Collector's note.
- **MQ08 The Unbound Root.** The buyer's mark names the cell's safehouse, a cave in the north of the marsh. Inside:
  the cell's people, its sap jars, and the first plain sight of what the cult wants: a Mnemic Egg
  (story/lore/topics/hist-and-sap.md), which only a dead Hist leaves, and the Eye, to open a door they have dreamed
  of. Skills: sneak or blade through the cell. No choice. Reward: the cell's chest (fixed loot, row needed) and the
  first name of the cult, the Unbound Root.
- **MQ09 The Map Beneath the Old Rose.** The setting's cipher points to an explorer who died in the old Black Rose
  with an Eye route-tablet: a ruin in the far west of the marsh that the marsh took back, not the Rose BC02 uses.
  The tablet lies in the ruin's flooded lower ground. Skills: climbing (FreeClimb) over the fallen walls, swimming
  and breath in the flooded lower ground, a fight with, or a sneak past, what nests there (the marsh's own creatures; no draugr). No choice.
  Reward: the tablet and a fixed find in the explorer's resting place (row needed).
- **MQ10 The Auction of Drowned Things.** The last of the three leads, and the act's end (N1). Salvage divers at
  the north-east coast's ship landing are working a wreck whose cargo holds a lens-frame matching the setting; the Collector is asking
  the same questions. Skills: swimming (dive first, past the slaughterfish), or speech or pickpocket to take it off
  the divers' moored raft. Last stage: the handler, given setting, tablet and lens-frame (a line gated on holding
  all three), fits them together to show one place, a Xanmeer drowned off the coast, and tells that a second Hist
  has been cut, at a recorded tribal tree (Low-Crown, the Paatru Hist,
  `place.hist-heartland.hist-paatru-lowcrown`, one fixed place, B1; story/lore/topics/hist-placement.md "one per
  tribal settlement"). That tree dies; the cult has its Egg. No choice. Reward: fixed (the divers' fee if the dive
  was the player's, row needed).

## Act III: the spies (four quests)

**Hook:** the Eye is in the player's hand, the cult has an Egg, and the Reed wants the one person the cult has
noticed to walk into it carrying the jewel as bait.

- **MQ16 A Key Without a Lock.** A drowned Xanmeer off the coast (canon gives an underwater xanmeer, Lakemire,
  story/lore/topics/ecology-encounters-loot.md; its interior is an existing ruin chosen at record time, B5). Skills:
  swimming and air pockets, climbing the Hist-chamber shaft, the inner door's lever, one guardian fight; the
  Collector's hired divers are already in the dry chambers (a fight, or sneak past). Taking the Eye brings the
  sap-dream unbidden, as a message: the ring of trees, the door. No choice. Reward: the Eye of Argonia.
- **MQ18 A Sermon Against Roots.** Opening stage: Nesh-Deeka sends the player to the
  Unbound Root's front door with the Eye as bait. The Unbound Root gathers in the undercroft of an abandoned temple
  in the north of the marsh; the preacher is the Collector, Opens-the-Last-Door, who knows the player and says
  nothing. His sermon, what he says when the player speaks to him, names the state's real abuse. Skills: speech to
  hold the cover in the private interview (a skill check, not a trust meter), which earns the cult's mark; if it
  fails he turns the player out, and the mark is taken instead from the undercroft's locked chest (lockpicking or
  sneak). Both reach the same next stage. No choice. Reward: the cult's mark (quest item) and the Reed's pay (fixed
  gold).
- **MQ20 Dreams for Sale.** The Collector shows the player what the Reed hides: it buys sap-dreams and holds the
  dreamers to mine them. Nesh-Deeka was caught altering the dreamers' files to free them, and Never-Writes-Twice's
  honest word has put her among them. A break-in and rescue (B2), no files: the Reed's dream-house, a guarded house
  near Thorn. Skills: sneak or lockpicking in, a fight or illusion past the keepers, and opening the cells; the
  dreamers are gone when the player has reported to the Reed's house far away (no escort). Choice: free Nesh-Deeka with the dreamers, or leave her (she knows the Reed best); colour only:
  freed, she leaves the province and writes once at the end. Reward: fixed (row needed).
- **MQ21 The Black Sap House.** The cult's laboratory in a cave of the north, where it has been waking the Egg with
  sap and volunteers, one of whom volunteered twice. Skills: alchemy to know what the pools are doing, sneak or
  blade through, swimming by the underwater way. Last choice (the lie, B2): Never-Writes-Twice asks where the sap
  house is. Tell her the truth and she says the Reed will burn it: when the player next comes, its stock is gone and
  its volunteers with it; lie and the player keeps the house's whole stock of sap (fixed loot), no raid comes, and
  the volunteers are left behind. Either way the cult has already moved the Egg toward the door, and Act IV starts
  the same. Reward: fixed (row needed).

## Act IV: the marks and the road (three quests)

**Hook:** the Eye shows marks no one else can see, and a hand that knows the wards on them belongs to an old
retired Shadowscale, who has vanished.

- **MQ23 Marks Only the Eye Can See.** One route chain (B1). Carved marks at a waterfall, a ruin and the drowned
  marsh in the north can be read only by one holding the Eye (using a mark while holding it shows what it says);
  the wards on the last mark need a Shadowscale's knowledge. The player tracks the one
  vanished retired Shadowscale: at each site he is already gone, and the player reads which way
  from what the place gives up, then finds his hide at the lizardmen's shack. Skills: climbing to the marks, sneak
  and detection to read the trail, swimming between sites; at the hide, speech to have the wards from him, or a
  fight (his notes carry them). No one hunts the player. Reward: his blade (given, or taken; row needed).
- **MQ26 The Root of Accord.** The last mark opens the old roots beneath the northern marsh. Not a desk (B2): a
  flooded root-ruin where the carved tableaux and one guardian show the twist: the Root of Accord began as a bond
  freely given by selected Hist and was later made compulsory. The cult's grievance is real; its severance is
  indiscriminate. Skills: swimming, climbing, the one guardian fight; the carvings are read by using them while
  holding the Eye. No choice. The guardian is the existing Grevious Twilight; no new actor. Reward: the consent
  carving's rubbing (quest item; read at the Last Warden's seal in MQ29 it gives a ward-breaking scroll) and a fixed
  find (row needed).
- **MQ27 The Road No Map Keeps.** The crossing of the deep basin to the Lost City, by the blazes of
  Walks-Against-Current, who sets the player on the way, goes ahead and is found at the basin's far side; she is
  never followed or escorted. It leaves from the tribe village on the way toward Helstrom and goes by Temple Pass,
  not by Helstrom's gate (LQ30) or landing (LQ25). Skills: swimming, climbing, sneak past or fight the basin's
  placed predators, alchemy against the poison, shelter at two or three fixed camps. No choice. Reward: the guide's
  map of the basin; the way back is walked.

## Act V: the city and the door (two quests)

**Hook:** the door from the dreams is real, it stands in the Lost City, and Cuts-the-Old-Knot is already inside
with the Egg.

- **MQ29 The City Beneath the First Rain.** The Lost City stands open ground; the Eye opens only the Root's door
  (its home is an existing ruin of the load order chosen at record time, B5; the lore reviewer ruled BM&V's Dwemer
  pyramid ruins out as they stand). A multi-layer Xanmeer: flooded ways, root walls, the cult's rearguard placed
  where it waits, and its climax the Last Warden, the Xal-Krona bound to the Accord's consent. Skills: swimming,
  climbing, sneak or fight the rearguard, then the boss. The consent rubbing (MQ26), read at the Warden's seal,
  gives a ward-breaking scroll that weakens it and never releases it (B2): the fight is always fought. No choice.
  Reward: fixed treasure (rows needed).
- **MQ31 The Door That Was Promised.** The sanctuary at the Root, the door from the dreams, which only the Eye
  opens. Cuts-the-Old-Knot stands at the door on every path (B1), the Egg in her hands. Two ways through, both
  always open: speech (a high Speech check with the consent rubbing) or a hard, fair duel, begun by her line.
  Fail-forward: Opens-the-Last-Door stands with her, and if she is dead before this he holds the door. Then the
  line's one choice, each an act at the Root (one of three named things there, used while holding the Egg or the
  Eye), not a hearing:
  - **CUT**: pour the Egg into the Root and complete the severance; the selected Hist fall silent and the cult is
    the marsh's most feared power, and the player's.
  - **CLAIM**: set the Eye in the Root's socket and close the door to everyone else; the bearer who commands the
    Lost City walks out with a claim to the empty throne that others back for what the jewel means to them.
  - **MEND**: give the Egg back to the Root unbroken, and with the Eye read the old consent back into it, so the bond
    is again one each tree may refuse.
  The close and the end states follow from the choice (old MQ32, folded in, N3): a closing message and journal
  entry; a few fixed switches, made far from the Root, in Helstrom (the throne hall for CLAIM), Low-Reed Village and
  the trees the player touched, found when the player returns; a letter or two (Nesh-Deeka's if freed); and the
  custodians of MEND named only there. Reward: fixed per ending (rows needed).

## Places to fit at record time

This outline is reviewed at line level (round 4 ruling, [review/act1.md](review/act1.md)); a quest's place is fitted
and checked when it becomes a record. Cell ids, door ids and in-cell mechanics live only here. Known facts, so nobody
rediscovers them (census ids, `docs/research/bmv/census.md`):

- **MQ07, the Bandit Dock:** `bmv.murkwoodext`, BlackMarsh2 -10,6; its own place, not Murkwood. It has no interiors:
  the sale and the strongroom are in the open and in its buildings' exteriors.
- **MQ08, Swampy Cave:** `01Goblincave`, BlackMarshNorth site; one cell holds the whole beat.
- **MQ09, the old Rose:** cell BlackRoseold (BlackMarsh -27,-7, 7 refs) with `gg` (17 refs) beside it, `therose` and
  `mountainpass`: no navmesh, no actors, no placements to use and no doors. The census holds counts, not statics.
  Needs navmesh for its creatures and the tablet placed on a surface at record time; no interior, no new door pair
  and no set dressing.
- **MQ10, the north-east coast's ship landing:** BlackMarshNorth 25,19, attached to no settlement. The only door is 08325C (a Skyrim
  ship-door model, ShipKatariahDoorLoad01) into the ship cell `01Ship` (0AA665, MQ05's); the wreck is an existing
  one of the load order near the landing, chosen at record time; no hull is placed.
- **MQ16:** the drowned Xanmeer is an existing flooded ruin of the load order, chosen before Act III is fitted (B5);
  nothing is built.
- **MQ18, the temple:** `bmv.abondedtemple`, interior `01aundergroundcell` (092944), entered by the temple's front
  door 097D1A at BlackMarsh2 13,25. The cell's 10 placements
  need a `we.clean` row. Its inner doors are Nordic: 097CDE (HHDoor02) and 097D1D (NorWoodDoor01); the back door 097D22 (at -12,1, already Argonian 1DE5DF) is the way out.
- **MQ20, near Thorn:** `bmv.blackmarshnorth.thorn1` keeps guards and prisoners. The house interior
  `01cabinintDUPLICATE002` (129 refs) has no doors, so another guarded house with its own door is chosen; no door
  pair is added.
- **MQ21:** Sharpslope Cave, `01templecave`, BlackMarshNorth site.
- **MQ23:** BlackMarshNorth waterfalls (`bmv.blackmarshnorth.waterfalls`), the ruin `ruin12`, the drowned marsh
  (`marsh`), and the lizardmen's shack (`bmv.blackmarshnorth.lizardmen`).
- **MQ26:** `01underdark` and `01Underdarkmiddle`, entered at BlackMarshNorth -9,15 and -20,22 by book doors. `01Underdarkmiddle` holds a vampire lord and Dawnguard skeletons (vanilla, not ours): clear them
  or make them part of the fight. The guardian is Grevious Twilight, fought there.
- **MQ27:** the tribe village (`bmv.tribe`) and Temple Pass (`bmv.templepass`).
- **MQ29:** the Lost City's Xanmeer is an existing ruin of the load order, chosen before Act III is fitted (B5);
  nothing is built.

## The finale choice and what it carries

CUT, CLAIM or MEND at MQ31, chosen after the door is won by speech or duel. It is the line's only carried state:
it sets the closing message, the end states in Helstrom, Low-Reed Village and the trees the player touched, and the
one-line reactions of the people who survive. No earlier choice gates any of the three; every player can take any
of them.

## What changed from 30-main-quest and why

1. Cut: §20's trust variables, paths and custody table; §24b's four reward tracks and tier locks; §24.4's "offers
   only what accumulated state has enabled"; §21b.3's wrong-mark lead; MQ15's variant per lead city; the
   carry-forward clauses of MQ20, MQ25 and MQ27. Rewards are fixed per quest; the second Hist is one fixed recorded
   tribal tree (Low-Crown); Cuts-the-Old-Knot holds the door on every path (B1).
2. MQ22's two reports cut: the lie is MQ21's last choice (no raid comes on the lie). MQ20 is a
   break-in and rescue, no files. MQ25's council is background only and no longer a quest. MQ26 is a flooded ruin,
   not an archive desk. The consent evidence weakens the Last Warden but never releases it. MEND is an act at the
   Root; custodians appear only in the closing message (B2).
3. MQ05 is reworked whole by its own ruling; this outline reads only what it hands on (B3).
4. No Shadowscales hunt the player: MQ23 tracks one old retired Shadowscale, not "the last" (round 3 B3).
5. MQ14 (Archon's lighthouse) and MQ13 (Pusbottom, TG02's place) dropped: the three leads are MQ07, MQ09 and MQ10.
   Gideon and Stormhold homes struck: MQ07 at the Bandit Dock, MQ20 near Thorn. The sunken Xanmeer (MQ16)
   and the Lost City (MQ29) are existing places chosen at record time (B5, N2).
6. Act II opens on MQ07's false Eye; MQ06 cut; the triangulation is MQ10's last stage, so MQ15 is cut (N1).
7. Helstrom is the seat only; MQ09 leaves BC02's Blackrose cells for the old Rose; MQ10 leaves Soulrest's dock for
   the north-east coast's ship landing; MQ27 leaves by Temple Pass, not LQ30's gate; one MQ23 route chain (N2).
8. Talk-only quests cut or given skill stages: MQ06, MQ15, MQ22, MQ25 cut; MQ32's epilogue folded into MQ31's
   ending; MQ18's cover is a Speech check with a second way on, the locked chest (N3).
9. The act split (30-main-quest §22) now matches the line spirit below: 17 quests, I 4, II 4, III 4, IV 3, V 2 (N4).
10. The Eye's two statements reconciled in story/lore/eye-of-argonia.md: it grants no kingship by any power of
    its own; CLAIM's backing is what people believe the king's jewel means (N5). The owner's ruling: more Black
    Marsh (Murkwood, the north's caves and roots instead of offices), less bureaucratic (no reports, files,
    council or desk), every quest won with skills.
11. Round 3: MQ07 on the dock's own ground, no ship interior; MQ09 has no interior (the tablet lies in the old Rose's ruin
    cells); MQ18's undercroft cleaned by a we.clean row; MQ20 and MQ21 captives leave on their own; MQ26's guardian is
    the existing Grevious Twilight; MQ08's alchemy and back-water route, MQ07's speech-to-buy and MQ10's "at night" cut.
12. Round 4: the outline is line level; cell ids, door ids and in-cell mechanics moved to "Places to fit at record
    time". Cut: MQ21's "someone pays on screen" and fire escort, MQ23's "dies this year either way", MQ10's "the same
    night". MQ21's lie gains the player the stock of sap.

## For the data

The planner applies this to `quest.line.main` in `line_spirit` and `line_spirit_beat` (source unchanged in form;
add this file to it).

```yaml
line_spirit:
  line: quest.line.main
  promise: >-
    A nobody off an Owing barge, owed to no one, becomes the spy the Veiled Reed can deny and the
    treasure-hunter who finds the Eye of Argonia before the Unbound Root does: through a smugglers' dock, a drowned
    prison, a wreck, a sunken Xanmeer and the lethal basin to the Lost City and the door in the sap-dreams, where
    the player holds the jewel and chooses what Black Marsh keeps.
  core: >-
    A hunt and a spy story in the marsh: every quest is a place to reach, a thing to find, a cut tree to read, a
    cell to outrun or outfight, won with the player's own skills. The Hist and the sap are the mystery; the cult's
    grievance is real and its severance indiscriminate; the Reed's secrets have victims. Law, custom and the
    state's paper stay in the background.
  free: >-
    Which BM&V cell or building hosts a beat (fitted at record time, "Places to fit at record time"); names of minor
    people; routes and moored boats; levels and placements (nothing levelled against the player). Choices
    do not multiply: each quest works the same whatever came before; only the finale's CUT, CLAIM or MEND carries
    forward.
  source: >-
    story/design/quests/main-line-outline.md; story/design/quests/30-main-quest.md §16, §18, §19, §23, §24;
    story/design/quests/review/act1.md (the whole main line, rounds 1 to 6); story/lore/eye-of-argonia.md;
    story/lore/topics/hist-and-sap.md; story/lore/topics/labour-and-bondage.md;
    story/lore/topics/sithis-nisswo-shadowscales.md
line_spirit_beat:
  - ord: 0
    beat: >-
      Act I (MQ01 to MQ05, records): the Owing barge, the camp burned in the night and the woman with the knotted
      cord heard of; the Veiled Reed takes the player in; the cutters' jar and Nesh-Deeka's page of the dream (a
      ring of trees, a door not built, a voice); a Hist turns its face; the cut tree at Low-Reed
      Village and the cell's camp across the leech water; Helstrom, past the empty, swept
      Scalded Throne
  - ord: 1
    beat: >-
      Act II, the hunt (MQ07 to MQ10, outline): a false Eye sold at the Bandit Dock, its real setting lifted
      under the Collector's eye; the cell's safehouse, named by the buyer's mark, and in it the cult's want of a Mnemic Egg; a route-tablet in the
      flooded cells of the old Rose; a lens-frame dived from a wreck at the north-east coast's ship landing; the three together place a drowned
      Xanmeer, and the handler tells that the Hist at Low-Crown is cut and dies
  - ord: 2
    beat: >-
      Act III, the spies (MQ16 to MQ21, outline): the Eye taken from the drowned Xanmeer and its unbidden dream; the
      player sent into the cult's undercroft with the jewel as bait, where the preacher, the Collector
      Opens-the-Last-Door, knows them and says nothing; the Reed's dream-house broken open and its dreamers, and
      perhaps Nesh-Deeka, freed; the cult's sap house, which the Reed burns only if the player told the truth
  - ord: 3
    beat: >-
      Act IV, the marks and the road (MQ23 to MQ27, outline): marks only the Eye can see, and one old retired Shadowscale
      tracked from one to the next and found; the old roots under the northern marsh show the Root of Accord
      began as a bond freely given; the crossing of the deep basin by Walks-Against-Current's blazes, to where she
      waits
  - ord: 4
    beat: >-
      Act V, the city and the door (MQ29 to MQ31, outline): the Lost City stands open and its Last Warden is fought on every path; at the door from the dreams Cuts-the-Old-Knot stands with the Egg, talked down or
      beaten in a hard fair duel; the player ends it CUT, CLAIM or MEND at the Root, and Helstrom, Low-Reed Village
      and the trees the player touched are found changed
```

# Dressing interiors by hand: the craft, the measured evidence, and a skill design

Written 2026-11-24 for the owner's question on agents scattering things "in quite random places". Research only; nothing
generated, bought or downloaded. Source tags: [PAGE] I opened and read it; [SNIPPET] search-result summary only (page
blocked or not opened); [OWN] my inference. Local numbers are from my measurement run (section B), not from a doc.

## 0. Live docs, and the one to edit

- Cover hand dressing of rooms today: **none**. `.claude/skills/place-dressing/SKILL.md` is lights, hung lanterns, Hist sap,
  stations and collision boxes only. `place-stock` says "Set dressing (food, crockery, cheap clutter, furniture) stays as the
  source has it". `place-rooms` carries the source's room whole. `docs/design/dressing.md` is ground colour and signature
  things outdoors. `docs/research/new-art/interiors.md` is shells and kits. `docs/design/agent-view.md` and `place-look`
  give the eyes and hands (`probe`, `section`, `in <room> ...`, `place --within`, `move/turn/sink/duplicate`, seat modes
  ground/above/stilts/on/free in `tools/places/seat.py:7-14`) but no rule for where a loose thing may stand.
- Confirmed: the tools can already place one piece on another (`place ... --within <id>`, seat `on`), find floats (`probe`)
  and look into a room. Contradicted: nothing. Superseded: nothing.
- **The one doc to edit: `.claude/skills/place-dressing/SKILL.md`** (add a section "Furnishing a room" and widen its
  description), with a pointer line in `place-rooms` and the trade-kit link in `place-stock`. A separate `place-interiors`
  sub-skill is optional (only if the section outgrows ~60 lines).
- **Finding that changes the question:** in our six places the agents have hardly hand-placed any small clutter. Our rooms are
  the source cells carried whole (Jal-Veesa's ten rooms are King of the Murkmire's own huts). Agent-added rows inside rooms
  across all six places: 29, of which about 17 are lights, doors and walls, 8 furniture, 2 candle lanterns, 2 chests. Agent `ref.add`
  ops outdoors are mostly statics and trees (Jal-Veesa 50 static, outpost m6 38 static + 14 clutter). So the scatter the owner
  saw cannot be reproduced from committed files; it is either from the studio session itself or from work still to come
  (rooms that have no source, section 7 of `PROPOSAL.md` track G). The rules below are therefore preventive.

## A. The craft (sources)

**Bethesda's own practice**
1. Kits give architecture; dressing gives identity. Burgess and Purkeypile, GDC 2013 "Skyrim's Modular Approach to Level
   Design" [PAGE: gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design]: kits should "allow other elements to
   establish the specific identity of any given space"; Oblivion's cloned "warehouse" cells ("fully lit and cluttered rooms
   to copy, paste, and then arrange") were cookie-cutter; players "pick up on repeated clutter first, then the repeated
   architecture"; art fatigue is delayed by "doing away with copy and paste design". Directly relevant: Helstrom carries
   17 copies of one Argonian house (section B9).
2. Todd Howard (Lex Fridman interview, via TweakTown) [SNIPPET, page 403]: a clutter group are "like interior decorators for
   treasure and stuff and trash"; they go through every space; clutter also becomes landmarks for orientation.
3. CK wiki "Bethesda Tutorial Clutter" [SNIPPET; 403 on every mirror I tried]: static clutter is the majority of large
   objects; sets are found by name prefix; "clutter should support the room's function" (its example: a tomb entrance where
   people paid respects); movable pieces make a space feel alive. The Oblivion tutorial (cs.uesp.net "Develop Your Dungeon
   and Clutter") [SNIPPET]: treat a cave as a bandit hideout and choose clutter to match that story.
4. Noah Berry on Morrowind interiors (80.lv "Creating macro environments") [PAGE]: NPC homes were fully furnished "with their
   fully realized clutter and various prop arrangements"; kitchenware and tabletop items were hand-tuned; marsh towns' homes
   "reflect these qualities in their contents and layout", "fishing paraphernalia strewn about"; water under slatted floors.
5. NOT FOUND: any Joel Burgess blog or talk on clutter passes, "storytelling skeletons" or teddy bears beyond the above; no
   Beyond Skyrim interior rulebook (searched; none).

**Tamriel Rebuilt / Project Tamriel (the closest written rulebook)** [SNIPPET only: tamriel-rebuilt.org returned 403 to all
fetches and the Wayback Machine is blocked; the live rules are at wiki.project-tamriel.com/wiki/Interior_Guidelines, also 403].
What the snippets show: showcases needed at least 10 Tamriel_Data items beyond the furniture, "sufficiently clutter the
interior" judged against recent similar interiors; reviewers reject "looks unlived in" by comparison with similar Bethesda
interiors; do not mix poor, middle-class and rich sets without a reason (cellar, prison, servants); do not mix Dunmer and
Imperial sets; do not place whole book series; reviewers flag tapestries too close to walls; floorspace and navigability have
their own section; there is a separate item-placement-and-rotation tutorial (node/379) and a debate "are we being too picky
about item placement" (old_forum p=322432). **I could not read the numeric rules (tilt, floating, rotation, wall gaps).**
Action for the lead: fetch the PTR wiki page from a machine that is not blocked; until then the numbers below are mine.

**Environmental storytelling.** Smith and Worch, "What Happened Here?" GDC 2010 [PAGE: a slidetodoc mirror of the deck; the
speaker-notes PDF at worch.com saved but unreadable here]: establish a discernible chain of events; make it engage the
player; echo the world at large ("premise spawns events, events remind player of premise"); characterisation; avoid setups
the game cannot back; plan how set-dressing pieces connect to one another. [OWN] this is the vignette rule: each room gets one
or two small chains (a net half-mended, a bowl and two cups: someone was visited).

**Composition and real-interior rules** (not read from one source; common practice, marked [OWN] unless cited): focal point
per room, clusters with rest areas between, big-medium-small groupings, repetition with variation, wear along walked lines.
Cited numbers: kitchen planning walkway 36 in minimum, 42 in where walkways meet, work-triangle legs 4 to 9 ft, seating
clearance behind a chair about 32 to 36 in (NKBA Kitchen Planning Guidelines; figures vary by source) [SNIPPET:
kb.nkba.org/uploads/2022/05/Kitchen-Planning-Guidelines.pdf]. Skyrim scale: a character is about 128 units, one metre is
about 70 units (our `extract.py` UNITS_PER_M), so 36 in is about 64 units (a player-wide gap) and 4 to 9 ft is 85 to 190.

**Vernacular housing (wet climates)** [SNIPPET unless noted]: stilt houses exist against flood and vermin; the shaded
undercroft is used for work, storage, animals (Wikipedia "Stilt house"). Rural Khmer house [PAGE]: raised on stilts up to
3 m; upper floor is one room for sleeping and storing clothes, valuables and rice, partitioned by textiles; kitchen is a
separate lower room at the back; "furniture is placed along the walls, leaving the centre free"; a low multipurpose table
serves sleeping, sitting and work; hammock for daytime rest. Seminole chickee [PAGE for "raised floor, posts"; the rest
SNIPPET]: roofed open platform about 1 m up; separate cooking, sleeping and storage chickees; supplies hung from the lowest
roof beams, hides hung in bad weather (a Spanish-language marker text only). Gap: I found no source for drying racks over
a hearth; treat that as [OWN] (smoke curing is common practice, not verified here).

**Automatic furniture arrangement (rules and costs)**
- Merrell et al. 2011, SIGGRAPH [SNIPPET: project page and abstract read; the paper PDF would not render]: guidelines as
  terms of a density function sampled by Monte Carlo; user study (18 people, five rooms, p<0.01) preferred layouts with
  suggestions. I could not read the term list or numbers; from memory the terms are clearance, circulation, pairwise
  relationships, conversation, balance, alignment, emphasis [OWN, unverified].
- Yu et al. 2011 "Make it Home" [SNIPPET]: hierarchical and spatial priors learned from well-furnished example scenes, tied
  to visibility and accessibility, optimised by simulated annealing.
- Holodeck (CVPR 2024) [PAGE: arxiv.org/html/2312.09067v2]: ten constraints in five groups: global (edge, middle; exactly
  one per object), distance (near about 50 to 150 cm, far at least 150 cm), position (in front of, side of, above, on top
  of), alignment (centre aligned), rotation (face to). DFS on a grid, anchor object first, rotations in 90 degree steps, hard
  constraints no collision and in bounds, 30 s budget. Human ranking: constraint layouts 0.706 against direct LLM
  coordinates 0.364 ("no better than Random": out-of-bounds and collisions).
- LayoutGPT [PAGE abstract only], I-Design [SNIPPET: scene graph from several LLM agents, backtracking converts relations
  to positions, collision-free, in bounds], LayoutVLM (CVPR 2025) [PAGE: arxiv.org/html/2412.02193v3]: five relations
  (distance, on-top-of, against-wall with wall-normal alignment, point-towards, align-with), differentiable physics loss
  (pairwise 3D box overlap, boundary projection), at most one orientation constraint per asset. Failures it reports: direct
  pose prediction gives collisions and out-of-bounds (a piano in a chair, shelves outside the room), weak global coherence,
  semantic loss. Average layout quality 58.8 for LayoutVLM against 18.0 I-Design, 16.6 LayoutGPT, 5.6 Holodeck.
  Newer: AutoLayout and NaLA [SNIPPET]: floating and overlapping objects are the common failures; NaLA's floating metric
  is "fraction of objects with no physical support" with wall/ceiling-mounted items excluded.
- **What transfers** [OWN, grounded in the above]: (1) never let the agent write absolute coordinates for a loose item;
  give it relations and have a tool turn them into poses; (2) place hierarchically, anchor first; (3) check hard
  constraints (no overlap, in bounds, supported) by a tool, soft ones (facing, near) by score; (4) render and look.

## B. The evidence (measured here)

**Method.** I read every interior CELL of Skyrim.esm, Dragonborn.esm, King of the Murkmire.esp and Black Marsh.esm
(`~/games/skyrimse/Data`, own ESM reader; REFR base, position, rotation, scale; NAVM triangles), joined to
`out/places/catalogue/bases.jsonl` for model, kind and bounds (lights from `lights.jsonl`). Sample after filters: **112
houses and huts**: 70 vanilla Skyrim farms and town houses (inns, guardhouses, cellars, abandoned and over-260 m2 cells
dropped), 27 King of the Murkmire huts and houses (incl. the ten Jal-Veesa carries and some player homes), 10 Dragonborn
(Raven Rock, Skaal), 5 Black Marsh.esm cabins (only 3 distinct shells; BM&V's big 1557-piece Argonian house cell is not in
the sample). Median room 68 m2 (vanilla 67, KotM 52). A piece is classed by model path and record type into furniture, bed,
seat, container, table or shelf, small clutter classes (tableware, food, drink, ingredient, book, vessel, tool, gear,
candle, firewood, valuable), floor cover and hung decor. "Resting on a surface" = the item's lowest point within 14 units of a
table, shelf, chest, bed, barrel, or another item's top and its origin within 12 units of that top's footprint (rotated
box). "On the floor" = its lowest point within 10 of the room's walkable-mesh height. Wall distance is the distance to the
edge of the filled walkable mesh, which sits about 20 to 30 units off the real wall, so only the relative figures matter.
**Cannot be measured from this data:** the room shell's real walls and ceiling height (not read; only the walkable mesh),
whether a piece is hung from a hook (there is no hook record; hung is inferred from height), intent, and wear. 27% of small
items stay unresolved by my rules (16.5% above floor with no top found, 6.7% off by 10 to 45 units, 3.5% no floor found);
so the on-surface share is a **lower bound**, the on-floor share is solid. Numbers are medians or shares over the 112
rooms; vanilla (V) and King of the Murkmire (K) differ where noted. Scratch scripts: scratchpad `dress/meas.py`, `run.py`,
`agg.py`, `ours.py` (session-local; commit as a tool if the checks in C are built).

**B1. How much.** Vanilla house: median 93 small items per room, 1.43 per m2, plus 11 containers, 4 chairs, 7.7 tables or
shelves, 10 hung decor (pelts, garlic, rabbits, mounted heads), 3.7 floor covers, 6 candles; total median 80 small items
over all 112 rooms, 1.24 per m2. K huts are sparser: 58 per room, 0.97 per m2, 5.5 containers, 5 floor covers, 12 hung decor,
13 ingredients and 1 hung plant per room (the huts hang little; they use hung decor pieces). Beds 1.5 per house (K 2.1).
Lights: median 5 light references per room (K 2).

**B2. On a surface or on the floor.** All rooms: surface 55%, floor 18%, unresolved 27% (hung, wall, slightly off). By class
(share on the floor / on a surface): tableware 2 / 78, book 4 / 76, ingredient 5 / 72, food 8 / 62, drink 3 / 54, valuable
4 / 87, gear 11 / 55, vessels (baskets, buckets) 51 / 28, tools 47 / 25, candle stands 45 / 29, other clutter 38 / 29.
Things that are on the floor (share of that model's instances that stand on the floor): floor candlestick 98%, large
firewood pile 100%, small and medium piles 93 and 89%, hay scatter 91 to 100%, broom 82%, basket04 80%, kettle 78%, basket02
67%, basket05 55%, bucket 42%, spit 94%, small crate 57%, woven fence 50%. Never or almost never (under 5% on the floor,
n at least 40): tankard (494 seen, 6 on floor), wooden plate (285, 1), bowl (268, 2), bread (234, 3), wine bottles (190
and 172, 5 and 0), cast-iron pot (125, 2), fork, cheese wheels and wedges (0), glazed plates, cups and goblets (0), apple,
books (3 and 0), garlic, eggs, ladle, silver plate and goblets, ingots, coins, dagger, wreath, candle lanterns. Potatoes
16% and cabbages 17% on the floor (sacks and crates are their homes). So the rule is by kind, not by a global share.

**B3. Against walls.** Floor-standing small things: 78.5% within 30 units of the walkable-mesh edge, 87% within 60, 93%
within 120; measured to the nearest wall or large furniture: 89 / 96 / 99%. Floor items are against something; the clear
middle stays clear. Beds: 92% have a side within 36 units of a wall, 84% two sides (a corner); containers 90% within 36 of a
wall, 94% within 72; tables, shelves and counters (long pieces) 84% within 36. K huts: containers 82%, long furniture 76%.

**B4. The clear middle.** Furniture and containers cover a median 14% of the walkable floor (p10 to p90: 7 to 25%); of floor
at least 60 units from a wall, a median 77% (p10 40%, p90 89%) is at least 40 units clear of every piece; overall 53% of the
floor is at least 40 units from any furniture. Floor things in the centre are rare (5% of floor-standing items are more
than 60 from a wall).

**B5. Turns.** Yaw measured from the room's own axis (circular mean of its furniture), deviation folded to 0 to 45
degrees. A random pose has 6.7% within 3 degrees, 22% within 10, 33% beyond 30. Vanilla: beds 50% within 3 degrees, 86%
within 10, 5% beyond 30 (median 3); containers 33 / 59 / 18% (median 7); tables and shelves 37 / 57 / 16% (7); seats
23 / 47 / 18% (median 11); small clutter overall 22 / 45 / 39% (median 13). By class: tableware median 13, books 11,
food 17, ingredients 17, vessels 8, tools 12. So furniture is square or near it, clutter is turned a moderate, varied
amount: about one in five exactly square, a third more than 30 degrees off. A drop in an agent's turns to "all 0" or to
"fully random" are both outside this.

**B6. Clusters and surfaces.** Linking items within 40 units: only 14.8% of small items are alone; 79% sit in a group of 3
or more; groups of 2 or more have median size 4 (p90 15, max 45: a shelf or a table). Median real surfaces per room
(table, shelf, chest, bed at least 40 wide) 13; a median 5.5 carry something. Items per used surface: median 2, p90 6, max
25. Surfaces used: chests and dressers (299 uses) and tables and shelves (367) lead; beds 30 (K: 9 of 57).
Exact repeats (same base at the same turn) are 5% of small items (K 1%).

**B7. Lights.** 5.7 light references per vanilla room (K 2). By position: 41% on a wall within 60 units of it at 40 to 180
high, 13% above 180 (chandeliers, hung), 7.5% on a table or shelf, 2% on the floor, the rest at mid heights over a fixture;
**89% of lights have a candle, lantern, sconce or table piece within 30 units (K 100%)**: Bethesda never leaves a light with
no fixture.

**B8. Chairs.** 77% of seats are within 150 units of a table; of those 64% point their axis (either way) within 30
degrees at the table (K 91%, V 53%). Weak: I did not verify the chair model's front axis, and benches and chairs at table
ends are not distinguished. Treat as soft.

**B9. Our six places as the agents left them.** 38 rooms analysed (Jal-Veesa 10, Helstrom 25, Dushnikh-Yal camp 2, m13 1; the rest
have no source cell I read). **Jal-Veesa as carried** (the K huts less removals): 38 small items per room (median), surface
62%, floor 11%; furniture within 3 degrees 63%; every bed in a corner, every container against a wall; lights 1.8 per room, 100%
with a fixture; exact repeats 1%. It looks like King of the Murkmire, as expected. **Helstrom's unique rooms:** surface 59%,
floor 11%, lights 11.8 per room, 92% with a fixture. **Duplication:** Helstrom has 17 copies of the one BM&V Argonian house
with 6 distinct item-count signatures across 17 rooms and 128 to 144 pieces each; they differ only by agent additions or
removals. **Agent additions** (rows with no `src` in a draft bundle space): 29 in rooms (list: scratchpad `dress/added.json`):
Helstrom's Xanmeer hall 6 benches, 10 lights, 2 walls, a door; Chainbreaker's safehouse a chest and 2 candle lanterns;
Elder's hut a bedroll; ship and dock a cooking pot each; m13 a hut's static, furniture and container. Too few to give a
distribution. The comparison of agent against Bethesda hand placement **cannot be made from these files**; the shares above
are what a correct agent room must match.

**Well-evidenced:** B2 by-kind floor rule, B3, B4, B6 clustering, B7 light-with-fixture. **Weaker:** the exact
on-surface share (a lower bound), chair facing, wall distances in units. **Inference:** everything in C.

## C. Skill design

### C1. Dressing order (the recipe)

1. **Read the room's function.** From `place-people` (household size, head, band, `trade`) and the matching `kits.json`
   kit (23 trade kits with `home` and `never` lists, `newworld/sources/stock/kits.json`). Zones: sleep, cook and eat, store,
   work, worship, wash, entry. A one-room hut has all of them in a rough ring round the hearth with the entry in one wall.
2. **Anchors** (large, square to a wall within 3 to 10 degrees): bed(s) in a corner (B3: 84% corner), hearth or fire,
   table, wall shelves, chest or wardrobe against a wall. Black Marsh: sleep on a platform or hammock, off the wet floor.
3. **Secondary furniture:** seats toward the table or fire, stools at the work bench, a second chest by the bed, a drying
   rack by the hearth. Leave the centre clear: at least 64 units clear walkway from the entry to every bed, seat, container
   and the hearth (about 36 in; the mesh check in C2).
4. **Surface sets** (the bulk: 55%+ of small items): each set on a table, shelf, chest top or bench, in groups of 2 to 6
   (B6), tableware, food, books, ingredients, tools by function. Place settings: one plate, cup, perhaps a bowl per diner.
5. **Hung things:** from beams, hooks and walls: pelts, braids of herbs, nets, dried fish, lanterns, baskets; Black Marsh
   rooms hang first and stand last.
6. **The few floor things**, only floor-allowed kinds (B2): baskets, buckets, sacks, firewood, a broom, a kettle, floor
   candles, rugs and bedrolls, near a wall or furniture (96% within 60).
7. **One or two vignettes** from the person's backstory and stock rows (a net half-mended by the fisher's seat; an
   egg-tender's warming bowl and cloths; the healer's bench with a mortar and bound herbs; a drying rack of fish at the
   hearth). Each is a chain of events (A: Smith and Worch), with a reason traced to a people or stock row.
8. **Light last:** every light on a fixture (candle, lantern, sconce, fire); about 1 per 12 m2 in a hut (K), 1 per 13 in a
   town house (V).

### C2. Verbs for the studio (ordinary placed rows the owner can edit)

Exist today: `place <base> <x,y[,z]> [--rot] [--above dz] [--within <id>] --why`, `move`, `turn`, `sink [--until-feet-buried]`,
`duplicate`, `delete`, `probe`, `in <room> overview/at/probe`, seat modes `on`, `free`, `above`, `stilts`
(`tools/places/look/verbs.py:18`, `tools/places/seat.py:7-14`). `tools/places/hands.py` itself is only the row-merge guard
for stages running beside hands (`hands.py:1-9`, `merge`, `keep_placed`), not a placement vocabulary.
New (each a thin layer over `place`, writing seat `on` and a `why`):
- `dress <base> on <surface> [--n k] [--spread]`: picks a free spot on the surface's top (from `model_bounds` footprint in
  `seat.py`), z = the top, yaw = surface axis plus a small random turn (kind-dependent: tableware ±15 to 35, books ±10 to
  25, bowls ±45), refuses a spot that overlaps another piece's box.
- `against <thing> <wall> [--gap 4]`, `beside <thing> <other>`, `under <surface>`, `corner <thing>` (turns it square to the
  wall, back flat).
- `hang <base> from <beam|hook|wall piece>`: z so the item's top is at the hold; `--wall` fixes it flat to a wall.
- `set <table> for <n>`: one plate, cup and optional bowl per place, at 55 units from the table centre, turned toward it,
  a jug in the middle.
- `fill <shelf> [--with kind,kind]`: rows with spacing 8 to 20 units, small yaw jitter, a few gaps.
- `stack <base> x n`: pile, offset ±3 units, turns varied.
- `cluster <anchor> [--big B --medium M --small S]`: one big thing, two or three medium, a handful small, within 40.
- `vignette <name> at <place>`: templates `fisher-corner`, `egg-tender-shelf`, `healer-bench`, `hearth-drying-rack`, `smith-
  bench`, `sleeper` (bed, chest, boots, a cup), each expanding to rows from the person's kit.
- `probe --dress <room>`: runs the C3 checks.

### C3. Rules as checks (numbers from B; a probe after dressing)

1. **No small item on the bare floor** unless its kind is floor-allowed (basket, bucket, sack, barrel, firewood, broom,
   kettle, floor candle, rug, bedroll, tool leaning on a wall, hay): the allow list is data, with B2's never-list (cups,
   plates, cutlery, food, bottles, books, ingredients except in sacks, coins, jewellery).
2. **Every loose item rests on something**: lowest point within 6 of a top inside its footprint, or of the floor within 3;
   no float over 6, no sink over 4 (existing `probe` floats extended; hung items are exempt only with a `hang` anchor).
3. **Share on a surface:** at least 45% of small items on surfaces in a house (vanilla 55%, lower bound), floor at most 25%
   in a vanilla-type house, at most 15% in Black Marsh (hung or raised instead), no more than 8 items on one surface unless
   a shelf (p90 6, max 25).
4. **Clear middle and reach:** at least 60% of the floor at least 60 units from the walls is at least 40 from every piece
   (B4 median 77%); the walkable mesh reaches the door, every bed, seat, container, station and the arrival with at least
   64 units clear width; the arrival point and 100 units in front of each door and its swing stay empty.
5. **Furniture squareness and clutter turns:** beds, tables, chests, shelves within 10 degrees of the room's axis (B5:
   57 to 86%) and at most 20% beyond 20 degrees; clutter not all square (at most 35% within 3 degrees) and not all random
   (at least 40% within 20 degrees); a row of 3 or more of one item at the same turn and equal spacing fails.
6. **Anchoring:** beds and chests have a side within 36 units of a wall (B3: 92 and 90%); tables and shelves 84%.
7. **Groups:** at most 20% of small items alone (vanilla 15%); a group of more than 15 is a shelf or table; no pile of 5 of
   one item without a container.
8. **Traceable:** every item has a `why` that names a household stock row, a person's trade kit `home` entry or a vignette;
   an item with none is an error ("nothing unexplained").
9. **Wet floor (Black Marsh and any marsh or stilt room):** stores raised on racks or platforms (top at least 20 units over
   the floor) or hung; sleeping on a platform, bedroll on a raised pad; no sacks, food or books on bare floor; baskets and
   buckets allowed only on a platform.
10. **Lights have a fixture** within 30 units (B7: 89%, K 100%), no light inside a solid, at most 4 shadow-casting lights
    in view (`interiors.md` finding 5).
11. **No duplicate rooms:** two houses within a place may not share the same item-count signature plus more than 70% of
    the same positions; vary at least vignette, work zone and 20% of the surface sets (Helstrom has 17 copies of one house).

These are checks an agent runs; `place-stock reach` stays for material rules.

### C4. Judging by eye after the checks (fixed views)

`in <room> at door --eye` (what do I see first from the entry? one focal thing, not a sprawl), `in <room> at <bed> --eye`
(what the sleeper wakes to), `in <room> overview` (top-down, ceiling cut: is the middle open, is each zone a place, any
perfect grid?), then each surface close up (`at <surface> --high`): is each set one thing happening? Questions: who lives
here and what do they do? where do they sleep, eat, cook, keep things and work? what would they have left out today? what
does a visitor from another house see that no other house has? what is on the floor, and would it be?
**Only the owner's eye can settle:** how much clutter is "lived in" versus tidy for Argonia, how much the Hist-people hang
versus stand, taste of the vignettes, whether the chair-facing and light numbers read right; nothing here replaces his view.

### C5. Variety across a province

- Layout templates per shell and household type: for each shell, three to five placements of the anchors (bed corner, hearth
  or table positions) as data, each also mirrored and rotated 90 degrees, so one carried shell yields 6 to 10 rooms.
- Wealth band (W1 to W6) scales quantity and quality (tableware count, chests, rugs, candles; pewter or glazed over wood),
  not the plan: B1 gives vanilla 93 small items against K 58.
- Trade sets the work zone (fisher: net rack and traps, smith: bench, healer: drying herbs and mortar); tribe sets motifs
  and hung things (Argonian: reed, egg, scale and bone; Dunmer: ash colours and bonemold; Imperial: wine and ledgers).
- A shared vignette pool, each used at most once per place or per ten houses; per-house seeds from the place and room id so
  reruns are byte-stable (the rule `dressing.md` already uses for outdoor kinds).

### C6. Where it goes

- `place-dressing`: "Furnishing a room": C1 order, the C2 verb table (existing and new), the C3 check list with numbers and
  the allow and never lists, the C4 views and questions, the C5 variety rule. Widen the description to "furnishing a room".
- `place-stock` section 5 (loose things): point to the kit's `home` entries as the source of room contents and to
  `dress --why` as the way a row is traced. `place-rooms` "Look inside": run `probe --dress` after each carried room.
- `place-people`: nothing new; it supplies household size, trade and backstory.
- Tools to build (deliver lane, not this report): the C2 verbs and `probe --dress`; the allow/never list as
  `newworld/sources/stock/floor_allowed.json`; a vignette template file; a measurement tool from the scratch scripts
  (`tools/places/dressing_measure.py`) rerun when the checks' numbers need renewing.

## Recommendations (each with its evidence)

1. Build `probe --dress` and `dress ... on` first: they stop the failure LLM layout research reports most (floating,
   collisions, direct coordinates no better than random: Holodeck human study 0.364 against 0.706 for constraints).
2. Fetch the Project Tamriel Interior Guidelines page and Tamriel Rebuilt node/379 from an unblocked machine; replace my
   [OWN] numbers with theirs where they are stricter (the only gap in A that matters).
3. Fix Helstrom's 17 identical Argonian houses before more dressing (B9: 6 count signatures over 17 rooms; Burgess and
   Purkeypile: players notice repeated clutter first).
4. Re-run the measurement over the BM&V big house cell and Baan Malur cells (16 in `out/places/srccells`; not in my sample).
5. Ask the owner for the case he saw (place, room, capture): the files show almost no agent-placed clutter, so the real
   failure mode is still unseen.

Covered: out/places/srccells, out/places/bundles/draft.* (all six places), out/places/catalogue (bases, lights),
newworld/places/*/spaces, agent-edits, stock sources, skills place-look/dressing/stock/people(rooms,routines read in part),
docs/design/{agent-view,dressing}.md, PROPOSAL.md track G, Skyrim/Dragonborn/KotM/Black Marsh ESMs · Skipped: Baan Malur
cells and Dawnguard houses (not measured), place-people and place-routines in full (only fields used), vanilla shell
walls and ceilings (not read), every Tamriel Rebuilt and CK wiki page (403), Merrell and Make it Home paper texts
(unrenderable), Burgess's blog (no clutter material found).

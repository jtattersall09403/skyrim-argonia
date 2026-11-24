# New art for Argonia: what we could do, and what I recommend

Written 2026-11-24 for owner call #93, rewritten the same day from the owner's comments on #94. Nothing beyond three
test examples has been made. The research behind it sits beside it in this folder:

- [have-get-make.md](have-get-make.md): what we hold, can compose, can get, or must genuinely make, checked by looking.
- [tooling.md](tooling.md), [skyrim-asset-pipeline.md](skyrim-asset-pipeline.md), [visual-consistency.md](visual-consistency.md): tools, prices, policies; getting a model into Skyrim; keeping a set looking like one game.
- [gear-and-clothing.md](gear-and-clothing.md), [wearables-by-hand.md](wearables-by-hand.md): weapons, armour, clothing, and fitting all ten races.
- [places-and-pieces.md](places-and-pieces.md), [identity-vs-lore.md](identity-vs-lore.md): places, pieces, and each culture against the lore.
- [foreign-and-remnant.md](foreign-and-remnant.md), [ruins-and-weathering.md](ruins-and-weathering.md): Imperial, Dunmer and other peoples; ruins; making any kit look like it stands in Black Marsh.
- [nature-and-vessels.md](nature-and-vessels.md), [vegetation-and-vessels-by-hand.md](vegetation-and-vessels-by-hand.md): plants, trees, boats, wrecks.
- [interiors.md](interiors.md), [buildings.md](buildings.md), [buildings-in-places.md](buildings-in-places.md), [interior-dressing.md](interior-dressing.md): interiors, new buildings, kits, stairs, doors, how our buildings enter a place draft, and how rooms are dressed.

The three test examples (a dugout canoe, a Stone-Sleeper glaive, a root-grown hut) are in the
[asset explorer](https://claude.ai/artifact/QcwA43dLwFabYVNJi8hSpC).

## 1. The short answer

**We hold far more than we use. The first job is to know exactly what, by looking, and put it to work. New art
comes after that, for the short list that is genuinely missing, made by hand in a 3D scene with the generators as
helpers, inside a budget of about $90.**

In order:

1. **Know what we hold.** The looked-at index is being built now (section 2): every model we hold drawn once and
   searchable by how it looks, not only by its name.
2. **Use what we hold and what Nexus has** (track A): held pieces wired into our tables, things composed from held
   pieces, mossy and wet variants by record, lore-true sources, and flat emblems (track B).
3. **Run the cost experiment** (section 4): about $5, to choose the cheapest route that is good enough, by kind of
   thing, before spending the rest of the budget.
4. **Build the model workshop and prove each kind of making once**, on things that are genuinely missing.
5. **Widen track by track**, each your choice after its proof, inside the budget.

## 2. What we hold, can get, or must make

### The method, which is the rule

For every item, in this order; "not held" may only be written with the searches and looks listed:

1. Name it every way: the lore word, the plain word, the real thing, what a modder might have called the file
   (the grave-stakes are files named "roadsign").
2. Search what we hold by record name, display name and model path across every mod we hold, vanilla and the
   Creation Club content included, and by how it looks in the looked-at index; list model files no record uses.
3. Search what we have built: drafted places' plans, place records and source places, for the thing existing as
   an arrangement of pieces. Record the recipe.
4. **Look at every candidate**, on a contact sheet or alone. A name is never enough either way.
5. Check use: in our tables, placed somewhere, or held and idle.
6. Only then Nexus, in both Skyrim games, by name and description.
7. One verdict: have, compose, get, adapt something close, make, or could not look.

### The looked-at index (being built)

The studio's asset search already exists, but it is text only: it embeds each model's names, editor id, file
path and a plain-English line, so it finds the grave-stakes only because their editor id says "GraveStake", and
knows nothing of how a model looks. The index adds the other half:

- every model we hold (19,385 distinct; 9,087 from mods, done first) drawn once to a small picture, with a failed
  drawing marked as "could not look" and never as "not held";
- a picture embedding of each, so a search for "dugout canoe" or "fish trap basket" finds models by their look;
- the studio's search scoring both halves, so you get the same results there;
- a contact-sheet action, so an agent looks at 48 candidates in one picture.

It runs under the job guard so it resumes after any stop. Its acceptance test is the list of things I wrongly
called missing: each must come up in the top ten by look.

### What the check found (about 90 models looked at, one at a time)

| Thing | Verdict | What we hold |
|---|---|---|
| Native river boats | **have** | King of the Murkmire's 10 m plank boat with a woven-reed cover and striped awning; the same hull with a pole-sail and sweep; a 25 m barge under a reed roof placed nowhere |
| Dugout, canoe, punt | **make** | nothing in 28,880 model files or 40,968 records; the nearest held are rotted logs |
| Reed raft; wrecks | **compose** | cut logs and scaffold floors; ship planks and held hulls |
| Fish weir, trap, net rack | **compose / have** | Reed-Sill Weir's is four woven fences, two log walks, hanging moss, two net baskets and a fish rack |
| Grave-stakes | **have** | five in Here There Be Monsters, placed nowhere |
| Sap tap, bowl, bottle, jar | **have** | vanilla's Sleeping Tree camp pieces |
| Egg clutch | **have** | King of the Murkmire's eggs in five colours, and nests |
| Hammock | **have** | a net hammock on a frame; it has no bed record |
| Cattails, giant fungus, lilies, prop-root mangrove | **have** | cattails in four styles, a mushroom tree, about 16 lily models, a mangrove with prop roots |
| Company crates, signs, warehouse | **have** | vanilla's East Empire set |
| Black Marsh weapons | **have, mostly** | over 60 native weapons in Here There Be Monsters and 14 in King of the Murkmire |
| Obsidian weapons | **have, now used** | the Xanmeer make for every type and tier it covers; the glass recolours only for the three two-handers at the tier the Xanmeer make lacks (done 24 November) |
| Shields, masks, crests, loincloth, necklaces | **have, fit unknown** | seen as ground models only; fit on the ten races not yet looked at |
| A sick and dying Hist | **have, as a block** | the "sick Hist bark" block: our recolour tool's darkened copy of the Hist bark on a base of ours, with King of the Murkmire's dead roots set round the tree (docs/design/blocks.md; the place-story skill; used in Jal-Veesa's plan). No new art. |
| Huts | **have** | a mud-dome stilt hut, round bamboo huts, a stilt house |
| Root-grown buildings | **make** | root pieces are held; no root-grown building of any kind |
| Whip, claw, rapier, halberd in a Black Marsh make; gourd; toll bar; milestone | to check in the index | not found by name |

### Where the province is still thin (measured)

| Area | Where it is thin |
|---|---|
| Use of gear | The 11 lowest-tier "bog iron" weapons are vanilla iron and steel models. Every Argonian village guard wears one set; every town watch one other. |
| Clothing | 12 of the 23 trade kits have no clothing row. In the six stocked places 126 of 165 people have no authored clothing. |
| Places | 126 of 258 places take a source built from vanilla Skyrim pieces. About 19 sit on sources that contradict the lore: four on Dwemer ruins, three Velothi places on Daedric ones, six Imperial ruins on snowy Nordic forts, Kothringi ruins on Nordic stone. |
| Interiors | In the four drafted places with rooms, 18 of 41 rooms are one Helstrom house interior. The Root-Folk's 19 places have 3 source interiors for 22 households. |
| Pieces | 47% of doors in the drafts are Nordic-ruin or Solitude doors. The vanilla candle lantern is placed 173 times; the fur bedroll is 27 of 97 furniture pieces. |
| Loose things outdoors | At Ashgate Landing loose things (reed bundles and others) were left scattered on open ground; you moved them by hand. It is a row in skill-fixes, owed a fix in the stock and dressing skills. |
| Marks | No culture has a standard and no story line a sign. |
| Plants | The ground layer is 57% of all plant placements: reeds 7.4% on one model, lilies 4% with one model at 93%, the fern family 26%. Held cattails, lilies and fungus are barely used. |

### What Nexus adds

Searched in both Skyrim games by name and description. Nothing was downloaded, so the big packs' contents are
known only from their descriptions; a mod of the 2011 game needs its models converted at staging.

| For | Found |
|---|---|
| Plants | GKB Green Trees (2011, 19268; 40 of its models already held), Tropical Lands Assets (33446), Waterplants (6092), Harvestables (2011, 15108) |
| Ships | Ships and Boats of Tamriel (41653), three 2011 ship packs, two pirate packs, two sailing mods that mention canoes |
| Banners | Incaendo's Banner Resource (17604) and 2 (94919), over 200 banners; Flags Resource (56152) |
| Argonian dress | Argonian Mercenary Armor with Armored Tail (2011, 27676), Argonian Raptor Feet (2011, 19283), HistBone and Bonewood Argonian Armors (2011, 99144), Argonian War Tails (2011, 28502), Saxhleel Sundries (191593), Simple Straw Hats (89962) |
| Dunmer, Imperial | Morrowind Hlaalu Architecture (157997), a Velothi kit (107571), Den of Fen assets (167214), Beyond Skyrim Bruma's assets, Imperial Stone (6481) |
| Ruins, overgrowth, buildings | an Ayleid kit (2011, 90667), ivy and hanging-moss packs, Stroti's Stilt House (2011, 61824) |

## 3. How anything new would be made

### By hand, with eyes, in a workshop

The method is the one your place drafting uses: the agent names what to look at, the tool places the camera, the
agent measures for truth and looks for judgement, changes one thing and looks again.

### Blender: one warm session per batch, not one per thing

Starting Blender for every model would waste most of the day. The pattern:

- **A warm workshop daemon**, like the studio's look daemon: one long-lived process that imports Blender as a
  Python module (the `bpy` package, no window) and holds many models at once, each in its own collection. The
  agent sends it actions (load, measure, view, select, edit, clean, wrap, export) and it answers at once.
- **An agent owns a batch**, a whole family at a time: the nine tribal weapons, the four boats, a building kit.
  It loads them all into one session, takes each through the stages, and compares siblings side by side in the
  same scene, which is also how a family stays consistent.
- **Two or three batches in parallel**, one daemon each, on the build machine's four cores.
- **Eyes stay in the studio's own renderer**, which already draws models fast with no graphics card; Blender
  renders only for checks that need it.

### Measure and look, at every stage

No stage passes on numbers alone or on a look alone, and each stage can send the work back.

| Stage | Measured | Looked at | If it fails |
|---|---|---|---|
| Brief and reference images | views present, plain background, size | reads as the thing, in its builder's style, beside its anchor | new prompt |
| Generation | triangle count, closed shape, proportions | the outline from fixed views against the reference | throw away, regenerate |
| Shaping by hand | dimensions, grip point and axis, length against the donor | from all sides, in the hand or on the body | edit again |
| Clean-up | stray vertices, holes, hidden faces, loose pieces, triangle budget | before and after from the same views | undo, clean more gently |
| Surface | pixels per metre; colour and brightness inside ranges measured from the game | beside vanilla neighbours in one lighting set-up | re-wrap, re-grade |
| Into the game's format | collision fits, tags and markers kept, the file re-read | the written file drawn in the studio | fix the write step |
| Interior planning | floor heights, headroom, stairs proven, walking mesh connected | from each door and in each room at eye height | re-plan |
| Placement and dressing | seated, reachable, nothing floating or blocking | how it reads where it stands | move it |
| In game | your check | your check | back to the stage at fault |

**Real geometry, never bounding boxes.** Placing, snapping, seating, fitting, stacking and dressing work from the
mesh's actual triangles and contact surfaces; a box is only a first filter for speed.

### The rule for references: no moving parts

Nothing a player would expect to move on its own goes into a reference or a model: a rope or string dangling from
a boat or a weapon, a loose cord, a tassel, a hanging feather, a flag in the wind. They would hang frozen while
the weapon swings or the boat rocks. A coil of rope lying in a boat, or a rope pulled taut along its side, is
fine: the player reads it as still.

### Doors: marked by hand

The building is generated with its door as part of the mesh. The agent marks the door by hand: it looks at the
building from the front, picks the door's corners and outline on the drawn view, and the tool lays the plate onto
the real surface there (a thin invisible door record a hair in front of the painted door, carrying the prompt,
with no animation). The agent then checks the plate from the side and in front of the furthest part of the
doorway. The automatic door finder of the hut example is dropped: it took three attempts and once put the door
on a stretch of wall.

### Long-weapon shafts

The head and shaft must read as made for each other: either one piece, or two pieces where the head plainly seats
into a socket or under a binding. What I recommend, to be tried side by side in the cost experiment:

- **Hybrid (recommended):** the head is generated with its own socket and a binding collar, as the glaive's
  already is. The shaft is made by hand in Blender to the donor's length and the socket's measured diameter, so
  it seats exactly, with its grip wrap (a raised helix of cord), carved rings, knots and a slight crook modelled
  as real geometry, and its wood taken from one generated swatch graded to the socket's colour. The small,
  characterful ends (a bone butt cap, a decorated grip band) are generated as separate short pieces, which
  generators do well, and seated by measurement. Cost: about the head alone plus a few cents.
- **Whole weapon generated** in one long reference: one consistent look, but a 1-to-10 shape gives the head
  little detail and long thin shafts are the generators' weak side.
- **Plain hand-made pole**, as in the glaive example: cheapest, exact fit, but plain.

### Generators for the shape, shared materials for the surface

Fal hosts Tripo, Hunyuan 3D, Trellis and others. They make solid objects seen from outside, at any size. For big
things the shape is generated and the surface redone with repeating materials so it stays sharp up close; for
small things the generator's own texture may be enough. You have not yet chosen between the three canoe surfaces
in the explorer (generator texture, shared material, shared material with the generator's shading); the cost
experiment adds a fourth question, whether a bare shape with our materials is good enough to save the texture fee.

### "Acts like an existing thing"

Copy an existing model file and record, replace only the visible shape, keep the rest. A pike, halberd, spear,
quarterstaff, whip, rapier or claw of ours copies the existing record of that type from Animated Armoury or our
other sources.

### One game: the hierarchy

| Level | Fixed once | Who approves |
|---|---|---|
| 0. The game | colour, brightness and sharpness ranges measured from the game's textures; pixels per metre; triangle limits; one lighting set-up; a size chart; a "never" list | you, on a line-up beside vanilla pieces |
| 1. Material | one library material per ladder and building material | you, once each |
| 2. Builder | each culture, story line and foreign builder: colours, materials, one sentence of shape, an emblem, a hero piece | you |
| 3. Family | one anchor taken into the game; every sibling made from it | you |
| 4. Object | purpose, size, the record it copies, its own feature | automatic checks; you see the family as a line-up |

Anything built also has a state (maintained, neglected, abandoned, ruined, drowned, reclaimed) and a location,
applied by record and by hand-dressing.

### Skills that learn

One map skill routing to a sub-skill per stage and per kind of thing, each a clean recipe; your feedback on any
model goes into skill-fixes the same day, and its lesson into the recipe once you verify the fix. The have-get-make
method is the first of them.

### The studio, for you as well as the agents

Every new placing action (grid snap, a piece palette, stairs between two floors, placing on a surface, against a
wall or hung from a beam, marking a door) is built once as a studio operation and offered twice: as a button or
tool in the studio for you, and as a look action for the agents. Your edits and theirs land in the same place
files.

## 4. Cost: getting the full amount inside about $90

### Where the $7.07 went

The three examples cost $7.07. About two thirds of it was Tripo P2, which I ran beside Tripo H3.1 on every object
at $1.10 to $1.20 a run; H3.1 won every time. Without P2 the same three would have cost about $2.30, about $0.75
a kept model. That is still too much for hundreds of models.

### The levers

| Lever | Saving |
|---|---|
| One generator per object, chosen by kind, not two | half |
| Cheaper reference images where the cheap ones are good enough (about $0.005 an image against about $0.07) | most of the image cost |
| A bare shape where our materials will surface it (Tripo H3.1 $0.20 bare against $0.30 to $0.40 textured; Hunyuan 2 mini $0.08 bare against $0.24 textured) | a third or more of the model cost |
| Cheaper generators for simple, solid things (Trellis about $0.02 a run on Fal) | most of the model cost, where quality holds |
| Fewer throw-aways: references with no moving parts; the agent looking before it generates | fewer retries |
| Hand work instead of generation where it is better and cheaper (shafts, kit pieces) | the whole fee for those parts |

**Tripo's own plans do not help us directly.** Tripo's help page and terms say Studio plan credits (Free, Pro,
Max) and API credits are separate and not interchangeable: a Max subscription pays for models made in Tripo's web
studio, not for the API that agents call. Using Max would mean agents driving the web studio in a browser, which
is fragile and which I have not checked against Tripo's terms. Tripo's API costs the same per model as Tripo on
Fal ($0.01 a credit). So the budget goes further on Fal, choosing the model by kind.

### The cost experiment (about $5)

The same three references as the examples (canoe, glaive head, hut) through six routes each, all on Fal:

| Route | Price a run |
|---|---|
| Trellis | about $0.02 |
| Trellis 2 | about $0.25 |
| Hunyuan 2 mini turbo, textured | $0.24 |
| Hunyuan 3.1 rapid | $0.225 |
| Idol max turbo | about $0.10 |
| Tripo H3.1, standard texture | $0.30 |

Plus the glaive as one whole weapon, and two reference images from a cheap image model beside the ones we have.
Every result is measured and looked at the same way as the examples, then put in the explorer side by side with
the H3.1 results we already have, for you to rank.

What it tells us: for each kind of thing (small solid prop, weapon head, building), the cheapest route whose
result you accept, and how often a first try is kept. Cost at scale is then the number of models of each kind
times (image cost + model cost) divided by the rate kept.

### What $90 buys, by route (to be replaced by the experiment's numbers)

| Cost per kept model | Models for $90 |
|---|---|
| $0.75 (H3.1 detailed, Nano Banana images, as the examples without P2) | about 120 |
| $0.35 (H3.1 bare or standard, cheap images, one try in three thrown away) | about 250 |
| $0.10 (a cheap generator for simple things, cheap images) | about 900 |

A likely mix, if the cheap routes hold up for small solid things: 300 to 500 models inside the budget. How many
we need is unknown until the index has cut the make list; my guess for "more" is 100 to 200.

## 5. The tracks

### A. Use what we hold (no art)

- The looked-at index, then every "have" wired in: grave-stakes into the dressing rules for burial grounds; the
  reed-roofed barge and the river boats at the boat stops; sap gear at Hist-tending places; cattails, lilies,
  fungus, saltrice and cypress knees into the planting tables; the native weapons checked against the gear tables.
- **Plant swaps are allowed** across the province and are not a terrain rebuild; the terrain is never redone. They
  are made with care: each region's distinctive ground cover stays, nothing is overhauled wholesale, and each swap
  must add variety, regional character or lore. BM&V's bamboo is never placed (it comes out an artificial
  turquoise).
- Composed things kept as recipes: the weir, a raft, a drying rack, a wreck.
- A bed record for the hammock. A swap table for Argonian places (lanterns, doors, tents, shrines of the Nine,
  banners). A different held interior for each house.
- Sources that contradict the lore corrected to better matches; a source may be shared.
- The holes in our own tables: three tribes pointed at armour we do not hold; 12 trade kits with no clothing row;
  the town guard's cuirass with no dropped model.
- The Ashgate Landing scatter: loose things placed by relation outdoors, with a check for things alone on open
  ground.

### B. Marks (flat images)

An emblem for each of the 18 cultures and nine story lines; the Company and Brethren flags; a Warden pennant. On
banner models that exist, as door signs, and later carved or painted on each builder's things.

### C. Things genuinely missing

Decided from the index, never from a name search. Confirmed so far: small craft (dugout, canoe, punt) and
root-grown buildings.

### D. Plants

The held variety first. Then reed, sedge and rice clump sets as hand-built cards with painted sway; a fern that
sways; a tall stilt-root mangrove; a signature planting per wet region. New trees are capped by the game: 87 of
256 distant-tree slots are free.

### E. The Black Marsh treatment and ruins

A second record of a model with its own projected material is how Skyrim does snow, ash and moss; King of the
Murkmire already has 176 mossy records with clean twins. Our mossy, silted and algae variants copy Dragonborn's
moss record. Then hand-dressing by state and location.

### F. Wearables, for all ten races

Body items need one set of models for all ten races; headgear needs three head models. First the held pieces
looked at on all ten races; then rigid head pieces, outfits reshaped from vanilla ones, plates on a cloth base,
tribal head parts, a bow.

### G. Buildings and interiors

**How Skyrim does it:** a closed exterior shell with its door and windows painted on; a door record in front of
the painted door; the interior a separate space. Doors as above: marked by hand, an invisible plate.

**Root-grown buildings: a family, not one hut.** The grown-root kit belongs to the interior: Helstrom (a city of
110 people), two hamlets and sixteen outposts of four to six people each, and the Middle Argonia and Helstrom
basin places of the same kit. One hut would repeat everywhere. The family I would make, each in two or three
variants, plus mossy and state twins by record and mirrored placement:

| Building | Where it is needed |
|---|---|
| A one-family hut (the example's size) | every outpost and hamlet |
| A larger family house, two rooms or with a loft | the hamlets, Helstrom's households |
| A long hall grown from several trees | an elders' or council hall, a guild or a hostel in Helstrom |
| A store or granary, raised on roots | every settlement's goods |
| A tree-minder's house beside the Hist | wherever a Hist is tended |
| A station shelter with a lookout | the sixteen outposts, most of which are stations or posts |
| Grown walkways and root stairs between them | Helstrom and the hamlets |

About 15 to 20 models in all, which fits the hand-made-from-a-generated-concept route.

**Stairs:** measured on 13 vanilla pieces, steps rise 14.5 to 24 units and floors sit 257 to 264 units apart in
small houses; one stair rule fits the held loft stairs. **Dressing rooms:** by relation, with eleven numeric
checks measured from 112 real interiors. **How our buildings enter a place draft:** the source is brought in
whole, and our buildings are swapped in at the adapting stage.

## 6. The options

- **Nothing.** The rule stays. Track A still stands as ordinary work.
- **Least.** Tracks A and B. Fal fees under $10. The province uses what it owns.
- **More (recommended).** Tracks A and B, the cost experiment (about $5), the workshop, one proof per kind of
  making, then each track funded after its proof, all inside about $90.
- **Most.** Kits and their skins, trees with distant views, wrecks, tribal head parts, a bow: chosen from once
  "more" has shown what the pipeline does well and what it costs, and only if the budget allows.

Not at any level for now: rooms straight from a generator; new animations; the ball court and the banyan.

## 7. Risks

- **Fal account:** it is out of credits; the experiment needs about $5 (check #95).
- **Unproven links,** each with a proof: collision the game walks on; worn models on Linux; sway from a plant
  model we write; the invisible door plate.
- **My searches** were wrong five times; the index and the method are the answer, and the make list stays
  provisional until the index has been searched.
- **Placement and rebuilds:** a model changes nothing until tables and drafts use it; a world rebuild runs only
  when you ask.
- **Labelling:** if the mod is ever published on Nexus it carries the AI-generated label, as the music already
  would. King of the Murkmire's author is asked again only then.
- **Where files live:** like the soundtrack, outside the repository, one row in the mod list, every request
  recorded.
- **The rule:** decision 0006 point 5 and the "Never make art" line in CLAUDE.md would be amended to say what is
  allowed and how: only what the index shows is missing, made by hand in the workshop under the style sheets,
  generators as helpers, inside the budget.

## 8. What I need from you

1. **Top up Fal by about $5** for the cost experiment (check #95).
2. **The option** on #94: nothing, least, more, or most. My recommendation is "more", inside the $90.
3. **A look at the explorer** when the experiment is in, to rank the routes by look, and to say which of the
   three canoe surfaces you prefer.

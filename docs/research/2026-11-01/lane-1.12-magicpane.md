# Lane 1.12-magicpane: our magic pane with Morrowind's six schools; Magic Expanded's tomes sold at Claywater

Owner, 2026-10-31: Magic Expanded wired into "our magic pane UI" with Morrowind's schools. Wind UI's magic window
cannot head a Mysticism group (its five school headings are fixed strings in its closed DLL, lane-1.12-magic.md), so
we stand our own PrismaUI view in for it, as the chart and the journal stand in for its map and journal. Route 1
(the world db) for the schools and the stock, then route 5 (our SKSE and our view).

## Built
- **Schema** `ui/schema/magic.ts`: `magic.state` v1 (powers; the six schools always, in Morrowind's order; active
  effects; a notice) and the one intent `magic.equip {spell, hand: left|right|voice}`; `ViewId` gains `magic`.
- **Rules** (skse/core `magic.h`, unit-tested in `test_magic.cpp`): `school_of` (the effect's mod_form school, so
  Mysticism for Mark, Recall, Dispel, Absorb, Soul Trap, Telekinesis, Reflect, Spell Absorption, Analyze, Teleport;
  else the Skyrim magic skill's school), `pane_state` (powers by name, then Alteration, Conjuration, Destruction,
  Illusion, Mysticism, Restoration, each by name, a spell known twice once; a spell with no school under Alteration,
  logged), `equip_refusal` (a power only to the voice slot, a spell only to a hand), `active_detail`, `stock_of`.
  `views::close_intent` closes the pane on Esc, Tab, B and P again (`quick_magic`); `pad::panes()` puts our magic
  pane third in the bumpers' cycle where Wind UI's magic window was.
- **View** `ui/views/magic/`: frame style; title bar names what each hand holds; the active effects; the list well
  with a Cost column. A spell's name readies it in the right hand (click, Enter, pad A), its "L" in the left; a power
  in the voice slot. `nav.ts`: a row's side control (`data-aside`) is outside the list walk, so down goes row to row.
- **ArgoniaCore** `magic.cpp`: `OpenMagic` reads the player's added, base and race spells (spells and powers only),
  the engine's magicka cost, the readied slots and the shown active effects; `MagicIntent` equips through
  `ActorEquipManager::EquipSpell` with the default left, right or voice equip slot. `views.cpp` registers the
  router's `magicMenu` surface (data/router/surfaces.json: now `view` by `magic`); `dialogue.cpp` routes the intent.
- **Opening (acceptance 2).** P opens MagicMenu, which Wind UI takes into its windows. The router's MenuOpenClose sink
  hides MagicMenu and pushes our pane. padcursor's sink then hides `WindUIMenu` every 50 ms for 1.5 s while our pane
  is the open modal: the kHide route that works for J's journal. Wind UI's per-window close and its taskbar setting
  were not needed. In the pad cycle the "magic" pane closes Wind UI's windows, then taps P; when our pane closes, the
  windows come back, as for the journal and map.
- **Stock (acceptance 3).** New table `trade_class_mod_stock` (world/schema.sql; rows by db.py): 13 Magic Expanded
  tomes for `trade-class.general` (Water Walking, Swift Swim; Bound Shield, Bound Mace; Viperbolt, Poison Spray;
  Blind, Command Creature; Mark, Recall, Weak Spelldrinker; Fortify Health, Cure Poison), each named as
  `<local id>:Magic.esp` from Magic.esp's BOOK records (read in place, nothing copied). `core_tables` renders
  `kModStock` per trader (npc_trade joined on trade class). At data load ArgoniaCore finds each trader's merchant
  chest through their vendor faction and adds the tome to its base container. Our plugin has no master on Magic.esp.
  The engine prices the tomes (their own values).

## Evidence
- L2: `ctest` 35/35 (core.magic: schools, order, equip, stock; core.views; core.pad; core.messages fixture round trip).
- L1/L3: node view tests 13/13; magic stills x 4 viewports (kit, fresh, many, refused, kit+focus): 0 fails, the
  smallest text 21.2 px at 720p and 40.8 px folded; the wiring (click R and L, pad down/A/right/A, power, Esc) sends
  exactly the fixture's intents. Read: kit@1080p, kit+focus@v5-folded (Mysticism: Absorb Health, Dispel, Mark,
  Recall (R), Spelldrinker), many@v5-unfolded.
- `make check`: CHECK GREEN.

## In game (L4, argonia-play-ie, job mp11, one deploy): magic-pane PASS 8/8, pad-panes PASS
`out/batch/adhoc/20261101T092610/01-magic-pane-1-20261101T092611`, `out/batch/adhoc/20261101T092610/02-pad-panes-1-20261101T092725`. Stills read:
- 03-pane: P opens our pane alone over play (no Wind UI window); its ViewState puts Absorb Health, Dispel, Mark and
  Recall under Mysticism (groups[4]); log "pad: Wind UI's windows hidden under our magic pane".
- 04-ready-right: Recall readied by `magic.equip` right; Views reads "magic right Recall". The title also reads
  "Left Recall": the engine fills both hand slots for Recall (a both-hands spell), and the pane shows the engine's state.
- 05-close: Esc ("ESC 150 engine") closes to play.
- 07-barter-tomes: Wind UI's barter window lists 13 spell tomes in Livia's stock; Views "magic stock 13/13".
- pad-panes 07-bumper-to-magic: the third bumper pane is our magic pane alone; B returns to Wind UI's windows; the
  cycle goes on to journal, map and System.
Fixes found on the way (one per run): a null actor-value name for an effect with no magic skill crashed the pane's
first open (mp3, `std::string_view(nullptr)`); MSVC's `GetObject` macro (mp1); the windows Wind UI pops as P opens
MagicMenu cancelled the pad's way back (mp7); a chest the base save had already filled never showed base-container
additions, so the stock is also topped up on the chest reference at each load (mp7 still: no tome), and the typed
`LookupForm<TESBoundObject>` refused the BOOKs (mp10: 0/13).
Not proven: the pad's d-pad and A inside the pane in game (the L3 wiring proves nav.ts's walk and A); the tomes'
names in the barter window (icons only at the still's zoom; the read counts them).

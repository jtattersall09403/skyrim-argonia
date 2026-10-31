# The design system: tokens and the UI map

The tokens for every screen the player meets. They live in `ui/views/core/theme.css`, and this file gives the reason
for each. A screen uses only these tokens. This is the paper cut made for our first screens (1.2). 1.12's designer
sets the whole system around Wind UI's retinted frames (the dark green-black panes of the owner's reference), keeps the
paper for the front door, the journal book, books and the chart, and adds the UI map of every screen here (decision
0017 §6).

**Reference.** The look follows Dear Diary – Paper SkyUI Menus (uranreactor; the paper theme over the vanilla menus,
1.2 §a), so our screens and the themed menus read as one: warm paper sheets, dark-brown ink, a soft mottle, a darker
rim, and no metal, stone or knotwork. Black Marsh's palette moves it off Skyrim: red-clay headings, marsh-teal links
and a moss accent. No Nordic ornament (0006).

## Type

- **Pelagiad everywhere** (OFL; `fonts/Pelagiad.ttf` sits beside the views and is copied at install from
  `$ARGONIA_PRIVATE/fonts/pelagiad`, never committed). The fallback is Palatino.
- **The scale follows the viewport.** `1rem = min(height / 34, width / 52)`, and `height / 26` on a screen 2:1 or
  wider, which is a phone held landscape (the fold closed is 2.24:1; desktops are 16:9 or 16:10). `core/scale.ts`
  sets it:

  | Viewport | 1rem | Physical |
  |---|---|---|
  | 1920×1080 | 31.8 px | above the 28 px 10-foot minimum |
  | 1280×720 | 21.2 px | |
  | Magic V5 folded, 2376×1060 at 404 ppi | 40.8 px | 2.56 mm |
  | Magic V5 unfolded, 2352×2172 at 403 ppi | 45.2 px | 2.85 mm |

  The 0.2 §d stream scale is not recorded, so the views are judged at 1:1.
- **No text is smaller than 1rem.** That is the readability bar: at least 2.5 mm em height on the phone. The
  reader's first round failed 1.96 mm. The harness measures the smallest drawn text in every still.
- **Sizes:** `--t-body` 1rem, `--t-head` 1.25rem, `--t-title` 1.6rem, `--t-banner` 2.6rem. The line height is 1.32.

## Colour

| Token | Value | Use |
|---|---|---|
| `--paper` / `-light` / `-dark` | #e6d9b8 / #f1e8cf / #cdbb8f | sheets, raised buttons, the mottle |
| `--paper-edge` | #9c8259 | the sheet's rim |
| `--ink` / `-soft` / `-faint` | #2a2015 / #54432c / #7d6a4c | text, secondary text and rules, disabled |
| `--rust` | #7b2f1d | headings, dates, the disposition fill (red clay) |
| `--link` | #1d5263 | hyperlinked keywords and topics (Morrowind's blue, moved to marsh teal) |
| `--moss` | #4b5a2a | a finished quest, a boon, a gain |
| `--focus` | #b0702a | the focus ring (amber), seen on paper and over play |
| `--bar-*` | health #7e2a1e, stamina #42622c, magicka #34506e (slate), breath #3a7884, climb #b07a26 | HUD bars |
| `--bar-*-hi` | health #b65438, stamina #7d9450, magicka #6f8fae, breath #6cadb5, climb #d9a24e | a bar's lit tone at its leading edge |
| `--trail` | #dba66e | the trail's fallback; each bar's trail (`--tr` in hud.css) is a lighter, warmer step of its own fill |
| `--hud-plate`, `--hud-trim` / `-hi`, `--hud-text` / `-soft` | ink-black at 74%; #9c8259 / #d4b27a; #f1e8cf / #cdbb8f | the HUD's dark lacquer plates, bronze hairlines and words (the HUD page) |
| `--plate` | paper at 92% | a paper plaque over play (no longer used by the HUD, 1.11) |
| `--frame-ground` | #0e130d | the frame style's solid pane ground; Wind UI's art ramp starts here, and cleared knots take it |
| `--frame-bg` / `-well` | ground at 95% / #080b08 at 90% | a pane over play, an inset list well (the reference's green-black) |
| `--frame-trim` / `-hi` | #6f6a35 / #b5a862 | the gold-green filigree rule and its lit edge: Skyrim's grey rules and white edges map to these |
| `--frame-text` / `-soft` / `-head` | #d9cfa6 / #a39a74 / #e6dcb2 | warm body text, labels, titles on dark panes (Pelagiad) |
| `--frame-link`, `--frame-select` | #8fb7c0, teal at 16% | keywords on a dark pane; a selected row's wash |

## Space, edges and depth

- Spacing steps: `--s1` 0.25rem, `--s2` 0.5, `--s3` 0.75, `--s4` 1, `--s6` 1.5, `--s8` 2.
- `--edge` (0.12rem) is the one border weight. Corners are 0.15–0.2rem, close to square, the way paper is cut.
- A sheet has one drop shadow and an inset hairline frame, as Dear Diary's double rule does. The journal sits in a
  dark leather binding.

## Input

- Every control is a `<button>` at least one line tall: for touch, keyboard focus and Enter.
- `core/nav.ts` moves focus spatially for the arrows and the pad. A list walks in order.
- Focus is an amber ring with a light amber wash. It is hidden while the last input was touch.
- Escape and the pad's B are back (`view.close`, or closing the persuasion panel). Q/E, PageUp/PageDown and LB/RB
  are previous and next. On the chart, +/-, the wheel, pinch and the triggers zoom, and WASD, a drag and the right
  stick pan.
- Input glyphs: the prompt carries one glyph per device, and CSS shows the device last used. Until the installer
  extracts Skyrim's own button art (0017 §5), the glyphs are a keycap, a round pad button and a touch ring drawn in
  CSS.

## What the web view must support (for 1.2 §0)

Flexbox, CSS columns (the journal's two leaves), `min()` (with a JS fallback), canvas 2D with `source-in` (the chart
mask), inline SVG (the sneak eye and status marks), and `@font-face` from a relative file. There are no web
components, no fetch and no framework. If 1.2 §0 picks Scaleform, these tokens carry over and only the views change.

## The HUD (1.11)

Our HUD over play, rebuilt from the old project's (its 2.2 §b; the inventory is
`docs/research/2026-10-31/lane-1.11.md`) and from Dark Souls' restraint, in our own drawing. The view is
`views/hud`; its interface (`schema/hud.ts`) is unchanged.

**Layout.** One column top left: the bars, vastei directly under them, then the notices, newest last. Top right the
minimap with its compass rose (1.12), the effect stack beside it; top centre the sneak eye while sneaking; the place banner at 15% height; the prompt under the centre.
Nothing else at the centre, no compass, no marker. The column never grows past 44% of the width.

**Plates.** Every HUD word sits on dark lacquer (`--hud-plate`) with a bronze hairline and a soft shadow, the
words in paper-light. Paper plates read as a menu laid over play and were the owner's "parchment box"; dark plates
read over a bright marsh and a dark interior alike. The banner has no plate: the name over a soft dark band between
two bronze rules.

**Bars.** Health, stamina, magicka in that fixed order, told apart by colour and place (Dark Souls); breath and grip
come and go below them with their name.
- *Length* grows with the maximum: 0.1rem a point, at least 4rem, at most 40% of the width.
- *Frame*: a recessed black trough (near-black, a deep inner shadow, a faint lower lip), a bronze hairline, a black keyline; a
  bronze spine with a lozenge head binds the three on the left. Health 1.05rem tall, the others 0.8rem.
- *Fill*: the bar's hue at its root running to its lit tone (`--bar-*-hi`) at the leading edge, a top highlight, a bevel (a light top line, a shaded base) and a shadow cast on the track
  and a lower shade for depth, and a lit lip at the edge. A faint tick every 50 points.
- *Damage trail*: on a drop the fill falls at once and a lighter, warmer step of the bar's own colour, with a lit end, holds what was lost; 0.9 s after the
  last hit it falls to the fill over 0.5 s (main.ts; `remember` in render.ts). A second hit inside the hold keeps
  the trail at its first height, so a combo reads as one loss.
- *Regeneration*: while a bar rises a soft light runs along its fill toward the edge; it stops 0.7 s after the last
  rise.
- *Low health* (at or under a quarter): the health fill pulses brighter, its frame warms to red clay, and the
  screen's rim darkens to a red-clay vignette that breathes.

**Vastei.** Under the bars: our lozenge mark, the count in heading size, the word. A gain (`gained`) shows "+N" in
the stamina's lit tone, rising in; the frame warms and one glint runs along the plate (1.6 s, once). A loss shows at
once, as the count.

**Notices** are lacquer strips with a rule in the kind's colour (journal teal, discovery moss, warning clay),
rising in. **Effects** keep their stack top right, the medals dark with a moss or clay ring.

**Motion** stays under 2 s and never loops but for the regeneration light and the low-health pulse, which say a
state that persists.

**Not on our HUD**, with the reason in the inventory: the time readout, the equipped hands, the quick
belt, the crosshair, and the lock-on cue and target bar (TDM draws the lock-on reticle in the world; a target bar
needs a field the interface does not have, 2.7).

## Wind UI's frames (1.12 §3)

Wind UI's pane fill and text colour are fixed in its DLL (black, grey-white) and it is never modified; its four frame
pieces are drawn from shapes in `interface/inventory components/itemcard.swf` (panel9, knot) and
`interface/tweenmenu.swf` (the caps), and redrawn whenever those files change. `tools/ui_theme/windui.py` maps every
shape colour there through a luminance ramp (ground, trim, trim-hi) and clears the shapes that carry Nordic interlace
(itemcard #78, tweenmenu #48 #53 #55 #57) at install. Geometry and bounds stay, since Wind UI finds each piece by size.

## The UI map

| Screen | Drawn by | Style |
|---|---|---|
| Front door (main menu) | Dear Diary's menu, our title wallpaper (ui/title) | paper, lightly tweaked |
| Loading | Oblivion-like Loading Menu, retheme recipe | paper |
| Menu mode, inventory, stats, magic, favourites, container, barter, gift, crafting, the taskbar | Wind UI | frame style (retinted art over its black panes) |
| Map | our chart (ArgoniaCore mapMenu surface, PrismaUI) | paper chart in a frame |
| Journal | our journal view (PrismaUI) | paper book |
| Dialogue | our dialogue view (PrismaUI) | frame style |
| System pane (Esc), settings | Skyrim's Scaleform (Dear Diary), our System view where 1.12 lands it | frame style |
| HUD and minimap | our HUD view (ui/views/hud) | lacquer plates (`--hud-*`) |
| Message boxes | Skyrim's MessageBoxMenu, retheme recipe | frame style |
| Books and notes | Skyrim's Book Menu, Dear Diary paper | paper |
| The sitting (level up), perks | our System pane + perks lane | frame style |
| Notices | our HUD view | lacquer strips |
| Lockpicking | Skyrim's Lockpicking Menu, retheme recipe | frame style |
| Sleep / wait | Skyrim's Sleep/Wait Menu (Dear Diary), retheme recipe | frame style |

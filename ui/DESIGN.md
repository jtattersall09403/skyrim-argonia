# The paper theme: tokens, first cut (1.2)

Stage one's look for our four screens (dialogue, journal, HUD, chart). The full design system, with the mood boards
and the owner's rounds, is 2.2 (decision 0017 §2). The tokens live in `ui/views/core/theme.css`, and this file gives
the reason for each. A screen uses only these tokens.

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
| `--bar-*` | health #9a2f22, stamina #3f6e2c, magicka #2f4f96, breath #3a7884, climb #b07a26 | HUD bars |
| `--trough` | ink at 82% | a bar's empty part |
| `--plate` | paper at 92% | the plaque behind every HUD word, so it reads over a bright frame |

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

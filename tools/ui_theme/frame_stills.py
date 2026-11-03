"""L3 stills of the pages our System pane hands over (Settings, Load, the Mod configuration pages, a message box,
lockpicking) in the frame style: the recoloured art from the retheme overlay with sample text in the frame tokens.
A static mock of the layout; output stays in out/ (derived from mod files, never committed).

    python -m tools.ui_theme.frame_stills <theme-overlay> out/ui_theme/stills-frame
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from tools.ui_theme import swf
from collections import Counter
from tools.ui_theme.palette import tokens
from tools.ui_theme.retheme import DEFINE_EDIT_TEXT, DO_INIT_ACTION, edit_text_colour, script_text_colours
th, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
t = tokens(); txt, soft, head, trim = t['frame-text'], t['frame-text-soft'], t['frame-head'], t['frame-trim-hi']
F = lambda n: ImageFont.truetype(str(Path(os.environ.get('ARGONIA_PRIVATE', Path.home() / 'argonia-private')) / 'fonts/pelagiad/Pelagiad.ttf'), n)
def field_colour(rel):
    """The commonest text field colour in the recoloured movie: the text as the game draws it."""
    m = swf.read((th / rel).read_bytes())
    c = Counter(tuple(t.data[o:o + 3]) for t in m.tags if t.code == DEFINE_EDIT_TEXT and (o := edit_text_colour(t.data)) is not None)
    return c.most_common(1)[0][0]
JT, CT, MT, LT = (field_colour(f"interface/{n}.swf") for n in ("quest_journal", "skyui/configpanel", "messagebox", "lockpickingmenu"))
def row_colours(rel):
    """The list rows' run-time colours (the SetEntryText textColor pushes), plain and highlighted, as the game sets them."""
    m = swf.read((th / rel).read_bytes())
    vs = sorted({v for t in m.tags if t.code == DO_INIT_ACTION for _o, v in script_text_colours(t.data, 2)})
    return [((v >> 16) & 255, (v >> 8) & 255, v & 255) for v in vs]
JR = row_colours("interface/quest_journal.swf")
JT, JH = JR[0], JR[-1]
def bg(rel):
    return Image.fromarray(swf.bitmaps(swf.read((th / rel).read_bytes()))[0][1].rgba, 'RGBA')
def page(name, rel, at, lines, scale=1.0):
    can = Image.new('RGB', (1920, 1080), (52, 64, 46))  # a stand-in for play behind the menu
    im = bg(rel); im = im.resize((int(im.width * scale), int(im.height * scale)))
    can.paste(im, at, im); d = ImageDraw.Draw(can)
    for (x, y, s, size, col) in lines: d.text((at[0] + x, at[1] + y), s, font=F(size), fill=col)
    can.save(out / f'{name}.png')
QJ = 'interface/deardiary/quest_journal/quest_journal_bg.swf'
cats = [(30, 150 + 40 * i, s, 26, JH if i == 0 else JT) for i, s in enumerate(['Settings', 'Load', 'Gameplay', 'Display', 'Audio', 'Mod configuration'])]
page('settings', QJ, (260, 180), cats[2:] + [(330, 150, 'Difficulty', 26, JT), (700, 150, 'Adept', 26, trim), (330, 200, 'Show floating markers', 26, JT), (700, 200, 'On', 26, trim), (330, 250, 'Save on rest', 26, soft), (700, 250, 'Off', 26, soft)])
page('load', QJ, (260, 180), [(330, 150 + 45 * i, s, 26, head if i == 0 else JT) for i, s in enumerate(['Save 12  Lukiul, Stormhold, 9 Rain\'s Hand', 'Save 11  Lukiul, Gideon', 'Save 10  Lukiul, the Hist grove'])] + [(30, 150, 'Load', 26, head)])
page('mcm', 'interface/deardiary/configpanel/configpanel_bg.swf', (310, 170), [(40, 100 + 40 * i, s, 26, head if i == 0 else CT) for i, s in enumerate(['ArgoniaCore', 'Wind UI', 'Dear Diary'])] + [(290, 110, 'Pad cursor speed', 26, CT), (650, 110, '1.0', 26, trim), (290, 160, 'Hold to sprint', 26, CT), (650, 160, 'On', 26, trim)])
page('messagebox', 'interface/deardiary/messagebox/messagebox_bg.swf', (696, 333), [(60, 110, 'The door is barred from', 28, MT), (60, 150, 'the other side.', 28, MT), (220, 320, 'Ok', 30, MT)])
page('lockpicking', 'interface/deardiary/lockpickingmenu/lockpickingmenu_bg.swf', (287, 900), [(260, 50, 'Lock level: Adept', 28, LT), (620, 50, 'Lockpicks: 12', 28, LT), (960, 50, 'Skill: 25', 28, soft)])

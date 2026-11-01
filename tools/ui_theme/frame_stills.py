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
from tools.ui_theme.palette import tokens
th, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
t = tokens(); txt, soft, head, trim = t['frame-text'], t['frame-text-soft'], t['frame-head'], t['frame-trim-hi']
F = lambda n: ImageFont.truetype(str(Path(os.environ.get('ARGONIA_PRIVATE', Path.home() / 'argonia-private')) / 'fonts/pelagiad/Pelagiad.ttf'), n)
def bg(rel):
    return Image.fromarray(swf.bitmaps(swf.read((th / rel).read_bytes()))[0][1].rgba, 'RGBA')
def page(name, rel, at, lines, scale=1.0):
    can = Image.new('RGB', (1920, 1080), (52, 64, 46))  # a stand-in for play behind the menu
    im = bg(rel); im = im.resize((int(im.width * scale), int(im.height * scale)))
    can.paste(im, at, im); d = ImageDraw.Draw(can)
    for (x, y, s, size, col) in lines: d.text((at[0] + x, at[1] + y), s, font=F(size), fill=col)
    can.save(out / f'{name}.png')
QJ = 'interface/deardiary/quest_journal/quest_journal_bg.swf'
cats = [(30, 150 + 40 * i, s, 26, head if i == 0 else txt) for i, s in enumerate(['Settings', 'Load', 'Gameplay', 'Display', 'Audio', 'Mod configuration'])]
page('settings', QJ, (260, 180), cats[2:] + [(330, 150, 'Difficulty', 26, txt), (700, 150, 'Adept', 26, trim), (330, 200, 'Show floating markers', 26, txt), (700, 200, 'On', 26, trim), (330, 250, 'Save on rest', 26, soft), (700, 250, 'Off', 26, soft)])
page('load', QJ, (260, 180), [(330, 150 + 45 * i, s, 26, head if i == 0 else txt) for i, s in enumerate(['Save 12  Lukiul, Stormhold, 9 Rain\'s Hand', 'Save 11  Lukiul, Gideon', 'Save 10  Lukiul, the Hist grove'])] + [(30, 150, 'Load', 26, head)])
page('mcm', 'interface/deardiary/configpanel/configpanel_bg.swf', (310, 170), [(40, 100 + 40 * i, s, 26, head if i == 0 else txt) for i, s in enumerate(['ArgoniaCore', 'Wind UI', 'Dear Diary'])] + [(290, 110, 'Pad cursor speed', 26, txt), (650, 110, '1.0', 26, trim), (290, 160, 'Hold to sprint', 26, txt), (650, 160, 'On', 26, trim)])
page('messagebox', 'interface/deardiary/messagebox/messagebox_bg.swf', (696, 333), [(60, 110, 'The door is barred from', 28, txt), (60, 150, 'the other side.', 28, txt), (220, 320, 'Ok', 30, head)])
page('lockpicking', 'interface/deardiary/lockpickingmenu/lockpickingmenu_bg.swf', (287, 900), [(80, 55, 'Lock level: Adept', 28, txt), (560, 55, 'Lockpicks: 12', 28, txt), (1000, 55, 'Skill: 25', 28, soft)])

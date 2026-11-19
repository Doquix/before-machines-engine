"""E018 thumbnail: Yisungge at full draw on the gallop, the record distance as the headline.
1080x1920 for Shorts, plus a 1280x720 crop for the channel page."""
import math, sys
from PIL import Image, ImageDraw
sys.argv = ['x', 'T']
import render_mb as R
from lib import *
from rig import *
from mb import mongol_archer
from props import mongol_arrow, stele
from fx import speed_lines, particles
CAM.drift = 0; CAM.extra = None; CAM.set(0)
im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
lay = new_layer(); pn = Pen(lay, cam=False)
R.GY = 1400
R.steppe(im, pn, 0.0, 300.0)
# the stone that records the shot
stele(pn, 900, 1420, 1.05)
# Yisungge on foot at full draw, aimed high for distance (the stone does not say he was mounted)
mongol_archer(pn, 330, 1480, 2.25, 1, 1.0, 'yisungge', 'determined', aim=0.32, look=(1.0, -0.35))
pn.push(700, 860, 1.8); mongol_arrow(pn, (0, 0), -0.32); pn.pop()
speed_lines(pn, 700, 860, math.cos(-0.32), math.sin(-0.32), 0.2, length=150, n=7, spread=26, seed=4, alpha=220)
flatten(im, lay)
d = ImageDraw.Draw(im)
def big(txt, y, size, col, x=540):
    f = F('Black', size, True)
    d.text((x, y), txt, font=f, fill=col, anchor='mm', stroke_width=max(6, size // 11), stroke_fill=(16, 12, 10))
big('536 M', 400, 290, AMBER)
big('ONE ARROW', 620, 130, WHITE)
im = im.convert('RGB')
im.save('/home/claude/out/E018_thumbnail_vertical.png')
h = Image.new('RGB', (1280, 720))
h.paste(im.crop((0, 700, 1080, 1308)).resize((1280, 720)))
d2 = ImageDraw.Draw(h)
d2.text((880, 110), '536 M', font=F('Black', 150, True), fill=AMBER, anchor='mm', stroke_width=11, stroke_fill=(16, 12, 10))
d2.text((880, 225), 'ONE ARROW', font=F('Black', 70, True), fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(16, 12, 10))
h.save('/home/claude/out/E018_thumbnail_16x9.png')
print('ok')

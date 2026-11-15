"""E015 thumbnail, 1080x1920, drawn with the engine: the corvus biting into a Carthaginian deck."""
import math
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import cv, env, fx
from cv import galley, CV_FT
from render_cv import sword_held

t = 0.37
CAM.drift = 0; CAM.set(0); CAM.s, CAM.ox, CAM.oy = 1.0, 0, 0
base = env.get('seaday').copy().convert('RGBA')
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([260, 1000, 900, 1560], fill=(255, 226, 170, 110)); glow = glow.filter(ImageFilter.GaussianBlur(110))
base.alpha_composite(glow)
lay = new_layer(); pn = Pen(lay, cam=False)
WL, K = 1520, 1.8
RX = 300 - 440 * K; EX = RX + 1000 * K
C = galley(pn, EX, WL, K, t, -1, hull=cv.PUN_HULL, stripe=cv.PUN_STRIPE, oar_rate=0.3, row=0.3)
R = galley(pn, RX, WL, K, t, 1, oar_rate=0.3, row=0.3, corvus_ang=5.0, corvus_kw=dict(rope_slack=1.0))
cvp = R['cv']; tip = cvp['tip']; piv = cvp['piv']
deck = R['bow'][1]
# the Keeper braced behind the corvus, a Carthaginian recoiling on his own deck
figure(pn, 120, deck, 1.25, 1, pose('brace'), 'legion', 'determined', look=(1.0, 0.0), held=lambda pn_, J: sword_held(pn_, J))
figure(pn, 960, C['bow'][1], 1.2, -1, 'cower', 'punic2', 'terrified', look=(-0.8, -0.2))
import gf; gf.water(pn, WL - 2, t, col=(52, 92, 116), light=(130, 170, 190), x0=-900, x1=2200)
sx, sy = cvp['spike']
fx.particles(pn, 'chips', sx, sy - 6, 0.14, 0.0, 0.9, seed=91, ang=-math.pi * 0.3, cone=math.pi * 0.5)
fx.particles(pn, 'sparks', sx, sy - 6, 0.08, 0.0, 1.0, seed=95, cone=math.pi * 1.2)
fx.impact(pn, sx, sy - 6, 0.09, 0.0, 0.85, seed=94, lines=False)
flatten(base, lay)
im = base.convert('RGB')
grad = Image.new('L', (W, H), 0); gdr = ImageDraw.Draw(grad)
for y in range(H):
    a = max(0, 1 - y / 820) * 190 + max(0, (y - 1640) / 280) * 170
    gdr.line([(0, y), (W, y)], fill=int(min(255, a)))
im.paste(Image.new('RGB', (W, H), (10, 8, 12)), (0, 0), grad)
d = ImageDraw.Draw(im)
def txt(y, s, size, col, stroke=14):
    f = F('Black', size, True)
    while f.getlength(s) > 980: size -= 4; f = F('Black', size, True)
    d.text((W / 2 + 8, y + 10), s, font=f, fill=(0, 0, 0), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0))
    d.text((W / 2, y), s, font=f, fill=col, anchor='mm', stroke_width=stroke, stroke_fill=(16, 12, 10))
txt(300, "ROME COULDN'T", 112, (255, 255, 255), 12)
txt(430, 'FIGHT AT SEA', 112, (255, 255, 255), 12)
txt(620, 'SO IT BUILT THIS', 150, AMBER, 16)
# arrow from the title down to the bridge
lay2 = new_layer(); p2 = Pen(lay2, cam=False)
import props
mid = cvp['mid']
tgt = (mid[0] + 30, mid[1] - 40)
a0 = (930, 720)
gap = 130      # clear space between the arrowhead and the bridge
dl = math.hypot(tgt[0] - a0[0], tgt[1] - a0[1])
a1 = (tgt[0] - (tgt[0] - a0[0]) / dl * gap, tgt[1] - (tgt[1] - a0[1]) / dl * gap)
props.swoosh_arrow(p2, a0, a1, bend=-0.28, w_tail=6, w_body=46, head=2.5)
imr = im.convert('RGBA'); flatten(imr, lay2); im = imr.convert('RGB')
im.save('/home/claude/out/BM_E015_corvus_thumbnail.png')
im.resize((360, 640)).save('thumb_small.png')

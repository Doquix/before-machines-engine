"""E014 thumbnail, 1080x1920, drawn with the engine."""
import math
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
from gf import *
import env

t = 0.37
CAM.drift = 0; CAM.set(0); CAM.s, CAM.ox, CAM.oy = 1.0, 0, 0
base = env.get('nightsea').copy().convert('RGBA')
# warm glow behind the fire
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([380, 900, 1300, 1700], fill=(255, 120, 40, 120)); glow = glow.filter(ImageFilter.GaussianBlur(120))
base.alpha_composite(glow)
lay = new_layer(); pn = Pen(lay, cam=False)
WL = 1470
galley_small(pn, 1010, WL - 6, 0.75, t, -1, seed=3)
for i, dx in enumerate((-170, -60, 50, 160)):
    fire_patch(pn, 1010 + dx, WL - 70, 1.0, t, 20 + i, 1.0, water=False)
K = dromon(pn, -660, WL, 2.0, t, 1, oar_rate=1.0)
nx, ny = K['nozzle']
jet(pn, nx, ny, math.radians(3), 900, 1.0, t, 2.1, grav=0.00040)
pn.circ(nx + 20, ny, 46, fill=F_IN + (220,))
for i, x in enumerate((640, 790, 930, 1070)):
    fire_patch(pn, x, WL + 16, 1.25 + 0.1 * i, t, i + 1, 1.0)
water(pn, WL, t)
for i, x in enumerate((640, 790, 930, 1070)):
    flame(pn, x, WL + 20, 90, t, 9 + i, 0.8)
dx_, dy_ = K['deck']
figure(pn, dx_ - 40, dy_, 1.45, 1, pose('point', uaF=100, faF=104), EPISODE_OUTFIT, 'surprised', look=(1.0, 0.1))
flatten(base, lay)
# darken the top for the title and the bottom for the platform UI
im = base.convert('RGB')
grad = Image.new('L', (W, H), 0); gdr = ImageDraw.Draw(grad)
for y in range(H):
    a = max(0, 1 - y / 760) * 200 + max(0, (y - 1600) / 320) * 160
    gdr.line([(0, y), (W, y)], fill=int(min(255, a)))
im.paste(Image.new('RGB', (W, H), (10, 8, 12)), (0, 0), grad)
# title
d = ImageDraw.Draw(im)
def txt(y, s, size, col, stroke=14):
    f = F('Black', size, True)
    while f.getlength(s) > 980: size -= 4; f = F('Black', size, True)
    d.text((W / 2 + 8, y + 10), s, font=f, fill=(0, 0, 0), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0))
    d.text((W / 2, y), s, font=f, fill=col, anchor='mm', stroke_width=stroke, stroke_fill=(16, 12, 10))
txt(330, 'GREEK FIRE', 196, AMBER, 16)
txt(520, "IT WASN'T", 120, (255, 255, 255), 12)
txt(660, 'THE RECIPE', 120, (255, 255, 255), 12)
im.save('/home/claude/out/BM_E014_greek_fire_thumbnail.png')
im.resize((360, 640)).save('thumb_small.png')

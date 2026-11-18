"""E017 thumbnail: the reach gap. 1080x1920 for Shorts, plus a 1280x720 crop for the channel page."""
import math
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import sp, env
from sp import phalangite, hoplite, dry_ground
from fx import impact, particles

CAM.drift = 0; CAM.set(0)
G = 1480
im = env.get('plain').convert('RGBA')
lay = new_layer(); pn = Pen(lay, cam=False)
dry_ground(pn, G - 40, 0.0)
# the Greek hoplite on the right: his 8 ft spear falls short
Rh = hoplite(pn, 975, G + 40, 1.6, -1, 0.0, 'hoplite', 'terrified', look=(-0.9, 0.1), ang=0.08, thrust=1.0,
             p=pose('brace', uaF=60, faF=96, torso=6))
# the phalangite: sarissa level, point on the hoplite's shield
Rk = phalangite(pn, 105, G + 40, 1.6, 1, 0.0, 0.0, 'phalanx', 'smug', look=(1.0, 0.0), back=240)
impact(pn, Rk['tip'][0] - 6, Rk['tip'][1], 0.06, 0.0, 0.45, seed=3)
particles(pn, 'sparks', Rk['tip'][0] - 6, Rk['tip'][1], 0.12, 0.0, 1.0, seed=5)
# the gap the short spear cannot close
tx, ty = Rh['tip']; body = 105 + 52 * 1.6
for i in range(int((tx - body - 30) / 30)):
    x0 = tx - 30 - i * 30
    pn.line([(x0, ty), (x0 - 16, ty)], RUST, 8)
for a, b in (((-28, -28), (28, 28)), ((-28, 28), (28, -28))):
    pn.line([(tx - 70 + a[0], ty - 70 + a[1]), (tx - 70 + b[0], ty - 70 + b[1])], INK, 20)
    pn.line([(tx - 70 + a[0], ty - 70 + a[1]), (tx - 70 + b[0], ty - 70 + b[1])], RUST, 12)
flatten(im, lay)

# headline: large, top third, clear of the Shorts interface at the bottom and right
d = ImageDraw.Draw(im)
def big(txt, y, size, col):
    f = F('Black', size, True)
    d.text((540, y), txt, font=f, fill=col, anchor='mm', stroke_width=max(6, size // 11), stroke_fill=(16, 12, 10))
big('18 FT', 420, 300, AMBER)
big('BEATS 8 FT', 650, 130, WHITE)
im = im.convert('RGB')
im.save('/home/claude/out/E017_thumbnail_vertical.png')
# 16:9 version for the channel page
h = Image.new('RGB', (1280, 720))
crop = im.crop((0, 880, 1080, 1488)).resize((1280, 720))
h.paste(crop)
d2 = ImageDraw.Draw(h)
f = F('Black', 120, True)
d2.text((640, 95), '18 FT vs 8 FT', font=f, fill=AMBER, anchor='mm', stroke_width=12, stroke_fill=(16, 12, 10))
h.save('/home/claude/out/E017_thumbnail_16x9.png')
print('ok')

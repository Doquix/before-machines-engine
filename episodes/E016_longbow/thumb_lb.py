"""E016 thumbnail, 1080x1920, drawn with the engine: the Keeper straining at full draw of an English war bow."""
import math
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import lb, env, fx, props
from render_lb import archer, grass_ground

t = 1.7
CAM.drift = 0; CAM.set(0); CAM.s, CAM.ox, CAM.oy = 1.0, 0, 0
base = env.get('green').copy().convert('RGBA')
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([180, 900, 1000, 1700], fill=(255, 226, 170, 120)); glow = glow.filter(ImageFilter.GaussianBlur(120))
base.alpha_composite(glow)
lay = new_layer(); pn = Pen(lay, cam=False)
grass_ground(pn, 1560, t)
lb.butt(pn, 960, 1600, 0.6)
KX, KY, KK = 380, 2010, 3.35
A = archer(pn, KX, KY, KK, 1, 1.0, t, expr='pain', look=(1.0, 0.0), tremble=0.0, blink=0.0)
# strain: shake marks beside the bow hand and the string hand
for (x, y) in (A['grip'], A['nock']):
    for i in range(3):
        a = -0.6 + i * 0.6
        pn.line([(x + 40 * math.cos(a) + 26, y + 40 * math.sin(a)), (x + 68 * math.cos(a) + 26, y + 68 * math.sin(a))], INK, 6)
flatten(base, lay)
im = base.convert('RGB')
grad = Image.new('L', (W, H), 0); gdr = ImageDraw.Draw(grad)
for y in range(H):
    a = max(0, 1 - y / 900) * 200 + max(0, (y - 1700) / 220) * 150
    gdr.line([(0, y), (W, y)], fill=int(min(255, a)))
im.paste(Image.new('RGB', (W, H), (10, 8, 12)), (0, 0), grad)
d = ImageDraw.Draw(im)
def txt(y, s, size, col, stroke=14):
    f = F('Black', size, True)
    while f.getlength(s) > 980: size -= 4; f = F('Black', size, True)
    d.text((W / 2 + 8, y + 10), s, font=f, fill=(0, 0, 0), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0))
    d.text((W / 2, y), s, font=f, fill=col, anchor='mm', stroke_width=stroke, stroke_fill=(16, 12, 10))
txt(270, 'THIS BOW TOOK', 116, (255, 255, 255), 12)
txt(480, '150 LB', 270, AMBER, 20)
txt(680, 'TO PULL', 116, (255, 255, 255), 12)
lay2 = new_layer(); p2 = Pen(lay2, cam=False)
top = (A['grip'][0] - 30, A['grip'][1] - 360)
props.swoosh_arrow(p2, (900, 760), (top[0] + 70, top[1] - 40), bend=0.3, w_tail=6, w_body=46, head=2.5)
imr = im.convert('RGBA'); flatten(imr, lay2); im = imr.convert('RGB')
im.save('/home/claude/out/BM_E016_longbow_thumbnail.png')
im.resize((360, 640)).save('thumb_small.png')
print(A['grip'], A['nock'])

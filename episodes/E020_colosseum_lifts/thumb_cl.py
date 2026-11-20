"""E020 thumbnail: its own composition (original art only). A big tiger erupting from the trap door, the hunter
terrified in the foreground, a cutaway of the lift below, big hook text on a dark band."""
import math
from PIL import Image, ImageDraw, ImageFont
import render_cl as R
from render_cl import *
import scenes_cl as SC
import cl
FD_ = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'

def scene(base, pn, t):
    SC.bgp(base, 'arena', 0.0)
    SC.sand_grain(pn, 1080)
    H_ = dict(cx=640, y0=1180, y1=1290, w0=330, w1=400)
    SC.hole_and_door(pn, 1.0, H_=H_)
    SC.clipped(pn, H_['y1'] - 6, lambda p2: cl.tiger(p2, 660, 1430, 2.25, 1, gait='leap', ph=0.2, body_tilt=-1.0, expr='roar', t=0.4,
                                                     look=(-0.8, 0.2)))
    SC.speed_lines(pn, 660, 900, 0, -1, 0.1, length=200, n=6, spread=420, seed=3)
    cl.venator(pn, 230, 1720, 2.4, 1, 0.3, ang=0.1, expr='terrified', look=(0.9, -0.5))

def make(out):
    CAM.extra = None; CAM.drift = 0; CAM.set(0.0)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255)); lay = new_layer(); pn = Pen(lay, cam=False)
    scene(base, pn, 0.0); flatten(base, lay)
    d = ImageDraw.Draw(base)
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(0, 700):
        gd.line([(0, y), (W, y)], fill=(20, 12, 8, int(215 * (1 - y / 700) ** 1.3)))
    base.alpha_composite(g); d = ImageDraw.Draw(base)
    def txt(y, s, size, col, stroke=14):
        f = ImageFont.truetype(FD_, size)
        while d.textlength(s, font=f) > W - 90: size -= 4; f = ImageFont.truetype(FD_, size)
        d.text((W / 2, y), s, font=f, fill=col, anchor='mm', stroke_width=stroke, stroke_fill=(20, 12, 8))
    txt(230, 'ROMAN', 200, (255, 255, 255))
    txt(430, 'ELEVATORS', 200, (250, 186, 40))
    txt(600, 'THE COLOSSEUM REALLY HAD THEM', 66, (255, 255, 255), 9)
    base.convert('RGB').save(out, quality=95)

make('/home/claude/out/E020_thumbnail.png')

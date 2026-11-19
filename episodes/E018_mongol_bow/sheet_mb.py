"""E018 check sheets: Mongol archer drawing with the thumb, mounted archer at the gallop, outfits, props at three sizes."""
import math, sys
from PIL import Image
from lib import *
from rig import *
import mb, env, props as PR
CAM.drift = 0; CAM.set(0)

def sheet1():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    pn.text(540, 70, 'E018 POSE SHEET', 44, INK, 'Black')
    for i, d_ in enumerate((0.0, 0.5, 1.0)):
        mb.mongol_archer(pn, 170 + i * 330, 600, 1.2, 1, d_, expr=('neutral', 'determined', 'determined')[i])
        pn.text(170 + i * 330, 660, f'draw {d_}', 30, INK, 'Black')
    # mounted, three gallop phases
    for i, ph in enumerate((0.0, 0.33, 0.66)):
        pass
    mb.mounted_archer(pn, 330, 1230, 1.05, 1, ph=0.1, gallop=1.0, draw=1.0, out='yisungge')
    pn.text(330, 1290, 'gallop, full draw', 30, INK, 'Black')
    mb.mounted_archer(pn, 820, 1230, 0.8, -1, ph=0.55, gallop=1.0, draw=0.0, out='mongol3', expr='neutral')
    pn.text(820, 1290, 'gallop, braced', 30, INK, 'Black')
    # outfits: yisungge standing with the unstrung bow, warrior walking, keeper idle
    def unstrung(pn_, J):
        g = J['haF']; PR.mongol_bow(pn_, g[0], g[1], 1, -1.0)
    def m(pn_, J):
        PR.combat_quiver(pn_, J, 1); PR.bow_case(pn_, J, 1)
    figure(pn, 170, 1800, 1.15, 1, 'idle', 'yisungge', 'proud', hands={'F': (62, -120)}, held=unstrung, mid=m, blink=0)
    pn.text(170, 1860, 'unstrung', 30, INK, 'Black')
    figure(pn, 480, 1800, 1.15, 1, 'walk', 'mongol3', 'determined', mid=m, blink=0)
    figure(pn, 780, 1800, 1.15, -1, 'point', 'mkeeper', 'happy', blink=0)
    figure(pn, 980, 1800, 0.8, -1, 'idle', 'mkeeper', 'thinking', blink=0)
    flatten(im, lay); return im.convert('RGB')

def sheet2():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    pn.text(540, 70, 'E018 PERIOD PROPS', 44, INK, 'Black')
    # bow states, full screen size
    for i, (st, lab) in enumerate(((-1.0, 'UNSTRUNG'), (0.0, 'BRACED'), (1.0, 'FULL DRAW'))):
        x = 190 + i * 330
        pn.push(x, 420, 1.9)
        hand = (-108, 0) if st >= 1 else None
        PR.mongol_bow(pn, 0, 0, 1, st, string_to=hand)
        if hand: PR.mongol_arrow(pn, hand, 0.0)
        pn.pop()
        pn.text(x, 650, lab, 30, INK, 'Black')
    # small sizes
    for i, k in enumerate((0.45, 0.8)):
        pn.push(90 + i * 110, 900, k); PR.mongol_bow(pn, 0, 0, 1, 0.0); pn.pop()
    # cutaway
    PR.mongol_bow(pn, 470, 900, 1, 0.0, cut=True)
    PR.limb_layers(pn, 800, 900, 340, 60, bend=0.0)
    PR.limb_layers(pn, 800, 1080, 340, 60, bend=0.8, arrows=1.0)
    # arrows and thumb ring
    PR.mongol_arrow(pn, (60, 1250), 0.0)
    PR.mongol_arrow(pn, (60, 1310), 0.0, head='forked')
    pn.push(420, 1280, 3.0); PR.thumb_ring(pn, 0, 0, r=6); pn.pop()
    # quiver and bow case on a mannequin, large
    def m(pn_, J):
        PR.combat_quiver(pn_, J, 1); PR.bow_case(pn_, J, 1)
    figure(pn, 640, 1840, 1.8, 1, 'idle', 'mongol3', 'neutral', mid=m, blink=0)
    # stele and horse
    PR.stele(pn, 920, 1840, 1.1)
    pn.text(920, 1880, 'STELE (SCRIPT SIMPLIFIED)', 22, INK, 'Black')
    PR.horse(pn, 230, 1840, 0.95, 1, 0.0, gallop=0.0)
    flatten(im, lay); return im.convert('RGB')

a = sheet1(); b = sheet2()
o = Image.new('RGB', (2160, 1920)); o.paste(a, (0, 0)); o.paste(b, (1080, 0))
o.save('e018_period_props.png'); print('ok')

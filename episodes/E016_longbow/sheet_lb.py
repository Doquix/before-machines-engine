"""E016 check sheets: archer holding and drawing the longbow, outfits, props at three sizes."""
import math
from PIL import Image
from lib import *
from rig import *
import lb, env
CAM.drift = 0; CAM.set(0)

def bow_figure(pn, x, y, k, f, draw, out='archer', expr='determined', arrow_on=True, pz='idle'):
    p = pose(pz)
    J0 = joints(p, f, 1.0)
    hands = lb.archer_hands(f, draw, J0['neck'])
    def held(pn_, J):
        g = J['haF']; s = J['haB']
        B = lb.longbow(pn_, g[0], g[1], f, draw, string_to=s)
        if arrow_on:
            ang = math.atan2(g[1] - s[1], g[0] - s[0])
            lb.arrow(pn_, s, ang)
    return figure(pn, x, y, k, f, p, out, expr, hands=hands, held=held, blink=0)

def sheet1():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    for i, d_ in enumerate((0.0, 0.5, 1.0)):
        bow_figure(pn, 190 + i * 340, 820, 1.25, 1, d_, expr=('neutral', 'determined', 'pain')[i])
        pn.text(190 + i * 340, 880, f'draw {d_}', 30, INK, 'Black')
    bow_figure(pn, 190, 1600, 1.25, -1, 1.0, out='archer2', expr='angry')
    # holding the bow upright, unstrung check: hand on the grip, lower tip on the floor
    def upright(pn_, J):
        g = J['haF']; lb.longbow(pn_, g[0], g[1] - 0, 1, 0.0)
    figure(pn, 520, 1600, 1.25, 1, 'idle', 'archer3', 'happy', hands={'F': (60, -150)}, held=upright, blink=0)
    for i, o in enumerate(('french1', 'french2', 'boy', 'bowyer')):
        figure(pn, 760 + (i % 2) * 210, 1250 + (i // 2) * 420, 0.95 if o != 'boy' else 0.62, -1, 'walk' if i < 2 else 'idle', o,
               'determined' if i < 2 else 'neutral', blink=0)
    flatten(im, lay); im.convert('RGB').save('sheet_pose.png')

def sheet2():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    for i, k in enumerate((0.35, 0.8, 2.2)):
        pn.push(120 + i * 150 if i < 2 else 700, 520, k)
        lb.longbow(pn, 0, 0, 1, 0.6 if i == 2 else 0.0, string_to=(-110, 0) if i == 2 else None)
        if i == 2: lb.arrow(pn, (-110, 0), 0)
        pn.pop()
    lb.log_end(pn, 220, 1150, 120)
    lb.log_end(pn, 220, 1450, 90, split=1.0, glow_sap=0.5)
    lb.butt(pn, 560, 1250, 1.3, hit=((-8, 6, 0.5), (14, -12, 0.4)))
    lb.skeleton(pn, 900, 1450, 1.0, arm_thick=1.0, hl=0.6, draw=0.6)
    lb.scroll(pn, 560, 1450, 300, 1.0, 1.0)
    lb.banner_fr(pn, 980, 1000, 1.0, 0.3)
    lb.limb_segment(pn, 540, 1800, 360, 60, 0.6, 0.5, 0.0)
    flatten(im, lay); im.convert('RGB').save('sheet_props.png')

sheet1(); sheet2()

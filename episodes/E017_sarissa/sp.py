"""E017 Macedonian sarissa phalanx: held object rigs (phalangite with sarissa and pelta, hoplite with dory and aspis),
environments and map levels."""
import math, random
from PIL import Image, ImageDraw
from lib import *
from rig import *
import props as PR
from props import sarissa, dory, pelta, aspis, SARISSA_L, DORY_L
import env as E
from detail import shade, light

# ---------------- grips (figure local units; feet at y 0, pelvis about -72, neck about -172) ----------------
def pike_hands(f, ang=0.0, lift=0.0):
    """Two handed sarissa hold: right (back) hand near the butt end, left (front) hand a forearm ahead, both on one shaft line.
    ang: shaft angle from level (positive raises the point), lift: raises the whole grip."""
    a = -ang
    bx, by = -f * 12, -92 - lift
    fx_, fy = bx + f * 52 * math.cos(a), by + 52 * math.sin(a)
    return {'B': (bx, by), 'F': (fx_, fy)}

def phalangite(pn, x, y, k, f=1, ang=0.0, t=0.0, out='phalanx', expr='determined', look=(0.8, 0.0), p=None, lift=0.0,
               pike=True, shield=True, back=240, L=SARISSA_L, flex=0.0, blink=None, pike_alpha=1.0, upright=False):
    """Phalangite. CARRY (BM-P002): the pelta hangs from a neck strap on the LEFT side, over the left shoulder and upper arm;
    the left (front, F) forearm goes through the armband behind it and only the left hand comes out past the rim onto
    the shaft. The right (back, B) arm stays free and in front, gripping near the butt. The shaft passes in front of the
    shield's lower edge. Returns world tip and butt of the sarissa."""
    p = p or pose('idle', torso=2)
    p = dict(p); p['torso'] = p.get('torso', 0) + 1.2 * math.sin(t * 2.3 + x * 0.011)   # breathing (secondary action)
    info = {}
    if upright:        # marching carry: shaft vertical in the right (back) hand; left hand rests behind the pelta
        hands = {'B': (-f * 50, -118), 'F': (f * 16, -104)}
        ang_r = -math.pi / 2
    else:
        hands = pike_hands(f, ang, lift)
        ang_r = math.atan2(hands['F'][1] - hands['B'][1], hands['F'][0] - hands['B'][0])
    def mid(pn_, J):
        if shield:
            nk, sh = J['neck'], J['shF']
            pelta(pn_, sh[0] + f * 4, sh[1] + 22, 40, f, strap_to=(nk[0], nk[1] + 2))
    def held(pn_, J):
        if not pike: return
        if upright:
            g = J['haB']
            R = sarissa(pn_, g[0], g[1], ang_r, back=88, L=L)
        else:
            g = J['haB']
            R = sarissa(pn_, g[0], g[1], ang_r, back=back, L=L, flex=flex)
        info.update(R)
    J = figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink_at(t, x * 0.013) if blink is None else blink,
               hands=hands, held=held, mid=mid, f_behind=shield, b_hide=upright)
    W_ = lambda pt: (x + pt[0] * k, y + pt[1] * k)
    res = dict(J=J)
    if 'tip' in info: res.update(tip=W_(info['tip']), butt=W_(info['butt']))
    return res

def hoplite(pn, x, y, k, f=1, t=0.0, out='hoplite', expr='determined', look=(0.8, 0.0), p=None, thrust=0.0, ang=0.18,
            spear=True, blink=None, shield_r=56, legs=1.0):
    """Hoplite: aspis on the back forearm (hand hidden on the antilabe), dory overhand in the front hand.
    thrust 0..1 pushes the spear hand forward along the shaft line."""
    p = p or pose('idle', torso=3)
    p = dict(p); p['torso'] = p.get('torso', 0) + 1.2 * math.sin(t * 2.3 + x * 0.011)   # breathing (secondary action)
    a = ang
    hx = f * (26 + 34 * thrust); hy = -168 + 6 * thrust
    hands = {'F': (hx, hy), 'B': (-f * 8, -120)}
    info = {}
    def mid(pn_, J):
        nk, pe = J['neck'], J['pelvis']
        aspis(pn_, lerp(nk[0], pe[0], .5) - f * 10, lerp(nk[1], pe[1], .5) - 4, shield_r, f)
    def held(pn_, J):
        if not spear: return
        g = J['haF']
        R = dory(pn_, g[0], g[1], math.atan2(math.sin(a), f * math.cos(a)), back=120)
        info.update(R)
    J = figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink_at(t, x * 0.017) if blink is None else blink,
               hands=hands, held=held, mid=mid, b_behind=True, b_hide=True, legs=legs)
    W_ = lambda pt: (x + pt[0] * k, y + pt[1] * k)
    res = dict(J=J)
    if 'tip' in info: res.update(tip=W_(info['tip']))
    return res

# ---------------- environments ----------------
def env_plain():
    """Open plain in northern Greece, late summer: hazy sky, blue ranges, dry golden grass."""
    im = E.sky((150, 178, 206), (238, 224, 190), (40, 26, 0), 0.5)
    E.clouds(im, 41, (255, 250, 240, 140), n=6)
    E.hill_layer(im, 990, 70, (128, 140, 164), 3)
    E.hill_layer(im, 1070, 40, (150, 150, 140), 8, freqs=(1.2, 3.0, 6.0))
    E.hill_layer(im, 1150, 12, (196, 170, 112), 2, freqs=(1.5, 4.0))
    return E.grade(im, blur=3, sat=0.85, bright=1.0)

def env_plaindust():
    im = E.sky((176, 170, 158), (226, 208, 172), (40, 26, 0), 0.5)
    E.hill_layer(im, 1000, 60, (150, 148, 150), 3)
    E.hill_layer(im, 1150, 12, (190, 164, 110), 2, freqs=(1.5, 4.0))
    return E.grade(im, blur=4, sat=0.7, bright=0.98)

for _n in ('plain', 'plaindust'):
    setattr(E, 'env_' + _n, globals()['env_' + _n])

GRASS = (200, 176, 116); GRASS_D = (164, 140, 86)
def dry_ground(pn, y, t=0.0, col=GRASS, seed=8, n=60):
    pn.rect(-400, y, 1480, 2800, fill=col)
    pn.line([(-400, y), (1480, y)], lerpc(col, INK, .4), 4, caps=False)
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.uniform(-60, 1140); yy = y + 10 + rnd.uniform(0, 700)
        sw = math.sin(t * 2 + i) * 2
        pn.line([(x, yy), (x + sw - 4, yy - 12 - (yy - y) / 50)], GRASS_D, 3)
        pn.line([(x + 6, yy), (x + 8 + sw, yy - 10 - (yy - y) / 60)], light(col, 0.3), 3)
    for i in range(7):
        x = rnd.uniform(-40, 1120); yy = y + 30 + rnd.uniform(0, 500)
        pn.ell(x, yy, 13, 6, fill=(170, 160, 140), outline=INK, width=2)

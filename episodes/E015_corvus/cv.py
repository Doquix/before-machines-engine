"""E015 Corvus: props (galley with ram, corvus boarding bridge, pestle) and environments."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
import env as E
import make_map as MM

MM.LEVELS = [('ov', 12.6, 39.2, 12.5, 2), ('det', 15.3, 38.1, 2.6, 2)]

ROM_HULL = (104, 70, 42); ROM_STRIPE = (150, 58, 44)
PUN_HULL = (78, 58, 46); PUN_STRIPE = (104, 46, 92)
BRZ = (196, 146, 66); BRZ_D = (140, 98, 40)
DECK_Y = -70          # deck height in galley units
CV_FT = 11.0          # corvus units per foot when mounted on a galley

def plank_rect(pn, a, b, w, fill, width=3.4):
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / Ln * w / 2, dx / Ln * w / 2
    pn.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill=fill, outline=INK, width=width)

def spike_shape(pn, x, y, ang, ln, f=1, col=IRON):
    """Pestle shaped iron spike: rounded heavy head at (x, y), pointed end ln away along ang (radians)."""
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    def P_(u, v): return (x + ca * u * ln + nx * v * ln, y + sa * u * ln + ny * v * ln)
    body = [P_(0.0, -0.13), P_(0.18, -0.16), P_(0.5, -0.10), P_(0.82, -0.05), P_(1.0, 0), P_(0.82, 0.05), P_(0.5, 0.10), P_(0.18, 0.16), P_(0.0, 0.13)]
    pn.poly(body, fill=col, outline=INK, width=3)
    pn.line([P_(0.12, -0.08), P_(0.55, -0.05)], lerpc(col, WHITE, .45), 3)
    pn.circ(*P_(-0.06, 0), ln * 0.09, outline=INK, width=3)      # ring for the rope
    return P_(1.0, 0)

def corvus(pn, x, y, k, ang, f=1, ft=CV_FT, rails=1.0, spike=1.0, pole=1.0, pulley=1.0, bridge=1.0, rope=1.0,
           inner=True, hl=None, rope_slack=0.0):
    """Corvus on a deck. Origin (x, y) is the foot of the pole on the deck. ang: outer bridge angle in degrees above
    horizontal, pointing toward +f. Proportions after Polybius 1.22: pole 4 fathoms, gangway 6 fathoms (12 ft inboard
    of the pole, 24 ft outboard), 4 ft wide, knee high rails, pestle shaped iron spike at the tip.
    Returns world points."""
    hl = hl or {}
    def hc(part, base): v = hl.get(part, 0); return lerpc(base, AMBER, v) if v else base
    pn.push(x, y, k)
    X = lambda v: f * v
    Hp = 24 * ft * clamp(pole); thick = 1.1 * ft; railh = 1.7 * ft
    piv = (0.0, -1.2 * ft)
    a = math.radians(ang); ux, uy = f * math.cos(a), -math.sin(a)
    Lo = 24 * ft
    tip = (piv[0] + ux * Lo * clamp(bridge), piv[1] + uy * Lo * clamp(bridge))
    top = (0.0, -Hp)
    # inboard part lying on the deck
    if inner and bridge > 0.01:
        a0 = (X(-12 * ft), -thick / 2); b0 = (X(-0.4 * ft), -thick / 2)
        plank_rect(pn, a0, b0, thick, hc('bridge', (168, 122, 74)))
        if rails > 0.01:
            for i in range(5):
                xx = lerp(a0[0], b0[0], i / 4)
                pn.line([(xx, -thick), (xx, -thick - railh * rails)], WOOD_D, 3.4, caps=False)
            pn.line([(a0[0], -thick - railh * rails), (b0[0], -thick - railh * rails)], hc('rail', WOOD_D), 4)
    # pole
    if pole > 0.01:
        plank_rect(pn, (0, 0), top, 0.9 * ft, hc('pole', WOOD))
        pn.line([(0, 0), (X(-2.2 * ft), 0)], WOOD_D, 6)
    # rope from the pulley down to the tip ring
    tipring = None
    if bridge > 0.01:
        # outboard gangway with rails
        plank_rect(pn, piv, tip, thick, hc('bridge', (168, 122, 74)))
        if rails > 0.01:
            nx_, ny_ = uy * f * -1 if False else -uy, ux    # perpendicular
            nx_, ny_ = (uy, -ux) if f == 1 else (-uy, ux)
            if ny_ > 0: nx_, ny_ = -nx_, -ny_         # always toward the sky side
            for i in range(7):
                u = 0.05 + i * 0.15
                b_ = (piv[0] + ux * Lo * clamp(bridge) * u, piv[1] + uy * Lo * clamp(bridge) * u)
                pn.line([(b_[0] + nx_ * thick * .5, b_[1] + ny_ * thick * .5), (b_[0] + nx_ * (thick * .5 + railh * rails), b_[1] + ny_ * (thick * .5 + railh * rails))],
                        WOOD_D, 3.4, caps=False)
            r0 = (piv[0] + ux * Lo * 0.04 + nx_ * (thick * .5 + railh * rails), piv[1] + uy * Lo * 0.04 + ny_ * (thick * .5 + railh * rails))
            r1 = (tip[0] - ux * Lo * 0.04 + nx_ * (thick * .5 + railh * rails), tip[1] - uy * Lo * 0.04 + ny_ * (thick * .5 + railh * rails))
            pn.line([r0, r1], hc('rail', WOOD_D), 4.5)
        pn.circ(*piv, 0.55 * ft, fill=IRON, outline=INK, width=2.6)
        # spike under the tip, perpendicular to the gangway
        if spike > 0.01:
            sx_, sy_ = (-uy, ux) if f == 1 else (uy, -ux)
            if sy_ < 0: sx_, sy_ = -sx_, -sy_
            sp_ = spike_shape(pn, tip[0], tip[1] + 0.2 * ft, math.atan2(sy_, sx_), 3.6 * ft * clamp(spike), f, hc('spike', IRON))
        else:
            sp_ = tip
        tipring = (tip[0] - ux * 0.6 * ft, tip[1] - uy * 0.6 * ft - 1.4 * ft)
    if rope > 0.01 and bridge > 0.01 and pole > 0.5:
        if rope_slack > 0:
            mid = ((top[0] + tipring[0]) / 2 + X(2 * ft * rope_slack), (top[1] + tipring[1]) / 2 + 6 * ft * rope_slack)
            pn.line([top, mid, tipring], INK, 5); pn.line([top, mid, tipring], hc('rope', ROPE), 3)
        else:
            pn.line([top, tipring], INK, 5); pn.line([top, tipring], hc('rope', ROPE), 3)
        # hauling end runs down the back of the pole
        pn.line([(X(-0.6 * ft), -Hp), (X(-0.6 * ft), -3 * ft)], INK, 5); pn.line([(X(-0.6 * ft), -Hp), (X(-0.6 * ft), -3 * ft)], ROPE, 3)
    if pulley > 0.01 and pole > 0.5:
        pn.circ(0, -Hp, 1.3 * ft * clamp(pulley), fill=hc('pulley', WOOD_D), outline=INK, width=3)
        pn.circ(0, -Hp, 0.4 * ft * clamp(pulley), fill=IRON)
    pn.pop()
    Wp = lambda p: (x + p[0] * k, y + p[1] * k)
    return dict(top=Wp(top), tip=Wp(tip), piv=Wp(piv), spike=Wp(sp_) if bridge > 0.01 else Wp(tip),
                base=Wp((0, 0)), ring=Wp(tipring) if tipring else Wp(tip), mid=Wp(((piv[0] + tip[0]) / 2, (piv[1] + tip[1]) / 2)))

def galley(pn, x, y, k, t, f=1, hull=ROM_HULL, stripe=ROM_STRIPE, oar_rate=1.2, row=1.0, mast=False, sail=(226, 214, 186),
           eye=True, corvus_ang=None, corvus_kw=None, damage=0.0, oars=True):
    """Oared warship (quinquereme type), side view, waterline at y, bow toward +f, bronze ram at the waterline.
    Returns world points (deck at bow, mid deck, ram, pole base if a corvus is mounted, corvus dict)."""
    pn.push(x, y, k)
    X = lambda v: f * v
    if oars:
        for bank, (yt, n, x0, dxo) in enumerate(((-52, 15, -380, 54), (-26, 15, -353, 54))):
            for i in range(n):
                ox = x0 + i * dxo
                ph = t * oar_rate * 2 * math.pi * row + i * 0.18 + bank * 0.6
                sw = math.sin(ph) * 22 * row
                top = (X(ox), yt); bot = (X(ox + sw - 46), 74 + 10 * math.cos(ph) * row)
                pn.line([top, bot], INK, 6.5); pn.line([top, bot], (156, 118, 74), 3.2)
    hp = [(X(-470), -150), (X(-430), -100), (X(-380), DECK_Y), (X(420), DECK_Y), (X(462), -96), (X(486), -112),
          (X(492), -96), (X(470), -40), (X(470), 14), (X(420), 34), (X(-360), 34), (X(-440), -10), (X(-500), -110)]
    pn.poly(hp, fill=hull, outline=INK, width=4)
    pn.line([(X(-420), -58), (X(450), -58)], stripe, 9, caps=False)
    pn.line([(X(-370), -6), (X(452), -6)], lerpc(hull, INK, .3), 3, caps=False)
    for i in range(14):
        xx = -330 + i * 54
        pn.circ(X(xx), -40, 5, fill=lerpc(hull, INK, .45))
    # bronze ram (rostrum) with fins
    ram = [(X(460), -22), (X(536), -8), (X(548), 2), (X(536), 12), (X(460), 24)]
    pn.poly(ram, fill=BRZ, outline=INK, width=3.4)
    for yy in (-6, 8): pn.line([(X(476), yy), (X(536), yy * .6)], BRZ_D, 3, caps=False)
    pn.line([(X(470), -32), (X(500), -30)], BRZ, 6)      # proembolion
    if eye:
        pn.ell(X(430), -34, 15, 9, fill=WHITE, outline=INK, width=3)
        pn.circ(X(434), -34, 5, fill=INK)
    # stern curl (aplustre)
    cur = [(X(-470), -150), (X(-500), -205), (X(-488), -252), (X(-452), -268), (X(-428), -246), (X(-446), -228)]
    pn.line(cur, INK, 15); pn.line(cur, hull, 9)
    # steering oar
    pn.line([(X(-420), -96), (X(-470), 60)], INK, 9); pn.line([(X(-420), -96), (X(-470), 60)], (156, 118, 74), 5)
    pn.poly([(X(-462), 20), (X(-482), 22), (X(-478), 80), (X(-458), 76)], fill=(156, 118, 74), outline=INK, width=2.6)
    # deck rail
    pn.line([(X(-390), -96), (X(410), -96)], lerpc(hull, WHITE, .2), 5, caps=False)
    for i in range(16):
        xx = -380 + i * 50
        pn.line([(X(xx), -96), (X(xx), DECK_Y)], lerpc(hull, INK, .2), 3, caps=False)
    if mast:
        pn.line([(X(-30), DECK_Y), (X(-30), -560)], INK, 16); pn.line([(X(-30), DECK_Y), (X(-30), -560)], WOOD, 10)
        pn.line([(X(-230), -520), (X(170), -520)], INK, 10); pn.line([(X(-230), -520), (X(170), -520)], WOOD, 6)
        pn.rect(X(-220), -520, X(160), -490, fill=sail, outline=INK, width=3, r=12)   # sail furled for battle
    if damage > 0:
        rnd = random.Random(7)
        cx_ = X(-120)
        pn.poly([(cx_ - 50, -50), (cx_ + 10, -66), (cx_ + 60, -30), (cx_ + 30, 10), (cx_ - 40, 4)], fill=(30, 22, 18, int(255 * damage)))
        for i in range(6):
            a = rnd.uniform(0, 6.28); r = rnd.uniform(40, 90) * damage
            pn.line([(cx_, -20), (cx_ + math.cos(a) * r, -20 + math.sin(a) * r * .6)], INK, 3)
    cv = None
    if corvus_ang is not None:
        kw = dict(corvus_kw or {})
        cv = corvus(pn, X(440), DECK_Y, 1.0, corvus_ang, f, **kw)
    pn.pop()
    W_ = lambda p: (x + p[0] * k, y + p[1] * k)
    out = dict(bow=W_((X(440), DECK_Y)), mid=W_((0, DECK_Y)), ram=W_((X(548), 2)), deck=DECK_Y, stern=W_((X(-300), DECK_Y)))
    if cv: out['cv'] = {n: (x + p[0] * k, y + p[1] * k) for n, p in cv.items()}
    return out

def pestle(pn, x, y, k, ang=-0.35, mortar=True):
    pn.push(x, y, k)
    if mortar:
        pn.poly([(-80, -110), (80, -110), (60, -10), (40, 0), (-40, 0), (-60, -10)], fill=(170, 160, 146), outline=INK, width=4)
        pn.ell(0, -110, 80, 16, fill=(110, 104, 96), outline=INK, width=3.4)
    # club shaped pestle: heavy rounded end in the bowl, thin handle up and out
    ca, sa = math.cos(ang - math.pi / 2), math.sin(ang - math.pi / 2); nx, ny = -sa, ca
    def Q(u, v): return (10 + ca * u + nx * v, -100 + sa * u + ny * v)
    prof = [(0, 26), (40, 24), (110, 15), (200, 11), (230, 11)]
    pts = [Q(u, v) for u, v in prof] + [Q(u, -v) for u, v in prof[::-1]]
    pn.poly(pts, fill=(184, 150, 106), outline=INK, width=3.4)
    pn.circ(*Q(0, 0), 26, fill=(184, 150, 106), outline=INK, width=3.4)
    pn.poly([Q(4, 22), Q(40, 22), Q(40, -22), Q(4, -22)], fill=(184, 150, 106))
    pn.circ(*Q(230, 0), 11, fill=(184, 150, 106), outline=INK, width=3.4)
    if mortar: pn.poly([(-80, -110), (80, -110), (74, -86), (-74, -86)], fill=(170, 160, 146), outline=INK, width=3.4)
    pn.pop()

def formation(pn, x0, x1, y, k, n, t, out='legion2', expr='determined', seed=0, march=0.0, f=1, look=(0.6, 0)):
    """A row of identical small legionaries (a formation counts as one figure)."""
    from rig import figure, pose, blink_at
    for i in range(n):
        x = lerp(x0, x1, i / max(1, n - 1))
        p = pose('walk', thF=18 * math.sin(t * 8 + i), thB=-18 * math.sin(t * 8 + i)) if march else 'idle'
        figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink_at(t, seed + i * 0.7))

# ---------------- environments ----------------
def env_field():
    im = E.sky((118, 166, 214), (248, 228, 190), (40, 24, 0), 0.5)
    E.clouds(im, 11, (255, 250, 240, 150))
    E.hill_layer(im, 1010, 70, (128, 136, 150), 4)
    E.hill_layer(im, 1110, 36, (150, 150, 120), 8, freqs=(1.4, 3.3, 6.0))
    E.hill_layer(im, 1200, 14, (150, 146, 92), 2, freqs=(1.5, 4.0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for i in range(9):   # cypress and olive dots on the near hills
        x = rnd.uniform(30, 1050); y = 1150 + rnd.uniform(0, 60)
        if i % 2: d.ellipse([x - 9, y - 70, x + 9, y], fill=(78, 92, 60))
        else: d.ellipse([x - 26, y - 34, x + 26, y], fill=(110, 118, 78))
    return E.grade(im, blur=3, sat=0.85, bright=1.04)

def env_beach():
    im = E.sky((116, 160, 204), (248, 226, 190), (40, 22, 0), 0.5)
    E.clouds(im, 13, (255, 250, 240, 140))
    E.hill_layer(im, 1000, 50, (124, 130, 146), 6)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1040, W, H], fill=(54, 96, 118))
    for i in range(70):
        y = 1050 + (i * 17) % 300; x = (i * 211) % W
        d.line([(x, y), (x + 40 + y / 30, y)], fill=(110, 150, 170), width=2)
    return E.grade(im, blur=3, sat=0.85, bright=1.04)

def env_seaday():
    im = E.sky((112, 160, 208), (248, 226, 188), (40, 20, 0), 0.55)
    E.clouds(im, 17, (255, 250, 240, 140))
    E.hill_layer(im, 1040, 22, (116, 122, 136), 5, freqs=(1.0, 2.6, 6.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1066, W, H], fill=(52, 92, 116))
    for i in range(90):
        y = 1076 + (i * 17) % 840; x = (i * 211) % W
        d.line([(x, y), (x + 40 + y / 30, y)], fill=(110, 150, 170), width=2)
    return E.grade(im, blur=3, sat=0.85, bright=1.04)

for _n in ('field', 'beach', 'seaday'):
    setattr(E, 'env_' + _n, globals()['env_' + _n])

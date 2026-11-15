"""E015 Corvus: props (galley with ram, corvus boarding bridge, pestle) and environments."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
import env as E
import make_map as MM
from detail import lod, thin_ok, shade, light, wood_plank, rivet, scratches
from detail import rope as rope_line

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
    """Pestle shaped iron spike (Polybius 1.22): heavy rounded head at (x, y), forged point ln away along ang.
    Two tones split down a forged ridge, a hard highlight, hammer facets and a ring for the rope at close range."""
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    def P_(u, v): return (x + ca * u * ln + nx * v * ln, y + sa * u * ln + ny * v * ln)
    prof = [(0.0, 0.13), (0.06, 0.16), (0.2, 0.165), (0.5, 0.10), (0.82, 0.05), (1.0, 0.0)]
    left = [P_(u, -v) for u, v in prof]; right = [P_(u, v) for u, v in prof[::-1]]
    L = lod(pn, ln)
    # the lit half faces up and left; pick which side is lit from the normal
    lit_neg = (nx * -1 + ny * -1) > 0
    pn.poly(left + right, fill=col, outline=INK, width=3)
    dark = right if lit_neg else left[::-1]
    ridge = [P_(u, 0) for u, v in prof]
    pn.poly(ridge + (dark if not lit_neg else dark), fill=shade(col, 0.3))
    hs = -1 if lit_neg else 1
    pn.poly([P_(0.08, hs * 0.11), P_(0.45, hs * 0.07), P_(0.75, hs * 0.03), P_(0.45, hs * 0.045), P_(0.1, hs * 0.075)], fill=light(col, 0.55))
    if L >= 1:
        for u in (0.28, 0.42, 0.6):     # hammer facets
            pn.line([P_(u, -prof[3][1] * 0.8), P_(u + 0.04, 0)], shade(col, 0.45), max(1.0, ln * 0.008), caps=False)
        pn.line([P_(0.0, -0.13), P_(0.0, 0.13)], shade(col, 0.4), max(1.2, ln * 0.012), caps=False)
    rc = P_(-0.07, 0)
    pn.circ(*rc, ln * 0.085, outline=INK, width=max(3, ln * 0.03))
    if L >= 1: pn.circ(*rc, ln * 0.085, outline=light(col, 0.3), width=max(1, ln * 0.01))
    if L >= 2: scratches(pn, *P_(0.3, 0), ln * 0.18, 2, col=(255, 255, 255, 50))
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
        wood_plank(pn, a0, b0, thick, hc('bridge', (168, 122, 74)), seed=5, nails=[ft * 1.5 * i for i in range(1, 8)])
        if rails > 0.01:
            for i in range(5):
                xx = lerp(a0[0], b0[0], i / 4)
                pn.line([(xx, -thick), (xx, -thick - railh * rails)], WOOD_D, 3.4, caps=False)
            pn.line([(a0[0], -thick - railh * rails), (b0[0], -thick - railh * rails)], hc('rail', WOOD_D), 4)
    # pole
    if pole > 0.01:
        wood_plank(pn, (0, 0), top, 0.9 * ft, hc('pole', WOOD), seed=9, knots=True)
        for u in (0.12, 0.5, 0.88):      # iron bands round the pole
            yy = -Hp * u
            pn.rect(-0.55 * ft, yy - 0.25 * ft, 0.55 * ft, yy + 0.25 * ft, fill=IRON, outline=INK, width=2)
            pn.line([(-0.45 * ft, yy - 0.12 * ft), (0.1 * ft, yy - 0.12 * ft)], light(IRON, 0.5), max(1, 0.08 * ft), caps=False)
        wood_plank(pn, (X(0.4 * ft), -0.3 * ft), (X(-2.4 * ft), -0.3 * ft), 0.6 * ft, WOOD_D, seed=2)   # step block
    # rope from the pulley down to the tip ring
    tipring = None
    if bridge > 0.01:
        # outboard gangway with rails
        wood_plank(pn, piv, tip, thick, hc('bridge', (168, 122, 74)), seed=7, nails=[Lo * clamp(bridge) * u for u in (0.12, 0.3, 0.48, 0.66, 0.84)])
        if rails > 0.01:
            nx_, ny_ = uy * f * -1 if False else -uy, ux    # perpendicular
            nx_, ny_ = (uy, -ux) if f == 1 else (-uy, ux)
            if ny_ > 0: nx_, ny_ = -nx_, -ny_         # always toward the sky side
            for i in range(7):
                u = 0.05 + i * 0.15
                b_ = (piv[0] + ux * Lo * clamp(bridge) * u, piv[1] + uy * Lo * clamp(bridge) * u)
                p0 = (b_[0] + nx_ * thick * .5, b_[1] + ny_ * thick * .5); p1 = (b_[0] + nx_ * (thick * .5 + railh * rails), b_[1] + ny_ * (thick * .5 + railh * rails))
                pn.line([p0, p1], INK, max(3.4, 0.42 * ft), caps=False); pn.line([p0, p1], WOOD, max(1.6, 0.26 * ft), caps=False)
            r0 = (piv[0] + ux * Lo * 0.04 + nx_ * (thick * .5 + railh * rails), piv[1] + uy * Lo * 0.04 + ny_ * (thick * .5 + railh * rails))
            r1 = (tip[0] - ux * Lo * 0.04 + nx_ * (thick * .5 + railh * rails), tip[1] - uy * Lo * 0.04 + ny_ * (thick * .5 + railh * rails))
            wood_plank(pn, r0, r1, max(4.0, 0.45 * ft), hc('rail', WOOD_D), seed=11, bevel=False)
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
        rw = max(3.0, 0.32 * ft)
        if rope_slack > 0:
            pts = []
            for i in range(9):
                u = i / 8
                pts.append((lerp(top[0], tipring[0], u) + X(2 * ft * rope_slack) * math.sin(math.pi * u),
                            lerp(top[1], tipring[1], u) + 6 * ft * rope_slack * math.sin(math.pi * u)))
            rope_line(pn, pts, rw, hc('rope', ROPE))
        else:
            rope_line(pn, [top, tipring], rw, hc('rope', ROPE))
        # hauling end runs down the back of the pole to a cleat
        rope_line(pn, [(X(-0.6 * ft), -Hp), (X(-0.6 * ft), -3 * ft)], rw, ROPE)
        pn.rect(X(-0.6 * ft) - 0.5 * ft, -3.2 * ft, X(-0.6 * ft) + 0.5 * ft, -2.6 * ft, fill=WOOD_D, outline=INK, width=2)
    if pulley > 0.01 and pole > 0.5:
        R_ = 1.3 * ft * clamp(pulley)
        pn.rect(-0.35 * ft, -Hp - R_ * 0.2, 0.35 * ft, -Hp + R_ * 1.1, fill=IRON, outline=INK, width=2)   # iron strap
        pn.circ(0, -Hp, R_, fill=hc('pulley', WOOD_D), outline=INK, width=3)
        if lod(pn, 2 * R_) >= 1 or R_ * pn.k() > 14:
            pn.circ(0, -Hp, R_ * 0.72, outline=shade(WOOD_D, 0.35), width=max(1, 0.12 * ft))
            for i in range(4):
                a_ = i * math.pi / 4 + 0.3
                pn.line([(math.cos(a_) * R_ * 0.7, -Hp + math.sin(a_) * R_ * 0.7), (-math.cos(a_) * R_ * 0.7, -Hp - math.sin(a_) * R_ * 0.7)],
                        shade(WOOD_D, 0.3), max(1, 0.1 * ft), caps=False)
            pn.circ(-R_ * 0.35, -Hp - R_ * 0.35, R_ * 0.18, fill=light(WOOD_D, 0.3))
        pn.circ(0, -Hp, 0.4 * ft * clamp(pulley), fill=IRON, outline=INK, width=1.6)
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
    GL = lod(pn, 1000)
    # planking: strakes follow the sheer, lower hull in shade under the wale
    pn.poly([(X(-380), -20), (X(462), -20), (X(470), 14), (X(420), 34), (X(-360), 34), (X(-420), 0)], fill=shade(hull, 0.18))
    if GL >= 1:
        for yy in (-30, -12, 6, 22):
            pn.line([(X(-400 + (yy + 30) * 0.6), yy), (X(462), yy)], shade(hull, 0.42), 2.6, caps=False)
            pn.line([(X(-400 + (yy + 30) * 0.6), yy + 3), (X(458), yy + 3)], light(hull, 0.16), 1.6, caps=False)
        if GL >= 2:
            for yy in (-21, -3, 14):
                for i in range(5):
                    x0 = -300 + i * 160 + (yy * 7) % 60
                    pn.line([(X(x0), yy), (X(x0 + 70), yy + 1.5), (X(x0 + 120), yy)], shade(hull, 0.3) + (160,), 1.4, caps=False)
        rnd = random.Random(int(hull[0]))
        for i in range(10):     # butt joints between planks
            xx = rnd.uniform(-330, 420); yy = rnd.choice((-30, -12, 6))
            pn.line([(X(xx), yy), (X(xx), yy + 18)], shade(hull, 0.3), 2, caps=False)
    pn.line([(X(-420), -66), (X(456), -66)], light(hull, 0.25), 3, caps=False)
    pn.line([(X(-420), -58), (X(450), -58)], stripe, 9, caps=False)
    if GL >= 1: pn.line([(X(-420), -61), (X(450), -61)], light(stripe, 0.3), 2, caps=False)
    pn.line([(X(-370), -6), (X(452), -6)], lerpc(hull, INK, .3), 3, caps=False)
    for i in range(14):     # oar ports with leather sleeves
        xx = -330 + i * 54
        if GL >= 1:
            pn.ell(X(xx), -40, 9, 6, fill=(96, 66, 40), outline=INK, width=1.4)
            pn.circ(X(xx), -40, 3.6, fill=(26, 18, 12))
        else:
            pn.circ(X(xx), -40, 5, fill=lerpc(hull, INK, .45))
    # bronze ram (rostrum) with three fins, after the First Punic War rams raised off the Egadi Islands
    ram = [(X(458), -24), (X(530), -12), (X(550), 2), (X(530), 16), (X(458), 26)]
    pn.poly(ram, fill=BRZ, outline=INK, width=3.4)
    pn.poly([(X(458), 6), (X(530), 6), (X(550), 2), (X(530), 16), (X(458), 26)], fill=shade(BRZ, 0.28))
    pn.poly([(X(462), -20), (X(526), -10), (X(520), -5), (X(462), -12)], fill=light(BRZ, 0.5))
    for yy in (-10, 2, 14):
        pn.line([(X(470), yy), (X(538), yy * .5 + 1)], BRZ_D, 3, caps=False)
    if GL >= 1:
        for xx in (468, 490):
            for yy in (-14, 16): rivet(pn, X(xx), yy, 2.2, BRZ)
    pn.line([(X(470), -32), (X(500), -30)], BRZ, 6)      # proembolion
    if eye:
        pn.ell(X(430), -34, 15, 9, fill=WHITE, outline=INK, width=3)
        pn.circ(X(434), -34, 5, fill=INK)
    # stern curl (aplustre)
    cur = [(X(-470), -150), (X(-500), -205), (X(-488), -252), (X(-452), -268), (X(-428), -246), (X(-446), -228)]
    pn.line(cur, INK, 15); pn.line(cur, hull, 9)
    if GL >= 1: pn.line(cur[:4], light(hull, 0.3), 2.4, caps=False)
    # steering oar
    pn.line([(X(-420), -96), (X(-470), 60)], INK, 9); pn.line([(X(-420), -96), (X(-470), 60)], (156, 118, 74), 5)
    pn.poly([(X(-462), 20), (X(-482), 22), (X(-478), 80), (X(-458), 76)], fill=(156, 118, 74), outline=INK, width=2.6)
    # deck rail
    for i in range(16):
        xx = -380 + i * 50
        pn.line([(X(xx), -96), (X(xx), DECK_Y)], lerpc(hull, INK, .2), 3, caps=False)
    pn.line([(X(-390), -96), (X(410), -96)], INK, 7, caps=False)
    pn.line([(X(-390), -96), (X(410), -96)], lerpc(hull, WHITE, .2), 4, caps=False)
    if GL >= 1:
        for i in range(16): pn.circ(X(-380 + i * 50), -96, 2, fill=light(hull, 0.35))
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

def short_sword(pn, hand, elbow, k=1.0):
    """Mid Republican short sword in the fist: blade along the forearm line, two tones split down a central ridge,
    a hard highlight, a wooden grip with finger ridges, crossguard and round pommel (generic Italic type: the exact
    pattern Roman infantry carried in 260 BC is debated, so no type specific features are drawn)."""
    (hx, hy), (ex, ey) = hand, elbow
    dx, dy = hx - ex, hy - ey; Ln = math.hypot(dx, dy) or 1; ux, uy = dx / Ln, dy / Ln; nx, ny = -uy, ux
    if ny > 0: nx, ny = -nx, -ny
    q = lambda u, v: (hx + ux * u * k + nx * v * k, hy + uy * u * k + ny * v * k)
    BL = 62; SL = lod(pn, BL * k)
    steel = (206, 210, 216)
    blade = [q(9, 5), q(BL * .78, 4.6), q(BL, 0), q(BL * .78, -4.6), q(9, -5)]
    pn.poly(blade, fill=steel, outline=INK, width=2.4)
    pn.poly([q(9, 0), q(BL * .78, 0), q(BL, 0), q(BL * .78, -4.6), q(9, -5)], fill=shade(steel, 0.25))
    pn.line([q(11, 2), q(BL * .74, 1.8)], light(steel, 0.7), max(1, 1.2 * k), caps=False)
    pn.line([q(10, 0), q(BL * .9, 0)], shade(steel, 0.4), max(1, 0.8 * k), caps=False)
    pn.poly([q(5, 9), q(9, 9), q(9, -9), q(5, -9)], fill=cv_bronze(), outline=INK, width=2)       # guard
    pn.poly([q(-9, 3.6), q(5, 3.6), q(5, -3.6), q(-9, -3.6)], fill=(120, 84, 50), outline=INK, width=1.6)  # grip
    if SL >= 1:
        for u in (-5, -1, 3): pn.line([q(u, 3.4), q(u, -3.4)], shade((120, 84, 50), 0.35), max(1, 0.8 * k), caps=False)
    pn.circ(*q(-12, 0), 4.5 * k, fill=cv_bronze(), outline=INK, width=2)
    pn.circ(*q(-13, 1.4), 1.6 * k, fill=light(cv_bronze(), 0.6))

def cv_bronze(): return BRZ

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
    wc = (184, 150, 106); PL_ = lod(pn, 260)
    pn.poly(pts, fill=wc, outline=INK, width=3.4)
    pn.circ(*Q(0, 0), 26, fill=shade(wc, 0.12), outline=INK, width=3.4)      # the working end, darkened by use
    pn.poly([Q(4, 22), Q(40, 22), Q(40, -22), Q(4, -22)], fill=shade(wc, 0.12))
    pn.circ(*Q(230, 0), 11, fill=wc, outline=INK, width=3.4)
    side = 1 if (nx + ny) > 0 else -1      # lit side toward the upper left
    pn.poly([Q(30, -side * 22), Q(110, -side * 13), Q(225, -side * 9), Q(225, -side * 4), Q(110, -side * 6), Q(30, -side * 12)], fill=light(wc, 0.3))
    pn.poly([Q(20, side * 24), Q(110, side * 15), Q(225, side * 11), Q(225, side * 5), Q(110, side * 7), Q(20, side * 12)], fill=shade(wc, 0.22))
    if PL_ >= 1:
        for i, v in enumerate((-6, 2, 9)):      # grain along the handle
            pn.line([Q(40, v * 1.6), Q(120, v), Q(220, v * 0.6)], shade(wc, 0.32), 1.8, caps=False)
        pn.circ(*Q(234, 0), 6, outline=shade(wc, 0.3), width=1.4)     # end grain ring
        scratches(pn, *Q(10, 0), 60, 7, col=(60, 40, 24, 90))
    if mortar:
        pn.poly([(-80, -110), (80, -110), (74, -86), (-74, -86)], fill=(170, 160, 146), outline=INK, width=3.4)
        pn.line([(-76, -106), (76, -106)], light((170, 160, 146), 0.4), 2, caps=False)
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

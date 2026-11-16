"""E016 English longbow at Agincourt (1415): props, held object helpers and environments."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
import env as E
import make_map as MM
from detail import lod, thin_ok, shade, light, wood_plank, rivet, scratches
from detail import rope as rope_line

# overview: southern England and northern France; detail: the Agincourt area
MM.LEVELS = [('ov', 0.9, 50.3, 8.6, 2), ('det', 2.12, 50.47, 1.25, 2)]

SAP = (234, 216, 172)        # yew sapwood: pale cream
HEART = (170, 88, 50)        # yew heartwood: orange brown
HORN = (226, 210, 170)
SHAFT = (216, 190, 142)      # poplar arrow shaft (most Mary Rose arrows were poplar)
FLETCH = (226, 224, 214); FLETCH_D = (120, 116, 108)
BOW_U = 3.9                  # rig units per inch (a 5 ft 8 in figure is about 265 units tall)
BOW_L = 78 * BOW_U           # about six and a half feet
ARROW_L = 30 * BOW_U
EARTH = (122, 94, 62); EARTH_D = (92, 68, 44); MUD = (96, 74, 50); MUD_D = (70, 52, 34); MUD_WET = (120, 104, 84)
GRASS = (124, 134, 78); GRASS_L = (150, 156, 92)

# ---------------- the longbow ----------------
def bow_shape(gx, gy, f, draw, L=BOW_L, tilt=0.0, n=24):
    """Centreline of the bow, top to bottom, gripped at (gx, gy). Tips bend back toward the archer (-f) as it draws.
    Returns points and the deflection of the tips."""
    c = 24 + 46 * draw            # tip deflection: brace height when braced, more at full draw
    Lh = L / 2 * (1 - 0.05 * draw)
    pts = []
    ca, sa = math.cos(tilt), math.sin(tilt)
    for i in range(n + 1):
        v = -1 + 2 * i / n
        x = -f * c * v * v
        y = v * Lh
        pts.append((gx + x * ca - y * sa, gy + x * sa + y * ca))
    return pts, c

def longbow(pn, gx, gy, f=1, draw=0.0, string_to=None, tilt=0.0, L=BOW_L, strung=True, hl_back=0.0, hl_belly=0.0, w0=11.0, vib=0.0):
    """English war bow: a single yew stave with sapwood on the back (facing the target, +f) and heartwood on the belly
    (facing the archer), horn nocks at both tips. Returns the nock and string points."""
    pts, c = bow_shape(gx, gy, f, draw if strung else 0.0, L, tilt)
    if not strung:
        pts, c = bow_shape(gx, gy, f, -0.52, L, tilt)      # unstrung stave: almost straight
    n = len(pts) - 1
    back, belly, mid = [], [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(n, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(tx, ty) or 1
        nx, ny = ty / Ln, -tx / Ln
        if nx * f < 0: nx, ny = -nx, -ny                    # normal points to the back (target side)
        v = -1 + 2 * i / n
        w = w0 * (1 - 0.62 * abs(v) ** 1.3) + 2.2
        sap = 0.38                                          # sapwood is the thinner outer layer
        back.append((x + nx * w / 2, y + ny * w / 2))
        mid.append((x + nx * (w / 2 - w * sap), y + ny * (w / 2 - w * sap)))
        belly.append((x - nx * w / 2, y - ny * w / 2))
    L_ = lod(pn, L)
    # string first so the stave covers its ends
    top, bot = pts[0], pts[-1]
    sp = None
    if strung:
        if string_to is not None:
            sp = string_to
            pn.line([top, sp, bot], (238, 232, 214), 2.6, caps=False)
            pn.line([top, sp, bot], INK + (150,), 1.0, caps=False)
        else:
            if vib > 0:
                mx, my = (top[0] + bot[0]) / 2, (top[1] + bot[1]) / 2
                off = vib * 14 * math.sin(vib * 60)
                pn.line([top, (mx - f * off, my), bot], (238, 232, 214), 2.6, caps=False)
            else:
                pn.line([top, bot], (238, 232, 214), 2.6, caps=False)
            sp = ((top[0] + bot[0]) / 2, gy)
    sapc = lerpc(SAP, AMBER, hl_back) if hl_back else SAP
    hc = lerpc(HEART, AMBER, hl_belly) if hl_belly else HEART
    pn.poly(back + mid[::-1], fill=sapc)
    pn.poly(mid + belly[::-1], fill=hc)
    if L_ >= 1:
        pn.line(mid[2:-2], lerpc(hc, SAP, 0.35), 1.4, caps=False)           # the boundary between the two woods
        pn.line(back[3:-3], light(sapc, 0.5), 1.6, caps=False)                 # lit edge on the back
        if L_ >= 2:
            for k_ in (0.25, 0.7):
                q = [(lerp(m[0], b[0], k_), lerp(m[1], b[1], k_)) for m, b in zip(mid[4:-4], belly[4:-4])]
                pn.line(q, shade(hc, 0.22) + (170,), 1.2, caps=False)           # grain
            j = n // 2 + 3                                                    # a small pin knot on the belly
            pn.ell(lerp(mid[j][0], belly[j][0], .5), lerp(mid[j][1], belly[j][1], .5), 2.2, 1.4, fill=shade(hc, 0.4))
    pn.poly(back + belly[::-1], outline=INK, width=2.8)
    # horn nocks
    for i0, sgn in ((0, -1), (n, 1)):
        x, y = pts[i0]
        a = pts[i0 + (1 if i0 == 0 else -1)]
        dx, dy = x - a[0], y - a[1]; Ln = math.hypot(dx, dy) or 1; ux, uy = dx / Ln, dy / Ln
        hn = [(x - uy * 4 - ux * 2, y + ux * 4 - uy * 2), (x + uy * 4 - ux * 2, y - ux * 4 - uy * 2), (x + ux * 13, y + uy * 13)]
        pn.poly(hn, fill=HORN, outline=INK, width=2.2)
    return dict(top=top, bot=bot, string=sp, grip=(gx, gy), deflect=c)

def arrow(pn, nock, ang, L=ARROW_L, head='bodkin', hl=0.0, fl=True, w=3.4):
    """War arrow from its nock along angle ang (radians): poplar shaft, three goose feathers, iron bodkin."""
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    q = lambda u, v: (nock[0] + ca * u + nx * v, nock[1] + sa * u + ny * v)
    sc = lerpc(SHAFT, AMBER, hl) if hl else SHAFT
    pn.line([q(0, 0), q(L - 10, 0)], INK, w + 2.6)
    pn.line([q(0, 0), q(L - 10, 0)], sc, w)
    if fl:      # long, low goose feathers, tallest at the rear, tapering toward the head
        for sd, col in ((-1, FLETCH), (1, FLETCH_D)):
            pn.poly([q(3, 0), q(5, sd * 7.5), q(18, sd * 6.5), q(34, sd * 2.5), q(38, 0)], fill=col, outline=INK, width=1.6)
        pn.line([q(1, 0), q(4, 0)], (60, 46, 34), w + 1, caps=False)          # horn nock insert
    if head == 'bodkin':
        pn.poly([q(L - 13, -3.2), q(L - 6, -2.6), q(L + 6, 0), q(L - 6, 2.6), q(L - 13, 3.2)], fill=IRON, outline=INK, width=2)
    else:
        pn.poly([q(L - 13, -3), q(L - 6, -9), q(L + 8, 0), q(L - 6, 9), q(L - 13, 3)], fill=IRON, outline=INK, width=2)
    return q(L + 6, 0)

DRAW_START = 40       # string hand, units ahead of the neck, when the draw begins
DRAW_ANCHOR = -12     # string hand under the chin on the draw side at full draw (about a 29 inch draw)
ARROW_Y = 6           # arrow line, units below the neck (just under the chin)

def archer_hands(f, draw, neck, rel=0.0, aim=0.0):
    """IK targets (figure local units) for a front-on archer drawing correctly: bow arm locked straight and level with
    the arrow, string hand drawn back along the arrow line to the jaw, draw elbow raised behind it on the same line
    (the upper arm points back into depth, so it is drawn foreshortened). rel 0..1 is the follow through after the
    release: the string hand slides back past the jaw."""
    nx, ny = neck
    sh_f = (nx + f * 28, ny + 21)
    y = ny + ARROW_Y
    reach = 74.5
    dy = y - sh_f[1]
    bow = (sh_f[0] + f * math.sqrt(max(1.0, reach * reach - dy * dy)), y)
    hx = lerp(DRAW_START, DRAW_ANCHOR, clamp(draw)) - 18 * rel
    hand = (nx + f * hx, y - 2 * rel)
    J = {'F': bow, 'B': hand}
    # draw elbow: level with the arrow, a forearm length behind the hand, once the draw is under way
    sh_b = (nx - f * 28, ny + 21)
    el_full = (hand[0] - f * 37, y - 1)
    el_low = (lerp(sh_b[0], hand[0], 0.35), sh_b[1] + 26)
    u = clamp(draw * 1.25)
    J['elB'] = (lerp(el_low[0], el_full[0], u), lerp(el_low[1], el_full[1], u))
    if aim:     # shooting high (volleys): the whole draw tilts up about the bow shoulder, form unchanged
        a = -f * aim; ca, sa = math.cos(a), math.sin(a)
        for k_ in ('F', 'B', 'elB'):
            px, py = J[k_][0] - sh_f[0], J[k_][1] - sh_f[1]
            J[k_] = (sh_f[0] + px * ca - py * sa, sh_f[1] + px * sa + py * ca)
    return J

def string_bend(f, grip, hand):
    """Bow bend from the real distance the string is pulled behind the grip (braced 24 units, full draw about 113)."""
    d = math.hypot(grip[0] - hand[0], grip[1] - hand[1])
    return clamp((d - 24) / (113 - 24))

def stuck_arrow(pn, x, y, ang, L=ARROW_L * 0.7, s=1.0):
    """Arrow standing in the ground, shot from the left: nock and fletching up, head buried."""
    ca, sa = math.cos(ang), math.sin(ang)
    nock = (x - ca * L * s, y - sa * L * s)
    pn.line([nock, (x, y)], INK, 5.5 * s); pn.line([nock, (x, y)], SHAFT, 3.2 * s)
    nx, ny = -sa, ca
    q = lambda u, v: (nock[0] + ca * u * s + nx * v * s, nock[1] + sa * u * s + ny * v * s)
    for sd, col in ((-1, FLETCH), (1, FLETCH_D)):
        pn.poly([q(2, 0), q(4, sd * 7), q(16, sd * 6), q(30, sd * 2.2), q(34, 0)], fill=col, outline=INK, width=1.4)
    pn.line([q(-2, 0), q(2, 0)], (60, 46, 34), 4 * s, caps=False)

# ---------------- workshop props ----------------
def log_end(pn, x, y, r, split=0.0, glow_sap=0.0, glow_heart=0.0):
    """End grain of a yew log: bark ring, pale sapwood band, dark heartwood core with growth rings."""
    for sd in ((-1, 1) if split > 0 else (0,)):
        dx = sd * split * 40
        pn.push(x + dx, y, 1.0)
        rng_ = (90, 270) if sd < 0 else ((270, 450) if sd > 0 else (0, 360))
        def wedge(rr, col, outline=None):
            if sd == 0: pn.circ(0, 0, rr, fill=col, outline=outline, width=3 if outline else 0)
            else:
                a0, a1 = rng_; pts = [(0, 0)] + [(math.cos(math.radians(a0 + (a1 - a0) * i / 24)) * rr, math.sin(math.radians(a0 + (a1 - a0) * i / 24)) * rr) for i in range(25)]
                pn.poly(pts, fill=col, outline=outline, width=3 if outline else 0)
        wedge(r, (96, 64, 46), INK)
        wedge(r * 0.9, lerpc(SAP, AMBER, glow_sap))
        wedge(r * 0.66, lerpc(HEART, AMBER, glow_heart))
        for k_ in (0.52, 0.38, 0.24, 0.1):
            if sd == 0: pn.circ(0, 0, r * k_, outline=shade(HEART, 0.25), width=1.6)
            else:
                a0, a1 = rng_
                pn.line([(math.cos(math.radians(a0 + (a1 - a0) * i / 20)) * r * k_, math.sin(math.radians(a0 + (a1 - a0) * i / 20)) * r * k_) for i in range(21)], shade(HEART, 0.25), 1.6, caps=False)
        for k_ in (0.78,):
            if sd == 0: pn.circ(0, 0, r * k_, outline=shade(SAP, 0.12), width=1.4)
        pn.pop()

def log_side(pn, x, y, ln, r, split=0.0):
    """Side of the log on the trestle (bark), drawn behind the end grain at its right end."""
    for sd in ((-1, 1) if split > 0 else (0,)):
        dy = sd * split * 40
        pn.rect(x - ln, y - r + dy * 0.0 + (0 if sd <= 0 else r), x, y + (r if sd >= 0 else 0) + (0 if sd != 0 else 0), fill=(110, 76, 52), outline=INK, width=3)
    rnd = random.Random(3)
    for i in range(10):
        xx = x - ln + 20 + i * ln / 10
        pn.line([(xx, y - r + 8), (xx + rnd.uniform(-6, 6), y + r - 8)], (84, 56, 38), 2.4)

def mallet(pn, hand, elbow, k=1.0):
    """Wooden mallet held at the end of its handle, head beyond the fist along the forearm."""
    hx, hy = hand; ex, ey = elbow
    d = math.hypot(hx - ex, hy - ey) or 1; ux, uy = (hx - ex) / d, (hy - ey) / d
    tip = (hx + ux * 54 * k, hy + uy * 54 * k)
    wood_plank(pn, (hx - ux * 6, hy - uy * 6), tip, 6 * k, WOOD, seed=2, knots=False)
    nx, ny = -uy, ux
    c = (tip[0], tip[1])
    pts = [(c[0] + nx * 22 * k - ux * 10 * k, c[1] + ny * 22 * k - uy * 10 * k), (c[0] + nx * 22 * k + ux * 12 * k, c[1] + ny * 22 * k + uy * 12 * k),
           (c[0] - nx * 22 * k + ux * 12 * k, c[1] - ny * 22 * k + uy * 12 * k), (c[0] - nx * 22 * k - ux * 10 * k, c[1] - ny * 22 * k - uy * 10 * k)]
    pn.poly(pts, fill=WOOD_D, outline=INK, width=2.6)
    pn.line([pts[0], pts[1]], light(WOOD_D, 0.3), 2, caps=False)
    return tip

def wedge(pn, x, y, s=1.0):
    pn.poly([(x - 9 * s, y - 34 * s), (x + 9 * s, y - 34 * s), (x + 2 * s, y + 4 * s), (x - 2 * s, y + 4 * s)], fill=IRON, outline=INK, width=2.4)
    pn.line([(x - 6 * s, y - 30 * s), (x - 1 * s, y)], light(IRON, 0.5), 1.6, caps=False)

def trestle(pn, x, y, w=140, h=120):
    pn.rect(x - w, y, x + w, y + 18, fill=WOOD, outline=INK, width=3)
    for sx in (-w + 20, w - 20):
        pn.line([(x + sx - 16, y + 18), (x + sx - 34, y + h)], INK, 13); pn.line([(x + sx - 16, y + 18), (x + sx - 34, y + h)], WOOD_D, 8)
        pn.line([(x + sx + 16, y + 18), (x + sx + 34, y + h)], INK, 13); pn.line([(x + sx + 16, y + 18), (x + sx + 34, y + h)], WOOD_D, 8)

# ---------------- practice and battle props ----------------
def butt(pn, x, y, s=1.0, hit=()):
    """Archery butt: a turf mound with a round cloth mark pinned to its face."""
    pn.ell(x, y + 4 * s, 120 * s, 18 * s, fill=(30, 22, 14, 70))
    pn.poly([(x - 115 * s, y), (x - 90 * s, y - 80 * s), (x - 40 * s, y - 104 * s), (x + 40 * s, y - 104 * s), (x + 90 * s, y - 80 * s), (x + 115 * s, y)],
            fill=EARTH, outline=INK, width=3)
    pn.poly([(x - 92 * s, y - 78 * s), (x - 40 * s, y - 104 * s), (x + 40 * s, y - 104 * s), (x + 92 * s, y - 78 * s), (x + 60 * s, y - 86 * s), (x - 60 * s, y - 86 * s)], fill=GRASS)
    for i in range(6):
        pn.line([(x - 100 * s + i * 40 * s, y - 20 * s), (x - 80 * s + i * 40 * s, y - 16 * s)], EARTH_D, 2.4)
    cx, cy = x, y - 54 * s
    pn.circ(cx, cy, 30 * s, fill=(240, 234, 216), outline=INK, width=2.6)
    pn.circ(cx, cy, 18 * s, outline=(40, 34, 30), width=3)
    pn.circ(cx, cy, 7 * s, fill=(40, 34, 30))
    pn.line([(cx, cy - 30 * s), (cx, cy - 36 * s)], (60, 46, 34), 3)        # the peg holding the mark
    for (dx, dy, a) in hit:
        stuck_arrow(pn, cx + dx * s, cy + dy * s, a, ARROW_L * 0.55, s)
    return (cx, cy)

def scroll(pn, x, y, w, open_, seal=0.0, lines=6):
    """Parchment proclamation unrolling downward from its top roller, with a red wax seal."""
    h = 300 * open_
    pn.rect(x - w / 2, y, x + w / 2, y + h, fill=(240, 228, 198), outline=INK, width=3)
    if open_ > 0.3:
        for i in range(lines):
            yy = y + 40 + i * 34
            if yy < y + h - 40:
                pn.line([(x - w / 2 + 34, yy), (x + w / 2 - 34 - (i * 37 % 60), yy)], (120, 100, 76), 4, caps=True)
    for yy in (y, y + h):
        pn.rect(x - w / 2 - 16, yy - 12, x + w / 2 + 16, yy + 12, fill=(214, 196, 158), outline=INK, width=3, r=12)
    if seal > 0:
        s = eoback(clamp(seal))
        pn.push(x + w / 2 - 60, y + h - 60, s)
        pn.line([(-10, -20), (-24, 40)], (170, 40, 36), 5); pn.line([(10, -20), (22, 42)], (170, 40, 36), 5)
        pn.circ(0, 0, 30, fill=(176, 40, 36), outline=INK, width=3)
        pn.circ(0, 0, 18, outline=(120, 24, 22), width=3)
        pn.circ(-8, -9, 6, fill=(214, 90, 80))
        pn.pop()

def bunting(pn, x0, x1, y, t, a=1.0):
    if a <= 0: return
    pts = [(lerp(x0, x1, i / 12), y + 30 * math.sin(math.pi * i / 12)) for i in range(13)]
    pn.line(pts, INK, 3)
    cols = [(190, 40, 36), (240, 234, 216), (60, 90, 150)]
    for i in range(12):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        m = ((ax + bx) / 2, (ay + by) / 2 + 30 + 3 * math.sin(t * 4 + i))
        sc = eoback(clamp(a * 1.6 - i * 0.05))
        if sc <= 0: continue
        pn.poly([(ax, ay), (bx, by), (lerp((ax + bx) / 2, m[0], sc), lerp((ay + by) / 2, m[1], sc))], fill=cols[i % 3], outline=INK, width=2)

def skeleton(pn, x, y, k, arm_thick=0.0, hl=0.0, draw=0.0, f=1):
    """Front-on skeleton in the channel's bone style. arm_thick thickens the drawing arm (screen right)."""
    pn.push(x, y, k)
    B = (246, 240, 224); BD = (200, 190, 168)
    def bone(a, b, w, col=B):
        pn.line([a, b], INK, w + 5); pn.line([a, b], col, w)
        for p_ in (a, b):
            pn.circ(p_[0], p_[1], w * 0.75, fill=col, outline=INK, width=2.4)
    # legs
    for sd in (-1, 1):
        bone((sd * 16, -150), (sd * 22, -78), 10); bone((sd * 22, -78), (sd * 24, -6), 9)
        pn.ell(sd * 30, -2, 16, 7, fill=B, outline=INK, width=2.4)
    # pelvis
    pn.poly([(-40, -170), (40, -170), (30, -140), (12, -132), (-12, -132), (-30, -140)], fill=B, outline=INK, width=3)
    pn.circ(0, -150, 9, fill=BD, outline=INK, width=2)
    # spine and ribs
    for i in range(9):
        pn.rect(-6, -180 - i * 14, 6, -170 - i * 14, fill=B, outline=INK, width=2, r=3)
    for i in range(6):
        yy = -228 - i * 15
        for sd in (-1, 1):
            pn.line([(0, yy), (sd * 34, yy + 6), (sd * 38, yy + 18)], INK, 7.5); pn.line([(0, yy), (sd * 34, yy + 6), (sd * 38, yy + 18)], B, 3.6)
    # collarbones and arms
    sh = {-1: (-44, -306), 1: (44, -306)}
    for sd in (-1, 1): bone((sd * 6, -312), sh[sd], 6)
    # back arm hangs; the drawing arm (screen right) can lift toward a draw anchor
    bone(sh[-1], (-56, -238), 9); bone((-56, -238), (-60, -172), 7)
    pn.circ(-60, -166, 8, fill=B, outline=INK, width=2.4)
    el = (lerp(58, 30, draw), lerp(-238, -300, draw)); ha = (lerp(62, -2, draw), lerp(-172, -330, draw))
    col = lerpc(B, AMBER, hl)
    w1 = 9 + 7 * arm_thick; w2 = 7 + 6 * arm_thick
    bone(sh[1], el, w1, col); bone(el, ha, w2, col)
    pn.circ(ha[0], ha[1], 8, fill=col, outline=INK, width=2.4)
    # skull
    pn.circ(0, -362, 40, fill=B, outline=INK, width=3.4)
    pn.rect(-20, -334, 20, -312, fill=B, outline=INK, width=3, r=6)
    for sd in (-1, 1): pn.ell(sd * 15, -366, 10, 12, fill=(46, 38, 32))
    pn.poly([(0, -352), (-5, -342), (5, -342)], fill=(46, 38, 32))
    for i in range(5): pn.line([(-14 + i * 7, -330), (-14 + i * 7, -318)], INK, 1.6, caps=False)
    pn.pop()
    return dict(el=(x + el[0] * k, y + el[1] * k), ha=(x + ha[0] * k, y + ha[1] * k), sh=(x + sh[1][0] * k, y + sh[1][1] * k))

def fleur(pn, x, y, s, col):
    pn.ell(x, y - 10 * s, 5 * s, 14 * s, fill=col)
    for sd in (-1, 1):
        pn.poly([(x, y + 2 * s), (x + sd * 6 * s, y - 14 * s), (x + sd * 15 * s, y - 10 * s), (x + sd * 10 * s, y + 2 * s)], fill=col)
    pn.rect(x - 9 * s, y + 1 * s, x + 9 * s, y + 5 * s, fill=col)
    pn.ell(x, y + 10 * s, 4 * s, 5 * s, fill=col)

def banner_fr(pn, x, y, k, t):
    """French royal banner of 1415: azure, three gold fleurs de lis (France modern), on a lance."""
    pn.line([(x, y), (x, y - 330 * k)], INK, 9 * k); pn.line([(x, y), (x, y - 330 * k)], WOOD, 5 * k)
    pts = []
    for i in range(9):
        u = i / 8
        pts.append((x + 6 * k + u * 150 * k, y - 320 * k + 10 * k * math.sin(t * 4 + u * 4) * u))
    bot = [(px, py + 120 * k + 6 * k * math.sin(t * 4 + 1)) for px, py in pts]
    pn.poly(pts + bot[::-1], fill=(40, 62, 130), outline=INK, width=3)
    G = (232, 184, 60)
    for (u, v) in ((0.3, 0.3), (0.72, 0.3), (0.51, 0.7)):
        i = int(u * 8)
        px = lerp(pts[i][0], bot[i][0], v); py = lerp(pts[i][1], bot[i][1], v)
        fleur(pn, px, py, 1.1 * k, G)

def furrows(pn, y0, t, wet=0.0, scroll_=0.0, x0=-300, x1=1380, bottom=2600):
    """Ploughed field: ridges running toward the horizon, darker and shinier as it gets wet."""
    base = lerpc((138, 110, 74), MUD, wet)
    pn.rect(x0, y0, x1, bottom, fill=base)
    vx = 540
    for i in range(-16, 17):
        xb = vx + i * 150 - scroll_ % 150
        pn.line([(vx + i * 10, y0), (xb, bottom)], lerpc(lerpc((112, 88, 58), MUD_D, wet), INK, 0.1), 7)
        pn.line([(vx + i * 10 + 4, y0), (xb + 30, bottom)], lerpc((160, 132, 92), MUD_WET, wet) + (150,), 3)
    if wet > 0.3:
        rnd = random.Random(6)
        for i in range(14):
            px = rnd.uniform(-60, 1140); py = y0 + rnd.uniform(40, 900)
            s = 0.4 + (py - y0) / 600
            pn.ell(px, py, 40 * s, 9 * s, fill=(150, 156, 160, int(160 * (wet - 0.3) / 0.7)))
            pn.line([(px - 24 * s, py - 2 * s), (px + 6 * s, py - 3 * s)], (220, 226, 230, int(140 * (wet - 0.3) / 0.7)), 2)
    pn.line([(x0, y0), (x1, y0)], lerpc(base, INK, .35), 4, caps=False)

def rain(pn, t, a=1.0, seed=3, n=90, ang=0.18, speed=1900, ln=60):
    if a <= 0.02: return
    rnd = random.Random(seed)
    for i in range(int(n * a)):
        x0 = rnd.uniform(-200, 1280); y0 = rnd.uniform(0, 1920); sp = speed * rnd.uniform(0.8, 1.2)
        y = (y0 + t * sp) % 2100 - 100; x = x0 - (y - y0) * math.tan(ang) * 0.3
        L = ln * rnd.uniform(0.7, 1.2)
        pn.line([(x, y), (x - math.sin(ang) * L, y - math.cos(ang) * L)], (210, 220, 232, int(150 * a)), 3)

def mud_band(pn, y, t, x0=-300, x1=1380, bottom=2600):
    pn.rect(x0, y, x1, bottom, fill=MUD)
    rnd = random.Random(2)
    for i in range(26):
        px = rnd.uniform(x0, x1); py = y + rnd.uniform(10, 500)
        pn.ell(px, py, rnd.uniform(30, 90), rnd.uniform(5, 12), fill=MUD_D + (180,))
        pn.line([(px - 30, py - 4), (px + 10, py - 5)], MUD_WET + (150,), 3)
    pn.line([(x0, y), (x1, y)], lerpc(MUD, INK, .4), 4, caps=False)

def pulley_frame(pn, x, top, ground, k=1.0):
    """Timber hoist frame: two posts, a cross beam and an iron bound pulley wheel."""
    for px in (x - 180 * k, x + 180 * k):
        wood_plank(pn, (px, ground), (px, top), 22 * k, WOOD, seed=int(px) % 7, knots=True)
    wood_plank(pn, (x - 210 * k, top + 6 * k), (x + 210 * k, top + 6 * k), 26 * k, WOOD, seed=4, nails=[20 * k, 400 * k])
    pn.line([(x, top + 18 * k), (x, top + 40 * k)], IRON, 6 * k)
    pn.circ(x, top + 58 * k, 24 * k, fill=WOOD_D, outline=INK, width=3)
    pn.circ(x, top + 58 * k, 24 * k, outline=IRON, width=4)
    pn.circ(x, top + 58 * k, 6 * k, fill=IRON, outline=INK, width=2)
    return (x, top + 58 * k), 24 * k

def counter(pn, x, y, v, label='LB', sz=230):
    """Rolling number readout on a parchment plate."""
    w = 560; h = 300
    pn.rect(x - w / 2 + 10, y - h / 2 + 14, x + w / 2 + 10, y + h / 2 + 14, fill=(0, 0, 0, 80), r=26)
    pn.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=(240, 230, 204), outline=INK, width=6, r=26)
    pn.text(x - 40, y + 6, f'{int(round(v))}', sz, INK, 'Black', 'mm', True)
    pn.text(x + 200, y + 50, label, 70, RUST, 'Black', 'mm', True)

def limb_segment(pn, x, y, Lh, th, bend, t_hl=0.0, c_hl=0.0, f=1):
    """Close up of a bow limb seen from the side, back (sapwood) on top, belly (heartwood) below, bending downward
    at the ends (bend 0..1). Returns centre line points."""
    n = 30
    top, midl, bot, cen = [], [], [], []
    R = 1e9 if bend < 1e-3 else Lh * 1.6 / bend
    for i in range(n + 1):
        u = -1 + 2 * i / n
        s_ = u * Lh
        if bend < 1e-3:
            cx, cy, nx, ny = x + s_, y, 0.0, -1.0
        else:
            a = s_ / R
            cx = x + R * math.sin(a); cy = y + R - R * math.cos(a)
            nx, ny = math.sin(a), -math.cos(a)
        cen.append((cx, cy))
        top.append((cx + nx * th / 2, cy + ny * th / 2))
        midl.append((cx + nx * (th / 2 - th * 0.4), cy + ny * (th / 2 - th * 0.4)))
        bot.append((cx - nx * th / 2, cy - ny * th / 2))
    pn.poly(top + midl[::-1], fill=lerpc(SAP, AMBER, t_hl))
    pn.poly(midl + bot[::-1], fill=lerpc(HEART, AMBER, c_hl))
    # fibres: spacing opens up in the stretched back, squeezes in the belly
    for j in range(1, 4):
        q = [(lerp(top[i][0], midl[i][0], j / 4), lerp(top[i][1], midl[i][1], j / 4)) for i in range(n + 1)]
        pn.line(q, shade(SAP, 0.18), 1.6, caps=False)
    for j in range(1, 6):
        q = [(lerp(midl[i][0], bot[i][0], j / 6), lerp(midl[i][1], bot[i][1], j / 6)) for i in range(n + 1)]
        pn.line(q, shade(HEART, 0.25), 1.6, caps=False)
    pn.line(midl, lerpc(HEART, SAP, 0.4), 2, caps=False)
    pn.poly(top + bot[::-1], outline=INK, width=4)
    return dict(top=top, mid=midl, bot=bot, cen=cen)

def double_arrow(pn, a, b, col, w=8, head=24, out=True):
    """Two headed arrow: heads pointing outward (stretching) or inward (crushing)."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    for p in (a, b):
        if out:
            s, e = (mx, my), p
        else:
            s, e = p, (lerp(p[0], mx, 0.82), lerp(p[1], my, 0.82))
        pn.line([s, e], col, w)
        ang = math.atan2(e[1] - s[1], e[0] - s[0])
        pn.poly([(e[0] + math.cos(ang) * 10, e[1] + math.sin(ang) * 10), (e[0] - head * math.cos(ang - .5), e[1] - head * math.sin(ang - .5)),
                 (e[0] - head * math.cos(ang + .5), e[1] - head * math.sin(ang + .5))], fill=col, outline=INK, width=2)

# ---------------- environments ----------------
def env_green():
    """English village green: soft autumn sky, low hills, a stone church tower, hedges."""
    im = E.sky((138, 166, 196), (240, 226, 196), (40, 24, 0), 0.5)
    E.clouds(im, 21, (255, 250, 240, 150))
    E.hill_layer(im, 1010, 50, (128, 138, 150), 4)
    E.hill_layer(im, 1110, 30, (132, 142, 104), 9, freqs=(1.4, 3.3, 6.0))
    d = ImageDraw.Draw(im)
    # church: nave and square tower with battlements
    d.rectangle([700, 990, 900, 1110], fill=(150, 144, 130)); d.polygon([(690, 990), (800, 930), (910, 990)], fill=(120, 96, 80))
    d.rectangle([880, 880, 960, 1110], fill=(160, 154, 140))
    for i in range(4): d.rectangle([880 + i * 22, 866, 892 + i * 22, 882], fill=(160, 154, 140))
    d.rectangle([910, 930, 930, 960], fill=(70, 60, 56))
    for x in range(-20, W + 40, 70):      # hedgerow
        d.ellipse([x, 1110, x + 90, 1160], fill=(92, 110, 70))
    E.hill_layer(im, 1180, 10, (138, 146, 88), 2, freqs=(1.5, 4.0))
    return E.grade(im, blur=3, sat=0.85, bright=1.02)

def env_workshop():
    """Bowyer's workshop: timber wall, staves seasoning on pegs, a window of daylight."""
    im = Image.new('RGBA', (W, H), (96, 70, 48, 255)); d = ImageDraw.Draw(im)
    for x in range(0, W, 120):
        d.rectangle([x, 0, x + 118, 1250], fill=(108 + (x // 120 % 2) * 8, 80, 54))
        d.line([(x, 0), (x, 1250)], fill=(66, 46, 30), width=4)
    d.rectangle([90, 300, 380, 640], fill=(226, 216, 186)); d.line([(235, 300), (235, 640)], fill=(80, 60, 40), width=10)
    d.line([(90, 470), (380, 470)], fill=(80, 60, 40), width=10)
    for i in range(7):                    # staves on pegs
        x = 520 + i * 70
        d.line([(x, 220), (x + 8, 1000)], fill=(214, 186, 132), width=16)
        d.line([(x - 4, 220), (x + 4, 1000)], fill=(176, 100, 60), width=7)
    d.rectangle([480, 210, 1040, 226], fill=(70, 50, 34))
    d.rectangle([0, 1250, W, H], fill=(124, 98, 70))
    for i in range(12): d.line([(0, 1250 + i * 60), (W, 1250 + i * 60)], fill=(108, 84, 58), width=3)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.polygon([(90, 300), (380, 300), (900, 1500), (300, 1600)], fill=(255, 240, 200, 50))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
    return E.grade(im, blur=4, sat=0.8, bright=0.96)

def env_lab():
    """Finds store: dark shelves of boxes behind a pale light table."""
    im = Image.new('RGBA', (W, H), (60, 58, 62, 255)); d = ImageDraw.Draw(im)
    for r in range(6):
        y = 160 + r * 190
        d.rectangle([0, y + 150, W, y + 166], fill=(110, 92, 70))
        for c in range(9):
            x = 20 + c * 118 + (r * 37) % 40
            d.rectangle([x, y + 60, x + 96, y + 150], fill=(176, 160, 128) if (r + c) % 3 else (150, 136, 110))
            d.rectangle([x + 30, y + 90, x + 66, y + 110], fill=(236, 228, 210))
    return E.grade(im, blur=5, sat=0.7, bright=0.8)

def env_agin():
    """Agincourt, late October: grey sky, the narrow open field between two woods."""
    im = E.sky((150, 156, 166), (214, 206, 190), (20, 14, 6), 0.5)
    E.clouds(im, 31, (236, 234, 230, 170), n=10)
    E.hill_layer(im, 1030, 26, (134, 136, 132), 5, freqs=(1.0, 2.6, 6.0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for side in (0, 1):                   # the woods of Agincourt and Tramecourt framing the field
        for i in range(26):
            x = (rnd.uniform(-60, 330) if side == 0 else rnd.uniform(750, 1140)); y = 1060 + rnd.uniform(-30, 50)
            r = rnd.uniform(50, 90)
            d.ellipse([x - r, y - r * 1.3, x + r, y + r * 0.4], fill=(74, 86, 62) if i % 2 else (88, 98, 70))
    E.hill_layer(im, 1120, 8, (118, 110, 80), 2, freqs=(1.5, 4.0))
    return E.grade(im, blur=3, sat=0.8, bright=0.98)

def env_aginrain():
    im = E.sky((92, 98, 112), (150, 148, 146), None, 0.5)
    E.clouds(im, 33, (120, 122, 130, 190), n=12)
    E.hill_layer(im, 1030, 26, (96, 100, 104), 5, freqs=(1.0, 2.6, 6.0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for side in (0, 1):
        for i in range(26):
            x = (rnd.uniform(-60, 330) if side == 0 else rnd.uniform(750, 1140)); y = 1060 + rnd.uniform(-30, 50)
            r = rnd.uniform(50, 90)
            d.ellipse([x - r, y - r * 1.3, x + r, y + r * 0.4], fill=(52, 62, 48) if i % 2 else (62, 72, 54))
    E.hill_layer(im, 1120, 8, (90, 82, 62), 2, freqs=(1.5, 4.0))
    return E.grade(im, blur=3, sat=0.75, bright=0.9)

for _n in ('green', 'workshop', 'lab', 'agin', 'aginrain'):
    setattr(E, 'env_' + _n, globals()['env_' + _n])

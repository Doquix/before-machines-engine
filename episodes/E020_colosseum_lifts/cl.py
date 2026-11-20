"""E020 Colosseum hypogeum lifts: props (capstan, lift shaft and cage, trap door ramp, arena floor, venabulum, torch,
big cats), Roman outfits, environments (arena, hypogeum, cavea). Period library BM-P022 to BM-P033."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import env as E
from detail import shade, light, wood_plank, rivet, rope, scratches, lod, thin_ok

SAND = (214, 186, 132); SAND_D = (182, 152, 100); BRICK = (156, 92, 66); TUFA = (176, 160, 128)
OAK = (126, 88, 52); OAK_L = (156, 114, 70); FUR = (204, 150, 72); FUR_D = (150, 100, 44); MANE = (96, 60, 34)
TIGER = (226, 128, 44)

# ---------------- outfits (BM-P029, BM-P030) ----------------
OUT.update({
    # the Keeper: Roman civilian tunic, round glasses kept
    'rkeeper': dict(tunic=(170, 140, 96), sleeve=(170, 140, 96), hose=(240, 232, 214), boot=(96, 66, 40), hat=None,
                    hair=(70, 52, 38), hair_style='crop', glasses=True, nose='button', ears=True, hem=(120, 92, 60)),
    # capstan crew: labourers, mixed origins as in the city of Rome; exomis and patched tunics, varied hair and beards
    'operae':  dict(tunic=(222, 212, 186), sleeve=(222, 212, 186), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, exomis=True,
                    skin=(226, 192, 152), hair=(46, 34, 26), hair_style='curly', beard=(46, 34, 26), beard_style='chinstrap',
                    nose='broad', age=0.3, ears=True, patches=True),
    'operae2': dict(tunic=(150, 82, 60), sleeve=(150, 82, 60), hose=(240, 232, 214), boot=(110, 80, 50), hat=None,
                    skin=(240, 214, 184), hair=(156, 150, 140), hair_style='receding', beard=(156, 150, 140), beard_style='goatee',
                    nose='long', age=0.9, ears=True, sash=(196, 160, 90)),
    'operae3': dict(tunic=(118, 100, 78), sleeve=(118, 100, 78), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, exomis=True,
                    skin=(150, 104, 72), hair=(30, 22, 18), hair_style='bald', nose='broad', scar=True, ears=True, age=0.4),
    'operae4': dict(tunic=(108, 122, 138), sleeve=(108, 122, 138), hose=(240, 232, 214), boot=(110, 80, 50), hat=None,
                    skin=(246, 222, 196), hair=(150, 80, 44), hair_style='tousled', nose='button', cheeks=(230, 130, 110), mole=True),
    'operae5': dict(tunic=(196, 170, 120), sleeve=(196, 170, 120), hose=(240, 232, 214), boot=(110, 80, 50), hat=None,
                    skin=(214, 172, 128), hair=(36, 28, 22), hair_style='long', nose='hook', ears=True, hem=(140, 70, 50)),
    'operae6': dict(tunic=(132, 140, 104), sleeve=(132, 140, 104), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, exomis=True,
                    skin=(176, 128, 92), hair=(28, 22, 18), hair_style='curly', beard=(28, 22, 18), beard_style='goatee', nose='broad', age=0.6),
    'operae7': dict(tunic=(232, 222, 200), sleeve=(232, 222, 200), hose=(240, 232, 214), boot=(110, 80, 50), hat=None,
                    skin=(250, 228, 204), hair=(196, 160, 96), hair_style='crop', nose='long', cheeks=(230, 140, 120), ears=True, patches=True),
    'operae8': dict(tunic=(96, 76, 60), sleeve=(96, 76, 60), hose=(240, 232, 214), boot=(110, 80, 50), hat=None,
                    skin=(236, 206, 170), hair=(110, 108, 104), hair_style='grey_temples', beard=(110, 108, 104), beard_style='mustache',
                    nose='button', age=0.8, scar=True, sash=(150, 60, 50)),
    # venator: belted tunic above the knee with clavi, leg wrappings drawn by leg_wraps()
    'venator': dict(tunic=(196, 178, 140), sleeve=(196, 178, 140), hose=(240, 232, 214), boot=(96, 66, 40), hat=None,
                    skin=(232, 200, 160), hair=(60, 44, 30), hair_style='fringe', clavi=(140, 60, 44), nose='hook', scar=True, age=0.35,
                    beard=(60, 44, 30), beard_style='chinstrap', ears=True),
})
EPISODE_OUTFIT = 'rkeeper'
WRAP = (176, 150, 108)

def leg_wraps(pn, x, y, k, J):
    """Venator fasciae: bands bound round the shin below the knee (Velleia cippus, Thelepte mosaic)."""
    pn.push(x, y, k)
    for s in ('F', 'B'):
        kx, ky = J['knee' + s]; fx, fy = J['foot' + s]
        for i in range(5):
            u = 0.12 + i * 0.17
            cx, cy = lerp(kx, fx, u), lerp(ky, fy, u)
            pn.line([(cx - 7.5, cy - 2), (cx + 7.5, cy + 2)], INK, 6.5, caps=False)
            pn.line([(cx - 6.5, cy - 2), (cx + 6.5, cy + 2)], WRAP, 4, caps=False)
    pn.pop()

# ---------------- venabulum (BM-P031) and the venator ----------------
VEN_L = 300
def venabulum(pn, hx, hy, ang, back=70, L=VEN_L, w=6.0):
    """Hunting spear through grip (hx, hy) at angle ang (radians, screen). Leaf head and a small cross lug."""
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
    butt = (hx - ux * back, hy - uy * back); tip = (hx + ux * (L - back), hy + uy * (L - back))
    hb = (tip[0] - ux * 46, tip[1] - uy * 46)
    wood_plank(pn, butt, hb, w, OAK_L, seed=5, knots=False, outline=2.6)
    sock = (hb[0] - ux * 14, hb[1] - uy * 14)
    pn.line([sock, (hb[0] + ux * 4, hb[1] + uy * 4)], INK, w + 4); pn.line([sock, (hb[0] + ux * 4, hb[1] + uy * 4)], IRON, w + 0.5)
    lug = (hb[0] - ux * 2, hb[1] - uy * 2)
    pn.line([(lug[0] - nx * 11, lug[1] - ny * 11), (lug[0] + nx * 11, lug[1] + ny * 11)], INK, 5.5)
    pn.line([(lug[0] - nx * 10, lug[1] - ny * 10), (lug[0] + nx * 10, lug[1] + ny * 10)], IRON, 3)
    q = lambda u, v: (hb[0] + ux * u + nx * v, hb[1] + uy * u + ny * v)
    blade = [q(2, 0), q(14, 9.5), q(30, 7), tip, q(30, -7), q(14, -9.5)]
    pn.poly(blade, fill=(150, 154, 162), outline=INK, width=2.6)
    pn.poly([q(4, 0), q(14, 8), q(30, 5.5), tip], fill=light(IRON, 0.45))
    pn.line([q(4, 0), tip], shade(IRON, 0.3), 1.6, caps=False)
    return dict(tip=tip, butt=butt)

def spear_hands(f, ang=0.25, lift=0.0):
    """Both hands on the shaft, low and forward: right (back) hand near the hip, left (front) hand a forearm ahead."""
    bx, by = -f * 4, -86 - lift
    return {'B': (bx, by), 'F': (bx + f * 50 * math.cos(ang), by + 50 * math.sin(ang))}

def venator(pn, x, y, k, f=1, t=0.0, p=None, ang=0.25, expr='determined', look=(0.8, 0.1), spear=True, blink=None, lift=0.0):
    p = p or pose('brace', torso=8)
    p = dict(p); p['torso'] += 1.0 * math.sin(t * 2.1 + x * 0.01)
    hands = spear_hands(f, ang, lift) if spear else None
    a_ = math.atan2(hands['F'][1] - hands['B'][1], hands['F'][0] - hands['B'][0]) if spear else 0
    def held(pn_, J):
        g = J['haB']; venabulum(pn_, g[0], g[1], a_, back=78)
    J = figure(pn, x, y, k, f, p, 'venator', expr, look=look, blink=blink_at(t, x * .01) if blink is None else blink,
               hands=hands, held=held if spear else None)
    leg_wraps(pn, x, y, k, J)
    return J

# ---------------- capstan crew grip (BM-P023) ----------------
def push_hands(f, h=-150):
    """Both hands on one capstan bar at chest height in front of the body, palms forward."""
    return {'F': (f * 46, h + 4), 'B': (f * 34, h + 10)}
PUSH = dict(torso=22, head=-14, uaF=70, faF=95, uaB=60, faB=90, thF=26, shF=-8, thB=-26, shB=-22)

def walk_push(ph):
    """Driving walk while leaning into the bar: legs cycle, torso stays forward (weight into the push)."""
    s = math.sin(ph * 2 * math.pi)
    p = dict(PUSH); p['thF'] = 6 + 24 * s; p['thB'] = -6 - 24 * s
    p['shF'] = -18 + 10 * max(0, -s); p['shB'] = -18 + 10 * max(0, s); p['torso'] = 22 + 2 * math.cos(ph * 4 * math.pi)
    return p

def pusher(pn, x, y, k, f=1, ph=0.0, out='operae', expr='determined', t=0.0, bar_h=-150):
    def held(pn_, J): pass
    return figure(pn, x, y, k, f, walk_push(ph), out, expr, look=(0.9, 0.0), blink=blink_at(t, x * .02), hands=push_hands(f, bar_h), held=held)

# ---------------- capstan (BM-P023) ----------------
def capstan(pn, x, yf, k=1.0, ang=0.0, levels=2, lvl_h=300, rope_turns=0.0, bar_len=150, show_front=None):
    """Side view of a two story capstan standing at floor yf. Bars rotate about the vertical post (ang radians).
    show_front: callable(level_index, depth) to draw figures between back and front bars."""
    pn.push(x, yf, k)
    top = -levels * lvl_h - 60
    # post with an iron collar at the floor hole
    pn.rect(-17, top, 17, 0, fill=OAK, outline=INK, width=3.2)
    pn.rect(-14, top + 4, -6, -4, fill=light(OAK, 0.2))
    pn.rect(8, top + 4, 14, -4, fill=shade(OAK, 0.25))
    for yy in range(int(top) + 40, -10, 70):
        pn.line([(-12, yy), (-4, yy + 26)], shade(OAK, 0.35), 1.6, caps=False)
    pn.rect(-22, -16, 22, 0, fill=IRON, outline=INK, width=2.6); pn.rect(-20, -14, -8, -10, fill=light(IRON, .4))
    # rope drum between the levels with wound turns
    dy0, dy1 = -lvl_h + 40, -lvl_h + 150
    pn.rect(-30, dy0 - 160, 30, dy0 - 40, fill=OAK_L, outline=INK, width=3)
    n = int(4 + 8 * clamp(rope_turns))
    for i in range(n):
        yy = dy0 - 50 - i * 9
        pn.line([(-29, yy), (29, yy - 4)], INK, 6.5, caps=False); pn.line([(-28, yy), (28, yy - 4)], ROPE, 4, caps=False)
    for i in range(1, levels):     # upper working floor: planks on a beam, the post passes through
        fy = -i * lvl_h
        for a, b in ((-260, -24), (24, 260)):
            wood_plank(pn, (a, fy), (b, fy), 16, OAK, seed=20 + i, outline=2.6, knots=False)
    for i in range(levels):
        yb = -i * lvl_h - 150
        bars = []
        for j in range(4):
            a = ang + j * math.pi / 2
            bars.append((math.sin(a), math.cos(a)))
        back_ = [b for b in bars if b[0] < 0]; front_ = [b for b in bars if b[0] >= 0]
        def bar(c):
            ex = c[1] * bar_len; dd = c[0]
            w = 11 + 3 * dd
            col = lerpc(OAK, shade(OAK, .35), 0.5 - 0.5 * dd)
            pn.line([(0, yb), (ex, yb + 6 * dd)], INK, w + 4.5); pn.line([(0, yb), (ex, yb + 6 * dd)], col, w)
            pn.circ(ex, yb + 6 * dd, w * 0.55, fill=shade(col, .2), outline=INK, width=2)
        for c in back_: bar(c)
        if show_front:
            cur = pn.T; pn.T = pn.stack[-1]; show_front(i, -1); pn.T = cur
        # iron through-pin band where the bars pass the post
        pn.rect(-19, yb - 12, 19, yb + 12, fill=IRON, outline=INK, width=2.4)
        for c in front_: bar(c)
        if show_front:
            cur = pn.T; pn.T = pn.stack[-1]; show_front(i, 1); pn.T = cur
    pn.pop()

# ---------------- shaft, cage, trap door (BM-P024, BM-P025) ----------------
def lift_shaft(pn, x, ytop, ybot, w=230, seed=2):
    """Masonry shaft walls with guide grooves (section view: back wall shown)."""
    pn.rect(x - w / 2, ytop, x + w / 2, ybot, fill=shade(TUFA, 0.45))
    rnd = random.Random(seed)
    for row, yy in enumerate(np.arange(ytop, ybot, 34)):
        off = (row % 2) * 30
        for xx in np.arange(x - w / 2 - off, x + w / 2, 60):
            x0, x1 = max(x - w / 2, xx + 2), min(x + w / 2, xx + 58)
            if x1 - x0 > 4:
                pn.rect(x0, yy + 2, x1, min(ybot, yy + 32), fill=lerpc(shade(BRICK, 0.35), shade(TUFA, 0.4), rnd.random() * .6))
    for sx in (-1, 1):
        gx = x + sx * (w / 2 - 14)
        pn.rect(gx - 7, ytop, gx + 7, ybot, fill=shade(TUFA, 0.7))
        pn.rect(x + sx * w / 2 - 3, ytop, x + sx * w / 2 + 3, ybot, fill=INK)

def pulley(pn, x, y, r=22, ang=0.0):
    pn.circ(x, y, r, fill=OAK_L, outline=INK, width=3)
    pn.circ(x, y, r * 0.35, fill=IRON, outline=INK, width=2)
    for j in range(3):
        a = ang + j * 2 * math.pi / 3
        pn.line([(x + math.cos(a) * r * .4, y + math.sin(a) * r * .4), (x + math.cos(a) * r * .9, y + math.sin(a) * r * .9)], shade(OAK, .3), 2.4, caps=False)

def lift_cage(pn, x, yb, k=1.0, gate=0.0, inside=None, seed=1):
    """Wooden cage, bottom centre at (x, yb). 220 wide, 150 tall at k=1. gate 0..1 lifts the front bars.
    inside(pn) draws the animal behind the bars."""
    pn.push(x, yb, k)
    W2, Hc = 110, 150
    pn.rect(-W2, -Hc, W2, 0, fill=(44, 34, 26))                          # dark interior
    wood_plank(pn, (-W2, -Hc), (-W2, 0), 16, OAK, seed=seed, knots=False, outline=2.8)  # back posts read as frame
    if inside: inside(pn)
    for (a, b) in (((-W2, -Hc), (W2, -Hc)), ((-W2, 0), (W2, 0))):
        wood_plank(pn, a, b, 18, OAK, seed=seed + 3, outline=2.8, nails=[14, 2 * W2 - 14])
    for sx in (-W2, W2):
        wood_plank(pn, (sx, -Hc - 8), (sx, 8), 18, OAK_L, seed=seed + 5, knots=False, outline=2.8)
    gy = -Hc * clamp(gate) * 0.95
    for i in range(7):
        bx = -W2 + 26 + i * (2 * W2 - 52) / 6
        pn.line([(bx, -Hc + 8 + gy), (bx, -8 + gy)], INK, 9); pn.line([(bx, -Hc + 8 + gy), (bx, -8 + gy)], OAK_L, 5.5)
    pn.line([(-W2 + 14, -Hc / 2 + gy), (W2 - 14, -Hc / 2 + gy)], INK, 9, caps=False)
    pn.line([(-W2 + 14, -Hc / 2 + gy), (W2 - 14, -Hc / 2 + gy)], IRON, 5, caps=False)
    for sx in (-W2, W2):
        for yy in (-Hc + 4, -4):
            rivet(pn, sx, yy, 4.2, IRON)
    # rope sling to the top centre
    rope(pn, [(-W2 + 8, -Hc), (0, -Hc - 60), (W2 - 8, -Hc)], 4.5)
    pn.pop()
    return (x, yb - (Hc + 60) * k)

def trapdoor(pn, xh, yf, w=200, op=0.0, f=1, th=16):
    """Hinged trap door. Hinge at (xh, yf); closed it lies along the floor toward +f; op 0..1 swings it down to ~60 deg
    (a ramp). Returns the free end point."""
    a = math.radians(62) * eoback(clamp(op), 1.2) if op > 0 else 0.0
    ux, uy = f * math.cos(a), math.sin(a)
    end = (xh + ux * w, yf + uy * w)
    wood_plank(pn, (xh, yf + th / 2 * math.cos(a)), (end[0], end[1] + th / 2 * math.cos(a)), th, OAK_L, seed=11, outline=2.8,
               nails=[w * 0.2, w * 0.8])
    for u in (0.25, 0.75):   # battens underneath
        bx, by = xh + ux * w * u, yf + uy * w * u
        pn.line([(bx, by + th * 0.6), (bx + 6 * f, by + th * 1.4)], INK, 7)
    pn.circ(xh, yf, 7, fill=IRON, outline=INK, width=2)
    return end

def arena_floor(pn, y, x0=-60, x1=1140, gap=None, depth=40, seed=4):
    """Section through the arena floor: sand on boards on beams. gap=(gx0, gx1) leaves an opening."""
    segs = [(x0, x1)] if not gap else [(x0, gap[0]), (gap[1], x1)]
    for a, b in segs:
        if b - a < 2: continue
        pn.rect(a, y + 12, b, y + depth, fill=OAK, outline=INK, width=2.6)
        for xx in np.arange(a + 30, b - 10, 80):
            pn.line([(xx, y + 14), (xx, y + depth - 2)], shade(OAK, .35), 2, caps=False)
        pn.rect(a, y - 4, b, y + 12, fill=SAND, outline=INK, width=2.6)
        rnd = random.Random(seed + int(a))
        for _ in range(int((b - a) / 25)):
            pn.circ(rnd.uniform(a + 4, b - 4), y + rnd.uniform(-1, 9), rnd.uniform(1, 2.2), fill=SAND_D)

def torch(pn, x, y, t=0.0, s=1.0):
    pn.push(x, y, s)
    pn.line([(0, 0), (-14, 40)], INK, 12); pn.line([(0, 0), (-14, 40)], OAK, 8)
    pn.rect(-9, -6, 9, 6, fill=IRON, outline=INK, width=2)
    fl = 1 + 0.12 * math.sin(t * 17) + 0.08 * math.sin(t * 29 + 1)
    pn.ell(0, -30 * fl, 15, 30 * fl, fill=(240, 120, 40, 230))
    pn.ell(0, -22 * fl, 8, 18 * fl, fill=(255, 214, 120, 240))
    pn.pop()

# ---------------- big cats (BM-P027, BM-P028): detailed 2D, anatomy first ----------------
def _cr(pts, n=6):
    """Closed Catmull-Rom spline through control points."""
    out = []; m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for j in range(n):
            t = j / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                     (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    return out

def _open_cr(pts, n=6):
    out = []
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for j in range(n):
            t = j / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                     (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1]); return out

def _quad(a, b, w0, w1):
    dx, dy = b[0] - a[0], b[1] - a[1]; L_ = math.hypot(dx, dy) or 1; nx, ny = -dy / L_, dx / L_
    return [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
            (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]

def _grow(poly, cx, cy, g):
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy; L_ = math.hypot(dx, dy) or 1
        out.append((x + dx / L_ * g, y + dy / L_ * g))
    return out

def _leg_chain(base, segs, s):
    """segs: (angle deg from straight down, + = forward, length, w0, w1). Returns joint list."""
    pts = [base]; x, y = base
    for a, l, _, _ in segs:
        r = math.radians(a); x += s * math.sin(r) * l; y += math.cos(r) * l; pts.append((x, y))
    return pts

def _draw_leg(pn, pts, segs, col, s, paw=True, claws=False, shade_k=0.0):
    c = shade(col, shade_k) if shade_k else col
    shapes = []
    for (a, b), (_, _, w0, w1) in zip(zip(pts[:-1], pts[1:]), segs):
        shapes.append(('q', _quad(a, b, w0, w1), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
        shapes.append(('c', b, w1 / 2))
    shapes.insert(0, ('c', pts[0], segs[0][2] / 2))
    px, py = pts[-1]
    pw = segs[-1][3] * 0.95
    paw_pts = _cr([(px - s * pw * .55, py - pw * .25), (px + s * pw * 0.4, py - pw * .55), (px + s * pw * 1.25, py - pw * .3),
                   (px + s * pw * 1.35, py + pw * .02), (px - s * pw * .5, py + pw * .05)], 4)
    for kind, g in ((0, 2.8), (1, 0)):
        cc = INK if kind == 0 else c
        for sh in shapes:
            if sh[0] == 'q': pn.poly(_grow(sh[1], *sh[2], g) if g else sh[1], fill=cc)
            else: pn.circ(sh[1][0], sh[1][1], sh[2] + g, fill=cc)
        if paw: pn.poly(_grow(paw_pts, px + s * pw * .4, py - pw * .2, g) if g else paw_pts, fill=cc)
    if paw:
        for i in range(3):
            tx = px + s * pw * (0.45 + i * 0.3)
            pn.line([(tx, py - pw * 0.05), (tx - s * 2, py - pw * 0.32)], shade(c, 0.4), 1.6, caps=False)
        if claws:
            for i in range(3):
                tx = px + s * pw * (0.6 + i * 0.28)
                pn.poly([(tx, py), (tx + s * 7, py + 3), (tx + s * 1, py + 4)], fill=(244, 238, 224), outline=INK, width=1.2)
    # light along the front edge of the upper segment
    a, b = pts[0], pts[1]
    pn.line([(lerp(a[0], b[0], .15) + s * segs[0][2] * .28, lerp(a[1], b[1], .15)), (lerp(a[0], b[0], .8) + s * segs[0][3] * .28, lerp(a[1], b[1], .8))],
            light(c, 0.25) + (200,), max(2, segs[0][3] * 0.18))

GAITS = {
    # (front: upper, forearm, paw) (hind: thigh, shank, metatarsus) per leg: near front, far front, near hind, far hind
    'stand': lambda ph: ([(-12, 4), (-4, 10)], [(28, -38, 6), (20, -30, 10)]),
    'crouch': lambda ph: ([(-50, 20), (-42, 26)], [(70, -40, 40), (64, -36, 44)]),
    'sit': lambda ph: ([(-6, 2), (2, 4)], [(80, -80, 88), (78, -78, 86)]),
    'lie': lambda ph: ([(84, 92), (78, 88)], [(-84, -90, -92), (-78, -86, -90)]),
}
def _gait(gait, ph):
    if gait in GAITS: return GAITS[gait](ph)
    c = math.sin(ph * 2 * math.pi); c2 = math.sin(ph * 2 * math.pi + 1.2)
    if gait == 'run':
        fn = [(-10 + 48 * c, -6 + 40 * max(0, -c) + 30 * c), (-10 - 48 * c2, -6 + 40 * max(0, c2) - 30 * c2)]
        hn = [(30 - 50 * c, -40 - 30 * max(0, c), 10 + 40 * max(0, -c)), (30 + 50 * c2, -40 - 30 * max(0, -c2), 10 + 40 * max(0, c2))]
        return fn, hn
    if gait == 'leap':
        e = clamp(ph)
        fn = [(lerp(-40, 70, e), lerp(30, 20, e)), (lerp(-30, 76, e), lerp(26, 18, e))]
        hn = [(lerp(70, -40, e), lerp(-40, -10, e), lerp(40, -30, e)), (lerp(64, -36, e), lerp(-36, -14, e), lerp(44, -26, e))]
        return fn, hn
    return GAITS['stand'](ph)

def bigcat(pn, x, y, k=1.0, f=1, gait='stand', ph=0.0, striped=False, mane=True, look=(0.8, 0.0), expr='neutral', t=0.0,
           crouch=0.0, body_tilt=0.0, mouth=None):
    """Lion (dark Barbary style mane) or tiger, about 290 units long, feet at y. gait: stand, crouch, sit, run (ph), leap (ph).
    expr: neutral, angry, roar. body_tilt (radians) pitches the whole cat (leaps, climbing a ramp)."""
    s = f
    col = TIGER if striped else FUR
    belly = (246, 236, 214) if striped else (236, 206, 150)
    dkc = shade(col, 0.22)
    fn, hn = _gait(gait, ph)
    if crouch: fn, hn = [(lerp(a, b, crouch), lerp(c_, d_, crouch)) for (a, c_), (b, d_) in zip(fn, _gait('crouch', 0)[0])], \
                        [(lerp(a, b, crouch), lerp(c_, d_, crouch), lerp(e_, g_, crouch)) for (a, c_, e_), (b, d_, g_) in zip(hn, _gait('crouch', 0)[1])]
    SH = (s * 64, -104); HP = (-s * 82, -98)
    fsegs = lambda a: [(a[0], 50, 36, 25), (a[1], 50, 24, 16)]
    hsegs = lambda a: [(a[0], 46, 46, 26), (a[1], 42, 22, 14), (a[2], 30, 14, 13)]
    legs = [('ff', _leg_chain((SH[0] - s * 12, SH[1] + 6), fsegs(fn[1]), s), fsegs(fn[1])),
            ('hf', _leg_chain((HP[0] + s * 10, HP[1] + 4), hsegs(hn[1]), s), hsegs(hn[1])),
            ('hn', _leg_chain(HP, hsegs(hn[0]), s), hsegs(hn[0])),
            ('fn', _leg_chain(SH, fsegs(fn[0]), s), fsegs(fn[0]))]
    low = max(p[-1][1] for _, p, _ in legs) if gait not in ('leap',) else 0.0
    bob = 0.0
    if gait == 'leap': bob = -60 * math.sin(clamp(ph) * math.pi)
    pn.push(x, y, k)
    if body_tilt: pass
    rot_ = lambda p: rot(p[0], p[1], 0, -80, body_tilt * s) if body_tilt else p
    T_ = lambda p: (rot_(p)[0], rot_(p)[1] - low + bob)
    # contact shadow
    if gait != 'leap' and not body_tilt: pn.ell(0, 2, 150, 12, fill=(20, 14, 10, 60))
    # tail: tapered with a dark tuft, swings with time
    sw = math.sin(t * 2.4 + ph * 6)
    tl = _open_cr([T_((-s * 112, -100)), T_((-s * 150, -96 + 10 * sw)), T_((-s * 176, -70 + 22 * sw)), T_((-s * 186, -40 + 30 * sw))], 6)
    for i, (a, b) in enumerate(zip(tl[:-1], tl[1:])):
        w = 13 - i * 0.45
        pn.line([a, b], INK, w + 5)
    for i, (a, b) in enumerate(zip(tl[:-1], tl[1:])):
        w = 13 - i * 0.45
        pn.line([a, b], col if not striped or (i // 3) % 2 == 0 else INK, w)
    pn.ell(tl[-1][0], tl[-1][1] + 6, 9, 13, fill=MANE if not striped else INK, outline=INK, width=2)
    # far legs (shaded)
    for nm, pts, sg in legs[:2]:
        _draw_leg(pn, [T_(p) for p in pts], sg, col, s, claws=(gait == 'leap'), shade_k=0.28)
    # torso
    ctrl = [(100, -84), (84, -124), (52, -134), (14, -122), (-30, -118), (-74, -126), (-112, -116), (-128, -90), (-112, -60),
            (-74, -52), (-20, -50), (36, -54), (78, -62)]
    if crouch: ctrl = [(cx_, cy_ + 10 * crouch) for cx_, cy_ in ctrl]
    body = [T_((s * px_, py_)) for px_, py_ in _cr(ctrl, 6)]
    pn.poly(body, fill=col, outline=INK, width=3.4)
    # underside cream band and back shadow
    under = [T_((s * px_, py_)) for px_, py_ in _open_cr([(-110, -66), (-70, -56), (-20, -54), (36, -58), (80, -66), (96, -82)], 5)]
    under2 = [T_((s * px_, py_)) for px_, py_ in _open_cr([(96, -78), (40, -68), (-20, -66), (-70, -68), (-104, -76)], 5)]
    pn.poly(under + under2, fill=belly)
    topl = [T_((s * px_, py_)) for px_, py_ in _open_cr([(78, -126), (52, -131), (14, -119), (-30, -115), (-74, -122), (-108, -113)], 5)]
    topl2 = [T_((s * px_, py_)) for px_, py_ in _open_cr([(-104, -105), (-74, -112), (-30, -106), (14, -110), (52, -120), (76, -116)], 5)]
    pn.poly(topl + topl2, fill=dkc)
    # muscle and rib lines, fur strokes
    mc = shade(col, 0.32)
    pn.line([T_((s * px_, py_)) for px_, py_ in _open_cr([(40, -128), (30, -100), (40, -74)], 5)], mc, 2.4, caps=False)      # shoulder blade
    pn.line([T_((s * px_, py_)) for px_, py_ in _open_cr([(-60, -122), (-90, -104), (-96, -74)], 5)], mc, 2.4, caps=False)   # haunch
    for i in range(3):
        xx = -10 - i * 16
        pn.line([T_((s * xx, -100)), T_((s * (xx - 6), -74))], mc + (140,), 1.6, caps=False)
    rnd = random.Random(7 if striped else 3)
    if lod(pn, 290) >= 1:
        for _ in range(26):
            px_, py_ = rnd.uniform(-100, 70), rnd.uniform(-118, -70)
            pn.line([T_((s * px_, py_)), T_((s * (px_ - 6), py_ + 3))], shade(col, 0.18) + (170,), 1.3, caps=False)
    if striped:   # stripes follow the body contour: wedges from the spine down the flank
        for i in range(10):
            xx = 70 - i * 19
            top_y = -126 + 6 * math.sin(i)
            L_ = 36 + 10 * (i % 3)
            pn.poly([T_((s * (xx - 4), top_y)), T_((s * (xx + 5), top_y)), T_((s * (xx - 3 + 6 * (i % 2)), top_y + L_)), T_((s * (xx - 6), top_y + L_ * .6))], fill=INK)
        for (xx, yy) in ((-100, -100), (-112, -88), (-90, -76)):
            pn.poly([T_((s * xx, yy)), T_((s * (xx + 16), yy - 4)), T_((s * (xx + 12), yy + 3))], fill=INK)
    # near legs
    for nm, pts, sg in legs[2:]:
        _draw_leg(pn, [T_(p) for p in pts], sg, col, s, claws=(gait == 'leap'))
        if striped:
            for u in (0.35, 0.6):
                a, b = pts[1], pts[2]
                c_ = T_((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
                pn.line([(c_[0] - 9, c_[1] - 2), (c_[0] + 5, c_[1] + 2)], INK, 3.4)
    # head
    hcx, hcy = T_((s * 124, -128 + (14 * crouch)))
    if gait == 'run': hcy += 3 * math.sin(ph * 4 * math.pi)
    _cat_head(pn, hcx, hcy, s, col, striped, mane and not striped, look, expr, t, mouth)
    pn.pop()

def _cat_head(pn, hx, hy, s, col, striped, mane, look, expr, t, mouth):
    dk = shade(col, 0.25)
    if mane:   # layered tufts, dark at the root, lighter tips; runs down onto the chest
        rnd = random.Random(11)
        for layer, (rr, c_) in enumerate(((66, shade(MANE, .25)), (56, MANE), (46, light(MANE, .12)))):
            n = 18
            for i in range(n):
                a = (i / n) * 2 * math.pi + layer * 0.17
                ex_ = 1.0 if math.cos(a) * s < 0 else 0.86
                cx_ = hx - s * 12 + math.cos(a) * rr * ex_ * 0.62
                cy_ = hy + 6 + math.sin(a) * rr * 0.66 + (14 if math.sin(a) > 0.3 else 0)
                tip = (cx_ + math.cos(a) * 26, cy_ + math.sin(a) * 26 + 6)
                b1 = (cx_ + math.cos(a + 1.4) * 15, cy_ + math.sin(a + 1.4) * 15)
                b2 = (cx_ + math.cos(a - 1.4) * 15, cy_ + math.sin(a - 1.4) * 15)
                pn.poly([b1, tip, b2], fill=c_, outline=INK if layer == 0 else None, width=2)
        pn.circ(hx - s * 10, hy + 6, 44, fill=MANE)
        for i in range(10):
            a = rnd.uniform(0, 2 * math.pi); r_ = rnd.uniform(24, 46)
            p = (hx - s * 10 + math.cos(a) * r_, hy + 6 + math.sin(a) * r_)
            pn.line([p, (p[0] + math.cos(a) * 10, p[1] + math.sin(a) * 10)], light(MANE, .3), 2, caps=False)
    elif striped:   # tiger ruff: white cheek fur flaring outward
        for sd in (-1, 1):
            pn.poly([(hx + sd * 6 - s * 4, hy - 4), (hx + sd * 40 - s * 4, hy + 10), (hx + sd * 30 - s * 4, hy + 22), (hx + sd * 38 - s * 4, hy + 30),
                     (hx + sd * 8, hy + 34)], fill=(246, 240, 226), outline=INK, width=2.4)
    # ears (rounded, dark backs; white spot on tiger ears)
    for sd in (-1, 1):
        ex_, ey_ = hx + sd * 22 - s * 6, hy - 30
        pn.circ(ex_, ey_, 11, fill=col, outline=INK, width=2.6)
        pn.circ(ex_ + 1, ey_ + 2, 6, fill=shade(col, 0.5))
        if striped: pn.circ(ex_, ey_ - 1, 3, fill=WHITE)
    # skull
    skull = _cr([(hx - s * 30, hy - 8), (hx - s * 18, hy - 32), (hx + s * 10, hy - 34), (hx + s * 30, hy - 18), (hx + s * 44, hy + 4),
                 (hx + s * 40, hy + 22), (hx + s * 14, hy + 32), (hx - s * 16, hy + 26), (hx - s * 32, hy + 10)], 5)
    pn.poly(skull, fill=col, outline=INK, width=3.2)
    pn.poly(_cr([(hx - s * 20, hy - 26), (hx + s * 10, hy - 32), (hx + s * 26, hy - 20), (hx + s * 4, hy - 20)], 4), fill=light(col, 0.18))
    if striped:
        for i, (dx, dy, l) in enumerate(((-6, -30, 12), (4, -32, 12), (14, -28, 10))):
            pn.line([(hx + s * dx, hy + dy), (hx + s * (dx - 2), hy + dy + l)], INK, 3.2)
        for dy in (-2, 8):
            pn.line([(hx - s * 30, hy + dy), (hx - s * 14, hy + dy + 3)], INK, 3.4)
    # muzzle: white upper lip pads, whisker dots, chin
    op = 1.0 if (expr == 'roar' or mouth == 'open') else 0.0
    jaw = 16 * op
    pn.poly(_cr([(hx + s * 14, hy + 20 + jaw), (hx + s * 36, hy + 18 + jaw), (hx + s * 30, hy + 30 + jaw), (hx + s * 16, hy + 30 + jaw)], 4),
            fill=light(col, 0.5), outline=INK, width=2.2)
    if op:
        pn.poly([(hx + s * 14, hy + 14), (hx + s * 42, hy + 10), (hx + s * 36, hy + 24 + jaw), (hx + s * 16, hy + 24 + jaw)], fill=(110, 30, 36), outline=INK, width=2.2)
        pn.ell(hx + s * 26, hy + 22 + jaw * .6, 7, 4, fill=(196, 80, 90))
        for dx in (18, 34):
            pn.poly([(hx + s * dx, hy + 12), (hx + s * (dx + 3), hy + 12), (hx + s * (dx + 1.5), hy + 22)], fill=WHITE, outline=INK, width=1.2)
            pn.poly([(hx + s * dx, hy + 24 + jaw), (hx + s * (dx + 3), hy + 24 + jaw), (hx + s * (dx + 1.5), hy + 16 + jaw)], fill=WHITE, outline=INK, width=1.2)
    for sd in (0, 1):
        pn.ell(hx + s * (24 + sd * 12), hy + 10, 10, 8, fill=(250, 244, 230) if striped else light(col, 0.55), outline=INK, width=2)
        for j in range(3):
            pn.circ(hx + s * (21 + sd * 12 + j * 3), hy + 9 + (j % 2) * 3, 1.1, fill=INK)
    for sd in (-1, 1):
        for j in range(2):
            pn.line([(hx + s * (30 + 8 * sd), hy + 10 + j * 4), (hx + s * (30 + 8 * sd) + s * sd * 26, hy + 6 + j * 8)], (255, 255, 255, 170), 1.2, caps=False)
    # nose leather and bridge
    pn.poly([(hx + s * 36, hy - 2), (hx + s * 46, hy - 1), (hx + s * 42, hy + 7), (hx + s * 39, hy + 7)], fill=(70, 42, 38) if not striped else (196, 120, 110), outline=INK, width=2)
    pn.line([(hx + s * 14, hy - 18), (hx + s * 36, hy - 4)], light(col, 0.35), 3, caps=False)
    if not op:
        pn.line([(hx + s * 40, hy + 7), (hx + s * 38, hy + 12), (hx + s * 30, hy + 14)], INK, 2, caps=False)
    # eye: almond, amber iris, round pupil, highlight, dark liner, brow
    ex, ey = hx + s * 18, hy - 10
    if expr == 'dead':   # crossed eye, tongue out
        for a_, b_ in (((-7, -6), (7, 6)), ((-7, 6), (7, -6))):
            pn.line([(ex + a_[0], ey + a_[1]), (ex + b_[0], ey + b_[1])], INK, 3.6)
        pn.ell(hx + s * 30, hy + 24, 6, 9, fill=(214, 96, 110), outline=INK, width=2)
        return
    eye = [(ex - s * 10, ey + 1), (ex - s * 2, ey - 6), (ex + s * 9, ey - 3), (ex + s * 10, ey + 1), (ex + s * 1, ey + 5)]
    pn.poly(eye, fill=(222, 170, 60), outline=INK, width=2.6)
    px, py = ex + s * clamp(look[0], -1, 1) * 2.4, ey + look[1] * 2
    pn.circ(px, py, 3.4, fill=INK); pn.circ(px - 1.2, py - 1.4, 1.2, fill=WHITE)
    pn.line([(ex + s * 1, ey + 5), (ex + s * 8, ey + 14)], INK, 2, caps=False)    # tear line
    if expr in ('angry', 'roar'):
        pn.line([(ex - s * 12, ey - 10), (ex + s * 10, ey - 5)], INK, 3.6)
        for j in range(3): pn.line([(hx + s * (22 + j * 5), hy - 18), (hx + s * (24 + j * 5), hy - 12)], shade(col, 0.4), 1.6, caps=False)
    else:
        pn.line([(ex - s * 12, ey - 8), (ex + s * 6, ey - 10)], shade(col, 0.35), 3)

def lion(pn, x, y, k=1.0, f=1, **kw): bigcat(pn, x, y, k, f, **kw)
def tiger(pn, x, y, k=1.0, f=1, **kw): bigcat(pn, x, y, k, f, striped=True, mane=False, **kw)

# ---------------- environments ----------------
def env_arena():
    img = E.sky((170, 200, 226), (244, 226, 190), glow=(30, 20, 0), gy=0.2)
    d = ImageDraw.Draw(img)
    # cavea: tiers in an arc behind the sand
    for i in range(9):
        y0 = 980 - i * 62
        c = lerpc((196, 178, 148), (226, 214, 190), i / 9)
        d.rectangle([0, y0 - 62, W, y0], fill=c)
        d.line([(0, y0), (W, y0)], fill=shade(c, .3), width=4)
        rnd = random.Random(i)
        for xx in range(-10, W + 10, 26):
            hc = lerpc((120, 70, 50), (226, 214, 200), rnd.random())
            d.ellipse([xx + rnd.uniform(-4, 4) - 9, y0 - 50, xx + 9, y0 - 32], fill=hc)
            d.rectangle([xx - 9, y0 - 32, xx + 9, y0 - 6], fill=lerpc(hc, (200, 190, 170), .5))
    # podium wall and arched top
    d.rectangle([0, 980, W, 1060], fill=(214, 200, 170)); d.line([(0, 980), (W, 980)], fill=INK, width=4)
    for xx in range(30, W, 110):
        d.rectangle([xx, 996, xx + 60, 1060], fill=(150, 130, 100))
    for xx in range(0, W, 180):
        d.rectangle([xx + 60, 300, xx + 120, 420], fill=(200, 186, 160))
    d.rectangle([0, 1060, W, H], fill=SAND)
    rnd = random.Random(7)
    for _ in range(900):
        x_, y_ = rnd.uniform(0, W), rnd.uniform(1060, H)
        d.ellipse([x_, y_, x_ + 3, y_ + 2], fill=SAND_D)
    return E.grade(img, blur=4.0, sat=0.8, bright=0.95)

def env_hypogeum():
    img = Image.new('RGBA', (W, H), (40, 30, 24, 255)); d = ImageDraw.Draw(img)
    vp = (540, 860)
    rnd = random.Random(3)
    # corridor in one point perspective: brick walls, vault, floor
    for i in range(14, 0, -1):
        s = i / 14
        hw, hh = 60 + 520 * s, 90 + 900 * s
        c = lerpc((28, 20, 16), (120, 76, 54), s ** 0.7)
        d.rectangle([vp[0] - hw, vp[1] - hh * .55, vp[0] + hw, vp[1] + hh * .55], outline=c, width=max(2, int(30 * s)))
    for i in range(40):
        s = rnd.uniform(0.2, 1)
        for sd in (-1, 1):
            x_ = vp[0] + sd * (60 + 520 * s); y_ = vp[1] + rnd.uniform(-.5, .5) * (90 + 900 * s)
            d.rectangle([x_ - 18 * s, y_ - 8 * s, x_ + 18 * s, y_ + 8 * s], fill=lerpc((90, 54, 40), (150, 92, 66), rnd.random()))
    d.polygon([(0, H), (W, H), (vp[0] + 60, vp[1] + 50), (vp[0] - 60, vp[1] + 50)], fill=(70, 54, 40))
    for sd in (-1, 1):
        for s in (0.35, 0.65, 0.95):
            x_ = vp[0] + sd * (60 + 500 * s); y_ = vp[1] - 200 * s
            g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            gd.ellipse([x_ - 260 * s, y_ - 260 * s, x_ + 260 * s, y_ + 260 * s], fill=(255, 150, 60, 70))
            img.alpha_composite(g.filter(ImageFilter.GaussianBlur(60 * s)))
    return E.grade(img, blur=5.0, sat=0.9, bright=0.95)

def env_section():
    """Cutaway: bright arena band at the top, dark hypogeum masonry below (for shaft and capstan diagrams)."""
    img = Image.new('RGBA', (W, H), (52, 40, 32, 255)); d = ImageDraw.Draw(img)
    rnd = random.Random(9)
    for row, yy in enumerate(range(520, H, 40)):
        off = (row % 2) * 40
        for xx in range(-off, W, 80):
            d.rectangle([xx + 2, yy + 2, xx + 78, yy + 38], fill=lerpc((70, 48, 36), (104, 70, 50), rnd.random()))
    sk = E.sky((150, 186, 220), (240, 224, 190)).crop((0, 0, W, 470))
    img.paste(sk, (0, 0))
    return E.grade(img, blur=2.5, sat=0.85, bright=0.95)

E.ENV_FN = getattr(E, 'ENV_FN', {})
def get_env(name):
    return cache(('env', name), lambda: {'arena': env_arena, 'hypogeum': env_hypogeum, 'section': env_section}[name](), 8)

def crowd(pn, x0, y0, cols, rows, dx=30, dy=40, t=0.0, wave=None, seed=1):
    """Spectators as a grid of identical small figures (formation rule). wave(t, col) -> 0..1 stands them up."""
    rnd = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * dx + (r % 2) * dx / 2; y = y0 + r * dy
            u = wave(t, c, r) if wave else 0.0
            tc = lerpc((150, 82, 60), (214, 204, 178), rnd.random())
            pn.rect(x - 9, y - 22 - 12 * u, x + 9, y, fill=tc, outline=INK, width=1.6, r=4)
            pn.circ(x, y - 32 - 12 * u, 9, fill=SKIN, outline=INK, width=1.6)
            if u > 0.4:
                pn.line([(x - 8, y - 20 - 12 * u), (x - 14, y - 44 - 14 * u)], INK, 3)
                pn.line([(x + 8, y - 20 - 12 * u), (x + 14, y - 44 - 14 * u)], INK, 3)


# ---------------- cartoon brawl cloud (E020 hook, by user request) ----------------
CLOUD_O = (176, 156, 134); CLOUD_M = (214, 200, 182); CLOUD_L = (246, 240, 230)
def _puffs(cx, cy, R, n, t, seed, wob=0.06):
    rnd = random.Random(seed); out = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.15, 0.15)
        rr = R * rnd.uniform(0.78, 0.98)
        r_ = R * rnd.uniform(0.32, 0.46) * (1 + wob * math.sin(t * 13 + i * 2.1))
        out.append((cx + math.cos(a) * rr * 1.12, cy + math.sin(a) * rr * 0.86, r_))
    return out

def _paw(pn, base, ang, L, striped=True):
    tip = (base[0] + math.cos(ang) * L, base[1] + math.sin(ang) * L)
    pn.line([base, tip], INK, 30); pn.line([base, tip], TIGER, 23)
    if striped:
        for u in (0.35, 0.6, 0.82):
            c = (lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)); nx, ny = -math.sin(ang), math.cos(ang)
            pn.line([(c[0] - nx * 10, c[1] - ny * 10), (c[0] + nx * 6, c[1] + ny * 6)], INK, 4)
    pn.circ(tip[0], tip[1], 19, fill=TIGER, outline=INK, width=3)
    for k in (-1, 0, 1):
        a = ang + k * 0.5
        c = (tip[0] + math.cos(a) * 17, tip[1] + math.sin(a) * 17)
        pn.poly([c, (c[0] + math.cos(a) * 12 - math.sin(a) * 3, c[1] + math.sin(a) * 12 + math.cos(a) * 3), (c[0] + math.sin(a) * 4, c[1] - math.cos(a) * 4)],
                fill=(246, 240, 226), outline=INK, width=1.6)

def _arm(pn, base, ang, L, skin=(232, 200, 160)):
    tip = (base[0] + math.cos(ang) * L, base[1] + math.sin(ang) * L)
    pn.line([base, tip], INK, 22); pn.line([base, tip], skin, 15)
    pn.circ(tip[0], tip[1], 17, fill=skin, outline=INK, width=3)          # fist
    for k in (-1, 0, 1):
        pn.line([(tip[0] - math.sin(ang) * k * 8 + math.cos(ang) * 4, tip[1] + math.cos(ang) * k * 8 + math.sin(ang) * 4),
                 (tip[0] - math.sin(ang) * k * 8 + math.cos(ang) * 12, tip[1] + math.cos(ang) * k * 8 + math.sin(ang) * 12)], INK, 2, caps=False)

def _leg(pn, base, ang, L):
    tip = (base[0] + math.cos(ang) * L, base[1] + math.sin(ang) * L)
    pn.line([base, tip], INK, 22); pn.line([base, tip], (240, 232, 214), 15)
    for u in (0.4, 0.6, 0.8):
        c = (lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)); nx, ny = -math.sin(ang), math.cos(ang)
        pn.line([(c[0] - nx * 9, c[1] - ny * 9), (c[0] + nx * 9, c[1] + ny * 9)], INK, 7); pn.line([(c[0] - nx * 8, c[1] - ny * 8), (c[0] + nx * 8, c[1] + ny * 8)], WRAP, 4)
    pn.ell(tip[0] + math.cos(ang) * 8, tip[1] + math.sin(ang) * 8, 22, 13, fill=(96, 66, 40), outline=INK, width=3)

def _star(pn, x, y, r, a, col=(250, 214, 60)):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a + i * math.pi / 5) * rr, y + math.sin(a + i * math.pi / 5) * rr))
    pn.poly(pts, fill=col, outline=INK, width=3)

def fight_cloud(pn, x, y, t, t0, R=210, seed=3, burst=None):
    """Cartoon brawl: a churning dust ball with limbs, paws, the spear, tail, stars, swirls and impact spikes.
    Limbs swap every 0.12 s (held on fours, like a classic cartoon). burst: time it bursts apart (poof)."""
    if t < t0: return
    g = eoback(clamp((t - t0) / 0.18), 1.6)
    out = 0.0
    if burst is not None and t >= burst: out = clamp((t - burst) / 0.3)
    if out >= 1: return
    Rr = R * g * (1 + 0.5 * out); alpha = int(255 * (1 - out))
    jx = 10 * math.sin(t * 31) ; jy = 8 * math.cos(t * 27)
    cx, cy = x + jx, y + jy
    step = int((t - t0) / 0.12)
    rnd = random.Random(seed * 100 + step)
    # impact spikes behind the cloud
    if out == 0:
        for i in range(7):
            a = rnd.uniform(0, 2 * math.pi); L = Rr * rnd.uniform(1.75, 2.05)
            b = (cx + math.cos(a) * Rr * 0.8, cy + math.sin(a) * Rr * 0.7)
            pn.poly([(b[0] - math.sin(a) * 18, b[1] + math.cos(a) * 18), (cx + math.cos(a) * L, cy + math.sin(a) * L * 0.85), (b[0] + math.sin(a) * 18, b[1] - math.cos(a) * 18)],
                    fill=(250, 214, 60), outline=INK, width=3)
    # the cloud: ink rim, outer tone, mid tone, lit core
    P_ = _puffs(cx, cy, Rr, 13, t, seed)
    for px, py, r in P_: pn.circ(px, py, r + 6, fill=INK + (alpha,))
    pn.ell(cx, cy, Rr * 1.02 + 6, Rr * 0.8 + 6, fill=INK + (alpha,))
    for px, py, r in P_: pn.circ(px, py, r, fill=CLOUD_O + (alpha,))
    pn.ell(cx, cy, Rr * 1.02, Rr * 0.8, fill=CLOUD_O + (alpha,))
    for px, py, r in _puffs(cx, cy, Rr * 0.66, 10, t + 0.3, seed + 1): pn.circ(px, py, r, fill=CLOUD_M + (alpha,))
    for px, py, r in _puffs(cx, cy, Rr * 0.36, 8, t + 0.6, seed + 2): pn.circ(px, py, r, fill=CLOUD_L + (alpha,))
    if out > 0: return
    # limbs poking out of the cloud edge (drawn over it so they read)
    slots = [(-2.6, 'arm'), (-1.6, 'paw'), (-0.4, 'spear'), (0.5, 'arm2'), (1.4, 'leg'), (2.3, 'paw2'), (3.0, 'tail')]
    rnd.shuffle(slots)
    for k, (a0, kind) in enumerate(slots[:5]):
        a = a0 + rnd.uniform(-0.35, 0.35)
        base = (cx + math.cos(a) * Rr * 0.98, cy + math.sin(a) * Rr * 0.78)
        L = Rr * rnd.uniform(0.5, 0.68)
        if kind == 'arm': _arm(pn, base, a, L)
        elif kind == 'arm2': _arm(pn, base, a, L * 0.9)
        elif kind in ('paw', 'paw2'): _paw(pn, base, a, L)
        elif kind == 'leg': _leg(pn, base, a, L)
        elif kind == 'spear':
            venabulum(pn, base[0], base[1], a, back=0, L=Rr * 0.9)
        elif kind == 'tail':
            tip = (base[0] + math.cos(a) * L, base[1] + math.sin(a) * L)
            mid_ = ((base[0] + tip[0]) / 2 - math.sin(a) * 30, (base[1] + tip[1]) / 2 + math.cos(a) * 30)
            pts = [base, mid_, tip]
            pn.line(pts, INK, 20); pn.line(pts, TIGER, 13)
            for u in (0.3, 0.6, 0.85):
                c = (lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)); pn.circ(c[0], c[1], 6, fill=INK)
            pn.ell(tip[0], tip[1], 10, 8, fill=INK)
    # inner puff outlines (churning), centre burst ticks
    for px, py, r in _puffs(cx, cy, Rr * 0.6, 6, t * 1.7, seed + step % 3):
        pn.arc(px, py, r, 200, 330, INK, 4)
    for i in range(10):
        a = i * math.pi / 5 + t * 3
        pn.line([(cx + math.cos(a) * 22, cy + math.sin(a) * 22), (cx + math.cos(a) * 40, cy + math.sin(a) * 40)], (170, 60, 40) if i % 2 else INK, 4)
    # stars and swirls around the outside
    for i in range(4):
        a = t * 2.4 + i * math.pi / 2
        _star(pn, cx + math.cos(a) * Rr * 1.15, cy + math.sin(a) * Rr * 0.9, 22 + 6 * (i % 2), t * 5 + i)
    for i in range(3):
        a = -t * 1.8 + i * 2.1
        ox, oy = cx + math.cos(a) * Rr * 1.05, cy + math.sin(a) * Rr * 0.85
        pts = [(ox + math.cos(u * 9) * 14 * (1 - u) + u * 60 * math.cos(a), oy + math.sin(u * 9) * 14 * (1 - u) + u * 60 * math.sin(a)) for u in np.linspace(0, 1, 18)]
        pn.line(pts, (176, 60, 120), 5)
    for i in range(4):   # speed ticks
        a = rnd.uniform(0, 2 * math.pi)
        p0 = (cx + math.cos(a) * Rr * 1.25, cy + math.sin(a) * Rr * 1.0)
        pn.line([p0, (p0[0] + math.cos(a) * 34, p0[1] + math.sin(a) * 34)], INK, 4)

def poof(pn, x, y, t, t0, R=300):
    """Cloud bursting apart: expanding puffs that thin out."""
    u = (t - t0) / 0.45
    if u < 0 or u > 1: return
    e = eo3(u); a = int(200 * (1 - u))
    rnd = random.Random(9)
    for i in range(14):
        ang = i * 2 * math.pi / 14 + rnd.uniform(-0.2, 0.2)
        d = R * (0.5 + 0.9 * e)
        pn.circ(x + math.cos(ang) * d, y + math.sin(ang) * d * 0.8, 46 * (1 - 0.5 * u), fill=CLOUD_M + (a,))


def claw_marks(pn, x, y, s=1.0, ang=-0.6, n=3, L=46, col=(168, 34, 34)):
    """Cartoon claw slashes (scars): parallel red strokes with an ink edge, no blood pools."""
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
    for i in range(n):
        o = (i - (n - 1) / 2) * 12 * s
        a = (x + nx * o - ux * L * s / 2, y + ny * o - uy * L * s / 2); b = (x + nx * o + ux * L * s / 2, y + ny * o + uy * L * s / 2)
        pn.line([a, b], INK, 9 * s); pn.line([a, b], col, 5.5 * s)
        pn.line([(lerp(a[0], b[0], .2), lerp(a[1], b[1], .2)), (lerp(a[0], b[0], .7), lerp(a[1], b[1], .7))], (236, 120, 110), 1.6 * s, caps=False)

LIE = dict(torso=-90, head=8, uaF=-100, faF=-120, uaB=100, faB=80, thF=92, shF=96, thB=84, shB=88)
def dead_venator(pn, x, y, k, f=1, t=0.0):
    """Venator lying on his back after the fight: X eyes, claw scars on chest and arm, torn hem."""
    J = figure(pn, x, y, k, f, dict(LIE), 'venator', 'dead', look=(0, 0), blink=0.0)
    leg_wraps(pn, x, y, k, J)
    Wp = lambda p_, u=0.0, v=0.0: (x + (p_[0] + u) * k, y + (p_[1] + v) * k)
    nk, pl = J['neck'], J['pelvis']
    mid = ((nk[0] + pl[0]) / 2, (nk[1] + pl[1]) / 2)
    claw_marks(pn, *Wp(mid, 0, -6), s=k * 0.9, ang=0.9)
    claw_marks(pn, *Wp(J['elF']), s=k * 0.6, ang=-0.4, n=3, L=34)
    # torn tunic edge
    hx, hy = Wp(pl, -f * 4, 18)
    pn.line([(hx - 14 * k, hy), (hx - 7 * k, hy + 6 * k), (hx, hy), (hx + 7 * k, hy + 6 * k), (hx + 14 * k, hy)], INK, 3 * k)
    return J

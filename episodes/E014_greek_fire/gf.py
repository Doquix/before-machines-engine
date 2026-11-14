"""E014 Greek fire: props (dromon, siphon system, flames, jet, jars) and painted environments."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
import env as E

BRONZE_L = (214, 168, 92); BRONZE_D = (140, 96, 44)
F_OUT = (232, 92, 30); F_MID = (250, 160, 40); F_IN = (255, 238, 160)
LIQ = (96, 62, 30)
SEA_N = (22, 34, 52); SEA_D = (52, 92, 116)

# ---------------- fire ----------------
def flame(pn, x, y, h, t, seed=0, a=1.0, w=None):
    """Teardrop flame standing on (x, y), height h."""
    if h < 2 or a <= 0: return
    w = w or h * 0.42
    al = int(255 * clamp(a))
    for col, sc in ((F_OUT, 1.0), (F_MID, 0.72), (F_IN, 0.42)):
        N = 11; L, R = [], []
        hh = h * sc; ww = w * sc
        for i in range(N + 1):
            u = i / N
            prof = ww * math.sin(math.pi * min(1, u * 0.9 + 0.1)) * (1 - u) ** 0.35
            wob = math.sin(t * 13 + u * 5 + seed * 1.7) * h * 0.07 * u + math.sin(t * 7.3 + seed) * h * 0.04 * u * u
            yy = y - hh * u
            L.append((x + wob - prof, yy)); R.append((x + wob + prof, yy))
        pn.poly(L + R[::-1], fill=col + (al,))

def fire_patch(pn, x, y, s, t, seed=0, a=1.0, water=True):
    rnd = random.Random(seed)
    if water:
        for i in range(3):
            dx = (i - 1) * 26 * s
            pn.line([(x + dx, y + 6), (x + dx + 6 * math.sin(t * 5 + i), y + 50 * s)], F_MID + (int(90 * a),), 10 * s)
    for i in range(4):
        dx = rnd.uniform(-38, 38) * s
        hh = (70 + rnd.uniform(0, 60)) * s * (0.85 + 0.15 * math.sin(t * 9 + i + seed))
        flame(pn, x + dx, y, hh, t, seed * 7 + i, a)

def smoke(pn, x, y, s, t, seed=0, a=1.0):
    for i in range(5):
        ph = ((t * 0.5 + i / 5 + seed * 0.13) % 1.0)
        pn.circ(x + math.sin(i * 2 + t) * 30 * s + ph * 60 * s, y - ph * 300 * s, (30 + 60 * ph) * s,
                fill=(112, 104, 106, int(70 * (1 - ph) * a)))

def jet(pn, x0, y0, ang, L, lit, t, k=1.0, grav=0.0012, ymax=99999):
    """Liquid stream from a nozzle; lit 0..1 turns it into fire from the nozzle outward."""
    if L <= 0: return []
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    n = max(2, int(L / 18))
    for i in range(n + 1):
        d = L * i / n
        p_ = (x0 + ca * d, y0 + sa * d + grav * d * d)
        if p_[1] > ymax: break
        pts.append(p_)
    if len(pts) < 2: return pts
    pn.line(pts, LIQ, 16 * k); pn.line(pts, (150, 100, 46), 8 * k)
    if lit > 0:
        m = int(len(pts) * clamp(lit))
        for i in range(0, m, 2):
            px, py = pts[i]
            f = i / max(1, len(pts))
            pn.circ(px, py, (18 + 26 * f) * k * (0.8 + 0.2 * math.sin(t * 20 + i)), fill=F_OUT + (220,))
        for i in range(1, m, 2):
            px, py = pts[i]
            pn.circ(px, py, (10 + 14 * (i / len(pts))) * k, fill=F_MID + (230,))
        for i in range(0, m, 3):
            px, py = pts[i]
            flame(pn, px, py + 6 * k, (34 + 40 * i / len(pts)) * k, t, i, 0.9)
    return pts

# ---------------- props ----------------
def jar(pn, x, y, k, t=0.0, slosh=0.0, label=None, col=(176, 106, 70)):
    """Clay jar (narrow neck, two handles); origin at base center."""
    pn.push(x, y, k)
    body = [(-28, 0), (-62, -50), (-70, -110), (-58, -160), (-30, -186), (-22, -206), (22, -206), (30, -186), (58, -160), (70, -110), (62, -50), (28, 0)]
    for sd in (-1, 1):
        pn.line([(sd * 22, -196), (sd * 56, -200), (sd * 50, -160)], INK, 12); pn.line([(sd * 22, -196), (sd * 56, -200), (sd * 50, -160)], col, 6)
    pn.poly(body, fill=col, outline=INK, width=4)
    pn.line([(-60, -130), (60, -130)], lerpc(col, INK, .3), 3, caps=False)
    pn.rect(-26, -222, 26, -204, fill=lerpc(col, INK, .15), outline=INK, width=3.4, r=4)
    if slosh:
        yy = -216 + math.sin(t * 8) * 3
        pn.ell(0, yy, 18, 4, fill=LIQ)
    pn.line([(-44, -150), (-50, -80)], lerpc(col, WHITE, .35), 5)
    pn.pop()

def sack(pn, x, y, k, col=(196, 172, 120)):
    pn.push(x, y, k)
    pn.poly([(-60, 0), (-70, -60), (-50, -120), (-26, -140), (26, -140), (50, -120), (70, -60), (60, 0)], fill=col, outline=INK, width=4)
    pn.line([(-30, -128), (30, -128)], ROPE, 6)
    pn.line([(-40, -60), (-20, -50)], lerpc(col, INK, .3), 3)
    pn.pop()

def pot(pn, x, y, k, col=(150, 96, 64)):
    pn.push(x, y, k)
    pn.poly([(-40, 0), (-62, -40), (-58, -84), (-46, -98), (46, -98), (58, -84), (62, -40), (40, 0)], fill=col, outline=INK, width=4)
    pn.ell(0, -98, 50, 10, fill=lerpc(col, INK, .35), outline=INK, width=3.4)
    pn.arc(62, -60, 20, 270, 450, INK, 7)
    pn.pop()

def tube(pn, a, b, w, col=BRONZE, hi=True):
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / Ln * w / 2, dx / Ln * w / 2
    pn.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill=col, outline=INK, width=3.6)
    if hi: pn.line([(a[0] + nx * .5, a[1] + ny * .5), (b[0] + nx * .5, b[1] + ny * .5)], lerpc(col, WHITE, .4), max(2, w * .12), caps=False)

def siphon_head(pn, x, y, k, f=1):
    """Bronze nozzle with a beast head mouth; origin at the mouth."""
    pn.push(x, y, k)
    tube(pn, (-f * 150, 0), (-f * 30, 0), 34)
    for xx in (-110, -70):
        pn.line([(f * xx, -20), (f * xx, 20)], BRONZE_D, 6, caps=False)
    pn.poly([(-f * 36, -26), (f * 6, -18), (f * 4, 18), (-f * 36, 26)], fill=BRONZE_L, outline=INK, width=3.4)
    pn.circ(-f * 22, -14, 4, fill=INK)
    pn.poly([(-f * 30, -26), (-f * 22, -40), (-f * 16, -24)], fill=BRONZE_L, outline=INK, width=2.6)
    pn.pop()

def dromon(pn, x, y, k, t, f=1, hull=(98, 66, 38), sail=(232, 220, 192), stripe=(170, 60, 40), oar_rate=1.6,
           siphon=True, row=1.0, fire=0.0, mast=True, sail_on=True):
    """Oared galley side view, waterline at y. Bow toward +f. Returns world points (nozzle, bow, deck)."""
    pn.push(x, y, k)
    X = lambda v: f * v
    # oars (behind hull), sweeping
    for i in range(13):
        ox = -360 + i * 54
        ph = t * oar_rate * 2 * math.pi * row + i * 0.15
        sw = math.sin(ph) * 22 * row
        top = (X(ox), -48); bot = (X(ox + sw - 40), 70 + 10 * math.cos(ph) * row)
        pn.line([top, bot], INK, 7); pn.line([top, bot], (150, 112, 70), 3.5)
    # hull
    hp = [(X(-470), -150), (X(-430), -90), (X(-380), -60), (X(400), -60), (X(450), -76), (X(470), -84),
          (X(470), -40), (X(560), 4), (X(470), 14), (X(420), 34), (X(-360), 34), (X(-440), -10), (X(-500), -110)]
    pn.poly(hp, fill=hull, outline=INK, width=4)
    pn.line([(X(-420), -60), (X(440), -60)], lerpc(hull, WHITE, .25), 6, caps=False)
    pn.line([(X(-370), -10), (X(430), -10)], lerpc(hull, INK, .3), 3, caps=False)
    pn.line([(X(470), -20), (X(560), 4)], IRON, 8)   # spur
    # rail
    pn.line([(X(-400), -88), (X(330), -88)], lerpc(hull, WHITE, .15), 5, caps=False)
    for i in range(16):
        xx = -390 + i * 46
        pn.line([(X(xx), -88), (X(xx), -60)], lerpc(hull, INK, .2), 3, caps=False)
    # stern post
    pn.line([(X(-470), -150), (X(-500), -200), (X(-470), -230)], hull, 14)
    pn.line([(X(-470), -150), (X(-500), -200), (X(-470), -230)], INK, 3)
    # forecastle (xylokastron)
    fc = [(X(330), -60), (X(330), -190), (X(450), -190), (X(450), -60)]
    pn.poly(fc, fill=lerpc(hull, WHITE, .12), outline=INK, width=3.6)
    for i in range(4):
        xx = 336 + i * 30
        pn.rect(X(xx), -212, X(xx + 18), -188, fill=lerpc(hull, WHITE, .12), outline=INK, width=3)
    pn.line([(X(330), -130), (X(450), -130)], lerpc(hull, INK, .3), 3, caps=False)
    noz = None
    if siphon:
        pn.pop(); pn.push(x, y, k)
        siphon_head(pn, X(510), -150, 1.0, f)
        noz = (X(516), -150)
    # mast and lateen sail
    if mast:
        pn.line([(X(20), -60), (X(20), -620)], INK, 16); pn.line([(X(20), -60), (X(20), -620)], WOOD, 10)
        if sail_on:
            yard = [(X(-300), -380), (X(330), -700)]
            sl = [(X(-290), -384), (X(320), -694), (X(20), -110)]
            pn.poly(sl, fill=sail, outline=INK, width=3.6)
            pn.line([(lerp(sl[0][0], sl[1][0], .5), lerp(sl[0][1], sl[1][1], .5)), sl[2]], stripe, 10, caps=False)
            pn.line(yard, INK, 10); pn.line(yard, WOOD, 6)
    pn.pop()
    W_ = lambda p: (x + p[0] * k, y + p[1] * k)
    return dict(nozzle=W_(noz) if noz else None, bow=W_((X(480), -84)), deck=W_((X(390), -190)), mid=W_((0, -60)))

def water(pn, y, t, col=SEA_N, x0=-200, x1=1300, amp=1.0, scroll=0.0, light=(110, 150, 180), bottom=2400):
    """Foreground water band from y down, with moving wave dashes."""
    pn.rect(x0, y, x1, bottom, fill=col + (235,))
    rnd = random.Random(4)
    for i in range(70):
        wx = rnd.uniform(0, 1600); wy = y + 14 + rnd.uniform(0, 520) ** 1.0
        xx = (wx - scroll * (0.6 + (wy - y) / 600) + t * 30) % 1600 - 200
        ln = 30 + (wy - y) * 0.12
        a = int(130 * (1 - (wy - y) / 700))
        bob = math.sin(t * 2.2 + i) * 4 * amp
        pn.line([(xx, wy + bob), (xx + ln, wy + bob)], light + (max(20, a),), 3 + (wy - y) / 160)
    # surface highlight line
    pts = [(xx, y + math.sin(xx / 70 + t * 2.5) * 6 * amp) for xx in range(x0, x1 + 1, 40)]
    pn.line(pts, light + (160,), 4)

def galley_small(pn, x, y, k, t, f=-1, sail=(236, 232, 220), hull=(110, 78, 46), seed=0):
    dromon(pn, x, y, k, t + seed * 0.37, f, hull=hull, sail=sail, stripe=(60, 100, 80), siphon=False, oar_rate=1.2)

def lever_pump(pn, x, y, k, ang, col=BRONZE):
    """Force pump cylinder with a see-saw lever. Returns world lever ends (left, right)."""
    pn.push(x, y, k)
    pn.rect(-30, -150, 30, 0, fill=col, outline=INK, width=3.6, r=6)
    pn.line([(-16, -140), (-16, -10)], lerpc(col, WHITE, .4), 4, caps=False)
    pn.rect(-46, -8, 46, 12, fill=WOOD_D, outline=INK, width=3)
    pn.line([(0, -150), (0, -200)], IRON, 10)
    piv = (0, -230)
    pn.rect(-10, -236, 10, -150, fill=WOOD_D, outline=INK, width=3)
    a = math.radians(ang)
    L_ = 170
    le = (piv[0] - math.cos(a) * L_, piv[1] - math.sin(a) * L_); re = (piv[0] + math.cos(a) * L_, piv[1] + math.sin(a) * L_)
    pn.line([le, re], INK, 16); pn.line([le, re], WOOD, 10)
    pn.circ(*piv, 9, fill=IRON, outline=INK, width=3)
    rod = (piv[0] + math.cos(a) * 40, piv[1] + math.sin(a) * 40)
    pn.line([rod, (rod[0], -150)], IRON, 6)
    pn.pop()
    W_ = lambda p: (x + p[0] * k, y + p[1] * k)
    return W_(le), W_(re)

def tank(pn, x, y, k, t, heat=0.0, sealed=1.0, level=0.6, bulge=0.0, cut=True, press=0.0):
    """Sealed bronze tank, cutaway; origin at base center. Returns outlet world point (top right)."""
    pn.push(x, y, k)
    b = 1 + bulge * 0.05 * (0.6 + 0.4 * math.sin(t * 40))
    w, h = 130 * b, 210
    pn.rect(-w, -h, w, 0, fill=BRONZE, outline=INK, width=4, r=40)
    if cut:
        pn.rect(-w + 18, -h + 18, w - 18, -18, fill=(62, 46, 30), r=30)
        ly = -18 - (h - 36) * level
        pn.rect(-w + 18, ly, w - 18, -18, fill=LIQ, r=26)
        if heat > 0.05:
            for i in range(10):
                ph = (t * (0.8 + heat) + i * 0.13) % 1
                bx = -w + 40 + (i * 37 % int(2 * w - 80))
                pn.circ(bx, lerp(-30, ly + 6, ph), 4 + 5 * heat, fill=(200, 150, 80, int(200 * heat * (1 - ph))))
        if press > 0:
            for i in range(6):
                a = i / 6 * 2 * math.pi + 0.3
                r0 = 30; r1 = 30 + 40 * press
                c0 = (math.cos(a) * r0, (ly - 18 - h) / 2 + 8 + math.sin(a) * r0 * .5)
                c1 = (math.cos(a) * r1, (ly - 18 - h) / 2 + 8 + math.sin(a) * r1 * .5)
                pn.line([c0, c1], AMBER + (int(255 * press),), 5)
    for i in range(7):
        pn.circ(-w + 26 + i * (2 * w - 52) / 6, -h + 10, 5, fill=BRONZE_D)
    # lid
    ly_ = -h - 4 - 120 * (1 - eoback(sealed))
    pn.rect(-w * .55, ly_ - 20, w * .55, ly_ + 6, fill=BRONZE_L, outline=INK, width=3.6, r=6)
    if sealed >= 1:
        for sd in (-1, 1): pn.rect(sd * w * .55 - 10, -h - 22, sd * w * .55 + 10, -h + 16, fill=IRON, outline=INK, width=3)
    pn.pop()
    return (x + 70 * k, y - (h + 20) * k)

def brazier(pn, x, y, k, t, heat=1.0):
    pn.push(x, y, k)
    for sd in (-1, 1): pn.line([(sd * 80, 0), (sd * 110, -70)], IRON, 10)
    pn.poly([(-150, -70), (150, -70), (120, -20), (-120, -20)], fill=IRON, outline=INK, width=3.6)
    for i in range(7):
        pn.circ(-110 + i * 36, -76, 14, fill=lerpc((60, 30, 20), (250, 120, 40), heat * (0.7 + 0.3 * math.sin(t * 6 + i))), outline=INK, width=2)
    pn.pop()
    if heat > 0.02:
        for i in range(5):
            flame(pn, x + (-100 + i * 50) * k, y - 80 * k, (40 + 30 * math.sin(i * 2.1)) * k * heat, t, i + 3, clamp(heat * 1.4))

def pbar(pn, x, y, w, h, v, label, col=AMBER):
    """Unnumbered gauge bar."""
    pn.rect(x, y, x + w, y + h, fill=(250, 244, 228), outline=INK, width=4, r=10)
    if v > 0.01: pn.rect(x + 8, y + 8, x + 8 + (w - 16) * clamp(v), y + h - 8, fill=col, r=6)
    pn.text(x + w / 2, y - 28, label, 32, INK, 'Black', 'mm', True)

def wall_city(pn, x0, x1, base, t, k=1.0, dome=True):
    """Sea walls of Constantinople with towers, a large dome behind (no minarets: 7th century)."""
    W1 = (176, 164, 146)
    if dome:
        cx = (x0 + x1) / 2 + 60 * k
        pn.rect(cx - 170 * k, base - 330 * k, cx + 170 * k, base - 120 * k, fill=(160, 146, 128), outline=INK, width=3)
        pn.circ(cx, base - 330 * k, 120 * k, fill=(150, 140, 126), outline=INK, width=3)
        pn.rect(cx - 125 * k, base - 330 * k, cx + 125 * k, base - 300 * k, fill=(160, 146, 128))
        for sd in (-1, 1):
            pn.circ(cx + sd * 150 * k, base - 260 * k, 70 * k, fill=(150, 140, 126), outline=INK, width=3)
            pn.rect(cx + sd * 150 * k - 72 * k, base - 260 * k, cx + sd * 150 * k + 72 * k, base - 120 * k, fill=(160, 146, 128), outline=INK, width=3)
    pn.rect(x0, base - 120 * k, x1, base + 4, fill=W1, outline=INK, width=3.4)
    xx = x0
    while xx < x1:
        pn.rect(xx, base - 140 * k, xx + 20 * k, base - 118 * k, fill=W1, outline=INK, width=2.6); xx += 36 * k
    xx = x0 + 40 * k
    while xx < x1:
        pn.rect(xx - 34 * k, base - 190 * k, xx + 34 * k, base + 4, fill=lerpc(W1, INK, .08), outline=INK, width=3.4)
        for d in (-34, -12, 10):
            pn.rect(xx + d * k, base - 208 * k, xx + (d + 22) * k, base - 188 * k, fill=lerpc(W1, INK, .08), outline=INK, width=2.6)
        pn.rect(xx - 6 * k, base - 150 * k, xx + 6 * k, base - 124 * k, fill=INK, r=5)
        xx += 260 * k

# ---------------- environments ----------------
def _stars(im, n=140, y1=1000, seed=3):
    d = ImageDraw.Draw(im, 'RGBA'); rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, y1) ** 1.0
        r = rnd.uniform(0.8, 2.2); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 230, int(rnd.uniform(90, 220))))

def env_nightsea():
    im = E.sky((14, 18, 34), (70, 64, 88), (30, 14, 0), 0.62)
    _stars(im)
    d = ImageDraw.Draw(im)
    E.hill_layer(im, 1060, 26, (34, 34, 52), 6, freqs=(1.2, 3.1, 7.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1080, W, H], fill=SEA_N)
    for i in range(80):
        y = 1090 + (i * 13) % 800; x = (i * 197) % W
        d.line([(x, y), (x + 40 + y / 40, y)], fill=(60, 80, 110), width=2)
    return E.grade(im, blur=2.5, sat=0.8, bright=0.95)

def env_daysea():
    im = E.sky((96, 128, 160), (232, 206, 170), (40, 20, 0), 0.55)
    E.clouds(im, 6, (250, 236, 214, 130))
    E.hill_layer(im, 1040, 30, (112, 118, 130), 5, freqs=(1.0, 2.6, 6.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1070, W, H], fill=SEA_D)
    for i in range(90):
        y = 1080 + (i * 17) % 840; x = (i * 211) % W
        d.line([(x, y), (x + 40 + y / 30, y)], fill=(110, 150, 170), width=2)
    return E.grade(im, blur=3)

def env_cityview():
    im = E.sky((92, 116, 150), (236, 196, 156), (40, 20, 0), 0.5)
    E.clouds(im, 9, (250, 230, 206, 120), y0=150, y1=700)
    lay = new_layer(); pn = Pen(lay, cam=False)
    wall_city(pn, -40, 1120, 1040, 0, 1.15)
    flatten(im, lay)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1044, W, H], fill=SEA_D)
    for i in range(90):
        y = 1056 + (i * 17) % 840; x = (i * 211) % W
        d.line([(x, y), (x + 40 + y / 30, y)], fill=(110, 150, 170), width=2)
    return E.grade(im, blur=3)

def env_road():
    im = E.sky((120, 140, 170), (240, 210, 160), (50, 26, 0), 0.5)
    E.clouds(im, 2, (250, 236, 214, 110))
    E.hill_layer(im, 1020, 70, (176, 150, 118), 3)
    E.hill_layer(im, 1120, 30, (196, 168, 120), 7, freqs=(1.4, 3.3, 6.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1230, W, H], fill=(186, 158, 110))
    return E.grade(im, blur=3.5)

def env_gate():
    im = E.sky((80, 92, 120), (226, 180, 140), (40, 20, 0), 0.5)
    E.clouds(im, 4, (246, 222, 200, 110))
    d = ImageDraw.Draw(im)
    Wc = (164, 154, 138)
    d.rectangle([0, 700, W, 1260], fill=Wc, outline=INK)
    for row in range(10):
        yy = 720 + row * 54; d.line([(0, yy), (W, yy)], fill=(130, 122, 110), width=2)
        for xx in range((row % 2) * 60, W, 120): d.line([(xx, yy), (xx, yy + 54)], fill=(130, 122, 110), width=2)
    for x in range(0, W, 70): d.rectangle([x, 660, x + 40, 702], fill=Wc, outline=INK, width=2)
    d.rectangle([380, 880, 700, 1262], fill=(40, 32, 30))
    d.ellipse([380, 720, 700, 1040], fill=(40, 32, 30))
    d.rectangle([0, 1260, W, H], fill=(120, 108, 80))
    return E.grade(im, blur=3.5)

for _n in ('nightsea', 'daysea', 'cityview', 'road', 'gate'):
    setattr(E, 'env_' + _n, globals()['env_' + _n])

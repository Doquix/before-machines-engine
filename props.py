"""Props: counterweight trebuchet, castle pieces, flags, sticker tags, stamp, small engines."""
import math, random
from lib import *
from detail import lod, shade, light, rivet, scratches

PIV_H, LA, LS, SL = 420, 560, 112, 300
TH_COCK, TH_REL, TH_END = 137.0, 292.0, 318.0

def sling_rel(th):
    s = clamp((th - TH_COCK) / (TH_REL - TH_COCK))
    return -132 + 150 * s ** 2.3

def treb_points(th, rel=None):
    """Local key points (origin at ground center, y up negative)."""
    a = math.radians(th)
    piv = (0.0, -PIV_H)
    tip = (piv[0] + math.cos(a) * LA, piv[1] + math.sin(a) * LA)
    se = (piv[0] - math.cos(a) * LS, piv[1] - math.sin(a) * LS)
    if rel is None: rel = sling_rel(th)
    ph = math.radians(th + rel)
    pouch = (tip[0] + math.cos(ph) * SL, tip[1] + math.sin(ph) * SL)
    if pouch[1] > -12:
        dy = -12 - tip[1]
        dx = math.sqrt(max(0, SL * SL - dy * dy))
        pouch = (tip[0] + dx, -12.0)
    return dict(piv=piv, tip=tip, se=se, pouch=pouch, cw=(se[0], se[1] + 72))

def stone(pn, x, y, r, seed=1, col=STONE):
    rnd = random.Random(seed)
    pts = []
    for i in range(9):
        a = i / 9 * 2 * math.pi; rr = r * (0.84 + 0.2 * rnd.random())
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    pn.poly(pts, fill=col, outline=INK, width=3)
    pn.line([(x - r * .35, y - r * .3), (x - r * .05, y - r * .45)], lerpc(col, WHITE, .4), 3)

def beam_rect(pn, a, b, w, fill):
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / Ln * w / 2, dx / Ln * w / 2
    pn.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill=fill, outline=INK, width=3.4)

def trebuchet(pn, x, y, k, th=TH_COCK, rel=None, stones=1.0, stone_in=True, rope=0.0, hl=None, winch_a=0.0,
              cw_extra=0.0, loop_off=0.0, show_sling=True, ghost=0.0):
    """hl: dict of part -> 0..1 highlight (cw, short, long, sling, piv, prong)."""
    hl = hl or {}
    pn.push(x, y, k)
    K = treb_points(th, rel)
    def hc(part, base):
        v = hl.get(part, 0)
        return lerpc(base, AMBER, v) if v else base
    # ground sills and trough
    beam_rect(pn, (-300, -8), (300, -8), 18, WOOD_D)
    beam_rect(pn, (-240, -26), (260, -26), 10, (120, 86, 52))
    # back A-frame leg pair (darker)
    for sx in (-1, 1):
        beam_rect(pn, (sx * 175, -16), (sx * 8, -PIV_H + 4), 22, lerpc(WOOD, INK, .25))
    beam_rect(pn, (-120, -150), (120, -150), 14, lerpc(WOOD, INK, .25))
    beam_rect(pn, (-60, -290), (60, -290), 12, lerpc(WOOD, INK, .25))
    # winch (windlass) at back left
    wx, wy = -250, -70
    beam_rect(pn, (wx, -16), (wx, wy), 14, WOOD_D)
    pn.circ(wx, wy, 34, fill=(120, 86, 52), outline=INK, width=3.4)
    for i in range(4):
        aa = winch_a + i * math.pi / 2
        pn.line([(wx, wy), (wx + math.cos(aa) * 58, wy + math.sin(aa) * 58)], INK, 9)
        pn.line([(wx, wy), (wx + math.cos(aa) * 58, wy + math.sin(aa) * 58)], WOOD, 5)
    pn.circ(wx, wy, 9, fill=INK)
    if rope > 0:
        t = K['tip']
        pn.line([(wx, wy - 30), (lerp(wx, t[0], rope), lerp(wy - 30, t[1], rope))], ROPE, 4)
    # beam
    a = math.radians(th)
    ux, uy = math.cos(a), math.sin(a)
    beam_rect(pn, K['se'], K['piv'], 30, hc('short', (150, 108, 64)))
    beam_rect(pn, K['piv'], K['tip'], 26, hc('long', (150, 108, 64)))
    for f_ in (0.35, 0.7):  # iron bands
        bx, by = K['piv'][0] + ux * LA * f_, K['piv'][1] + uy * LA * f_
        pn.line([(bx - uy * 14, by + ux * 14), (bx + uy * 14, by - ux * 14)], IRON, 5, caps=False)
    # prong at the tip
    tip = K['tip']
    pr = (tip[0] + ux * 26, tip[1] + uy * 26)
    pn.line([tip, pr], hc('prong', IRON), 7)
    # counterweight box hanging from short end
    se = K['se']; bw, bh = 128, 112
    top = se[1] + 14 + cw_extra
    pn.line([(se[0] - 40, top), se, (se[0] + 40, top)], INK, 5)
    pn.rect(se[0] - bw / 2, top, se[0] + bw / 2, top + bh, fill=hc('cw', (122, 84, 50)), outline=INK, width=3.6, r=4)
    n = int(round(clamp(stones) * 9))
    for i in range(n):
        cxs = se[0] - 40 + (i % 3) * 40; cys = top + bh - 22 - (i // 3) * 32
        stone(pn, cxs, cys, 17, seed=i + 3, col=lerpc(STONE, STONE_D, (i * 37 % 10) / 14))
    pn.rect(se[0] - bw / 2, top, se[0] + bw / 2, top + bh, outline=INK, width=3.6, r=4)
    for yy in (0.33, 0.66):
        pn.line([(se[0] - bw / 2, top + bh * yy), (se[0] + bw / 2, top + bh * yy)], lerpc(INK, WOOD, .3), 2.2, caps=False)
    # front A-frame legs
    for sx in (-1, 1):
        beam_rect(pn, (sx * 185, -10), (sx * 10, -PIV_H + 10), 26, WOOD)
    beam_rect(pn, (-130, -140), (130, -140), 16, WOOD)
    pn.circ(0, -PIV_H, 20, fill=hc('piv', IRON), outline=INK, width=3.6)
    pn.circ(0, -PIV_H, 6, fill=INK)
    # sling
    pouch = K['pouch']
    if show_sling:
        sc = hc('sling', ROPE)
        pn.line([tip, pouch], INK, 7); pn.line([tip, pouch], sc, 4)
        lo = (lerp(pr[0], pouch[0], loop_off * 0.25), lerp(pr[1], pouch[1], loop_off * 0.25))
        if loop_off < 1:
            pn.line([lo, pouch], INK, 6); pn.line([lo, pouch], sc, 3)
            pn.circ(lo[0], lo[1], 8, outline=INK, width=3)
        pn.ell(pouch[0], pouch[1], 22, 14, fill=(116, 84, 56), outline=INK, width=3)
        if stone_in: stone(pn, pouch[0], pouch[1] - 10, 20, seed=11)
    pn.pop()
    W_ = lambda p: (x + p[0] * k, y + p[1] * k)
    return {n_: W_(v) for n_, v in K.items()} | {'prong': W_(pr)}

def small_engine(pn, x, y, k, th=0.0, col=WOOD):
    pn.push(x, y, k)
    beam_rect(pn, (-60, -4), (60, -4), 10, WOOD_D)
    beam_rect(pn, (-45, -4), (0, -95), 10, col); beam_rect(pn, (45, -4), (0, -95), 10, col)
    a = math.radians(200 + th)
    beam_rect(pn, (0, -95), (math.cos(a) * 110, -95 + math.sin(a) * 110), 9, (150, 108, 64))
    beam_rect(pn, (0, -95), (-math.cos(a) * 26, -95 - math.sin(a) * 26), 12, (150, 108, 64))
    pn.rect(-math.cos(a) * 26 - 16, -95 - math.sin(a) * 26 + 4, -math.cos(a) * 26 + 16, -95 - math.sin(a) * 26 + 32, fill=(122, 84, 50), outline=INK, width=3)
    pn.circ(0, -95, 6, fill=IRON, outline=INK, width=2)
    pn.pop()

def flag(pn, x, y, k, t, size=1.0, col=(246, 244, 236), wave=1.0, pole=150):
    pn.push(x, y, k)
    pn.line([(0, 0), (0, -pole)], WOOD_D, 7)
    pts_t, pts_b = [], []
    for i in range(9):
        u = i / 8
        off = math.sin(t * 9 - u * 5) * 9 * u * wave
        pts_t.append((u * 96 * size, -pole + off))
        pts_b.append((u * 96 * size, -pole + 62 * size + off * 1.2))
    pn.poly(pts_t + pts_b[::-1], fill=col, outline=INK, width=3)
    pn.pop()

def merlons(pn, y, x0=-40, x1=1120, mw=120, gap=70, h=90, col=(146, 140, 128), seed=4, phase=0.0):
    """Castle parapet in the foreground: wall body below y, merlons above."""
    rnd = random.Random(seed)
    pn.rect(x0, y, x1, y + 700, fill=col, outline=INK, width=4)
    x = x0 + phase
    while x < x1:
        pn.rect(x, y - h, x + mw, y + 6, fill=col, outline=INK, width=4)
        x += mw + gap
    for row in range(8):
        yy = y + 30 + row * 52
        pn.line([(x0, yy), (x1, yy)], lerpc(col, INK, .3), 2.2, caps=False)
        off = 0 if row % 2 else 50
        for xx in range(int(x0) + off, int(x1), 100):
            pn.line([(xx, yy), (xx, yy + 52)], lerpc(col, INK, .3), 2.2, caps=False)

# User rule (2026-11-26): tags and stamps sit level and centred across the frame. TAG_LEVEL ignores any rot_ an
# episode passes; TAG_CENTER puts every tag and stamp on the frame's centre line (x = 540), keeping its height.
TAG_LEVEL = True
TAG_CENTER = True

def tag(pn, x, y, text, sz=46, t=1.0, rot_=0, fill=PARCH, col=INK, sub=None, string_to=None):
    """Sticker tag: level parchment card with border; pops via t in 0..1 (eoback)."""
    if t <= 0.01: return
    if TAG_LEVEL: rot_ = 0
    if TAG_CENTER: x = W / 2
    w = max(pn.tw(text, sz, 'Black', True), (pn.tw(sub, sz * 0.42, 'Bold') + len(sub) * 2) if sub else 0) + 56; h = sz * 1.5 + (sz * 0.62 if sub else 0)
    if string_to:
        pn.line([(x, y), string_to], INK, 3)
        pn.circ(*string_to, 6, fill=INK)
    pn.push(x, y, t)
    a = math.radians(rot_)
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    R = [(cx * math.cos(a) - cy * math.sin(a) + 7, cx * math.sin(a) + cy * math.cos(a) + 9) for cx, cy in corners]
    pn.poly(R, fill=(0, 0, 0, 70))
    R = [(cx * math.cos(a) - cy * math.sin(a), cx * math.sin(a) + cy * math.cos(a)) for cx, cy in corners]
    pn.poly(R, fill=fill, outline=INK, width=4)
    ty = -h / 2 + sz * 0.78
    pn.text(-math.sin(a) * (ty), math.cos(a) * ty, text, sz, col, 'Black', 'mm', True)
    if sub:
        sy = h / 2 - sz * 0.5
        pn.text(-math.sin(a) * sy, math.cos(a) * sy, sub, sz * 0.42, MUTED, 'Bold', 'mm', sp=2)
    pn.pop()

def stamp(pn, x, y, text, t, sz=120, col=RUST, rot_=0):
    """Solid stamp slammed from 2.6x to 1x over 0.12 s (t = seconds since slam start)."""
    if t < 0: return
    if TAG_LEVEL: rot_ = 0
    if TAG_CENTER: x = W / 2
    s = lerp(2.6, 1.0, ei3(clamp(t / 0.12))) if t < 0.12 else 1.0
    a_ = clamp(t / 0.05)
    w = pn.tw(text, sz, 'Black', True) + 90; h = sz * 1.42
    pn.push(x, y, s)
    a = math.radians(rot_)
    def R(pts): return [(cx * math.cos(a) - cy * math.sin(a), cx * math.sin(a) + cy * math.cos(a)) for cx, cy in pts]
    alpha = int(255 * a_)
    pn.poly(R([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]), fill=col + (alpha,))
    i = 14
    pn.poly(R([(-w / 2 + i, -h / 2 + i), (w / 2 - i, -h / 2 + i), (w / 2 - i, h / 2 - i), (-w / 2 + i, h / 2 - i)]),
            outline=(255, 255, 255, alpha), width=5)
    pn.text(0, 4, text, sz, (255, 255, 255, alpha), 'Black', 'mm', True)
    # grunge speckles
    rnd = random.Random(5)
    for _ in range(46):
        px, py = rnd.uniform(-w / 2, w / 2), rnd.uniform(-h / 2, h / 2)
        q = R([(px, py)])[0]
        pn.circ(q[0], q[1], rnd.uniform(2, 7), fill=col + (alpha,))
    pn.pop()

def arrow(pn, a, b, col=INK, w=6, head=22, dash=0, p=1.0):
    if p <= 0: return
    b = (lerp(a[0], b[0], p), lerp(a[1], b[1], p))
    if dash:
        L_ = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L_ / dash)
        for i in range(0, n, 2):
            u0, u1 = i / max(1, n), min(1, (i + 1) / max(1, n))
            pn.line([(lerp(a[0], b[0], u0), lerp(a[1], b[1], u0)), (lerp(a[0], b[0], u1), lerp(a[1], b[1], u1))], col, w)
    else:
        pn.line([a, b], col, w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pn.poly([b, (b[0] - head * math.cos(ang - .45), b[1] - head * math.sin(ang - .45)),
             (b[0] - head * math.cos(ang + .45), b[1] - head * math.sin(ang + .45))], fill=col)

def callout(pn, ax, ay, lx, ly, text, p=1.0, sz=34, col=INK, hl=False):
    """Label with leader line from (ax,ay) to label at (lx,ly)."""
    if p <= 0: return
    e = eo3(clamp(p * 1.6))
    mx, my = lerp(ax, lx, e), lerp(ay, ly, e)
    pn.line([(ax, ay), (mx, my)], col, 3.4)
    pn.circ(ax, ay, 7, fill=col)
    if p > 0.35:
        s = eoback(clamp((p - 0.35) / 0.65))
        w = pn.tw(text, sz, 'Black', True) + 34
        pn.push(lx, ly, s)
        pn.rect(-w / 2, -sz * 0.75, w / 2, sz * 0.75, fill=AMBER if hl else (250, 244, 228), outline=INK, width=3.4, r=10)
        pn.text(0, 2, text, sz, INK, 'Black', 'mm', True)
        pn.pop()

ROCK = (92, 86, 90); ROCK_D = (66, 62, 68); CWALL = (168, 160, 146)

def castle(pn, x, y, k, gap=0.0, dust=0.0, t=0.0):
    """Stirling crag with a simplified medieval curtain wall. Returns world point at the top of the tall tower."""
    pn.push(x, y, k)
    crag = [(-360, 0), (-300, -90), (-270, -200), (-230, -255), (230, -262), (270, -210), (320, -120), (380, 0)]
    pn.poly(crag, fill=ROCK, outline=INK, width=4)
    for i, (a, b) in enumerate(((-280, -150), (-250, -60), (260, -170), (300, -80), (-120, -210), (90, -230))):
        pn.line([(a, b), (a + 40, b + 30), (a + 70, b + 26)], ROCK_D, 4)
    base = -255
    def wall(x0, x1, h):
        pn.rect(x0, base - h, x1, base + 6, fill=CWALL, outline=INK, width=3.4)
        xx = x0
        while xx < x1 - 10:
            pn.rect(xx, base - h - 18, min(xx + 18, x1), base - h + 2, fill=CWALL, outline=INK, width=3)
            xx += 32
    def tower(cx, w, h, roof=False):
        pn.rect(cx - w / 2, base - h, cx + w / 2, base + 6, fill=lerpc(CWALL, INK, .08), outline=INK, width=3.4)
        for dx in (-w / 2, -w / 6, w / 6):
            pn.rect(cx + dx, base - h - 20, cx + dx + w / 6 + 2, base - h + 2, fill=lerpc(CWALL, INK, .08), outline=INK, width=3)
        pn.rect(cx - 6, base - h * 0.6, cx + 6, base - h * 0.6 + 22, fill=INK, r=6)
    wall(-230, 230, 96)
    if gap > 0:
        g = clamp(gap)
        x0, x1 = 30, 30 + 90 * g
        jag = [(x0, base - 96 - 20), (x0 + 10, base - 50 * g), (x0 + 30, base - 20 * g), ((x0 + x1) / 2, base - 8 * g),
               (x1 - 20, base - 30 * g), (x1, base - 60 * g), (x1 + 6, base - 116)]
        pn.poly(jag, fill=(214, 172, 132))
        for i in range(5):
            stone(pn, x0 + 10 + i * 18 * g, base + 2 - (i % 2) * 8, 9, seed=20 + i, col=CWALL)
    tower(-230, 70, 150); tower(230, 70, 140); tower(-70, 84, 210); tower(130, 64, 130)
    pn.pop()
    if dust > 0:
        for i in range(10):
            a = i * 0.7; r = 30 + 90 * dust
            pn.circ(x + (65 + math.cos(a) * r * .9) * k, y + (base - 60 + math.sin(a) * r * .5 - 30 * dust) * k,
                    (26 + 22 * dust) * k, fill=(200, 184, 160, int(170 * (1 - dust))))
    return (x - 70 * k, y + (base - 210 - 20) * k)

class WallBlocks:
    def __init__(s, x0=60, x1=1020, y0=640, y1=1400, bw=118, bh=62, hit=(600, 930), R=250):
        s.blocks = []
        rnd = random.Random(12)
        row = 0; y = y0
        while y < y1:
            off = 0 if row % 2 == 0 else -bw / 2
            x = x0 + off
            while x < x1:
                cx, cy = x + bw / 2, y + bh / 2
                d = math.hypot(cx - hit[0], (cy - hit[1]) * 1.2)
                moving = d < R
                col = lerpc(CWALL, STONE_D, rnd.random() * 0.35)
                s.blocks.append(dict(cx=cx, cy=cy, w=bw - 4, h=bh - 4, d=d, m=moving, col=col,
                                     vx=(cx - hit[0]) * rnd.uniform(1.2, 2.4) + rnd.uniform(-80, 80),
                                     vy=rnd.uniform(-420, -120), vr=rnd.uniform(-5, 5), delay=d / 900))
                x += bw
            y += bh; row += 1
        s.x0, s.x1, s.y0, s.y1, s.hit = x0, x1, y0, y1, hit
    def draw(s, pn, tf, crack=0.0):
        """tf: seconds since collapse start (negative = intact)."""
        for b in s.blocks:
            cx, cy, ang = b['cx'], b['cy'], 0.0
            if b['m'] and tf > b['delay']:
                u = tf - b['delay']
                cx += b['vx'] * u * 0.5; cy += b['vy'] * u + 0.5 * 2600 * u * u; ang = b['vr'] * u
                if cy > 2300: continue
            w, h = b['w'] / 2, b['h'] / 2
            ca, sa = math.cos(ang), math.sin(ang)
            pts = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in ((-w, -h), (w, -h), (w, h), (-w, h))]
            pn.poly(pts, fill=b['col'], outline=INK, width=3)
        if crack > 0 and tf < 0.05:
            hx, hy = s.hit; rnd = random.Random(3)
            for i in range(8):
                a = i / 8 * 6.28 + rnd.uniform(-.2, .2); L_ = 60 + 200 * crack * rnd.uniform(.6, 1)
                mid = (hx + math.cos(a + .2) * L_ * .5, hy + math.sin(a + .2) * L_ * .5)
                pn.line([(hx, hy), mid, (hx + math.cos(a) * L_, hy + math.sin(a) * L_)], INK, 5)

def swoosh_arrow(pn, p0, p1, bend=0.3, w_tail=5, w_body=44, head=2.6, col=(222, 32, 36), shadow=True, outline=True):
    """Curved, tapered thumbnail arrow: thin tail swelling into a thick body and a notched triangular head.
    bend: sideways bulge as a fraction of the length (sign picks the side)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; Ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / Ln, dx / Ln
    c = ((p0[0] + p1[0]) / 2 + nx * Ln * bend, (p0[1] + p1[1]) / 2 + ny * Ln * bend)
    hl = w_body * head * 0.95                    # head length
    def B(u): return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])
    # stop the body where the head starts
    N = 60; pts = [B(i / N) for i in range(N + 1)]
    acc = [0.0]
    for a, b in zip(pts[:-1], pts[1:]): acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = acc[-1]; stop = total - hl * 0.72
    left, right = [], []
    for i, (p, s) in enumerate(zip(pts, acc)):
        if s > stop: break
        q = pts[min(i + 1, N)] if i < N else p; r = pts[max(i - 1, 0)]
        tx, ty = q[0] - r[0], q[1] - r[1]; tl = math.hypot(tx, ty) or 1
        mx, my = -ty / tl, tx / tl
        w = lerp(w_tail, w_body, (s / stop) ** 0.7) / 2
        left.append((p[0] + mx * w, p[1] + my * w)); right.append((p[0] - mx * w, p[1] - my * w))
    body = left + right[::-1]
    # head: direction of the curve at its end
    e0 = pts[-6]; ex, ey = p1[0] - e0[0], p1[1] - e0[1]; el = math.hypot(ex, ey) or 1; ux, uy = ex / el, ey / el; vx, vy = -uy, ux
    hw = w_body * head / 2
    base = (p1[0] - ux * hl, p1[1] - uy * hl)
    notch = (p1[0] - ux * hl * 0.72, p1[1] - uy * hl * 0.72)
    head_pts = [p1, (base[0] + vx * hw, base[1] + vy * hw), notch, (base[0] - vx * hw, base[1] - vy * hw)]
    if shadow:
        sh = lambda P_: [(x + 10, y + 12) for x, y in P_]
        pn.poly(sh(body), fill=(0, 0, 0, 90)); pn.poly(sh(head_pts), fill=(0, 0, 0, 90))
    if outline:
        pn.poly(body, fill=INK, outline=INK, width=9); pn.poly(head_pts, fill=INK, outline=INK, width=9)
    pn.poly(body, fill=col); pn.poly(head_pts, fill=col)


# ================= E017 Macedon, 4th to 2nd century BC (period library BM-P001 to BM-P006) =================
# figure units: the rig is about 264 units tall for a man of about 1.72 m, so 1 unit is about 0.66 cm
UNIT_CM = 0.66
SARISSA_L = 830       # about 5.5 m: 12 cubits (Theophrastus); Polybius gives 14 for the 2nd century BC
DORY_L = 370          # about 2.4 m (hoplite spear, 7 to 8 ft)
ASH = (176, 140, 92); ASH_D = (132, 100, 62)
BRZ = (196, 150, 72); BRZ_D = (150, 104, 44)

def _seg(pn, a, b, w, col, outline=3.0):
    pn.line([a, b], INK, w + outline * 2, caps=False); pn.line([a, b], col, w, caps=False)

def sarissa(pn, hx, hy, ang, back=240, L=SARISSA_L, w=7.0, butt=True, head=True, flex=0.0):
    """Sarissa from a grip point: shaft of ash or cornel, iron leaf head, butt spike (attested on some, debated).
    hx, hy: the rear hand on the shaft; ang: direction of the point (radians); back: shaft length behind the hand.
    flex: slight droop of the long shaft (units at the tip)."""
    ca, sa = math.cos(ang), math.sin(ang)
    x0, y0 = hx - ca * back, hy - sa * back
    x1, y1 = x0 + ca * L, y0 + sa * L
    n = 10; pts = []
    for i in range(n + 1):
        u = i / n; d_ = flex * u * u
        pts.append((x0 + ca * L * u - sa * d_ * 0, y0 + sa * L * u + d_))
    tip = pts[-1]
    pn.line(pts, INK, w + 6, caps=False); pn.line(pts, ASH, w, caps=False)
    if lod(pn, L) >= 1:
        pn.line([(p[0] - sa * w * .25, p[1] - ca * w * .25 - w * .2) for p in pts], light(ASH, 0.35), max(1.2, w * .28), caps=False)
    # iron head: socket, then a long leaf blade with a midrib
    if head:
        hl, hw = 46, 9.5
        ex, ey = tip[0] + ca * hl, tip[1] + sa * hl
        nx, ny = -sa, ca
        sock = [(tip[0] + nx * 5 - ca * 12, tip[1] + ny * 5 - sa * 12), (tip[0] - nx * 5 - ca * 12, tip[1] - ny * 5 - sa * 12),
                (tip[0] - nx * 4.2 + ca * 8, tip[1] - ny * 4.2 + sa * 8), (tip[0] + nx * 4.2 + ca * 8, tip[1] + ny * 4.2 + sa * 8)]
        pn.poly(sock, fill=IRON, outline=INK, width=2.4)
        leaf = [(tip[0] + ca * 6, tip[1] + sa * 6), (tip[0] + ca * 18 + nx * hw, tip[1] + sa * 18 + ny * hw), (ex, ey),
                (tip[0] + ca * 18 - nx * hw, tip[1] + sa * 18 - ny * hw)]
        pn.poly(leaf, fill=IRON, outline=INK, width=2.6)
        pn.poly([(tip[0] + ca * 6, tip[1] + sa * 6), (tip[0] + ca * 18 - nx * hw, tip[1] + sa * 18 - ny * hw), (ex, ey)], fill=shade(IRON, 0.25))
        pn.line([(tip[0] + ca * 10, tip[1] + sa * 10), (ex - ca * 4, ey - sa * 4)], light(IRON, 0.6), 1.8, caps=False)
    else:
        ex, ey = tip
    if butt:   # bronze butt spike (sauroter type), also a counterweight
        bl = 30; nx, ny = -sa, ca
        bx, by_ = x0 - ca * bl, y0 - sa * bl
        pn.poly([(x0 + nx * 5, y0 + ny * 5), (x0 - nx * 5, y0 - ny * 5), (x0 - ca * 10 - nx * 4, y0 - sa * 10 - ny * 4), (bx, by_),
                 (x0 - ca * 10 + nx * 4, y0 - sa * 10 + ny * 4)], fill=BRZ, outline=INK, width=2.4)
        pn.line([(x0 - ca * 4 + nx * 2, y0 - sa * 4 + ny * 2), (bx + ca * 6, by_ + sa * 6)], light(BRZ, 0.5), 1.4, caps=False)
    return dict(tip=(ex, ey), butt=(x0 - ca * 30, y0 - sa * 30))

def dory(pn, hx, hy, ang, back=110, L=DORY_L, w=6.5):
    """Hoplite spear: ash shaft, iron leaf head, bronze sauroter at the butt. hx, hy: grip (near the balance point)."""
    return sarissa(pn, hx, hy, ang, back=back, L=L, w=w)

def pelta(pn, cx, cy, r=42, f=1, strap_to=None, deco=True):
    """Macedonian phalanx shield (pelta): bronze faced, about 60 to 74 cm, shallow and rimless, hung from the neck by a
    strap (telamon) with the forearm through a single armband. Decoration simplified: a ring of semicircles with a central
    star, as on Macedonian shield types (painted or embossed patterns varied)."""
    L_ = lod(pn, 2 * r)
    if strap_to:
        for sd in (-1, 1):
            pn.line([(strap_to[0] + sd * 16, strap_to[1]), (cx + sd * r * .55, cy - r * .78)], (96, 64, 38), 4.2)
    pn.circ(cx + 4, cy + 5, r, fill=(20, 14, 10, 60))
    pn.circ(cx, cy, r, fill=BRZ, outline=INK, width=3.2)
    pn.poly(_ell_pts_(cx, cy, r - 2, r - 2, -70, 90) + _ell_pts_(cx + r * .25, cy + r * .1, r * .62, r * .78, 90, -70), fill=shade(BRZ, 0.22))
    pn.poly(_ell_pts_(cx, cy, r - 3, r - 3, 150, 250) + _ell_pts_(cx - r * .3, cy - r * .2, r * .48, r * .55, 250, 150), fill=light(BRZ, 0.3))
    if deco and L_ >= 1:
        k_ = 7
        for i in range(k_):
            a = math.radians(i * 360 / k_ - 90)
            px, py = cx + math.cos(a) * r * .7, cy + math.sin(a) * r * .7
            pn.arc(px, py, r * .2, math.degrees(a) + 90, math.degrees(a) + 270, BRZ_D, 2.6)
        pn.circ(cx, cy, r * .42, outline=BRZ_D, width=2.4)
        for i in range(8):     # eight rayed star
            a = math.radians(i * 45)
            pn.line([(cx, cy), (cx + math.cos(a) * r * .34, cy + math.sin(a) * r * .34)], BRZ_D, 2.6)
        pn.circ(cx, cy, r * .09, fill=light(BRZ, 0.5), outline=BRZ_D, width=1.6)
    if L_ >= 2: scratches(pn, cx - r * .3, cy + r * .2, r, 5, n=2)

def aspis(pn, cx, cy, r=56, f=1, col=BRZ, device=None):
    """Hoplite aspis: deep, dished wooden shield faced with bronze, flat offset rim (antyx), about 80 to 90 cm. Carried on
    the forearm (porpax) with the hand on a cord grip at the rim (antilabe), so the hand is hidden behind it."""
    L_ = lod(pn, 2 * r)
    pn.circ(cx + 5, cy + 6, r + 3, fill=(20, 14, 10, 70))
    pn.circ(cx, cy, r, fill=shade(col, 0.1), outline=INK, width=3.4)          # rim
    pn.circ(cx, cy, r * .84, fill=col, outline=INK, width=2.4)               # bowl
    pn.poly(_ell_pts_(cx, cy, r * .84 - 2, r * .84 - 2, -70, 90) + _ell_pts_(cx + r * .2, cy + r * .08, r * .54, r * .66, 90, -70), fill=shade(col, 0.24))
    pn.poly(_ell_pts_(cx, cy, r * .84 - 3, r * .84 - 3, 150, 250) + _ell_pts_(cx - r * .26, cy - r * .18, r * .42, r * .48, 250, 150), fill=light(col, 0.32))
    if L_ >= 1:
        pn.circ(cx, cy, r * .92, outline=light(col, 0.3), width=1.6)
        for i in range(16):
            a = math.radians(i * 22.5)
            rivet(pn, cx + math.cos(a) * r * .92, cy + math.sin(a) * r * .92, 1.6, col)
    if device: device(pn, cx, cy, r * .84)
    if L_ >= 2: scratches(pn, cx + r * .2, cy - r * .3, r, 7, n=3)

def _ell_pts_(cx, cy, rx, ry, a0, a1, n=18):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

# ================= E021 Roman scorpio, late Republic (period library BM-P034 to BM-P044) =================
# The scorpio is modelled in 3D (centimetres) and projected, so the same model gives the side view, the oblique crew
# view and the top down diagram, and the arms, string and slider stay consistent in every state.
CM_U = 1 / UNIT_CM                       # figure units per centimetre (rig: 1 unit is about 0.66 cm)
OAK = (150, 108, 64); OAK_D = (112, 78, 44); SINEW = (214, 190, 146); SINEW_W = (168, 150, 120)
SC_ARM_L = 48.0; SC_SK_Y = 18.0; SC_PHI_REST = -8.0; SC_PHI_FULL = 40.0; SC_BOLT = 70.0

class Proj:
    """Orthographic view: yaw about the vertical, then pitch down. Returns screen x, screen y (down) and depth."""
    def __init__(s, yaw=0.0, pitch=18.0, scale=CM_U):
        s.cy, s.sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        s.cp, s.sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch)); s.k = scale
    def v(s, p):
        x, y, z = p
        x1 = x * s.cy - y * s.sy; y1 = x * s.sy + y * s.cy
        dep = y1 * s.cp - z * s.sp; up = z * s.cp + y1 * s.sp
        return x1 * s.k, -up * s.k, dep
    def n(s, nv):   # normal in view space (x right, y up, z toward viewer)
        x, y, z = nv
        x1 = x * s.cy - y * s.sy; y1 = x * s.sy + y * s.cy
        return (x1, z * s.cp + y1 * s.sp, -(y1 * s.cp - z * s.sp))

_LIGHT = (-0.45, 0.62, 0.64)
def _lit(pr, nrm, col, amb=0.62):
    vx, vy, vz = pr.n(nrm)
    if vz < -0.02: return None          # back face
    dl = max(0.0, vx * _LIGHT[0] + vy * _LIGHT[1] + vz * _LIGHT[2])
    return shade(col, 0.30 * (1 - dl)) if dl < 0.75 else light(col, (dl - 0.75) * 0.7)

def _box(Q, pr, x0, x1, y0, y1, z0, z1, col, grain=False, tag=None, iron=False):
    c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    faces = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]
    for idx, nrm in faces:
        fc = _lit(pr, nrm, col)
        if fc is None: continue
        P3 = [c[i] for i in idx]
        dep = sum(pr.v(p)[2] for p in P3) / 4 - 0.01 * abs(nrm[2])
        Q.append((dep, 'poly', [pr.v(p)[:2] for p in P3], fc, (grain, P3, col, iron)))

def _cyl(Q, pr, cx, cy, z0, z1, r, col, n=14, twist=None, strand=None):
    """Vertical cylinder. twist: angle (radians) of the strand helix per unit height, for sinew skeins."""
    ring = lambda z: [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]
    lo, hi = ring(z0), ring(z1)
    for i in range(n):
        j = (i + 1) % n
        a = 2 * math.pi * (i + 0.5) / n
        fc = _lit(pr, (math.cos(a), math.sin(a), 0), col)
        if fc is None: continue
        P3 = [lo[i], lo[j], hi[j], hi[i]]
        dep = sum(pr.v(p)[2] for p in P3) / 4
        Q.append((dep, 'poly', [pr.v(p)[:2] for p in P3], fc, None))
    for ringp, nz in ((hi, 1), (lo, -1)):
        fc = _lit(pr, (0, 0, nz), col)
        if fc is not None:
            dep = sum(pr.v(p)[2] for p in ringp) / n - 0.02
            Q.append((dep, 'poly', [pr.v(p)[:2] for p in ringp], fc, None))
    if twist is not None:      # helical strands on the near side
        m = 9
        for i in range(m):
            a0 = 2 * math.pi * i / m; pts = []
            for jj in range(13):
                z = lerp(z0 + 1, z1 - 1, jj / 12); a = a0 + twist * (z - z0)
                pts.append((cx + r * 1.01 * math.cos(a), cy + r * 1.01 * math.sin(a), z))
            segs = []
            for p in pts:
                nn = pr.n(((p[0] - cx) / r, (p[1] - cy) / r, 0))
                segs.append((pr.v(p), nn[2] > 0.05))
            run = []
            for (sxy, vis) in segs:
                if vis: run.append(sxy)
                elif run:
                    if len(run) > 1: Q.append((sum(q[2] for q in run) / len(run) - 0.5, 'line', [q[:2] for q in run], strand or shade(col, 0.4), 1.4))
                    run = []
            if len(run) > 1: Q.append((sum(q[2] for q in run) / len(run) - 0.5, 'line', [q[:2] for q in run], strand or shade(col, 0.4), 1.4))

def _beam(Q, pr, a, b, w, h, col, iron=False, seg=24.0):
    """Square section beam from 3D point a to b, w wide, h tall. Long beams are split so the depth sort holds."""
    Lb = math.dist(a, b)
    if Lb > seg * 1.5:
        n = int(Lb // seg) + 1
        for i in range(n):
            p0 = tuple(lerp(a[j], b[j], i / n) for j in range(3)); p1 = tuple(lerp(a[j], b[j], (i + 1) / n) for j in range(3))
            _beam1(Q, pr, p0, p1, w, h, col, iron, ends=(i == 0, i == n - 1))
        return
    _beam1(Q, pr, a, b, w, h, col, iron)

def _beam1(Q, pr, a, b, w, h, col, iron=False, ends=(True, True)):
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]; L_ = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
    u = (dx / L_, dy / L_, dz / L_)
    up = (0, 0, 1) if abs(u[2]) < 0.9 else (1, 0, 0)
    sv = (u[1] * up[2] - u[2] * up[1], u[2] * up[0] - u[0] * up[2], u[0] * up[1] - u[1] * up[0])
    sl = math.sqrt(sum(c * c for c in sv)) or 1; sv = tuple(c / sl for c in sv)
    tv = (sv[1] * u[2] - sv[2] * u[1], sv[2] * u[0] - sv[0] * u[2], sv[0] * u[1] - sv[1] * u[0])
    def P(p, s_, t_): return (p[0] + sv[0] * s_ + tv[0] * t_, p[1] + sv[1] * s_ + tv[1] * t_, p[2] + sv[2] * s_ + tv[2] * t_)
    hw, hh = w / 2, h / 2
    quads = [((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    for i in range(4):
        s0, t0 = corners[i]; s1, t1 = corners[(i + 1) % 4]
        nm = ((s0 + s1) / 2, (t0 + t1) / 2); nl = math.hypot(*nm) or 1
        nrm = tuple((sv[k] * nm[0] + tv[k] * nm[1]) / nl for k in range(3))
        fc = _lit(pr, nrm, col)
        if fc is None: continue
        P3 = [P(a, s0, t0), P(b, s0, t0), P(b, s1, t1), P(a, s1, t1)]
        dep = sum(pr.v(p)[2] for p in P3) / 4
        Q.append((dep, 'poly', [pr.v(p)[:2] for p in P3], fc, (not iron, P3, col, iron)))
    for (end, sg), on in zip(((a, -1), (b, 1)), ends):
        if not on: continue
        nrm = tuple(u[k] * sg for k in range(3)); fc = _lit(pr, nrm, shade(col, 0.15))
        if fc is None: continue
        P3 = [P(end, s_, t_) for s_, t_ in corners]
        dep = sum(pr.v(p)[2] for p in P3) / 4
        Q.append((dep, 'poly', [pr.v(p)[:2] for p in P3], fc, None))

def _flush(pn, Q, L_):
    Q.sort(key=lambda q: -q[0])
    for q in Q:
        if q[1] == 'poly':
            pts, fc, extra = q[2], q[3], q[4]
            pn.poly(pts, fill=fc, outline=INK, width=2.2 if L_ >= 1 else 2.6)
            if extra and L_ >= 1:
                grain, P3, col, iron = extra
                if iron:
                    pn.line([lerp2(pts[0], pts[3], .3), lerp2(pts[1], pts[2], .3)], light(col, 0.5), 1.4, caps=False)
                elif grain:
                    e1 = math.dist(pts[0], pts[1]); e2 = math.dist(pts[1], pts[2])
                    if max(e1, e2) * pn.k() > 60:
                        a0, a1, b0, b1 = (pts[0], pts[1], pts[3], pts[2]) if e1 >= e2 else (pts[1], pts[2], pts[0], pts[3])
                        for fr in ((0.33, 0.7) if L_ == 1 else (0.22, 0.5, 0.78)):
                            p0 = lerp2(a0, b0, fr); p1 = lerp2(a1, b1, fr)
                            pn.line([lerp2(p0, p1, .06), lerp2(p0, p1, .94)], shade(fc, 0.28) + (200,), 1.1, caps=False)
        elif q[1] == 'line':
            pn.line(q[2], INK, q[4] + 2.2); pn.line(q[2], q[3], q[4])
        elif q[1] == 'fn':
            q[2](pn)

def lerp2(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

def scorpio_state(draw):
    """Arm angle, claw position and arm tips (3D, cm) for a draw of 0 (braced, at rest) to 1 (full draw)."""
    phi = math.radians(lerp(SC_PHI_REST, SC_PHI_FULL, draw))
    pr_ = math.radians(SC_PHI_REST)
    half = SC_SK_Y + SC_ARM_L * math.cos(pr_)
    tip_x = -SC_ARM_L * math.sin(phi); tip_y = SC_SK_Y + SC_ARM_L * math.cos(phi)
    xc = tip_x - math.sqrt(max(0.0, half * half - tip_y * tip_y))
    return phi, xc, tip_x, tip_y

def scorpio(pn, x, y, k=1.0, draw=0.0, yaw=-8.0, pitch=16.0, twist=0.0, slack=0.0, bolt=False, bolt_out=None,
            winch_a=0.0, trigger=0.0, stand=True, aim=0.0, labels=None, ghost_bow=0.0, H0=122.0):
    """Roman scorpio of the Vitruvian type (BM-P034). (x, y) is the ground point under the stand; k the figure scale.
    draw 0..1 string pulled back by the winch; twist adds turns to the washers (wind up beat); slack 0..1 is a rain
    soaked spring (skeins bulge, darken and untwist, the string sags); bolt draws a loaded bolt; bolt_out = forward travel
    in cm of a bolt leaving the groove; trigger 0..1 lifts the trigger lever; aim tilts the stock (degrees, up positive).
    Returns screen points (world) for hands and effects."""
    pn.push(x, y, k)
    pr = Proj(yaw, pitch, CM_U)
    L_ = lod(pn, 160 * CM_U)
    Q = []
    # H0: case top above the ground. 122 cm is the real height; scenes with the rig use about 92 so the stock sits at the
    # big headed rig's chest (the rig's legs are short for its height)
    phi, xc, tip_x, tip_y = scorpio_state(draw)
    ca, sa = math.cos(math.radians(aim)), math.sin(math.radians(aim))
    def M(p):   # machine local to world: tilt about the pivot (x=-30, z=-8), then lift to H0
        px, py, pz = p[0] + 30, p[1], p[2] + 8
        return (px * ca - pz * sa - 30, py, px * sa + pz * ca - 8 + H0)
    class MP:   # projector wrapper that applies the machine tilt
        def v(s_, p): return pr.v(M(p))
        def n(s_, nv): return pr.n((nv[0] * ca - nv[2] * sa, nv[1], nv[0] * sa + nv[2] * ca))
    mp = MP()
    # ---- stand (world, not tilted): post, pivot block, three legs
    if stand:
        g = 0.0
        _beam(Q, pr, (-30, 0, H0 - 16), (-30, 0, H0 * 0.38), 7, 7, OAK_D)
        for ang in (90, 210, 330):
            a_ = math.radians(ang)
            _beam(Q, pr, (-30, 0, H0 * 0.41), (-30 + math.cos(a_) * 52, math.sin(a_) * 52, g + 2), 5.5, 5.5, OAK_D)
        _box(Q, pr, -37, -23, -7, 7, H0 - 22, H0 - 12, IRON, iron=True)
        Q.append((99, 'fn', lambda p_: p_.ell(*pr.v((-30, 0, 0))[:2], 62 * CM_U, 12 * CM_U, fill=(20, 14, 10, 60))))
    # ---- case (stock) and rear cheeks
    _box(Q, mp, -115, 26, -5, 5, -10, 0, OAK, grain=True)
    for sy_ in (-1, 1):
        _box(Q, mp, -114, -102, sy_ * 5, sy_ * 9, -14, 3, OAK_D, grain=True)
    # ratchet strip with teeth on the near side
    _box(Q, mp, -100, -12, -6.5, -5, -4, 0, IRON, iron=True)
    def teeth(p_):
        for i in range(12):
            xx = -98 + i * 7.2
            a_, b_, c_ = mp.v((xx, -6.6, 0)), mp.v((xx + 3.6, -6.6, 1.8)), mp.v((xx + 7.2, -6.6, 0))
            p_.line([a_[:2], b_[:2], c_[:2]], INK, 1.2, caps=False)
    if L_ >= 1: Q.append((mp.v((-55, -7, 0))[2] - 0.3, 'fn', teeth))
    # ---- windlass: axle, drum and four handspikes each side
    wx, wz = -108, -5
    _beam(Q, mp, (wx, -13, wz), (wx, 13, wz), 4, 4, OAK_D)
    for sy_ in (-1, 1):
        for i in range(4):
            a_ = winch_a + i * math.pi / 2
            _beam(Q, mp, (wx, sy_ * 13, wz), (wx + math.cos(a_) * 17, sy_ * 13, wz + math.sin(a_) * 17), 2.6, 2.6, OAK)
    # ---- slider with claw; rope from the windlass drum to the slider when drawn
    _box(Q, mp, xc, xc + 58, -3.6, 3.6, 0, 3.6, light(OAK, 0.08), grain=True)
    _box(Q, mp, xc - 4, xc + 5, -3, 3, 3.6, 9.5, IRON, iron=True)          # claw block
    tl = math.radians(lerp(-62, -30, trigger))
    _beam(Q, mp, (xc + 1, -3.4, 7), (xc + 1 - math.cos(tl) * 13, -3.4, 7 + math.sin(tl) * 13), 1.8, 1.8, IRON, iron=True)
    if draw > 0.02:
        ra, rb = mp.v((wx, 0, wz + 2)), mp.v((xc - 4, 0, 1.5))
        Q.append(((ra[2] + rb[2]) / 2 - 0.2, 'line', [ra[:2], rb[:2]], ROPE, 1.6))
    # ---- capitulum: boards, posts, stanchions, iron corner plates
    zt0, zt1, zb0, zb1 = 21, 26, -34, -29
    _box(Q, mp, -7, 7, -35, 35, zt0, zt1, OAK, grain=True)
    _box(Q, mp, -7, 7, -35, 35, zb0, zb1, OAK, grain=True)
    for sy_ in (-1, 1):
        _box(Q, mp, -5, 5, sy_ * 28, sy_ * 34, zb1, zt0, OAK_D, grain=True)
        _box(Q, mp, -5, 5, sy_ * 5, sy_ * 10, zb1, zt0, OAK_D, grain=True)
    # skeins with washers and lever bars
    tw_ = (2.2 + twist) * (1 - 0.75 * slack)
    skr = 6.4 * (1 + 0.22 * slack)
    skc = lerpc(SINEW, (120, 104, 82), slack * 0.8)
    for sy_ in (-1, 1):
        cy_ = sy_ * SC_SK_Y
        _cyl(Q, mp, 0, cy_, zb1, zt0, skr, skc, twist=sy_ * tw_ * 0.06 + sy_ * phi * 0.012, strand=shade(skc, 0.42))
        for zz, d_ in ((zt1, 1), (zb0, -1)):
            z0_, z1_ = (zz, zz + 4) if d_ > 0 else (zz - 4, zz)
            _cyl(Q, mp, 0, cy_, z0_, z1_, 9.5, BRZ, n=16)
            ba = sy_ * (0.35 + twist * 0.55)
            zb_ = z1_ + 1.2 if d_ > 0 else z0_ - 1.2
            _beam(Q, mp, (-math.cos(ba) * 11, cy_ - math.sin(ba) * 11, zb_), (math.cos(ba) * 11, cy_ + math.sin(ba) * 11, zb_), 2.6, 2.2, IRON, iron=True)
    # arms: from the skein centre out through the bundle; tips carry the string nocks
    for sy_ in (-1, 1):
        root = (0, sy_ * SC_SK_Y, -4)
        tip = (tip_x, sy_ * tip_y, -4)
        droop = 2.5 * slack
        _beam(Q, mp, root, (tip[0], tip[1], tip[2] - droop), 4.4, 5.2, OAK)
        _box(Q, mp, tip[0] - 1.6, tip[0] + 1.6, tip[1] - 1.6 * sy_ - 1.6, tip[1] - 1.6 * sy_ + 1.6, -6.5 - droop, -1.5 - droop, IRON, iron=True)
    # bowstring: two straight halves to the claw (sags when slack and at rest)
    sag = 7 * slack * (1 - draw)
    for sy_ in (-1, 1):
        a_ = (tip_x, sy_ * tip_y, -4 - 2.5 * slack)
        b_ = (xc - 1, 0, 6) if draw > 0.02 else (tip_x, 0, -4 - sag)
        pts = [mp.v((lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u), lerp(a_[2], b_[2], u) - sag * math.sin(math.pi * u) * (draw <= 0.02))) for u in (0, .25, .5, .75, 1)]
        Q.append((sum(p[2] for p in pts) / 5 - 0.6, 'line', [p[:2] for p in pts], SINEW_W, 1.5))
    # bolt in the groove (nock at the claw) or leaving
    if bolt or bolt_out is not None:
        bx0 = (xc if bolt_out is None else xc + bolt_out) + 2
        a_, b_ = mp.v((bx0, 0, 5.2)), mp.v((bx0 + SC_BOLT, 0, 5.2))
        def bolt_fn(p_, a_=a_, b_=b_):
            ang_ = math.atan2(b_[1] - a_[1], b_[0] - a_[0]); Ls = math.dist(a_[:2], b_[:2])
            catapult_bolt(p_, a_[0], a_[1], ang_, Ls)
        Q.append((min(a_[2], b_[2]) - 2, 'fn', bolt_fn))
    if ghost_bow > 0:   # the bow it does NOT have: a faint bent bow outline over the frame
        def gb(p_):
            pts = [mp.v((-14 * math.sin(math.pi * u) ** 1 * 1.0 + 4, lerp(-62, 62, u), 2))[:2] for u in [i / 16 for i in range(17)]]
            p_.line(pts, (38, 30, 22, int(150 * ghost_bow)), 3.4)
        Q.append((-999, 'fn', gb))
    _flush(pn, Q, L_)
    def Wp(p3, tilt=True):
        sx_, sy_, _ = (mp if tilt else pr).v(p3)
        return (x + sx_ * k, y + sy_ * k)
    res = dict(claw=Wp((xc, 0, 8)), trigger=Wp((xc + 1 - math.cos(tl) * 13, -3.4, 7 + math.sin(tl) * 13)),
               stock=Wp((-70, -5, -5)), winch=Wp((wx, -13, wz)), handspike=Wp((wx + math.cos(winch_a) * 17, -13, wz + math.sin(winch_a) * 17)),
               skein_l=Wp((0, -SC_SK_Y, 0)), skein_r=Wp((0, SC_SK_Y, 0)), muzzle=Wp((26, 0, 5)), bolt_tip=Wp(((xc if bolt_out is None else xc + bolt_out) + 2 + SC_BOLT, 0, 5)),
               tip_l=Wp((tip_x, -tip_y, -4)), tip_r=Wp((tip_x, tip_y, -4)), washer_top=Wp((0, -SC_SK_Y, zt1 + 4)), sight=Wp((-112, 0, 8)))
    pn.pop()
    if labels:
        for name, (lx, ly) in labels.items():
            if name in res: callout(pn, res[name][0], res[name][1], lx, ly, name.upper().replace('_', ' '), sz=30)
    return res

def catapult_bolt(pn, x0, y0, ang, L=None, head_only=False, k=1.0, vanes=True):
    """Roman catapult bolt (BM-P036): short four sided pyramidal iron point on a conical socket with a rivet, ash shaft,
    three thin vanes at the rear. (x0, y0) is the nock; ang the flight direction; L its length on screen (default 70 cm)."""
    L = L if L is not None else SC_BOLT * CM_U * k
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    q = lambda u, v: (x0 + ca * u + nx * v, y0 + sa * u + ny * v)
    sw = max(1.2, L * 0.022); hl = L * 0.13; sk = L * 0.07
    L_ = lod(pn, L)
    if not head_only:
        pn.line([q(0, 0), q(L - hl - sk * .5, 0)], INK, sw + 2.6, caps=False)
        pn.line([q(0, 0), q(L - hl - sk * .5, 0)], ASH, sw, caps=False)
        if L_ >= 1: pn.line([q(L * .04, -sw * .25), q(L - hl - sk, -sw * .25)], light(ASH, 0.4), max(1.0, sw * .3), caps=False)
        if vanes:
            vl = L * 0.16
            for sg in (-1, 1):
                pn.poly([q(L * .02, sg * sw * .4), q(L * .02 + vl * .85, sg * sw * .4), q(L * .02 + vl, sg * sw * 2.6), q(L * .03, sg * sw * 2.8)],
                        fill=(206, 186, 146), outline=INK, width=1.6)
    # socket then pyramid point
    s0 = L - hl - sk
    sock = [q(s0, sw * .7), q(s0 + sk, sw * .95), q(s0 + sk, -sw * .95), q(s0, -sw * .7)]
    pn.poly(sock, fill=IRON, outline=INK, width=1.8)
    pt = [q(s0 + sk, sw * 1.05), q(L, 0), q(s0 + sk, -sw * 1.05)]
    pn.poly(pt, fill=IRON, outline=INK, width=1.8)
    pn.poly([q(s0 + sk, 0), q(L, 0), q(s0 + sk, -sw * 1.05)], fill=shade(IRON, 0.3))
    if L_ >= 1:
        pn.line([q(s0 + sk + 1, sw * .45), q(L - 2, sw * .05)], light(IRON, 0.6), 1.2, caps=False)
        rivet(pn, *q(s0 + sk * .45, 0), max(1.0, sw * .35), IRON)

def bolt_head_insert(pn, cx, cy, s=1.0, rust=0.5):
    """Close up of an excavated Hod Hill type bolt head (British Museum 1892,0901.1141: thin pyramidal head, conical socket
    with a rivet across it, 88 mm). Drawn horizontally, point right, about s * 600 units long; rust 0..1 corrosion."""
    Lh = 600 * s; x0 = cx - Lh / 2
    col = lerpc(IRON, (128, 84, 56), rust)
    sock = [(x0, cy - 34 * s), (x0 + Lh * .52, cy - 26 * s), (x0 + Lh * .52, cy + 26 * s), (x0, cy + 34 * s)]
    pn.poly(sock, fill=col, outline=INK, width=3.4)
    pn.poly([(x0, cy + 6 * s), (x0 + Lh * .52, cy + 4 * s), (x0 + Lh * .52, cy + 26 * s), (x0, cy + 34 * s)], fill=shade(col, 0.25))
    pn.line([(x0 + 8 * s, cy - 22 * s), (x0 + Lh * .5, cy - 16 * s)], light(col, 0.4), 4 * s, caps=False)
    pn.line([(x0 + 4 * s, cy - 2 * s), (x0 + 90 * s, cy - 1 * s)], shade(col, 0.5), 3 * s, caps=False)   # split in the socket
    rivet(pn, x0 + Lh * .2, cy, 9 * s, col)
    tip = [(x0 + Lh * .52, cy - 30 * s), (x0 + Lh, cy), (x0 + Lh * .52, cy + 30 * s)]
    pn.poly(tip, fill=col, outline=INK, width=3.4)
    pn.poly([(x0 + Lh * .52, cy), (x0 + Lh, cy), (x0 + Lh * .52, cy + 30 * s)], fill=shade(col, 0.3))
    pn.line([(x0 + Lh * .54, cy - 12 * s), (x0 + Lh * .97, cy - 1 * s)], light(col, 0.55), 3 * s, caps=False)
    rnd = random.Random(21)
    for _ in range(int(26 * rust)):
        px_, py_ = x0 + rnd.uniform(.05, .9) * Lh, cy + rnd.uniform(-20, 20) * s
        pn.circ(px_, py_, rnd.uniform(2, 6) * s, fill=lerpc(col, (150, 92, 52), 0.6) + (170,))

def skein_diagram(pn, cx, cy, s=1.0, twist=0.0, arm=0.0, slack=0.0, labels=True, lab_p=1.0):
    """Cutaway front elevation of one torsion spring (BM-P035): frame boards, bronze washers with iron lever bars, the
    bundle of sinew loops, and the arm pushed through its middle. twist 0..1 winds the strands into a steeper helix;
    arm is the arm's swing in degrees (seen from the front it shortens as it swings back); slack sags the bundle."""
    H_ = 520 * s; Wb = 190 * s * (1 + 0.25 * slack)
    top, bot = cy - H_ / 2, cy + H_ / 2
    col = lerpc(SINEW, (120, 104, 82), slack * 0.8)
    # frame boards behind
    for yy in (top - 56 * s, bot + 8 * s):
        wood_plank_(pn, (cx - 300 * s, yy + 24 * s), (cx + 300 * s, yy + 24 * s), 48 * s, OAK)
    # bundle
    bow = 18 * s * slack
    left = [(cx - Wb / 2 - bow * math.sin(math.pi * u), lerp(top, bot, u)) for u in [i / 12 for i in range(13)]]
    right = [(cx + Wb / 2 + bow * math.sin(math.pi * u), lerp(bot, top, u)) for u in [i / 12 for i in range(13)]]
    pn.poly(left + right, fill=col, outline=INK, width=3.4)
    pn.poly([(cx + Wb * .15, top)] + right[::-1][1:] + [(cx + Wb * .15, bot)], fill=shade(col, 0.18))
    nstr = 13; ang = lerp(0.12, 0.75, clamp(twist)) * (1 - 0.8 * slack)
    for i in range(nstr):
        x_ = lerp(-Wb / 2, Wb / 2, (i + .5) / nstr)
        pts = []
        for j in range(15):
            u = j / 14; yy = lerp(top + 6 * s, bot - 6 * s, u)
            xx = cx + ((x_ / (Wb / 2) + math.tan(ang) * (u - .5) * 2.2 + 1) % 2 - 1) * (Wb / 2 - 4 * s)
            pts.append((xx, yy))
        run = [pts[0]]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            if abs(p1[0] - p0[0]) > Wb * .5:
                if len(run) > 1: pn.line(run, shade(col, 0.42), 2.6 * s, caps=False)
                run = [p1]
            else: run.append(p1)
        if len(run) > 1: pn.line(run, shade(col, 0.42), 2.6 * s, caps=False)
    # washers and lever bars
    for yy, sg in ((top, -1), (bot, 1)):
        pn.ell(cx, yy, 150 * s, 30 * s, fill=BRZ, outline=INK, width=3.4)
        pn.ell(cx, yy + sg * 10 * s, 150 * s, 30 * s, fill=BRZ_D, outline=INK, width=3.0)
        pn.ell(cx, yy, 150 * s, 30 * s, fill=BRZ, outline=INK, width=3.0)
        for i in range(6):
            a_ = math.radians(-160 + i * 15)
            rivet(pn, cx + math.cos(a_) * 128 * s, yy + math.sin(a_) * 24 * s, 7 * s, BRZ)
        ba = math.radians(18 + twist * 40)
        bx_, by_ = math.cos(ba) * 175 * s, math.sin(ba) * 22 * s
        pn.line([(cx - bx_, yy - by_ - 8 * s), (cx + bx_, yy + by_ - 8 * s)], INK, 26 * s)
        pn.line([(cx - bx_, yy - by_ - 8 * s), (cx + bx_, yy + by_ - 8 * s)], IRON, 18 * s)
        pn.line([(cx - bx_ * .9, yy - by_ * .9 - 13 * s), (cx + bx_ * .9, yy + by_ * .9 - 13 * s)], light(IRON, 0.5), 3 * s, caps=False)
    # arm through the middle, projecting toward the viewer and out to the right
    al = 360 * s * math.cos(math.radians(arm)) + 40 * s
    pn.poly([(cx - 22 * s, cy - 30 * s), (cx + al, cy - 18 * s), (cx + al, cy + 18 * s), (cx - 22 * s, cy + 30 * s)], fill=OAK, outline=INK, width=3.4)
    pn.poly([(cx - 22 * s, cy + 4 * s), (cx + al, cy + 2 * s), (cx + al, cy + 18 * s), (cx - 22 * s, cy + 30 * s)], fill=shade(OAK, 0.22))
    pn.line([(cx, cy - 12 * s), (cx + al - 10 * s, cy - 8 * s)], shade(OAK, 0.35), 2 * s, caps=False)
    pn.rect(cx + al - 18 * s, cy - 24 * s, cx + al + 6 * s, cy + 24 * s, fill=IRON, outline=INK, width=2.8)
    if labels and lab_p > 0:
        callout(pn, cx - Wb * .3, cy + H_ * .3, cx - 300 * s, cy + H_ * .3 + 40 * s, 'SINEW', p=pop(lab_p, 0.0), sz=34)
        callout(pn, cx - 120 * s, top, cx - 300 * s, top - 90 * s, 'WASHER', p=pop(lab_p, 0.15), sz=34)
        callout(pn, cx + al * .7, cy, cx + al * .55, cy + 170 * s, 'ARM', p=pop(lab_p, 0.3), sz=34)

def wood_plank_(pn, a, b, w, col):
    from detail import wood_plank
    wood_plank(pn, a, b, w, col)

THATCH = (176, 146, 92); DAUB = (184, 160, 120); HIDE = (124, 88, 56); CHALK = (226, 222, 204); TURF = (126, 140, 86)
BALSA = (226, 200, 150); RUBBER = (150, 104, 70); PLANE_RED = (196, 52, 40)

def toy_plane(pn, x, y, k=1.0, prop_a=0.0, wind=0.0, ang=0.0, blur=0.0):
    """Rubber powered stick model (BM-P043), side view, nose to the right. (x, y) is the grip point under the wing;
    wind 0..1 bunches the rubber motor into knots; prop_a the propeller angle; blur 0..1 a spinning disc."""
    pn.push(x, y, k)
    u = CM_U; ca, sa = math.cos(ang), math.sin(ang)
    R = lambda px_, py_: (px_ * ca - py_ * sa, px_ * sa + py_ * ca)
    L_ = lod(pn, 60 * u)
    stick = [R(-30 * u, -1.2 * u), R(22 * u, -1.2 * u), R(22 * u, 1.2 * u), R(-30 * u, 1.2 * u)]
    # wing (seen edge on with a little camber), tail and fin
    pn.poly([R(-6 * u, -1.2 * u), R(-2 * u, -4.2 * u), R(10 * u, -4.6 * u), R(12 * u, -1.2 * u)], fill=(244, 238, 222), outline=INK, width=2.4)
    pn.poly([R(-30 * u, -1.2 * u), R(-34 * u, -10 * u), R(-27 * u, -10 * u), R(-23 * u, -1.2 * u)], fill=(244, 238, 222), outline=INK, width=2.4)
    pn.poly([R(-31 * u, 0), R(-21 * u, -0.5 * u), R(-21 * u, 1.5 * u), R(-31 * u, 1.8 * u)], fill=(244, 238, 222), outline=INK, width=2.0)
    pn.poly(stick, fill=BALSA, outline=INK, width=2.4)
    if L_ >= 1: pn.line([R(-28 * u, -0.3 * u), R(20 * u, -0.3 * u)], light(BALSA, 0.4), 1.2, caps=False)
    # rubber motor under the stick, hook to hook; knots bunch it
    hook_r, hook_f = R(-24 * u, 3.5 * u), R(20 * u, 3.5 * u)
    n = 22; pts = []
    for i in range(n + 1):
        t_ = i / n
        bump = wind * 1.8 * u * abs(math.sin(t_ * math.pi * (4 + 10 * wind)))
        pts.append(R(lerp(-24 * u, 20 * u, t_), 3.5 * u + 1.2 * u * math.sin(math.pi * t_) * (1 - wind) + bump))
    pn.line(pts, INK, 3.4 + 2.2 * wind); pn.line(pts, RUBBER, 1.8 + 2.2 * wind)
    if wind > 0.2 and L_ >= 1:
        for i in range(int(3 + 9 * wind)):
            p_ = pts[int(lerp(2, n - 2, (i + .5) / (3 + 9 * wind)))]
            pn.circ(p_[0], p_[1], (1.2 + 1.4 * wind) * u, fill=shade(RUBBER, 0.25), outline=INK, width=1.4)
    for hk in (hook_r, hook_f): pn.circ(hk[0], hk[1], 0.9 * u, fill=IRON)
    # nose block and propeller (two blades seen from the side: length foreshortens with the angle)
    nb = R(24 * u, 0)
    pn.poly([R(22 * u, -1.6 * u), R(25.5 * u, -1.2 * u), R(25.5 * u, 3.6 * u), R(22 * u, 3.8 * u)], fill=(90, 90, 96), outline=INK, width=2)
    hub = R(26.5 * u, 1.4 * u)
    if blur > 0.5:
        pn.ell(hub[0], hub[1], 1.6 * u, 11 * u, fill=PLANE_RED + (90,), outline=INK + (120,), width=1.4)
    else:
        sp_ = 11 * u * math.cos(prop_a)
        for sg in (-1, 1):
            pn.poly([(hub[0] - 0.9 * u, hub[1]), (hub[0] - 1.6 * u, hub[1] + sg * sp_), (hub[0] + 1.6 * u, hub[1] + sg * sp_ * 0.96), (hub[0] + 0.9 * u, hub[1])],
                    fill=PLANE_RED, outline=INK, width=1.8)
    pn.circ(hub[0], hub[1], 1.3 * u, fill=shade(PLANE_RED, 0.3), outline=INK, width=1.4)
    pn.pop()
    W_ = lambda p_: (x + p_[0] * k, y + p_[1] * k)
    return dict(grip=W_(R(2 * u, 2 * u)), hub=W_(hub), prop_tip=W_((hub[0], hub[1] - 11 * u)))

def rubber_ecu(pn, cx, cy, s=1.0, wind=0.0, t=0.0):
    """Extreme close up of a twisted rubber motor running vertically (it match cuts to the sinew skein): strands wind into
    a helix that steepens with wind, then double back into knots."""
    H_ = 560 * s; top, bot = cy - H_ / 2, cy + H_ / 2
    n = 6; ang = lerp(0.1, 1.15, clamp(wind))
    # hooks
    for yy, sg in ((top, -1), (bot, 1)):
        pn.arc(cx, yy + sg * 18 * s, 34 * s, 0 if sg > 0 else 180, 180 if sg > 0 else 360, INK, 16 * s)
        pn.arc(cx, yy + sg * 18 * s, 34 * s, 0 if sg > 0 else 180, 180 if sg > 0 else 360, IRON, 9 * s)
    for i in range(n):
        ph = 2 * math.pi * i / n + t * 0.0
        pts = []
        for j in range(41):
            u = j / 40; yy = lerp(top, bot, u)
            a_ = ph + math.tan(ang) * (u - .5) * 9
            xx = cx + math.sin(a_) * 34 * s * (1 + 0.25 * wind)
            pts.append((xx, yy, math.cos(a_)))
        for j in range(40):
            p0, p1 = pts[j], pts[j + 1]
            front = (p0[2] + p1[2]) > 0
            col = light(RUBBER, 0.25) if front else shade(RUBBER, 0.25)
            pn.line([(p0[0], p0[1]), (p1[0], p1[1])], INK, 16 * s, caps=False)
            pn.line([(p0[0], p0[1]), (p1[0], p1[1])], col, 10 * s, caps=False)
    if wind > 0.55:   # knots: the twist doubles back on itself
        rnd = random.Random(5)
        for i in range(int((wind - 0.55) * 18)):
            yy = lerp(top + 60 * s, bot - 60 * s, rnd.random()); xx = cx + rnd.uniform(-30, 30) * s
            r_ = rnd.uniform(18, 30) * s
            pn.circ(xx, yy, r_, fill=RUBBER, outline=INK, width=4 * s)
            pn.arc(xx, yy, r_ * .6, 200, 320, light(RUBBER, 0.35), 4 * s)

def murus_gallicus(pn, x0, x1, y_top, y_bot, seed=3, beams=True, walk=True):
    """Gallic rampart (BM-P040) seen from outside: dry stone face with the ends of the cross beams showing at regular
    intervals (Caesar 7.23), a timber breastwork on the wall walk."""
    rnd = random.Random(seed)
    pn.rect(x0, y_top, x1, y_bot, fill=STONE_D)
    row_h = 34
    y = y_top + 4; r_i = 0
    while y < y_bot:
        x = x0 - rnd.uniform(0, 40)
        while x < x1:
            w_ = rnd.uniform(46, 90)
            c = lerpc(STONE, (168, 158, 140), rnd.random() * 0.6)
            pn.rect(x + 2, y + 2, x + w_ - 2, y + row_h - 2, fill=c, outline=INK, width=1.6, r=5)
            pn.line([(x + 6, y + 6), (x + w_ - 8, y + 6)], light(c, 0.3), 1.6, caps=False)
            x += w_
        y += row_h; r_i += 1
    if beams:   # beam ends every two feet, in rows
        for j, yy in enumerate(range(int(y_top + 50), int(y_bot - 20), 110)):
            off = 60 if j % 2 else 0
            for xx in range(int(x0 + 40 + off), int(x1), 120):
                pn.rect(xx - 13, yy - 13, xx + 13, yy + 13, fill=WOOD, outline=INK, width=2.2, r=3)
                pn.circ(xx, yy, 7, outline=shade(WOOD, 0.4), width=1.4)
    if walk:
        for xx in range(int(x0), int(x1) + 40, 44):
            pn.rect(xx, y_top - 70, xx + 40, y_top + 2, fill=lerpc(WOOD, PARCH, 0.12), outline=INK, width=2.2)
            pn.line([(xx + 10, y_top - 64), (xx + 10, y_top - 4)], shade(WOOD, 0.3), 1.4, caps=False)
        pn.rect(x0, y_top - 78, x1, y_top - 66, fill=WOOD_D, outline=INK, width=2.4)

def gallic_tower(pn, x, y_base, k=1.0, storeys=3):
    """Storied timber tower on the rampart, its front covered with hides against fire (Caesar 7.22)."""
    pn.push(x, y_base, k)
    for i in range(storeys):
        y0 = -i * 110
        pn.rect(-70, y0 - 110, 70, y0, fill=HIDE, outline=INK, width=3)
        for j in range(3):
            pn.line([(-70 + 47 * j + 10, y0 - 104), (-70 + 47 * j + 34, y0 - 8)], shade(HIDE, 0.3), 2, caps=False)
        pn.line([(-70, y0 - 2), (70, y0 - 2)], WOOD_D, 8)
        for sx_ in (-74, 74): pn.line([(sx_, y0), (sx_, y0 - 110)], WOOD_D, 9)
    pn.rect(-40, -storeys * 110 + 16, 40, -storeys * 110 + 44, fill=(30, 24, 20), outline=INK, width=2)
    pn.pop()

def siege_tower(pn, x, y_base, k=1.0, storeys=4):
    """Roman siege tower on the terrace (BM-P041): timber frame, plank walls, a fighting floor at the top."""
    pn.push(x, y_base, k)
    for i in range(storeys):
        w0 = 120 - i * 10; y0 = -i * 120
        pn.poly([(-w0, y0), (w0, y0), (w0 - 10, y0 - 120), (-w0 + 10, y0 - 120)], fill=lerpc(WOOD, PARCH, 0.08), outline=INK, width=3)
        for j in range(5):
            yy = y0 - 22 * j - 12
            pn.line([(-w0 + 4 + j * 2, yy), (w0 - 4 - j * 2, yy)], shade(WOOD, 0.3), 1.6, caps=False)
        pn.line([(-w0, y0), (-w0 + 10, y0 - 120)], WOOD_D, 10); pn.line([(w0, y0), (w0 - 10, y0 - 120)], WOOD_D, 10)
        pn.line([(-w0 + 8, y0 - 4), (w0 - 8, y0 - 116)], WOOD_D, 6); pn.line([(w0 - 8, y0 - 4), (-w0 + 8, y0 - 116)], WOOD_D, 6)
    top = -storeys * 120
    for xx in range(-80, 81, 32):
        pn.rect(xx - 12, top - 36, xx + 12, top, fill=WOOD, outline=INK, width=2)
    for wx_ in (-90, 90):
        pn.circ(wx_, 0, 26, fill=WOOD_D, outline=INK, width=3); pn.circ(wx_, 0, 6, fill=IRON)
    pn.pop()

def siege_terrace(pn, x0, x1, y_top_l, y_top_r, y_ground):
    """Earth and timber siege terrace (agger) rising toward the wall: log revetment on the face."""
    pn.poly([(x0, y_ground), (x0, y_top_l), (x1, y_top_r), (x1, y_ground)], fill=(132, 110, 80), outline=INK, width=3)
    n = 9
    for i in range(1, n):
        yy_l = lerp(y_top_l, y_ground, i / n); yy_r = lerp(y_top_r, y_ground, i / n)
        pn.line([(x0, yy_l), (x1, yy_r)], (104, 78, 50), 6)
        pn.line([(x0, yy_l - 3), (x1, yy_r - 3)], (156, 120, 80), 2, caps=False)
    for i in range(12):
        xx = lerp(x0, x1, (i + .5) / 12); yy = lerp(y_top_l, y_top_r, (i + .5) / 12)
        pn.circ(xx, yy + 8, 7, fill=WOOD, outline=INK, width=1.6)

def roundhouse(pn, x, y, k=1.0, door=True, palisade=False, bolts=0, smoke=0.0):
    """Iron Age roundhouse (BM-P042): wattle and daub wall, conical thatched roof, porch door; palisade around it."""
    pn.push(x, y, k)
    if palisade:
        for xx in range(-240, 241, 22):
            pn.poly([(xx - 9, 0), (xx - 9, -70), (xx, -84), (xx + 9, -70), (xx + 9, 0)], fill=lerpc(WOOD, PARCH, 0.1), outline=INK, width=2)
    pn.rect(-150, -86, 150, 0, fill=DAUB, outline=INK, width=3)
    for xx in range(-140, 150, 26):
        pn.line([(xx, -82), (xx + 4, -4)], shade(DAUB, 0.2), 1.6, caps=False)
    if door:
        pn.rect(-30, -72, 30, 0, fill=(58, 44, 32), outline=INK, width=2.6)
    roof = [(-190, -70), (0, -250), (190, -70)]
    pn.poly(roof, fill=THATCH, outline=INK, width=3.4)
    pn.poly([(0, -250), (190, -70), (60, -70)], fill=shade(THATCH, 0.18))
    for i in range(14):
        a_ = lerp(-170, 170, i / 13)
        pn.line([(a_ * 0.25, -220), (a_, -78)], shade(THATCH, 0.3), 1.8, caps=False)
    pn.line([(-190, -72), (190, -72)], shade(THATCH, 0.35), 5)
    rnd = random.Random(9)
    for i in range(bolts):
        bx = rnd.uniform(-150, 150); by_ = rnd.uniform(-200, -90) if abs(bx) < 120 else rnd.uniform(-110, -60)
        catapult_bolt(pn, bx - 70, by_ - 22, math.radians(18), 80)
    if smoke > 0:
        for i in range(5):
            pn.circ(rnd.uniform(-20, 20), -270 - i * 34, 18 + i * 6, fill=(200, 196, 186, int(90 * smoke)))
    pn.pop()

def hodhill_plan(pn, cx, cy, s=1.0, p_huts=1.0, n_bolts=11, p_bolts=1.0, fort=1.0, line_p=0.0, label=True):
    """Simplified site plan of Hod Hill (BM-P042), overhead: roughly square hillfort with double rampart, round hut
    platforms, the large hut in its palisade near the SE corner, the Roman fort in the NW corner. Bolt dots pop in;
    line_p draws the dashed firing line from the fort (scale bar about 170 m, LIKELY). Returns the hut centre."""
    pn.push(cx, cy, s)
    ram = [(-330, -380), (300, -410), (350, 360), (-310, 400)]
    for off, col in ((26, TURF), (0, (150, 162, 104))):
        pts = [(x_ + (off if x_ > 0 else -off), y_ + (off if y_ > 0 else -off)) for x_, y_ in ram]
        pn.poly(pts, fill=col, outline=INK, width=3.4)
    pn.poly([(x_ * 0.9, y_ * 0.9) for x_, y_ in ram], fill=(170, 178, 120), outline=lerpc(TURF, INK, 0.4), width=2)
    rnd = random.Random(14)
    for i in range(int(70 * p_huts)):
        hx, hy = rnd.uniform(-270, 280), rnd.uniform(-330, 330)
        if hx < -80 and hy < -120: continue      # Roman fort corner
        pn.circ(hx, hy, rnd.uniform(9, 13), outline=lerpc(TURF, INK, 0.5), width=2.2)
    hut = (230, 250)
    pn.rect(hut[0] - 52, hut[1] - 48, hut[0] + 52, hut[1] + 48, outline=WOOD_D, width=3.4)
    pn.circ(hut[0], hut[1], 30, fill=THATCH, outline=INK, width=3)
    if fort > 0:
        f_ = [(-312, -360), (-60, -372), (-56, -120), (-300, -110)]
        pn.poly(f_, fill=(214, 200, 168, int(220 * fort)), outline=RUST, width=3.6)
        pn.rect(-200, -260, -160, -230, fill=RUST)
    rnd2 = random.Random(37)
    for i in range(n_bolts):
        u = clamp(p_bolts * n_bolts - i)
        if u <= 0: break
        a_ = rnd2.uniform(0, 2 * math.pi); r_ = rnd2.uniform(4, 26)
        pn.circ(hut[0] + math.cos(a_) * r_, hut[1] + math.sin(a_) * r_, 5.5 * pop(u, 0.0, 1.0), fill=INK)
    if line_p > 0:
        a_, b_ = (-180, -245), hut
        n_ = 24
        for i in range(n_):
            u0, u1 = i / n_, (i + 0.55) / n_
            if u0 > line_p: break
            pn.line([lerp2(a_, b_, u0), lerp2(a_, b_, min(u1, line_p))], RUST, 5, caps=False)
    if label:
        pn.text(hut[0], hut[1] + 82, 'HUT', 30, INK, 'Black', disp=True)
        if fort > 0.5: pn.text(-185, -60, 'ROMAN FORT', 28, RUST, 'Black', disp=True)
    pn.pop()
    return (cx + hut[0] * s, cy + hut[1] * s)

def tallow_lump(pn, x, y, r=9.0, pitch=False, burning=0.0):
    """Lump of tallow (pale) or pitch (black) the Gauls threw onto the fire at the terrace (Caesar 7.25)."""
    col = (36, 30, 28) if pitch else (232, 222, 190)
    pts = [(x + r * (1 + 0.15 * math.sin(i * 2.3)) * math.cos(i * math.pi / 4), y + r * 0.85 * (1 + 0.12 * math.cos(i * 1.7)) * math.sin(i * math.pi / 4)) for i in range(8)]
    pn.poly(pts, fill=col, outline=INK, width=2)
    pn.circ(x - r * .3, y - r * .3, r * .25, fill=light(col, 0.5))
    if burning > 0:
        for i in range(3):
            pn.poly([(x - r * .5 + i * r * .5, y - r * .6), (x - r * .2 + i * r * .5, y - r * (1.8 + 0.5 * math.sin(i))), (x + i * r * .5, y - r * .6)],
                    fill=(246, 170, 60, int(220 * burning)))

def breastwork(pn, x0, x1, y_top, h=70):
    """Timber breastwork on the rampart walk, drawn IN FRONT of the defenders so their legs are hidden behind it."""
    for xx in range(int(x0), int(x1) + 40, 44):
        pn.rect(xx, y_top - h, xx + 40, y_top + 2, fill=lerpc(WOOD, PARCH, 0.12), outline=INK, width=2.2)
        pn.line([(xx + 10, y_top - h + 6), (xx + 10, y_top - 4)], shade(WOOD, 0.3), 1.4, caps=False)
    pn.rect(x0, y_top - h - 8, x1, y_top - h + 4, fill=WOOD_D, outline=INK, width=2.4)

def scorpio_pt(name, k=1.0, yaw=-8.0, pitch=16.0, draw=0.0, H0=122.0, aim=0.0):
    """Screen offset (from the ground point) of a named scorpio point at scale k, without drawing: used to frame close
    ups (put this point at the centre of the shot)."""
    phi, xc, tip_x, tip_y = scorpio_state(draw)
    P3 = dict(washer_top=(0, -SC_SK_Y, 30), skein_l=(0, -SC_SK_Y, 0), claw=(xc, 0, 8), trigger=(xc - 5, -3.4, 15), frame=(0, 0, 0),
              winch=(-108, -13, -5))[name]
    ca, sa = math.cos(math.radians(aim)), math.sin(math.radians(aim))
    px, py, pz = P3[0] + 30, P3[1], P3[2] + 8
    p = (px * ca - pz * sa - 30, py, px * sa + pz * ca - 8 + H0)
    v = Proj(yaw, pitch, CM_U).v(p)
    return v[0] * k, v[1] * k


# ======================================================================================================
# E022 Persian yakhchal (BM-P045 to BM-P053): domed ice house, shade wall, ice pool, qanat, ice blocks,
# straw, tools, sherbet bowl, night sky radiation diagram. All sizes in metres times s (design px per metre).
# ======================================================================================================
ADOBE = (204, 170, 122); ADOBE_D = (150, 116, 78); ADOBE_L = (230, 204, 158)
ICE = (220, 238, 246); ICE_D = (150, 192, 214); ICE_L = (248, 252, 255)
WATER = (64, 104, 136); WATER_L = (120, 160, 186); STRAW = (218, 188, 110); STRAW_D = (170, 136, 64)
GLAZE = (44, 104, 150); GLAZE_L = (120, 176, 206); SHERBET = (214, 120, 96)

def _mud_texture(pn, pts_box, seed, n=40, col=None):
    """Light plaster marks (short strokes) inside an axis box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = pts_box; rnd = random.Random(seed); c = col or ADOBE_D
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1); L_ = rnd.uniform(3, 9)
        pn.line([(x, y), (x + L_, y + rnd.uniform(-1.5, 1.5))], c + (90,), 1.3, caps=False)

def yakhchal_dome(pn, x, y, s, H=16.0, R=10.5, steps=17, door=True, vent=True, seed=5, lit=1.0, night=0.0):
    """Domed ice house, Meybod type (BM-P045): stepped conical mud brick dome over the ice pit. (x, y) = ground centre.
    Light from screen right: the left flank is in shade. night 0..1 cools and darkens the mud."""
    col = lerpc(ADOBE, (70, 74, 96), 0.7 * night); cd = lerpc(ADOBE_D, (40, 42, 60), 0.7 * night); cl = lerpc(ADOBE_L, (120, 124, 146), 0.7 * night)
    prof = []
    for i in range(steps + 1):
        h = H * i / steps
        r = R * (1 - (h / H) ** 1.7) ** 0.95 if i < steps else R * 0.07
        prof.append((h, max(r, R * 0.07)))
    # silhouette: vertical riser then inward step
    right, left = [], []
    for i in range(steps):
        h0, r0 = prof[i]; h1, r1 = prof[i + 1]
        hr = h0 + (h1 - h0) * 0.9
        rr = lerp(r0, r1, 0.55)
        right += [(x + r0 * s, y - h0 * s), (x + rr * s, y - hr * s), (x + r1 * s, y - hr * s)]
        left += [(x - r0 * s, y - h0 * s), (x - rr * s, y - hr * s), (x - r1 * s, y - hr * s)]
    top_y = y - H * s
    sil = right + [(x + R * 0.07 * s, top_y), (x - R * 0.07 * s, top_y)] + left[::-1]
    pn.poly(sil, fill=col)
    # shade flank (left 45 percent) and lit rim on the right
    shd = [(x - R * 0.1 * s, y)] + [(x - R * 0.1 * s * (1 - i / steps), y - prof[i][0] * s) for i in range(steps + 1)] + left[::-1]
    pn.poly([(px, py) for px, py in shd], fill=cd + (150,))
    # step ledges: light top edge and dark undercut
    for i in range(1, steps):
        h0, r0 = prof[i]; hr = prof[i - 1][0] + (h0 - prof[i - 1][0]) * 0.9
        yy = y - hr * s
        pn.line([(x - r0 * s, yy), (x + r0 * s, yy)], cl, max(1.4, 0.06 * s), caps=False)
        pn.line([(x - r0 * s, yy + 0.12 * s), (x + r0 * s, yy + 0.12 * s)], cd + (160,), max(1.0, 0.05 * s), caps=False)
    _mud_texture(pn, (x - R * s * 0.8, y - H * s * 0.7, x + R * s * 0.8, y - 0.3 * s), seed, n=int(30 + s * 2), col=cd)
    if vent:   # small vent cap at the apex (hole covered against rain, reconstruction of the cap shape)
        pn.rect(x - 0.45 * s, top_y - 0.7 * s, x + 0.45 * s, top_y + 0.05 * s, fill=col, outline=INK, width=2.2)
        pn.rect(x - 0.62 * s, top_y - 0.85 * s, x + 0.62 * s, top_y - 0.62 * s, fill=cl, outline=INK, width=2.0)
    if door:   # arched door at ground level
        dw, dh = 1.1 * s, 2.3 * s; dx = x + 1.6 * s
        pts = [(dx - dw / 2, y)] + [(dx - dw / 2 * math.cos(math.radians(a)), y - dh + dw / 2 - dw / 2 * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(dx + dw / 2, y)]
        pn.poly(pts, fill=(36, 26, 20), outline=INK, width=2.4)
    pn.poly(sil, outline=INK, width=3.4)
    pn.line([(x - R * s * 1.08, y), (x + R * s * 1.08, y)], INK, 3.0)
    return dict(top=(x, top_y), door=(x + 1.6 * s, y), r=R * s)

def yakhchal_section(pn, x, y, s, H=16.0, R=10.5, pit=6.0, pit_r=6.5, fill=1.0, layers=7, straw=True, stairs=True,
                     cold=0.0, label=None, seed=3):
    """Cutaway of the domed ice house and its pit (BM-P045, BM-P049). fill 0..1 of the pit filled with ice blocks,
    each course capped by a straw layer. cold 0..1 tints the air inside blue. label(pn, name, pt) for callouts."""
    # ground mass around the pit
    pn.rect(x - R * 1.5 * s, y, x + R * 1.5 * s, y + (pit + 1.6) * s, fill=(176, 146, 104))
    for i in range(14):
        rnd = random.Random(seed + i)
        pn.line([(x - R * 1.5 * s + rnd.uniform(0, 3 * R * s), y + rnd.uniform(0.3, pit + 1.4) * s), (x - R * 1.5 * s + rnd.uniform(0, 3 * R * s), y + rnd.uniform(0.3, pit + 1.4) * s)],
                (150, 120, 84, 80), 1.2, caps=False)
    # pit (bowl with brick lining)
    pit_pts = [(x - pit_r * s, y)] + [(x - pit_r * s * math.cos(math.radians(a)) * (0.86 + 0.14 * math.cos(math.radians(a)) ** 2),
                                       y + pit * s * math.sin(math.radians(a))) for a in range(0, 181, 10)] + [(x + pit_r * s, y)]
    pn.poly(pit_pts, fill=(52, 44, 40), outline=INK, width=3.0)
    # ice courses
    if fill > 0:
        top_d = pit * (1 - fill)
        n = layers; ch = pit / n
        for i in range(n):
            d0 = pit - (i + 1) * ch; d1 = pit - i * ch
            if d1 <= top_d + 1e-6: break
            d0 = max(d0, top_d)
            for d_ in (d1,):
                pass
            # half width at that depth (inside the bowl)
            def hw(dd):
                a = math.asin(clamp(dd / pit, 0, 1)); return pit_r * math.cos(a) * (0.86 + 0.14 * math.cos(a) ** 2) - 0.25
            w0, w1 = hw(d0), hw(d1)
            # blocks
            nb = max(2, int((w0 * 2) / 1.3))
            for b in range(nb):
                bx0 = x + (-w0 + b * 2 * w0 / nb + 0.06) * s; bx1 = x + (-w0 + (b + 1) * 2 * w0 / nb - 0.06) * s
                pn.rect(bx0, y + (d0 + 0.08) * s, bx1, y + (d1 - (0.22 if straw else 0.06)) * s, fill=ICE, outline=ICE_D, width=1.4)
                pn.line([(bx0 + 0.15 * s, y + (d0 + 0.2) * s), (bx1 - 0.25 * s, y + (d0 + 0.2) * s)], ICE_L, 1.6, caps=False)
            if straw:
                pn.rect(x - w1 * s, y + (d1 - 0.2) * s, x + w1 * s, y + d1 * s, fill=STRAW)
                rnd = random.Random(i * 7 + seed)
                for _ in range(int(w1 * 3)):
                    sx_ = x + rnd.uniform(-w1, w1) * s
                    pn.line([(sx_, y + (d1 - 0.18) * s), (sx_ + rnd.uniform(-0.4, 0.4) * s, y + (d1 - 0.04) * s)], STRAW_D, 1.1, caps=False)
        if straw and fill >= 0.999:   # thick straw blanket on top
            pn.rect(x - pit_r * 0.98 * s, y - 0.5 * s, x + pit_r * 0.98 * s, y + 0.05 * s, fill=STRAW, outline=STRAW_D, width=1.4)
    # stairs down the south side (right)
    if stairs:
        for i in range(8):
            sx0 = x + (pit_r - 0.2 - i * 0.55) * s; sy0 = y + i * (pit * 0.8 / 8) * s
            pn.line([(sx0, sy0), (sx0 - 0.55 * s, sy0), (sx0 - 0.55 * s, sy0 + pit * 0.8 / 8 * s)], (110, 88, 64), 2.2, caps=False)
    # dome shell in section: thick at the base (about 2 m), thin at the top (about 0.5 m)
    steps = 10; outer, inner = [], []
    for i in range(steps + 1):
        h = H * i / steps; r = max(R * (1 - (h / H) ** 1.7) ** 0.95, R * 0.07)
        t_ = lerp(2.2, 0.5, h / H); outer.append((r, h)); inner.append((max(r - t_, 0.25), h))
    air = [(x + r * s, y - h * s) for r, h in inner] + [(x - r * s, y - h * s) for r, h in inner[::-1]]
    pn.poly(air, fill=lerpc((60, 50, 44), (70, 110, 150), cold) + (235,))
    for sd in (-1, 1):
        band = [(x + sd * r * s, y - h * s) for r, h in outer] + [(x + sd * r * s, y - h * s) for r, h in inner[::-1]]
        pn.poly(band, fill=ADOBE if sd > 0 else lerpc(ADOBE, ADOBE_D, 0.5), outline=INK, width=2.6)
        for i in range(1, steps):     # brick course lines in the cut face
            ro, h = outer[i]; ri, _ = inner[i]
            pn.line([(x + sd * ro * s, y - h * s), (x + sd * ri * s, y - h * s)], ADOBE_D, 1.4, caps=False)
    pn.rect(x - 0.3 * s, y - (H + 0.6) * s, x + 0.3 * s, y - H * s + 2, fill=ADOBE, outline=INK, width=2)
    pn.line([(x - R * 1.5 * s, y), (x - pit_r * s, y)], INK, 3); pn.line([(x + pit_r * s, y), (x + R * 1.5 * s, y)], INK, 3)
    return dict(pit=(x, y + pit * 0.6 * s), vent=(x, y - H * s), wall=(x + R * 0.8 * s, y - 2 * s), top_ice=(x, y + pit * (1 - fill) * s))

def shade_wall(pn, x0, x1, y, s, h=10.0, niches=True, buttress=False, seed=7, night=0.0, top_rough=True):
    """Shade wall (BM-P046): long mud brick wall running east to west, here in front elevation (south face toward the
    viewer when niches show). Height up to about 10 m; in the Yazd region the face carries shallow arched niches."""
    col = lerpc(ADOBE, (66, 70, 92), 0.72 * night); cd = lerpc(ADOBE_D, (36, 38, 56), 0.72 * night); cl = lerpc(ADOBE_L, (110, 114, 136), 0.72 * night)
    rnd = random.Random(seed)
    top = [(x0, y - h * s)]
    nx = max(4, int((x1 - x0) / (0.9 * s)))
    for i in range(1, nx):
        top.append((x0 + (x1 - x0) * i / nx, y - h * s + (rnd.uniform(-0.12, 0.12) * s if top_rough else 0)))
    top.append((x1, y - h * s))
    pn.poly([(x0, y)] + top + [(x1, y)], fill=col)
    pn.line(top, cl, max(1.6, 0.12 * s), caps=False)          # lit coping
    pn.rect(x0, y - 0.9 * s, x1, y, fill=cd + (90,))           # damp base band
    # brick courses (faint), offset joints
    for j in range(int(h / 0.5)):
        yy = y - j * 0.5 * s
        if s < 6 and j % 2: continue
        pn.line([(x0, yy), (x1, yy)], cd + (60,), 1.0, caps=False)
    if niches:
        pitch = 3.2; w = 2.2; nh = h * 0.55
        n = int((x1 - x0) / (pitch * s))
        off = ((x1 - x0) - n * pitch * s) / 2
        for i in range(n):
            cx = x0 + off + (i + 0.5) * pitch * s; by = y - 1.4 * s
            pts = [(cx - w / 2 * s, by)] + [(cx - w / 2 * s * math.cos(math.radians(a)), by - nh * s + w / 2 * s - w / 2 * s * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(cx + w / 2 * s, by)]
            pn.poly(pts, fill=cd + (120,))
            pn.line(pts[1:-1], cd, max(1.2, 0.06 * s), caps=False)
            pn.line([(cx + w / 2 * s - 1, by), (cx + w / 2 * s - 1, by - nh * s + w / 2 * s)], cl + (150,), 1.4, caps=False)
    if buttress:
        for bx in (x0 + 0.15 * (x1 - x0), x1 - 0.15 * (x1 - x0)):
            pn.poly([(bx - 0.6 * s, y), (bx - 0.4 * s, y - h * 0.7 * s), (bx + 0.4 * s, y - h * 0.7 * s), (bx + 0.6 * s, y)], fill=cl, outline=INK, width=2)
    _mud_texture(pn, (x0, y - h * s, x1, y - 0.2 * s), seed, n=int((x1 - x0) / 8), col=cd)
    pn.poly([(x0, y)] + top + [(x1, y)], outline=INK, width=3.2)
    return dict(top=y - h * s)

def wall_end_section(pn, x, y, s, h=10.0, base=2.0, topw=0.6, f=1, night=0.0):
    """Shade wall seen end on (BM-P046): thick base tapering to a thin top. f=1 puts the south face on the left."""
    col = lerpc(ADOBE, (66, 70, 92), 0.72 * night); cd = lerpc(ADOBE_D, (36, 38, 56), 0.72 * night)
    pts = [(x - base / 2 * s, y), (x - topw / 2 * s, y - h * s), (x + topw / 2 * s, y - h * s), (x + base / 2 * s, y)]
    pn.poly(pts, fill=col, outline=INK, width=3)
    pn.poly([pts[0], pts[1], (x, y - h * s), (x, y)] if f > 0 else [(x, y), (x, y - h * s), pts[2], pts[3]], fill=cd + (120,))

def ice_pool(pn, x0, x1, y_far, y_near, skew=0.0, water=1.0, ice=0.0, stars=None, t=0.0, seed=2, night=1.0, crack=0.0):
    """Ice making pool, yakhband (BM-P047), seen from above at an angle: long rectangular shallow basin with a mud
    brick rim. water 0..1 shows the basin flooded (night sky reflection), ice 0..1 grows frost from the edges to a
    full sheet. crack 0..1 breaks the sheet into blocks for harvesting."""
    rim = 0.06 * (x1 - x0) / 10
    q = [(x0 + skew, y_far), (x1 + skew, y_far), (x1, y_near), (x0, y_near)]
    pn.poly([(q[0][0] - 10, q[0][1] - 8), (q[1][0] + 10, q[1][1] - 8), (q[2][0] + 14, q[2][1] + 12), (q[3][0] - 14, q[3][1] + 12)],
            fill=lerpc(ADOBE, (70, 74, 96), 0.7 * night), outline=INK, width=2.6)
    base = lerpc((150, 124, 92), (40, 40, 56), 0.7 * night)
    pn.poly(q, fill=base, outline=INK, width=2.4)
    if water > 0:
        wc = lerpc(WATER_L, (34, 48, 74), night)
        pn.poly(q, fill=wc + (int(235 * water),))
        if stars:
            rnd = random.Random(seed)
            for _ in range(stars):
                u, v = rnd.random(), rnd.random()
                px = lerp(lerp(q[3][0], q[2][0], u), lerp(q[0][0], q[1][0], u), v); py = lerp(y_near, y_far, v)
                tw_ = 0.6 + 0.4 * math.sin(t * 3 + u * 40)
                pn.circ(px, py, 1.4 + tw_, fill=(230, 236, 250, int(150 * water * (1 - ice * 0.8))))
    if ice > 0:
        # frost grows from the rim inward: inset polygon shrinks as ice -> 1
        e = clamp(ice)
        pn.poly(q, fill=lerpc(ICE, (76, 104, 146), 0.55 * night) + (int(120 + 135 * e),))
        cx = (q[0][0] + q[1][0] + q[2][0] + q[3][0]) / 4; cy = (y_far + y_near) / 2
        if e < 1:
            hole = [(lerp(px, cx, e), lerp(py, cy, e)) for px, py in q]
            pn.poly(hole, fill=lerpc(WATER_L, (34, 48, 74), night))
            if stars:
                rnd2 = random.Random(seed + 3)
                for _ in range(int(stars * (1 - e) ** 2)):
                    u, v = rnd2.uniform(0.15, 0.85), rnd2.uniform(0.2, 0.8)
                    px = lerp(lerp(hole[3][0], hole[2][0], u), lerp(hole[0][0], hole[1][0], u), v); py = lerp(hole[3][1], hole[0][1], v)
                    pn.circ(px, py, 1.8, fill=(230, 236, 250, 200))
        rnd = random.Random(seed + 9)
        for _ in range(int(40 * e)):   # feather crystals growing in from the edges
            side = rnd.randrange(4); a, b = q[side], q[(side + 1) % 4]; u = rnd.random()
            px, py = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            L_ = rnd.uniform(0.04, 0.22) * e
            ex, ey = lerp(px, cx, L_), lerp(py, cy, L_)
            pn.line([(px, py), (ex, ey)], ICE_L + (200,), 1.4, caps=False)
            mx, my = lerp(px, ex, 0.5), lerp(py, ey, 0.5)
            pn.line([(mx, my), (mx + (ey - py) * 0.2, my - (ex - px) * 0.2)], ICE_L + (160,), 1.0, caps=False)
    if crack > 0:
        nx = 6; ny = 2
        for i in range(1, nx):
            u = i / nx
            a = (lerp(q[0][0], q[1][0], u), y_far); b = (lerp(q[3][0], q[2][0], u), y_near)
            pn.line([a, (lerp(a[0], b[0], clamp(crack * 1.5)), lerp(a[1], b[1], clamp(crack * 1.5)))], (70, 110, 150), 3.4, caps=False)
        for j in range(1, ny):
            v = j / ny; yy = lerp(y_near, y_far, v)
            xa = lerp(q[3][0], q[0][0], v); xb = lerp(q[2][0], q[1][0], v)
            pn.line([(xa, yy), (lerp(xa, xb, clamp(crack * 1.5 - 0.3)), yy)], (70, 110, 150), 3.4, caps=False)
    pn.poly(q, outline=INK, width=2.4)
    return dict(c=((q[0][0] + q[2][0]) / 2, (y_far + y_near) / 2), q=q)

def pool_layers_section(pn, x0, x1, y, s, layers=0.0, pour=0.0, max_layers=6, ruler=True, night=1.0):
    """Section through the pool (BM-P047 diagram): each night about 5 to 10 cm of water is let in and freezes; the
    stack grows to about 50 cm. layers = frozen layer count (float), pour 0..1 shows the newest water on top."""
    cm = s / 100.0                      # s = px per metre
    depth = 60 * cm
    pn.rect(x0 - 30, y, x1 + 30, y + depth + 30, fill=lerpc((168, 138, 98), (64, 60, 72), 0.5 * night))
    pn.rect(x0, y, x1, y + depth, fill=lerpc((120, 98, 72), (30, 30, 42), 0.5 * night), outline=INK, width=2.6)
    lay_h = 50 * cm / max_layers
    nfull = int(layers); frac = layers - nfull
    for i in range(min(nfull + (1 if frac > 0 else 0), max_layers)):
        hh = lay_h * (1 if i < nfull else frac)
        yb = y + depth - i * lay_h
        pn.rect(x0 + 2, yb - hh, x1 - 2, yb, fill=lerpc(ICE, ICE_D, 0.15 * (i % 2)), outline=ICE_D, width=1.4)
        pn.line([(x0 + 8, yb - hh + 3), (x1 - 8, yb - hh + 3)], ICE_L, 1.6, caps=False)
    if pour > 0 and layers < max_layers:
        yb = y + depth - nfull * lay_h
        pn.rect(x0 + 2, yb - lay_h * pour, x1 - 2, yb, fill=WATER + (200,))
    if ruler:
        rx = x1 + 46
        pn.line([(rx, y + depth), (rx, y + depth - 50 * cm)], INK, 3)
        for c in range(0, 51, 10):
            yy = y + depth - c * cm
            pn.line([(rx - 8, yy), (rx + 8, yy)], INK, 2.4, caps=False)
            pn.text(rx + 16, yy, '%d' % c, 22, INK, 'Bold', 'lm')
        pn.text(rx + 16, y + depth - 50 * cm - 26, 'cm', 20, MUTED, 'Bold', 'lm')
    return dict(top=y + depth - layers * lay_h)

def qanat_section(pn, x0, x1, y_ground, s_v=1.0, shafts=6, flow=0.0, t=0.0, outlet=True, hill=300.0):
    """Qanat (BM-P048) in section: the mother well reaches the water table under the hills (left); a gently falling
    tunnel carries the water out to daylight on the plain (right), where the ground has dropped faster than the
    tunnel. Vertical access shafts ringed by spoil mounds. Vertical scale exaggerated (diagram)."""
    W_ = x1 - x0
    gx = lambda u: x0 + u * W_
    gy = lambda u: y_ground - hill * (1 - clamp(u / 0.85)) ** 1.6
    ground = [(gx(u / 60), gy(u / 60)) for u in range(61)]
    bot = y_ground + 70
    pn.poly(ground + [(x1, bot), (x0, bot)], fill=(186, 156, 112), outline=INK, width=2.6)
    t0 = (gx(0.08), y_ground - hill * 0.45); t1 = (gx(0.86), y_ground - 6)
    aq = [(x0, t0[1] - 30), (gx(0.3), t0[1] + 10), (gx(0.3), t0[1] + 60), (x0, t0[1] + 80)]
    pn.poly(aq, fill=(92, 132, 160, 150))
    pn.text(gx(0.13), t0[1] + 46, 'WATER TABLE', 20, (30, 50, 70), 'Black', 'mm', True)
    pn.line([t0, t1], (40, 32, 26), 13, caps=False)
    if flow > 0:
        n = 16
        for i in range(n):
            u = ((i / n) + t * 0.25) % 1.0
            if u > flow: continue
            px, py = lerp(t0[0], t1[0], u), lerp(t0[1], t1[1], u)
            pn.line([(px - 8, py - 0.3), (px + 8, py + 0.3)], (120, 176, 220), 4, caps=False)
    for i in range(shafts):
        u = 0.08 + i * (0.7 / max(1, shafts - 1))
        sx = gx(u); top = gy(u); tb = lerp(t0[1], t1[1], (sx - t0[0]) / (t1[0] - t0[0]))
        pn.line([(sx, top), (sx, tb)], (40, 32, 26), 7, caps=False)
        pn.ell(sx - 15, top - 2, 13, 7, fill=(168, 138, 96), outline=INK, width=2)
        pn.ell(sx + 15, top - 2, 13, 7, fill=(168, 138, 96), outline=INK, width=2)
    if outlet:
        pn.poly([(t1[0], y_ground - 10), (x1, y_ground - 10), (x1, y_ground), (t1[0], y_ground)], fill=(90, 140, 180), outline=INK, width=2)
    return dict(outlet=(t1[0], y_ground - 6), mouth=t0)

def ice_block(pn, cx, cy, w, h, ang=0.0, straw=0.0, seed=1, alpha=255):
    """Ice block cut from the pool (BM-P049): about 50 cm thick; slightly cloudy, with layer lines from the nightly
    pours, chipped edges, highlight on the lit side; optional straw clinging to it."""
    a = math.radians(ang)
    def R_(px, py): return (cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a))
    rnd = random.Random(seed)
    top = [R_(-w / 2, -h / 2), R_(-w / 2 + w * 0.12, -h / 2 - h * 0.28), R_(w / 2 + w * 0.12, -h / 2 - h * 0.28), R_(w / 2, -h / 2)]
    side = [R_(w / 2, -h / 2), R_(w / 2 + w * 0.12, -h / 2 - h * 0.28), R_(w / 2 + w * 0.12, h / 2 - h * 0.28), R_(w / 2, h / 2)]
    front = [R_(-w / 2, -h / 2), R_(w / 2, -h / 2), R_(w / 2, h / 2), R_(-w / 2, h / 2)]
    pn.poly(front, fill=ICE + (alpha,), outline=INK, width=2.4)
    pn.poly(top, fill=ICE_L + (alpha,), outline=INK, width=2.0)
    pn.poly(side, fill=ICE_D + (alpha,), outline=INK, width=2.0)
    for j in range(1, 5):   # pour layers
        yy = -h / 2 + h * j / 5
        pn.line([R_(-w / 2 + 3, yy), R_(w / 2 - 3, yy)], ICE_D + (150,), 1.2, caps=False)
    for _ in range(3):
        px, py = rnd.uniform(-w / 2.6, w / 2.6), rnd.uniform(-h / 3, h / 3)
        pn.line([R_(px, py), R_(px + w * 0.12, py - h * 0.12)], ICE_L, 1.6, caps=False)
    if straw > 0:
        for _ in range(int(10 * straw)):
            px = rnd.uniform(-w / 2, w / 2 + w * 0.1)
            pn.line([R_(px, -h / 2 - h * 0.1), R_(px + rnd.uniform(-8, 8), -h / 2 - h * 0.1 + rnd.uniform(-6, 2))], STRAW_D, 1.6, caps=False)
    return dict(L=R_(-w / 2, 0), Rr=R_(w / 2 + w * 0.06, -h * 0.1))

def kolang(pn, hx, hy, ang, L=135.0, k=1.0):
    """Pick (kolang, BM-P051): wooden haft about 90 cm with a two pointed iron head. Handle end at (hx, hy), ang in
    degrees (0 = pointing right). Returns grip points (rear hand near the end, front hand 40 percent up) and head."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    L *= k; head = (hx + ux * L, hy + uy * L)
    pn.line([(hx, hy), head], INK, 9 * k); pn.line([(hx, hy), head], WOOD, 6 * k)
    pn.line([(hx + nx * 1.4 * k, hy + ny * 1.4 * k), (head[0] + nx * 1.4 * k, head[1] + ny * 1.4 * k)], light(WOOD, 0.3), 1.4 * k, caps=False)
    hl = 42 * k
    def hp(v, w):   # point along the head: v sideways (-1..1), curved back toward the handle at the tips
        return (head[0] + nx * hl * v - ux * 9 * k * v * v + ux * w, head[1] + ny * hl * v - uy * 9 * k * v * v + uy * w)
    upper = [hp(v / 10, 5 * k * (1 - abs(v / 10)) ** 0.6) for v in range(-10, 11)]
    lower = [hp(v / 10, -5 * k * (1 - abs(v / 10)) ** 0.6) for v in range(10, -11, -1)]
    pn.poly(upper + lower, fill=IRON, outline=INK, width=2.4 * k)
    pn.line(upper[11:20], light(IRON, 0.45), 1.4 * k, caps=False)
    pn.rect(head[0] - 6 * k, head[1] - 6 * k, head[0] + 6 * k, head[1] + 6 * k, fill=shade(IRON, 0.25), outline=INK, width=1.6 * k)
    p1, p2 = upper[-1], upper[0]
    return dict(rear=(hx + ux * 10 * k, hy + uy * 10 * k), front=(hx + ux * L * 0.42, hy + uy * L * 0.42), tip=p1, tip2=p2)

def bil(pn, hx, hy, ang, L=170.0, k=1.0):
    """Spade (bil, BM-P051): long straight wooden handle, flat iron blade with a step for the foot. Handle top at
    (hx, hy); ang the shaft direction. Returns grips (top hand at the end, lower hand 45 percent down) and blade."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    L *= k; b0 = (hx + ux * L, hy + uy * L)
    pn.line([(hx, hy), b0], INK, 9 * k); pn.line([(hx, hy), b0], WOOD, 6 * k)
    pn.line([(hx + nx * 1.4 * k, hy + ny * 1.4 * k), (b0[0] + nx * 1.4 * k, b0[1] + ny * 1.4 * k)], light(WOOD, 0.3), 1.4 * k, caps=False)
    bw, bl = 15 * k, 34 * k
    blade = [(b0[0] + nx * bw, b0[1] + ny * bw), (b0[0] - nx * bw, b0[1] - ny * bw),
             (b0[0] - nx * bw * 0.85 + ux * bl, b0[1] - ny * bw * 0.85 + uy * bl), (b0[0] + ux * (bl + 6 * k), b0[1] + uy * (bl + 6 * k)),
             (b0[0] + nx * bw * 0.85 + ux * bl, b0[1] + ny * bw * 0.85 + uy * bl)]
    pn.poly(blade, fill=IRON, outline=INK, width=2.4 * k)
    pn.line([(b0[0] + nx * bw * 0.6, b0[1] + ny * bw * 0.6), (b0[0] + nx * bw * 0.5 + ux * bl * 0.8, b0[1] + ny * bw * 0.5 + uy * bl * 0.8)], light(IRON, 0.45), 1.4 * k, caps=False)
    pn.line([(b0[0] + nx * (bw + 9 * k), b0[1] + ny * (bw + 9 * k)), (b0[0] + nx * bw, b0[1] + ny * bw)], WOOD_D, 5 * k)   # foot step
    return dict(top=(hx + ux * 6 * k, hy + uy * 6 * k), low=(hx + ux * L * 0.45, hy + uy * L * 0.45), blade=b0)

def sherbet_bowl(pn, cx, cy, r=30.0, ice=True, sherbet=SHERBET, spoon=False):
    """Glazed bowl of sherbet with ice (BM-P053). (cx, cy) = rim centre. Light from the right."""
    body = [(cx - r, cy)] + [(cx - r * math.cos(math.radians(a)), cy + r * 0.62 * math.sin(math.radians(a))) for a in range(0, 181, 12)] + [(cx + r, cy)]
    pn.poly(body, fill=GLAZE, outline=INK, width=2.6)
    pn.poly([(cx - r * 0.3, cy + 2)] + [(cx - r * 0.3 - r * 0.5 * math.cos(math.radians(a)) * 0.0 - r * 0.6 * math.cos(math.radians(a)), cy + r * 0.55 * math.sin(math.radians(a))) for a in range(0, 91, 15)],
            fill=shade(GLAZE, 0.3))
    pn.arc(cx + r * 0.2, cy + r * 0.18, r * 0.62, 300, 350, GLAZE_L, 2.4)
    for a in range(30, 160, 32):   # painted band
        px = cx - r * 0.8 * math.cos(math.radians(a)); py = cy + r * 0.3 * math.sin(math.radians(a))
        pn.circ(px, py, r * 0.07, fill=(236, 230, 214))
    pn.rect(cx - r * 0.34, cy + r * 0.6, cx + r * 0.34, cy + r * 0.72, fill=shade(GLAZE, 0.2), outline=INK, width=2)
    pn.ell(cx, cy, r, r * 0.26, fill=sherbet, outline=INK, width=2.4)
    pn.ell(cx + r * 0.1, cy - r * 0.02, r * 0.7, r * 0.14, fill=light(sherbet, 0.25))
    if ice:
        for dx_, dy_, w_ in ((-0.35, -0.02, 0.28), (0.12, -0.08, 0.32), (0.4, 0.02, 0.22)):
            ice_block(pn, cx + dx_ * r, cy + dy_ * r - r * 0.06, w_ * r, w_ * r * 0.7, ang=dx_ * 20, seed=int(dx_ * 10 + 5))
    if spoon:
        pn.line([(cx + r * 0.3, cy), (cx + r * 1.1, cy - r * 0.7)], (160, 120, 70), 3)

def radiation_arrows(pn, x0, x1, y_from, y_to, p=1.0, n=5, t=0.0, col=(246, 178, 52)):
    """Night sky radiation diagram: wavy arrows rising from the water straight up into the clear sky."""
    for i in range(n):
        x = lerp(x0, x1, (i + 0.5) / n)
        pp = clamp(p * 1.3 - i * 0.06)
        if pp <= 0: continue
        yt = lerp(y_from, y_to, pp)
        pts = [(x + 9 * math.sin((y_from - yy) / 22.0 + t * 5 + i), yy) for yy in [lerp(y_from, yt, u / 24) for u in range(25)]]
        pn.line(pts, col, 5, caps=False)
        hx_, hy_ = pts[-1]
        pn.poly([(hx_, hy_ - 16), (hx_ - 11, hy_ + 4), (hx_ + 11, hy_ + 4)], fill=col)

def stars(pn, seed, n=80, y0=0, y1=900, t=0.0, x0=0, x1=1080):
    rnd = random.Random(seed)
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1); r = rnd.choice((1.2, 1.6, 2.2, 3.0))
        tw_ = 0.7 + 0.3 * math.sin(t * rnd.uniform(1, 3) + i)
        pn.circ(x, y, r, fill=(240, 240, 255, int(220 * tw_)))

def _ice_arrive_np(X, Y, x0, y0, x1, y1, seed):
    W_, H_ = x1 - x0, y1 - y0
    sx, sy = x0 + W_ * 0.62, y0 + H_ * 0.38; D = min(W_, H_) * 0.55
    de = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
    ds = np.hypot(X - sx, Y - sy) * 1.1
    n = 0.16 * np.sin(X * 0.011 + seed) * np.cos(Y * 0.009 - seed) + 0.03 * np.sin(X * 0.037 + Y * 0.031)
    return np.clip(np.minimum(de, ds) / D + n, 0, 1.2)

_ICEF = {}
def ice_fill_image(freeze, x0, y0, x1, y1, seed=5):
    """Smooth night water and clear ice as a full frame RGB image (drawn under the vector frost layer)."""
    key = (x0, y0, x1, y1, seed)
    if key not in _ICEF:
        Y, X = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
        A = _ice_arrive_np(X, Y, x0, y0, x1, y1, seed)
        g = (Y / H)[..., None]
        water = np.array((8, 14, 34), np.float32) * (1 - g) + np.array((24, 40, 78), np.float32) * g
        ice = water * 0.45 + np.array((64, 110, 150), np.float32) * 0.55
        # gentle tone variation inside the ice (thickness)
        v = (0.5 + 0.5 * np.sin(X * 0.006 + 1.3) * np.cos(Y * 0.004 + 0.4))[..., None]
        ice = ice * (0.9 + 0.2 * v)
        _ICEF[key] = (A, water, ice)
    A, water, ice = _ICEF[key]
    F_ = freeze * 1.2
    m = np.clip((F_ - A) / 0.05, 0, 1)[..., None]
    rim = np.clip(1 - np.abs(F_ - A - 0.02) / 0.02, 0, 1)[..., None] * 0.6
    img = water * (1 - m) + ice * m
    img = img * (1 - rim) + np.array((220, 240, 252), np.float32) * rim
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)

def ice_surface(pn, x0, y0, x1, y1, freeze=1.0, t=0.0, seed=3, glint=None, stars=170, cell=30, fill=True):
    """E022 hook (BM-P047 close up): water freezing at night, seen from just above. Dark water full of star
    reflections; clear dark ice spreads in from the edges, laced with feather (dendrite) frost crystals that grow with
    the front and stay as texture, trapped air bubbles in rows, hairline fractures, and a glint of light that sweeps
    across. Night ice stays dark and see through, which is what reads as real ice. freeze 0..1. Needs lib.BLEND on."""
    rnd = random.Random(seed)
    W_, H_ = x1 - x0, y1 - y0
    if fill:
        for i in range(12):
            yy0 = y0 + H_ * i / 12
            pn.rect(x0, yy0, x1, yy0 + H_ / 12 + 1, fill=lerpc((8, 14, 34), (24, 40, 78), i / 11))
    seeds = [(x0 + W_ * 0.62, y0 + H_ * 0.38)]
    D = min(W_, H_) * 0.55
    def arrive(px, py):
        de = min(px - x0, x1 - px, py - y0, y1 - py)
        ds = min(math.hypot(px - sx, py - sy) for sx, sy in seeds) * 1.1
        n = 0.16 * math.sin(px * 0.011 + seed) * math.cos(py * 0.009 - seed) + 0.03 * math.sin(px * 0.037 + py * 0.031)
        return clamp(min(de, ds) / D + n, 0, 1.2)
    F_ = freeze * 1.2
    # clear ice: slightly lighter, bluer than the water, opaque so overlaps never stack
    nx, ny = (int(W_ / cell) + 2, int(H_ / cell) + 2) if fill else (0, 0)
    for j in range(ny):
        for i in range(nx):
            px, py = x0 + i * cell, y0 + j * cell
            a = arrive(px, py)
            if F_ > a:
                age = clamp((F_ - a) / 0.3)
                base_ = lerpc((8, 14, 34), (24, 40, 78), (py - y0) / H_)
                pn.circ(px, py, cell * 0.9, fill=lerpc(base_, (64, 110, 150), 0.35 + 0.3 * age))
    # star reflections: bright in open water, softened under the ice
    for i in range(stars):
        sx, sy = rnd.uniform(x0, x1), rnd.uniform(y0, y1); r = rnd.choice((1.2, 1.6, 2.2, 3.0))
        tw_ = 0.6 + 0.4 * math.sin(t * rnd.uniform(1, 3) + i)
        iced = F_ > arrive(sx, sy)
        pn.circ(sx, sy, r * (0.8 if iced else 1.0), fill=(230, 236, 255, int((120 if iced else 220) * tw_)))
    # milky depth patches inside older ice
    r2 = random.Random(seed + 1)
    for _ in range(22):
        px, py = r2.uniform(x0, x1), r2.uniform(y0, y1)
        if F_ > arrive(px, py) + 0.2:
            pn.ell(px, py, r2.uniform(70, 150), r2.uniform(18, 40), fill=(180, 214, 236, 34))
    # feather crystals: each grows from its root once the ice reaches it and stays as frost texture
    r3 = random.Random(seed + 2)
    for k in range(150):
        px, py = r3.uniform(x0, x1), r3.uniform(y0, y1)
        a = arrive(px, py)
        a0 = r3.uniform(0, 6.28); Lf = r3.uniform(50, 150)
        if F_ <= a: continue
        g = eo3(clamp((F_ - a) / 0.18))
        L_ = Lf * g
        ex, ey = px + math.cos(a0) * L_, py + math.sin(a0) * L_
        hot = (F_ - a) < 0.12                      # just formed: brighter
        al = 240 if hot else 170
        pn.line([(px, py), (ex, ey)], (236, 248, 255, al), 2.8 if hot else 2.0, caps=False)
        nb = 6
        for qi in range(1, nb):
            q = qi / nb
            mx, my = lerp(px, ex, q), lerp(py, ey, q); bl = L_ * 0.32 * (1 - q * 0.6)
            for sd in (-1, 1):
                b = a0 + sd * 1.0
                pn.line([(mx, my), (mx + math.cos(b) * bl, my + math.sin(b) * bl)], (214, 238, 252, al - 40), 1.5, caps=False)
    # growth front: a thin bright rim where water is turning to ice right now (the fill image draws it when fill=False)
    r6 = random.Random(seed + 6)
    for _ in range(500 if fill else 0):
        px, py = r6.uniform(x0, x1), r6.uniform(y0, y1)
        a = arrive(px, py)
        if 0 < F_ - a < 0.04: pn.circ(px, py, 2.4, fill=(240, 250, 255, 200))
    # trapped air bubbles in short rows and hairline fractures, only in mature ice
    r4 = random.Random(seed + 3)
    for _ in range(30):
        bx, by = r4.uniform(x0, x1), r4.uniform(y0, y1); ang = r4.uniform(-0.6, 0.6); nb_ = r4.randint(2, 5); rr = [r4.uniform(3, 8) for _m in range(nb_)]
        if F_ > arrive(bx, by) + 0.3:
            for m in range(nb_):
                cx_, cy_ = bx + math.cos(ang) * m * 18, by + math.sin(ang) * m * 18
                pn.ell(cx_, cy_, rr[m], rr[m] * 0.8, fill=(220, 238, 250, 150))
                pn.circ(cx_ - rr[m] * 0.3, cy_ - rr[m] * 0.3, rr[m] * 0.32, fill=(255, 255, 255, 240))
    r5 = random.Random(seed + 4)
    for _ in range(8):
        px, py = r5.uniform(x0, x1), r5.uniform(y0, y1); a = r5.uniform(0, 6.28); steps_ = [r5.uniform(-0.6, 0.6) for _s in range(6)]
        if F_ > arrive(px, py) + 0.45:
            pts = [(px, py)]
            for da in steps_:
                a += da; px += math.cos(a) * 46; py += math.sin(a) * 46; pts.append((px, py))
            pn.line([(p[0] + 2, p[1] + 2) for p in pts], (255, 255, 255, 150), 1.4, caps=False)
            pn.line(pts, (150, 196, 226, 220), 2.4, caps=False)
    if glint is not None and 0 <= glint <= 1:
        gx = lerp(x0 - W_ * 0.6, x1 + W_ * 0.3, glint)
        for wdt, al in ((200, 26), (100, 46), (34, 110)):
            pn.poly([(gx, y0), (gx + wdt, y0), (gx + wdt - H_ * 0.45, y1), (gx - H_ * 0.45, y1)], fill=(255, 255, 255, al))


# ===== horse, copied from the e018-mongol-bow branch (BM-P012) with a Celtic horned saddle option for E023 =====
# ---------------- the steppe horse (BM-P012), side view, facing f ----------------
HORSE = (152, 108, 68); HORSE_D = (116, 80, 50); MANE = (54, 40, 30); HOOF = (60, 48, 40)
SADDLE = (150, 52, 40); SADDLE_D = (60, 34, 26); FELT = (196, 180, 146)

def smooth(pts, closed=True, n=5):
    """Catmull Rom resample of a control polygon, for organic outlines (horse, cloth)."""
    P_ = list(pts); m = len(P_); out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P_[(i - 1) % m] if closed or i > 0 else P_[0]
        p1 = P_[i]; p2 = P_[(i + 1) % m]
        p3 = P_[(i + 2) % m] if closed or i + 2 < m else P_[-1]
        for j in range(n):
            t = j / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    if not closed: out.append(P_[-1])
    return out

def _taper(pn, pts, w0, w1, col, outline=2.6):
    """Tapered limb through a polyline: width w0 at the start to w1 at the end, rounded joints."""
    L_ = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(L_ - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / Ln, tx / Ln
        w = lerp(w0, w1, i / (L_ - 1)) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    pn.poly(left + right[::-1], fill=col, outline=INK, width=outline)

def _seg_pts(p0, angs, lens, f):
    pts = [p0]
    for a, l in zip(angs, lens):
        r = math.radians(a); x, y = pts[-1]
        pts.append((x + f * math.sin(r) * l, y + math.cos(r) * l))
    return pts

def horse(pn, x, y, k, f=1, ph=0.0, gallop=1.0, saddle=True, rider_far=None, rider_near=None, col=HORSE, hl_saddle=0.0,
          stirrup=True, reins_to=None, head_a=0.0, stirrup_at=None, saddle_type='steppe'):
    """Small Mongol steppe horse (about 13 hands, about 130 cm at the withers) in a gallop (gallop 0 stands square).
    Wooden frame saddle with a high narrow pommel and lower cantle over a felt pad, short iron stirrups, bridle with bit.
    rider_far / rider_near(pn) draw between the layers. Returns the seat and stirrup points (world)."""
    pn.push(x, y, k)
    g = gallop
    w2 = 2 * math.pi
    bob = -9 * g * (0.5 + 0.5 * math.sin(w2 * ph - 0.4))
    pitch = math.radians(5 * g * math.sin(w2 * ph + 0.9))
    def R(px, py, cx=0.0, cy=-160.0):
        dx, dy = px - cx, py - cy
        ca, sa = math.cos(pitch), math.sin(pitch)
        X_ = cx + dx * ca - dy * sa; Y_ = cy + dx * sa + dy * ca + bob
        return (X_ * f, Y_)
    cd = shade(col, 0.24)
    def leg(kind, o, colr):
        u = w2 * (ph + o)
        sw = math.sin(u) * g                      # + forward reach, - pushed back
        fold = g * max(0.0, math.cos(u)) ** 1.5   # folding while it swings forward
        if kind == 'hind':
            p0 = R(-78, -150)
            angs = [24 + 26 * sw, -24 - 34 * fold + 14 * sw, 6 + 40 * fold + 10 * sw, 24 + 30 * fold]
            pts = _seg_pts(p0, angs, (50, 50, 46, 16), f)
            ws = (46, 24, 14, 13)
        else:
            p0 = R(74, -146)
            angs = [-8 + 30 * sw, 2 + 26 * sw + 70 * fold, 2 + 26 * sw + 40 * fold, 26 + 20 * fold]
            pts = _seg_pts(p0, angs, (34, 52, 44, 16), f)
            ws = (40, 22, 13, 13)
        # ground contact: lift the whole leg so the hoof never sinks below the ground
        _taper(pn, pts[:3], ws[0], ws[1], colr)
        _taper(pn, pts[1:4], ws[1], ws[2], colr)
        _taper(pn, pts[3:5], ws[2], ws[3], colr, 2.2)
        hx3, hy3 = pts[-1]; a_ = math.radians(angs[-1])
        pn.poly([(hx3 - 7, hy3 - 3), (hx3 + 7, hy3 - 3), (hx3 + 9, hy3 + 8), (hx3 - 9, hy3 + 8)], fill=HOOF, outline=INK, width=2)
        pn.circ(pts[3][0], pts[3][1], ws[2] * 0.62, fill=colr)     # fetlock
        return pts[-1]
    # far legs
    leg('hind', 0.0, cd); leg('fore', 0.42, cd)
    if rider_far: rider_far(pn)
    # tail: long, flowing back in the gallop
    sw_ = math.sin(w2 * ph) * 8 * g
    tail = smooth([R(-112, -196), R(-150, -188 + sw_ - 20 * g), R(-186, -150 + sw_ - 30 * g), R(-200, -104 + sw_ - 30 * g),
                   R(-176, -112 + sw_ - 20 * g), R(-150, -150), R(-120, -176)], True, 5)
    pn.poly(tail, fill=MANE, outline=INK, width=2.6)
    # body, neck and head in one smooth outline
    ha = head_a + 6 * g * math.sin(w2 * ph + 2.0)
    def Hd(px, py):   # head and upper neck nod about the neck base
        a = math.radians(ha); cx, cy = 60, -200
        dx, dy = px - cx, py - cy
        return R(cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))
    outline_ = [R(-118, -196), R(-92, -212), R(-50, -210), R(-6, -200), R(40, -208), Hd(70, -222), Hd(98, -250), Hd(124, -282),
                Hd(140, -290), Hd(156, -280), Hd(184, -246), Hd(204, -226), Hd(210, -208), Hd(198, -198), Hd(174, -202),
                Hd(150, -214), Hd(134, -236), Hd(124, -222), R(112, -186), R(110, -154), R(98, -118), R(60, -102), R(0, -98),
                R(-56, -104), R(-96, -124), R(-124, -160)]
    body = smooth(outline_, True, 6)
    pn.poly(body, fill=col, outline=INK, width=3)
    # shading: belly and under the neck, lit back line
    pn.poly(smooth([R(-96, -132), R(-56, -116), R(0, -110), R(60, -114), R(94, -126), R(60, -130), R(0, -126), R(-56, -130)], True, 4),
            fill=shade(col, 0.16))
    pn.line(smooth([R(-84, -204), R(-40, -204), R(0, -194), R(36, -200)], False, 5), light(col, 0.3), 2.6, caps=False)
    pn.line(smooth([R(-70, -190), R(-96, -170), R(-104, -140)], False, 4), shade(col, 0.2), 2.2, caps=False)   # hip line
    pn.line(smooth([R(92, -190), R(84, -160), R(88, -134)], False, 4), shade(col, 0.2), 2.2, caps=False)       # shoulder
    # ear, eye, nostril, mouth
    pn.poly([Hd(128, -286), Hd(128, -310), Hd(142, -290)], fill=col, outline=INK, width=2.4)
    pn.circ(*Hd(160, -262), 4.2, fill=INK); pn.circ(*Hd(158.5, -263.5), 1.3, fill=WHITE)
    pn.ell(*Hd(201, -220), 3.2, 2.2, fill=shade(col, 0.55))
    pn.line([Hd(196, -205), Hd(206, -207)], INK, 2, caps=False)
    # mane: thick, upright, dark
    mn = []
    for i in range(9):
        t_ = i / 8
        bx, by = lerp(44, 128, t_), lerp(-208, -286, t_) - 6 * math.sin(t_ * math.pi)
        mn.append(Hd(bx - 4, by - 14 - 4 * (i % 2)))
    pn.poly([Hd(40, -204)] + mn + [Hd(134, -284), Hd(120, -262), Hd(82, -226)], fill=MANE, outline=INK, width=2.4)
    pn.poly([Hd(126, -288), Hd(146, -296), Hd(140, -280)], fill=MANE, outline=INK, width=2)                  # forelock
    # bridle and bit
    pn.line([Hd(134, -282), Hd(150, -246), Hd(196, -212)], SADDLE_D, 3.2, caps=False)
    pn.line([Hd(150, -246), Hd(178, -240)], SADDLE_D, 3.2, caps=False)
    pn.circ(*Hd(196, -212), 3.6, fill=IRON, outline=INK, width=1.4)
    seat = R(8, -216)
    if saddle and saddle_type == 'horned':
        # E023 (BM-P060): Celtic four horned saddle on a cloth: two horns at the front leaning out over the thighs, two at
        # the back; no stirrups (not used in Europe until centuries later)
        sc = lerpc((120, 84, 52), AMBER, hl_saddle) if hl_saddle else (120, 84, 52)
        pn.poly(smooth([R(-50, -204), R(54, -208), R(60, -166), R(-54, -162)], True, 3), fill=(150, 60, 44), outline=INK, width=2.4)
        pn.line([R(-48, -170), R(56, -172)], (220, 190, 120), 3, caps=False)                                   # cloth border
        pn.line([R(30, -172), R(36, -110)], SADDLE_D, 6, caps=False)                                           # girth
        pn.poly(smooth([R(-36, -206), R(40, -208), R(44, -196), R(-38, -194)], True, 3), fill=sc, outline=INK, width=2.4)
        for hx_, lean in ((34, 10), (-30, -10)):
            pn.poly([R(hx_ - 6, -206), R(hx_ + lean - 4, -236), R(hx_ + lean + 6, -238), R(hx_ + 8, -206)], fill=sc, outline=INK, width=2.4)
            pn.circ(*R(hx_ + lean + 1, -238), 4.4, fill=(196, 150, 72), outline=INK, width=1.4)
        pn.line([R(-20, -214), R(26, -214)], shade(sc, 0.4), 4, caps=False)
    elif saddle:
        sc = lerpc(SADDLE, AMBER, hl_saddle) if hl_saddle else SADDLE
        pn.poly(smooth([R(-44, -204), R(50, -208), R(56, -170), R(-48, -166)], True, 3), fill=FELT, outline=INK, width=2.4)
        pn.line([R(32, -172), R(38, -110)], SADDLE_D, 6, caps=False)                                           # girth
        pn.poly([R(-30, -210), R(38, -212), R(42, -200), R(-32, -198)], fill=sc, outline=INK, width=2.4)      # side bars
        pn.poly([R(28, -208), R(32, -242), R(44, -244), R(46, -208)], fill=sc, outline=INK, width=2.4)        # high pommel
        pn.poly([R(-32, -206), R(-34, -228), R(-22, -230), R(-18, -208)], fill=sc, outline=INK, width=2.4)    # lower cantle
        pn.line([R(-20, -216), R(30, -216)], shade(sc, 0.4), 4, caps=False)
    if reins_to is not None:
        rt = ((reins_to[0] - x) / k, (reins_to[1] - y) / k)
        pn.line([Hd(196, -212), Hd(150, -228), rt], SADDLE_D, 2.4, caps=False)
    # near legs over the body
    leg('hind', 0.10, col); leg('fore', 0.55, col)
    st_ = None
    if saddle and stirrup and saddle_type != 'horned':
        st_ = R(22, -156) if stirrup_at is None else (stirrup_at[0], stirrup_at[1] + 4)
        pn.line([R(6, -208), st_], SADDLE_D, 3.2, caps=False)
        pn.poly([(st_[0] - 9, st_[1]), (st_[0] + 9, st_[1]), (st_[0] + 6, st_[1] + 11), (st_[0] - 6, st_[1] + 11)], outline=INK, width=3)
        pn.line([(st_[0] - 8, st_[1] + 11), (st_[0] + 8, st_[1] + 11)], IRON, 4, caps=False)
    if rider_near: rider_near(pn)
    pn.pop()
    sx, sy = seat
    return dict(seat=(x + sx * k, y + sy * k), stirrup=(x + st_[0] * k, y + st_[1] * k) if st_ else None, bob=bob)



# ======================================================================================================
# E023 Caesar's double walls at Alesia, 52 BC (BM-P054 to BM-P059, BM-P063): the siege line in section and elevation,
# timber towers, cippi, lilia, stimuli, dolabra, wicker basket, folding camp stool. Sizes in metres times s (px per m),
# Roman foot (pes) = 0.296 m. Light from screen right.
# ======================================================================================================
PES = 0.296
EARTH = (150, 116, 78); EARTH_D = (112, 84, 54); EARTH_L = (186, 152, 106); TURF = (104, 124, 64)
TIMBER = (132, 94, 58); TIMBER_D = (92, 64, 38); TIMBER_L = (176, 136, 90)
WICKER = (170, 130, 76); WICKER_D = (120, 88, 50)
BRUSH = (96, 104, 58)

def _grain(pn, a, b, col, n=2, seed=0):
    rnd = random.Random(seed)
    for i in range(n):
        o = rnd.uniform(-0.3, 0.3)
        pn.line([(lerp(a[0], b[0], 0.1) + o * 4, lerp(a[1], b[1], 0.1)), (lerp(a[0], b[0], 0.9) + o * 4, lerp(a[1], b[1], 0.9))], col, 1.1, caps=False)

def post(pn, x0, y0, x1, y1, w, col=TIMBER, seed=0):
    """Squared timber between two points, two tones, grain."""
    ang = math.atan2(y1 - y0, x1 - x0); nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
    pn.poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=col, outline=INK, width=2.2)
    pn.poly([(x0 + nx * 0.2, y0 + ny * 0.2), (x1 + nx * 0.2, y1 + ny * 0.2), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=light(col, 0.18))
    _grain(pn, (x0, y0), (x1, y1), shade(col, 0.3), 1, seed)

def cervus(pn, x, y, s, ang=-35, L=2.2, seed=0):
    """Cervus: a big forked branch, sharpened, set at the foot of the breastwork pointing out like antlers (Caesar 7.72)."""
    rnd = random.Random(seed); a = math.radians(ang)
    ex, ey = x + math.cos(a) * L * s, y + math.sin(a) * L * s
    pn.line([(x, y), (ex, ey)], INK, max(3, 0.16 * s)); pn.line([(x, y), (ex, ey)], TIMBER_D, max(2, 0.1 * s))
    for q in (0.45, 0.7):
        mx, my = lerp(x, ex, q), lerp(y, ey, q)
        for sd in (-1, 1):
            b = a + sd * rnd.uniform(0.4, 0.7); bl = L * s * rnd.uniform(0.2, 0.32)
            pn.line([(mx, my), (mx + math.cos(b) * bl, my + math.sin(b) * bl)], INK, max(2.4, 0.1 * s))
            pn.line([(mx, my), (mx + math.cos(b) * bl, my + math.sin(b) * bl)], TIMBER_D, max(1.4, 0.06 * s))

def breastwork(pn, x0, x1, y, s, h=1.5, merlon=0.9, gap=0.6, night=0.0):
    """Lorica and pinnae (Caesar 7.72): a wicker breastwork on top of the rampart with battlements (merlons of hurdles)."""
    col = lerpc(WICKER, (60, 60, 80), 0.6 * night); cd = lerpc(WICKER_D, (40, 40, 56), 0.6 * night)
    pn.rect(x0, y - h * 0.55 * s, x1, y, fill=col, outline=INK, width=2.4)
    x = x0
    while x < x1 - 0.1 * s:
        xe = min(x1, x + merlon * s)
        pn.rect(x, y - h * s, xe, y - h * 0.55 * s + 1, fill=col, outline=INK, width=2.4)
        x = xe + gap * s
    # weave: horizontal withies with uprights (stakes) showing
    for j in range(1, int(h / 0.18)):
        yy = y - j * 0.18 * s
        pn.line([(x0 + 2, yy), (x1 - 2, yy)], cd, max(1, 0.05 * s), caps=False)
    for i in range(int((x1 - x0) / (0.35 * s)) + 1):
        xx = x0 + i * 0.35 * s
        pn.line([(xx, y - 0.04 * s), (xx, y - h * 0.55 * s)], shade(col, 0.35), max(1, 0.05 * s), caps=False)

def roman_tower(pn, x, y, s, h=6.0, w=3.0, night=0.0, seed=0):
    """Timber tower on the rampart (Caesar 7.72: towers every 80 feet). Four posts, cross braces, a fighting platform with
    a plank and wicker parapet, a pent roof of boards; ladder inside. (x, y) = base centre on the rampart top.
    Reconstruction after the MuseoParc Alesia rebuilt section (VERIFY proportions)."""
    col = lerpc(TIMBER, (60, 60, 80), 0.6 * night)
    for px in (-w / 2, w / 2):
        post(pn, x + px * s, y, x + px * s * 0.94, y - h * s, max(4, 0.26 * s), col, seed)
    for k_ in range(2):
        y0, y1 = y - k_ * h * 0.42 * s, y - (k_ + 1) * h * 0.42 * s
        pn.line([(x - w / 2 * s, y0), (x + w / 2 * s, y1)], shade(col, 0.2), max(2, 0.14 * s))
        pn.line([(x + w / 2 * s, y0), (x - w / 2 * s, y1)], shade(col, 0.3), max(2, 0.14 * s))
        post(pn, x - w / 2 * s, y1, x + w / 2 * s, y1, max(3, 0.18 * s), col, seed + k_)
    # platform parapet
    py = y - h * s
    pn.rect(x - (w / 2 + 0.25) * s, py - 1.1 * s, x + (w / 2 + 0.25) * s, py + 0.15 * s, fill=lerpc(WICKER, (60, 60, 80), 0.6 * night), outline=INK, width=2.4)
    for j in range(1, 6):
        yy = py - 1.1 * s + j * 0.2 * s
        pn.line([(x - (w / 2 + 0.2) * s, yy), (x + (w / 2 + 0.2) * s, yy)], WICKER_D, max(1, 0.05 * s), caps=False)
    # roof
    pn.poly([(x - (w / 2 + 0.5) * s, py - 2.0 * s), (x + (w / 2 + 0.5) * s, py - 2.4 * s), (x + (w / 2 + 0.5) * s, py - 2.1 * s), (x - (w / 2 + 0.5) * s, py - 1.75 * s)],
            fill=shade(col, 0.1), outline=INK, width=2.4)
    for px in (-w / 2, w / 2):
        pn.line([(x + px * s, py - 1.1 * s), (x + px * s, py - 1.95 * s - (0.2 * s if px > 0 else 0))], INK, max(2, 0.12 * s))
    return dict(top=(x, py - 1.1 * s))

def siege_line_elevation(pn, x0, x1, y, s, rampart=12 * PES, tower_every=80 * PES, night=0.0, build=1.0, towers=True, cervi=True, seed=1):
    """The line seen from outside: earth and turf rampart about 12 feet high, wicker breastwork with battlements, cervi at
    the foot of the breastwork, timber towers about every 80 feet. build 0..1 raises it (earth, then breastwork, then towers)."""
    re_ = clamp(build * 3); bw = clamp(build * 3 - 1); tw = clamp(build * 3 - 2)
    hh = rampart * s * re_
    col = lerpc(EARTH, (50, 50, 66), 0.6 * night); cd = lerpc(EARTH_D, (34, 34, 48), 0.6 * night); tf = lerpc(TURF, (40, 50, 50), 0.6 * night)
    if hh > 1:
        pn.poly([(x0, y), (x0, y - hh), (x1, y - hh), (x1, y)], fill=col, outline=INK, width=2.6)
        rnd = random.Random(seed)
        for j in range(int(rampart / 0.3)):      # cut turf courses (Caesar's rampart of earth and turf)
            yy = y - j * 0.3 * s * re_
            if yy < y - hh: break
            pn.line([(x0, yy), (x1, yy)], cd, max(1, 0.05 * s), caps=False)
            off = (j % 2) * 0.35 * s
            for xx in range(int(x0 + off), int(x1), int(max(8, 0.7 * s))):
                pn.line([(xx, yy), (xx, max(y - hh, yy - 0.3 * s * re_))], cd, max(1, 0.04 * s), caps=False)
        pn.rect(x0, y - hh - 0.12 * s, x1, y - hh + 0.04 * s, fill=tf)
    top = y - hh
    if cervi and bw > 0:
        for i, xx in enumerate(range(int(x0 + 0.6 * s), int(x1), int(max(20, 1.6 * s)))):
            cervus(pn, xx, top - 0.1 * s, s * bw, ang=-150 + (i % 3) * 8, L=1.8, seed=i)
    if bw > 0:
        breastwork(pn, x0, x1, top, s, h=1.5 * bw, night=night)
    if towers and tw > 0:
        n = int((x1 - x0) / (tower_every * s)) + 1
        for i in range(n):
            tx = x0 + (i + 0.5) * tower_every * s
            if tx > x1: break
            roman_tower(pn, tx, top, s, h=6.0 * tw, night=night, seed=i)
    return dict(top=top)

def cippus(pn, x, y, s, seed=0, night=0.0):
    """Cippus (Caesar 7.73): tree trunk or stout branch with its side branches stripped and sharpened, sunk in a trench
    5 feet deep in rows of five, tied together at the base so they could not be pulled up. (x, y) = trench floor."""
    rnd = random.Random(seed); col = lerpc(TIMBER_D, (40, 40, 56), 0.5 * night)
    h = rnd.uniform(1.9, 2.3) * s
    tip = (x + rnd.uniform(-0.2, 0.2) * s, y - h)
    pn.line([(x, y), tip], INK, max(3, 0.16 * s)); pn.line([(x, y), tip], col, max(2, 0.1 * s))
    for q in (0.55, 0.72, 0.86):
        mx, my = lerp(x, tip[0], q), lerp(y, tip[1], q)
        for sd in (-1, 1):
            bl = (1 - q) * h * rnd.uniform(0.6, 0.9)
            ex, ey = mx + sd * bl * 0.7, my - bl * 0.7
            pn.line([(mx, my), (ex, ey)], INK, max(2.4, 0.1 * s)); pn.line([(mx, my), (ex, ey)], col, max(1.4, 0.06 * s))
            pn.poly([(ex, ey), (ex - sd * 0.04 * s, ey + 0.1 * s), (ex + sd * 0.02 * s, ey + 0.08 * s)], fill=TIMBER_L)
    pn.poly([(tip[0], tip[1] - 0.15 * s), (tip[0] - 0.05 * s, tip[1] + 0.05 * s), (tip[0] + 0.05 * s, tip[1] + 0.05 * s)], fill=TIMBER_L, outline=INK, width=1.6)

def lilium(pn, x, y, s, cover=1.0, cut=True, night=0.0):
    """Lilium (Caesar 7.73): pit about 3 feet deep, narrowing toward the bottom, a sharpened stake as thick as a thigh set in
    it, its point standing only about four fingers above the ground; the mouth covered with brushwood. Laid out in eight
    rows, three feet apart. (x, y) = ground at the pit centre; cut=True shows it in section."""
    d = 3 * PES * s; w0 = 0.9 * s; w1 = 0.3 * s
    g = lerpc(EARTH, (50, 50, 66), 0.6 * night)
    if cut:
        pn.poly([(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y + d), (x - w1 / 2, y + d)], fill=(46, 34, 26), outline=INK, width=2.4)
        stake_top = y - 4 * 0.019 * s
        pn.poly([(x - 0.09 * s, y + d), (x + 0.09 * s, y + d), (x + 0.07 * s, stake_top + 0.2 * s), (x, stake_top), (x - 0.07 * s, stake_top + 0.2 * s)],
                fill=TIMBER, outline=INK, width=2)
        pn.line([(x - 0.03 * s, y + d - 0.05 * s), (x - 0.03 * s, stake_top + 0.25 * s)], light(TIMBER, 0.25), 1.2, caps=False)
    if cover > 0:   # brushwood laid over the mouth
        rnd = random.Random(int(x))
        for i in range(int(10 * cover)):
            a = rnd.uniform(-0.25, 0.25); L_ = rnd.uniform(0.6, 1.1) * s; cx_ = x + rnd.uniform(-0.25, 0.25) * s
            pn.line([(cx_ - math.cos(a) * L_ / 2, y - 0.03 * s - math.sin(a) * L_ / 2), (cx_ + math.cos(a) * L_ / 2, y - 0.03 * s + math.sin(a) * L_ / 2)],
                    lerpc(BRUSH, (40, 46, 40), 0.6 * night), max(1.6, 0.05 * s), caps=False)

def stimulus(pn, x, y, s, cut=True, night=0.0, hook=1.0):
    """Stimulus (Caesar 7.73): a wooden peg about a foot long with an iron hook (barbed spike) fixed in its top, driven
    fully into the ground so only the hook shows. Iron hooks of this kind were found in the excavations at Alesia.
    (x, y) = ground level."""
    L_ = 1 * PES * s
    if cut:
        pn.poly([(x - 0.045 * s, y), (x + 0.045 * s, y), (x + 0.03 * s, y + L_), (x, y + L_ + 0.05 * s), (x - 0.03 * s, y + L_)],
                fill=TIMBER, outline=INK, width=2)
    hx, hy = x, y - 0.12 * s * hook
    pn.line([(x, y + 0.02 * s), (hx, hy)], INK, max(3, 0.05 * s)); pn.line([(x, y + 0.02 * s), (hx, hy)], IRON, max(2, 0.03 * s))
    pn.line([(hx, hy), (hx + 0.045 * s, hy + 0.04 * s)], INK, max(2.6, 0.04 * s)); pn.line([(hx, hy), (hx + 0.045 * s, hy + 0.04 * s)], IRON, max(1.6, 0.025 * s))

def siege_line_section(pn, x_r, y, s, night=0.0, show=1.0, labels=None, water=True, traps=1.0, seed=2):
    """The inner line in section, outside (toward the town) on the LEFT, the Roman side on the RIGHT (Caesar 7.72 to 7.73):
    rampart with breastwork and a tower at x_r; two ditches 15 feet wide and deep in front (the inner one filled with water
    where the ground allowed); then trenches of cippi, eight rows of lilia, and stimuli scattered furthest out. The single
    20 foot ditch, about 400 feet further toward the town, is left off (shown in its own beat). Distances compressed:
    SIMPLIFIED. labels(name, (x, y)) is called for each part. traps 0..1 reveals the traps from the wall outward."""
    col = lerpc(EARTH, (50, 50, 66), 0.6 * night); cd = lerpc(EARTH_D, (34, 34, 48), 0.6 * night)
    D15 = 15 * PES * s; W15 = 15 * PES * s
    # ground block
    xL = x_r - 46 * s
    pn.rect(xL - 10 * s, y, x_r + 12 * s, y + D15 + 2.5 * s, fill=col)
    pn.line([(xL - 10 * s, y), (x_r + 12 * s, y)], INK, 3, caps=False)
    # rampart (agger) with breastwork and tower
    rh = 12 * PES * s
    pn.poly([(x_r - 2.2 * s, y), (x_r - 0.3 * s, y - rh), (x_r + 3.4 * s, y - rh), (x_r + 5.4 * s, y)], fill=col, outline=INK, width=2.6)
    for j in range(1, int(rh / (0.3 * s))):
        yy = y - j * 0.3 * s
        pn.line([(x_r - 2.2 * s + (0.3 * s) * j * 1.9 / 12 * 1.0 * 0 + j * 0.3 * s * 1.9 / (12 * PES) * 0.33, yy), (x_r + 5.4 * s - j * 0.3 * s * 0.55, yy)], cd, 1.1, caps=False)
    breastwork(pn, x_r - 0.3 * s, x_r + 0.4 * s, y - rh, s, h=1.5, merlon=0.7, gap=0.3, night=night)
    cervus(pn, x_r - 0.2 * s, y - rh - 0.15 * s, s, ang=-160, L=1.8, seed=seed)
    roman_tower(pn, x_r + 1.8 * s, y - rh, s, h=5.0, w=2.4, night=night, seed=seed)
    if labels: labels('RAMPART', (x_r + 1.6 * s, y + 1.0 * s)); labels('TOWER', (x_r - 2.6 * s, y - rh - 5.0 * s))
    # two ditches 15 feet wide and deep
    xs = []
    for i in range(2):
        cx = x_r - 2.6 * s - W15 / 2 - i * (W15 + 1.2 * s)
        xs.append(cx)
        pn.poly([(cx - W15 / 2, y), (cx + W15 / 2, y), (cx + 0.35 * s, y + D15), (cx - 0.35 * s, y + D15)], fill=(52, 40, 30), outline=INK, width=2.4)
        if water and i == 0:
            wl = y + D15 * 0.35; ww = (W15 / 2) * 0.65
            pn.poly([(cx - ww, wl), (cx + ww, wl), (cx + 0.35 * s, y + D15), (cx - 0.35 * s, y + D15)], fill=lerpc((70, 120, 160), (40, 60, 90), night))
            pn.line([(cx - ww, wl), (cx + ww, wl)], (150, 196, 226), 2, caps=False)
    if labels: labels('TWO DITCHES, 15 FT', (lerp(xs[0], xs[1], 0.5), y + D15 + 1.2 * s))
    # traps, from the wall outward (to the left): cippi trench, lilia, stimuli
    xt = xs[1] - W15 / 2 - 1.2 * s
    tr = clamp(traps * 3)
    if tr > 0:
        tw_ = 4.0 * s; td = 5 * PES * s
        pn.poly([(xt - tw_, y), (xt, y), (xt, y + td), (xt - tw_, y + td)], fill=(70, 54, 40), outline=INK, width=2)
        n = max(1, int(5 * tr))
        for i in range(n):
            cippus(pn, xt - tw_ * (i + 0.5) / 5, y + td, s * 0.85, seed=i, night=night)
        if labels: labels('CIPPI, 5 ROWS', (xt - tw_ / 2, y + td + 1.2 * s))
        xt -= tw_ + 1.0 * s
    lr = clamp(traps * 3 - 1)
    if lr > 0:
        n = max(1, int(8 * lr))
        for i in range(n):
            lilium(pn, xt - (i + 0.5) * 3 * PES * s * 1.0, y, s * 0.9, cover=1.0, night=night)
        if labels: labels('LILIA, 8 ROWS', (xt - 8 * 3 * PES * s * 0.5, y + 2.0 * s))
        xt -= 8 * 3 * PES * s * 1.0 + 1.0 * s
    sr = clamp(traps * 3 - 2)
    if sr > 0:
        n = max(1, int(7 * sr))
        for i in range(n):
            stimulus(pn, xt - (i + 0.5) * 0.5 * s, y, s * 1.4, night=night)
        if labels: labels('STIMULI', (xt - 1.8 * s, y + 1.6 * s))
    return dict(rampart=(x_r, y - rh), ditch=(xs[0], y + D15 * 0.5))

def dolabra(pn, hx, hy, ang, L=100.0, k=1.0, flip=False):
    """Dolabra (BM-P059): Roman legionary's entrenching tool, axe blade on one side of the head and a pick on the other,
    haft about 60 to 70 cm (drawn as 100 rig units). Handle end at (hx, hy), ang the haft direction. Returns grips."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    L *= k; head = (hx + ux * L, hy + uy * L)
    pn.line([(hx, hy), head], INK, 9 * k); pn.line([(hx, hy), head], WOOD, 6 * k)
    pn.line([(hx + nx * 1.4 * k, hy + ny * 1.4 * k), (head[0] + nx * 1.4 * k, head[1] + ny * 1.4 * k)], light(WOOD, 0.3), 1.4 * k, caps=False)
    # axe blade (one side): flares to a curved edge
    sg = -1 if flip else 1
    p = lambda u, v: (head[0] + ux * u * k + nx * v * sg * k, head[1] + uy * u * k + ny * v * sg * k)
    axe = [p(-6, 4), p(6, 4), p(14, 30), p(4, 36), p(-14, 34), p(-10, 28)]
    pn.poly(axe, fill=IRON, outline=INK, width=2.2 * k)
    pn.line([p(12, 30), p(-12, 33)], light(IRON, 0.5), 1.4 * k, caps=False)
    # pick (other side): tapers to a point, curving slightly down toward the handle
    pick = [p(-5, -4), p(5, -4), p(0, -36), p(-4, -34)]
    pn.poly(pick, fill=IRON, outline=INK, width=2.2 * k)
    pn.rect(head[0] - 6 * k, head[1] - 6 * k, head[0] + 6 * k, head[1] + 6 * k, fill=shade(IRON, 0.25), outline=INK, width=1.6 * k)
    return dict(rear=(hx + ux * 8 * k, hy + uy * 8 * k), front=(hx + ux * L * 0.45, hy + uy * L * 0.45), pick=p(0, -36), blade=p(4, 36))

def wicker_basket(pn, cx, cy, w=40.0, h=30.0, earth=1.0):
    """Wicker basket for carrying spoil (Josephus lists a basket in the legionary's kit). (cx, cy) = centre of the rim."""
    pn.poly([(cx - w / 2, cy), (cx + w / 2, cy), (cx + w * 0.38, cy + h), (cx - w * 0.38, cy + h)], fill=WICKER, outline=INK, width=2.4)
    for j in range(1, 5):
        yy = cy + h * j / 5; ww = lerp(w / 2, w * 0.38, j / 5)
        pn.line([(cx - ww, yy), (cx + ww, yy)], WICKER_D, 1.4, caps=False)
    for i in range(-3, 4):
        pn.line([(cx + i * w / 8, cy), (cx + i * w / 8 * 0.76, cy + h)], shade(WICKER, 0.25), 1.2, caps=False)
    if earth > 0:
        pn.poly([(cx - w / 2 + 3, cy + 1), (cx - w / 4, cy - 8 * earth), (cx + w / 6, cy - 10 * earth), (cx + w / 2 - 3, cy + 1)], fill=EARTH, outline=INK, width=2)

def camp_stool(pn, x, y, k=1.0, col=(160, 120, 70)):
    """Sella castrensis: folding camp stool with crossed legs and a leather seat. (x, y) = ground centre."""
    pn.push(x, y, k)
    for sd in (-1, 1):
        pn.line([(-24 * sd, 0), (22 * sd, -46)], INK, 7); pn.line([(-24 * sd, 0), (22 * sd, -46)], col, 4.5)
    pn.line([(-28, -48), (28, -48)], INK, 9); pn.line([(-28, -48), (28, -48)], (120, 60, 40), 6)
    pn.circ(0, -23, 3, fill=(196, 150, 72), outline=INK, width=1.4)
    pn.pop()
    return (x, y - 48 * k)

def gallic_sword(pn, x, y, ang, L=110.0, k=1.0, sheath=False):
    """La Tene long sword (BM-P062): long straight double edged blade with a rounded or blunt point, short grip, small
    pommel; drawn bare or sheathed (iron scabbard with a chape)."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    L *= k; tip = (x + ux * L, y + uy * L)
    if sheath:
        pn.line([(x + ux * 22 * k, y + uy * 22 * k), tip], INK, 10 * k); pn.line([(x + ux * 22 * k, y + uy * 22 * k), tip], (96, 98, 104), 7 * k)
        pn.circ(tip[0], tip[1], 5 * k, fill=(160, 120, 70), outline=INK, width=1.6)
    else:
        pn.poly([(x + ux * 22 * k + nx * 4 * k, y + uy * 22 * k + ny * 4 * k), (tip[0] + nx * 3 * k - ux * 6 * k, tip[1] + ny * 3 * k - uy * 6 * k), tip,
                 (tip[0] - nx * 3 * k - ux * 6 * k, tip[1] - ny * 3 * k - uy * 6 * k), (x + ux * 22 * k - nx * 4 * k, y + uy * 22 * k - ny * 4 * k)],
                fill=(186, 190, 196), outline=INK, width=2 * k)
        pn.line([(x + ux * 24 * k, y + uy * 24 * k), (tip[0] - ux * 8 * k, tip[1] - uy * 8 * k)], (140, 144, 150), 1.2 * k, caps=False)
    pn.line([(x + nx * 7 * k + ux * 20 * k, y + ny * 7 * k + uy * 20 * k), (x - nx * 7 * k + ux * 20 * k, y - ny * 7 * k + uy * 20 * k)], INK, 5 * k)
    pn.line([(x, y), (x + ux * 20 * k, y + uy * 20 * k)], INK, 6 * k); pn.line([(x, y), (x + ux * 20 * k, y + uy * 20 * k)], (120, 84, 52), 4 * k)
    pn.circ(x, y, 4.5 * k, fill=(196, 150, 72), outline=INK, width=1.4)
    return dict(grip=(x + ux * 10 * k, y + uy * 10 * k), tip=tip)

def spear(pn, x, y, ang, L=230.0, k=1.0):
    """Gallic spear (lancea): ash shaft, long leaf shaped iron head. Butt at (x, y)."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    L *= k; tip = (x + ux * L, y + uy * L); hb = (x + ux * (L - 40 * k), y + uy * (L - 40 * k))
    pn.line([(x, y), hb], INK, 7 * k); pn.line([(x, y), hb], WOOD, 4.5 * k)
    pn.poly([(hb[0] + nx * 6 * k, hb[1] + ny * 6 * k), tip, (hb[0] - nx * 6 * k, hb[1] - ny * 6 * k), (hb[0] - ux * 6 * k, hb[1] - uy * 6 * k)], fill=IRON, outline=INK, width=2 * k)
    return tip

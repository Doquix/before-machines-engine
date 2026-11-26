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

def tag(pn, x, y, text, sz=46, t=1.0, rot_=-3, fill=PARCH, col=INK, sub=None, string_to=None):
    """Sticker tag: tilted parchment card with border; pops via t in 0..1 (eoback)."""
    if t <= 0.01: return
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

def stamp(pn, x, y, text, t, sz=120, col=RUST, rot_=-8):
    """Solid stamp slammed from 2.6x to 1x over 0.12 s (t = seconds since slam start)."""
    if t < 0: return
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

def phalanx_token(pn, x, y, s=1.0, open_side=0.0, shield=True, spear=True, col_helm=(196, 150, 72), col_body=(160, 40, 36), up=1):
    """Hoplite seen from straight above (BM-P068). up=1 faces up the screen (his left is screen left), up=-1 faces down
    (his left is screen right). The aspis is upright in front of the body, so from above it is a shallow curved bar set
    to his left, reaching across the left neighbour; open_side 0..1 lights his uncovered right side in RUST.
    Units: rig units (1 m about 154). Shoulders about 70 wide, shield about 130 across."""
    u = up
    P_ = lambda px, py: (px * u, py * u)
    pn.push(x, y, s)
    if spear:
        pn.line([P_(22, 10), P_(22, -150)], (150, 112, 70), 4.5)
        pn.poly([P_(22, -168), P_(17, -150), P_(27, -150)], fill=(112, 116, 124), outline=INK, width=2)
    if open_side > 0:
        pn.ell(*P_(30, 0), 22, 30, fill=RUST + (int(200 * open_side),))
    pn.ell(0, 4 * u, 36, 15, fill=col_body, outline=INK, width=3)
    pn.circ(0, 0, 16, fill=col_helm, outline=INK, width=3)
    pn.circ(0, 0, 6, fill=lerpc(col_helm, (255, 250, 236), 0.4))
    if shield:
        pts = [P_(-38 + 65 * math.cos(math.radians(a)), -30 - 16 * math.sin(math.radians(a))) for a in range(0, 181, 10)]
        pn.poly(pts + [P_(-103, -24), P_(27, -24)], fill=(196, 150, 72), outline=INK, width=3)
        pn.line([P_(-103, -26), P_(27, -26)], lerpc((196, 150, 72), INK, .35), 3)
    pn.pop()

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

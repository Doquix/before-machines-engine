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


# ================= Mongol Empire, early 13th century (period library BM-P007 to BM-P014) =================
# Scale: a 5 ft 8 in figure is about 265 rig units tall, so 1 cm is about 1.53 units and 1 inch about 3.9 units.
CM = 1.53
BIRCH = (234, 226, 206); BIRCH_D = (92, 80, 66)      # birch bark wrap with dark lenticels
MHORN = (164, 146, 116); MHORN_D = (120, 104, 80)     # horn on the belly (greyish amber)
SINEW = (226, 212, 176)                               # sinew on the back, under the bark
MCORE = (206, 176, 118)                               # wooden (or bamboo) core
SIYAH = (150, 108, 64)                                # stiff wooden ears
MLEATH = (110, 66, 42); MLEATH_D = (76, 44, 28)       # grip wrap, bridges, cases
MSTRING = (232, 222, 196)
MSHAFT = (206, 182, 136)                              # birch or willow arrow shaft
MFLETCH = (112, 92, 70); MFLETCH_L = (182, 162, 130)  # brown raptor feathers with bars

# Bow states: st -1 unstrung (reflexed into a C toward the target), 0 braced, 1 full draw.
# (working limb turn in degrees, positive bends toward the archer; siyah kink, negative turns the ear toward the target)
_MB_STATES = {-1.0: (-128.0, -26.0), 0.0: (44.0, -66.0), 1.0: (80.0, -46.0)}
MB_GRIP = 8.0; MB_LIMB = 66.0; MB_SIYAH = 27.0     # about 136 cm along the curve (Ikh Bayan bow; EXARC tomb bow 141 cm)
MARROW_L = 31 * 3.9                                 # arrow about 80 cm (VERIFY: lengths varied)

def _mb_params(st):
    st = clamp(st, -1.0, 1.0)
    if st <= 0:
        a, b = _MB_STATES[-1.0], _MB_STATES[0.0]; u = st + 1
    else:
        a, b = _MB_STATES[0.0], _MB_STATES[1.0]; u = st
    return lerp(a[0], b[0], u), lerp(a[1], b[1], u)

def mbow_local(st, n_limb=14, n_siyah=4):
    """Top limb centreline in the bow frame from the grip outward: (u forward toward the target, v down), tangent angle phi
    (0 = straight up, positive leans toward the archer), and the index of the kink (string bridge)."""
    turn, kink = _mb_params(st)
    pts = [(0.0, 0.0, 0.0), (0.0, -MB_GRIP, 0.0)]
    u, v, phi = 0.0, -MB_GRIP, 0.0
    ds = MB_LIMB / n_limb; dk = math.radians(turn) / n_limb
    for i in range(n_limb):
        phi += dk / 2; u -= math.sin(phi) * ds; v -= math.cos(phi) * ds; phi += dk / 2
        pts.append((u, v, phi))
    ki = len(pts) - 1
    phi += math.radians(kink)
    ds = MB_SIYAH / n_siyah
    for i in range(n_siyah):
        u -= math.sin(phi) * ds; v -= math.cos(phi) * ds
        pts.append((u, v, phi))
    return pts, ki

def mbow_shape(gx, gy, f, st, tilt=0.0):
    """World centreline of the whole bow top tip to bottom tip, with widths and part codes ('g' grip, 'l' limb, 's' siyah),
    plus the world positions of the tips and the string bridges."""
    top, ki = mbow_local(st)
    ca, sa = math.cos(tilt), math.sin(tilt)
    def W_(u, v):
        x, y = f * u, v
        return (gx + x * ca - y * sa, gy + x * sa + y * ca)
    nT = len(top)
    seq = []
    for i in range(nT - 1, 0, -1): seq.append((top[i], i))
    seq.append((top[0], 0))
    for i in range(1, nT): seq.append(((top[i][0], -top[i][1], -top[i][2]), i))
    pts, wid, part = [], [], []
    for (u, v, phi), i in seq:
        pts.append(W_(u, v))
        if i <= 1: wid.append(12.5); part.append('g')
        elif i <= ki:
            s_ = (i - 1) / (ki - 1); wid.append(lerp(10.5, 7.0, s_)); part.append('l')
        else:
            s_ = (i - ki) / (nT - 1 - ki); wid.append(lerp(7.4, 4.6, s_)); part.append('s')
    kT = W_(top[ki][0], top[ki][1]); kB = W_(top[ki][0], -top[ki][1])
    return dict(pts=pts, w=wid, part=part, top=pts[0], bot=pts[-1], kT=kT, kB=kB, ki=ki, n=len(pts))

def mbow_string_bend(grip, hand):
    """Bow state from the real distance the string is pulled behind the grip (braced about 24 units, full draw about 109)."""
    d = math.hypot(grip[0] - hand[0], grip[1] - hand[1])
    return clamp((d - 24) / (109 - 24))

def mongol_bow(pn, gx, gy, f=1, st=0.0, string_to=None, tilt=0.0, hl_horn=0.0, hl_back=0.0, hl_core=0.0, strung=None,
               vib=0.0, cut=False):
    """13th century Mongol composite bow (BM-P007): short, strongly reflexed, recurved with small stiff siyahs and small
    leather string bridges; wooden core, horn on the belly (archer side), sinew on the back (target side) under a thin
    birch bark wrap; leather wrapped grip. st: -1 unstrung, 0 braced, 1 full draw. cut: show the three layers (diagram)."""
    S = mbow_shape(gx, gy, f, st, tilt)
    pts, wid, part, n = S['pts'], S['w'], S['part'], S['n']
    if strung is None: strung = st > -0.5
    L_ = lod(pn, 200)
    # normals: the back side (toward the target when braced) is +f along the bow frame's u axis at the grip
    nrm = []
    for i in range(n):
        a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(tx, ty) or 1
        nrm.append((ty / Ln, -tx / Ln))
    mid_i = n // 2
    gx_n, gy_n = nrm[mid_i]
    ca, sa = math.cos(tilt), math.sin(tilt)
    want = (f * ca, f * sa)
    if gx_n * want[0] + gy_n * want[1] < 0: nrm = [(-x, -y) for x, y in nrm]
    back, belly, b1, b2 = [], [], [], []
    for (x, y), w, (nx, ny) in zip(pts, wid, nrm):
        back.append((x + nx * w / 2, y + ny * w / 2)); belly.append((x - nx * w / 2, y - ny * w / 2))
        b1.append((x + nx * w * 0.12, y + ny * w * 0.12))     # sinew / core boundary
        b2.append((x - nx * w * 0.2, y - ny * w * 0.2))       # core / horn boundary
    # string under the bow so the tips cover its loops
    sp = None
    if strung:
        top, bot, kT, kB = S['top'], S['bot'], S['kT'], S['kB']
        # where the string leaves the limb: it rests on the bridge until the draw lifts it off
        kbT = (kT[0] - nrm[S['ki']][0] * 5, kT[1] - nrm[S['ki']][1] * 5)
        kbB = (kB[0] - nrm[n - 1 - S['ki']][0] * 5, kB[1] - nrm[n - 1 - S['ki']][1] * 5)
        if string_to is not None: mid_s = string_to
        else:
            mid_s = ((kbT[0] + kbB[0]) / 2, (kbT[1] + kbB[1]) / 2)
            if vib > 0: mid_s = (mid_s[0] - f * vib * 12 * math.sin(vib * 60), mid_s[1])
        wrapT = st < 0.35; wrapB = wrapT
        line_ = [top] + ([kbT] if wrapT else []) + [mid_s] + ([kbB] if wrapB else []) + [bot]
        pn.line(line_, MSTRING, 2.6, caps=False)
        pn.line(line_, INK + (140,), 1.0, caps=False)
        sp = mid_s
    # body
    bc = lerpc(BIRCH, AMBER, hl_back) if hl_back else BIRCH
    hc = lerpc(MHORN, AMBER, hl_horn) if hl_horn else MHORN
    for i in range(n - 1):
        pi_ = part[i] if part[i] == part[i + 1] else ('s' if 's' in (part[i], part[i + 1]) else part[i])
        if pi_ == 's':
            pn.poly([back[i], back[i + 1], belly[i + 1], belly[i]], fill=SIYAH)
        elif cut:
            pn.poly([back[i], back[i + 1], b1[i + 1], b1[i]], fill=lerpc(SINEW, AMBER, hl_back))
            pn.poly([b1[i], b1[i + 1], b2[i + 1], b2[i]], fill=lerpc(MCORE, AMBER, hl_core))
            pn.poly([b2[i], b2[i + 1], belly[i + 1], belly[i]], fill=hc)
        else:
            pn.poly([back[i], back[i + 1], b2[i + 1], b2[i]], fill=bc)
            pn.poly([b2[i], b2[i + 1], belly[i + 1], belly[i]], fill=hc)
    if L_ >= 1 and not cut:
        rnd = random.Random(7)
        for i in range(2, n - 2):
            if part[i] == 'l' and rnd.random() < 0.8:      # birch bark lenticels: short dark dashes across the limb
                x, y = pts[i]; nx, ny = nrm[i]; w = wid[i]
                o = (rnd.random() - 0.2) * w * 0.3
                a_ = (x + nx * (o + w * 0.1), y + ny * (o + w * 0.1)); b_ = (x + nx * (o + w * 0.4), y + ny * (o + w * 0.4))
                pn.line([a_, b_], BIRCH_D, 1.3, caps=False)
        pn.line([b for b, p_ in zip(belly, part) if p_ == 'l'][:S['ki']], shade(hc, 0.25), 1.4, caps=False)
    if cut and L_ >= 1:
        for i in range(2, n - 2, 2):
            if part[i] == 'l':
                pn.line([back[i], b1[i]], shade(SINEW, 0.2), 1.0, caps=False)
    pn.poly(back + belly[::-1], outline=INK, width=2.8)
    # siyah joints and nocks
    for i in (S['ki'], n - 1 - S['ki']):
        pn.line([back[i], belly[i]], INK, 2.2, caps=False)
    for i0 in (0, n - 1):
        x, y = pts[i0]; a = pts[1 if i0 == 0 else n - 2]
        dx, dy = x - a[0], y - a[1]; Ln = math.hypot(dx, dy) or 1; ux, uy = dx / Ln, dy / Ln
        pn.poly([(x - uy * 3.4, y + ux * 3.4), (x + uy * 3.4, y - ux * 3.4), (x + ux * 6 + uy * 2, y + uy * 6 - ux * 2)], fill=shade(SIYAH, 0.2), outline=INK, width=1.8)
    # small leather string bridges on the belly at the kinks
    if L_ >= 1:
        for i in (S['ki'], n - 1 - S['ki']):
            x, y = belly[i]; nx, ny = nrm[i]
            pn.circ(x - nx * 1.5, y - ny * 1.5, 3.4, fill=MLEATH, outline=INK, width=1.6)
    # leather wrapped grip with binding
    gi = [i for i, p_ in enumerate(part) if p_ == 'g']
    if gi:
        a, b = gi[0], gi[-1]
        pn.poly([back[a], back[b], belly[b], belly[a]], fill=MLEATH, outline=INK, width=2.4)
        if L_ >= 1:
            for t_ in (0.25, 0.5, 0.75):
                p0 = (lerp(back[a][0], back[b][0], t_), lerp(back[a][1], back[b][1], t_))
                p1 = (lerp(belly[a][0], belly[b][0], t_), lerp(belly[a][1], belly[b][1], t_))
                pn.line([p0, p1], MLEATH_D, 1.4, caps=False)
    return dict(top=S['top'], bot=S['bot'], string=sp, grip=(gx, gy), kT=S['kT'], kB=S['kB'], shape=S)

def mongol_arrow(pn, nock, ang, L=MARROW_L, head='leaf', hl=0.0, fl=True, w=3.2, whistle=False):
    """Mongol arrow: birch or willow shaft, three long brown barred feathers, tanged iron head (light leaf point for
    distance shooting, Marco Polo's two classes: light and heavy broad heads; 'forked' for the broad type)."""
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    q = lambda u, v: (nock[0] + ca * u + nx * v, nock[1] + sa * u + ny * v)
    sc = lerpc(MSHAFT, AMBER, hl) if hl else MSHAFT
    pn.line([q(0, 0), q(L - 12, 0)], INK, w + 2.6)
    pn.line([q(0, 0), q(L - 12, 0)], sc, w)
    if fl:
        for sd, col in ((-1, MFLETCH_L), (1, MFLETCH)):
            pn.poly([q(4, 0), q(6, sd * 7), q(22, sd * 6.5), q(36, sd * 2.5), q(40, 0)], fill=col, outline=INK, width=1.6)
            if lod(pn, 40) >= 1:
                for u_ in (12, 20, 28):
                    pn.line([q(u_, sd * 1.2), q(u_ + 2, sd * 5.2)], shade(col, 0.35), 1.1, caps=False)
        pn.line([q(1, 0), q(4, 0)], (70, 52, 36), w + 1, caps=False)
        pn.line([q(41, 0), q(44, 0)], (120, 40, 34), w + 1.2, caps=False)    # sinew binding painted red
    if whistle:
        pn.ell(*q(L - 22, 0), 6, 4.5, fill=(214, 196, 160), outline=INK, width=1.6)
    pn.line([q(L - 14, 0), q(L - 10, 0)], (90, 70, 50), w + 1.4, caps=False)   # binding over the tang
    if head == 'forked':
        pn.poly([q(L - 10, -2), q(L + 4, -9), q(L + 10, -6), q(L + 1, 0), q(L + 10, 6), q(L + 4, 9), q(L - 10, 2)], fill=IRON, outline=INK, width=1.8)
    else:
        pn.poly([q(L - 10, -2.2), q(L - 2, -4.6), q(L + 9, 0), q(L - 2, 4.6), q(L - 10, 2.2)], fill=IRON, outline=INK, width=1.8)
        if lod(pn, 30) >= 1: pn.line([q(L - 6, 0), q(L + 6, 0)], light(IRON, 0.45), 1.0, caps=False)
    return q(L + 9, 0)

def thumb_ring(pn, x, y, ang=0.0, r=3.6):
    """Thumb ring of horn or bone on the drawing thumb (thumb draw; Mongol archers wore leather, bone or horn rings)."""
    ca, sa = math.cos(ang), math.sin(ang)
    pn.ell(x + ca * 2, y + sa * 2, r + 1.2, r, fill=(226, 212, 176), outline=INK, width=1.6)
    pn.ell(x + ca * 2, y + sa * 2, r * 0.45, r * 0.35, fill=shade((226, 212, 176), 0.35))

def combat_quiver(pn, J, f, n=6, hl=0.0, col=(118, 62, 42), arrows=None):
    """Open combat quiver (BM-P009) on the right hip: hangs from the belt at a slant, bottom forward, top rearward,
    holding about six arrows and covering a third to half their length, fletchings up and back.
    For a right handed archer facing f, the right hip is the back (B) side. arrows: how many still in it."""
    pl, nk = J['pelvis'], J['neck']
    hx, hy = pl[0] - f * 30, pl[1] - 18
    a = math.radians(-24) * f                        # tilt: top toward the rear
    up = (math.sin(a) * -1, -math.cos(a))
    up = (-f * math.sin(math.radians(24)), -math.cos(math.radians(24)))
    sd = (-up[1], up[0])
    q = lambda u, v: (hx + up[0] * u + sd[0] * v, hy + up[1] * u + sd[1] * v)
    m = n if arrows is None else arrows
    # arrows: nock end up, fanned slightly
    for i in range(m):
        o = (i - (n - 1) / 2) * 3.2
        aa = math.atan2(up[1], up[0]) + math.radians(o * 1.4 * f)
        base = q(-36, o * 0.8)
        mongol_arrow(pn, (base[0] + math.cos(aa) * 104, base[1] + math.sin(aa) * 104), aa + math.pi, L=100, head='leaf', fl=True, w=2.6)
    # case: a stiff open pouch, narrow at the mouth, wider at the bottom, tooled border
    cc = lerpc(col, AMBER, hl) if hl else col
    body = [q(30, -11), q(30, 11), q(-40, 15), q(-52, 9), q(-52, -9), q(-40, -15)]
    pn.poly(body, fill=cc, outline=INK, width=2.6)
    if lod(pn, 80) >= 1:
        pn.line([q(24, -8), q(-38, -11), q(-46, -6)], light(cc, 0.3), 1.6, caps=False)
        pn.line([q(24, 8), q(-38, 11)], shade(cc, 0.3), 1.6, caps=False)
        for u_ in (18, -8, -30):
            pn.circ(*q(u_, 0), 2.2, fill=(214, 176, 90), outline=INK, width=1)
    # two straps up to the belt
    belt = (lerp(nk[0], pl[0], 0.88), lerp(nk[1], pl[1], 0.88))
    for u_ in (26, 6):
        pn.line([q(u_, -10), (belt[0] - f * (18 if u_ > 10 else 10), belt[1])], MLEATH_D, 2.6, caps=False)
    return q(30, 0)

def bow_case(pn, J, f, hl=0.0, col=(96, 58, 40)):
    """Bow case (BM-P010) on the left hip (front, F side for a right handed archer facing f): leather, open mouth up and
    forward, tapering down and back along the outer thigh; empty while the bow is in the hand. Size reduced for reading."""
    pl, nk = J['pelvis'], J['neck']
    hx, hy = pl[0] + f * 34, pl[1] - 4
    cc = lerpc(col, AMBER, hl) if hl else col
    q = lambda u, v: (hx + f * u, hy + v)
    body = [q(14, -24), q(24, -12), q(18, 10), q(4, 34), q(-8, 46), q(-8, 24), q(-4, 0), q(2, -20)]
    pn.poly(body, fill=cc, outline=INK, width=2.4)
    if lod(pn, 80) >= 1:
        pn.line([q(12, -18), q(18, -9), q(13, 8), q(1, 28)], (214, 176, 90), 1.4, caps=False)
    belt = (lerp(nk[0], pl[0], 0.88), lerp(nk[1], pl[1], 0.88))
    pn.line([q(12, -22), (belt[0] + f * 18, belt[1])], MLEATH_D, 2.4, caps=False)

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
          stirrup=True, reins_to=None, head_a=0.0, stirrup_at=None):
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
    if saddle:
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
    if saddle and stirrup:
        st_ = R(22, -156) if stirrup_at is None else (stirrup_at[0], stirrup_at[1] + 4)
        pn.line([R(6, -208), st_], SADDLE_D, 3.2, caps=False)
        pn.poly([(st_[0] - 9, st_[1]), (st_[0] + 9, st_[1]), (st_[0] + 6, st_[1] + 11), (st_[0] - 6, st_[1] + 11)], outline=INK, width=3)
        pn.line([(st_[0] - 8, st_[1] + 11), (st_[0] + 8, st_[1] + 11)], IRON, 4, caps=False)
    if rider_near: rider_near(pn)
    pn.pop()
    sx, sy = seat
    return dict(seat=(x + sx * k, y + sy * k), stirrup=(x + st_[0] * k, y + st_[1] * k) if st_ else None, bob=bob)

# ---------------- the Stele of Yisungge (BM-P013) ----------------
GRANITE = (168, 156, 148); GRANITE_D = (122, 112, 106)

def stele(pn, x, y, k=1.0, carve=1.0, hl=0.0, base=True, seed=5):
    """Granite stele, about 202 x 74 x 22 cm, five vertical lines in Uyghur Mongol script. Line 1 (Genghis Khan) set
    highest and line 4 (Yisungge) raised less, as a sign of respect. Script SIMPLIFIED: strokes, not a transcription.
    carve 0..1 reveals the lines top to bottom, left to right."""
    pn.push(x, y, k)
    w, h = 74 * CM, 202 * CM
    rnd = random.Random(seed)
    top = [(-w / 2, -h + 14), (-w / 2 + 14, -h + 2), (-w / 4, -h - 4), (w / 6, -h - 2), (w / 2 - 12, -h + 4), (w / 2, -h + 18)]
    shape = top + [(w / 2 + 2, -6), (-w / 2 - 2, -6)]
    gc = lerpc(GRANITE, AMBER, hl) if hl else GRANITE
    pn.poly([(p[0] + 10, p[1] + 4) for p in shape], fill=shade(gc, 0.35))       # side depth
    pn.poly(shape, fill=gc, outline=INK, width=3)
    if lod(pn, 200) >= 1:
        for i in range(160):
            px = rnd.uniform(-w / 2 + 4, w / 2 - 4); py = rnd.uniform(-h + 12, -10)
            c = rnd.choice((GRANITE_D, light(gc, 0.25), (150, 120, 112)))
            pn.circ(px, py, rnd.uniform(0.8, 1.8), fill=c)
        pn.line([(-w / 2 + 6, -h + 18), (-w / 2 + 6, -12)], light(gc, 0.3), 2, caps=False)
    # five lines, read left to right, each written top to bottom
    starts = (-h + 22, -h + 56, -h + 56, -h + 38, -h + 56)
    ends = (-h * 0.18, -h * 0.12, -h * 0.30, -h * 0.20, -h * 0.55)
    xs = [-w / 2 + 16 + i * (w - 32) / 4 for i in range(5)]
    for i in range(5):
        u = clamp(carve * 5 - i)
        if u <= 0: break
        y0 = starts[i]; y1 = lerp(y0, ends[i], u)
        xx = xs[i]
        pn.line([(xx, y0), (xx, y1)], shade(gc, 0.55), 2.2, caps=False)
        yy = y0 + 6; r2 = random.Random(seed * 31 + i)
        while yy < y1 - 4:
            kind = r2.random(); sd_ = r2.choice((-1, 1))
            if kind < 0.4: pn.line([(xx, yy), (xx + sd_ * 7, yy + 3)], shade(gc, 0.55), 2, caps=False)
            elif kind < 0.7: pn.ell(xx + sd_ * 4, yy + 2, 3.6, 2.6, outline=shade(gc, 0.55), width=1.6)
            else: pn.line([(xx, yy), (xx - sd_ * 5, yy + 5), (xx + sd_ * 3, yy + 8)], shade(gc, 0.55), 1.8, caps=False)
            yy += r2.uniform(9, 15)
    if base:
        pn.rect(-w / 2 - 18, -6, w / 2 + 18, 18, fill=(70, 60, 54), outline=INK, width=3, r=3)
    pn.pop()

# ---------------- composite limb, diagram (BM-P007 cutaway) ----------------
def limb_layers(pn, x, y, ln, th, bend=0.0, hl_horn=0.0, hl_sinew=0.0, hl_core=0.0, arrows=0.0, t=0.0, f=1, birch=False):
    """Side view of a short piece of the limb, the back (sinew) on top, the belly (horn) below; bend 0..1 curls it toward
    the belly as when drawn. arrows 0..1 shows tension (outward, on the back) and compression (inward, on the belly)."""
    n = 24
    R_ = 1e9 if bend <= 1e-3 else ln / (bend * 1.3)
    ctr, nrm = [], []
    for i in range(n + 1):
        s = (i / n - 0.5) * ln
        if bend <= 1e-3:
            ctr.append((x + s, y)); nrm.append((0.0, -1.0))
        else:
            a = s / R_
            ctr.append((x + R_ * math.sin(a), y + R_ * (1 - math.cos(a)))); nrm.append((-math.sin(a), -math.cos(a)))
    def band(o0, o1, col):
        A = [(cx + nx * o0, cy + ny * o0) for (cx, cy), (nx, ny) in zip(ctr, nrm)]
        B = [(cx + nx * o1, cy + ny * o1) for (cx, cy), (nx, ny) in zip(ctr, nrm)]
        pn.poly(A + B[::-1], fill=col, outline=INK, width=2.6)
        return A, B
    s_top, s_bot = th * 0.5, th * 0.12
    c_bot = -th * 0.2
    band(s_bot, s_top, lerpc(SINEW, AMBER, hl_sinew))
    band(c_bot, s_bot, lerpc(MCORE, AMBER, hl_core))
    band(-th * 0.5, c_bot, lerpc(MHORN, AMBER, hl_horn))
    if birch: band(s_top, s_top + 4, BIRCH)
    # material detail: sinew fibres along the length, wood grain, horn streaks
    for j, (o, col, wd) in enumerate(((th * 0.32, shade(SINEW, 0.25), 1.4), (th * 0.4, shade(SINEW, 0.25), 1.4), (th * 0.24, shade(SINEW, 0.25), 1.4),
                                      (-th * 0.04, shade(MCORE, 0.25), 1.6), (-th * 0.36, shade(MHORN, 0.25), 1.6))):
        pts = [(cx + nx * o, cy + ny * o) for (cx, cy), (nx, ny) in zip(ctr[2:-2], nrm[2:-2])]
        pn.line(pts, col, wd, caps=False)
    if arrows > 0:
        a_ = arrows
        L2 = 0.5 * ln * (1 + 0.2 * math.sin(t * 8))
        for i0, sg in ((3, -1), (n - 3, 1)):
            (cx, cy), (nx, ny) = ctr[i0], nrm[i0]
            tx, ty = ny * -1, nx    # tangent
            tx, ty = (ctr[i0 + 1][0] - ctr[i0 - 1][0]), (ctr[i0 + 1][1] - ctr[i0 - 1][1]); Ln = math.hypot(tx, ty); tx, ty = tx / Ln, ty / Ln
            pT = (cx + nx * (th * 0.5 + 26), cy + ny * (th * 0.5 + 26))
            arrow(pn, pT, (pT[0] + sg * tx * 60 * a_, pT[1] + sg * ty * 60 * a_), RUST, 7, 20)       # back stretches: outward
            pC = (cx + nx * (-th * 0.5 - 26), cy + ny * (-th * 0.5 - 26))
            arrow(pn, (pC[0] + sg * tx * 60 * a_, pC[1] + sg * ty * 60 * a_), pC, (40, 90, 150), 7, 20)  # belly squeezes: inward
    return ctr, nrm

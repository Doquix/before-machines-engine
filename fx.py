"""Action effects (docs/ACTION_FX.md): motion smears, speed lines, impact frames and particles.
Every effect is a pure function of time since its event, so any frame renders the same in any order."""
import math, random
from lib import *

FX_GAIN = 1.25          # channel preset: punchy, like an action cartoon (1.0 = clean)

# ---------------- motion smears ----------------
def smear(pn, samples, col=(255, 255, 255), alpha=200, ink=True):
    """Swept band left by a fast moving edge. samples: [(base, tip), ...] oldest first, newest last
    (e.g. hand and sword tip at t - 0.1, t - 0.06, t - 0.03, t). Drawn under the object."""
    if len(samples) < 2: return
    n = len(samples) - 1
    for i in range(n):
        (b0, t0), (b1, t1) = samples[i], samples[i + 1]
        a = int(alpha * ((i + 1) / n) ** 1.4 * min(1.0, FX_GAIN))
        if a < 6: continue
        pn.poly([b0, t0, t1, b1], fill=col + (a,))
    if ink:
        tips = [s[1] for s in samples]
        pn.line(tips, INK + (int(120 * min(1, FX_GAIN)),), 3, caps=False)

def speed_lines(pn, x, y, dirx, diry, t, length=260, n=7, spread=120, seed=0, col=(255, 255, 255), alpha=200, width=5):
    """Streaks trailing behind an object moving along (dirx, diry), anchored to it at (x, y)."""
    Ln = math.hypot(dirx, diry) or 1; ux, uy = dirx / Ln, diry / Ln; nx, ny = -uy, ux
    rnd = random.Random(seed)
    n = int(round(n * FX_GAIN))
    for i in range(n):
        off = rnd.uniform(-spread, spread)
        ph = (t * rnd.uniform(5, 9) + rnd.random()) % 1.0
        L = length * rnd.uniform(0.45, 1.0) * (0.6 + 0.4 * FX_GAIN)
        back = rnd.uniform(20, 120) + ph * 60
        sx, sy = x + nx * off - ux * back, y + ny * off - uy * back
        a = int(alpha * (1 - ph) * rnd.uniform(0.6, 1.0))
        if a < 8: continue
        pn.line([(sx, sy), (sx - ux * L, sy - uy * L)], col + (a,), width * rnd.uniform(0.6, 1.2))

def focus_lines(pn, cx, cy, t, t0, dur=0.25, n=34, r0=260, r1=1500, seed=1, col=(255, 255, 255)):
    """Manga style radial lines converging on a hit, for the first instants after a big impact."""
    u = t - t0
    if u < 0 or u > dur: return
    rnd = random.Random(seed)
    a_ = (1 - u / dur) ** 1.5
    for i in range(int(n * FX_GAIN)):
        ang = rnd.uniform(0, 2 * math.pi); w = rnd.uniform(3, 9)
        ri = r0 * rnd.uniform(0.8, 1.3) + u * 300
        pn.poly([(cx + math.cos(ang - 0.012) * ri, cy + math.sin(ang - 0.012) * ri),
                 (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                 (cx + math.cos(ang + 0.012) * ri, cy + math.sin(ang + 0.012) * ri)], fill=col + (int(170 * a_),))
        if w > 7: pn.line([(cx + math.cos(ang) * ri, cy + math.sin(ang) * ri), (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)], col + (int(120 * a_),), w)

# ---------------- impact frames ----------------
def burst_pts(cx, cy, r_in, r_out, n, seed, rot=0.0):
    rnd = random.Random(seed); pts = []
    for i in range(n * 2):
        a = rot + i * math.pi / n
        r = (r_out * rnd.uniform(0.75, 1.15)) if i % 2 == 0 else r_in * rnd.uniform(0.85, 1.1)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts

def impact(pn, x, y, t, t0, size=1.0, col=(255, 248, 220), seed=0, lines=True):
    """Impact frame: a solid jagged burst for two frames, then an outline ring and radiating strokes that fly out
    and fade over about a quarter second."""
    u = t - t0
    if u < 0 or u > 0.32: return
    s = size * (0.8 + 0.2 * FX_GAIN)
    if u < 2.0 / FPS:
        pn.poly(burst_pts(x, y, 46 * s, 150 * s, 9, seed), fill=INK)
        pn.poly(burst_pts(x, y, 38 * s, 122 * s, 9, seed, 0.05), fill=col)
        pn.circ(x, y, 30 * s, fill=WHITE)
    else:
        q = (u - 2.0 / FPS) / (0.32 - 2.0 / FPS)
        a = int(255 * (1 - q) ** 1.3)
        if a > 6: pn.poly(burst_pts(x, y, (50 + 120 * q) * s, (130 + 140 * q) * s, 9, seed, 0.1), outline=col + (a,), width=max(2, 7 * s * (1 - q)))
    if lines:
        rnd = random.Random(seed + 7)
        q = clamp(u / 0.3)
        for i in range(int(10 * FX_GAIN)):
            ang = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(0.7, 1.2)
            r0 = (90 + 330 * eo3(q) * sp) * s; r1 = r0 + (70 - 50 * q) * s
            a = int(255 * (1 - q))
            if a > 8:
                pn.line([(x + math.cos(ang) * r0, y + math.sin(ang) * r0), (x + math.cos(ang) * r1, y + math.sin(ang) * r1)], INK + (a,), 8 * s * (1 - q) + 2)
                pn.line([(x + math.cos(ang) * r0, y + math.sin(ang) * r0), (x + math.cos(ang) * r1, y + math.sin(ang) * r1)], col + (a,), 4 * s * (1 - q) + 1)

# ---------------- particles ----------------
KIND = {
    # colour, count, speed range, gravity, life, size, drag
    'dust':   ((222, 208, 176), 14, (60, 260), 60, 0.9, 26, 2.6),
    'splash': ((214, 236, 246), 22, (260, 760), 1900, 0.8, 9, 0.4),
    'spray':  ((240, 248, 252), 18, (120, 420), 700, 0.6, 6, 1.0),
    'chips':  ((190, 142, 92), 14, (300, 820), 2200, 0.9, 12, 0.3),
    'sparks': ((255, 214, 96), 16, (420, 1100), 900, 0.35, 4, 0.6),
    'debris': ((150, 146, 136), 10, (220, 640), 2200, 1.0, 10, 0.3),
}

def particles(pn, kind, x, y, t, t0, scale=1.0, seed=0, ang=-math.pi / 2, cone=math.pi * 0.9, ground=None, col=None):
    """Burst of particles from (x, y) at t0, thrown around angle `ang` (radians, screen space, up = -pi/2) within `cone`.
    ground: y below which particles stop falling (they settle and fade)."""
    u = t - t0
    c0, n, (v0, v1), g, life, sz, drag = KIND[kind]
    if u < 0 or u > life * 1.4: return
    c = col or c0
    rnd = random.Random(seed * 131 + len(kind))
    for i in range(int(n * FX_GAIN)):
        a = ang + rnd.uniform(-cone / 2, cone / 2)
        v = rnd.uniform(v0, v1) * scale
        lf = life * rnd.uniform(0.6, 1.2)
        if u > lf: continue
        # velocity with drag, gravity
        k = (1 - math.exp(-drag * u)) / drag if drag > 0 else u
        px = x + math.cos(a) * v * k
        py = y + math.sin(a) * v * k + 0.5 * g * scale * u * u
        if ground is not None and py > ground: py = ground
        q = u / lf
        al = int(235 * (1 - q) ** (0.6 if kind != 'dust' else 1.2))
        r = sz * scale * rnd.uniform(0.6, 1.3)
        if kind == 'dust':
            pn.circ(px, py, r * (0.6 + 1.6 * q), fill=c + (int(al * 0.75),))
        elif kind in ('splash', 'spray'):
            vx = math.cos(a) * v * math.exp(-drag * u); vy = math.sin(a) * v * math.exp(-drag * u) + g * scale * u
            sp = math.hypot(vx, vy) or 1
            tail = min(40, sp * 0.025) * scale
            pn.line([(px, py), (px - vx / sp * tail, py - vy / sp * tail)], c + (al,), r * 1.2)
            pn.circ(px, py, r * 0.8, fill=c + (al,))
        elif kind == 'sparks':
            vx = math.cos(a) * v; vy = math.sin(a) * v + g * scale * u
            sp = math.hypot(vx, vy) or 1
            pn.line([(px, py), (px - vx / sp * 26 * scale, py - vy / sp * 26 * scale)], c + (al,), r)
            pn.circ(px, py, r * 0.9, fill=(255, 250, 220, al))
        else:   # chips, debris: tumbling shards
            rot = rnd.uniform(-14, 14) * u + rnd.random() * 6
            w_, h_ = r * 1.6, r * 0.55
            ca, sa = math.cos(rot), math.sin(rot)
            pts = [(px + dx * ca - dy * sa, py + dx * sa + dy * ca) for dx, dy in ((-w_, -h_), (w_, -h_ * 0.4), (w_, h_), (-w_, h_ * 0.6))]
            pn.poly(pts, fill=c + (al,), outline=INK + (al,), width=1.6)

def ring(pn, x, y, r, col, u, width=8):
    if 0 < u < 1: pn.circ(x, y, r, outline=col + (int(255 * (1 - u)),), width=width)

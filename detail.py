"""Material helpers for detailed props (docs/PROP_DETAIL.md).
Light comes from the upper left. Every helper scales its detail with the size it is drawn at on screen."""
import math, random
from lib import *

def onscreen(pn, units):
    """Size in final screen pixels of `units` drawn with the current pen transform and camera."""
    return units * pn.k()

FIXED_DETAIL = False   # True: every detail is drawn at every size (no popping when the camera moves in or out)

def lod(pn, units):
    """0 = silhouette (under ~120 px), 1 = construction and materials, 2 = full detail (over ~400 px).
    With FIXED_DETAIL the answer is always 2, so details never appear or vanish as the camera moves."""
    if FIXED_DETAIL: return 2
    s = onscreen(pn, units)
    return 0 if s < 120 else (1 if s < 400 else 2)

def thin_ok(pn, width, minpx=1.6):
    """True when a line of `width` units is at least `minpx` screen pixels: thinner lines are noise."""
    if FIXED_DETAIL: return True
    return width * pn.k() >= minpx

def shade(c, a): return lerpc(c, (20, 14, 10), a)
def light(c, a): return lerpc(c, (255, 250, 236), a)

def _frame(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy) or 1.0
    return dx / Ln, dy / Ln, -dy / Ln, dx / Ln, Ln

def wood_plank(pn, a, b, w, col, seed=0, grain=True, bevel=True, outline=3.4, knots=True, nails=None):
    """A plank from a to b, w wide: base tone, lit top edge, shaded bottom edge, grain along its length."""
    ux, uy, nx, ny, Ln = _frame(a, b)
    if ny > 0: nx, ny = -nx, -ny          # n points to the lit (upper) side
    h = w / 2
    q = lambda u, v: (a[0] + ux * u + nx * v, a[1] + uy * u + ny * v)
    pn.poly([q(0, h), q(Ln, h), q(Ln, -h), q(0, -h)], fill=col, outline=INK, width=outline)
    L = lod(pn, Ln)
    if L == 0: return
    if bevel and thin_ok(pn, w * 0.18):
        pn.poly([q(2, h - 1), q(Ln - 2, h - 1), q(Ln - 2, h * 0.55), q(2, h * 0.55)], fill=light(col, 0.22))
        pn.poly([q(2, -h + 1), q(Ln - 2, -h + 1), q(Ln - 2, -h * 0.6), q(2, -h * 0.6)], fill=shade(col, 0.22))
    if grain and thin_ok(pn, 1.2):
        rnd = random.Random(seed)
        n = 2 if L == 1 else 4
        gc = shade(col, 0.38); gl = light(col, 0.18)
        for i in range(n):
            v = lerp(-h * 0.5, h * 0.5, (i + 0.5) / n) + rnd.uniform(-h * .1, h * .1)
            pts = []
            for j in range(9):
                u = Ln * (0.04 + 0.92 * j / 8)
                pts.append(q(u, v + math.sin(u / max(8, w * 2.2) + i * 1.7 + seed) * h * 0.12))
            pn.line(pts, gc + (210,), max(1.0, w * 0.07), caps=False)
            if L == 2: pn.line([(px_, py_ + max(1.0, w * 0.06)) for px_, py_ in pts], gl + (160,), max(1.0, w * 0.04), caps=False)
        if knots and L == 2 and Ln > w * 5:
            u = Ln * rnd.uniform(0.3, 0.7); v = rnd.uniform(-h * .3, h * .3)
            pn.ell(*q(u, v), w * 0.18, w * 0.1, fill=shade(col, 0.35))
    if nails and L >= 1:
        for u in nails:
            for v in (-h * 0.45, h * 0.45):
                rivet(pn, *q(u, v), max(1.6, w * 0.07), IRON)

def rivet(pn, x, y, r, col=IRON):
    if r * pn.k() < 1.4: return
    pn.circ(x, y, r, fill=shade(col, 0.25), outline=INK if r * pn.k() > 3 else None, width=1.2)
    pn.circ(x - r * 0.3, y - r * 0.3, r * 0.45, fill=light(col, 0.5))

def metal_poly(pn, pts, col, width=3.2, hi=None, sh=None):
    """Metal surface: base tone, shaded lower right band, one hard highlight (pass point lists to override)."""
    pn.poly(pts, fill=col, outline=INK, width=width)
    if sh: pn.poly(sh, fill=shade(col, 0.28))
    if hi: pn.poly(hi, fill=light(col, 0.55))

def rope(pn, pts, w, col=ROPE, slack=0.0):
    """Twisted rope: outline, body, then short diagonal strand marks when it is big enough to read."""
    pn.line(pts, INK, w + 2.4); pn.line(pts, col, w)
    if not thin_ok(pn, w, 3.0): return
    sc = shade(col, 0.35)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        Ln = math.hypot(x1 - x0, y1 - y0); n = int(Ln / (w * 1.4))
        if n < 1: continue
        ux, uy = (x1 - x0) / Ln, (y1 - y0) / Ln; nx, ny = -uy, ux
        for i in range(n):
            u = (i + 0.5) / n
            cx, cy = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            pn.line([(cx - nx * w * .45 - ux * w * .35, cy - ny * w * .45 - uy * w * .35),
                     (cx + nx * w * .45 + ux * w * .35, cy + ny * w * .45 + uy * w * .35)], sc, max(1.0, w * 0.22), caps=False)

def scratches(pn, x, y, s, seed=0, col=None, n=3):
    """A few light wear marks around (x, y)."""
    if s * pn.k() < 40: return
    rnd = random.Random(seed)
    for _ in range(n):
        a = rnd.uniform(-0.6, 0.6); L = rnd.uniform(0.1, 0.22) * s
        cx, cy = x + rnd.uniform(-s * .2, s * .2), y + rnd.uniform(-s * .2, s * .2)
        pn.line([(cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L)], col or (255, 255, 255, 55), max(1.0, s * 0.01), caps=False)

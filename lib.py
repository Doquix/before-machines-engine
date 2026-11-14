"""Before Machines engine: easing, camera, a camera-aware vector pen drawn at 2x, caching."""
import math, random
from collections import OrderedDict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SS = 2
CX, CY = 540, 860
FD = '/usr/share/fonts/opentype/inter/'

INK = (38, 30, 22); MUTED = (120, 105, 85); RUST = (170, 60, 40); BRONZE = (184, 134, 60)
IRON = (110, 114, 122); WOOD = (139, 98, 58); WOOD_D = (98, 66, 38); PARCH = (236, 226, 204)
AMBER = (246, 178, 52); WHITE = (255, 255, 255); SKIN = (247, 234, 212); ROPE = (196, 168, 112)
STONE = (150, 146, 136); STONE_D = (112, 108, 100)

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def P(t, t0, d): return clamp((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)
def lerp(a, b, x): return a + (b - a) * x
def lerpc(c1, c2, x): return tuple(int(round(lerp(a, b, x))) for a, b in zip(c1, c2))
def eo3(x): return 1 - (1 - x) ** 3
def ei3(x): return x ** 3
def ei2(x): return x * x
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eoexpo(x): return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def eoback(x, s=1.9):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)
def spring(dt, f=1.9, z=6.5):
    if dt <= 0: return 0.0
    return 1 - math.exp(-z * dt) * math.cos(2 * math.pi * f * dt)
def pop(t, t0, d=0.32): return eoback(P(t, t0, d)) if t >= t0 else 0.0
def win(t, a, b, fi=0.15, fo=0.15):
    if t < a or t > b: return 0.0
    return min(P(t, a, fi), 1 - P(t, b - fo, fo))

_F = {}
def F(w, size, disp=False):
    k = (w, max(4, int(round(size))), disp)
    if k not in _F:
        _F[k] = ImageFont.truetype(FD + ('InterDisplay-' if disp else 'Inter-') + w + '.otf', k[1])
    return _F[k]

_C = OrderedDict()
def cache(key, fn, maxn=60):
    if key in _C:
        _C.move_to_end(key); return _C[key]
    v = fn(); _C[key] = v
    if len(_C) > maxn: _C.popitem(last=False)
    return v

class Cam:
    def __init__(c):
        c.punch = []; c.shake = []; c.extra = None
        c.s = 1.0; c.ox = 0.0; c.oy = 0.0; c.drift = 1.0
    def set(c, t):
        dr = c.drift
        sc = 1.0 + 0.02 * dr + 0.014 * dr * math.sin(2 * math.pi * t / 7.3)
        ox = 8 * dr * math.sin(2 * math.pi * t / 9.1)
        oy = 6 * dr * math.sin(2 * math.pi * t / 6.7 + 1)
        for t0, amt in c.punch:
            if t >= t0:
                p = t - t0
                sc += amt * eoexpo(clamp(p / 0.1)) * math.exp(-max(0.0, p - 0.1) * 2.2)
        for t0, amp, dur in c.shake:
            if t0 <= t < t0 + dur:
                k = (1 - (t - t0) / dur) ** 2
                ox += amp * k * math.sin(2 * math.pi * 23 * (t - t0))
                oy += amp * k * math.cos(2 * math.pi * 19 * (t - t0) + .5)
        if c.extra: sc, ox, oy = c.extra(t, sc, ox, oy)
        c.s, c.ox, c.oy = sc, ox, oy
CAM = Cam()

class Pen:
    """Draws in 1080x1920 design units onto a 2x canvas; optional camera and local transform."""
    def __init__(s, img, cam=True):
        s.img = img; s.d = ImageDraw.Draw(img, 'RGBA'); s.cam = cam
        s.stack = []; s.T = (1.0, 0.0, 0.0)   # local scale, dx, dy (applied before camera)
    # local transforms for drawing a group at a position and scale
    def push(s, x, y, k):
        s.stack.append(s.T); a, b, c = s.T
        s.T = (a * k, b + x * a, c + y * a)
    def pop(s): s.T = s.stack.pop()
    def k(s):
        return s.T[0] * (CAM.s if s.cam else 1.0)
    def xy(s, x, y):
        a, b, c = s.T; x = b + x * a; y = c + y * a
        if s.cam: x = CX + (x - CX) * CAM.s + CAM.ox; y = CY + (y - CY) * CAM.s + CAM.oy
        return x * SS, y * SS
    def w(s, v): return max(1, int(round(v * s.k() * SS)))
    def line(s, pts, fill, width, caps=True):
        P2 = [s.xy(*p) for p in pts]
        wd = s.w(width)
        s.d.line(P2, fill=fill, width=wd, joint='curve')
        if caps:
            r = wd / 2
            for x, y in (P2[0], P2[-1]):
                s.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    def poly(s, pts, fill=None, outline=None, width=0):
        P2 = [s.xy(*p) for p in pts]
        s.d.polygon(P2, fill=fill)
        if outline and width:
            s.d.line(P2 + [P2[0]], fill=outline, width=s.w(width), joint='curve')
    def circ(s, x, y, r, fill=None, outline=None, width=0):
        X, Y = s.xy(x, y); R = r * s.k() * SS
        if R < 0.5: return
        s.d.ellipse([X - R, Y - R, X + R, Y + R], fill=fill, outline=outline, width=s.w(width) if width else 0)
    def ell(s, x, y, rx, ry, fill=None, outline=None, width=0):
        X, Y = s.xy(x, y); kk = s.k() * SS
        s.d.ellipse([X - rx * kk, Y - ry * kk, X + rx * kk, Y + ry * kk], fill=fill, outline=outline, width=s.w(width) if width else 0)
    def rect(s, x0, y0, x1, y1, fill=None, outline=None, width=0, r=0):
        X0, Y0 = s.xy(x0, y0); X1, Y1 = s.xy(x1, y1)
        if X1 < X0: X0, X1 = X1, X0
        if Y1 < Y0: Y0, Y1 = Y1, Y0
        if X1 - X0 < 1 or Y1 - Y0 < 1: return
        rr = min(r * s.k() * SS, (X1 - X0) / 2, (Y1 - Y0) / 2)
        s.d.rounded_rectangle([X0, Y0, X1, Y1], rr, fill=fill, outline=outline, width=s.w(width) if width else 0)
    def arc(s, x, y, r, a0, a1, fill, width):
        X, Y = s.xy(x, y); R = r * s.k() * SS
        s.d.arc([X - R, Y - R, X + R, Y + R], a0, a1, fill=fill, width=s.w(width))
    def text(s, x, y, t, size, fill, weight='Bold', anchor='mm', disp=False, sp=0):
        sz = size * s.k() * SS
        if sz < 4 * SS: return
        f = F(weight, sz, disp); X, Y = s.xy(x, y)
        if not sp:
            s.d.text((X, Y), t, font=f, fill=fill, anchor=anchor); return
        spx = sp * s.k() * SS
        tw = sum(f.getlength(c) for c in t) + spx * (len(t) - 1)
        x0 = X - (tw / 2 if anchor[0] == 'm' else tw if anchor[0] == 'r' else 0)
        for c in t:
            s.d.text((x0, Y), c, font=f, fill=fill, anchor='l' + anchor[1]); x0 += f.getlength(c) + spx
    def tw(s, t, size, weight='Bold', disp=False):
        return F(weight, size * 4, disp).getlength(t) / 4

def rot(px, py, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return cx + (px - cx) * ca - (py - cy) * sa, cy + (px - cx) * sa + (py - cy) * ca

def new_layer(): return Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
def flatten(base, layer):
    small = layer.resize((W, H), Image.BOX)
    base.alpha_composite(small)

def bg_cam(img, par=1.0):
    """Apply the camera to a full frame background (par < 1 for parallax)."""
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par
    # inverse affine: src = (dst - C - o)/s + C
    a = 1 / s
    return img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR)

def radial_mask(ox, oy, p):
    lw, lh = 135, 240
    yy, xx = np.mgrid[0:lh, 0:lw]
    d = np.sqrt((xx * 8 - ox) ** 2 + (yy * 8 - oy) ** 2)
    maxd = max(math.hypot(ox - a, oy - b) for a in (0, W) for b in (0, H)) + 160
    m = np.clip((p * maxd - d) / 140 + 0.5, 0, 1)
    return Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)

"""2.5D depth world: flat layers placed at real depths, seen through a perspective camera.

World units are rig units (a man is about 265 tall, 1 m is about 154). Y points down; the ground is Y = 0.
Figures and props stay flat cutouts (billboards that always face the camera); only their placement, scale,
parallax, haze and focus come from depth. No pitch: the horizon stays at a fixed screen height.

    cam = Cam3(x, y=-eye_height, z, yaw, F, horizon)
    scene = Scene(); scene.sky(...); scene.ridge(...); scene.ground(...); scene.card(X, Z, draw_fn); ...
    frame = scene.render(cam)            # PIL RGB image, 1080 x 1920

Depth of field and haze work per depth band: each band is drawn on its own layer, blurred, then composited
far to near. Helpers: orbit(target, R, a) for a camera that circles a point while keeping it centred.
"""
import math, random
import numpy as np
from PIL import Image, ImageFilter
from lib import *

class Cam3:
    def __init__(c, x=0.0, y=-200.0, z=0.0, yaw=0.0, F=3600.0, horizon=860.0, cx=CX):
        c.x, c.y, c.z, c.yaw, c.F, c.hy, c.cx = x, y, z, yaw, F, horizon, cx
    def to_cam(c, X, Y, Z):
        dx, dz = X - c.x, Z - c.z; co, si = math.cos(c.yaw), math.sin(c.yaw)
        return dx * co + dz * si, Y - c.y, -dx * si + dz * co
    def proj(c, X, Y, Z):
        xr, yr, zr = c.to_cam(X, Y, Z)
        if zr <= 1: return None
        k = c.F / zr
        return c.cx + xr * k, c.hy + yr * k, k, zr

def orbit(tx, ty, tz, R, a, F=3600.0, horizon=860.0, eye=None):
    """Camera on a circle of radius R around (tx, tz), angle a (radians, 0 = straight in front), aimed at the target."""
    eye = ty if eye is None else eye
    return Cam3(tx + R * math.sin(a), eye, tz - R * math.cos(a), a, F, horizon)

def haze(col, zr, sky, dist=16000.0, amt=0.85):
    h = amt * (1 - math.exp(-max(0.0, zr) / dist))
    return lerpc(col[:3], sky[:3], h) + ((col[3],) if len(col) > 3 else ())

# depth bands: (name, near z, far z, blur radius in output px)
BANDS = [('far', 7000, 1e9, 3.0), ('mid', 2600, 7000, 1.4), ('subject', 700, 2600, 0.0), ('fore', 1, 700, 7.0)]

class Scene:
    def __init__(s, sky_top=(150, 178, 206), sky_bot=(238, 224, 190)):
        s.top, s.bot = sky_top, sky_bot; s.items = []
        s.focus = None          # optional (near, far) override for the sharp band
    # --- builders ---
    def ridge(s, Z, heights, col, x0=-40000, x1=40000, seed=1):
        """A mountain or hill line at depth Z: heights is a function X -> height (world units), or a number."""
        s.items.append(('ridge', Z, dict(h=heights, col=col, x0=x0, x1=x1, seed=seed)))
    def ground(s, col, col2=None, stripes=True):
        s.items.append(('ground', 1e12, dict(col=col, col2=col2 or shade(col, 0.08), stripes=stripes)))
    def tufts(s, n, x0, x1, z0, z1, col, seed=7, size=1.0):
        rnd = random.Random(seed)
        for _ in range(n):
            X, Z = rnd.uniform(x0, x1), z0 * (z1 / z0) ** rnd.random()
            s.items.append(('tuft', Z, dict(X=X, col=col, h=rnd.uniform(10, 22) * size, seed=rnd.random())))
    def card(s, X, Z, draw, Y=0.0, scale=1.0):
        """draw(pn, sx, sy, k): draws a flat cutout whose ground contact point is (sx, sy) at scale k."""
        s.items.append(('card', Z, dict(X=X, Y=Y, draw=draw, scale=scale)))
    # --- render ---
    def _band(s, zr):
        for name, a, b, _ in BANDS:
            if a <= zr < b: return name
        return 'far'
    def render(s, cam):
        im = Image.new('RGBA', (W, H)); px = np.zeros((H, W, 4), np.uint8)
        g = np.linspace(0, 1, H)[:, None]
        hy = cam.hy / H
        tcol = np.array(s.top, float); bcol = np.array(s.bot, float)
        sky = tcol + (bcol - tcol) * np.clip(g / max(hy, 1e-3), 0, 1)
        px[..., :3] = sky[:, None, :].astype(np.uint8).repeat(W, 1); px[..., 3] = 255
        im = Image.fromarray(px, 'RGBA')
        layers = {b[0]: new_layer() for b in BANDS}
        pens = {k: Pen(v, cam=False) for k, v in layers.items()}
        # ground is drawn first on the far layer (it spans every depth)
        order = []
        for kind, Z, d in s.items:
            if kind == 'ground': order.append((1e12, kind, d)); continue
            if kind == 'ridge': order.append((Z, kind, d)); continue
            X = d['X']; pr = cam.proj(X, d.get('Y', 0.0), Z)
            if pr is None: continue
            order.append((pr[3], kind, d, pr))
        order.sort(key=lambda o: -o[0])
        for o in order:
            kind = o[1]; d = o[2]
            if kind == 'ground': s._ground(pens['far'], cam, d); continue
            if kind == 'ridge':
                zr = cam.to_cam(0, 0, o[0])[2]
                s._ridge(pens[s._band(zr)], cam, o[0], d); continue
            sx, sy, k, zr = o[3]
            if sx < -600 or sx > W + 600: continue
            pn = pens[s._band(zr)]
            if kind == 'tuft':
                c = haze(d['col'], zr, s.bot, amt=0.7); h = d['h'] * k
                if h < 0.6: continue
                for j in range(3):
                    a = (j - 1) * 0.35 + (d['seed'] - 0.5) * 0.3
                    pn.line([(sx + (j - 1) * 3 * k, sy), (sx + (j - 1) * 3 * k + math.sin(a) * h, sy - math.cos(a) * h)], c, max(0.6, 2.2 * k))
            else:
                d['draw'](pn, sx, sy, k * d['scale'])
        for name, a, b, blur in sorted(BANDS, key=lambda t: -t[1]):
            small = layers[name].resize((W, H), Image.BOX)
            if blur > 0: small = small.filter(ImageFilter.GaussianBlur(blur))
            im.alpha_composite(small)
        return im.convert('RGB')
    def _ground(s, pn, cam, d):
        col, col2 = d['col'], d['col2']
        pn.poly([(-50, cam.hy), (W + 50, cam.hy), (W + 50, H + 50), (-50, H + 50)], fill=haze(col, 3000, s.bot, amt=0.3))
        if d['stripes']:   # field bands at fixed depths: they slide as the camera dollies (the main depth cue)
            base = 500.0
            for i in range(0, 60):
                Za = base * 1.18 ** i; Zb = base * 1.18 ** (i + 1)
                if Zb < cam.z + 30: continue
                pa = (cam.F / max(30.0, Za - cam.z)) * (-cam.y) + cam.hy
                pb = (cam.F / max(30.0, Zb - cam.z)) * (-cam.y) + cam.hy
                if pb > H + 50: continue
                c = col if i % 2 else col2
                zr = (Za + Zb) / 2 - cam.z
                pn.poly([(-50, min(pa, H + 50)), (W + 50, min(pa, H + 50)), (W + 50, pb), (-50, pb)], fill=haze(c, zr, s.bot, amt=0.75))
    def _ridge(s, pn, cam, Z, d):
        h = d['h']; rnd = random.Random(d['seed'])
        ph = [rnd.random() * 6.28 for _ in range(4)]
        def hf(X):
            if callable(h): return h(X)
            return h * (0.55 + 0.25 * math.sin(X / 9000 + ph[0]) + 0.13 * math.sin(X / 3100 + ph[1]) + 0.07 * math.sin(X / 1100 + ph[2]))
        pts = []
        zr = cam.to_cam(0, 0, Z)[2]
        if zr <= 1: return
        span = (W * 0.9) * zr / cam.F
        xc = cam.x - math.sin(cam.yaw) * zr
        for i in range(81):
            X = xc - span + 2 * span * i / 80
            p = cam.proj(X, -hf(X), Z)
            if p: pts.append((p[0], p[1]))
        if len(pts) < 2: return
        pg = cam.proj(xc, 0, Z)
        gy = pg[1] if pg else cam.hy
        pts = pts + [(pts[-1][0], gy + 4), (pts[0][0], gy + 4)]
        pn.poly(pts, fill=haze(d['col'], zr, s.bot, dist=70000.0, amt=0.7))

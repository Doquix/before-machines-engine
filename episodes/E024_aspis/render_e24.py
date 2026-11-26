"""E024 Greek hoplite aspis: full render. Rig v2 cutout figures, world25 depth scenes, mesh3d props.
Usage: python3 render_e24.py [still t1 t2 ...] | [frames a b]   (frames writes PNGs a..b-1 into /tmp/e24f)"""
import math, os, sys, json, random, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image, ImageFilter
from lib import *
import rig as R, rig_cutout as C, world25 as W25, mesh3d as M, props as PR, env as E

CAM.drift = 0; CAM.set(0)
CUR = {'t': 0.0}
def HOP(pn, *a, **kw):
    """Rig v2 hoplite with breathing and blinks on the global clock (no frozen frames)."""
    kw.setdefault('t', CUR['t']); kw.setdefault('blink', R.blink_at(CUR['t'], a[0] * 0.0031))
    return C.hoplite(pn, *a, **kw)
WORDS = json.load(open(os.path.join(HERE, 'audio', 'words.json')))
def w(beat, i): return WORDS[beat - 1]['words'][i]['t']
def bs(beat): return WORDS[beat - 1]['start']
END = 47.4
AMBER_ = AMBER
BRZ = (196, 150, 72)

# ---------------- shot table (start times are phrase starts) ----------------
SHOTS = [  # (start, name)
    (0.0, 's1'), (bs(3), 's2'), (bs(4), 's3'), (bs(7), 's4'), (bs(8), 's5'), (bs(9), 's6'), (bs(10), 's7'), (bs(11), 's8'),
    (bs(12), 's9'), (bs(13), 's10'), (bs(14), 's11'), (bs(15), 's12'), (bs(17), 's13'), (bs(19), 's14'), (bs(20), 's15')]
SLIDES = {bs(3), bs(10), bs(15), bs(17)}
DISSOLVES = {bs(7)}
PUNCH = [(w(2, 6), 0.06), (w(8, 3), 0.07), (w(16, 5), 0.06), (w(17, 9), 0.05), (w(20, 4), 0.05)]

def ke(t, keys, ease=eio):
    """Keyframes [(t, v), ...] with easing between them."""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1:
            u = ease((t - t0) / (t1 - t0))
            return tuple(lerp(a, b, u) for a, b in zip(v0, v1)) if isinstance(v0, tuple) else lerp(v0, v1, u)
    return keys[-1][1]

# ---------------- helpers ----------------
FLAT = W25.Cam3(0, 0, -3600, 0, F=3600, horizon=0, cx=0)          # parchment scenes: world (x, y, 0) = screen (x, y)

def flat_hooks(x, y, k, store=None, cam=FLAT):
    wpt = lambda lx, ly, dz: (x + lx * k, y + ly * k, dz * k)
    def shield_fn(pn_, cx, cy, r, f):
        if store is not None: store['shield'] = (x + cx * k, y + cy * k, r * k)
        M.draw_mesh(pn_, cam, M.get('aspis'), wpt(cx, cy, -14), M.rot(-f * 0.22, 0, 0 if f == 1 else math.pi), scale=k * r / 64)
    def spear_fn(pn_, gx, gy, a, back):
        M.draw_mesh(pn_, cam, M.dory_for(back), wpt(gx, gy, -8), M.rot(0, 0, a), scale=k)
    return dict(shield_fn=shield_fn, spear_fn=spear_fn)

def world_hooks(cam, X, Z, store=None):
    co, si = math.cos(cam.yaw), math.sin(cam.yaw)
    wpt = lambda lx, ly, dz: (X + lx * co, ly, Z + lx * si + dz)
    def shield_fn(pn_, cx, cy, r, f):
        if store is not None:
            p = cam.proj(*wpt(cx, cy, -14))
            if p: store['shield'] = (p[0], p[1], r * p[2])
        M.draw_mesh(pn_, cam, M.get('aspis'), wpt(cx, cy, -14), M.rot(-f * 0.22, 0, 0 if f == 1 else math.pi), scale=r / 64)
    def spear_fn(pn_, gx, gy, a, back):
        M.draw_mesh(pn_, cam, M.dory_for(back), wpt(gx, gy, -8), M.rot(0, 0, a))
    return dict(shield_fn=shield_fn, spear_fn=spear_fn)

def frame_cam(X, Z, Yt, Yb, st, sb, hy=900.0, F=3600.0, sx=540.0):
    """Camera that puts world heights Yt..Yb (at depth Z) on screen rows st..sb, and world X on screen column sx."""
    k = (sb - st) / (Yb - Yt); zr = F / k
    cy = Yb - (sb - hy) / k
    return W25.Cam3(X - (sx - 540) / k, cy, Z - zr, 0.0, F, hy)

def bare_side(pn, x, y, k, a, f=-1):
    """RUST glow on a front on figure's uncovered right side (screen left when facing left)."""
    if a <= 0: return
    pn.push(x, y, k)
    pn.ell(f * 34, -112, 22, 52, fill=RUST + (int(150 * a),), outline=RUST + (int(255 * a),), width=4)
    pn.pop()

def floor(pn, y, col=(206, 190, 156)):
    pn.rect(-20, y, W + 20, H + 20, fill=col)
    pn.line([(-20, y), (W + 20, y)], INK, 3)

PARCH_BG = None
def parch():
    global PARCH_BG
    if PARCH_BG is None: PARCH_BG = E.get('parch').convert('RGBA')
    return PARCH_BG.copy()

# ---------------- world25 scenes ----------------
def plain_scene(seed=4, dusk=False):
    if dusk: sc = W25.Scene(sky_top=(70, 66, 96), sky_bot=(226, 160, 110))
    else: sc = W25.Scene(sky_top=(146, 176, 206), sky_bot=(238, 224, 190))
    sc.ridge(42000, 5200, (112, 126, 156) if not dusk else (96, 82, 110), seed=3)
    sc.ridge(22000, 2600, (122, 132, 140) if not dusk else (118, 92, 104), seed=5)
    sc.ridge(9000, 650, (160, 148, 104) if not dusk else (150, 110, 90), seed=8)
    sc.ground((200, 176, 116) if not dusk else (170, 128, 92), (188, 164, 104) if not dusk else (156, 116, 84))
    rnd = random.Random(seed)
    for i in range(34):
        X = rnd.choice([-1, 1]) * rnd.uniform(350, 2400); Z = rnd.uniform(2600, 9000)
        sc.card(X, Z, W25.oak(sc, seed=i, size=rnd.uniform(.85, 1.25)))
    for i in range(50):
        X = rnd.uniform(-1600, 1600); Z = rnd.uniform(-400, 3000)
        if abs(X) < 400 and 500 < Z < 1400: continue
        sc.card(X, Z, W25.rock(sc, seed=i, size=rnd.uniform(.35, 1.0)))
    sc.tufts(900, -5000, 5000, 300, 9000, (150, 128, 76) if not dusk else (120, 86, 60), seed=11)
    return sc

class Person:
    """A rig v2 hoplite placed in a world25 scene; attributes can be changed per frame."""
    def __init__(s, sc, X, Z, out, f=-1, **kw):
        s.X, s.Z, s.out, s.f, s.kw = X, Z, out, f, kw
        s.dy = 0.0; s.bare = 0.0; s.store = {}; s.vis = True
        s.sc = sc; sc.card(X, Z, s.draw)
    def draw(s, pn, sx, sy, k):
        if not s.vis: return
        cam = s.sc.cam
        kw = dict(s.kw)
        if kw.get('shield', True) is not False or kw.get('spear_hand') is not None:
            kw.update(world_hooks(cam, s.X, s.Z, s.store))
        HOP(pn, sx, sy + s.dy * k, k, s.f, out=s.out, **kw)
        bare_side(pn, sx, sy + s.dy * k, k, s.bare, s.f)

def move_card(sc, person, X):
    """Cards store X at creation: update the item's X so depth sorting and projection follow."""
    person.X = X
    for it in sc.items:
        if it[0] == 'card' and it[2]['draw'] == person.draw: it[2]['X'] = X

# shot 1 and 15: the Keeper on the Mantinea plain, AS
S1 = plain_scene()
K1 = Person(S1, 0, 900, 'hop_keeper', -1, expr='neutral', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104)
S15 = plain_scene()
K15 = Person(S15, 0, 900, 'hop_keeper', -1, expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104)
N15a = Person(S15, -100, 900, 'hop_a', -1, expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104)
N15b = Person(S15, 100, 900, 'hop_b', -1, expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104)
CAM1 = frame_cam(0, 900, -265, -35, 400, 1300)

def shot_world(sc, cam):
    return sc.render(cam).convert('RGBA')

def s1(t):
    K1.kw['expr'] = 'worried' if t >= w(2, 6) else ('neutral' if t < w(2, 0) else 'thinking')
    K1.kw['look'] = (-0.9, 0.5) if t >= w(2, 3) else (0.6, 0)
    K1.bare = clamp((t - w(2, 6)) / 0.25) * (0.75 + 0.25 * math.sin(t * 9))
    # push in toward his open side on "open"
    u = eio(clamp((t - w(2, 4)) / 0.9))
    cam = frame_cam(lerp(0, -20, u), 900, -265, -35, lerp(400, 300, u), lerp(1300, 1420, u))
    im = shot_world(S1, cam)
    if t >= w(2, 6) - 0.1:      # arrow to the open side
        lay = new_layer(); pn = Pen(lay, cam=False)
        p = pop(t, w(2, 6) - 0.1, 0.35)
        PR.arrow(pn, (150, 760), (lerp(150, 330, p), lerp(760, 820, p)), col=RUST, w=12, head=36)
        flatten(im, lay)
    return im

def s15(t):
    t0 = bs(20); tl = w(20, 1)
    u = eio(clamp((t - t0) / 0.7))
    move_card(S15, N15a, lerp(-420, -100, u)); move_card(S15, N15b, lerp(420, 100, u))
    lit = clamp((t - w(20, 2)) / 0.3)
    for p in (N15a, K15, N15b): p.store.clear()
    back = eio(clamp((t - w(20, 4)) / 0.9))
    cam = frame_cam(0, 900, -265, -35, lerp(400, 470, back), lerp(1300, 1250, back))
    im = shot_world(S15, cam)
    if lit > 0:     # the overlap halves light up
        lay = new_layer(); pn = Pen(lay, cam=False)
        for p in (N15a, K15):
            if 'shield' in p.store:
                cx, cy, r = p.store['shield']
                pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
                pn.poly(pts, fill=RUST + (int(80 * lit),))
        flatten(im, lay)
    return im

# shot 12: low angle, the line breaks
S12 = plain_scene(seed=9)
L12 = [Person(S12, x, 700, o, -1, expr='determined', p=R.pose('brace', torso=8, head=-4), spear_hand=(40, -186),
              spear_ang=math.pi - 0.2, spear_back=130, shield_dx=8) for x, o in ((-100, 'hop_a'), (0, 'hop_b'), (100, 'hop_keeper'))]
def s12(t):
    tb = w(15, 0)
    fall = ei2(clamp((t - tb - 0.15) / 0.45))
    L12[1].dy = fall * 420; L12[1].kw['expr'] = 'terrified' if t > tb else 'determined'
    L12[1].vis = fall < 1
    for p in (L12[0], L12[2]):
        p.kw['expr'] = 'worried' if t > tb + 0.3 else 'determined'
        p.bare = clamp((t - w(16, 5)) / 0.2) * (0.7 + 0.3 * math.sin(t * 10))
    cam = W25.Cam3(0, -70, 700 - 1350, 0, F=3600, horizon=1500)     # low angle: horizon in the lower fifth
    return shot_world(S12, cam)

# shot 13: high angle, Spartan camp at dusk
S13 = plain_scene(seed=13, dusk=True)
SP1 = Person(S13, 90, 900, 'spartan1', -1, expr='worried', shield=False, p=R.pose('idle'))
SP2 = Person(S13, -120, 980, 'spartan2', 1, expr='angry', shield=False, p=R.pose('idle'))
DROP = {}
def drop_draw(pn, sx, sy, k):
    cam = S13.cam
    if 'aspis' in DROP:
        X, Y, Z, pitch, yaw = DROP['aspis']
        M.draw_mesh(pn, cam, M.get('aspis'), (X, Y, Z), M.rot(yaw, pitch, 0))
    if 'pilos' in DROP:
        X, Y, Z, rot_ = DROP['pilos']
        M.draw_mesh(pn, cam, M.get('pilos'), (X, Y, Z), M.rot(*rot_), scale=0.9)
S13.card(60, 860, drop_draw)
def s13(t):
    td = w(17, 8)
    SP2.kw['p'] = R.pose('point') if t >= w(17, 4) else R.pose('idle')
    if t >= w(18, 2): SP2.kw['p'] = R.pose('cross')
    SP1.kw['expr'] = 'embarrassed' if t >= td else 'worried'
    # aspis held low at his side, then dropped: falls, tips flat, one bounce, settles
    u = clamp((t - td) / 0.5)
    if t < td:
        DROP['aspis'] = (150, -70, 860, math.radians(-10), 0.3)
    else:
        y = lerp(-70, -6, ei2(u)) - (12 * math.sin(math.pi * clamp((t - td - 0.5) / 0.25)) if t > td + 0.5 else 0)
        DROP['aspis'] = (lerp(150, 170, u), y, 860, math.radians(lerp(-10, -84, eo3(u))), 0.3)
    th = w(18, 2)
    if t >= th - 0.35:
        v = clamp((t - th + 0.35) / 0.35)
        DROP['pilos'] = (-10, lerp(-260, -40, ei2(v)), 840, (-0.6, -0.6, 1.6))
    cam = W25.Cam3(20, -560, 900 - 2250, 0, F=3600, horizon=260)    # high angle: horizon near the top
    return shot_world(S13, cam)

# ---------------- parchment and painted scenes ----------------
def s2(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    floor(pn, 1240)
    a = ke(t, [(bs(3), -0.5), (bs(3) + 1.0, 0.0)])
    M.draw_mesh(pn, FLAT, M.get('aspis'), (540, 760, 0), M.rot(a, math.radians(-6)), scale=5.0)
    p = clamp((t - w(3, 1)) / 0.6)
    if p > 0:   # dimension arrow across, about 0.85 to 0.9 m
        x0, x1 = 540 - 320, 540 - 320 + 640 * eio(p)
        pn.line([(x0, 1150), (x1, 1150)], INK, 6)
        for xx in (x0, x1): pn.line([(xx, 1125), (xx, 1175)], INK, 6)
        PR.tag(pn, 540, 1080, 'ABOUT 0.9 m', 54, t=pop(t, w(3, 3), 0.35), rot_=-3)
    if t >= w(3, 5):
        PR.tag(pn, 760, 300, 'ABOUT 7 kg', 54, t=pop(t, w(3, 6), 0.35), rot_=4)
    flatten(im, lay); return im

def s3(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    t0 = bs(4)
    yaw = ke(t, [(t0, 0.0), (t0 + 0.9, math.pi)])
    push = eio(clamp((t - bs(5)) / 2.5)) * 0.12
    sc = 5.4 * (1 + push)
    cx, cy = 560, 760
    M.draw_mesh(pn, FLAT, M.get('aspis'), (cx, cy, 0), M.rot(yaw, math.radians(-4)), scale=sc)
    # beat 4: a ghost central handle appears, then is crossed out
    gh = clamp((t - w(4, 5)) / 0.25) * (1 - clamp((t - bs(5) + 0.2) / 0.3))
    if gh > 0:
        for i in range(0, 360, 30):
            a0 = math.radians(i); a1 = math.radians(i + 18)
            pn.line([(cx + 70 * math.cos(a0), cy + 40 * math.sin(a0)), (cx + 70 * math.cos(a1), cy + 40 * math.sin(a1))], INK + (int(255 * gh),), 6)
        x = clamp((t - w(4, 5) - 0.4) / 0.3)
        if x > 0:
            pn.line([(cx - 110, cy - 90), (cx - 110 + 220 * x, cy - 90 + 180 * x)], RUST, 16)
            pn.line([(cx + 110, cy - 90), (cx + 110 - 220 * x, cy - 90 + 180 * x)], RUST, 16)
    # beats 5 and 6: forearm from the right passes under the porpax, hand reaches the antilabe
    if t >= bs(5):
        u = eio(clamp((t - w(5, 1)) / 0.8))
        k = 5.4 * (1 + push)
        hand_x = lerp(1250, cx - 48 * sc + 18, u)      # the antilabe is at object +X, screen left after the turn
        el = (hand_x + 37 * k * 1.25, cy + 6)
        ha = (hand_x, cy)
        O = C.OUT2['hop_keeper']
        C.draw_part(pn, 'sleeve', (el[0] + 38 * k, cy + 4), el, 1, O, scale=k)
        C.draw_part(pn, 'upper_arm', (el[0] + 38 * k, cy + 4), el, 1, O, scale=k)
        C.draw_part(pn, 'forearm', el, ha, 1, O, scale=k * 1.25)
        grip = t >= w(6, 3)
        C.draw_part(pn, 'fist' if grip else 'hand', ha, (ha[0] - 10, ha[1]), 1, O, scale=k)
        M.draw_mesh(pn, FLAT, M.get('porpax'), (cx, cy, 0), M.rot(yaw, math.radians(-4)), scale=sc)
        if t >= w(5, 6):
            PR.callout(pn, cx, cy - 90, cx + 160, 330, 'PORPAX', p=clamp((t - w(5, 6)) / 0.35), sz=50)
        if t >= w(6, 5):
            PR.callout(pn, cx - 48 * sc, cy - 60, cx - 240, 1150, 'ANTILABE', p=clamp((t - w(6, 5)) / 0.35), sz=50)
    flatten(im, lay); return im

def s4(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    floor(pn, 1300)
    k = 3.1; x, y = 560, 1300
    HOP(pn, x, y, k, -1, out='hop_keeper', expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104,
              **flat_hooks(x, y, k))
    p = clamp((t - w(7, 6)) / 0.4)
    if p > 0:      # the body's centre line, dashed
        for i in range(12):
            ya = 1300 - 900 * (i / 12) * p
            pn.line([(x, ya), (x, ya - 32 * p)], RUST, 6)
    flatten(im, lay); return im

def s5(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    floor(pn, 1300)
    k = 1.75; y = 1300; sp = 100 * k
    u = eio(clamp((t - bs(8)) / 0.6))
    xs = [540 - sp - lerp(500, 0, u), 540, 540 + sp + lerp(500, 0, u)]
    outs = ['hop_a', 'hop_keeper', 'hop_b']
    stores = [{}, {}, {}]
    for i in (2, 1, 0):        # right to left: each shield overlaps its right neighbour
        HOP(pn, xs[i], y, k, -1, out=outs[i], expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2,
                  spear_back=104, **flat_hooks(xs[i], y, k, stores[i]))
    lit = [clamp((t - w(8, 4) - 0.15 * j) / 0.25) for j in range(2)]
    for j in range(2):
        if lit[j] > 0 and 'shield' in stores[j]:
            cx, cy, r = stores[j]['shield']
            pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
            pn.poly(pts, fill=RUST + (int(120 * lit[j]),))
    if t >= w(8, 4):
        PR.stamp(pn, 540, 330, 'LIKELY', clamp((t - w(8, 4)) / 0.3), sz=120)
    flatten(im, lay); return im

def s6(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    k = 4.2; y = 1300 + 120 * k
    xk = 720; xa = xk - 100 * k
    st = {}
    look = (-1.0, 0.1) if t >= w(9, 4) else (0.4, 0)
    HOP(pn, xk, y, k, -1, out='hop_keeper', expr='skeptical' if t >= w(9, 4) else 'neutral', look=look,
              spear_hand=None, shield_r=64, **flat_hooks(xk, y, k))
    HOP(pn, xa, y, k, -1, out='hop_a', expr='determined', shield_r=64, **flat_hooks(xa, y, k, st))
    if 'shield' in st and t >= w(9, 8):
        p = pop(t, w(9, 8), 0.4)
        cx, cy, r = st['shield']
        PR.arrow(pn, (cx, cy - r - 60), (lerp(cx, xk - 150, p), lerp(cy - r - 60, cy - 160, p)), col=RUST, w=12, head=36)
    flatten(im, lay); return im

STUDY = None
def study_bg():
    global STUDY
    if STUDY is None:
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.exp(-(((xx - 820) / 520.0) ** 2 + ((yy - 520) / 640.0) ** 2))
        base = np.array((58, 44, 34), float); glow = np.array((214, 160, 96), float)
        img = base + (glow - base) * (g[..., None] * 0.85)
        img[1260:] = img[1260:] * 0.55 + np.array((86, 60, 40)) * 0.45
        STUDY = Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)).convert('RGBA')
    return STUDY.copy()

def s7(t):
    im = study_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    # oil lamp on the shelf, flame flickers
    fl = 1 + 0.08 * math.sin(t * 13) + 0.05 * math.sin(t * 7.3)
    pn.ell(880, 640, 60, 18, fill=(150, 110, 70), outline=INK, width=3)
    pn.poly([(830, 630), (930, 630), (960, 610), (820, 610)], fill=(176, 126, 80), outline=INK, width=3)
    pn.poly([(946, 606), (956, 606 - 46 * fl), (966, 606)], fill=(255, 210, 110), outline=(230, 140, 50), width=2)
    pn.rect(-20, 660, 1100, 690, fill=(96, 66, 42), outline=INK, width=3)
    k = 3.6; x = 470; y = 1300 + 130 * k
    def held(pn_, J):
        M.draw_mesh(pn_, FLAT, M.get('papyrus'), (x, y - 120 * k, -26 * k), M.rot(math.pi + 0.45, math.radians(-8), 0), scale=1.9 * k)
    HOP(pn, x, y, k, -1, out='hop_keeper', expr='thinking', look=(0.3, 0.9), shield=False,
              hands_in={'F': (-58, -122), 'B': (62, -116)}, held_fn=held)
    if t >= w(10, 1):
        PR.tag(pn, 820, 300, 'BOOK 5.71', 54, t=pop(t, w(10, 1), 0.35), rot_=4)
    flatten(im, lay); return im

MAPIMG = None
def lonlat(lon, lat, c_lon=22.40, c_lat=37.40, span=2.8):
    lat_px = span / H; lon_px = lat_px / math.cos(math.radians(c_lat))
    return (lon - c_lon) / lon_px + W / 2, (c_lat - lat) / lat_px + H / 2
def s8(t):
    global MAPIMG
    if MAPIMG is None: MAPIMG = Image.open(os.path.join(HERE, 'maps', 'map_pelo.png')).convert('RGBA')
    mx, my = lonlat(22.39, 37.62)       # Mantinea
    u = eio(clamp((t - bs(11)) / 1.4))
    z = lerp(1.0, 1.7, u) + 0.05 * clamp((t - bs(11) - 1.4) / 1.0)     # keeps drifting in after the move
    tx, ty = lerp(mx, 540, u), lerp(my, 600, u)     # where Mantinea sits on screen: Sparta stays above the captions
    ox0, oy0 = mx - tx / z, my - ty / z             # map point at the screen's top left
    cw, ch = W / z, H / z
    ox, oy = ox0 + cw / 2, oy0 + ch / 2
    box = [2 * ox0, 2 * oy0, 2 * (ox0 + cw), 2 * (oy0 + ch)]
    im = MAPIMG.transform((W, H), Image.EXTENT, tuple(box), Image.BILINEAR)
    lay = new_layer(); pn = Pen(lay, cam=False)
    S_ = lambda x, y: ((x - (ox - cw / 2)) * z, (y - (oy - ch / 2)) * z)
    sx_, sy_ = S_(*lonlat(22.43, 37.075))
    pn.circ(sx_, sy_, 12, fill=INK); pn.text(sx_ + 24, sy_, 'SPARTA', 46, INK, 'Black', anchor='lm')
    p = pop(t, w(11, 1), 0.35)
    px_, py_ = S_(mx, my)
    if p > 0:
        pn.circ(px_, py_, 18 * p, fill=RUST, outline=INK, width=4)
        pn.text(px_, py_ - 60, 'MANTINEA', 58 * min(1, p), INK, 'Black')
    flatten(im, lay); return im

GROUND = (204, 186, 146)
def tokens_bg():
    im = Image.new('RGBA', (W, H), GROUND + (255,))
    return im

def s9(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    s = 1.3; sp = 124 * s; n = 5
    pn.text(960, 330, 'RIGHT', 48, INK, 'Black'); PR.arrow(pn, (870, 390), (1040, 390), col=INK, w=8, head=26)
    for r in range(3):
        for i in range(n):
            j = n - 1 - i                                   # rightmost man moves first
            u = eio(clamp((t - w(12, 2) - j * 0.12) / 0.55))
            x = 540 + (i - (n - 1) / 2) * sp + u * 34 * s
            y = 720 + r * 150 * s
            open_ = (1 - u) if r == 0 else 0.0
            PR.phalanx_token(pn, x, y, s, open_side=open_, spear=(r == 0))
    flatten(im, lay); return im

def s10(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    z = ke(t, [(bs(13), 3.2), (bs(13) + 2.5, 3.6)])
    u = eio(clamp((t - w(13, 1)) / 0.9))
    gap = lerp(150, 100, u)
    xL = 540 - gap * z / 2; xR = 540 + gap * z / 2
    PR.phalanx_token(pn, xL, 860, z, open_side=1.0 - 0.6 * u, spear=False)
    PR.phalanx_token(pn, xR, 860, z, open_side=0.0, spear=False)       # its shield is drawn over the left man's right side
    if t >= w(13, 7):
        PR.callout(pn, xR - 60 * z, 860 - 30 * z, 300, 380, "NEIGHBOR'S SHIELD", p=clamp((t - w(13, 7)) / 0.35), sz=44)
    flatten(im, lay); return im

def s11(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    s = 0.78; sp = 112 * s
    u = eio(clamp((t - w(14, 3)) / 1.6))
    adv = eio(clamp((t - bs(14)) / 2.4))
    for side in (1, -1):        # 1: our army at the bottom facing up; -1: the enemy at the top facing down
        y0 = (900 - adv * 90) if side == 1 else (380 + adv * 90)
        drift = side * u * 120
        for r in range(3):
            for i in range(7):
                x = 540 + (i - 3) * sp + drift
                y = y0 + side * r * 120 * s
                PR.phalanx_token(pn, x, y, s, spear=(r == 0), up=side,
                                 col_body=(160, 40, 36) if side == 1 else (70, 92, 128))
        if u > 0.05:
            ya = y0 - side * 230 * s
            PR.arrow(pn, (540 - 120 * side, ya), (540 - 120 * side + side * 260 * u, ya), col=RUST, w=10, head=30, dash=18)
    flatten(im, lay); return im

def s14(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    k = 8.4; x = 540; y = 820 + 220 * k
    HOP(pn, x, y, k, -1, out='spartan1', expr='neutral', shield=False, look=(0.2, 0))
    p = clamp((t - w(19, 3)) / 0.5)
    if p > 0:
        hc = y - 232 * k
        n = 28; r = 60 * k
        for i in range(int(n * p)):
            a0 = 2 * math.pi * i / n - math.pi / 2; a1 = a0 + math.pi / n
            pn.line([(x + r * math.cos(a0), hc + r * math.sin(a0)), (x + r * math.cos(a1), hc + r * math.sin(a1))], RUST, 12)
    flatten(im, lay); return im

SCENES = dict(s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, s6=s6, s7=s7, s8=s8, s9=s9, s10=s10, s11=s11, s12=s12, s13=s13, s14=s14, s15=s15)

# ---------------- captions ----------------
CAPS = [("A Greek soldier carried", "shield"), ("a shield", "shield"), ("that left his own", "own"), ("right side open.", "open"),
        ("Around three feet across", "three"), ("and about sixteen pounds,", "sixteen"), ("the hoplite shield", "hoplite"),
        ("had no handle", "handle"), ("in the middle.", "middle"), ("His forearm went through", "forearm"),
        ("a bronze band", "band"), ("at the center,", "center"), ("and his hand gripped", "gripped"), ("a cord near the rim.", "cord"),
        ("So the shield sat", "shield"), ("to his left,", "left"), ("and its left half", "half"), ("covered the next man.", "covered"),
        ("His own right side", "right"), ("depended on the man", "depended"), ("to his right.", "right"),
        ("Thucydides described the result", "Thucydides"), ("at Mantinea in 418 BC.", "Mantinea"), ("Each man edged right", "edged"),
        ("to tuck his open side", "tuck"), ("behind his neighbor's shield,", "neighbor's"), ("and both armies", "armies"),
        ("drifted right as they closed.", "drifted"), ("Break the line,", "Break"), ("and every right side", "every"),
        ("was bare.", "bare"), ("That is why Spartans", "Spartans"), ("shamed a man", "shamed"), ("who dropped his shield,", "dropped"),
        ("not his helmet.", "helmet"), ("The helmet protected", "helmet"), ("one man.", "one"), ("The shield protected", "shield"),
        ("the line.", "line")]
ALLW = [wd for p in WORDS for wd in p['words']]
CHUNKS = []
_i = 0
for text, key in CAPS:
    toks = text.split(); ws = ALLW[_i:_i + len(toks)]; _i += len(toks)
    CHUNKS.append(dict(words=[(tk, a['t']) for tk, a in zip(toks, ws)], key=key))
for j, c in enumerate(CHUNKS):
    nxt = CHUNKS[j + 1]['words'][0][1] if j + 1 < len(CHUNKS) else END - 0.6
    c['end'] = min(nxt, c['words'][-1][1] + 1.1)

def captions(im, t):
    c = next((c for c in CHUNKS if c['words'][0][1] <= t < c['end']), None)
    if not c: return
    lay = Image.new('RGBA', im.size); from PIL import ImageDraw
    d = ImageDraw.Draw(lay)
    font = F('Black', 76, disp=True)
    words = [wd for wd, _ in c['words']]
    widths = [d.textlength(wd, font=font) for wd in words]; space = d.textlength(' ', font=font)
    lines = [[]]; lw = 0
    for i, ww in enumerate(widths):
        if lines[-1] and lw + space + ww > 960: lines.append([]); lw = 0
        lines[-1].append(i); lw += (space if len(lines[-1]) > 1 else 0) + ww
    y0 = 1440 - (len(lines) - 1) * 48
    for li, ln in enumerate(lines):
        tw = sum(widths[i] for i in ln) + space * (len(ln) - 1); x = 540 - tw / 2
        for i in ln:
            wd, wt_ = c['words'][i]
            if t >= wt_:
                p = pop(t, wt_, 0.18)
                clean = re.sub(r'[^\w]', '', wd).lower()
                col = AMBER if clean == re.sub(r'[^\w]', '', c['key']).lower() else WHITE
                fsz = max(8, int(76 * (0.7 + 0.3 * p)))
                f2 = F('Black', fsz, disp=True)
                cx = x + widths[i] / 2; cy = y0 + li * 96
                d.text((cx, cy), wd, font=f2, fill=col, anchor='mm', stroke_width=9, stroke_fill=(20, 14, 10))
            x += widths[i] + space
    im.alpha_composite(lay)

CAPDARK = None
def cap_dark(im):
    global CAPDARK
    if CAPDARK is None:
        a = np.zeros((H, W), np.uint8)
        yy = np.arange(H)
        prof = np.clip((yy - 1260) / 140, 0, 1) * np.clip((1700 - yy) / 120, 0, 1) * 110
        a[:] = prof[:, None].astype(np.uint8)
        CAPDARK = Image.merge('RGBA', [Image.new('L', (W, H), 10)] * 3 + [Image.fromarray(a)])
    im.alpha_composite(CAPDARK)

# ---------------- frame composer ----------------
def shot_at(t):
    idx = 0
    for i, (st, _) in enumerate(SHOTS):
        if t >= st: idx = i
    return idx

def render_shot(i, t):
    return SCENES[SHOTS[i][1]](t)

def punch_zoom(im, t):
    s = 1.0
    for t0, amt in PUNCH:
        if t >= t0:
            p = t - t0
            s += amt * eoexpo(clamp(p / 0.1)) * math.exp(-max(0.0, p - 0.1) * 2.2)
    if s <= 1.0005: return im
    a = 1 / s
    return im.transform((W, H), Image.AFFINE, (a, 0, 540 - 540 * a, 0, a, 860 - 860 * a), Image.BILINEAR)

def frame(t):
    CUR['t'] = t
    i = shot_at(t); st = SHOTS[i][0]
    im = render_shot(i, t)
    if st in SLIDES and t < st + 0.35 and i > 0:          # slide push: new scene enters from the right
        u = eio((t - st) / 0.35)
        old = render_shot(i - 1, st - 0.001)
        canvas = Image.new('RGBA', (W, H))
        canvas.paste(old, (int(-W * u), 0)); canvas.paste(im, (int(W * (1 - u)), 0))
        im = canvas
    elif st in DISSOLVES and t < st + 0.3:
        old = render_shot(i - 1, st - 0.001)
        im = Image.blend(old, im, (t - st) / 0.3)
    im = punch_zoom(im, t)
    if t > END - 0.5:                                    # fade to the opening frame so the Short loops
        CUR['t'] = 0.0; first = render_shot(0, 0.0); CUR['t'] = t
        im = Image.blend(im, first, clamp((t - (END - 0.5)) / 0.5))
    cap_dark(im)
    captions(im, t)
    return im.convert('RGB')

if __name__ == '__main__':
    if sys.argv[1] == 'still':
        for a in sys.argv[2:]:
            frame(float(a)).save(f'/tmp/e24s_{float(a):05.2f}.png'); print('still', a, flush=True)
    elif sys.argv[1] == 'frames':
        os.makedirs('/tmp/e24f', exist_ok=True)
        a, b = int(sys.argv[2]), int(sys.argv[3])
        for n in range(a, b):
            frame(n / FPS).save(f'/tmp/e24f/f{n:05d}.png')
            if n % 60 == 0: print('frame', n, flush=True)

"""E024 Greek hoplite aspis: full render. Rig v2 cutout figures, world25 depth scenes, mesh3d props.
Usage: python3 render_e24.py [still t1 t2 ...] | [frames a b]   (frames writes PNGs a..b-1 into /tmp/e24f)"""
import math, os, sys, json, random, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image, ImageFilter
from lib import *
import rig as R, rig_cutout as C, world25 as W25, mesh3d as M, props as PR, env as E, actions as A, emphasis as EM
import lib
PREVIEW = len(sys.argv) > 1 and sys.argv[1] == 'preview'
if PREVIEW: lib.SS = 1                         # gate 4: cheap preview, no supersampling
C.OUT2['spartan1_bare'] = dict(C.OUT2['spartan1'], helmet=None)

CAM.drift = 0; CAM.set(0)
CUR = {'t': 0.0, 'qc': []}
def qc(kind, **kw): CUR['qc'].append(dict(t=kind, **kw))
def qbox(kind, x0, y0, x1, y1): qc(kind, box=[float(min(x0, x1)), float(min(y0, y1)), float(max(x0, x1)), float(max(y0, y1))])
def union(*bs):
    bs = [b for b in bs if b]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)) if bs else None
# record arrow, label and token sizes (gate 3) without changing how they draw
_arrow, _tag, _call, _tok, _text = PR.arrow, PR.tag, PR.callout, PR.phalanx_token, Pen.text
def _arrow_w(pn, a, b, col=INK, w=6, head=22, dash=0, p=1.0):
    qc('arrow', w=w * pn.T[0], len=math.hypot(b[0] - a[0], b[1] - a[1]) * pn.T[0]); return _arrow(pn, a, b, col, w, head, dash, p)
def _quiet(fn):
    def g(*a, **k):
        CUR['mute'] = True
        try: return fn(*a, **k)
        finally: CUR['mute'] = False
    return g
def _tag_w(pn, x, y, text, sz=46, *a, **k): qc('text', px=sz * pn.T[0]); return _quiet(_tag)(pn, x, y, text, sz, *a, **k)
def _call_w(pn, ax, ay, lx, ly, text, p=1.0, sz=34, *a, **k): qc('text', px=sz * pn.T[0]); return _quiet(_call)(pn, ax, ay, lx, ly, text, p, sz, *a, **k)
def _tok_w(pn, x, y, s=1.0, *a, **k): qc('token', px=72 * s * pn.T[0]); return _tok(pn, x, y, s, *a, **k)
def _text_w(self, x, y, t, size, *a, **k):
    if size >= 4 and not CUR.get('mute'): qc('text', px=size * self.T[0])
    return _text(self, x, y, t, size, *a, **k)
PR.arrow, PR.tag, PR.callout, PR.phalanx_token, Pen.text = _arrow_w, _tag_w, _call_w, _tok_w, _text_w
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

BARE_STYLE = os.environ.get('BARE_STYLE', 'ghost')
def ghost_shield(pn, cx, cy, r, a, t=0.0):
    """The shield that is not there: a dashed aspis outline (rim and bowl) over the uncovered side."""
    if a <= 0: return
    rr = r * (0.85 + 0.15 * eoback(min(1.0, a)))
    pn.circ(cx, cy, rr, fill=RUST + (int(45 * min(1, a)),))
    n = 22; ph = t * 0.6
    for i in range(n):
        a0 = 2 * math.pi * (i / n) + ph; a1 = a0 + math.pi / n
        for rad, wd in ((rr, 7), (rr * 0.84, 4)):
            pn.line([(cx + rad * math.cos(a0), cy + rad * math.sin(a0)), (cx + rad * math.cos(a1), cy + rad * math.sin(a1))],
                    RUST + (int(255 * min(1, a)),), wd)
def bare_side(pn, x, y, k, a, f=-1):
    """Mark a front on figure's uncovered right side (screen left when facing left)."""
    if a <= 0: return
    pn.push(x, y, k)
    if BARE_STYLE == 'ghost': EM.ghost_rim(pn, f * 38, -112, 58, a, width=5.0, t=CUR['t'])
    else: EM.burst(pn, f * 44, -118, 0.8, 180 if f == -1 else 0, a, t=CUR['t'])
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
        s.dy = 0.0; s.bare = 0.0; s.store = {}; s.vis = True; s.rot = 0.0; s.extra = None
        s.sc = sc; sc.card(X, Z, s.draw)
    def draw(s, pn, sx, sy, k):
        if not s.vis: return
        cam = s.sc.cam
        kw = dict(s.kw)
        if kw.get('shield', True) is not False or kw.get('spear_hand') is not None:
            kw.update(world_hooks(cam, s.X, s.Z, s.store))
        y = sy + s.dy * k
        s.store['fig'] = (sx - 110 * k, y - 280 * k, sx + 110 * k, y)
        s.store['bare'] = (sx + s.f * 34 * k - 24 * k, y - 166 * k, sx + s.f * 34 * k + 24 * k, y - 58 * k)
        def body(p_):
            HOP(p_, sx, y, k, s.f, out=s.out, **kw)
            bare_side(p_, sx, y, k, s.bare, s.f)
            if s.extra: s.extra(p_, sx, y, k)
        A.draw_rotated(pn, sx, y, s.rot, body)

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
    K1.bare = EM.pop_env(t, w(2, 6) - 0.05, hold=0.75)
    # push in toward his open side on "open"
    u = eio(clamp((t - w(2, 4)) / 0.9))
    cam = frame_cam(lerp(0, -20, u), 900, -265, -35, lerp(400, 300, u), lerp(1300, 1420, u))
    im = shot_world(S1, cam)
    sh = K1.store.get('shield'); sb = (sh[0] - sh[2], sh[1] - sh[2], sh[0] + sh[2], sh[1] + sh[2]) if sh else None
    qbox('subject', *union(sb, K1.store.get('bare'))); qbox('key', *K1.store['bare'])
    return im

def s15(t):
    t0 = bs(20); tl = w(20, 1)
    u = eio(clamp((t - t0) / 0.7))
    move_card(S15, N15a, lerp(-420, -100, u)); move_card(S15, N15b, lerp(420, 100, u))
    lit = clamp((t - w(20, 2)) / 0.3)
    for p in (N15a, K15, N15b): p.store.clear()
    back = eio(clamp((t - w(20, 4)) / 0.9))
    cam = frame_cam(0, 900, -265, -35, lerp(500, 560, back), lerp(1250, 1220, back))
    im = shot_world(S15, cam)
    if 'fig' in N15a.store and 'fig' in N15b.store:
        qbox('subject', N15a.store['fig'][0], N15a.store['fig'][1], N15b.store['fig'][2], N15b.store['fig'][3])
    else: qbox('subject', *K15.store['fig'])
    if 'shield' in K15.store: cx, cy, r = K15.store['shield']; qbox('key', cx - 2 * r, cy - r, cx + 2 * r, cy + r)
    if lit > 0:     # the overlap halves light up
        lay = new_layer(); pn = Pen(lay, cam=False)
        for p in (N15a, K15):
            if 'shield' in p.store:
                cx, cy, r = p.store['shield']
                pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
                pn.poly(pts, fill=RUST + (int(150 * lit),), outline=RUST, width=5)
        flatten(im, lay)
    return im

# shot 12: low angle, the line breaks
S12 = plain_scene(seed=9)
L12 = [Person(S12, x, 700, o, -1, expr='determined', p=R.pose('idle', torso=3), spear_hand=(6, -104),
              spear_ang=-math.pi / 2, spear_back=104) for x, o in ((-100, 'hop_a'), (0, 'hop_b'), (100, 'hop_keeper'))]
ENEMY = {}
def enemy_spear(pn, sx, sy, k):
    if 'tip' not in ENEMY: return
    M.draw_mesh(pn, S12.cam, M.dory_for(110), (ENEMY['tip'] - 260, -150, 640), M.rot(0, 0, 0.08))
S12.card(-300, 640, enemy_spear)
def s12(t):
    tb = w(15, 0)
    th_ = tb + 0.02
    if th_ - 0.3 <= t < th_ + 0.6:      # enemy spear from off frame: fast drive in, short hold, pull back
        if t < th_: ENEMY['tip'] = lerp(-900, -30, ei3((t - th_ + 0.3) / 0.3))
        elif t < th_ + 0.2: ENEMY['tip'] = -30
        else: ENEMY['tip'] = lerp(-30, -900, eio((t - th_ - 0.2) / 0.4))
    else: ENEMY.pop('tip', None)
    Fl = A.fall(t, th_ + 0.05, side=1, dur=0.7)
    m = L12[1]
    base = R.pose('idle', torso=3)
    base.update({k_: v for k_, v in Fl['pose'].items() if k_ in base})
    m.kw['p'] = base; m.rot = Fl['deg']
    m.kw['expr'] = 'terrified' if t > tb else 'determined'
    for p in (L12[0], L12[2]):
        p.kw['expr'] = 'worried' if t > tb + 0.3 else 'determined'
        p.bare = EM.pop_env(t, w(16, 5) - 0.05, hold=0.75)
    cam = W25.Cam3(0, -70, 700 - 1350, 0, F=3600, horizon=1060)     # low eye (knee height): looking up at the line
    im = shot_world(S12, cam)
    if t >= Fl['t_impact'] and t < Fl['t_impact'] + 0.6:             # dust where he lands
        lay = new_layer(); pn = Pen(lay, cam=False)
        x0, y0 = m.store['fig'][0], m.store['fig'][3]
        import fx; fx.particles(pn, 'dust', x0 + 40, y0, t, Fl['t_impact'], scale=1.4, seed=3)
        flatten(im, lay)
    if all('fig' in p.store for p in L12): qbox('subject', L12[0].store['fig'][0], L12[0].store['fig'][1], L12[2].store['fig'][2], L12[2].store['fig'][3])
    qbox('key', m.store['fig'][0] - 100, m.store['fig'][1], m.store['fig'][2], m.store['fig'][3] - 300)
    return im

# shot 13: high angle, Spartan camp at dusk
S13 = plain_scene(seed=13, dusk=True)
SP1 = Person(S13, 90, 900, 'spartan1', -1, expr='worried', shield=False, p=R.pose('idle'))
SP2 = Person(S13, -120, 980, 'spartan2', 1, expr='angry', shield=False, p=R.pose('idle'))
C.OUT2['spartan3'] = dict(C.OUT2['spartan2'], skin=(232, 196, 160), beard=(110, 76, 44), beard_style='full', hair=(110, 76, 44),
                          cloth=(170, 52, 40))
SP3 = Person(S13, -250, 1130, 'spartan3', 1, expr='angry', shield=False, p=R.pose('idle'))
DROP = {}
def drop_draw(pn, sx, sy, k):
    cam = S13.cam
    if 'aspis' in DROP:
        X, Y, Z, pitch, yaw = DROP['aspis']
        M.draw_mesh(pn, cam, M.get('aspis'), (X, Y, Z), M.rot(yaw, pitch, 0))
S13.card(60, 860, drop_draw)
def sp1_helmet(pn, sx, sy, k):
    if 'pilos' in DROP:
        (hx, hy), rot_ = DROP['pilos']
        co, si = math.cos(S13.cam.yaw), math.sin(S13.cam.yaw)
        M.draw_mesh(pn, S13.cam, M.get('pilos'), (SP1.X + hx * co, hy, SP1.Z + hx * si - 12), M.rot(*rot_), scale=0.9)
SP1.extra = sp1_helmet
def s13(t):
    td = w(17, 8)
    SP2.kw['p'] = R.pose('point') if t >= w(17, 4) else R.pose('idle')
    SP3.kw['p'] = R.pose('point', uaF=80) if t >= w(17, 4) + 0.25 else R.pose('idle')
    th = w(18, 1) - 0.35            # the helmet comes off on "his", drops on "helmet"
    Ho = A.helmet_off(t, th, f=-1)
    if t >= th + 0.6:               # nobody cares about a helmet: the pointing stops
        for o in (SP2, SP3): o.kw['p'] = R.pose('idle', uaF=20, faF=10); o.kw['expr'] = 'bored'
    shame = clamp((t - td) / 0.3) * (1 - clamp((t - th) / 0.3))
    SP1.kw['expr'] = ('embarrassed' if shame > 0.5 else 'neutral') if t >= td else 'worried'
    SP1.kw['p'] = R.pose('idle', head=16 * shame, torso=5 * shame)
    SP1.out = 'spartan1' if Ho['on_head'] else 'spartan1_bare'
    SP1.kw['hands_in'] = {'F': Ho['hand']} if Ho['hand'] else None
    if not Ho['on_head']: DROP['pilos'] = (Ho['helmet'], Ho['rot'])
    else: DROP.pop('pilos', None)
    # the aspis: held low at his side, dropped, falls, tips flat, one bounce, settles
    u = clamp((t - td) / 0.5)
    if t < td:
        DROP['aspis'] = (128, -70, 860, math.radians(-10), 0.3)
    else:
        y = lerp(-70, -6, ei2(u)) - (12 * math.sin(math.pi * clamp((t - td - 0.5) / 0.25)) if t > td + 0.5 else 0)
        DROP['aspis'] = (lerp(128, 120, u), y, 860, math.radians(lerp(-10, -84, eo3(u))), 0.3)
    cam = W25.Cam3(-45, -371, 900 - 1500, 0, F=3600, horizon=260)   # high angle: horizon near the top
    im = shot_world(S13, cam)
    if 'fig' in SP1.store and 'fig' in SP2.store: qbox('subject', *union(SP2.store['fig'], SP1.store['fig']))
    qbox('key', SP1.store['fig'][0] - 60, SP1.store['fig'][1], SP1.store['fig'][2] + 80, SP1.store['fig'][3])
    return im

# ---------------- parchment and painted scenes ----------------
def s2(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    floor(pn, 1240)
    a = ke(t, [(bs(3), -0.5), (bs(3) + 1.0, 0.0)])
    M.draw_mesh(pn, FLAT, M.get('aspis'), (540, 760, 0), M.rot(a, math.radians(-6)), scale=5.0)
    qbox('subject', 220, 440, 860, 1080); qbox('key', 220, 440, 860, 1180)
    p = clamp((t - w(3, 1)) / 0.6)
    if p > 0:   # dimension arrow across, about 0.85 to 0.9 m
        x0, x1 = 540 - 320, 540 - 320 + 640 * eio(p)
        pn.line([(x0, 1150), (x1, 1150)], INK, 6)
        for xx in (x0, x1): pn.line([(xx, 1125), (xx, 1175)], INK, 6)
        PR.tag(pn, 540, 1080, 'ABOUT 0.9 m', 58, t=pop(t, w(3, 2), 0.35), rot_=-3)
    if t >= w(3, 6):
        PR.tag(pn, 760, 300, 'ABOUT 7 kg', 58, t=pop(t, w(3, 6), 0.3), rot_=4)
    flatten(im, lay); return im

def s3(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    t0 = bs(4)
    yaw = ke(t, [(t0, 0.0), (t0 + 0.9, math.pi)])
    push = eio(clamp((t - bs(5)) / 2.5)) * 0.12
    sc = 5.4 * (1 + push)
    cx, cy = 560, 760
    M.draw_mesh(pn, FLAT, M.get('aspis'), (cx, cy, 0), M.rot(yaw, math.radians(-4)), scale=sc)
    qbox('subject', cx - 64 * sc, cy - 64 * sc, cx + 64 * sc, cy + 64 * sc); qbox('key', cx - 64 * sc, cy - 64 * sc, cx + 64 * sc, cy + 64 * sc)
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
        u = eo3(clamp((t - w(5, 1) + 0.15) / 0.6))
        k = 5.4 * (1 + push)
        hand_x = lerp(1250, cx - 48 * sc + 18, u)      # the antilabe is at object +X, screen left after the turn
        el = (hand_x + 37 * k * 1.25, cy + 6)
        ha = (hand_x, cy)
        O = C.OUT2['hop_keeper']
        O_ = C.OUT2['hop_keeper']
        pn.line([(1200, cy + 4), (ha[0] + 6 * k, ha[1])], INK, 13 * k + 6)
        pn.line([(1200, cy + 4), (ha[0] + 6 * k, ha[1])], O_['skin'], 13 * k)
        pn.line([(1200, cy + 4 + 3 * k), (ha[0] + 10 * k, ha[1] + 3 * k)], lerpc(O_['skin'], INK, .14), 4 * k)
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
    k = 3.1; x, y = 560, 1300; st = {}
    HOP(pn, x, y, k, -1, out='hop_keeper', expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104,
              **flat_hooks(x, y, k, st))
    qbox('subject', x - 110 * k, y - 280 * k, x + 110 * k, y)
    if 'shield' in st: cx, cy, r = st['shield']; qbox('key', cx - r - 120, cy - r, cx + r, cy + r)
    p = clamp((t - w(7, 6)) / 0.4)
    if p > 0:      # the body's centre line, dashed
        for i in range(12):
            ya = 1300 - 900 * (i / 12) * p
            pn.line([(x, ya), (x, ya - 32 * p)], RUST, 6)
    flatten(im, lay); return im

def s5(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    floor(pn, 1300)
    k = 2.7; y = 1300; sp = 100 * k
    u = eio(clamp((t - bs(8)) / 0.6))
    xs = [540 - sp - lerp(500, 0, u), 540, 540 + sp + lerp(500, 0, u)]
    outs = ['hop_a', 'hop_keeper', 'hop_b']
    stores = [{}, {}, {}]
    for i in (2, 1, 0):        # right to left: each shield overlaps its right neighbour
        HOP(pn, xs[i], y, k, -1, out=outs[i], expr='determined', spear_hand=(6, -104), spear_ang=-math.pi / 2,
                  spear_back=104, **flat_hooks(xs[i], y, k, stores[i]))
    qbox('subject', xs[0] - 110 * k, y - 280 * k, xs[2] + 110 * k, y)
    if all('shield' in st for st in stores[:2]):
        qbox('key', *union(*[(st['shield'][0] - st['shield'][2], st['shield'][1] - st['shield'][2], st['shield'][0] + st['shield'][2],
                               st['shield'][1] + st['shield'][2]) for st in stores[:2]]))
    lit = [clamp((t - w(8, 4) - 0.15 * j) / 0.25) for j in range(2)]
    for j in range(2):
        if lit[j] > 0 and 'shield' in stores[j]:
            cx, cy, r = stores[j]['shield']
            pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
            pn.poly(pts, fill=RUST + (int(170 * lit[j]),), outline=RUST, width=6)
    if t >= w(8, 4):
        PR.stamp(pn, 860, 170, 'LIKELY', clamp((t - w(8, 4)) / 0.3), sz=70)
    flatten(im, lay); return im

def s6(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    k = 4.2; y = 1300 + 30 * k
    xk = 720; xa = xk - 100 * k
    st = {}
    look = (-1.0, 0.1) if t >= w(9, 4) else (0.4, 0)
    HOP(pn, xk, y, k, -1, out='hop_keeper', expr='skeptical' if t >= w(9, 4) else 'neutral', look=look,
              spear_hand=None, shield_r=64, **flat_hooks(xk, y, k))
    HOP(pn, xa, y, k, -1, out='hop_a', expr='determined', shield_r=64, **flat_hooks(xa, y, k, st))
    qbox('subject', xa - 110 * k, y - 280 * k, xk + 110 * k, 1260)
    if 'shield' in st: qbox('key', st['shield'][0] - st['shield'][2], st['shield'][1] - st['shield'][2] - 80, xk, 1250)
    if 'shield' in st and t >= w(9, 4) + 0.1:
        p = pop(t, w(9, 4) + 0.1, 0.4)
        cx, cy, r = st['shield']
        fx_, fy_ = xk - 34 * k, y - 112 * k                      # the Keeper's right flank, behind the neighbour's shield
        a0 = (cx - r * 0.3, cy - r - 150); a1 = (fx_ - 10, fy_ - 30 * k)
        PR.arrow(pn, a0, (lerp(a0[0], a1[0], p), lerp(a0[1], a1[1], p)), col=RUST, w=16, head=44)
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
    k = 3.6; x = 470; y = 1300 + 50 * k
    qbox('subject', x - 130 * k, y - 280 * k, x + 130 * k, y - 120 * k + 50 * 1.9 * k)
    qbox('key', x - 70 * 1.9 * k, 220, 1000, y - 120 * k + 26 * 1.9 * k)
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
    qbox('subject', px_ - 170, py_ - 100, px_ + 170, py_ + 20); qbox('key', px_ - 170, py_ - 100, px_ + 170, py_ + 20)
    flatten(im, lay); return im

GROUND = (204, 186, 146)
TOKBG = None
def tokens_bg():
    global TOKBG
    if TOKBG is None:
        rng = np.random.default_rng(5)
        n = rng.standard_normal((H // 6, W // 6))
        n = np.asarray(Image.fromarray(((n - n.min()) / np.ptp(n) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
        img = np.array(GROUND, float) * (0.92 + 0.14 * n[..., None])
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert('RGBA')
        lay = new_layer(); pn = Pen(lay, cam=False); r = random.Random(2)
        for _ in range(420):
            x, y = r.uniform(0, W), r.uniform(0, H); c = (150, 128, 76) if r.random() < .7 else (176, 156, 112)
            for j in (-1, 0, 1): pn.line([(x + j * 4, y), (x + j * 7, y - 12)], c, 2.2)
        CUR['mute'] = True; flatten(im, lay); CUR['mute'] = False
        TOKBG = im
    return TOKBG.copy()

def s9(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    s = 1.3; sp = 124 * s; n = 5
    pn.text(960, 330, 'RIGHT', 48, INK, 'Black'); PR.arrow(pn, (870, 390), (1040, 390), col=INK, w=8, head=26)
    qbox('subject', 540 - 2.5 * sp - 100, 720 - 160 * s, 540 + 2.5 * sp + 60, 720 + 2 * 150 * s + 40)
    qbox('key', 540 - 2.5 * sp - 100, 720 - 160 * s, 540 + 2.5 * sp + 60, 720 + 40)
    for r in range(3):
        for i in range(n):
            j = n - 1 - i                                   # rightmost man moves first
            u = eo3(clamp((t - w(12, 2) + 0.12 - j * 0.13) / 0.4))
            x = 540 + (i - (n - 1) / 2) * sp + u * 60 * s
            y = 720 + r * 150 * s
            pin = eoback(clamp((t - bs(12) - 0.1) / 0.18))
            open_ = min(pin, 1 - u) if r == 0 else 0.0
            PR.phalanx_token(pn, x, y, s, open_side=open_, spear=(r == 0))
    flatten(im, lay); return im

def s10(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    z = ke(t, [(bs(13), 3.2), (bs(13) + 2.5, 3.6)])
    u = eio(clamp((t - w(13, 1)) / 0.9))
    gap = lerp(150, 100, u)
    xL = 540 - gap * z / 2; xR = 540 + gap * z / 2
    qbox('subject', xL - 110 * z, 860 - 50 * z, xR + 40 * z, 860 + 25 * z); qbox('key', xL - 40 * z, 860 - 50 * z, xR, 860 + 25 * z)
    PR.phalanx_token(pn, xL, 860, z, open_side=min(eoback(clamp((t - bs(13) - 0.1) / 0.18)), 1.0 - u), spear=False)
    PR.phalanx_token(pn, xR, 860, z, open_side=0.0, spear=False)       # its shield is drawn over the left man's right side
    if t >= w(13, 7):
        PR.callout(pn, xR - 60 * z, 860 - 30 * z, 300, 380, "NEIGHBOR'S SHIELD", p=clamp((t - w(13, 7)) / 0.35), sz=44)
    flatten(im, lay); return im

def s11(t):
    im = tokens_bg(); lay = new_layer(); pn = Pen(lay, cam=False)
    s = 1.1; sp = 112 * s
    u = eio(clamp((t - w(14, 3)) / 1.6))
    adv = eio(clamp((t - bs(14)) / 2.4))
    for side in (1, -1):        # 1: our army at the bottom facing up; -1: the enemy at the top facing down
        y0 = (1000 - adv * 90) if side == 1 else (300 + adv * 90)
        drift = side * u * 200
        for r in range(2):
            for i in range(5):
                x = 540 + (i - 2) * sp + drift
                y = y0 + side * r * 120 * s
                PR.phalanx_token(pn, x, y, s, spear=(r == 0), up=side,
                                 col_body=(160, 40, 36) if side == 1 else (70, 92, 128))
        ya = y0 - side * 170 * s
        if u > 0.02:
            PR.arrow(pn, (540 - 130 * side, ya), (540 - 130 * side + side * 280 * max(u, 0.45), ya), col=RUST, w=14, head=40)
    pn.text(540, 160, 'ENEMY', 46, INK, 'Black'); pn.text(540, 1200, 'US', 46, INK, 'Black')
    qbox('subject', 540 - 2.5 * sp - 120, 330 - 200 * s, 540 + 2.5 * sp + 240, 930 + 240 * s)
    qbox('key', 540 - 2.5 * sp - 120, 330 - 200 * s, 540 + 2.5 * sp + 240, 930 + 240 * s)
    flatten(im, lay); return im

def s14(t):
    im = parch(); lay = new_layer(); pn = Pen(lay, cam=False)
    k = 8.4; x = 540; y = 820 + 220 * k
    HOP(pn, x, y, k, -1, out='spartan1', expr='neutral', shield=False, look=(0.2, 0))
    qbox('subject', x - 60 * k, y - 300 * k, x + 60 * k, y - 170 * k); qbox('key', x - 60 * k, y - 300 * k, x + 60 * k, y - 170 * k)
    p = clamp((t - w(19, 3)) / 0.5)
    if p > 0:
        hc = y - 232 * k
        n = 28; r = 60 * k
        for i in range(int(n * p)):
            a0 = 2 * math.pi * i / n - math.pi / 2; a1 = a0 + math.pi / n
            pn.line([(x + r * math.cos(a0), hc + r * math.sin(a0)), (x + r * math.cos(a1), hc + r * math.sin(a1))], RUST, 12)
    flatten(im, lay); return im

# gate 1: shot spec. cue = the word that must visibly change something; MUST SEE and PROVES are the pass rule
SPEC = {
 's1': (lambda: w(2, 6), 'figure', "Keeper's bare right side next to his shield", "a shield that left his own right side open"),
 's2': (lambda: w(3, 1), 'graphic', 'the aspis with a 0.9 m dimension and 7 kg tag', 'about three feet across, about sixteen pounds'),
 's3': (lambda: w(5, 1), 'graphic', 'no centre handle; forearm under the porpax, hand on the antilabe', 'forearm through a band at the centre, hand on a cord near the rim'),
 's4': (lambda: w(7, 6), 'figure', "shield sitting to the left of the Keeper's centre line", 'the shield sat to his left'),
 's5': (lambda: w(8, 4), 'figure', "each shield's left half lit over the next man", 'its left half covered the next man (stamped LIKELY)'),
 's6': (lambda: w(9, 4), 'figure', "neighbour's shield and an arrow to the Keeper's bare side", 'his right side depended on the man to his right'),
 's7': (lambda: w(10, 1), 'figure', 'the Keeper reading a book roll, tag BOOK 5.71', 'Thucydides described it'),
 's8': (lambda: w(11, 1), 'graphic', 'MANTINEA pinned on the real Peloponnese', 'at Mantinea (in 418 BC)'),
 's9': (lambda: w(12, 2), 'graphic', 'front rank stepping right, rightmost man first', 'each man edged right'),
 's10': (lambda: w(13, 1), 'graphic', "open side sliding behind the neighbour's shield", "to tuck his open side behind his neighbour's shield"),
 's11': (lambda: w(14, 3), 'graphic', 'both armies sliding to their own right', 'both armies drifted right as they closed'),
 's12': (lambda: w(15, 0), 'figure', 'the middle man falls and a gap opens; bare sides glow', 'break the line and every right side was bare'),
 's13': (lambda: w(17, 8), 'figure', 'Spartan drops his shield and is pointed at; then takes off his helmet, drops it, and nobody cares', 'shamed for the shield, not the helmet'),
 's14': (lambda: w(19, 3), 'figure', 'a circle around one head under the helmet', 'the helmet protected one man'),
 's15': (lambda: w(20, 1), 'figure', 'three shields locking, overlaps lit', 'the shield protected the line'),
}

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
    CUR['t'] = t; CUR['qc'] = []
    i = shot_at(t); st = SHOTS[i][0]
    im = render_shot(i, t)
    if st in SLIDES and t < st + 0.35 and i > 0:          # slide push: new scene enters from the right
        u = eio((t - st) / 0.35)
        keep = CUR['qc']; old = render_shot(i - 1, st - 0.001); CUR['qc'] = keep
        canvas = Image.new('RGBA', (W, H))
        canvas.paste(old, (int(-W * u), 0)); canvas.paste(im, (int(W * (1 - u)), 0))
        im = canvas
    elif st in DISSOLVES and t < st + 0.3:
        keep = CUR['qc']; old = render_shot(i - 1, st - 0.001); CUR['qc'] = keep
        im = Image.blend(old, im, (t - st) / 0.3)
    im = punch_zoom(im, t)
    if t > END - 0.3:                                    # fade to the opening frame so the Short loops
        keep = CUR['qc']; CUR['t'] = 0.0; first = render_shot(0, 0.0); CUR['t'] = t; CUR['qc'] = keep
        im = Image.blend(im, first, clamp((t - (END - 0.3)) / 0.3))
    cap_dark(im)
    captions(im, t)
    return im.convert('RGB')

def preview(a, b, out='/tmp/e24p'):
    os.makedirs(out, exist_ok=True); recs = {}
    for n in range(a, b):
        im = frame(n / FPS)
        im.resize((540, 960), Image.BILINEAR).save(f'{out}/f{n:05d}.png')
        recs[str(n)] = CUR['qc']
        if n % 120 == 0: print('preview', n, flush=True)
    json.dump(recs, open(f'{out}/recs_{a}.json', 'w'))

def write_qc(out='/tmp/e24p'):
    recs = {}
    for fn in os.listdir(out):
        if fn.startswith('recs_'): recs.update(json.load(open(os.path.join(out, fn))))
    shots = []
    for i, (st, name) in enumerate(SHOTS):
        en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
        cue, kind, must, proves = SPEC[name]
        shots.append(dict(name=name, start=st, end=en, cue=cue(), kind=kind, must_see=must, proves=proves))
    json.dump(dict(fps=FPS, W=W, H=H, shots=shots, frames=recs), open(f'{out}/qc.json', 'w'))

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        preview(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == 'qcjson':
        write_qc()
    elif sys.argv[1] == 'still':
        for a in sys.argv[2:]:
            frame(float(a)).save(f'/tmp/e24s_{float(a):05.2f}.png'); print('still', a, flush=True)
    elif sys.argv[1] == 'frames':
        os.makedirs('/tmp/e24f', exist_ok=True)
        a, b = int(sys.argv[2]), int(sys.argv[3])
        for n in range(a, b):
            frame(n / FPS).save(f'/tmp/e24f/f{n:05d}.png')
            if n % 60 == 0: print('frame', n, flush=True)

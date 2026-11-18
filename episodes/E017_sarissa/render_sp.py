"""E017 Macedonian sarissa phalanx: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
from props import tag, stamp, callout, arrow as arrow_line, sarissa, dory, pelta, aspis, SARISSA_L, DORY_L
import sp
from sp import phalangite, hoplite, dry_ground
import env
import make_map as MM
from fx import smear, speed_lines, focus_lines, impact, particles
from detail import shade, light

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
PH = {}
for wd in WORDS: PH.setdefault(wd['p'], []).append(wd['t'])
def w(p, i): return PH[p][i]
def S(p): return CAPS[p]['s']
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))
KEEPER = EPISODE_OUTFIT

# ---------------- beat table (all from measured word onsets) ----------------
T = dict(
    two0=w(0, 0), walls=w(0, 1), shields0=w(0, 3), slam=w(0, 4), together=w(0, 5),
    s1=S(1), only=w(1, 1), first1=w(1, 3), two1=w(1, 4), ranks1=w(1, 5), reach=w(1, 7), enemy1=w(1, 9),
    s2=S(2), philip=w(2, 0), second=w(2, 2), macedon=w(2, 4), kings=w(2, 7), fixed=w(2, 10), length=w(2, 13),
    s3=S(3), soldiers=w(3, 1), carried=w(3, 2), sarissa=w(3, 4),
    s4=S(4), pike=w(4, 1), n18=w(4, 3), feet4=w(4, 4), long4=w(4, 5),
    s5=S(5), gripped=w(5, 0), both5=w(5, 2), hands5=w(5, 3),
    s6=S(6), greek=w(6, 1), spears6=w(6, 2), facing=w(6, 3), closer=w(6, 6), eight=w(6, 8), feet6=w(6, 9),
    s7=S(7), packed=w(7, 0), three=w(7, 2), apart=w(7, 4),
    s8=S(8), first8=w(8, 1), five=w(8, 2), ranks8=w(8, 3), points8=w(8, 6), sticking=w(8, 7), past=w(8, 9), front8=w(8, 11), man8=w(8, 12),
    s9=S(9), enemy9=w(9, 1), dodged=w(9, 3), point9=w(9, 5), met=w(9, 6), next9=w(9, 8),
    s10=S(10), next10=w(10, 2),
    s11=S(11), behind=w(11, 2), tilted=w(11, 3), pikes11=w(11, 5), up11=w(11, 6), roof=w(11, 9), knock=w(11, 11), arrows11=w(11, 13),
    s12=S(12), spike=w(12, 1), backend=w(12, 4), balanced=w(12, 6), weight=w(12, 8), planted=w(12, 12), ground=w(12, 15),
    s13=S(13), both13=w(13, 0), busy=w(13, 3),
    s14=S(14), hung=w(14, 3), small=w(14, 5), shield14=w(14, 6), two14=w(14, 8), wide=w(14, 10), neck=w(14, 13),
    s15=S(15), front15=w(15, 2),
    s16=S(16), spears16=w(16, 1), rarely=w(16, 2), close=w(16, 4), touch=w(16, 7), shield16=w(16, 9),
    end=VO_END,
)
T['impact0'] = T['slam'] + 0.06
T['plant'] = T['planted'] + 0.22
T['hit1'] = T['met'] + 0.12
T['hit2'] = T['next10'] + 0.02
T['volley'] = T['knock'] - 0.05
FLIGHT = 0.5
CAM.drift = 0.5
CAM.punch = [(T['impact0'], 0.07), (T['length'], 0.05), (T['both5'], 0.05), (T['hit2'], 0.07), (T['roof'], 0.05), (T['spike'] + 0.45, 0.06)]
CAM.shake = [(T['impact0'], 14, 0.4), (T['hit1'], 7, 0.25), (T['hit2'], 11, 0.3), (T['plant'], 8, 0.25)]
FLASH = [(T['impact0'], 0.12, (255, 240, 214), 100)]

GROUND = 1300
FLOOR_C = (206, 190, 158)

def bgp(base, name, par=0.5):
    """Background with parallax; scaled up just enough that a strong camera offset never exposes the frame edge."""
    img = env.get(name)
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def floor(pn, y, col=FLOOR_C, line=True):
    pn.rect(-400, y, 1480, 2800, fill=col)
    if line: pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def walk_pose(t, rate=9.0, amp=22, base='walk', **over):
    s = math.sin(t * rate)
    p = pose(base, thF=amp * s, thB=-amp * s, shF=-max(0, -s) * 30, shB=-max(0, s) * 30,
             uaF=-18 * s, faF=-10 * s + 6, uaB=18 * s, faB=10 * s + 6)
    p.update(over); return p

def antic(t, t0, d=0.35, back=0.18, ad=0.35):
    """Anticipation then action with overshoot and settle (12 principles: anticipation, ease, follow through).
    0 before t0; dips to -back over the first ad of d; then drives to 1 with an overshoot that settles."""
    u = (t - t0) / d
    if u <= 0: return 0.0
    if u < ad: return -back * eio(u / ad)
    v = clamp((u - ad) / (1 - ad))
    return lerp(-back, 1.0, eoback(v, 1.6))

def strike(t, t_hit, wind=0.16, hold=0.18, back=0.4):
    """A thrust: draw back, drive forward to full extension at t_hit, hold, recover (anticipation, timing)."""
    if t < t_hit - wind - 0.12: return 0.0
    if t < t_hit - 0.12: return -back * eio(P(t, t_hit - wind - 0.12, wind))
    if t < t_hit: return lerp(-back, 1.0, ei2(P(t, t_hit - 0.12, 0.12)))
    if t < t_hit + hold: return 1.0
    return lerp(1.0, 0.25, eio(P(t, t_hit + hold, 0.4)))

def step_pose(t, rate=8.0, amp=16, **over):
    """Walk for figures whose arms are on a held object (legs only)."""
    s = math.sin(t * rate)
    p = pose('idle', torso=3, thF=amp * s, thB=-amp * s, shF=-max(0, -s) * 24, shB=-max(0, s) * 24)
    p.update(over); return p

def dim(pn, x0, x1, y, label, p, col=INK, sz=40, below=False, tick=18):
    """Dimension line with end ticks and a label, drawing out from the left over p in 0..1."""
    if p <= 0: return
    e = eo3(p); xe = lerp(x0, x1, e)
    pn.line([(x0, y - tick), (x0, y + tick)], col, 4)
    pn.line([(x0, y), (xe, y)], col, 4)
    if e > 0.98: pn.line([(x1, y - tick), (x1, y + tick)], col, 4)
    if p > 0.5:
        s = eoback(clamp((p - 0.5) / 0.5))
        wv = pn.tw(label, sz, 'Black', True) + 30
        ly = y + (sz * 1.0 if below else -sz * 1.0)
        pn.push((x0 + x1) / 2, ly, s)
        pn.rect(-wv / 2, -sz * 0.72, wv / 2, sz * 0.72, fill=(250, 244, 228), outline=col, width=3.4, r=10)
        pn.text(0, 2, label, sz, col, 'Black', 'mm', True)
        pn.pop()

def ring(pn, x, y, t, t0, col=AMBER, r0=18, r1=70):
    u = t - t0
    if u < 0 or u > 0.6: return
    e = eo3(u / 0.6)
    pn.circ(x, y, lerp(r0, r1, e), outline=col + (int(255 * (1 - e)),), width=6)

def xmark(pn, x, y, p, s=22, col=RUST):
    if p <= 0: return
    e = eoback(p)
    pn.push(x, y, e)
    for a, b in (((-s, -s), (s, s)), ((-s, s), (s, -s))):
        pn.line([a, b], INK, 13); pn.line([a, b], col, 8)
    pn.pop()

def check(pn, x, y, p, s=22, col=(70, 150, 70)):
    if p <= 0: return
    e = eoback(p)
    pn.push(x, y, e)
    pts = [(-s, 0), (-s * .3, s * .7), (s, -s * .8)]
    pn.line(pts, INK, 13); pn.line(pts, col, 8)
    pn.pop()

# ---------------- 1. hook: two walls of shields slam together ----------------
def hook_frame(base, pn, t, settle=False):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    tc = T['impact0']
    u = ei2(P(t, -0.25, tc + 0.25)) if not settle else 1.0
    if t >= tc: u = 1.0
    rec = 0 if t < tc else 10 * math.exp(-(t - tc) * 6) * math.sin((t - tc) * 30)
    k = 1.45
    # back rank first (higher on screen, slightly smaller), then the front rank
    for row in (1, 0):
        kk = k * (1 - row * 0.12); yy = GROUND + 60 - row * 70
        for side in (-1, 1):
            x_end = 540 + side * (150 + row * 110) * (kk / k)
            x0 = 540 + side * 560
            x = lerp(x0, x_end, u) + side * rec
            out = 'hoplite' if side < 0 else 'hoplite2'
            if row == 1: out = 'hoplite2' if side < 0 else 'hoplite'
            moving = t < tc
            p = step_pose(t + row * 0.3 + (side > 0) * 0.5, 11, 18, torso=8) if moving else pose('brace', uaF=60, faF=96)
            ex = 'angry' if t < tc else ('determined' if row else 'pain')
            bob = -abs(math.sin((t + row * 0.3 + (side > 0) * 0.5) * 11)) * 9 * kk if moving else 0
            hoplite(pn, x, yy + bob, kk, -side, t, out, ex, look=(-side * 0.9, 0), p=p, ang=0.12, thrust=0.0)
            if moving and row == 0:
                speed_lines(pn, x - side * 90, yy - 160, -side, 0, t, length=240, n=5, spread=110, seed=3 + side)
    if t >= tc:
        impact(pn, 540, GROUND - 120, t, tc, 1.4, seed=2)
        focus_lines(pn, 540, GROUND - 120, t, tc, 0.28)
        particles(pn, 'dust', 540, GROUND + 50, t, tc, 1.4, seed=4, ground=GROUND + 56)
        particles(pn, 'sparks', 540, GROUND - 150, t, tc, 1.2, seed=5)

def sc_hook(base, pn, t): hook_frame(base, pn, t)
def cam_hook(t, sc, ox, oy):
    return camfocus(lerp(1.05, 1.15, eio(P(t, 0, T['s1']))) * sc, 540, 1120, CX, 1000, ox, oy)

# ---------------- 2. only the first two ranks can reach ----------------
HR = dict(k=1.0, y=1200, x0=560, dx=150, enemy=700)
def sc_ranks(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    floor(pn, HR['y'])
    k = HR['k']
    # the enemy front: a hoplite facing left, with a dashed contact line
    ea = eo3(P(t, T['s1'], 0.4))
    ex = HR['enemy'] + 150 + 300 * (1 - ea)
    hoplite(pn, ex, HR['y'], k, -1, t, 'hoplite2', 'angry', look=(-0.9, 0), ang=0.16)
    la = P(t, T['s1'] + 0.2, 0.3)
    if la > 0:
        for i in range(12):
            y0 = HR['y'] - 420 + i * 36
            pn.line([(HR['enemy'], y0), (HR['enemy'], y0 + 13)], RUST + (int(255 * la),), 5)
        pn.text(HR['enemy'] + 6, HR['y'] - 460, 'ENEMY', 40, RUST + (int(255 * la),), 'Black', 'mm', True)
    tips = []
    for r in range(3, -1, -1):
        x = HR['x0'] - r * HR['dx']
        th = 0.0
        tr = T['first1'] + 0.06 * r
        th = strike(t, tr + 0.28)
        R = hoplite(pn, x, HR['y'], k, 1, t, 'hoplite' if r % 2 == 0 else 'hoplite2', 'determined' if r < 2 else 'worried',
                    look=(0.9, 0), ang=0.2, thrust=th)
        tips.append((r, R['tip']))
        # rank numbers on the floor
        pn.text(x, HR['y'] + 56, str(r + 1), 48, INK + (int(255 * P(t, T['s1'] + 0.1 * r, 0.3)),), 'Black', 'mm', True)
    for r, tp in tips:
        if r < 2: check(pn, tp[0] + 10, tp[1] - 60 - 40 * r, P(t, T['reach'] - 0.05 + 0.1 * r, 0.3), 28)
        else:
            xmark(pn, tp[0] + 6, tp[1] - 60, P(t, T['reach'] + 0.15 + 0.1 * r, 0.3), 26)
    tag(pn, 540, 520, 'RANKS 3 AND 4', 56, pop(t, T['enemy1'] - 0.1), rot_=-3, sub='OUT OF REACH')

# ---------------- 3. Philip II of Macedon (map) ----------------
_MAP = {}
def map_img(name):
    if name not in _MAP: _MAP[name] = Image.open(f'map_{name}.png').convert('RGB')
    return _MAP[name]
LV = {l[0]: l for l in MM.LEVELS}
def geo_xy(lon, lat, lev='ov'):
    _, c_lon, c_lat, span, _ = LV[lev]
    lon_px, lat_px = MM.geo(c_lon, c_lat, span)
    return 540 + (lon - c_lon) / lon_px, 960 - (lat - c_lat) / lat_px
PELLA = (22.52, 40.76); ATHENS = (23.73, 37.98); THEBES = (23.32, 38.32)

def map_view(z, fx_, fy, tx, ty):
    a = 2 / z
    return map_img('ov').transform((W, H), Image.AFFINE, (a, 0, 2 * fx_ - tx * a, 0, a, 2 * fy - ty * a), Image.BILINEAR)

def pin(pn, x, y, t, t0, col=RUST):
    if t < t0: return
    u = t - t0; drop = 1 - spring(u, 1.5, 7)
    py = y - 220 * drop
    rp = eo3(P(u, 0.12, 0.6))
    if 0 < rp < 1: pn.circ(x, y, 24 + 90 * rp, outline=col + (int(255 * (1 - rp)),), width=6)
    pn.poly([(x, py), (x - 22, py - 44), (x + 22, py - 44)], fill=col, outline=INK, width=3)
    pn.circ(x, py - 56, 25, fill=col, outline=INK, width=4); pn.circ(x, py - 56, 9, fill=PARCH)

def label(pn, x, y, txt, sz, a=1.0, col=(60, 48, 34)):
    if a <= 0: return
    pn.text(x, y, txt, sz, col + (int(230 * a),), 'Black', 'mm', True, sp=4)

def sc_map(base, pn, t):
    zp = eio(P(t, T['s2'], T['kings'] - T['s2'] + 0.6))
    z = lerp(1.0, 1.35, zp)
    f0 = geo_xy(23.0, 39.6); f1 = geo_xy(22.8, 40.0)
    fx_, fy = lerp(f0[0], f1[0], zp), lerp(f0[1], f1[1], zp)
    tx, ty = 540, 880
    base.paste(map_view(z, fx_, fy, tx, ty))
    def xy(lon, lat):
        px, py = geo_xy(lon, lat); return tx + (px - fx_) * z, ty + (py - fy) * z
    # Macedon highlighted as a soft region around the plain of Pella (simplified)
    a = P(t, T['macedon'] - 0.1, 0.35)
    if a > 0:
        c = xy(22.3, 40.7)
        pn.ell(c[0], c[1], 210 * a, 120 * a, fill=(190, 40, 36, int(70 * a)), outline=(150, 34, 30, int(200 * a)), width=4)
    label(pn, *xy(22.2, 41.45), 'MACEDON', 58, P(t, T['macedon'], 0.3))
    pin(pn, *xy(*PELLA), t, T['macedon'] + 0.05)
    ga = P(t, T['kings'] - 0.2, 0.3)
    label(pn, *xy(23.0, 38.6), 'GREEK CITY STATES', 40, ga)
    for c_ in (ATHENS, THEBES):
        p_ = xy(*c_)
        if ga > 0: pn.circ(p_[0], p_[1], 11 * ga, fill=INK, outline=PARCH, width=3)
    label(pn, 900, 1330, 'SIMPLIFIED', 26, P(t, T['macedon'] + 0.3, 0.3) * 0.8)
    tag(pn, 540, 1180, 'PHILIP II', 66, pop(t, T['second'] - 0.05), rot_=-3, sub='KING OF MACEDON, 359 TO 336 BC')

# ---------------- 4. fixed that with length ----------------
LN = dict(x=330, y=GROUND + 20, k=1.1)
def sc_length(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    g = eo3(P(t, T['length'] - 0.15, 0.55))
    L = lerp(300, SARISSA_L, g)
    lv = antic(t, T['fixed'] - 0.3, 0.55, 0.12)
    R = phalangite(pn, LN['x'], LN['y'], LN['k'], 1, lerp(0.9, 0.04, lv), t, KEEPER, 'determined' if t < T['length'] else 'smug',
                   look=(1.0, -0.1), back=lerp(110, 240, g), L=L, shield=True)
    if 0 < g < 1:
        tp = R['tip']
        speed_lines(pn, tp[0], tp[1], 1, 0, t, length=280, n=6, spread=40, seed=8)
    if g >= 1:
        ring(pn, *R['tip'], t, T['length'] + 0.4, AMBER, 20, 90)

def cam_length(t, sc, ox, oy):
    m = eio(P(t, T['length'] - 0.15, 0.7))
    return camfocus(lerp(1.75, 1.0, m) * sc, lerp(360, 540, m), lerp(1150, 1000, m), CX, 960, ox, oy)

# ---------------- 5. his soldiers carried the sarissa ----------------
def sc_march(base, pn, t):
    bgp(base, 'plain', 0.4)
    dry_ground(pn, GROUND - 40, t * 0.0)
    u = t - T['s3']
    for i, (out, dx, kk) in enumerate((('phalanx3', -560, 1.15), ('phalanx2', -280, 1.25), (KEEPER, 0, 1.4))):
        x = 560 + dx + 70 * u - 60
        yy = GROUND + 120 - (2 - i) * 30
        phalangite(pn, x, yy, kk, 1, t=t, out=out, expr='determined' if i < 2 else ('happy' if t > T['sarissa'] else 'determined'),
                   look=(1.0, -0.2), p=step_pose(t + i * 0.4, 9, 18), upright=True, L=SARISSA_L)
    # ground scrolls under the marching file for speed reference
    rnd = random.Random(12)
    for i in range(14):
        x = (rnd.uniform(0, 1400) - u * 120) % 1400 - 160
        yy = GROUND + 20 + rnd.uniform(0, 160)
        pn.ell(x, yy, 13, 6, fill=(170, 160, 140), outline=INK, width=2)
    tag(pn, 760, 760, 'SARISSA', 64, pop(t, T['sarissa'] + 0.05), rot_=3, sub='ALSO SPELLED SARISA')

def cam_march(t, sc, ox, oy):
    return camfocus(1.0 * sc, 540, 1000, CX, 1000, ox, oy)

# ---------------- 6. a pike around 18 feet long (scale diagram) ----------------
SC_ = dict(k=1.16, y=1240, fx=150)
def sc_scale(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    floor(pn, SC_['y'])
    k = SC_['k']
    figure(pn, SC_['fx'], SC_['y'], k * 0.98, 1, 'idle', KEEPER, 'surprised' if t > T['n18'] else 'neutral', look=(1.0, -0.4),
           blink=blink_at(t, 1))
    # the sarissa slides in and lies level above the figure's head for comparison
    si = eo3(P(t, T['pike'] - 0.15, 0.5))
    L = SARISSA_L * k * 0.98
    x0 = 60 + (1 - si) * 1100
    yy = 760
    if si > 0:
        sarissa(pn, x0 + 30, yy, 0.0, back=0, L=L - 60, w=7 * k)
    dim(pn, 60, 60 + L - 14, 690, 'ABOUT 18 FT', P(t, T['n18'] - 0.05, 0.5))
    # figure height for scale
    hp = P(t, T['n18'] + 0.25, 0.4)
    if hp > 0:
        top = SC_['y'] - 270 * k * 0.98
        pn.line([(SC_['fx'] + 110, top), (SC_['fx'] + 110, SC_['y'])], INK + (int(255 * hp),), 3)
        for yv in (top, SC_['y']): pn.line([(SC_['fx'] + 96, yv), (SC_['fx'] + 124, yv)], INK + (int(255 * hp),), 3)
        pn.text(SC_['fx'] + 190, (top + SC_['y']) / 2, 'A MAN', 32, INK + (int(255 * hp),), 'Black', 'mm', True)
    tag(pn, 700, 470, 'SOURCES VARY', 54, pop(t, T['long4'] + 0.1), rot_=-3, sub='ABOUT 16 TO 23 FT')

# ---------------- 7. gripped in both hands ----------------
GR = dict(x=420, y=GROUND + 260, k=2.5)
def sc_grip(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    lv = antic(t, T['gripped'] - 0.2, 0.5, 0.1)
    R = phalangite(pn, GR['x'], GR['y'], GR['k'], 1, lerp(1.2, 0.02, lv), t, KEEPER, 'determined', look=(0.9, 0.2), back=240)
    J = R['J']
    for i, s in enumerate(('B', 'F')):
        hx, hy = J['ha' + s]
        X_, Y_ = GR['x'] + hx * GR['k'], GR['y'] + hy * GR['k']
        ring(pn, X_, Y_, t, T['both5'] + 0.08 * i, AMBER, 16, 80)
        if t > T['both5'] + 0.08 * i:
            pn.circ(X_, Y_, 28, outline=AMBER + (int(200 * win(t, T['both5'], T['s6'], 0.1, 0.2)),), width=5)
    if T['gripped'] - 0.1 < t < T['gripped'] + 0.3:
        speed_lines(pn, R['tip'][0], R['tip'][1], 1, 0.6, t, length=200, n=5, spread=60, seed=2)

def cam_grip(t, sc, ox, oy):
    return camfocus(sc * lerp(1.0, 1.06, eio(P(t, T['s5'], 1.2))), 540, 1000, CX, 960, ox, oy)

# ---------------- 8. the Greek spears were closer to eight feet ----------------
CP = dict(kx=190, hx=820, y=GROUND + 60, k=0.95)
def sc_compare(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    k = CP['k']
    a = eo3(P(t, T['s6'] - 0.1, T['facing'] - T['s6'] + 0.1))
    hx = CP['hx'] + 300 * (1 - a)
    th = 0.0
    th = strike(t, T['eight'] + 0.05)
    Rk = phalangite(pn, CP['kx'], CP['y'], k, 1, 0.0, t, KEEPER, 'determined', look=(1.0, 0), back=240)
    Rh = hoplite(pn, hx, CP['y'], k, -1, t, 'hoplite', 'worried' if t > T['closer'] else 'angry', look=(-0.9, 0), ang=0.1,
                 thrust=th, p=pose('brace', uaF=60, faF=96, torso=6 * th) if th != 0 else None)
    if a >= 1 and t < T['facing'] + 0.4:
        particles(pn, 'sparks', Rk['tip'][0], Rk['tip'][1], t, T['facing'], 0.6, seed=6)
    # lengths
    dim(pn, Rk['butt'][0] + 10, Rk['tip'][0], CP['y'] - 380, 'ABOUT 18 FT', P(t, T['spears6'], 0.45))
    if 'tip' in Rh:
        tipx = Rh['tip'][0]
        dim(pn, tipx, tipx + DORY_L * k * 0.98, CP['y'] - 260, '8 FT', P(t, T['eight'], 0.4), col=RUST, sz=44)
        if t > T['eight'] + 0.1:
            # the gap the short spear cannot close
            g = P(t, T['eight'] + 0.15, 0.4)
            body = CP['kx'] + 40 * k
            for i in range(int((tipx - body) / 22)):
                x0 = body + i * 22
                if i % 2 == 0: pn.line([(x0, CP['y'] - 125), (x0 + 11, CP['y'] - 125)], RUST + (int(255 * g),), 5)
    tag(pn, 800, 520, 'DORY', 60, pop(t, T['greek']), rot_=3, sub='THE HOPLITE SPEAR')

# ---------------- 9. packed three feet apart, five ranks of points ----------------
PK = dict(k=0.75, y=1180, x0=600, dx=118 * 0.75)
def file_ranks(pn, t, n=8, lowered=None, raise_ang=1.2, x0=None, y=None, k=None, appear=None, outs=None, expr='determined', keeper_front=True):
    k = k or PK['k']; x0 = PK['x0'] if x0 is None else x0; y = PK['y'] if y is None else y
    dx = 118 * k
    res = []
    for r in range(n - 1, -1, -1):
        if appear is not None:
            a = appear(r)
            if a <= 0: continue
        else: a = 1.0
        ang = lowered(r) if lowered else 0.0
        x = x0 - r * dx
        out = KEEPER if (r == 0 and keeper_front) else (('phalanx2', 'phalanx3')[r % 2])
        yy = y - (1 - eoback(a)) * 60 if a < 1 else y
        R = phalangite(pn, x, yy, k, 1, ang, t, out, expr, look=(1.0, -0.1), back=240, lift=r * 12 if ang < 0.3 else 0,
                       blink=0.0)
        res.append((r, R))
    return res

def sc_pack(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    floor(pn, PK['y'])
    def appear(r): return P(t, T['packed'] + r * 0.09, 0.25)
    def lowered(r):
        if r >= 5: return 1.25
        tl = T['first8'] + r * 0.14
        return lerp(1.25, 0.0, antic(t, tl - 0.06, 0.42, 0.12))
    R = dict(file_ranks(pn, t, 8, lowered, appear=appear))
    dx = PK['dx']
    # three feet apart
    dim(pn, PK['x0'] - dx, PK['x0'], PK['y'] + 60, '3 FT', P(t, T['three'], 0.35), sz=36, below=True, tick=12)
    # rank numbers and tip counters
    for r in range(5):
        if r in R and t > T['first8'] + r * 0.14 + 0.25:
            tp = R[r]['tip']
            a = P(t, T['first8'] + r * 0.14 + 0.25, 0.2)
            cx_, cy_ = tp[0] - 24, tp[1] - 34 - 38 * (r % 2)
            pn.line([(cx_, cy_ + 18), (tp[0] - 24, tp[1] - 4)], INK, 2.4)
            pn.circ(cx_, cy_, 22 * eoback(a), fill=AMBER, outline=INK, width=3)
            pn.text(cx_, cy_ + 1, str(r + 1), 28 * eoback(a), INK, 'Black', 'mm', True)
    # the front man's line
    fa = P(t, T['past'] - 0.1, 0.3)
    if fa > 0:
        fx_ = PK['x0'] + 30
        for i in range(14):
            y0 = PK['y'] - 470 + i * 34
            pn.line([(fx_, y0), (fx_, y0 + 17)], RUST + (int(255 * fa),), 5)
        pn.text(fx_, PK['y'] - 500, 'FRONT MAN', 32, RUST + (int(255 * fa),), 'Black', 'mm', True)
        if 4 in R:
            tp = R[4]['tip']
            pn.line([(fx_, tp[1] + 34), (tp[0] + 20, tp[1] + 34)], RUST + (int(255 * P(t, T['front8'], 0.3)),), 6)
    tag(pn, 540, 420, 'LATER ACCOUNT', 56, pop(t, T['ranks8'] + 0.1), rot_=-3, sub='POLYBIUS, ABOUT 150 BC')
    pn.text(540, PK['y'] + 150, 'SIMPLIFIED', 28, MUTED + (int(200 * P(t, T['s8'], 0.3)),), 'Black', 'mm', True)

def cam_pack(t, sc, ox, oy):
    return camfocus(sc * lerp(1.0, 1.04, eio(P(t, T['s7'], 4.0))), 540, 1000, CX, 980, ox, oy)

# ---------------- 10. an enemy who dodged one point met the next ----------------
EN = dict(x=760, y=GROUND + 100, k=1.5)
PT_Y = [-215, -125, -150, -110, -205]
def sc_dodge(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    k = EN['k']
    tdod = T['dodged']
    events = [T['dodged'] - 0.05, T['hit1'] - 0.15, T['hit2'] - 0.15]
    # enemy: ducks under the first point, then takes the second and third on his shield
    duck = win(t, tdod - 0.1, T['met'] - 0.05, 0.15, 0.2)
    back_ = 0.0
    for te, amt in ((T['hit1'], 40), (T['hit2'], 70)):
        if t > te: back_ += amt * eo3(P(t, te, 0.25))
    p = pose('idle', torso=14 * duck) if t < T['hit1'] else pose('brace', uaF=60, faF=96)
    ex = 'determined'
    if t > tdod - 0.1: ex = 'surprised'
    if t > T['hit1']: ex = 'fear'
    if t > T['hit2']: ex = 'terrified'
    hoplite(pn, EN['x'] + back_, EN['y'], k, -1, t, 'hoplite2', ex, look=(-0.9, 0.0), p=p, ang=0.15, thrust=0.0, legs=1.0 - 0.45 * duck)
    # three sarissa points thrust in from the left edge, one after another
    for i, te in enumerate(events):
        pr = eoback(P(t, te, 0.22), 1.2) if t > te else 0.0
        if pr <= 0: continue
        yy = EN['y'] + PT_Y[i] * k
        reach = [EN['x'] - 40, EN['x'] - 60 + 40 * eo3(P(t, T['hit1'], 0.25)), EN['x'] - 70 + 70 * eo3(P(t, T['hit2'], 0.25))][i]
        if i == 0: reach = EN['x'] + 260      # passes over the ducking head
        tipx = lerp(-200, reach, pr)
        sarissa(pn, tipx - 46 - 760, yy, 0.0, back=0, L=760, w=7 * k)
        if 0 < P(t, te, 0.22) < 1:
            speed_lines(pn, tipx - 60, yy, 1, 0, t, length=220, n=5, spread=26, seed=10 + i)
    for i, te in enumerate((T['hit1'], T['hit2'])):
        if t >= te:
            hx, hy = EN['x'] - 60 + 70 * i, EN['y'] + PT_Y[i + 1] * k
            impact(pn, hx, hy, t, te, 0.8 + 0.3 * i, seed=3 + i)
            particles(pn, 'sparks', hx, hy, t, te, 0.8 + 0.3 * i, seed=7 + i)
    if t >= T['hit2']: focus_lines(pn, EN['x'] - 10, EN['y'] - 140, t, T['hit2'], 0.25)

def cam_dodge(t, sc, ox, oy):
    return camfocus(sc * lerp(1.0, 1.08, eio(P(t, T['s9'], 3.0))), 640, 1050, CX, 960, ox, oy)

# ---------------- 11. the ranks behind made a roof against arrows ----------------
RF = dict(k=0.62, y=1220, x0=880)
def arrow_small(pn, x, y, ang, L=70):
    ca, sa = math.cos(ang), math.sin(ang)
    pn.line([(x, y), (x - ca * L, y - sa * L)], (110, 84, 52), 3.4)
    pn.poly([(x + ca * 9, y + sa * 9), (x - sa * 4, y + ca * 4), (x + sa * 4, y - ca * 4)], fill=IRON, outline=INK, width=1.4)
    pn.line([(x - ca * L, y - sa * L), (x - ca * (L - 14) - sa * 5, y - sa * (L - 14) + ca * 5)], (230, 224, 210), 3)

TIPS = []
def sc_roof(base, pn, t):
    bgp(base, 'plain', 0.4)
    dry_ground(pn, RF['y'] - 30, t)
    k = RF['k']
    tl = T['tilted']
    def lowered(r):
        if r < 5: return 0.0
        return lerp(1.57, 0.8, antic(t, tl - 0.16 + (r - 5) * 0.06, 0.55, 0.15))
    Rs = dict(file_ranks(pn, t, 11, lowered, x0=RF['x0'], y=RF['y'], k=k, keeper_front=False))
    TIPS[:] = [Rs[r]['tip'] for r in range(10, 4, -1) if r in Rs]
    # the roof: a line along the raised points
    ra = P(t, T['roof'] - 0.1, 0.3) * (1 - P(t, T['s12'] - 0.4, 0.3))
    if ra > 0 and len(TIPS) > 1:
        pts = [(x, y - 20) for x, y in TIPS]
        pn.line(pts, AMBER + (int(255 * ra),), 9)
        mx = sum(p[0] for p in pts) / len(pts); my = min(p[1] for p in pts)
        pn.text(mx, my - 70, 'ROOF OF SHAFTS', 40, AMBER + (int(255 * ra),), 'Black', 'mm', True)
    # arrows arc in from the upper right and are knocked down by the shafts
    rnd = random.Random(21)
    for i in range(10):
        t0 = T['volley'] + rnd.uniform(-0.25, 0.25)
        u = (t - t0) / FLIGHT
        if u < 0: continue
        sx, sy = 1200 + rnd.uniform(0, 200), rnd.uniform(160, 360)
        tp = TIPS[i % len(TIPS)] if TIPS else (400, 600)
        ex_, ey_ = tp[0] + rnd.uniform(-60, 20), tp[1] + rnd.uniform(-10, 40)
        if u < 1:
            x = lerp(sx, ex_, u); y = lerp(sy, ey_, u) - 160 * math.sin(math.pi * u) * 0.4
            ang = math.atan2(ey_ - sy, ex_ - sx)
            arrow_small(pn, x, y, ang)
        else:
            v = u - 1
            if v * FLIGHT > 1.4: continue
            x = ex_ + rnd.uniform(-30, 30) * v; y = ey_ + 900 * (v * FLIGHT) ** 2
            if y < RF['y'] - 40:
                arrow_small(pn, x, y, math.pi / 2 + rnd.uniform(-1.2, 1.2) + v * 6)
            if v * FLIGHT < 0.05: pass
            particles(pn, 'chips', ex_, ey_, t, t0 + FLIGHT, 0.5, seed=30 + i)

def cam_roof(t, sc, ox, oy):
    return camfocus(sc * lerp(1.12, 1.02, eio(P(t, T['s11'], 1.0))), 520, 900, CX, 900, ox, oy)

# ---------------- 12. a spike on the back end ----------------
def sc_spike(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    floor(pn, 1240)
    pl = eio(P(t, T['planted'] - 0.25, 0.47))          # swing upright and plant
    k = 1.0
    if pl <= 0:
        # level shaft on a fulcrum at the hands: rocks until the spike end balances it
        bal = eo3(P(t, T['balanced'], 0.6))
        rock = (1 - bal) * 0.06 * math.sin((t - T['s12']) * 5)
        fx_, fy = 330, 860
        ang = -0.10 * (1 - bal) + rock
        R = sarissa(pn, fx_, fy, ang, back=240, L=SARISSA_L, w=8)
        pn.poly([(fx_, fy + 8), (fx_ - 34, fy + 64), (fx_ + 34, fy + 64)], fill=WOOD, outline=INK, width=3.4)
        pn.text(fx_, fy + 100, 'HANDS', 28, MUTED, 'Black', 'mm', True)
        bt = R['butt']
        callout(pn, bt[0] + 18, bt[1], 210, 640, 'BUTT SPIKE', P(t, T['spike'], 0.5), sz=36, hl=True)
        ring(pn, bt[0] + 18, bt[1], t, T['spike'] + 0.1, RUST, 16, 70)
        if T['balanced'] - 0.1 < t:
            arrow_line(pn, (bt[0] + 20, bt[1] + 70), (bt[0] + 20, bt[1] + 150), RUST, 7, 24, p=P(t, T['balanced'], 0.3))
            pn.text(bt[0] + 70, bt[1] + 190, 'COUNTERWEIGHT', 30, RUST + (int(255 * P(t, T['weight'], 0.3)),), 'Black', 'mm', True)
    else:
        # the shaft swings up around the hands and the spike drives into the ground
        a0, a1 = -0.10, -math.pi / 2
        ang = lerp(a0, a1 + math.pi, 0) if False else lerp(0.0, math.pi / 2, pl)
        cx, cy = 540, lerp(860, 1240 - 60 - 0, pl)
        L = SARISSA_L * 0.86
        # point up, butt down
        bx, by = 540, lerp(860, 1262, pl)
        sarissa(pn, bx, by, -math.pi / 2 * pl + (0.0) * (1 - pl), back=0, L=L, w=8)
        if t >= T['plant']:
            impact(pn, 540, 1244, t, T['plant'], 0.7, seed=9)
            particles(pn, 'dust', 540, 1244, t, T['plant'], 1.0, seed=11, ground=1250)
            pn.text(540, 1330, 'PLANTED, POINT UP', 30, MUTED + (int(255 * P(t, T['plant'] + 0.2, 0.3)),), 'Black', 'mm', True)
    if t > T['spike'] + 0.45:
        stamp(pn, 760, 420, 'DISPUTED', t - (T['spike'] + 0.45), 96)

# ---------------- 13. both hands were busy, so a small shield hung from the neck ----------------
NK = dict(x=540, y=GROUND + 110, k=2.6)
def sc_neck(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    k = NK['k']
    th = T['hung']
    drop = 0.0 if t < th else 1.0
    show = t >= th - 0.25
    def mid_extra():
        pass
    ex = 'thinking' if t < T['busy'] else ('confused' if t < th else 'happy')
    if t > T['neck']: ex = 'smug'
    # pelta drops from above on its strap, springs into place
    R = phalangite(pn, NK['x'], NK['y'], k, 1, 0.02, t, KEEPER, ex, look=(-0.2, 0.6) if t < th else (0.8, 0.1), back=240,
                   shield=False)
    J = R['J']
    nk = (NK['x'] + J['neck'][0] * k, NK['y'] + J['neck'][1] * k)
    shF = (NK['x'] + J['shF'][0] * k, NK['y'] + J['shF'][1] * k)
    if show:
        # falls (accelerating), catches on the strap, then swings on an arc around the neck and settles
        u = t - (th - 0.25)
        rx, ry = shF[0] + 4 * k - nk[0], shF[1] + 22 * k - nk[1]
        if u < 0.25:
            yo = -420 * (1 - ei2(u / 0.25)); ang_ = 0.0
        else:
            yo = 0.0; v = u - 0.25; ang_ = 0.5 * math.exp(-v * 4.5) * math.sin(v * 13)
        ca_, sa_ = math.cos(ang_), math.sin(ang_)
        cx, cy = nk[0] + rx * ca_ - ry * sa_, nk[1] + rx * sa_ + ry * ca_ + yo
        # strap
        for sd in (-1, 1):
            pn.line([(nk[0] + sd * 16 * k, nk[1] + 2 * k), (cx + sd * 40 * k * .55, cy - 40 * k * .78)], (96, 64, 38), 4.2 * k)
        pelta(pn, cx, cy, 40 * k)
        # redraw the shaft and hands over the shield (the grip is in front of it)
        hb = J['haB']; hf = J['haF']
        HB = (NK['x'] + hb[0] * k, NK['y'] + hb[1] * k); HF = (NK['x'] + hf[0] * k, NK['y'] + hf[1] * k)
        ang = math.atan2(HF[1] - HB[1], HF[0] - HB[0])
        sarissa(pn, HB[0], HB[1], ang, back=240 * k, L=SARISSA_L * k, w=7 * k)
        for X_, Y_ in (HB, HF): pn.circ(X_, Y_, 5.2 * k, fill=BONE, outline=INK, width=2.4 * k)
        if u > 0.25 and u < 0.5:
            particles(pn, 'sparks', cx, cy - 30 * k, t, th + 0.0, 0.5, seed=13)
        # strap highlight on "neck"
        sa = win(t, T['neck'] - 0.05, T['s15'], 0.15, 0.2)
        if sa > 0:
            for sd in (-1, 1):
                pn.line([(nk[0] + sd * 16 * k, nk[1] + 2 * k), (cx + sd * 40 * k * .55, cy - 40 * k * .78)], AMBER + (int(230 * sa),), 6 * k)
        dp = P(t, T['two14'] - 0.05, 0.4)
        if dp > 0:
            yl = cy + 40 * k + 26; e = eo3(dp)
            pn.line([(cx - 40 * k, yl), (lerp(cx - 40 * k, cx + 40 * k, e), yl)], INK, 4)
            for xv in (cx - 40 * k, cx + 40 * k * (1 if e > .98 else -1)): pn.line([(xv, yl - 14), (xv, yl + 14)], INK, 4)
            callout(pn, cx + 40 * k, yl, 900, yl - 330, 'ABOUT 2 FT', clamp((dp - 0.3) / 0.7), sz=40)
    for i, s in enumerate(('B', 'F')):
        hx, hy = J['ha' + s]
        ring(pn, NK['x'] + hx * k, NK['y'] + hy * k, t, T['both13'] + 0.1 * i, AMBER, 16, 80)
    tag(pn, 790, 420, 'PELTA', 64, pop(t, T['small'] + 0.05), rot_=3, sub='THE PHALANX SHIELD')

def cam_neck(t, sc, ox, oy):
    return camfocus(sc * lerp(1.0, 1.05, eio(P(t, T['s13'], 5.0))), 540, 900, CX, 900, ox, oy)

# ---------------- 14. from the front, enemy spears rarely got close ----------------
FN = dict(k=0.72, y=GROUND + 40, x0=400)
def sc_front(base, pn, t):
    bgp(base, 'plain', 0.35)
    dry_ground(pn, GROUND - 40, t)
    k = FN['k']
    adv = eo3(P(t, T['s15'] - 0.3, 1.2))
    x0 = FN['x0'] - 120 + 120 * adv
    R = dict(file_ranks(pn, t, 5, lambda r: 0.0, x0=x0, y=FN['y'], k=k))
    tip0 = R[0]['tip']
    # the enemy hoplite comes in, thrusts, and stops short of the shields
    a = eo3(P(t, T['s15'], 0.6))
    hx = 980 + 300 * (1 - a)
    th = strike(t, T['spears16'] + 0.05)
    stop = tip0[0] + 30
    hx = max(hx, stop + 40)
    Rh = hoplite(pn, hx, FN['y'] + 10, 0.9, -1, t, 'hoplite', 'fear' if t > T['rarely'] else 'angry', look=(-0.9, 0), ang=0.12,
                 thrust=th, p=pose('brace', uaF=60, faF=96, torso=6 * th) if th != 0 else None)
    if t > T['spears16'] + 0.05:
        particles(pn, 'sparks', tip0[0], tip0[1], t, T['spears16'] + 0.05, 0.6, seed=17)
    if 'tip' in Rh and t > T['close'] - 0.1:
        g = P(t, T['close'] - 0.1, 0.4)
        shield_x = x0 + 30 * k
        dim(pn, shield_x + 20, Rh['tip'][0], FN['y'] - 330, 'TOO FAR', g, col=RUST, sz=40)
    if t > T['touch']:
        xmark(pn, Rh['tip'][0] - 10, Rh['tip'][1] - 50, P(t, T['touch'], 0.3))

def cam_front(t, sc, ox, oy):
    return camfocus(sc * lerp(1.02, 1.1, eio(P(t, T['s16'], 2.5))), 560, 1000, CX, 960, ox, oy)

# (start, fn, cam, transition)
SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['s1'], sc_ranks, None, None),
    (T['s2'], sc_map, None, 'slide'),           # chapter: Macedon's answer
    (T['fixed'], sc_length, cam_length, 'dissolve'),
    (T['s3'], sc_march, cam_march, None),
    (T['s4'], sc_scale, None, None),
    (T['s5'], sc_grip, cam_grip, None),
    (T['s6'], sc_compare, None, None),
    (T['s7'], sc_pack, cam_pack, 'slide'),      # chapter: how the formation worked
    (T['s9'], sc_dodge, cam_dodge, None),
    (T['s11'], sc_roof, cam_roof, 'slide'),     # chapter: the ranks behind
    (T['s12'], sc_spike, None, None),
    (T['s13'], sc_neck, cam_neck, None),
    (T['s15'], sc_front, cam_front, 'slide'),   # chapter: from the front
]
HUD = {}
TINT = [None]
SLIDE = 0.35
DISS = 0.3

def scene_idx(t):
    return max(i for i, s in enumerate(SCENES) if s[0] <= t)

def render_scene(i, t):
    _, fn, cam, _ = SCENES[i]
    CAM.extra = cam; CAM.set(t)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay)
    TINT[0] = None
    fn(base, pn, t)
    if fn in HUD: HUD[fn](Pen(lay, cam=False), t)
    flatten(base, lay)
    return base

# ---------------- captions (word by word) ----------------
STOP = set('a an the of on in to and is it its was had his he them then that this did let at into off out up how here now for like even just according so were could with each'.split())
def build_chunks():
    chunks = []
    for pi, c in enumerate(CAPS):
        ws = [x for x in WORDS if x['p'] == pi]
        n = max(1, math.ceil(len(ws) / 4))
        size = math.ceil(len(ws) / n)
        for j in range(n):
            part = ws[j * size:(j + 1) * size]
            if not part: continue
            kw = None
            for x in part:
                if x['kw']: kw = x['w']
            if kw is None:
                cand = [x['w'] for x in part if x['w'].strip('.,').lower() not in STOP]
                kw = max(cand, key=len) if cand else None
            chunks.append(dict(words=part, kw=kw, s=part[0]['t']))
    for i, ch in enumerate(chunks):
        nxt = chunks[i + 1]['s'] if i + 1 < len(chunks) else VO_END + 0.25
        ch['e'] = min(nxt, ch['words'][-1]['t'] + 1.6)
    return chunks
CHUNKS = build_chunks()

def draw_captions(img, t):
    ch = None
    for c in CHUNKS:
        if c['s'] - 0.02 <= t < c['e']: ch = c
    if ch is None: return
    lay = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    size = 76
    f = F('Black', size * SS, True)
    texts = [x['w'] for x in ch['words']]
    sp_ = f.getlength(' ')
    widths = [f.getlength(x) for x in texts]
    total = sum(widths) + sp_ * (len(texts) - 1)
    k = min(1.0, 960 * SS / total)
    if k < 1:
        f = F('Black', size * SS * k, True); sp_ = f.getlength(' '); widths = [f.getlength(x) for x in texts]; total = sum(widths) + sp_ * (len(texts) - 1)
    x = W * SS / 2 - total / 2; y = 1440 * SS
    for wd, wdt in zip(ch['words'], widths):
        a = P(t, wd['t'] - 0.03, 0.14)
        if a > 0:
            s = eoback(a, 2.2)
            col = AMBER if wd['w'] == ch['kw'] else WHITE
            fs = F('Black', f.size * (0.72 + 0.28 * s), True)
            cx = x + wdt / 2
            d.text((cx, y), wd['w'], font=fs, fill=col + (int(255 * min(1, a * 2)),), anchor='mm',
                   stroke_width=int(8 * SS * 0.9), stroke_fill=(16, 12, 10, int(235 * min(1, a * 2))))
        x += wdt + sp_
    img.alpha_composite(lay.resize((W, H), Image.BOX))

_OPEN = None
def frame(t):
    global _OPEN
    i = scene_idx(t)
    img = render_scene(i, t)
    st, _, _, org = SCENES[i]
    if i > 0 and org == 'slide' and t < st + SLIDE:
        prev = render_scene(i - 1, t)
        u = eio(P(t, st, SLIDE)); dx = int(round(W * u))
        comp = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        comp.paste(prev, (-dx, 0)); comp.paste(img, (W - dx, 0))
        img = comp
    elif i > 0 and org == 'dissolve' and t < st + DISS:
        prev = render_scene(i - 1, t)
        img = Image.blend(prev, img, eio(P(t, st, DISS)))
    for t0, dur, col, st_ in FLASH:
        if t0 <= t < t0 + dur:
            a = 1 - (t - t0) / dur
            img.alpha_composite(Image.new('RGBA', (W, H), col + (int(st_ * a),)))
    if t < VO_END + 0.4: draw_captions(img, t)
    fo = P(t, DUR - 0.7, 0.65)
    if fo > 0:
        if _OPEN is None:
            _OPEN = render_scene(0, 0.0).convert('RGB').convert('RGBA')
        img = Image.blend(img, _OPEN, eio(fo))
    return img.convert('RGB')

# ---------------- SFX cue sheet ----------------
def cues():
    C = [(0.0, 'march', 0.8), (0.05, 'whooshlow', 0.4), (T['walls'], 'march', 0.7), (T['impact0'] - 0.02, 'clank', 1.0),
         (T['impact0'], 'thud', 1.0), (T['impact0'] + 0.01, 'swordclash', 0.6), (T['together'], 'rumble', 0.4),
         (T['s1'] + 0.05, 'paper', 0.4)]
    for r in range(4): C.append((T['first1'] + 0.06 * r, 'swish', 0.4))
    C += [(T['reach'], 'pop', 0.5), (T['reach'] + 0.1, 'pop', 0.5), (T['reach'] + 0.3, 'clack', 0.5), (T['reach'] + 0.4, 'clack', 0.5),
          (T['enemy1'] - 0.1, 'pop', 0.4),
          (T['second'] - 0.05, 'pop', 0.5), (T['macedon'] + 0.1, 'thud', 0.6), (T['macedon'] + 0.3, 'chime', 0.3), (T['kings'] - 0.2, 'paper', 0.4),
          (T['fixed'] - 0.25, 'swish', 0.6), (T['length'] - 0.15, 'whoosh', 0.6), (T['length'] + 0.35, 'clink', 0.6),
          (T['s3'], 'march', 0.8), (T['carried'], 'march', 0.6), (T['sarissa'] + 0.05, 'pop', 0.5),
          (T['pike'] - 0.15, 'slide', 0.6), (T['n18'] - 0.05, 'riser', 0.4), (T['n18'] + 0.3, 'pop', 0.5), (T['long4'] + 0.1, 'pop', 0.4),
          (T['gripped'] - 0.1, 'swish', 0.7), (T['both5'], 'clack', 0.6), (T['both5'] + 0.08, 'clack', 0.6),
          (T['s6'] - 0.1, 'march', 0.6), (T['facing'], 'clink', 0.8), (T['greek'], 'pop', 0.4), (T['spears6'], 'slide', 0.4),
          (T['eight'] - 0.25, 'swish', 0.7), (T['eight'], 'pop', 0.5),
          (T['packed'], 'cloth', 0.4)]
    for r in range(8): C.append((T['packed'] + r * 0.09, 'tick', 0.4))
    C += [(T['three'], 'pop', 0.4)]
    for r in range(5): C += [(T['first8'] + r * 0.14 + 0.2, 'clack', 0.5), (T['first8'] + r * 0.14 + 0.25, 'pop', 0.35)]
    C += [(T['ranks8'] + 0.1, 'paper', 0.4), (T['past'] - 0.1, 'slide', 0.4),
          (T['dodged'] - 0.05, 'swish', 0.8), (T['dodged'] + 0.05, 'whooshlow', 0.5),
          (T['hit1'] - 0.15, 'swish', 0.6), (T['hit1'], 'clank', 0.9), (T['hit1'] + 0.01, 'clink', 0.6),
          (T['hit2'] - 0.15, 'swish', 0.7), (T['hit2'], 'hit', 1.0), (T['hit2'] + 0.01, 'clank', 0.9),
          (T['tilted'] - 0.1, 'creak', 0.6), (T['tilted'] + 0.2, 'swish', 0.5), (T['roof'], 'pop', 0.5),
          (T['volley'], 'volley', 0.8), (T['volley'] + FLIGHT, 'clatter', 0.8), (T['volley'] + FLIGHT + 0.1, 'clatter', 0.5),
          (T['spike'], 'pop', 0.5), (T['spike'] + 0.45, 'stamp', 1.0), (T['balanced'], 'creak', 0.5), (T['weight'], 'thud', 0.4),
          (T['planted'] - 0.25, 'swish', 0.7), (T['plant'], 'thud', 0.9), (T['plant'] + 0.01, 'crack', 0.5),
          (T['both13'], 'clack', 0.5), (T['both13'] + 0.1, 'clack', 0.5), (T['busy'], 'pop', 0.3),
          (T['hung'] - 0.25, 'whooshlow', 0.5), (T['hung'], 'clank', 0.8), (T['small'] + 0.05, 'pop', 0.5),
          (T['two14'] - 0.05, 'slide', 0.4), (T['neck'] - 0.05, 'chime', 0.3),
          (T['s15'] - 0.1, 'march', 0.8), (T['spears16'] - 0.2, 'swish', 0.7), (T['spears16'] + 0.05, 'clink', 0.8),
          (T['close'] - 0.1, 'slide', 0.4), (T['touch'], 'pop', 0.5)]
    starts = {round(st, 3) for st, _, _, org in SCENES[1:]}
    C = [((c[0] - 0.12) if (round(c[0], 3) in starts and c[1] != 'whoosh') else c[0], c[1], c[2]) for c in C]
    for st, _, _, org in SCENES[1:]:
        if org == 'slide': C.append((st, 'whoosh', 0.35))
    C = sorted(set(C))
    json.dump(dict(cues=C, T=T, dur=DUR, nf=NF), open('cues.json', 'w'), indent=1)
    print(len(C), 'cues', 'dur', DUR, 'frames', NF)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'still':
        for a in sys.argv[2:]:
            t = float(a); frame(t).save(f'still_{t:06.2f}.png')
    elif mode == 'seg':
        a, b = int(sys.argv[2]), int(sys.argv[3])
        out = sys.stdout.buffer
        for n in range(a, b):
            out.write(frame(n / FPS).tobytes())
    elif mode == 'cues':
        cues()
    elif mode == 'T':
        for k, v in sorted(T.items(), key=lambda x: x[1]): print(f'{v:6.2f} {k}')

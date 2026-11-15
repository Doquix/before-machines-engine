"""E015 Corvus: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
from props import tag, stamp, callout, arrow
import gf
from gf import water, smoke, flame
import cv
from cv import galley, corvus, pestle, spike_shape, plank_rect, formation, ROM_HULL, ROM_STRIPE, PUN_HULL, PUN_STRIPE, CV_FT, DECK_Y
import env
import make_map as MM
import fx
from fx import smear, speed_lines, focus_lines, impact, particles

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
PH = {}
for wd in WORDS: PH.setdefault(wd['p'], []).append(wd['t'])
def w(p, i): return PH[p][i]
def S(p): return CAPS[p]['s']
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))
KEEPER = 'legion'

# ---------------- beat table (all from measured word onsets) ----------------
T = dict(
    rome0=w(0, 0), could0=w(0, 1), almost0=w(0, 3), any0=w(0, 4), fight0=w(0, 5), land0=w(0, 7),
    sea_s=S(1), sea1=w(1, 1), had1=w(1, 3), no1=w(1, 5), exp1=w(1, 6),
    mapc=S(2), ruled=w(2, 1), water2=w(2, 3),
    ram_s=S(3), crews=w(3, 1), ram=w(3, 3), ship3=w(3, 5), row=w(3, 7), away=w(3, 8),
    swd_s=S(4), single=w(4, 2), roman4=w(4, 3), sword=w(4, 4), got=w(4, 5), close=w(4, 6),
    plan=S(5), in5=w(5, 1), y260=w(5, 2), bc=w(5, 3), romans6=w(6, 1), changed=w(6, 2), rules=w(6, 4),
    parts=S(7), prow=w(7, 2), mounted=w(7, 4), tall=w(7, 6), pole=w(7, 7), pulley=w(7, 10),
    hang=S(8), wooden=w(8, 5), bridge8=w(8, 6),
    dims=S(9), n36=w(9, 1), long9=w(9, 3), and9=w(9, 4), n4=w(9, 5), wide=w(9, 7),
    rail_s=S(10), knee=w(10, 2), rail=w(10, 4), each10=w(10, 6), side=w(10, 7),
    spk=S(11), tip=w(11, 2), iron=w(11, 5), spike11=w(11, 6), shaped=w(11, 7), pestle=w(11, 10),
    appr=S(12), enemy=w(12, 2), near=w(12, 5), crew12=w(12, 7), let=w(12, 8), rope=w(12, 10), go=w(12, 11),
    swing=S(13), bridge13=w(13, 1), swung=w(13, 2), down=w(13, 3),
    punch_s=S(14), spike14=w(14, 1), punched=w(14, 2), into=w(14, 3), deck=w(14, 5),
    lock_s=S(15), two=w(15, 2), ships15=w(15, 3), locked=w(15, 5), together=w(15, 6),
    board=S(16), legionaries=w(16, 2), walked=w(16, 3), across=w(16, 4),
    mapm=S(17), mylae=w(17, 1), sicily=w(17, 3),
    cnt=S(18), lost18=w(18, 1), around=w(18, 2), fifty=w(18, 3), ships18=w(18, 4),
    landb=S(19), sea19=w(19, 1), battle19=w(19, 2), become=w(19, 4), land19=w(19, 6), battle19b=w(19, 7),
    fin=S(20), land20=w(20, 2), rome20=w(20, 3), rarely=w(20, 4), lost20=w(20, 5),
    end=VO_END,
)
T['land_dn'] = T['down'] + 0.1           # bridge lands
T['hit'] = T['punched'] + 0.02           # spike bites
CAM.drift = 0.5
CAM.punch = [(T['ram'], 0.05), (T['rules'], 0.06), (T['spike11'], 0.06), (T['hit'], 0.08), (T['fifty'], 0.07), (T['rarely'], 0.05)]
CAM.shake = [(T['ram'] + 0.05, 14, 0.45), (T['hit'], 16, 0.45)]
FLASH = [(T['hit'], 0.12, (255, 236, 200), 100)]

GRASS = (138, 140, 84); GRASS_L = (160, 156, 96); SAND = (214, 190, 140)
SEA_C = (52, 92, 116); SEA_L = (130, 170, 190)

def bgp(base, name, par=0.5):
    base.paste(bg_cam(env.get(name), par))

def floor(pn, y, col=(206, 190, 158), line=True):
    pn.rect(-400, y, 1480, 2800, fill=col)
    if line: pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def field_ground(pn, y, t=0.0):
    pn.rect(-400, y, 1480, 2800, fill=GRASS)
    pn.line([(-400, y), (1480, y)], lerpc(GRASS, INK, .4), 4, caps=False)
    rnd = random.Random(8)
    for i in range(60):
        x = rnd.uniform(-60, 1140); yy = y + 10 + rnd.uniform(0, 700) ** 1.0
        sw = math.sin(t * 2 + i) * 3
        pn.line([(x, yy), (x + sw - 4, yy - 12 - (yy - y) / 50)], lerpc(GRASS, INK, .25), 3)
        pn.line([(x + 6, yy), (x + 8 + sw, yy - 10 - (yy - y) / 60)], GRASS_L, 3)

def walk_pose(t, rate=9.0, amp=22, base='walk'):
    s = math.sin(t * rate)
    return pose(base, thF=amp * s, thB=-amp * s, shF=-max(0, -s) * 30, shB=-max(0, s) * 30,
                uaF=-18 * s, faF=-10 * s + 6, uaB=18 * s, faB=10 * s + 6)

def camfocus(z, fx, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def sword_held(pn_, J, side='F'):
    cv.short_sword(pn_, J['ha' + side], J['el' + side])

def ring(pn, x, y, r, col, u, width=8):
    if 0 < u < 1: pn.circ(x, y, r, outline=col + (int(255 * (1 - u)),), width=width)

def dust(pn, x, y, t, t0, s=1.0, col=(214, 196, 160)):
    if t < t0: return
    u = P(t, t0, 0.7)
    for i in range(7):
        a = math.pi + i / 6 * math.pi
        pn.circ(x + math.cos(a) * 90 * s * u, y + math.sin(a) * 30 * s * u - 10 * u, (18 + 26 * u) * s, fill=col + (int(170 * (1 - u)),))

def splinters(pn, x, y, t, t0, s=1.0, col=(186, 140, 90)):
    if t < t0: return
    u = t - t0
    if u > 0.8: return
    rnd = random.Random(int(x) + 3)
    for i in range(12):
        a = -math.pi * rnd.uniform(0.05, 0.95); v = rnd.uniform(300, 700) * s
        px = x + math.cos(a) * v * u; py = y + math.sin(a) * v * u + 900 * u * u
        r = rnd.uniform(-3, 3)
        pn.line([(px, py), (px + 16 * s * math.cos(r), py + 16 * s * math.sin(r))], col, 6 * s)

# ---------------- hook and final: the legion on land ----------------
def legion_frame(base, pn, t, t_slam, t_stomp, t_thrust, t_smug, expr_end='smug'):
    bgp(base, 'field', 0.35)
    field_ground(pn, 1110, t)
    st = P(t, t_stomp, 0.12) * (1 - P(t, t_stomp + 0.12, 0.25)) if t_stomp is not None else 0
    formation(pn, 70, 1010, 1185 + 8 * st, 0.5, 7, t, 'legion2', 'determined', seed=1)
    formation(pn, 40, 1040, 1270 + 10 * st, 0.68, 6, t, 'legion3', 'determined', seed=3)
    if t_stomp is not None and t > t_stomp:
        for x in range(90, 1040, 150): dust(pn, x, 1272, t, t_stomp, 0.5, (226, 216, 180))
    if t_stomp is not None:
        for i, x in enumerate(range(90, 1040, 190)):
            particles(pn, 'dust', x, 1272, t, t_stomp, 0.7, seed=i, cone=math.pi * 0.7, ground=1290)
    # the Keeper: shield slam, then a thrust, then the smug look
    def kp(tt):
        sl = P(tt, t_slam - 0.18, 0.18) if t_slam is not None else 1
        p = mix(pose('idle', uaB=40, faB=70), pose('idle', uaB=10, faB=20), ei3(sl)) if t_slam is not None else pose('idle')
        if t_thrust is not None and tt > t_thrust - 0.1:
            q = eoback(P(tt, t_thrust - 0.1, 0.25))
            p = mix(p, pose('slash', uaB=10, faB=20), clamp(q, 0, 1.15))
        return p
    KX, KY, KK = 540, 1400, 2.0
    if t_thrust is not None and t_thrust - 0.12 < t < t_thrust + 0.3:
        sm = []
        for dt in (0.12, 0.09, 0.06, 0.03, 0.0):
            J_ = joints(kp(t - dt), 1, 1.0)
            h, e = J_['haF'], J_['elF']; d_ = math.hypot(h[0] - e[0], h[1] - e[1]) or 1
            tip = (h[0] + (h[0] - e[0]) / d_ * 62, h[1] + (h[1] - e[1]) / d_ * 62)
            sm.append(((KX + h[0] * KK, KY + h[1] * KK), (KX + tip[0] * KK, KY + tip[1] * KK)))
        smear(pn, sm, alpha=210)
        if t < t_thrust + 0.15:
            b_, tp_ = sm[-1]
            speed_lines(pn, tp_[0], tp_[1], tp_[0] - b_[0], tp_[1] - b_[1], t, length=220, n=6, spread=60, seed=4)
    ex = 'determined' if (t_smug is None or t < t_smug) else expr_end
    figure(pn, KX, KY, KK, 1, kp(t), KEEPER, ex, look=(0.2, 0.1), blink=blink_at(t, 0.3), held=lambda pn_, J: sword_held(pn_, J))
    if t_slam is not None:
        particles(pn, 'dust', 430, 1400, t, t_slam, 1.2, seed=9, cone=math.pi * 0.9, ground=1410)
        particles(pn, 'debris', 430, 1395, t, t_slam, 0.7, seed=3, cone=math.pi * 0.6, ground=1410, col=(150, 140, 96))
        impact(pn, 425, 1330, t, t_slam, 0.8, seed=2)

def sc_hook(base, pn, t):
    legion_frame(base, pn, t, 0.12, T['fight0'], T['fight0'] + 0.05, T['land0'])

def cam_hook(t, sc, ox, oy):
    return sc + 0.05 * eio(P(t, 0, 2.6)), ox, oy

def sc_final(base, pn, t):
    legion_frame(base, pn, t, T['lost20'], T['rome20'], None, T['rarely'])

def cam_final(t, sc, ox, oy):
    return sc + 0.05 * eio(P(t, T['fin'], 2.2)), ox, oy

# ---------------- at sea, seasick legionary ----------------
SEA1 = dict(x=360, y=1300, k=1.0)
def sc_sea(base, pn, t):
    bgp(base, 'seaday', 0.0)
    bob = 9 * math.sin(t * 2.6); y = SEA1['y'] + bob
    G = galley(pn, SEA1['x'], y, SEA1['k'], t, 1, oar_rate=0.8)
    bx, by = G['bow']
    sway = 10 * math.sin(t * 2.6 + 0.6)
    ex = 'neutral' if t < T['had1'] else ('worried' if t < T['exp1'] else 'fear')
    p = pose('idle', torso=sway * 0.6, head=-sway * 0.4) if t < T['exp1'] - 0.1 else pose('cower', torso=6 + sway * 0.4)
    figure(pn, bx - 200, by, 0.9, 1, p, KEEPER, ex, look=(0.9, 0.4) if t < T['no1'] else (0.0, -0.2), blink=blink_at(t, 1.1),
           shield=t < T['exp1'] - 0.1)
    water(pn, SEA1['y'] - 4, t, col=SEA_C, light=SEA_L, amp=2.6)
    # spray when the deck pitches on "sea"
    particles(pn, 'splash', 860, SEA1['y'] - 10, t, T['sea1'] - 0.05, 1.3, seed=5, ang=-math.pi * 0.6, cone=math.pi * 0.6)
    particles(pn, 'spray', 880, SEA1['y'] - 20, t, T['sea1'] - 0.02, 1.4, seed=6, ang=-math.pi * 0.55, cone=math.pi * 0.7)

def cam_sea(t, sc, ox, oy):
    m = eio(P(t, T['no1'] - 0.2, 0.45))
    bx = SEA1['x'] + 440 - 200; dy = SEA1['y'] - 70
    hx, hy = bx, dy - 250 * 0.9
    return camfocus(lerp(1.6, 3.0, m) * sc, lerp(bx + 40, hx, m), lerp(dy - 60, hy, m), CX, lerp(1080, 760, m), ox, oy)

# ---------------- maps ----------------
_MAP = {}
def map_img(name):
    if name not in _MAP: _MAP[name] = Image.open(f'map_{name}.png').convert('RGB')
    return _MAP[name]
LV = {l[0]: l for l in MM.LEVELS}
def geo_xy(lon, lat, lev='ov'):
    _, c_lon, c_lat, span, _ = LV[lev]
    lon_px, lat_px = MM.geo(c_lon, c_lat, span)
    return 540 + (lon - c_lon) / lon_px, 960 - (lat - c_lat) / lat_px
ROME = (12.50, 41.90); CARTH = (10.32, 36.85); MYLAE = (15.24, 38.22)

class MapView:
    """View of the overview map: zoom z about overview pixel (fx, fy) placed at screen (tx, ty)."""
    def __init__(s, z, fx, fy, tx, ty): s.z, s.fx, s.fy, s.tx, s.ty = z, fx, fy, tx, ty
    def img_of(s, lev):
        if lev == 'ov':
            z, fx, fy = s.z, s.fx, s.fy
        else:
            # detail map: its own pixels; ratio of spans
            r = LV['ov'][3] / LV[lev][3]
            lon, lat = s.geo(s.fx, s.fy)
            fx, fy = geo_xy(lon, lat, lev); z = s.z / r
        a = 2 / z
        return map_img(lev).transform((W, H), Image.AFFINE, (a, 0, 2 * fx - s.tx * a, 0, a, 2 * fy - s.ty * a), Image.BILINEAR)
    def geo(s, px, py):
        _, c_lon, c_lat, span, _ = LV['ov']; lon_px, lat_px = MM.geo(c_lon, c_lat, span)
        return c_lon + (px - 540) * lon_px, c_lat - (py - 960) * lat_px
    def img(s):
        r = LV['ov'][3] / LV['det'][3]
        m = clamp((s.z - r * 1.0) / (r * 0.12))      # crossfade only where the detail map covers the whole screen
        if m <= 0: return s.img_of('ov')
        if m >= 1: return s.img_of('det')
        return Image.blend(s.img_of('ov'), s.img_of('det'), eio(m))
    def xy(s, lon, lat):
        px, py = geo_xy(lon, lat); return s.tx + (px - s.fx) * s.z, s.ty + (py - s.fy) * s.z

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

def ship_icon(pn, x, y, k, t, a=1.0, hull=PUN_HULL, stripe=PUN_STRIPE, f=-1, sink=0.0):
    """Simple map token: hull, mast and a square sail striped in the side's colour."""
    if a <= 0.02: return
    pn.push(x, y + 60 * sink, a * k / 0.11)
    hc = lerpc(hull, (20, 16, 18), sink); sc_ = lerpc((236, 226, 200), (60, 56, 60), sink); st_ = lerpc(stripe, (30, 26, 30), sink)
    X = lambda v: f * v
    pn.poly([(X(-58), -14), (X(52), -14), (X(66), -24), (X(60), -6), (X(44), 10), (X(-46), 10), (X(-62), -4)], fill=hc, outline=INK, width=3)
    pn.line([(X(-2), -14), (X(-2), -92)], INK, 4)
    pn.rect(X(-34), -86, X(30), -30, fill=sc_, outline=INK, width=3)
    for yy in (-72, -56, -40): pn.line([(X(-34), yy), (X(30), yy)], st_, 5, caps=False)
    pn.pop()

def sc_mapc(base, pn, t):
    z = lerp(1.12, 1.22, eio(P(t, T['mapc'], 1.8)))
    fx, fy = geo_xy(12.6, 39.2)
    mv = MapView(z, fx, fy, 540, 860)
    base.paste(mv.img())
    r = mv.xy(*ROME); c = mv.xy(*CARTH)
    label(pn, *mv.xy(14.6, 38.0), 'SICILY', 34)
    pin(pn, *r, t, T['mapc'] - 0.25, col=(150, 58, 44)); label(pn, r[0] + 120, r[1] - 50, 'ROME', 40)
    pin(pn, *c, t, T['mapc'] + 0.05, col=cv.PUN_STRIPE); label(pn, c[0] + 30, c[1] + 64, 'CARTHAGE', 44, P(t, T['mapc'] + 0.2, 0.3))
    SH = [(11.6, 37.9), (13.0, 37.0), (9.6, 38.9), (14.6, 36.3), (11.0, 40.1), (12.3, 35.6), (13.6, 39.4), (16.2, 37.0)]
    for i, (lon, lat) in enumerate(SH):
        t0 = T['ruled'] + i * 0.09
        if t < t0: continue
        u = eo3(P(t, t0, 0.5))
        x0, y0 = c; x1, y1 = mv.xy(lon, lat)
        ship_icon(pn, lerp(x0, x1, u), lerp(y0, y1, u) + 4 * math.sin(t * 2 + i), 0.11, t, eoback(P(t, t0, 0.3)), f=1 if x1 > x0 else -1)

def sc_mapm(base, pn, t):
    zp = eio(P(t, T['mapm'] + 0.05, 1.0))
    r = LV['ov'][3] / LV['det'][3]
    z = lerp(1.12, r * 1.15, zp)
    f0 = geo_xy(12.6, 39.2); f1 = geo_xy(15.3, 38.1)
    fx, fy = lerp(f0[0], f1[0], zp), lerp(f0[1], f1[1], zp)
    mv = MapView(z, fx, fy, 540, lerp(860, 960, zp))
    base.paste(mv.img())
    m = mv.xy(*MYLAE)
    label(pn, *mv.xy(14.85, 37.85), 'SICILY', 54, P(t, T['sicily'] - 0.1, 0.3))
    for i, (dx, dy) in enumerate(((-150, -170), (-40, -230), (90, -190), (-220, -90), (180, -120))):
        a = P(t, T['mylae'] + 0.15 + i * 0.07, 0.3)
        ship_icon(pn, m[0] + dx, m[1] + dy + 4 * math.sin(t * 2 + i), 0.11, t, eoback(a), hull=ROM_HULL if i % 2 else PUN_HULL,
                  stripe=ROM_STRIPE if i % 2 else PUN_STRIPE, f=1 if i % 2 else -1)
    pin(pn, *m, t, T['mylae'] - 0.1)
    tag(pn, 620, 420, 'MILAZZO', 60, pop(t, T['sicily']), rot_=-3, sub="MYLAE'S MODERN NAME")

# ---------------- ramming ----------------
RAM = dict(y=1300, k=0.95, rx=1020, imp=540)
def ram_x(t):
    x_imp = RAM['imp'] - 548 * RAM['k']
    a = lerp(-900, x_imp, ei2(P(t, T['ram_s'] - 0.3, T['ram'] - T['ram_s'] + 0.3)))
    if t > T['row'] - 0.1: a = lerp(x_imp, -520, eio(P(t, T['row'] - 0.1, 1.2)))
    return a
def sc_ram(base, pn, t):
    bgp(base, 'seaday', 0.35)
    y = RAM['y']
    hit = t > T['ram']
    lurch = 18 * math.exp(-max(0, t - T['ram']) * 4) * math.sin((t - T['ram']) * 18) if hit else 0
    R = galley(pn, RAM['rx'], y + 3 * math.sin(t * 1.9) + lurch, RAM['k'], t, -1, oar_rate=0.6, row=0.5 if hit else 1.0,
               damage=P(t, T['ram'], 0.2))
    bx, by = R['mid']
    for i, dx in enumerate((-120, 0, 120)):
        figure(pn, bx + dx * 1.5 - 60, by, 0.62, -1, 'idle' if not hit else 'cower', 'legion2', 'neutral' if not hit else 'surprised',
               look=(-0.8, 0), blink=blink_at(t, i), shield=not hit)
    cx = ram_x(t)
    rate = 1.6 if t < T['row'] - 0.1 else -2.0
    C = galley(pn, cx, y + 3 * math.sin(t * 2.2), RAM['k'], t, 1, hull=PUN_HULL, stripe=PUN_STRIPE, oar_rate=rate)
    if T['ram_s'] - 0.3 < t < T['ram']:
        speed_lines(pn, cx + 360 * RAM['k'], y - 150, 1, 0, t, length=420, n=9, spread=45, seed=11)
        particles(pn, 'spray', cx + 548 * RAM['k'] - 20, y - 4, t, t - (t * 7 % 1) / 7, 1.1, seed=int(t * 7), ang=-math.pi * 0.75, cone=math.pi * 0.4)
    water(pn, y - 2, t, col=SEA_C, light=SEA_L, x0=-900, x1=2200)
    if hit and t < T['ram'] + 1.2:
        splinters(pn, RAM['imp'], y - 30, t, T['ram'], 1.2)
        particles(pn, 'chips', RAM['imp'], y - 40, t, T['ram'], 1.4, seed=12, ang=-math.pi * 0.6, cone=math.pi * 0.9)
        particles(pn, 'splash', RAM['imp'] + 20, y, t, T['ram'] + 0.03, 1.6, seed=13, cone=math.pi * 0.7)
        focus_lines(pn, RAM['imp'], y - 30, t, T['ram'], 0.22)
        impact(pn, RAM['imp'], y - 30, t, T['ram'], 1.3, seed=14)
    # spray from the backing oars, and the ship pulling away
    if t > T['row'] - 0.1:
        for i in range(4):
            t0 = T['row'] - 0.1 + i * 0.28
            particles(pn, 'spray', cx + 160 - i * 110, y + 4, t, t0, 1.0, seed=20 + i, ang=-math.pi * 0.6, cone=math.pi * 0.6)
        if t < T['row'] + 0.9:
            speed_lines(pn, cx + 300, y - 60, -1, 0, t, length=300, n=7, spread=60, seed=15)

def cam_ram(t, sc, ox, oy):
    return camfocus(1.2 * sc, CX, 1180, CX, 1060, ox, oy)

# ---------------- the sword that never reaches ----------------
def enemy_x(t): return lerp(480, 860, eio(P(t, T['swd_s'] - 0.2, T['close'] - T['swd_s'] + 0.6)))
def sc_sword(base, pn, t):
    bgp(base, 'seaday', 0.35)
    ex_ = enemy_x(t)
    galley(pn, ex_ + 420, 1135 + 3 * math.sin(t * 2.1), 0.72, t, -1, hull=PUN_HULL, stripe=PUN_STRIPE, oar_rate=-1.8)
    water(pn, 1132, t, col=SEA_C, light=SEA_L, amp=0.8)
    # our own deck in the foreground so the figure stands on something
    pn.rect(-80, 1200, 1160, 1236, fill=(126, 88, 54), outline=INK, width=4)
    for i in range(14): pn.line([(-60 + i * 90, 1236), (-60 + i * 90, 1330)], (98, 68, 40), 8)
    pn.rect(-80, 1320, 1160, 2400, fill=(146, 104, 64), outline=INK, width=4)
    for i in range(9): pn.line([(-80, 1360 + i * 64), (1160, 1360 + i * 64)], (118, 84, 50), 4, caps=False)
    def sp(tt):
        sw_ = P(tt, T['sword'] - 0.12, 0.22)
        p_ = mix('idle', pose('slash', uaF=150, faF=160), eo3(P(tt, T['single'] - 0.1, 0.3)))
        if sw_ > 0: p_ = mix(p_, pose('slash', uaF=96, faF=90, torso=16), eoback(sw_))
        if tt > T['got'] - 0.1: p_ = mix(p_, pose('reach', uaF=92, faF=92, torso=14), P(tt, T['got'] - 0.1, 0.3))
        return p_
    KX, KY, KK = 330, 1330, 1.7
    for t_sw in (T['sword'] - 0.12, T['got'] - 0.1):
        if t_sw < t < t_sw + 0.32:
            sm = []
            for dt in (0.15, 0.11, 0.08, 0.05, 0.025, 0.0):
                J_ = joints(sp(t - dt), 1, 1.0)
                h, e = J_['haF'], J_['elF']; d_ = math.hypot(h[0] - e[0], h[1] - e[1]) or 1
                tip = (h[0] + (h[0] - e[0]) / d_ * 62, h[1] + (h[1] - e[1]) / d_ * 62)
                sm.append(((KX + h[0] * KK, KY + h[1] * KK), (KX + tip[0] * KK, KY + tip[1] * KK)))
            smear(pn, sm, alpha=220)
    ex = 'determined' if t < T['sword'] else ('angry' if t < T['close'] else 'confused')
    J = figure(pn, KX, KY, KK, 1, sp(t), KEEPER, ex, look=(1.0, -0.1), blink=blink_at(t, 2), held=lambda pn_, J: sword_held(pn_, J))
    if T['sword'] < t < T['sword'] + 0.4:
        h = J['haF']; tipw = (KX + (h[0] + 60) * KK, KY + h[1] * KK)
        impact(pn, tipw[0] + 40, tipw[1], t, T['sword'] + 0.08, 0.45, col=(255, 255, 255), seed=31, lines=True)
    # the gap: sword tip to the enemy bow, growing
    a = P(t, T['roman4'] - 0.1, 0.3)
    if a > 0:
        tipx = 330 + 1.7 * (J['haF'][0] + 58); yb = 1330 + 1.7 * J['haF'][1]
        x1 = ex_ + 420 - 548 * 0.72
        x1 = lerp(tipx, x1, eo3(a))
        pn.line([(tipx, yb), (x1, yb)], RUST, 7)
        for xx in (tipx, x1): pn.line([(xx, yb - 18), (xx, yb + 18)], RUST, 7)

# ---------------- 260 BC: the shipyard ----------------
YARD = dict(x=120, y=1200, k=1.1)
def sc_plan(base, pn, t):
    bgp(base, 'beach', 0.0)
    floor(pn, 1170, SAND)
    rnd = random.Random(2)
    for i in range(30):
        pn.ell(rnd.uniform(-40, 1120), 1190 + rnd.uniform(0, 700), 16, 5, fill=(196, 170, 120))
    # galley on the beach, propped on timbers so it touches the sand
    for x_ in (-260, 0, 260, 520):
        pn.rect(x_ - 30, 1150, x_ + 30, 1176, fill=WOOD_D, outline=INK, width=3)
    pole = eoback(P(t, T['changed'] - 0.05, 0.45)) if t > T['changed'] - 0.05 else 0
    br = eoback(P(t, T['rules'] - 0.15, 0.35)) if t > T['rules'] - 0.15 else 0
    G = galley(pn, YARD['x'], YARD['y'] - 60, YARD['k'], t, 1, oars=False,
               corvus_ang=72 if br > 0 else (72 if pole > 0 else None),
               corvus_kw=dict(pole=pole, pulley=clamp(pole), bridge=clamp(br, 0, 1.08) if br > 0 else 0.0, rope=br, inner=br > 0.5))
    # carpenter hammering at the hull
    hammering = t < T['romans6'] or t > T['rules'] + 0.3
    ham = (math.sin(t * 14) > 0) if hammering else False
    cx_ = 800
    figure(pn, cx_, 1260, 1.0, -1, pose('reach', uaF=120 if ham else 80, faF=150 if ham else 100), 'rower',
           'happy' if t > T['rules'] else 'thinking', look=(0.8, -0.6), blink=blink_at(t, 4),
           held=lambda pn_, J: (plank_rect(pn_, J['haF'], (J['haF'][0] - 6, J['haF'][1] - 34), 6, WOOD),
                                pn_.rect(J['haF'][0] - 18, J['haF'][1] - 44, J['haF'][0] + 10, J['haF'][1] - 30, fill=IRON, outline=INK, width=2.4)))
    # chips fly from each hammer stroke
    if hammering:
        k0 = math.floor(t * 14 / (2 * math.pi))
        for kk in (k0 - 1, k0):
            th = (2 * math.pi * kk) / 14
            if (th < T['romans6'] or th > T['rules'] + 0.3) and th > T['plan']:
                particles(pn, 'chips', cx_ - 80, 1100, t, th, 0.55, seed=kk % 9, ang=-math.pi * 0.8, cone=math.pi * 0.5, ground=1180)
    if br > 0 and t < T['rules'] + 0.3:
        cv_ = G.get('cv')
        if cv_:
            piv = cv_['piv']; Lb = 24 * CV_FT * YARD['k']; a72 = math.radians(72)
            sm = []
            for dt in (0.12, 0.08, 0.04, 0.0):
                bb = clamp(eoback(P(t - dt, T['rules'] - 0.15, 0.35)) if t - dt > T['rules'] - 0.15 else 0, 0, 1.08)
                sm.append((piv, (piv[0] + math.cos(a72) * Lb * bb, piv[1] - math.sin(a72) * Lb * bb)))
            smear(pn, sm, alpha=170)
    if pole > 0 and G.get('cv'):
        impact(pn, *G['cv']['top'], t, T['changed'] + 0.35, 0.45, seed=41, lines=True)
        impact(pn, *G['cv']['piv'], t, T['rules'] + 0.15, 0.6, seed=42)
        particles(pn, 'sparks', *G['cv']['piv'], t, T['rules'] + 0.15, 0.8, seed=43)
    # the Keeper walks in and points at the prow
    u = t - T['plan']
    x = lerp(-160, 190, eo3(clamp(u / 1.0)))
    p = walk_pose(t) if u < 1.0 else (pose('point', uaF=120, faF=128) if t > T['bc'] - 0.1 else pose('idle'))
    figure(pn, x, 1350, 1.3, 1, p, KEEPER, 'smug' if t > T['rules'] else ('thinking' if t > T['changed'] else 'neutral'),
           look=(0.9, -0.7), blink=blink_at(t, 0.5))

def hud_plan(pn, t):
    tag(pn, 540, 330, 'FIRST PUNIC WAR', 66, pop(t, T['y260']), rot_=-3, sub='ROME VS CARTHAGE')

def cam_plan(t, sc, ox, oy):
    m = eio(P(t, T['changed'] - 0.2, 1.0))
    px = YARD['x'] + 440 * YARD['k']; py = YARD['y'] - 60 - 70 * YARD['k'] - 150
    return camfocus(lerp(1.0, 1.45, m) * sc, lerp(CX, px - 120, m), lerp(CY, py + 40, m), CX, CY, ox, oy)

# ---------------- how it worked: the parts ----------------
PRT = dict(x=-330, y=1340, k=1.55)
def sc_parts(base, pn, t):
    bgp(base, 'parch', 0.0)
    pole = eoback(P(t, T['tall'] - 0.1, 0.4)) if t > T['tall'] - 0.1 else 0
    pul = eoback(P(t, T['pulley'] - 0.05, 0.3)) if t > T['pulley'] - 0.05 else 0
    br = eoback(P(t, T['hang'] - 0.05, 0.45)) if t > T['hang'] - 0.05 else 0
    ang = lerp(150, 72, eo3(P(t, T['hang'] - 0.05, 0.7)))
    hl = {}
    if T['prow'] - 0.1 < t < T['prow'] + 0.8: hl = {}
    G = galley(pn, PRT['x'], PRT['y'], PRT['k'], t, 1, oars=False, corvus_ang=ang if pole > 0 else None,
               corvus_kw=dict(pole=pole, pulley=clamp(pul), bridge=clamp(br, 0, 1.06), rope=clamp(br), inner=br > 0.3,
                              hl={'bridge': 0.6 * win(t, T['wooden'] - 0.05, T['wooden'] + 0.9)}))
    if G.get('cv') and T['hang'] - 0.05 < t < T['hang'] + 0.8:
        piv = G['cv']['piv']; Lb = 24 * CV_FT * PRT['k']
        sm = []
        for dt in (0.12, 0.08, 0.04, 0.0):
            a_ = math.radians(lerp(150, 72, eo3(P(t - dt, T['hang'] - 0.05, 0.7))))
            bb = clamp(eoback(P(t - dt, T['hang'] - 0.05, 0.45)) if t - dt > T['hang'] - 0.05 else 0, 0, 1.06)
            sm.append((piv, (piv[0] + math.cos(a_) * Lb * bb, piv[1] - math.sin(a_) * Lb * bb)))
        smear(pn, sm, alpha=160)
    water(pn, PRT['y'] - 6, t, col=(120, 150, 160), light=(190, 210, 214), amp=0.6)
    bx, by = G['bow']
    if G.get('cv'):
        impact(pn, *G['cv']['top'], t, T['pulley'] + 0.1, 0.5, seed=51)
    if t > T['prow'] - 0.1:
        u = P(t, T['prow'] - 0.1, 0.6)
        ring(pn, bx + 100, by + 10, 60 + 160 * u, AMBER, u, 10)
    if pole > 0.5:
        cvp = G['cv']
        fade = 1 - P(t, T['hang'] - 0.1, 0.25)
        callout(pn, cvp['base'][0] - 8, (cvp['base'][1] + cvp['top'][1]) / 2, 150, 900, 'POLE', P(t, T['pole'], 0.4) * fade, hl=True)
        if pul > 0.3:
            callout(pn, cvp['top'][0] - 20, cvp['top'][1], 190, 640, 'PULLEY', P(t, T['pulley'] + 0.05, 0.4) * fade, hl=True)
    # the Keeper on deck for scale
    figure(pn, bx - 190, by, 0.7, 1, 'point' if t > T['bridge8'] else 'idle', KEEPER, 'happy', look=(0.9, -0.8), blink=blink_at(t, 1.2))
    tag(pn, 300, 420, 'CORVUS', 70, pop(t, T['bridge8']), rot_=-3, sub='"THE RAVEN", ITS MODERN NAME')

def cam_parts(t, sc, ox, oy):
    m = eio(P(t, T['tall'] - 0.3, 0.8))
    return camfocus(lerp(1.15, 1.3, m) * sc, 470, lerp(1120, 1020, m), CX, lerp(1080, 1000, m), ox, oy)

# ---------------- dimensions: 36 ft long, 4 ft wide, knee high rails ----------------
def sc_dims(base, pn, t):
    bgp(base, 'parch', 0.3)
    fy = 1150
    floor(pn, fy)
    m = eio(P(t, T['and9'] - 0.05, 0.55))           # side view -> end view
    slide = eo3(P(t, T['dims'] - 0.05, 0.4))
    L_ = lerp(900, 250, m); th = lerp(30, 66, m)
    cx_ = lerp(540 + (1 - slide) * 900, 540, 1)
    cx_ = 540 + (1 - slide) * 1000
    x0, x1 = cx_ - L_ / 2, cx_ + L_ / 2
    # plank on low trestles so it stands on the floor
    for xx in ((x0 + 60, x1 - 60) if m < 0.5 else (cx_,)):
        pn.rect(xx - 18, fy - 70, xx + 18, fy, fill=WOOD_D, outline=INK, width=3)
    pn.rect(x0, fy - 70 - th, x1, fy - 70, fill=(168, 122, 74), outline=INK, width=4, r=4)
    top = fy - 70 - th
    if m < 0.98:
        for i in range(1, 12):
            xx = lerp(x0, x1, i / 12)
            pn.line([(xx, top + 4), (xx, top + th - 4)], lerpc((168, 122, 74), INK, .3), 2.4, caps=False)
    # figure for scale walks along the plank, then stands on the end view
    kf = lerp(0.52, 1.25, m)
    wx = lerp(x0 + 80, x1 - 120, eio(P(t, T['n36'], 1.2))) if m < 0.01 else cx_
    walking = m < 0.01 and T['n36'] < t < T['n36'] + 1.2
    rail_on = P(t, T['rail'] - 0.1, 0.3); rail2 = P(t, T['each10'] - 0.1, 0.3)
    look = (0.9, 0.2)
    if m > 0.9 and t > T['rail'] - 0.1: look = (-1.0, 0.6) if t < T['each10'] else (1.0, 0.6)
    ex = 'neutral' if t < T['knee'] else 'happy'
    J = figure(pn, wx, top, kf, 1, walk_pose(t, 8, 18) if walking else 'idle', KEEPER, ex, look=look, blink=blink_at(t, 2.2),
               shield=False)
    # knee height marker, then the rails at that height
    knee_y = top + J['kneeF'][1] * kf
    if m > 0.9:
        a = P(t, T['knee'] - 0.05, 0.3)
        if a > 0 and t < T['rail'] + 0.2:
            arrow(pn, (wx + 200, knee_y), (wx + 40 * kf + 10, knee_y), AMBER, 7, 24, p=eo3(a))
        for sd, q in ((-1, rail_on), (1, rail2)):
            if q <= 0: continue
            q = eoback(q); rx = cx_ + sd * (L_ / 2 - 10)
            pn.line([(rx, top), (rx, top - (top - knee_y) * q)], WOOD_D, 10)
            pn.rect(rx - 16, top - (top - knee_y) * q - 8, rx + 16, top - (top - knee_y) * q + 6, fill=WOOD_D, outline=INK, width=3, r=3)
            particles(pn, 'dust', rx, top, t, (T['rail'] if sd < 0 else T['each10']) - 0.05, 0.4, seed=140 + sd, ground=top + 2)
    # dimension arrows with their measurements
    a36 = P(t, T['n36'] - 0.05, 0.45) * (1 - m)
    if a36 > 0.01:
        yb = top - 360
        e = eo3(a36)
        arrow(pn, (cx_, yb), (lerp(cx_, x0, e), yb), INK, 6, 24); arrow(pn, (cx_, yb), (lerp(cx_, x1, e), yb), INK, 6, 24)
        for xx in (x0, x1): pn.line([(xx, yb - 30), (xx, top - 10)], (120, 105, 85, int(200 * a36)), 3, caps=False)
        pn.rect(cx_ - 120, yb - 44, cx_ + 120, yb + 44, fill=(250, 244, 228), outline=INK, width=4, r=12)
        pn.text(cx_, yb + 2, '36 FT', 56, INK, 'Black', 'mm', True)
    a4 = P(t, T['n4'] - 0.05, 0.4) * m
    if a4 > 0.01:
        yb = fy + 90
        e = eo3(a4)
        arrow(pn, (cx_, yb), (lerp(cx_, x0, e), yb), INK, 6, 24); arrow(pn, (cx_, yb), (lerp(cx_, x1, e), yb), INK, 6, 24)
        pn.rect(cx_ - 100, yb + 30, cx_ + 100, yb + 110, fill=(250, 244, 228), outline=INK, width=4, r=12)
        pn.text(cx_, yb + 72, '4 FT', 52, INK, 'Black', 'mm', True)
    if 0.05 < m < 0.95:
        pn.text(cx_, top - 420, '', 10, INK)
    tag(pn, 760, 560, 'SIDE VIEW', 40, pop(t, T['dims'] + 0.2) * (1 - P(t, T['and9'] - 0.1, 0.2)), rot_=3)
    tag(pn, 760, 560, 'END VIEW', 40, pop(t, T['and9'] + 0.45), rot_=3)

# ---------------- the spike ----------------
def sc_spike(base, pn, t):
    bgp(base, 'parch', 0.3)
    fl = 1330
    floor(pn, fl)
    ft = 30
    tipx, tipy = 430, 600
    # gangway coming in from the left edge, so nothing floats
    pn.rect(-100, tipy - 1.1 * ft, tipx, tipy, fill=(168, 122, 74), outline=INK, width=4)
    for i in range(5):
        xx = tipx - 40 - i * 120
        pn.line([(xx, tipy - 1.1 * ft), (xx, tipy - 2.9 * ft)], WOOD_D, 8, caps=False)
    pn.line([(-100, tipy - 2.9 * ft), (tipx - 20, tipy - 2.9 * ft)], WOOD_D, 10)
    s = eoback(P(t, T['iron'] - 0.1, 0.3)) if t > T['iron'] - 0.1 else 0
    if t > T['tip'] - 0.1 and s < 0.05:
        u = P(t, T['tip'] - 0.1, 0.5)
        ring(pn, tipx, tipy, 30 + 90 * u, AMBER, u, 8)
    glint = win(t, T['spike11'] - 0.05, T['spike11'] + 0.5)
    sp_len = 430
    if T['iron'] - 0.1 < t < T['iron'] + 0.15:
        speed_lines(pn, tipx - 40, tipy + 120, 0, 1, t, length=200, n=6, spread=70, seed=61)
    impact(pn, tipx - 40, tipy + 40, t, T['iron'] + 0.14, 0.7, seed=62, col=(230, 236, 244))
    particles(pn, 'sparks', tipx - 40, tipy + 30, t, T['iron'] + 0.14, 0.8, seed=63, cone=math.pi * 1.6)
    if s > 0:
        drop = (1 - clamp(s)) * -140
        spike_shape(pn, tipx - 40, tipy + 30 + drop, math.pi / 2, sp_len * min(1.0, s), 1, lerpc(IRON, (220, 224, 230), glint * 0.5))
    # the Keeper walks in holding a pestle, heavy end up: the same shape
    a = P(t, T['shaped'] - 0.15, 0.5)
    if a > 0:
        kx = lerp(1400, 900, eo3(a)); k_ = 1.5
        walking = a < 1
        if walking: speed_lines(pn, kx + 40, fl - 200, -1, 0, t, length=200, n=5, spread=150, seed=64, col=(120, 105, 85), alpha=150)
        particles(pn, 'dust', kx - 20, fl, t, T['shaped'] + 0.35, 0.8, seed=65, ground=fl + 4)
        pk = 1.16
        def held(pn_, J):
            hx, hy = J['haF']
            pestle(pn_, hx - 10 * pk, hy - 120 + 100 * pk, pk, ang=math.pi, mortar=False)
        figure(pn, kx, fl, k_, -1, walk_pose(t, 8, 16) if walking else 'idle', KEEPER, 'happy' if t > T['pestle'] else 'neutral',
               look=(-1, -0.4), blink=blink_at(t, 1.7), held=held, hands={'F': (-72, -150)}, shield=False)
        av = int(255 * win(t, T['pestle'] - 0.05, T['pestle'] + 1.4))
        if av > 3:
            pn.rect(tipx - 130, tipy + 10, tipx + 50, tipy + 40 + sp_len, outline=AMBER + (av,), width=8, r=50)
            hx_ = kx - 72 * k_; hy_ = fl - 150 * k_
            pn.rect(hx_ - 50, hy_ - 120 * k_ - 50, hx_ + 50, hy_ + (147) * k_ + 20, outline=AMBER + (av,), width=8, r=50)

def cam_spike(t, sc, ox, oy):
    m = eio(P(t, T['spk'], 2.0))
    return camfocus(lerp(1.0, 1.08, m) * sc, 520, 900, CX, 900, ox, oy)

# ---------------- the attack ----------------
AP = dict(rx=-40, y=1260, k=0.6)
def enemy_ax(t):
    xf = AP['rx'] + 1000 * AP['k']
    return lerp(xf + 900, xf + 40, eo3(P(t, T['enemy'] - 0.25, T['near'] - T['enemy'] + 0.35))) - 40 * eio(P(t, T['near'] + 0.1, 0.8))
def corvus_ang(t):
    if t < T['go']: return 72.0
    u = clamp((t - T['go']) / (T['land_dn'] - T['go']))
    return lerp(72.0, 5.0, u ** 2.2)

def attack_scene(base, pn, t, ang=None, crew=True, figs=True, slack=0.0, sync=0.0, vis=None):
    bgp(base, 'seaday', 0.0)
    y = AP['y']
    ex_ = enemy_ax(t)
    eb = 4 * math.sin(t * 2.3 + 1.7 * (1 - sync))
    rb = 4 * math.sin(t * 2.3)
    eb = lerp(eb, rb, sync)
    C = galley(pn, ex_, y + eb, AP['k'], t, -1, hull=PUN_HULL, stripe=PUN_STRIPE, oar_rate=1.6 if t < T['near'] else 0.4)
    ang = corvus_ang(t) if ang is None else ang
    R = galley(pn, AP['rx'], y + rb, AP['k'], t, 1, oar_rate=0.5, corvus_ang=ang, corvus_kw=dict(rope_slack=slack))
    return R, C

def sc_appr(base, pn, t):
    R, C = attack_scene(base, pn, t)
    y = AP['y']
    cvp = R['cv']
    if t < T['near'] + 0.1:
        ex_ = enemy_ax(t)
        speed_lines(pn, ex_ - 300 * AP['k'], y - 150, -1, 0, t, length=380, n=8, spread=45, seed=71)
        particles(pn, 'spray', ex_ - 548 * AP['k'] + 20, y - 4, t, t - (t * 7 % 1) / 7, 1.1, seed=int(t * 7), ang=-math.pi * 0.25, cone=math.pi * 0.4)
    # Carthaginian sailors on their deck
    cb = C['bow']
    for i, dx in enumerate((60, 170)):
        figure(pn, cb[0] + dx, cb[1], 0.42, -1, 'point' if i == 0 and t < T['go'] else 'idle', 'punic' if i == 0 else 'punic2',
               'happy' if t < T['go'] else 'surprised', look=(-1, -0.3), blink=blink_at(t, 3 + i))
    # legionaries waiting behind the corvus
    rb_ = R['bow']
    for i, dx in enumerate((-260, -330)):
        figure(pn, rb_[0] + dx, rb_[1], 0.42, 1, 'idle', 'legion2' if i == 0 else 'legion3', 'determined', look=(1, 0), blink=blink_at(t, 5 + i))
    # crewman at the hauling rope, lets go on "go"
    k_ = 0.48
    fx = rb_[0] - 100
    rope_x = cvp['base'][0] - 0.6 * CV_FT * AP['k']
    released = t > T['go']
    if not released:
        hy = (rb_[1] - 150 * k_ - rb_[1]) / k_
        hands = {'F': ((rope_x - fx) / k_, hy), 'B': ((rope_x - fx) / k_ - 4, hy + 26)}
        p = 'pull'
    else:
        hands = None
        p = mix('pull', pose('shrug' if 'shrug' in POSES else 'cheer'), eoback(P(t, T['go'], 0.25)))
    figure(pn, fx, rb_[1], k_, 1, p, 'rower', 'determined' if not released else 'happy', look=(1, -0.6), blink=blink_at(t, 2), hands=hands)
    if released and t < T['go'] + 0.35:
        speed_lines(pn, rope_x, rb_[1] - 120, 0, -1, t, length=160, n=5, spread=20, seed=72)
        impact(pn, rope_x, rb_[1] - 70 * k_, t, T['go'], 0.4, seed=73)
    water(pn, y - 2, t, col=SEA_C, light=SEA_L, x0=-900, x1=2200)

def cam_appr(t, sc, ox, oy):
    m = eio(P(t, T['crew12'] - 0.2, 0.6))
    fx = AP['rx'] + 440 * AP['k'] - 70; fy = AP['y'] - 70 * AP['k'] - 120
    bx = AP['rx'] + 440 * AP['k'] + 160
    return camfocus(lerp(1.4, 2.2, m) * sc, lerp(bx, fx, m), lerp(1130, fy, m), CX, lerp(1060, 980, m), ox, oy)

def sc_swing(base, pn, t):
    slack = P(t, T['go'], 0.4)
    R, C = attack_scene(base, pn, t, slack=slack)
    cvp = R['cv']
    # smear behind the falling bridge
    if T['go'] < t < T['land_dn'] + 0.12:
        piv = cvp['piv']; Lb = 24 * CV_FT * AP['k']
        sm = []
        for dt in (0.16, 0.12, 0.08, 0.05, 0.025, 0.0):
            aa = math.radians(corvus_ang(max(T['go'], t - dt)))
            sm.append(((piv[0] + math.cos(aa) * Lb * 0.35, piv[1] - math.sin(aa) * Lb * 0.35), (piv[0] + math.cos(aa) * Lb, piv[1] - math.sin(aa) * Lb)))
        smear(pn, sm, alpha=210)
        if t < T['land_dn']:
            aa = math.radians(corvus_ang(t)); tp = (piv[0] + math.cos(aa) * Lb, piv[1] - math.sin(aa) * Lb)
            speed_lines(pn, tp[0], tp[1], math.sin(aa), math.cos(aa), t, length=160, n=6, spread=40, seed=81)
    for i, dx in enumerate((-260, -330)):
        rb_ = R['bow']
        figure(pn, rb_[0] + dx, rb_[1], 0.42, 1, 'idle', 'legion2' if i == 0 else 'legion3', 'determined', look=(1, -0.3), blink=blink_at(t, 5 + i))
    cb = C['bow']
    for i, dx in enumerate((60, 170)):
        figure(pn, cb[0] + dx, cb[1], 0.42, -1, 'cower' if t > T['down'] else 'idle', 'punic' if i == 0 else 'punic2',
               'fear' if t > T['swung'] else 'surprised', look=(-0.6, -0.8), blink=0)
    if t > T['land_dn']:
        particles(pn, 'dust', cvp['tip'][0], cvp['tip'][1] + 20, t, T['land_dn'], 0.8, seed=82, ground=cvp['tip'][1] + 30)
        particles(pn, 'chips', cvp['tip'][0], cvp['tip'][1] + 10, t, T['land_dn'], 0.7, seed=83)
        impact(pn, cvp['tip'][0], cvp['tip'][1] + 10, t, T['land_dn'], 0.75, seed=84)
    water(pn, AP['y'] - 2, t, col=SEA_C, light=SEA_L, x0=-900, x1=2200)

def cam_swing(t, sc, ox, oy):
    fx = AP['rx'] + 440 * AP['k'] + 120; fy = AP['y'] - 70 * AP['k'] - 110
    return camfocus(1.75 * sc, fx, fy, CX, 960, ox, oy)

def sc_punch(base, pn, t):
    bgp(base, 'seaday', 0.3)
    dy_ = 1240
    # enemy deck planks fill the bottom of the frame
    pn.rect(-80, dy_, 1160, 2400, fill=(122, 94, 72), outline=INK, width=4)
    for i in range(10): pn.line([(-80, dy_ + 40 + i * 60), (1160, dy_ + 40 + i * 60)], (96, 72, 54), 4, caps=False)
    for i in range(8): pn.line([(60 + i * 150, dy_), (60 + i * 150, dy_ + 40)], (96, 72, 54), 4, caps=False)
    pn.line([(-80, dy_ - 70), (1160, dy_ - 70)], (100, 76, 58), 8)
    for i in range(10): pn.line([(i * 120, dy_ - 70), (i * 120, dy_)], (100, 76, 58), 5, caps=False)
    ft = 24
    u = clamp((t - (T['punch_s'] - 0.2)) / (T['hit'] - T['punch_s'] + 0.2))
    tipx, tipy0, tipy1 = 520, 420, dy_ - 110
    tipy = lerp(tipy0, tipy1, u ** 2.4)
    # the gangway comes down from the upper left edge
    pn.poly([(-120, tipy - 260), (tipx + 10, tipy - 30), (tipx + 10, tipy + 4), (-120, tipy - 226)], fill=(168, 122, 74), outline=INK, width=4)
    for i in range(5):
        xx = tipx - 60 - i * 130; yy = lerp(tipy - 30, tipy - 260, (tipx - xx) / (tipx + 120))
        pn.line([(xx, yy), (xx - 16, yy - 50)], WOOD_D, 7, caps=False)
    sink = 60 * eoback(P(t, T['hit'], 0.15)) if t > T['hit'] else 0
    spike_shape(pn, tipx - 10, tipy + 2 + sink * 0.0, math.pi / 2 + 0.06, 7.0 * ft + sink * 0.0, 1)
    if t > T['hit']:
        # the point is buried: redraw the top plank over it
        pn.rect(tipx - 60, dy_ + 30, tipx + 60, dy_ + 40, fill=(122, 94, 72))
        for i in range(6):
            a = -math.pi * (0.1 + i * 0.16)
            pn.line([(tipx - 6, dy_ + 34), (tipx - 6 + math.cos(a) * 46, dy_ + 34 + math.sin(a) * 18)], INK, 4)
        splinters(pn, tipx, dy_ + 20, t, T['hit'], 1.3)
        particles(pn, 'chips', tipx, dy_ + 20, t, T['hit'], 1.6, seed=91, cone=math.pi * 0.9)
        particles(pn, 'dust', tipx, dy_ + 30, t, T['hit'] + 0.02, 1.4, seed=92, ground=dy_ + 40)
    if T['punch_s'] < t < T['hit']:
        speed_lines(pn, tipx - 10, tipy - 60, 0.06, 1, t, length=260, n=7, spread=60, seed=93)
    focus_lines(pn, tipx, dy_ + 20, t, T['hit'], 0.28)
    impact(pn, tipx, dy_ + 20, t, T['hit'], 1.7, seed=94)
    if False:
        pass
    # a Carthaginian sailor recoils
    rec = P(t, T['hit'], 0.25)
    figure(pn, 860 + 60 * eo3(rec), dy_ + 34, 1.15, -1, mix('idle', 'cower', eoback(rec)) if rec > 0 else 'idle', 'punic2',
           'surprised' if t < T['hit'] else 'fear', look=(-1, -0.6) if t < T['hit'] else (-0.6, 0.6), blink=0)

def sc_locked(base, pn, t):
    sync = eio(P(t, T['locked'] - 0.15, 0.5))
    R, C = attack_scene(base, pn, t, ang=5.0, slack=1.0, sync=sync)
    rb_ = R['bow']; cb = C['bow']; cvp = R['cv']
    for i, dx in enumerate((-260, -330)):
        figure(pn, rb_[0] + dx, rb_[1], 0.42, 1, 'brace' if t > T['locked'] else 'idle', 'legion2' if i == 0 else 'legion3', 'determined', look=(1, 0), blink=blink_at(t, 5 + i))
    for i, dx in enumerate((90, 200)):
        figure(pn, cb[0] + dx, cb[1], 0.42, -1, 'cower', 'punic' if i == 0 else 'punic2', 'worried', look=(-0.6, -0.2), blink=blink_at(t, i))
    water(pn, AP['y'] - 2, t, col=SEA_C, light=SEA_L, x0=-900, x1=2200)
    # highlight both hulls on "two ships", a ring at the spike on "locked"
    a = win(t, T['two'] - 0.05, T['locked'] + 0.1, 0.12, 0.2)
    if a > 0.02:
        for G_, c in ((R, AMBER), (C, AMBER)):
            mx, my = G_['mid']
            pn.rect(mx - 300, my - 40, mx + 300, my + 60, outline=c + (int(200 * a),), width=7, r=30)
    if t > T['locked'] - 0.05:
        u = P(t, T['locked'] - 0.05, 0.6)
        sx, sy = cvp['spike']
        ring(pn, sx, sy, 30 + 120 * u, AMBER, u, 9)
        particles(pn, 'sparks', sx, sy - 10, t, T['locked'], 0.7, seed=101, cone=math.pi * 1.2)
        impact(pn, sx, sy - 10, t, T['locked'], 0.55, seed=102)

def cam_locked(t, sc, ox, oy):
    m = eio(P(t, T['lock_s'], 1.6))
    fx = AP['rx'] + 440 * AP['k'] + 140
    return camfocus(lerp(1.6, 1.75, m) * sc, fx, AP['y'] - 110, CX, 1000, ox, oy)

# ---------------- boarding ----------------
BD = dict(rx=-260, y=1330, k=0.95)
def sc_board(base, pn, t):
    bgp(base, 'seaday', 0.0)
    y = BD['y']; k = BD['k']
    sync = 4 * math.sin(t * 2.3)
    C = galley(pn, BD['rx'] + 1000 * k, y + sync, k, t, -1, hull=PUN_HULL, stripe=PUN_STRIPE, oar_rate=0.3, row=0.3)
    R = galley(pn, BD['rx'], y + sync, k, t, 1, oar_rate=0.3, row=0.3, corvus_ang=5.0, corvus_kw=dict(rope_slack=1.0))
    cvp = R['cv']; deck = R['bow'][1]
    piv, tip = cvp['piv'], cvp['tip']
    surf = lambda x: lerp(piv[1], tip[1], clamp((x - piv[0]) / (tip[0] - piv[0]))) - 1.1 * CV_FT * k * 0.5
    def gy(x):
        if x < piv[0]: return deck
        if x < tip[0] - 10: return surf(x)
        return C['bow'][1]
    # Carthaginians backing away, hands on cheeks
    cb = C['bow']
    for i, dx in enumerate((230, 360)):
        back = 40 * eio(P(t, T['across'] - 0.2, 0.8))
        figure(pn, cb[0] + dx + back, cb[1], 0.6, -1, 'cower', 'punic' if i == 0 else 'punic2', 'fear', look=(-0.8, 0), blink=0)
    # three legionaries march across
    u = t - T['board']
    for i, (o, d0) in enumerate((('legion2', 0.0), ('legion3', 0.35), (KEEPER, 0.7))):
        s0 = piv[0] - 200 - i * 120
        x = s0 + 260 * max(0, (t - (T['legionaries'] - 0.4) - d0 * 0.4)) * 0.9
        x = min(x, tip[0] + 120 - i * 110)
        moving = x < tip[0] + 120 - i * 110 - 1
        p = walk_pose(t + i, 8, 18) if moving and t > T['legionaries'] - 0.4 else pose('brace')
        if moving and t > T['legionaries'] - 0.4:
            k0 = math.floor((t + i) * 8 / math.pi)
            for kk in (k0 - 1, k0):
                particles(pn, 'dust', x + 10, gy(x), t, kk * math.pi / 8 - i, 0.35, seed=kk % 7 + i, cone=math.pi * 0.6, ground=gy(x) + 2)
        figure(pn, x, gy(x), 0.6, 1, p, o, 'determined', look=(1, 0), blink=blink_at(t, 7 + i))
    impact(pn, tip[0] + 110, C['bow'][1] - 40, t, T['across'] + 0.3, 0.6, seed=111)
    particles(pn, 'dust', tip[0] + 110, C['bow'][1], t, T['across'] + 0.3, 0.8, seed=112, ground=C['bow'][1] + 4)
    water(pn, y - 2, t, col=SEA_C, light=SEA_L, amp=0.6, x0=-900, x1=2200)

def cam_board(t, sc, ox, oy):
    m = eio(P(t, T['board'], T['across'] - T['board'] + 0.4))
    piv_x = BD['rx'] + 440 * BD['k']
    return camfocus(1.1 * sc, lerp(piv_x - 40, piv_x + 220, m), BD['y'] - 170, CX, 1020, ox, oy)

# ---------------- fifty ships (stamp) ----------------
def sc_count(base, pn, t):
    base.paste(bg_cam(env.get('ritual'), 0.3))
    for i in range(50):
        r, c = divmod(i, 5)
        x = 170 + c * 185; y = 470 + r * 82
        a = pop(t, T['cnt'] + i * 0.011, 0.25)
        sink = P(t, T['lost18'] + (49 - i) * 0.016, 0.5)
        ship_icon(pn, x, y, 0.13, t, a * (1 - 0.65 * sink), f=-1, sink=sink)
    focus_lines(pn, 540, 900, t, T['fifty'] - 0.04, 0.25, col=(255, 214, 160))
    impact(pn, 540, 900, t, T['fifty'] - 0.04, 1.8, seed=121, col=(255, 220, 170))
    stamp(pn, 540, 900, 'LIKELY', t - (T['fifty'] - 0.08), sz=140)

# ---------------- the sea battle becomes a land battle ----------------
def sc_landb(base, pn, t):
    m = eio(P(t, T['land19'] - 0.25, 0.6))
    if m <= 0: bgp(base, 'seaday', 0.0)
    elif m >= 1: bgp(base, 'field', 0.0)
    else:
        base.paste(Image.blend(bg_cam(env.get('seaday'), 0.0), bg_cam(env.get('field'), 0.0), m))
    y = 1290; k = 0.55
    sync = 4 * math.sin(t * 2.3) * (1 - m)
    C = galley(pn, -60 + 1000 * k, y + sync, k, t, -1, hull=PUN_HULL, stripe=PUN_STRIPE, row=0.2 * (1 - m), oars=m < 0.5)
    R = galley(pn, -60, y + sync, k, t, 1, row=0.2 * (1 - m), corvus_ang=5.0, corvus_kw=dict(rope_slack=1.0), oars=m < 0.5)
    cb = C['bow']
    # legionaries fight in formation on the enemy deck, Carthaginians fall back
    for i in range(3):
        x = cb[0] + 40 + i * 70 + 20 * eio(P(t, T['battle19'], 1.6))
        swing = math.sin(t * 9 + i * 1.3)
        figure(pn, x, cb[1], 0.4, 1, mix('brace', 'slash', 0.5 + 0.5 * swing), 'legion2' if i % 2 else 'legion3', 'determined',
               look=(1, 0), blink=blink_at(t, i), held=lambda pn_, J: sword_held(pn_, J))
    for i in range(2):
        figure(pn, cb[0] + 330 + i * 90 + 30 * eio(P(t, T['battle19'], 1.6)), cb[1], 0.4, -1, 'cower', 'punic' if i else 'punic2',
               'fear', look=(-0.8, 0), blink=0)
    for j, tc in enumerate((T['sea19'], T['battle19'] + 0.4, T['battle19b'])):
        cxp = cb[0] + 40 + (j % 3) * 70 + 20 * eio(P(t, T['battle19'], 1.6)) + 50
        particles(pn, 'sparks', cxp, cb[1] - 70, t, tc, 0.6, seed=130 + j, cone=math.pi * 1.4)
        impact(pn, cxp, cb[1] - 70, t, tc, 0.35, seed=133 + j, col=(255, 240, 200))
    # water turning into a field under the ships
    col = lerpc(SEA_C, GRASS, m)
    pn.rect(-900, y - 2, 2200, 2400, fill=col + (235,))
    if m < 1:
        rnd = random.Random(4)
        for i in range(60):
            wx = (rnd.uniform(0, 1600) + t * 30) % 1600 - 200; wy = y + 14 + rnd.uniform(0, 520)
            pn.line([(wx, wy), (wx + 30 + (wy - y) * 0.12, wy)], SEA_L + (int(130 * (1 - m)),), 3)
    if m > 0:
        rnd = random.Random(9)
        for i in range(50):
            x = rnd.uniform(-60, 1140); yy = y + 10 + rnd.uniform(0, 600)
            pn.line([(x, yy), (x - 4, yy - 14)], GRASS_L + (int(255 * m),), 3)

def cam_landb(t, sc, ox, oy):
    m = eio(P(t, T['landb'], 2.4))
    return camfocus(lerp(1.5, 1.65, m) * sc, 470, 1200, CX, 1000, ox, oy)

# (start, fn, cam, transition)
SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['sea_s'], sc_sea, cam_sea, None),
    (T['mapc'], sc_mapc, None, None),
    (T['ram_s'], sc_ram, cam_ram, None),
    (T['swd_s'], sc_sword, None, None),
    (T['plan'], sc_plan, cam_plan, 'slide'),        # chapter: 260 BC
    (T['parts'], sc_parts, cam_parts, 'slide'),     # chapter: how it worked
    (T['dims'], sc_dims, None, None),
    (T['spk'], sc_spike, cam_spike, None),
    (T['appr'], sc_appr, cam_appr, 'slide'),        # chapter: the attack
    (T['swing'], sc_swing, cam_swing, None),
    (T['punch_s'], sc_punch, None, None),
    (T['lock_s'], sc_locked, cam_locked, None),
    (T['board'], sc_board, cam_board, None),
    (T['mapm'], sc_mapm, None, 'slide'),            # chapter: the result
    (T['cnt'], sc_count, None, 'dissolve'),
    (T['landb'], sc_landb, cam_landb, 'dissolve'),
    (T['fin'], sc_final, cam_final, None),
]
HUD = {sc_plan: hud_plan}
SLIDE = 0.35
DISS = 0.3

def scene_idx(t):
    return max(i for i, s in enumerate(SCENES) if s[0] <= t)

def render_scene(i, t):
    _, fn, cam, _ = SCENES[i]
    CAM.extra = cam; CAM.set(t)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay)
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
    sp = f.getlength(' ')
    widths = [f.getlength(x) for x in texts]
    total = sum(widths) + sp * (len(texts) - 1)
    k = min(1.0, 960 * SS / total)
    if k < 1:
        f = F('Black', size * SS * k, True); sp = f.getlength(' '); widths = [f.getlength(x) for x in texts]; total = sum(widths) + sp * (len(texts) - 1)
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
        x += wdt + sp
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
    C = [(0.12, 'thud', 1.0), (0.12, 'clank', 0.5), (0.03, 'whooshlow', 0.4), (T['fight0'], 'march', 0.7), (T['fight0'] + 0.05, 'whoosh', 0.3),
         (T['sea_s'], 'waves', 0.7), (T['sea1'], 'splash', 0.5), (T['no1'] - 0.2, 'whooshlow', 0.4), (T['exp1'], 'creak', 0.5),
         (T['mapc'], 'paper', 0.5), (T['mapc'] + 0.05, 'thud', 0.4), (T['mapc'] + 0.2, 'pop', 0.4)]
    for i in range(8): C.append((T['ruled'] + i * 0.09, 'tick', 0.35))
    C += [(T['ram_s'], 'waves', 0.5), (T['ram_s'], 'oars', 0.6), (T['ram'], 'hit', 1.0), (T['ram'] + 0.05, 'crack', 0.8),
          (T['row'] - 0.1, 'oars', 0.6), (T['row'], 'splash', 0.4),
          (T['swd_s'], 'waves', 0.4), (T['single'] - 0.1, 'cloth', 0.4), (T['sword'] - 0.12, 'swish', 0.9), (T['got'], 'swish', 0.5),
          (T['roman4'], 'pop', 0.4),
          (T['plan'] + 0.1, 'waves', 0.3), (T['y260'], 'pop', 0.6), (T['changed'] - 0.05, 'creak', 0.6), (T['rules'] - 0.1, 'ratchetrun', 0.6),
          (T['rules'] + 0.15, 'clank', 0.8)]
    tt_ = T['plan']
    while tt_ < T['parts'] - 0.1:
        if not (T['romans6'] <= tt_ <= T['rules'] + 0.3): C.append((tt_, 'knock', 0.35))
        tt_ += 2 * math.pi / 14
    C += [(T['prow'] - 0.1, 'chime', 0.3), (T['tall'] - 0.1, 'creak', 0.5), (T['pole'], 'pop', 0.5), (T['pulley'] - 0.05, 'clink', 0.6),
          (T['pulley'] + 0.05, 'pop', 0.4), (T['hang'] - 0.05, 'ratchetrun', 0.5), (T['hang'] + 0.5, 'thud', 0.4), (T['bridge8'], 'pop', 0.6),
          (T['dims'] - 0.05, 'slide', 0.5), (T['n36'] - 0.05, 'pop', 0.5), (T['n36'], 'footsteps', 0.4), (T['and9'] - 0.05, 'whooshlow', 0.5),
          (T['n4'] - 0.05, 'pop', 0.5), (T['knee'] - 0.05, 'pop', 0.3), (T['rail'] - 0.1, 'knock', 0.6), (T['each10'] - 0.1, 'knock', 0.6),
          (T['tip'] - 0.1, 'chime', 0.3), (T['iron'] - 0.1, 'clank', 0.9), (T['spike11'], 'clink', 0.6), (T['shaped'] - 0.1, 'slide', 0.5),
          (T['pestle'] - 0.05, 'shimmer', 0.4),
          (T['appr'], 'waves', 0.6), (T['enemy'] - 0.25, 'oars', 0.8), (T['near'], 'horn', 0.4), (T['crew12'] - 0.2, 'whooshlow', 0.4),
          (T['rope'], 'creak', 0.5), (T['go'], 'ropewhip', 0.9),
          (T['swung'] - 0.1, 'whooshlow', 0.8), (T['land_dn'], 'thud', 0.8),
          (T['hit'] - 0.15, 'whoosh', 0.4), (T['hit'], 'hit', 1.0), (T['hit'] + 0.03, 'crack', 1.0),
          (T['two'], 'pop', 0.4), (T['locked'], 'clank', 0.7), (T['locked'] + 0.05, 'chime', 0.3),
          (T['legionaries'] - 0.4, 'march', 0.8), (T['walked'], 'march', 0.6), (T['across'] + 0.3, 'clank', 0.5),
          (T['mapm'] + 0.1, 'paper', 0.5), (T['mylae'] - 0.1, 'thud', 0.5), (T['sicily'], 'pop', 0.6)]
    for i in range(10): C.append((T['cnt'] + i * 0.05, 'tick', 0.3))
    C += [(T['lost18'], 'sinking', 0.6), (T['fifty'] - 0.08, 'stamp', 1.0),
          (T['landb'], 'waves', 0.4), (T['sea19'], 'swordclash', 0.6), (T['battle19'] + 0.4, 'swordclash', 0.5), (T['land19'] - 0.25, 'shimmer', 0.5),
          (T['land19'], 'thud', 0.5), (T['battle19b'], 'swordclash', 0.5),
          (T['rome20'], 'march', 0.7), (T['rarely'], 'pop', 0.5), (T['lost20'] - 0.05, 'thud', 0.9), (T['lost20'], 'clank', 0.4)]
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

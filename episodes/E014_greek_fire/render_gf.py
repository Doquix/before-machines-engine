"""E014 Greek fire: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
from props import tag, stamp, callout, arrow, stone
from gf import *
import env
import make_map as MM

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
PH = {}
for wd in WORDS: PH.setdefault(wd['p'], []).append(wd['t'])
def w(p, i): return PH[p][i]
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))
KEEPER = EPISODE_OUTFIT

# ---------------- beat table (all from measured word onsets) ----------------
T = dict(
    secret0=w(0, 3), greek=w(0, 5), liquid0=w(0, 9),
    mach_s=CAPS[1]['s'], real=w(1, 1), secret1=w(1, 2), machine1=w(1, 5), fired1=w(1, 7),
    map1=CAPS[2]['s'], y672=w(2, 1),
    kal_s=CAPS[3]['s'], refugee=w(3, 1), architect=w(3, 2), kalname=w(3, 4),
    map2=CAPS[4]['s'], const=w(4, 1), syria=w(4, 3),
    siege=CAPS[5]['s'], arab=w(5, 0), besiege=w(5, 5), city=w(5, 7),
    drom=CAPS[6]['s'], warships=w(6, 1), bronze=w(6, 4), tube_w=w(6, 5), bow=w(6, 8),
    rit=CAPS[7]['s'], sources=w(7, 2), suggest=w(7, 3),
    sys=CAPS[8]['s'], liquid8=w(8, 1), heated=w(8, 3), sealed=w(8, 6), tank_w=w(8, 7), crew=w(8, 10), worked=w(8, 11), pump=w(8, 13),
    press=CAPS[9]['s'], built=w(9, 1),
    jet_s=CAPS[10]['s'], jet_w=w(10, 1), shot=w(10, 2), lit=w(10, 5), nozzle=w(10, 8), spread=w(10, 10), water_w=w(10, 13),
    buck=CAPS[11]['s'], water11=w(11, 0), put=w(11, 3), out11=w(11, 5),
    rem=CAPS[12]['s'], sand=w(12, 1), vinegar=w(12, 2), urine=w(12, 4), according=w(12, 6), later=w(12, 8),
    rng=CAPS[13]['s'], calm=w(13, 2), close=w(13, 5), crews=w(13, 8), near_w=w(13, 11),
    bul=CAPS[14]['s'], y812=w(14, 1), bulgar=w(14, 3), captured=w(14, 5), siphons=w(14, 6), fuel=w(14, 8),
    sput=CAPS[15]['s'], make=w(15, 3), work=w(15, 5),
    whole_s=CAPS[16]['s'], never=w(16, 3), whole=w(16, 5), secret16=w(16, 6),
    fin=CAPS[17]['s'], machine17=w(17, 3), fired17=w(17, 5),
    end=VO_END,
)
T['ignite'] = T['spread'] + 0.9          # enemy ship catches
CAM.drift = 0.5
CAM.punch = [(T['liquid0'], 0.06), (T['machine1'], 0.05), (T['suggest'] - 0.12, 0.10), (T['lit'], 0.07),
             (T['y812'], 0.05), (T['whole'], 0.05)]
CAM.shake = [(T['lit'], 10, 0.4), (T['ignite'], 14, 0.5), (T['out11'], 12, 0.45)]
FLASH = [(T['lit'], 0.12, (255, 214, 150), 100)]

def bgp(base, name, par=0.5):
    base.paste(bg_cam(env.get(name), par))

def floor(pn, y, col=(206, 190, 158), line=True):
    """Solid ground in the vector layer so figures and props stand on something."""
    pn.rect(-400, y, 1480, 2800, fill=col)
    if line: pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def road(pn, y):
    pn.rect(-400, y - 6, 1480, 2800, fill=(176, 148, 104))
    pn.line([(-400, y - 6), (1480, y - 6)], (120, 96, 64), 4, caps=False)
    rnd = random.Random(5)
    for i in range(40):
        x = rnd.uniform(-60, 1140); yy = y + 10 + rnd.uniform(0, 500)
        pn.ell(x, yy, 10 + rnd.uniform(0, 14), 4 + rnd.uniform(0, 3), fill=(150, 124, 86))

def walk_pose(t, rate=9.0, amp=22, base='walk'):
    s = math.sin(t * rate)
    return pose(base, thF=amp * s, thB=-amp * s, shF=-max(0, -s) * 30, shB=-max(0, s) * 30,
                uaF=-18 * s, faF=-10 * s + 6, uaB=18 * s, faB=10 * s + 6)

# ---------------- the siphon system (shared by several scenes) ----------------
def machine(pn, ox, oy, k, t, heat=0.7, sealed=1.0, press=0.0, bulge=0.0, pump_ang=0.0, crew=0.0, fire=0.0,
            crew_expr='determined', level=0.62, pump_x=380, show_brazier=True, build=1.0):
    """Origin at ground under the tank. build 0..1 pops the parts in one after another. Returns world points."""
    def part(i):
        return 1.0 if build >= 1 else eoback(clamp(build * 4 - i))
    pn.push(ox, oy, k)
    s0 = part(0)
    if show_brazier and s0 > 0.01:
        pn.push(0, 0, s0); brazier(pn, 0, 0, 1, t, heat); pn.pop()
    s2 = part(2)
    if s2 > 0.01:
        pn.push(pump_x, 0, s2)
        tube(pn, (-30, -110), (126 - pump_x, -128), 22)
        le_, re_ = lever_pump(pn, 0, 0, 0.82, pump_ang)
        pn.pop()
    le, re = (pump_x + le_[0], le_[1]) if s2 > 0.01 else (0, 0), (pump_x + re_[0], re_[1]) if s2 > 0.01 else (0, 0)
    s1 = part(1)
    if s1 > 0.01:
        pn.push(0, -84, s1); tank(pn, 0, 0, 1, t, heat, sealed, level, bulge, press=press); pn.pop()
    out = (70, -314)
    s3 = part(3)
    if s3 > 0.01:
        pn.push(out[0], out[1], s3)
        tube(pn, (0, 0), (0, -246), 30); tube(pn, (-15, -246), (pump_x + 30 - out[0], -246), 30)
        siphon_head(pn, pump_x + 100 - out[0], -246, 1, 1)
        pn.pop()
    if crew > 0 and build >= 1:
        for side, (hx, hy), f_, o in ((0, le, 1, 'byz1'), (1, re, -1, 'byz2')):
            fx = hx - f_ * 62
            loc = ((hx - fx) / 0.95, (hy - 0) / 0.95)
            figure(pn, fx, 0, 0.95 * clamp(crew, 0, 1.2), f_, 'crank', o, crew_expr,
                   hands={'F': loc, 'B': (loc[0] - f_ * 8, loc[1] + 10)}, blink=blink_at(t, side * 1.3), look=(0.6, -0.3))
    pn.pop()
    W_ = lambda p: (ox + p[0] * k, oy + p[1] * k)
    return dict(noz=W_((pump_x + 100, -560)), tank=W_((0, -190)), braz=W_((0, -40)), pump=W_((pump_x, -120)),
                lever=W_((pump_x, -190)), tube=W_((out[0], -380)), crewL=W_((le[0] - 62, -200)))

# ---------------- scenes ----------------
def hook_frame(base, pn, t, final=False):
    bgp(base, 'nightsea', 0.35)
    WL = 1250
    K = dromon(pn, -444, WL + 3 * math.sin(t * 1.7), 1.5, t, 1, oar_rate=1.0)
    nx, ny = K['nozzle']
    L0 = 380 if not final else 820
    L = lerp(L0, 860, eo3(P(t, 0 if not final else T['fin'], 0.6)))
    jet(pn, nx, ny, math.radians(4), L, 1.0, t, 1.45, grav=0.00058)
    for i, x in enumerate((700, 840, 980, 1100)):
        a = 1.0 if final else clamp(0.55 + 0.45 * P(t, i * 0.25, 0.6))
        fire_patch(pn, x, WL + 14, 1.05 + 0.14 * i, t, i + 1, a)
    water(pn, WL, t)
    for i, x in enumerate((700, 840, 980, 1100)):
        flame(pn, x, WL + 18, 70, t, 9 + i, 0.8)
    return K

def sc_hook(base, pn, t):
    hook_frame(base, pn, t)
    tag(pn, 540, 330, 'THE SECRET RECIPE?', 58, pop(t, T['secret0']), rot_=-3, sub='WHAT EVERYONE SAYS')
    a = pop(t, T['liquid0'] - 0.05, 0.35)
    if a > 0:
        jar(pn, 600, 860, 1.45 * a, t, slosh=1.0)

def cam_hook(t, sc, ox, oy):
    return sc + 0.05 * eio(P(t, 0, 2.8)), ox, oy

def sc_final(base, pn, t):
    K = hook_frame(base, pn, t, final=True)
    nx, ny = K['nozzle']

JAR0 = (600, 860, 1.45)
def cam_machine(t, sc, ox, oy):
    z0, x0, y0 = cam_hook(t, sc, ox, oy)
    z1, x1, y1 = camfocus(1.12 * sc, 530, 1000, CX, 900, ox, oy)
    m = eio(P(t, T['mach_s'] + 0.45, 0.9))
    return lerp(z0, z1, m), lerp(x0, x1, m), lerp(y0, y1, m)
def sc_machine(base, pn, t):
    bgp(base, 'parch', 0.3)
    floor(pn, 1300)
    build = clamp((t - (T['mach_s'] + 0.25)) / 0.9)
    fire = P(t, T['fired1'], 0.15)
    M = machine(pn, 470, 1300, 1.0, t, heat=0.8 * build, build=build,
                pump_ang=10 * math.sin(t * 6) if t > T['fired1'] - 0.4 else 0)
    if fire > 0:
        nx, ny = M['noz']
        jet(pn, nx, ny, math.radians(-4), 230 * eo3(fire), 1.0, t, 0.6, grav=0.002)
    # the jar holds its exact screen position through the dissolve, then becomes the fuel beside the brazier
    jp = eio(P(t, T['mach_s'] + 0.35, 0.55))
    jar(pn, lerp(JAR0[0], 245, jp), lerp(JAR0[1], 1300, jp), lerp(JAR0[2], 0.5, jp), t, slosh=1 - jp)
    if jp >= 1:
        callout(pn, 245, 1210, 230, 1060, 'FUEL', P(t, T['machine1'] + 0.2, 0.4), sz=30, hl=True)
    a = P(t, T['mach_s'] + 0.2, 0.3)
    if a > 0:
        pp = 'point' if t > T['machine1'] - 0.15 else 'idle'
        figure(pn, 105, 1310, 1.2 * (0.6 + 0.4 * eoback(a)), 1, pose('point', uaF=105, faF=110) if pp == 'point' else 'idle', KEEPER,
               'smug' if t > T['machine1'] else 'neutral', look=(0.9, -0.5), blink=blink_at(t))

_MAP = {}
def map_img():
    if 'ov' not in _MAP: _MAP['ov'] = Image.open('map_ov.png').convert('RGB')
    return _MAP['ov']
LV = {l[0]: l for l in MM.LEVELS}
def geo_xy(lon, lat):
    _, c_lon, c_lat, span, _ = LV['ov']
    lon_px, lat_px = MM.geo(c_lon, c_lat, span)
    return 540 + (lon - c_lon) / lon_px, 960 - (lat - c_lat) / lat_px
HEL = (36.20, 34.01); CON = (28.98, 41.01)

class MapView:
    def __init__(s, z, fx, fy, tx, ty): s.z, s.fx, s.fy, s.tx, s.ty = z, fx, fy, tx, ty
    def img(s):
        a = 2 / s.z
        return map_img().transform((W, H), Image.AFFINE, (a, 0, 2 * s.fx - s.tx * a, 0, a, 2 * s.fy - s.ty * a), Image.BILINEAR)
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

def map_labels(pn, mv, a=1.0):
    if a <= 0: return
    for name, lon, lat, sz in (('BYZANTINE EMPIRE', 32.4, 39.3, 44), ('BLACK SEA', 34.5, 43.0, 34), ('MEDITERRANEAN', 30.5, 34.6, 32)):
        x, y = mv.xy(lon, lat)
        pn.text(x, y, name, sz, (60, 48, 34, int(220 * a)) if name.startswith('BYZ') else (200, 214, 222, int(200 * a)), 'Black', 'mm', True, sp=4)

def sc_map1(base, pn, t):
    z = lerp(1.18, 1.3, eio(P(t, T['map1'], 2.2)))
    fx, fy = geo_xy(32.6, 37.2)
    mv = MapView(z, fx, fy, 540, 800)
    base.paste(mv.img())
    map_labels(pn, mv, P(t, T['map1'] + 0.1, 0.4))
    tag(pn, 540, 330, 'AROUND 672 AD', 74, pop(t, T['y672']), rot_=-3)

def bez(p0, p1, p2, u): return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])

def sc_map2(base, pn, t):
    zp = eio(P(t, T['syria'] + 0.15, 0.9))
    z = lerp(1.3, 2.2, zp)
    f0 = geo_xy(32.6, 37.2); f1 = geo_xy(*CON)
    fx, fy = lerp(f0[0], f1[0], zp), lerp(f0[1], f1[1], zp)
    mv = MapView(z, fx, fy, 540, lerp(800, 700, zp))
    base.paste(mv.img())
    map_labels(pn, mv, (1 - zp) * (1 - P(t, T['map2'], 0.3)) + 0 * zp, )
    h = mv.xy(*HEL); c = mv.xy(*CON); m = mv.xy(33.4, 38.6)
    rp = eio(P(t, T['map2'] + 0.35, T['syria'] - T['map2'] - 0.2))
    n = 40
    for i in range(0, int(n * rp), 2):
        a_, b_ = bez(h, m, c, i / n), bez(h, m, c, min(rp, (i + 1) / n))
        pn.line([a_, b_], RUST, 8)
    if 0 < rp < 1:
        tx, ty = bez(h, m, c, rp); pn.circ(tx, ty, 16, fill=AMBER, outline=INK, width=4)
    pin(pn, *h, t, T['map2'] - 0.05)
    tag(pn, h[0] - 250, h[1] - 120, 'HELIOPOLIS', 44, pop(t, T['map2'] + 0.1) * (1 - zp), rot_=3, sub='SYRIA')
    pin(pn, *c, t, T['const'] - 0.1)
    tag(pn, c[0] + 230, c[1] - 150, 'CONSTANTINOPLE', 46, pop(t, T['const']), rot_=-3)
    tag(pn, 640, 560, 'ROUTE SIMPLIFIED', 30, pop(t, T['map2'] + 0.4) * (1 - zp), rot_=0)
    if t > T['syria'] - 0.05 and zp < 0.5:
        rp2 = eo3(P(t, T['syria'] - 0.05, 0.5))
        pn.circ(*h, 30 + 70 * rp2, outline=AMBER + (int(255 * (1 - rp2)),), width=7)

def sc_kalli(base, pn, t):
    bgp(base, 'road', 0.45)
    u = t - T['kal_s']
    x = lerp(860, 520, eo3(clamp(u / 1.6)))
    walking = u < 1.6
    look_back = T['refugee'] - 0.05 < t < T['architect'] + 0.35
    p = walk_pose(t) if walking else pose('idle')
    ex = 'worried' if look_back else ('determined' if t < T['kalname'] else 'neutral')
    def held(pn_, J):
        hx, hy = (J['haF'][0] + J['haB'][0]) / 2, (J['haF'][1] + J['haB'][1]) / 2
        pn_.push(hx, hy, 1.0)
        pn_.rect(-34, -12, 34, 12, fill=(236, 222, 186), outline=INK, width=3, r=10)
        pn_.circ(-34, 0, 12, fill=(214, 196, 156), outline=INK, width=3); pn_.circ(34, 0, 12, fill=(214, 196, 156), outline=INK, width=3)
        pn_.pop()
    # distant smoke over the hills behind him
    smoke(pn, 980, 1060, 1.3, t, 2, 0.8)
    road(pn, 1320)
    belly = -(L['th'] + L['sh']) - 14
    J = figure(pn, x, 1320, 2.05, -1, p, 'kalli', ex, look=(-1.0, -0.1) if look_back else (0.8, -0.1), blink=blink_at(t, 2), held=held,
               hands={'F': (-20, belly), 'B': (20, belly)})
    hx = x + J['head'][0] * 2.05; hy = 1320 + J['head'][1] * 2.05
    tag(pn, 400, 600, 'KALLINIKOS', 72, pop(t, T['kalname']), rot_=-4, sub='FROM HELIOPOLIS, SYRIA', string_to=(hx, hy - 60))

def sc_siege(base, pn, t):
    bgp(base, 'cityview', 0.4)
    u = t - T['arab']
    sp = eio(P(t, T['besiege'] - 0.3, 0.9))
    rows = ((1120, 0.16, 6, 0.0), (1200, 0.22, 5, 0.12), (1300, 0.3, 4, 0.24))
    for ry, k_, n, d_ in rows:
        a = eo3(P(t, T['arab'] + d_, 0.9))
        for i in range(n):
            gap = 1080 / (n - 0.4)
            bx = 60 + i * gap * lerp(0.75, 1.0, sp) + (1 - a) * 900 + 30 * math.sin(t * 0.8 + i)
            galley_small(pn, bx, ry + 3 * math.sin(t * 2 + i), k_, t, -1, seed=i + ry)
    water(pn, 1330, t, col=SEA_D, light=(130, 170, 190))
    tag(pn, 540, 380, '674 TO 678 AD', 70, pop(t, T['besiege']), rot_=-3, sub='ARAB SIEGE OF CONSTANTINOPLE')

DROM = dict(x=215, y=1250, k=1.25)
def drom_state(t):
    x = lerp(-1100, DROM['x'], eo3(P(t, T['drom'] - 0.05, 1.0)))
    return x, DROM['y'] + 4 * math.sin(t * 1.8), DROM['k']

def sc_drom(base, pn, t):
    bgp(base, 'daysea', 0.4)
    x, y, k = drom_state(t)
    K = dromon(pn, x, y, k, t, 1)
    dx, dy = K['deck']
    figure(pn, dx - 40, dy, 0.85, 1, 'point' if t > T['bronze'] - 0.1 else 'idle', KEEPER, 'happy', look=(0.8, 0.3), blink=blink_at(t))
    water(pn, y + 2, t, col=SEA_D, light=(130, 170, 190))
    nx, ny = K['nozzle']
    tag(pn, 760, 300, 'DROMON', 64, pop(t, T['warships']), rot_=-3, sub='BYZANTINE WARSHIP')
    callout(pn, nx - 70, ny, 800, 760, 'SIPHON', P(t, T['bronze'], 0.45), hl=True)

def camfocus(z, fx, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def cam_drom(t, sc, ox, oy):
    x, y, k = drom_state(t)
    nx, ny = x + 516 * k, y - 150 * k
    m = eio(P(t, T['bronze'] - 0.2, 0.6))
    return camfocus(lerp(1.0, 1.45, m) * sc, lerp(CX, nx - 120, m), lerp(CY, ny + 40, m), CX, CY, ox, oy)

def sc_rit(base, pn, t):
    base.paste(bg_cam(env.get('ritual'), 0.3))
    siphon_head(pn, 640, 900, 2.6, 1)
    pn.rect(-50, 960, 1130, 990, fill=(236, 226, 204, 40))
    tag(pn, 540, 420, 'MODERN RECONSTRUCTIONS', 50, pop(t, T['sources']), rot_=-3)
    stamp(pn, 560, 1160, 'LIKELY', t - (T['suggest'] - 0.12), sz=130)

SYS = dict(x=330, y=1290, k=1.2)
def sc_sys(base, pn, t):
    bgp(base, 'parch', 0.3)
    floor(pn, SYS['y'])
    heat = eo3(P(t, T['heated'] - 0.1, 0.6))
    sealed = clamp(P(t, T['sealed'] - 0.05, 0.35))
    crew = eoback(P(t, T['crew'] - 0.05, 0.35)) if t > T['crew'] - 0.05 else 0
    pumping = t > T['worked'] - 0.05
    rate = 7 if t < T['press'] else 10
    ang = 15 * math.sin((t - T['worked']) * rate) if pumping else 0
    press = clamp((t - T['pump']) / (T['built'] + 0.5 - T['pump'])) if t > T['pump'] else 0
    bulge = P(t, T['press'], 0.4) * press
    M = machine(pn, SYS['x'], SYS['y'], SYS['k'], t, heat=heat, sealed=sealed, press=press, bulge=bulge,
                pump_ang=ang, crew=crew, crew_expr='determined', level=0.62 + 0.04 * heat)
    # labels
    callout(pn, M['braz'][0] - 150, M['braz'][1], 110, 1000, 'HEAT', P(t, T['heated'], 0.45), hl=True)
    callout(pn, M['tank'][0] - 60, M['tank'][1] - 60, 200, 640, 'SEALED TANK', P(t, T['sealed'] + 0.05, 0.45) * (1 - P(t, T['press'], 0.25)))
    callout(pn, M['pump'][0], M['pump'][1] - 40, 900, 900, 'PUMP', P(t, T['pump'], 0.45) * (1 - P(t, T['press'], 0.25)), hl=True)
    callout(pn, M['tube'][0], M['tube'][1], 640, 460, 'TUBE', P(t, T['tank_w'] + 0.2, 0.45) * (1 - P(t, T['press'], 0.25)))

def hud_sys(pn, t):
    if t > T['pump'] - 0.1:
        press = clamp((t - T['pump']) / (T['built'] + 0.5 - T['pump']))
        a = P(t, T['pump'] - 0.1, 0.3)
        pn.push(540, 300, a)
        pbar(pn, -230, 0, 460, 64, press, 'PRESSURE')
        pn.pop()

def cam_sys(t, sc, ox, oy):
    m = eio(P(t, T['press'] - 0.15, 0.55))
    tx, ty = SYS['x'], SYS['y'] - 190 * SYS['k']
    return camfocus(lerp(1.0, 1.55, m) * sc, lerp(CX, tx + 60, m), lerp(CY, ty, m), CX, CY, ox, oy)

JS = dict(k=1.3, y=1250)
def jet_scroll(t): return 980 * eio(P(t, T['spread'] - 0.1, T['water_w'] + 0.35 - T['spread']))
ENEMY_X = 1500
def cam_jet(t, sc, ox, oy):
    return camfocus(1.22 * sc, CX, 1150, CX, 1010, ox, oy)
def sc_jet(base, pn, t):
    bgp(base, 'nightsea', 0.35)
    S = jet_scroll(t)
    y = JS['y']
    burning = t > T['ignite']
    galley_small(pn, ENEMY_X - S, y + 4 * math.sin(t * 2), 0.9, t, -1, seed=3)
    if burning:
        a = P(t, T['ignite'], 0.4)
        for i, dx in enumerate((-160, -60, 40, 140)):
            fire_patch(pn, ENEMY_X - S + dx * 1.3, y - 70, 0.9 * a + 0.2 * P(t, T['ignite'] + 0.3, 1.0), t, 20 + i, a, water=False)
        smoke(pn, ENEMY_X - S, y - 160, 1.2, t, 4, a)
    K = dromon(pn, -420 - S, y, JS['k'], t, 1, oar_rate=1.0)
    nx, ny = K['nozzle']
    L = 1250 * eo3(P(t, T['jet_w'] - 0.05, 0.6)) if t > T['jet_w'] - 0.05 else 0
    lit = eo3(P(t, T['lit'] - 0.02, 0.45)) if t > T['lit'] - 0.02 else 0
    pts = jet(pn, nx, ny, math.radians(-3), L, lit, t, 1.0, grav=0.00048)
    if lit > 0:
        pn.circ(nx + 10, ny, 50 * (1 - P(t, T['lit'], 0.3)) + 10, fill=F_IN + (int(230 * (1 - P(t, T['lit'], 0.5))),))
    # fire spreading over the water toward the enemy
    if t > T['spread'] - 0.1:
        sp = P(t, T['spread'] - 0.1, T['ignite'] - T['spread'] + 0.1)
        x0 = nx + 650; x1 = ENEMY_X - S - 220
        n = 9
        for i in range(n):
            u = i / (n - 1)
            if u <= sp:
                a = clamp((sp - u) * 4)
                fire_patch(pn, lerp(x0, x1, u), y + 12, 0.75 + 0.2 * (i % 2), t, 40 + i, a)
    water(pn, y + 2, t, scroll=S)
    if L > 600 and lit > 0.9:
        hx = nx + 640
        for i in range(3): flame(pn, hx + (i - 1) * 40, y + 16, 70, t, 60 + i, 0.9)
    callout(pn, nx + 20, ny - 10, 420, 760, 'NOZZLE', P(t, T['nozzle'] - 0.1, 0.4) * (1 - P(t, T['spread'], 0.3)), hl=True)

def sc_buck(base, pn, t):
    bgp(base, 'nightsea', 0.35)
    # ship deck in the vector layer so nothing floats
    pn.rect(-80, 1070, 1160, 1120, fill=(110, 78, 46), outline=INK, width=4)
    for i in range(14): pn.line([(-60 + i * 90, 1070), (-60 + i * 90, 1290)], (86, 60, 36), 8)
    pn.rect(-80, 1290, 1160, 2300, fill=(130, 94, 58), outline=INK, width=4)
    for i in range(8): pn.line([(-80, 1330 + i * 70), (1160, 1330 + i * 70)], (104, 74, 44), 4, caps=False)
    flare = 1.0 + 0.7 * eoback(P(t, T['out11'] - 0.05, 0.35)) if t > T['out11'] - 0.05 else 1.0
    damp = 1 - 0.5 * P(t, T['put'] - 0.05, 0.12) * (1 - P(t, T['out11'] - 0.1, 0.1))
    for i, (x, s) in enumerate(((760, 1.1), (900, 1.3), (1010, 1.0), (640, 0.8))):
        fire_patch(pn, x, 1300, s * flare * damp, t, 70 + i, 1.0, water=False)
    smoke(pn, 860, 1000, 1.5, t, 7, 0.8)
    sw = P(t, T['water11'] - 0.15, 0.3)
    p = mix('hold', pose('reach', uaF=110, faF=120, uaB=96, faB=110), eoback(sw)) if sw > 0 else POSES['hold']
    ex = 'determined' if t < T['put'] else ('surprised' if t < T['out11'] else 'fear')
    def held(pn_, J):
        hx, hy = (J['haF'][0] + J['haB'][0]) / 2, (J['haF'][1] + J['haB'][1]) / 2
        pn_.poly([(hx - 22, hy - 6), (hx + 22, hy - 6), (hx + 17, hy + 36), (hx - 17, hy + 36)], fill=(120, 86, 52), outline=INK, width=3)
        pn_.line([(hx - 22, hy + 6), (hx + 22, hy + 6)], IRON, 3, caps=False)
    figure(pn, 300, 1310, 1.9, 1, p, 'arab', ex, look=(1.0, 0.2), blink=blink_at(t, 3) if t < T['put'] else 0, held=held)
    # thrown water
    if sw > 0.4 and t < T['put'] + 0.35:
        q = P(t, T['water11'] + 0.05, T['put'] - T['water11'])
        for i in range(14):
            u = clamp(q - i * 0.03)
            if u <= 0: continue
            x = lerp(470, 820, u); y = lerp(980, 1240, u) - 220 * 4 * u * (1 - u)
            pn.circ(x + (i % 3) * 14, y + (i % 4) * 9, 12 - i * 0.5, fill=(150, 196, 230, 230))
    if t > T['put'] - 0.05:
        st = P(t, T['put'] - 0.05, 0.9)
        for i in range(6):
            pn.circ(820 + (i - 3) * 30, 1220 - 260 * st - i * 10, 30 + 50 * st, fill=(220, 220, 226, int(160 * (1 - st))))

REM = [('SAND', 'sand', 210), ('VINEGAR', 'vinegar', 540), ('URINE', 'urine', 870)]
def sc_rem(base, pn, t):
    bgp(base, 'parch', 0.3)
    floor(pn, 1220)
    for i, (lab, key, x) in enumerate(REM):
        t0 = T[key]
        hit = P(t, t0 + 0.12, 0.5)
        pn.rect(x - 110, 1180, x + 110, 1220, fill=STONE, outline=INK, width=4, r=8)
        a = pop(t, T['rem'] + i * 0.1, 0.3)
        if a > 0:
            flame(pn, x, 1182, 190 * a * (1 - hit), t, i + 2, 1.0)
            if hit > 0: smoke(pn, x, 1150, 0.7, t, i, 1 - hit * 0.6)
        # pourer hovering above
        lift = 30 * eoback(P(t, t0 - 0.15, 0.3)) if t > t0 - 0.15 else 0
        ix, iy = x, 840 - lift
        if key == 'sand': sack(pn, ix, iy, 1.3)
        elif key == 'vinegar': jar(pn, ix, iy, 1.05, col=(160, 120, 80))
        else: pot(pn, ix, iy, 1.35)
        if t0 - 0.05 < t < t0 + 0.75:
            q = P(t, t0 - 0.05, 0.25)
            col = (214, 190, 130) if key == 'sand' else ((180, 140, 80) if key == 'vinegar' else (220, 200, 90))
            for j in range(12):
                yy = lerp(iy + 6, 1170, ((t * 3 + j / 12) % 1) * q)
                pn.circ(ix + math.sin(j * 2.3) * 10, yy, 7, fill=col + (230,))
        tag(pn, x, 1290, lab, 40, pop(t, t0), rot_=(-1) ** i * 3)
    tag(pn, 540, 420, 'LATER ACCOUNTS', 60, pop(t, T['later'] - 0.05), rot_=-3, sub='WRITTEN AFTER THE FACT')

RG = dict(y=1250, k=0.7)
def cam_rng(t, sc, ox, oy): return camfocus(1.12 * sc, CX, 1180, CX, 1100, ox, oy)
def rng_x(t): return lerp(-120, 200, eio(P(t, T['near_w'] - 0.25, 0.9)))
def sc_rng(base, pn, t):
    bgp(base, 'daysea', 0.4)
    amp = lerp(3.2, 0.35, eio(P(t, T['calm'] - 0.1, 0.5)))
    y = RG['y']
    galley_small(pn, 1040, y + 5 * amp * math.sin(t * 2.4 + 1), RG['k'], t, -1, seed=5)
    dx = rng_x(t)
    rate = 1.2 if t < T['near_w'] - 0.3 else 2.6
    K = dromon(pn, dx, y + 5 * amp * math.sin(t * 2.4), RG['k'], t, 1, oar_rate=rate)
    nx, ny = K['nozzle']
    d_x, d_y = K['deck']
    figure(pn, d_x - 24, d_y, 0.5, 1, 'point' if t > T['close'] else 'idle', KEEPER, 'determined', look=(0.9, 0), blink=blink_at(t, 2))
    # rough sea crests
    if amp > 0.6:
        for i in range(10):
            xx = (i * 137 + t * 90) % 1300 - 100
            pn.poly([(xx, y + 30), (xx + 40, y + 30 - 14 * amp), (xx + 90, y + 30)], fill=(236, 244, 246, int(60 * amp)))
    water(pn, y + 2, t, col=SEA_D, light=(130, 170, 190), amp=amp)
    # range bar between nozzle and enemy bow
    ex_ = 1040 - 480 * RG['k'] - 20
    a = P(t, T['close'] - 0.05, 0.3)
    if a > 0:
        yb = ny - 70
        x1 = lerp(nx, ex_, eo3(a))
        pn.line([(nx, yb), (x1, yb)], RUST, 7)
        for xx in (nx, x1): pn.line([(xx, yb - 18), (xx, yb + 18)], RUST, 7)
    # a test shot that falls short before they close in
    if T['close'] + 0.3 < t < T['near_w'] - 0.2:
        q = P(t, T['close'] + 0.3, 0.5)
        jet(pn, nx, ny, math.radians(-6), 420 * eo3(q), 1.0, t, 0.65, grav=0.0030, ymax=y + 8)
    if t > T['near_w'] + 0.5:
        q = P(t, T['near_w'] + 0.5, 0.4)
        jet(pn, nx, ny, math.radians(-4), (ex_ - nx + 60) * eo3(q), 1.0, t, 0.65, grav=0.0006, ymax=y + 8)

def sc_bul(base, pn, t):
    bgp(base, 'gate', 0.4)
    gy = 1300
    pn.rect(-80, gy, 1160, 2300, fill=(126, 112, 82))
    u = t - T['bul']
    walk = u < 2.6
    x0 = lerp(380, 640, clamp(u / 3.6))
    ps = []
    for i, (o, dx) in enumerate((('bulgar', 0), ('bulgar2', 250))):
        x = x0 + dx - 120
        p = walk_pose(t + i * 0.4, rate=8, amp=18) if walk else pose('idle')
        J = joints(p, 1, 1.0)
        ps.append((x, p, o))
    # the bronze tube carried between them at shoulder height
    k_ = 1.0
    sh_y = gy - (L['th'] + L['sh'] + 10) * k_   # carried at waist height in both hands
    tx0, tx1 = ps[0][0] - 60, ps[1][0] + 90
    def tube_grip(pn_, J):
        pass
    tube(pn, (tx0, sh_y + 6), (tx1, sh_y - 8), 34)
    siphon_head(pn, tx1 + 30, sh_y - 10, 0.7, 1)
    for i, (x, p, o) in enumerate(ps):
        def on_tube(xx): return ((xx - x) / k_, (lerp(sh_y + 6, sh_y - 8, (xx - tx0) / (tx1 - tx0)) - gy) / k_)
        figure(pn, x, gy, k_, 1, p, o, 'happy' if t > T['captured'] else 'determined', look=(0.8, 0), blink=blink_at(t, i + 2),
               hands={'F': on_tube(x + 24), 'B': on_tube(x - 24)}, grip=tube_grip)
    # third man with fuel jars
    x3 = x0 + 470
    def held(pn_, J):
        hx, hy = J['haF']
        jar(pn_, hx + 10, hy + 70, 0.45)
    figure(pn, x3, gy, 1.0, 1, walk_pose(t + 1.1, 8, 18) if walk else pose('hold'), 'bulgar', 'smug', blink=blink_at(t, 5), held=held)
    tag(pn, 540, 330, '812 AD', 78, pop(t, T['y812']), rot_=-3, sub='BULGARS TAKE MESEMBRIA')
    callout(pn, (tx0 + tx1) / 2, sh_y - 24, 330, 760, 'SIPHONS', P(t, T['siphons'], 0.45), hl=True)
    callout(pn, x3 + 40, gy - 150, 860, 760, 'FUEL', P(t, T['fuel'], 0.45), hl=True)

def sc_sput(base, pn, t):
    bgp(base, 'gate', 0.4)
    gy = 1330
    pn.rect(-80, gy, 1160, 2300, fill=(126, 112, 82))
    hard = t > T['make'] - 0.1
    ang = (22 if hard else 10) * math.sin((t - T['sput']) * (12 if hard else 6))
    le, re = lever_pump(pn, 720, gy, 1.0, ang)
    tube(pn, (720 + 30, gy - 100), (950, gy - 100), 28)
    siphon_head(pn, 1010, gy - 100, 0.8, 1)
    fx = le[0] - 110
    loc = ((le[0] - fx) / 2.0, (le[1] - gy) / 2.0)
    ex = 'determined' if t < T['work'] - 0.05 else 'confused'
    figure(pn, fx, gy, 2.0, 1, 'crank', 'bulgar2', ex, look=(1.0, -0.2) if t < T['work'] else (0.2, -0.6),
           hands={'F': loc, 'B': (loc[0] - 8, loc[1] + 8)}, blink=blink_at(t, 1))
    if t > T['make']:
        q = P(t, T['make'], 0.5)
        jet(pn, 1018, gy - 100, math.radians(10), 70 * q, 0, t, 0.5, grav=0.02)
    if t > T['work'] - 0.05:
        q = P(t, T['work'] - 0.05, 1.0)
        for i in range(5):
            pn.circ(1030 + i * 14, gy - 130 - 160 * q - i * 12, 18 + 40 * q, fill=(90, 86, 86, int(170 * (1 - q))))
        tag(pn, 540, 420, '?', 120, pop(t, T['work']), rot_=6)

def sc_whole(base, pn, t):
    bgp(base, 'parch', 0.3)
    floor(pn, 1290)
    jp = eio(P(t, T['never'] - 0.1, 0.5))
    pa = eoback(P(t, T['whole'] - 0.15, 0.4)) if t > T['whole'] - 0.15 else 0
    if pa > 0.02:
        M = machine(pn, 420, 1290, 0.8 * pa, t, heat=1.0, crew=1.0, pump_ang=12 * math.sin(t * 8))
    jar(pn, lerp(540, 130, jp), lerp(1000, 1290, jp), lerp(1.5, 0.5, jp), t, slosh=1 - jp)
    if t < T['whole']:
        callout(pn, lerp(540, 130, jp), lerp(700, 1180, jp), 820, 560, 'THE LIQUID', P(t, T['whole_s'] + 0.05, 0.4) * (1 - jp), hl=True)
    if pa > 0.5:
        a = P(t, T['whole'] + 0.1, 0.35)
        pn.rect(40, 560, 1040, 1320, outline=AMBER + (int(255 * a),), width=10, r=40)
        labs = (('FUEL', (130, 1200), (130, 1090)), ('HEAT', M['braz'], (300, 1090)), ('PRESSURE', M['tank'], (240, 650)),
                ('CREW', M['crewL'], (560, 820)), ('NOZZLE', M['noz'], (900, 1000)))
        for i, (lab, an, lp_) in enumerate(labs):
            callout(pn, an[0], an[1], lp_[0], lp_[1], lab, P(t, T['whole'] + 0.15 + i * 0.12, 0.4), sz=30, hl=(lab == 'FUEL'))

# (start, fn, cam, wipe origin)
SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['mach_s'], sc_machine, cam_machine, 'dissolve'),   # match dissolve on the jar
    (T['map1'], sc_map1, None, 'slide'),      # chapter: the history
    (T['kal_s'], sc_kalli, None, None),
    (T['map2'], sc_map2, None, None),
    (T['siege'], sc_siege, None, None),
    (T['drom'], sc_drom, None, None),
    (T['rit'], sc_rit, None, 'slide'),        # chapter: how it worked
    (T['sys'], sc_sys, cam_sys, 'dissolve'),
    (T['jet_s'], sc_jet, cam_jet, 'slide'),   # chapter: the attack
    (T['buck'], sc_buck, None, None),
    (T['rem'], sc_rem, None, 'dissolve'),
    (T['rng'], sc_rng, cam_rng, None),
    (T['bul'], sc_bul, None, 'slide'),        # chapter: 812
    (T['sput'], sc_sput, None, None),
    (T['whole_s'], sc_whole, None, None),
    (T['fin'], sc_final, None, 'dissolve'),
]
HUD = {sc_sys: hud_sys}
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
    if fn in HUD:
        HUD[fn](Pen(lay, cam=False), t)
    flatten(base, lay)
    return base

# ---------------- captions (word by word) ----------------
STOP = set('a an the of on in to and is it its was had his he them then that this did let at into off out up how here now for like even just according so were could'.split())
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
    C = [(0.0, 'roar', 0.9), (0.0, 'thud', 0.6), (T['secret0'], 'pop', 0.5), (T['liquid0'] - 0.05, 'clack', 0.6), (T['liquid0'], 'slosh', 0.6),
         (T['mach_s'], 'whoosh', 0.4), (T['secret1'] - 0.15, 'whooshlow', 0.5), (T['secret1'] + 0.35, 'thud', 0.5), (T['machine1'], 'pop', 0.6),
         (T['fired1'], 'roar', 0.5),
         (T['map1'], 'whoosh', 0.4), (T['map1'] + 0.1, 'paper', 0.5), (T['y672'], 'pop', 0.6),
         (T['kal_s'], 'whoosh', 0.4), (T['architect'], 'pop', 0.4), (T['kalname'], 'pop', 0.6),
         (T['map2'], 'whoosh', 0.4), (T['map2'] - 0.05, 'thud', 0.4), (T['map2'] + 0.1, 'pop', 0.4), (T['const'] - 0.1, 'thud', 0.5),
         (T['const'], 'pop', 0.5), (T['syria'], 'chime', 0.3),
         (T['siege'], 'whoosh', 0.4), (T['arab'], 'horn', 0.5), (T['besiege'], 'stamp', 0.6), (T['besiege'] + 0.12, 'pop', 0.4),
         (T['drom'], 'whooshlow', 0.6), (T['warships'], 'pop', 0.5), (T['bronze'], 'clink', 0.6), (T['tube_w'], 'pop', 0.5),
         (T['rit'], 'whoosh', 0.4), (T['sources'], 'pop', 0.5), (T['suggest'] - 0.12, 'stamp', 1.0),
         (T['sys'], 'whoosh', 0.4), (T['heated'] - 0.1, 'ignite', 0.6), (T['heated'], 'pop', 0.4), (T['sealed'] + 0.25, 'clank', 0.7),
         (T['crew'] - 0.05, 'pop', 0.4), (T['pump'], 'pop', 0.4)]
    t_ = T['worked']
    while t_ < T['jet_s'] - 0.1:
        C.append((t_, 'pumpstroke', 0.45)); t_ += math.pi / (7 if t_ < T['press'] else 10)
    C += [(T['press'] - 0.15, 'riser', 0.6), (T['built'], 'creak', 0.5),
          (T['jet_s'], 'whoosh', 0.4), (T['jet_w'] - 0.05, 'hiss', 0.8), (T['lit'], 'ignite', 1.0), (T['lit'], 'roar', 0.9),
          (T['nozzle'] - 0.1, 'pop', 0.4), (T['spread'] - 0.1, 'roarlong', 0.7), (T['ignite'], 'hit', 0.8), (T['water_w'], 'pop', 0.5),
          (T['buck'], 'whoosh', 0.4), (T['water11'] - 0.1, 'whoosh', 0.5), (T['put'], 'splash', 0.8), (T['put'] + 0.05, 'hiss', 0.6),
          (T['out11'], 'roar', 1.0), (T['out11'] + 0.1, 'pop', 0.4),
          (T['rem'], 'whoosh', 0.4)]
    for key in ('sand', 'vinegar', 'urine'):
        C += [(T[key] - 0.05, 'pour', 0.55), (T[key] + 0.2, 'hiss', 0.5), (T[key], 'pop', 0.4)]
    C += [(T['later'] - 0.05, 'pop', 0.5),
          (T['rng'], 'whoosh', 0.4), (T['rng'], 'waves', 0.6), (T['calm'], 'pop', 0.5), (T['close'] - 0.05, 'pop', 0.5),
          (T['close'] + 0.3, 'hiss', 0.4), (T['close'] + 0.6, 'splash', 0.4), (T['near_w'] - 0.25, 'whooshlow', 0.5), (T['near_w'] + 0.5, 'roar', 0.5),
          (T['bul'], 'whoosh', 0.4), (T['y812'], 'stamp', 0.5), (T['captured'], 'clank', 0.5), (T['siphons'], 'pop', 0.4), (T['fuel'], 'pop', 0.4),
          (T['sput'], 'whoosh', 0.4)]
    t_ = T['sput']
    while t_ < T['work'] + 0.3:
        C.append((t_, 'pumpstroke', 0.4)); t_ += math.pi / (6 if t_ < T['make'] else 12)
    C += [(T['make'] + 0.1, 'dribble', 0.5), (T['work'], 'puff', 0.6), (T['work'] + 0.05, 'pop', 0.4),
          (T['whole_s'], 'whoosh', 0.4), (T['never'] - 0.1, 'whooshlow', 0.4), (T['whole'] - 0.15, 'thud', 0.6), (T['whole'] + 0.1, 'shimmer', 0.4)]
    for i in range(5): C.append((T['whole'] + 0.15 + i * 0.12, 'tick', 0.45))
    C += [(T['secret16'] - 0.05, 'pop', 0.6),
          (T['fin'], 'whoosh', 0.4), (T['fin'], 'roar', 0.7), (T['machine17'], 'pop', 0.6), (T['fired17'], 'thud', 0.5)]
    starts = {round(st, 3) for st, _, _, org in SCENES[1:]}
    C = [((c[0] - 0.12) if (round(c[0], 3) in starts and c[1] != 'whoosh') else c[0], c[1], c[2]) for c in C]
    cuts = {round(st, 3) for st, _, _, org in SCENES[1:] if org != 'slide'}
    C = [c for c in C if not (c[1] in ('whoosh',) and round(c[0], 3) in cuts)]
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

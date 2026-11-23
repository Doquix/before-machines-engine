"""E022 Persian yakhchal: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random, re
import numpy as np
from PIL import Image, ImageDraw
from lib import *
import lib
lib.BLEND = True
from rig import *
import props as PR
from props import tag, stamp, arrow as arrow_line
import yk
import env
import make_map as MM
from fx import smear, speed_lines, focus_lines, impact, particles
from detail import shade, light

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())
def w(p, word, n=0):
    hits = [x['t'] for x in WORDS if x['p'] == p and norm(x['w']) == norm(word)]
    return hits[n]
def S(p): return CAPS[p]['s']
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))

T = dict(
    frozen=w(0, 'frozen'), night0=w(0, 'night'), sky0=w(0, 'sky'),
    s1=S(1), deserts=w(1, 'deserts'), persia=w(1, 'Persia'),
    s2=S(2), winter=w(2, 'winter'), nights2=w(2, 'nights'), freezing2=w(2, 'freezing'),
    s3=S(3), builders=w(3, 'builders'), dug=w(3, 'dug'), long3=w(3, 'long'), shallow=w(3, 'shallow'), pools=w(3, 'pools'),
    s4=S(4), underground=w(4, 'underground'), canals=w(4, 'canals'),
    s5=S(5), raised=w(5, 'raised'), tall5=w(5, 'tall'), mud=w(5, 'mud'), wall5=w(5, 'wall'),
    s6=S(6), south=w(6, 'south'), side=w(6, 'side'),
    s7=S(7), day=w(7, 'day'), wall7=w(7, 'wall'), threw=w(7, 'threw'), shade7=w(7, 'shade'), water7=w(7, 'water'),
    s8=S(8), night8=w(8, 'night'), lost=w(8, 'lost'), heat=w(8, 'heat'),
    s9=S(9), straight=w(9, 'straight'), up=w(9, 'up'), clear=w(9, 'clear'), dry=w(9, 'dry'), sky9=w(9, 'sky'),
    s10=S(10), thin=w(10, 'thin'), skin=w(10, 'skin'), ice10=w(10, 'ice'), formed=w(10, 'formed'),
    s11=S(11), air=w(11, 'air'), likely=w(11, 'likely'), little=w(11, 'little'), above=w(11, 'above'), freezing11=w(11, 'freezing'),
    s12=S(12), workers=w(12, 'workers'), poured=w(12, 'poured'),
    s13=S(13), few=w(13, 'few'), inches13=w(13, 'inches'), water13=w(13, 'water'),
    s14=S(14), layer14=w(14, 'Layer'), layer14b=w(14, 'layer', 1),
    s15=S(15), grew=w(15, 'grew'), twenty=w(15, 'twenty'), thick=w(15, 'thick'),
    s16=S(16), cut=w(16, 'cut'), blocks=w(16, 'blocks'),
    s17=S(17), carried=w(17, 'carried'), domed=w(17, 'domed'), pit=w(17, 'pit'),
    s18=S(18), packed=w(18, 'packed'), straw=w(18, 'straw'),
    s19=S(19), domes=w(19, 'domes'), stand=w(19, 'stand'), sixty=w(19, 'sixty'), feet=w(19, 'feet'), tall19=w(19, 'tall'),
    s20=S(20), midsummer=w(20, 'midsummer'), towns=w(20, 'towns'), drank=w(20, 'drank'), sherbet=w(20, 'sherbet'),
    s21=S(21), thanks=w(21, 'thanks'), night21=w(21, 'night'), sky21=w(21, 'sky'),
    end=VO_END,
)
T['strike'] = T['cut'] + 0.04          # the pick lands on "cut"
T['strike2'] = T['blocks'] + 0.05
CAM.drift = 0.5
CAM.punch = [(T['frozen'], 0.04), (T['likely'], 0.06), (T['twenty'], 0.04), (T['strike'], 0.06), (T['sixty'], 0.04), (T['sherbet'], 0.04)]
CAM.shake = [(T['strike'], 8, 0.22), (T['strike2'], 5, 0.18)]
FLASH = [(T['strike'], 0.1, (240, 248, 255), 100)]
GROUND = 1300
NIGHTCOL = (16, 24, 56)

def bgp(base, name, par=0.5, dy=0.0):
    img = env.get(name)
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par + dy
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def ground(pn, y, col=(198, 172, 128), night=0.0):
    c = lerpc(col, (44, 46, 62), night)
    pn.rect(-400, y, 1480, 2800, fill=c)
    pn.line([(-400, y), (1480, y)], lerpc(c, INK, .4), 4, caps=False)
    rnd = random.Random(5)
    for _ in range(26):     # pebbles and cracks in the hardpan as a speed and scale reference
        x, yy = rnd.uniform(-300, 1380), rnd.uniform(y + 20, y + 600)
        pn.ell(x, yy, rnd.uniform(4, 10), rnd.uniform(2, 4), fill=shade(c, 0.18))

def night_tint(pn, a=80):
    pn.rect(-600, -600, 1680, 2600, fill=NIGHTCOL + (a,))

def thermo(pn, x, y, lvl, p=1.0, h=420):
    """Unnumbered temperature bar: a freezing line in the middle; lvl 0..1 (0.5 = freezing)."""
    if p <= 0: return
    pn.push(x, y, eoback(clamp(p)))
    pn.rect(-34, -h / 2, 34, h / 2, fill=PARCH, outline=INK, width=4, r=30)
    pn.circ(0, h / 2 + 22, 48, fill=PARCH, outline=INK, width=4)
    top = h / 2 - lvl * h
    pn.rect(-18, top, 18, h / 2 + 10, fill=(70, 130, 190), r=16)
    pn.circ(0, h / 2 + 22, 34, fill=(70, 130, 190))
    pn.line([(-60, 0), (60, 0)], RUST, 6, caps=False)
    pn.text(76, 0, 'FREEZING', 30, INK, 'Black', 'lm', True)
    pn.pop()

def breath(pn, x, y, t, f=1, seed=0):
    ph = (t * 0.7 + seed) % 1.0
    if ph > 0.6: return
    u = ph / 0.6
    for i in range(3):
        pn.circ(x + f * (10 + 40 * u + i * 14), y - 10 * u - i * 6, 8 + 14 * u + i * 3, fill=(230, 236, 246, int(110 * (1 - u))))

def fill_ok(pn, t): pass

# ======================= scenes =======================
# Shot 1 (insert, high angle): the night pool, frost racing in from the rim on the first frame
POOL1 = dict(x0=-60, x1=1140, yf=520, yn=1340, skew=90)
def frost_at(t, t0):
    return clamp(0.18 + 0.82 * eo3(P(t, t0, 2.0)))
def sc_pool_open(base, pn, t, loop=False):
    t0 = T['s21'] if loop else 0.0
    # the first frame already has crystals racing in from the edges; frozen solid by "frozen", glint on "frozen"
    fr = lerp(0.24, 0.96, eo3(P(t, t0, (T['night0'] + 0.3) if not loop else 1.6)))
    tg = T['frozen'] if not loop else T['night21']
    base.paste(bg_cam(PR.ice_fill_image(fr, -40, -40, 1120, 1960, 5), 1.0))
    PR.ice_surface(pn, -40, -40, 1120, 1960, freeze=fr, t=t, seed=5, fill=False, glint=P(t, tg - 0.1, 0.7) if t > tg - 0.1 else None)
def cam_pool_open(t, sc_, ox, oy): return camfocus(lerp(1.08, 1.0, eio(P(t, 0, 2.6))) * sc_, 540, 930, 540, 930, ox, oy)
def sc_loop(base, pn, t): sc_pool_open(base, pn, t, loop=True)
def cam_loop(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.08, eio(P(t, T['s21'], 1.8))) * sc_, 540, 930, 540, 930, ox, oy)

# Shot 2 (EWS, low angle): the ice house under the stars ("sky")
def sc_ews_night(base, pn, t):
    bgp(base, 'yknight', 0.3)
    ground(pn, 1180, night=1.0)
    PR.yakhchal_dome(pn, 760, 1180, 22, night=1.0)
    PR.shade_wall(pn, -40, 560, 1180, 22, h=9.0, night=1.0)
    PR.ice_pool(pn, -60, 560, 1210, 1330, skew=30, water=1.0, ice=0.6, stars=30, t=t, night=1.0)
def cam_ews_night(t, sc_, ox, oy): return camfocus(sc_, 540, 960, 540, 960, ox, oy)

# Shot 3 (graphic): map of Persia, zoom to the desert towns, pin on Meybod
_MAP = {}
def map_img():
    if 'ir' not in _MAP: _MAP['ir'] = Image.open('map_ir.png').convert('RGB')
    return _MAP['ir']
MAPC = (54.5, 30.6, 13.0)
def geo_xy(lon, lat):
    lon_px, lat_px = MM.geo(*MAPC)
    return 540 + (lon - MAPC[0]) / lon_px, 960 - (lat - MAPC[1]) / lat_px
def mclamp(z, fx_, fy, tx, ty):
    fx_ = min(max(fx_, tx / z), W - (W - tx) / z); fy = min(max(fy, ty / z), H - (H - ty) / z)
    return fx_, fy
def map_view(z, fx_, fy, tx, ty):
    a = 2 / z
    return map_img().transform((W, H), Image.AFFINE, (a, 0, 2 * fx_ - tx * a, 0, a, 2 * fy - ty * a), Image.BILINEAR)
def pin(pn, x, y, t, t0, col=RUST):
    if t < t0: return
    u = t - t0; drop = 1 - spring(u, 1.5, 7); py = y - 220 * drop
    rp = eo3(P(u, 0.12, 0.6))
    if 0 < rp < 1: pn.circ(x, y, 24 + 90 * rp, outline=col + (int(255 * (1 - rp)),), width=6)
    pn.poly([(x, py), (x - 22, py - 44), (x + 22, py - 44)], fill=col, outline=INK, width=3)
    pn.circ(x, py - 56, 25, fill=col, outline=INK, width=4); pn.circ(x, py - 56, 9, fill=PARCH)
def label(pn, x, y, txt, sz, a=1.0, col=(60, 48, 34)):
    if a <= 0: return
    pn.text(x, y, txt, sz, col + (int(230 * a),), 'Black', 'mm', True, sp=4)
MEYBOD = (54.02, 32.25)
KAVIR = (54.8, 34.4); LUT = (58.6, 30.6)
def desert_patch(pn, cx, cy, rx, ry, a, seed):
    if a <= 0: return
    rnd = random.Random(seed)
    pts = [(cx + rx * (0.8 + 0.25 * rnd.random()) * math.cos(th), cy + ry * (0.8 + 0.25 * rnd.random()) * math.sin(th)) for th in np.linspace(0, 6.28, 18)]
    pn.poly(pts, fill=(196, 150, 86, int(110 * a)))
    for _ in range(int(60 * a)):
        u, v = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8)
        if u * u + v * v < 0.64: pn.circ(cx + u * rx, cy + v * ry, 2.6, fill=(150, 104, 50, int(200 * a)))
def sc_map(base, pn, t):
    zp = eio(P(t, T['s1'], 1.4)); z = lerp(1.0, 1.15, zp)
    f = geo_xy(*MEYBOD); f0 = geo_xy(54.5, 31.0)
    fx_, fy = lerp(f0[0], f[0], zp), lerp(f0[1], f[1], zp); tx, ty = 400, 860
    fx_, fy = mclamp(z, fx_, fy, tx, ty)
    base.paste(map_view(z, fx_, fy, tx, ty))
    def xy(lon, lat):
        px, py = geo_xy(lon, lat); return tx + (px - fx_) * z, ty + (py - fy) * z
    a_d = P(t, T['deserts'] - 0.05, 0.4)
    desert_patch(pn, *xy(*KAVIR), 200 * z, 90 * z, a_d, 3)
    desert_patch(pn, *xy(57.9, 30.6), 110 * z, 170 * z, a_d, 5)
    label(pn, *xy(54.9, 34.4), 'DASHT E KAVIR', 34, a_d)
    lx_, ly_ = xy(57.9, 30.6); label(pn, min(lx_, 900), ly_, 'DASHT E LUT', 30, a_d)
    label(pn, 540, 330, 'PERSIA', 110, P(t, T['persia'] - 0.05, 0.3))
    pin(pn, *xy(*MEYBOD), t, T['persia'] + 0.25)
    label(pn, xy(*MEYBOD)[0], xy(*MEYBOD)[1] + 60, 'MEYBOD', 42, P(t, T['persia'] + 0.4, 0.3))
    label(pn, *xy(52.0, 27.4), 'PERSIAN GULF', 30, 0.8, col=(200, 214, 220))

# Shot 4 (MCU): the Keeper on a winter night, breath in the air, thermometer settles at freezing
def sc_cold(base, pn, t):
    bgp(base, 'yknight', 0.3)
    p = pose('cross', head=4 + 1.5 * math.sin(t * 9) * (P(t, T['nights2'], 0.2)))   # shiver: small head tremor
    J = figure(pn, 330, 2130, 4.6, 1, p, 'pkeeper', 'worried' if t > T['nights2'] else 'neutral', look=(0.8, -0.4), blink=blink_at(t, 0.2))
    hx, hy = 330 + J['head'][0] * 4.6, 2130 + J['head'][1] * 4.6
    breath(pn, hx + 120, hy + 70, t, 1, 0.3)
    night_tint(pn, 60)
    lvl = lerp(0.9, 0.52, eio(P(t, T['winter'], T['freezing2'] - T['winter'] + 0.2)))
    thermo(pn, 860, 760, lvl, P(t, T['s2'] + 0.05, 0.3))
    tag(pn, 820, 1120, 'AROUND 0 °C', 48, pop(t, T['freezing2']), rot_=3)

# Shot 5 (FS): a builder digs the pool with a spade, winter day
def sc_dig(base, pn, t):
    bgp(base, 'ykday', 0.4)
    ground(pn, GROUND)
    # the dug basin grows as he works (rim line in front of him)
    g = eio(P(t, T['s3'], T['pools'] - T['s3']))
    pn.poly([(560, GROUND + 30), (560 + 520 * g, GROUND + 30), (560 + 540 * g, GROUND + 90), (540, GROUND + 90)], fill=(150, 124, 92), outline=INK, width=3)
    ph = ((t - T['s3']) / 0.9) % 1.0
    push = eio(clamp(ph / 0.45)) if ph < 0.45 else 1 - eio(clamp((ph - 0.45) / 0.55))
    yk.worker_spade(pn, 420, GROUND, 2.9, 'yakh3', push=push, expr='determined', t=t)
    if 0.42 < ph < 0.7: particles(pn, 'dust', 760, GROUND + 40, t, t - (ph - 0.42) * 0.9, 0.8, seed=int(t), ground=GROUND + 60)
def cam_dig(t, sc_, ox, oy): return camfocus(sc_, 540, 900, 540, 900, ox, oy)

# Shot 6 (WS, high angle): the long shallow pool laid out beside the wall line
def sc_pool_high(base, pn, t):
    base.paste(Image.new('RGBA', (W, H), (190, 164, 120, 255)))
    pn.rect(-100, -100, 1180, 2100, fill=(198, 172, 128))
    rnd = random.Random(7)
    for _ in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H); pn.ell(x, y, 22, 4, fill=(184, 158, 116))
    a = eoback(P(t, T['pools'] - 0.05, 0.35))
    PR.ice_pool(pn, 120, lerp(400, 1010, a), 560, 1180, skew=-60, water=0.0, night=0.0)
    figure(pn, 330, 1290, 1.0, 1, pose('idle'), 'yakh3', 'neutral', blink=blink_at(t, 1.0))
    yk.worker_spade(pn, 860, 1290, 1.0, 'yakh1', push=0.3)
    tag(pn, 560, 400, '30 TO 50 cm DEEP', 54, pop(t, T['pools'] + 0.15), rot_=-3)

# Shot 7 (graphic): qanat section, water runs downhill to the pool
def sc_qanat(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    fl = eio(P(t, T['s4'], 1.2))
    R = PR.qanat_section(pn, 40, 1040, 1040, flow=fl, t=t, hill=380)
    ox_, oy_ = R['outlet']
    PR.ice_pool(pn, 900, 1060, 1030, 1070, skew=10, water=P(t, T['canals'], 0.6), night=0.0)
    tag(pn, 540, 470, 'QANAT', 64, pop(t, T['underground']), rot_=-3, sub='UNDERGROUND CANAL')
    tag(pn, 300, 1200, 'WATER FLOWS DOWNHILL', 40, pop(t, T['canals'] + 0.1), rot_=2)

# Shot 8 (WS, low angle, tilt up): the shade wall rises, a small figure at its foot
def sc_wall(base, pn, t):
    u = eio(P(t, T['s5'] + 0.1, T['wall5'] - T['s5'] + 0.2))
    dy = lerp(-260, 220, u)          # tilt: the scene moves down as the camera looks up
    bgp(base, 'ykday', 0.25, dy=-dy * 0.4)
    pn.push(0, dy, 1)
    ground(pn, 1500)
    PR.shade_wall(pn, -60, 1140, 1500, 120, h=9.0)
    figure(pn, 760, 1500, 1.55, -1, pose('look', head=-10), 'pkeeper', 'surprised', look=(0, -1), blink=blink_at(t, 0.5))
    pn.pop()
    tag(pn, 300, 300, 'UP TO ~10 m', 56, pop(t, T['tall5'] + 0.05), rot_=-3, sub='MUD BRICK')

# Shot 9 (graphic, overhead plan): wall on the south side, pool on the north, compass
def sc_plan(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    a = eoback(P(t, T['s6'], 0.35))
    pn.rect(140, 900, 940, 900 + 70 * a, fill=(204, 170, 122), outline=INK, width=4)
    PR.ice_pool(pn, 160, 920, 540, 870, skew=0, water=0.0, night=0.0)
    label(pn, 540, 705, 'POOL', 48, P(t, T['s6'] + 0.1, 0.3), col=(40, 30, 22))
    label(pn, 360, 1020, 'SHADE WALL', 48, P(t, T['south'] - 0.1, 0.3), col=(40, 30, 22))
    # compass
    pn.push(880, 330, 1.0)
    pn.circ(0, 0, 70, fill=PARCH, outline=INK, width=4)
    pn.poly([(0, -62), (-16, 0), (16, 0)], fill=RUST, outline=INK, width=3); pn.poly([(0, 62), (-16, 0), (16, 0)], fill=PARCH, outline=INK, width=3)
    pn.text(0, -96, 'N', 44, INK, 'Black', 'mm', True); pn.text(0, 100, 'S', 44, INK, 'Black', 'mm', True)
    pn.pop()
    if t > T['south']:
        arrow_line(pn, (800, 1200), (800, 990), RUST, 10, 34, p=eo3(P(t, T['south'], 0.4)))
        label(pn, 760, 1240, 'SUN FROM THE SOUTH', 34, P(t, T['south'] + 0.2, 0.3), col=(150, 54, 36))

# Shot 10 (graphic, end on section): by day the wall throws its shadow over the pool
def sc_shade(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    gy = 1180
    pn.rect(-100, gy, 1180, 1500, fill=(198, 172, 128)); pn.line([(-100, gy), (1180, gy)], INK, 4)
    wx = 470; s = 62
    # low winter sun in the south sky (left), rising a little then sinking
    u = eio(P(t, T['s7'], T['water7'] - T['s7'] + 0.6))
    sx, sy = lerp(150, 250, u), 520 - 90 * math.sin(u * math.pi)
    pn.circ(sx, sy, 56, fill=(250, 210, 90), outline=INK, width=4)
    for i in range(10):
        a_ = i * 36 + t * 30
        pn.line([(sx + 70 * math.cos(math.radians(a_)), sy + 70 * math.sin(math.radians(a_))), (sx + 92 * math.cos(math.radians(a_)), sy + 92 * math.sin(math.radians(a_)))], (240, 180, 60), 6)
    # shadow wedge from the wall top along the ray
    top = (wx, gy - 9 * s)
    dx, dy = top[0] - sx, top[1] - sy; k_ = (gy - top[1]) / dy
    tip = (top[0] + dx * k_, gy)
    sh = eio(P(t, T['wall7'], 0.6))
    pn.poly([(wx, gy), top, (lerp(wx, tip[0], sh), lerp(top[1], gy, sh))], fill=(40, 40, 70, 90))
    # pool on the north side (right)
    pn.rect(wx + 60, gy, wx + 560, gy + 40, fill=(90, 130, 170), outline=INK, width=3)
    PR.wall_end_section(pn, wx, gy, s, h=9.0, base=2.0, topw=0.6, f=1)
    # rays: blocked by the wall
    for i in range(5):
        a0 = (sx + 60, sy + 20 + i * 30)
        pn.line([a0, (lerp(a0[0], wx - 20, 0.98), lerp(a0[1], top[1] + 40 + i * 60, 0.98))], (240, 180, 60, 150), 4, caps=False)
    label(pn, 300, 360, 'LOW WINTER SUN', 34, P(t, T['day'], 0.3), col=(120, 70, 20))
    label(pn, wx + 310, gy + 90, 'POOL IN SHADE', 40, P(t, T['shade7'], 0.3))
    tag(pn, 760, 400, 'SHADE ALL DAY', 54, pop(t, T['shade7'] + 0.1), rot_=3)

# Shot 11 (WS, night): the pool by the wall, heat leaves straight up
def sc_heat(base, pn, t):
    bgp(base, 'yknight', 0.3)
    ground(pn, 1180, night=1.0)
    PR.shade_wall(pn, -60, 1140, 1180, 34, h=9.0, night=1.0)
    PR.ice_pool(pn, -40, 1120, 1210, 1400, skew=40, water=1.0, ice=0.0, stars=40, t=t, night=1.0)
    PR.radiation_arrows(pn, 80, 1000, 1290, 700, p=eio(P(t, T['lost'], 1.0)), n=6, t=t)
    tag(pn, 540, 470, 'HEAT RADIATES UP', 54, pop(t, T['heat']), rot_=-3)

# Shot 12 (EWS, tilt up into the stars): the arrows follow up into a clear, dry sky
def sc_sky(base, pn, t):
    u = eio(P(t, T['s9'], T['sky9'] - T['s9'] + 0.3))
    bgp(base, 'yknightsky', 0.2, dy=lerp(0, -120, u))
    pn.push(0, lerp(0, 700, u), 1)
    pn.rect(-100, 1500, 1180, 2600, fill=(30, 34, 52))
    PR.ice_pool(pn, 160, 920, 1520, 1600, skew=20, water=1.0, ice=0.1, night=1.0)
    PR.radiation_arrows(pn, 200, 880, 1500, -200, p=1.0, n=5, t=t)
    pn.pop()
    tag(pn, 540, 1180, 'NO CLOUDS, DRY AIR', 50, pop(t, T['dry']), rot_=3)

# Shot 13 (ECU): crystals branch across the water
def sc_crystals(base, pn, t):
    base.paste(Image.new('RGBA', (W, H), (22, 34, 66, 255)))
    PR.stars(pn, 21, 60, 0, H, t)
    g = eo3(P(t, T['s10'], T['formed'] - T['s10'] + 0.6))
    rnd = random.Random(5)
    for k in range(9):
        x0, y0 = rnd.uniform(-60, 1140), rnd.choice((-40, 1960, rnd.uniform(0, 1900)))
        a0 = math.atan2(960 - y0, 540 - x0) + rnd.uniform(-0.5, 0.5)
        L_ = 900 * g * rnd.uniform(0.6, 1.0)
        ex, ey = x0 + math.cos(a0) * L_, y0 + math.sin(a0) * L_
        pn.line([(x0, y0), (ex, ey)], (236, 246, 252, 230), 5, caps=False)
        for j in range(1, int(14 * g)):
            q = j / 14; px, py = lerp(x0, ex, q), lerp(y0, ey, q)
            for sd in (-1, 1):
                b = a0 + sd * 1.0; bl = 90 * (1 - q * 0.6) * g
                pn.line([(px, py), (px + math.cos(b) * bl, py + math.sin(b) * bl)], (214, 236, 248, 200), 3, caps=False)
    tag(pn, 540, 1180, 'A SKIN OF ICE', 56, pop(t, T['skin'] + 0.1), rot_=-2)

# Shot 14 (CU): the Keeper, thermometer just above freezing, LIKELY stamp
def sc_likely(base, pn, t):
    bgp(base, 'yknight', 0.2)
    ex = 'surprised' if t > T['likely'] - 0.05 else 'thinking'
    figure(pn, 330, 2550, 6.4, 1, pose('idle', head=3), 'pkeeper', ex, look=(1, -0.2), blink=blink_at(t, 0.7))
    night_tint(pn, 50)
    thermo(pn, 860, 760, lerp(0.5, 0.58, eio(P(t, T['above'] - 0.1, 0.5))), 1.0)
    stamp(pn, 760, 1150, 'LIKELY', t - T['likely'], 110)

# Shot 15 (AS, dusk): a worker opens the channel and water spills over the ice
def sc_pour(base, pn, t):
    bgp(base, 'ykdawn', 0.3)
    ground(pn, GROUND, (160, 134, 110))
    PR.ice_pool(pn, 520, 1180, GROUND + 10, GROUND + 180, skew=30, water=1.0, ice=1.0, night=0.4)
    fl = eio(P(t, T['poured'] - 0.1, 0.8))
    if fl > 0:
        pn.poly([(560, GROUND + 60), (560 + 560 * fl, GROUND + 50), (560 + 580 * fl, GROUND + 150), (540, GROUND + 160)], fill=(70, 120, 170, 170))
    pu = eio(P(t, T['workers'], 0.5)) if t < T['poured'] + 0.3 else 1 - eio(P(t, T['poured'] + 0.3, 0.6))
    yk.worker_spade(pn, 400, GROUND + 40, 3.8, 'yakh3', push=pu, expr='determined', t=t)
    if t > T['poured']: particles(pn, 'splash', 600, GROUND + 90, t, T['poured'], 0.8, seed=4, ang=-0.4, cone=1.2)
def cam_pour(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 980, ox, oy)

# Shot 16 (insert, top view): the new layer spreads over the ice
def sc_spread(base, pn, t):
    base.paste(Image.new('RGBA', (W, H), (40, 46, 70, 255)))
    PR.ice_pool(pn, -80, 1160, 380, 1340, skew=40, water=1.0, ice=1.0, night=0.6)
    sp = eio(P(t, T['s13'], 1.3))
    pts = [(-80 + 40, 380), (lerp(-40, 1200, sp), 380), (lerp(-80, 1160, sp), 1340), (-80, 1340)]
    pn.poly(pts, fill=(70, 120, 170, 150))
    for i in range(7):
        x = lerp(-60, 1180, sp) - i * 30
        pn.line([(x, 400 + i * 130), (x - 50, 470 + i * 130)], (220, 236, 250, 160), 4)
    tag(pn, 540, 300, '5 TO 10 cm A NIGHT', 52, pop(t, T['inches13']), rot_=-3)

# Shot 17 (graphic): layers stack on a ruler, to about 50 cm
def sc_layers(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    n = 0.0
    beats = [T['layer14'], T['layer14b'], T['grew'], T['about'] if 'about' in T else T['grew'] + 0.4, T['twenty'] - 0.2, T['twenty']]
    for b in beats:
        n += eo3(P(t, b, 0.25))
    PR.pool_layers_section(pn, 180, 760, 640, 900, layers=n, pour=0.0, max_layers=6)
    tag(pn, 540, 400, 'LAYER BY LAYER', 50, pop(t, T['layer14'] + 0.05), rot_=-3)
    tag(pn, 760, 1230, 'ABOUT 50 cm', 60, pop(t, T['twenty'] + 0.05), rot_=3, sub='ABOUT 20 INCHES')

# Shot 18 (FS, dawn): pick wind up and strike; chips fly
def sc_cut(base, pn, t):
    bgp(base, 'ykdawn', 0.3)
    ground(pn, GROUND, (160, 134, 110))
    PR.ice_pool(pn, -100, 1180, GROUND - 4, GROUND + 260, skew=0, water=0.0, ice=1.0, crack=P(t, T['strike'], 0.4), night=0.3)
    # anticipation from the start of the line, drive onto the measured word
    if t < T['strike'] - 0.16: sw = -0.0 + 0.0 * t
    sw = 0.0
    a0 = T['strike'] - 0.55; d0 = T['strike'] - 0.17
    if t < a0: sw = 0.35 * eio(P(t, T['s16'], a0 - T['s16']))
    elif t < d0: sw = lerp(0.35, 0.0, eio(P(t, a0, d0 - a0)))
    elif t < T['strike']: sw = ei2(P(t, d0, T['strike'] - d0))
    elif t < T['strike'] + 0.24: sw = 1.0
    else: sw = lerp(1.0, 0.4, eio(P(t, T['strike'] + 0.24, 0.5)))
    J = yk.worker_pick(pn, 380, GROUND + 60, 3.0, 'yakh1', sw=sw, expr='determined', t=t)
    if t >= T['strike']:
        particles(pn, 'debris', 760, GROUND + 70, t, T['strike'], 1.0, seed=3, col=(230, 244, 252), ground=GROUND + 140)
        impact(pn, 760, GROUND + 70, t, T['strike'], 0.8, seed=2)
def cam_cut(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 980, ox, oy)

# Shot 19 (insert): cracks run across the sheet into blocks
def sc_blocks(base, pn, t):
    base.paste(Image.new('RGBA', (W, H), (60, 64, 86, 255)))
    PR.ice_pool(pn, -120, 1200, 420, 1300, skew=60, water=0.0, ice=1.0, crack=eio(P(t, T['blocks'] - 0.15, 0.5)), night=0.3)
    tag(pn, 540, 300, 'CUT INTO BLOCKS', 52, pop(t, T['blocks']), rot_=-3)

# Shot 20 (WS, dawn): a worker carries a block to the dome's north door
def sc_carry(base, pn, t):
    bgp(base, 'ykdawn', 0.3)
    ground(pn, GROUND - 40, (160, 134, 110))
    PR.yakhchal_dome(pn, 830, GROUND - 40, 34, night=0.25)
    u = t - T['s17']
    x = lerp(160, 560, eio(clamp(u / 2.0)))
    yk.worker_carry(pn, x, GROUND - 30, 1.7, 'yakh2', walk=u * 1.3, t=t)
    tag(pn, 300, 480, 'NORTH DOOR', 46, pop(t, T['domed'] + 0.1), rot_=-3, sub='SLOPED FOR THE ICE')

# Shot 21 (graphic, section): courses of ice, each capped with straw
def sc_pack(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    fl = eio(P(t, T['s18'] - 0.1, 1.1))
    PR.yakhchal_section(pn, 540, 1080, 40, fill=fl, layers=7, straw=True, cold=0.7)
    tag(pn, 260, 1500, 'STRAW', 60, pop(t, T['straw']), rot_=-4, string_to=(440, 1200))
    tag(pn, 800, 400, 'ICE PIT', 52, pop(t, T['packed']), rot_=3, sub='ABOUT 5 TO 6 m DEEP')

# Shot 22 (EWS, low angle, pull out): the dome towers over a small Keeper
def sc_dome(base, pn, t):
    bgp(base, 'ykday', 0.3)
    ground(pn, 1320)
    PR.yakhchal_dome(pn, 560, 1320, 58)
    PR.shade_wall(pn, 1020, 1600, 1320, 58, h=9.0)
    figure(pn, 720, 1330, 0.62, -1, pose('look', head=-8), 'pkeeper', 'surprised', look=(0, -1), blink=blink_at(t, 0.4))
    # scale bar: dome height
    hp_ = eio(P(t, T['stand'], 0.6))
    if hp_ > 0:
        pn.line([(120, 1320), (120, 1320 - 16 * 58 * hp_)], RUST, 8, caps=False)
        for yy in (1320, 1320 - 16 * 58 * hp_): pn.line([(96, yy), (144, yy)], RUST, 8, caps=False)
    tag(pn, 300, 760, '15 TO 18 m', 60, pop(t, T['sixty']), rot_=-4, sub='SOURCES DIFFER')
def cam_dome(t, sc_, ox, oy): return camfocus(lerp(1.35, 1.0, eio(P(t, T['s19'], 2.4))) * sc_, 560, 900, 540, 900, ox, oy)

# Shot 23 (MS, summer): the Keeper lifts a bowl of iced sherbet at the dome's south door
def sc_summer(base, pn, t):
    bgp(base, 'yksummer', 0.3)
    ground(pn, 1700, (226, 196, 140))
    PR.yakhchal_dome(pn, 760, 1700, 64)
    lift = eio(P(t, T['drank'] - 0.1, 0.5))
    yk.keeper_bowl(pn, 400, 1780, 4.2, out='pkeeper_s', expr='happy' if t > T['towns'] else 'neutral', t=t, lift=lift)
    for i in range(6):   # heat shimmer lines
        y = 1100 + i * 60 + 10 * math.sin(t * 3 + i)
        pn.line([(600 + 30 * math.sin(t * 2 + i), y), (700 + 30 * math.sin(t * 2 + i), y - 6)], (255, 255, 255, 60), 4)
    tag(pn, 780, 470, 'MIDSUMMER', 56, pop(t, T['midsummer']), rot_=3)
    tag(pn, 780, 640, 'ICED SHERBET', 52, pop(t, T['sherbet'] + 0.05), rot_=-3)

SCENES = [
    (0.0, sc_pool_open, cam_pool_open, None),
    (T['night0'] - 0.05, sc_ews_night, cam_ews_night, None),
    (T['s1'], sc_map, None, None),
    (T['s2'], sc_cold, None, None),
    (T['s3'], sc_dig, cam_dig, None),
    (T['pools'] - 0.12, sc_pool_high, None, None),
    (T['s4'], sc_qanat, None, None),
    (T['s5'], sc_wall, None, None),
    (T['s6'], sc_plan, None, None),
    (T['s7'], sc_shade, None, 'slide'),           # chapter: how it works
    (T['s8'], sc_heat, None, 'dissolve'),         # day to night
    (T['s9'], sc_sky, None, None),
    (T['s10'], sc_crystals, None, None),
    (T['s11'], sc_likely, None, None),
    (T['s12'], sc_pour, cam_pour, 'slide'),       # chapter: the nightly work
    (T['s13'], sc_spread, None, None),
    (T['s14'], sc_layers, None, None),
    (T['s16'], sc_cut, cam_cut, None),
    (T['blocks'] - 0.2, sc_blocks, None, None),
    (T['s17'], sc_carry, None, None),
    (T['s18'], sc_pack, None, None),
    (T['s19'], sc_dome, cam_dome, None),
    (T['s20'], sc_summer, None, 'slide'),         # chapter: time jump to summer
    (T['s21'], sc_loop, cam_loop, 'dissolve'),    # back to the opening frame
]
HUD = {}
SLIDE = 0.35
DISS = 0.3

def scene_idx(t): return max(i for i, s in enumerate(SCENES) if s[0] <= t)

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
STOP = set('a an the of on in to and is it its was had his he them then that this did let at into off out up how here now for like even just according so were could with each by'.split())
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

def cues():
    C = [(0.0, 'frost', 0.9), (0.0, 'wind', 0.5), (T['frozen'], 'crack', 0.5), (T['night0'] - 0.05, 'shimmer', 0.4),
         (T['s1'], 'paper', 0.4), (T['deserts'], 'pop', 0.4), (T['persia'], 'pop', 0.5), (T['persia'] + 0.3, 'thud', 0.5),
         (T['s2'] - 0.12, 'wind', 0.6), (T['s2'] + 0.05, 'pop', 0.4), (T['freezing2'], 'pop', 0.5),
         (T['s3'] - 0.12, 'dig', 0.6), (T['dug'], 'dig', 0.6), (T['shallow'], 'dig', 0.6), (T['pools'], 'pop', 0.4), (T['pools'] + 0.15, 'pop', 0.4),
         (T['s4'] - 0.12, 'trickle', 0.6), (T['underground'], 'pop', 0.5), (T['canals'], 'pour', 0.5),
         (T['s5'], 'rumble', 0.4), (T['raised'], 'thud', 0.5), (T['mud'], 'thud', 0.5), (T['tall5'] + 0.05, 'pop', 0.5),
         (T['s6'], 'paper', 0.4), (T['south'], 'pop', 0.4), (T['south'] + 0.2, 'swish', 0.4),
         (T['day'], 'chime', 0.3), (T['shade7'] + 0.1, 'pop', 0.5),
         (T['s8'] - 0.12, 'wind', 0.6), (T['lost'], 'riser', 0.5), (T['heat'], 'pop', 0.5),
         (T['straight'], 'shimmer', 0.5), (T['dry'], 'pop', 0.4),
         (T['s10'] - 0.1, 'frost', 0.9), (T['skin'] + 0.1, 'pop', 0.4),
         (T['likely'], 'stamp', 0.9), (T['s11'], 'wind', 0.4),
         (T['workers'], 'dig', 0.5), (T['poured'] - 0.1, 'pour', 0.8), (T['poured'], 'splash', 0.5),
         (T['s13'], 'slosh', 0.6), (T['inches13'], 'pop', 0.5),
         (T['layer14'] + 0.05, 'pop', 0.4), (T['twenty'] + 0.05, 'pop', 0.5),
         (T['strike'] - 0.2, 'swish', 0.6), (T['strike'], 'crack', 1.0), (T['strike'] + 0.01, 'clink', 0.5), (T['strike2'], 'crack', 0.7),
         (T['blocks'], 'pop', 0.4), (T['s17'], 'footsteps', 0.6), (T['domed'] + 0.1, 'pop', 0.4),
         (T['s18'] - 0.1, 'rustle', 0.6), (T['straw'], 'pop', 0.5), (T['packed'], 'thud', 0.4),
         (T['stand'], 'riser', 0.4), (T['sixty'], 'thud', 0.7), (T['sixty'] + 0.02, 'pop', 0.4),
         (T['midsummer'], 'pop', 0.4), (T['drank'], 'clink', 0.6), (T['sherbet'] + 0.05, 'pop', 0.4),
         (T['s21'] - 0.12, 'frost', 0.8), (T['s21'] - 0.12, 'wind', 0.4)]
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
        for n in range(a, b): out.write(frame(n / FPS).tobytes())
    elif mode == 'T':
        for k, v in sorted(T.items(), key=lambda x: x[1]): print(f'{v:6.2f} {k}')
    elif mode == 'cues': cues()

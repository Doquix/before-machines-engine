"""E023 Caesar's double walls at Alesia: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T
Screen direction: the town and its Gauls on the LEFT (inside), the relief army on the RIGHT (outside)."""
import json, sys, math, random, re
import numpy as np
from PIL import Image, ImageDraw
import lib
lib.BLEND = True
from lib import *
from rig import *
import rig
rig.DEPTH_IK = True
import props as PR
from props import tag, stamp, arrow as arrow_line
import al
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
    miles0=w(0, 'miles'), wall0=w(0, 'wall'),
    s1=S(1), trap=w(1, 'trap'), hill1=w(1, 'hill'),
    s2=S(2), n52=w(2, '52'), caesar2=w(2, 'Caesar'), cornered=w(2, 'cornered'), army2=w(2, 'army'),
    s3=S(3), hilltop=w(3, 'hilltop'), france=w(3, 'France'),
    s4=S(4), judged=w(4, 'judged'), strong=w(4, 'strong'), storm=w(4, 'storm'),
    s5=S(5), ringed=w(5, 'ringed'), instead=w(5, 'instead'),
    s6=S(6), deep=w(6, 'deep'), ditch=w(6, 'ditch'),
    s7=S(7), rampart=w(7, 'rampart'), twelve=w(7, 'twelve'), high=w(7, 'high'),
    s8=S(8), wooden=w(8, 'wooden'), tower=w(8, 'tower'), eighty=w(8, 'eighty'),
    s9=S(9), riders=w(9, 'riders'), slipped=w(9, 'slipped'), night9=w(9, 'night'), help=w(9, 'help'),
    s10=S(10), answer=w(10, 'answer'), second=w(10, 'second'), facing=w(10, 'facing'), outward=w(10, 'outward'),
    s11=S(11), thirteen=w(11, 'thirteen'), around=w(11, 'around'),
    s12=S(12), legions=w(12, 'legions'), between=w(12, 'between'), rings=w(12, 'rings'),
    s13=S(13), both=w(13, 'both'), buried=w(13, 'buried'), traps=w(13, 'traps'),
    s14=S(14), sharpened=w(14, 'sharpened'), branches=w(14, 'branches'),
    s15=S(15), hidden=w(15, 'hidden'), pits=w(15, 'pits'), stakes=w(15, 'stakes'),
    s16=S(16), iron=w(16, 'iron'), hooks=w(16, 'hooks'), wood=w(16, 'wood'),
    s17=S(17), relief=w(17, 'relief'), came=w(17, 'came'),
    s18=S(18), hit18=w(18, 'hit'), outer=w(18, 'outer'),
    s19=S(19), town19=w(19, 'town'), inner=w(19, 'inner'),
    s20=S(20), same=w(20, 'same'), time20=w(20, 'time'),
    s21=S(21), bent=w(21, 'bent'), held=w(21, 'held'),
    s22=S(22), leader=w(22, 'leader'), verc=w(22, 'Vercingetorix'), surrendered=w(22, 'surrendered'),
    s23=S(23), came23=w(23, 'came'), miles23=w(23, 'miles'), wall23=w(23, 'wall'),
    end=VO_END,
)
T['strike'] = T['ditch'] + 0.02            # the dolabra bites on "ditch"
CAM.drift = 0.5
CAM.punch = [(T['miles0'], 0.04), (T['strong'], 0.04), (T['thirteen'], 0.06), (T['hooks'], 0.04), (T['bent'], 0.05), (T['surrendered'], 0.04)]
CAM.shake = [(T['strike'], 6, 0.18), (T['hit18'], 8, 0.3), (T['bent'], 10, 0.3)]
FLASH = [(T['bent'], 0.1, (255, 236, 200), 100)]
GROUND = 1300

def bgp(base, name, par=0.5, dy=0.0, dx=0.0):
    img = env.get(name)
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par + dx; oy = CAM.oy * par + dy
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def ground(pn, y, col=(140, 150, 86), night=0.0, dusk=0.0):
    c = lerpc(lerpc(col, (98, 96, 62), dusk), (34, 42, 50), night)
    pn.rect(-400, y, 1480, 2800, fill=c)
    pn.line([(-400, y), (1480, y)], lerpc(c, INK, .4), 4, caps=False)
    rnd = random.Random(5)
    for _ in range(40):   # grass tufts and stones as scale reference
        x, yy = rnd.uniform(-300, 1380), rnd.uniform(y + 20, y + 600)
        pn.line([(x, yy), (x - 4, yy - 12)], shade(c, 0.25), 2.4); pn.line([(x + 4, yy), (x + 6, yy - 10)], shade(c, 0.25), 2.4)

def night_tint(pn, a=70): pn.rect(-600, -600, 1680, 2600, fill=(16, 24, 56, a))
def label(pn, x, y, txt, sz, a=1.0, col=(60, 48, 34)):
    if a <= 0: return
    pn.text(x, y, txt, sz, col + (int(230 * a),), 'Black', 'mm', True, sp=4)

# ---------------- the site plan (overhead): Mont Auxois, rivers, both rings ----------------
PC = (540, 860); KM = 118.0
def _ring(rk, seed, n=90):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    pts = []
    for i in range(n + 1):
        a = i / n * 2 * math.pi
        r = rk * (1 + 0.06 * math.sin(2 * a + ph[0]) + 0.04 * math.sin(3 * a + ph[1]) + 0.03 * math.sin(5 * a + ph[2]))
        pts.append((PC[0] + math.cos(a - 2.2) * r * KM * 1.12, PC[1] + math.sin(a - 2.2) * r * KM * 0.92))
    return pts
INNER = _ring(2.35, 3); OUTER = _ring(3.3, 7)
def partial(pts, p):
    if p <= 0: return []
    n = len(pts) - 1; m = p * n; k = int(m)
    out = pts[:k + 1]
    if k < n: out = out + [(lerp(pts[k][0], pts[k + 1][0], m - k), lerp(pts[k][1], pts[k + 1][1], m - k))]
    return out
def ring_draw(pn, pts, p, col, wd=12, ticks=True, glow=True):
    q = partial(pts, p)
    if len(q) < 2: return
    if glow: pn.line(q, col + (70,), wd * 2.6, caps=False)
    pn.line(q, INK, wd + 5, caps=False); pn.line(q, col, wd, caps=False)
    if ticks:
        for i in range(0, len(q) - 1, 6):
            a = math.atan2(q[i + 1][1] - q[i][1], q[i + 1][0] - q[i][0])
            pn.rect(q[i][0] - 5, q[i][1] - 5, q[i][0] + 5, q[i][1] + 5, fill=(120, 84, 50), outline=INK, width=2)
    hx, hy = q[-1]
    pn.circ(hx, hy, wd * 0.9, fill=(255, 236, 190))
def plan_base(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    # rivers: Ose to the north, Oze to the south, joining the Brenne on the plain to the west
    pn.line([(1120, 560), (860, 600), (640, 610), (400, 640), (150, 700), (-40, 760)], (110, 150, 180), 12, caps=False)
    pn.line([(1120, 1120), (860, 1060), (640, 1060), (420, 1040), (200, 960), (-40, 900)], (110, 150, 180), 12, caps=False)
    pn.line([(80, 300), (100, 600), (130, 900), (90, 1500)], (110, 150, 180), 16, caps=False)
    # Mont Auxois: the plateau with contour rings
    hill = [(PC[0] + math.cos(a) * 1.05 * KM * 1.15 * (1 + 0.08 * math.sin(3 * a)), PC[1] + math.sin(a) * 0.4 * KM * 1.15 * (1 + 0.1 * math.cos(2 * a))) for a in np.linspace(0, 6.283, 40)]
    for i, sc in enumerate((1.5, 1.25, 1.0)):
        pts = [(PC[0] + (x - PC[0]) * sc, PC[1] + (y - PC[1]) * sc) for x, y in hill]
        pn.poly(pts, fill=lerpc((206, 190, 150), (176, 152, 108), i / 2), outline=(120, 96, 66), width=2)
    label(pn, PC[0], PC[1], 'ALESIA', 46, 1.0, (70, 50, 34))
    label(pn, 200, 1220, 'PLAIN', 30, 0.8, (90, 80, 60))
def sc_plan(base, pn, t, inner=1.0, outer=1.0, glow=True):
    plan_base(base, pn, t)
    ring_draw(pn, OUTER, outer, (150, 54, 40), 10)
    ring_draw(pn, INNER, inner, (196, 70, 48), 12)

def counter_tag(pn, x, y, t, t0, t1, n_to, text, sub=None):
    if t < t0 - 0.05: return
    v = int(round(n_to * eo3(P(t, t0, t1 - t0))))
    tag(pn, x, y, text.format(v), 64, pop(t, t0 - 0.05), rot_=-3, sub=sub)

# Shot 1 (graphic, overhead): both rings trace around the hill; "22 MILES"
def sc_open(base, pn, t, loop=False):
    t0 = T['s23'] if loop else 0.0
    ip = clamp(0.35 + 0.65 * eio(P(t, t0, 1.2))); op = clamp(eio(P(t, t0 + 0.5, 1.4)))
    sc_plan(base, pn, t, ip, op)
    tg = 0.0 if not loop else T['miles23'] - 0.1
    if t >= tg: tag(pn, 540, 330, '22 MILES', 66, pop(t, tg) if loop else 1.0, rot_=-3, sub='BOTH RINGS, ABOUT')
def cam_open(t, sc_, ox, oy): return camfocus(lerp(1.06, 1.0, eio(P(t, 0, 2.0))) * sc_, 540, 860, 540, 860, ox, oy)
def sc_loop(base, pn, t): sc_open(base, pn, t, loop=True)
def cam_loop(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.06, eio(P(t, T['s23'], 3.0))) * sc_, 540, 860, 540, 860, ox, oy)

# Shot 2 (EWS, low angle): the hill town above, the Roman line in the foreground
def oppidum(pn, cx, by, w, h, night=0.0, dusk=0.0, gauls=0, t=0.0):
    """Mont Auxois (BM-P063): steep sided, flat topped hill, the town wall (murus gallicus, BM-P040) along its rim,
    thatched roofs behind. Wider than tall."""
    g = lerpc(lerpc((120, 136, 78), (84, 80, 56), dusk), (30, 38, 46), night)
    top = by - h
    pts = [(cx - w * 0.75, by), (cx - w * 0.5, top + h * 0.25), (cx - w * 0.42, top + h * 0.04), (cx + w * 0.42, top + h * 0.04),
           (cx + w * 0.52, top + h * 0.3), (cx + w * 0.78, by)]
    pn.poly(pts, fill=g, outline=INK, width=3)
    pn.poly([(cx + w * 0.1, top + h * 0.06), (cx + w * 0.42, top + h * 0.04), (cx + w * 0.52, top + h * 0.3), (cx + w * 0.78, by), (cx + w * 0.3, by)], fill=light(g, 0.08))
    rs = random.Random(9)
    for i in range(int(w / 14)):     # scrub and small trees on the slopes, denser low down
        u = rs.random() ** 0.7; yy = lerp(top + h * 0.12, by - 6, u)
        half = lerp(w * 0.44, w * 0.76, (yy - top) / h)
        xx = cx + rs.uniform(-half, half) * 0.96
        r_ = rs.uniform(6, 14) * (w / 900)
        pn.circ(xx, yy, r_, fill=shade(g, rs.uniform(0.15, 0.35)), outline=lerpc(g, INK, 0.5), width=1.4)
    pn.line([(cx - w * 0.62, by - 4), (cx - w * 0.3, top + h * 0.5), (cx - w * 0.1, top + h * 0.3), (cx + w * 0.05, top + h * 0.08)], light(g, 0.25), 5, caps=False)   # path up to the gate
    rnd = random.Random(4)
    for i in range(int(w / 30)):   # roofs peeking over the wall
        x = cx - w * 0.38 + i * 30 + rnd.uniform(-6, 6)
        if x > cx + w * 0.38: break
        pn.poly([(x - 18, top - 2), (x, top - 26 - rnd.uniform(0, 10)), (x + 18, top - 2)], fill=lerpc((176, 148, 90), (50, 50, 60), night), outline=INK, width=2)
    PR.murus_gallicus(pn, cx - w * 0.44, cx + w * 0.44, top - 4, top + h * 0.08, seed=5)
    for i in range(gauls):
        figure(pn, cx - w * 0.36 + i * (w * 0.72 / max(1, gauls - 1)), top - 2, 0.32, -1, pose('idle'), 'gaul%d' % (1 + i % 3), 'angry', blink=blink_at(t, i))
def sc_hill_wide(base, pn, t):
    bgp(base, 'alday', 0.3)
    oppidum(pn, 540, 1080, 900, 300, gauls=7, t=t)
    ground(pn, 1080)
    PR.siege_line_elevation(pn, -60, 1140, 1420, 20, build=1.0)
def cam_hill_wide(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.08, eio(P(t, T['s1'], 2.0))) * sc_, 540, 900, 540, 900, ox, oy)

# Shot 3 (graphic): map of Gaul, the Gallic army driven onto Alesia
_MAP = {}
MAPC = (2.6, 46.6, 11.0)
def map_img():
    if 'g' not in _MAP: _MAP['g'] = Image.open('map_gaul.png').convert('RGB')
    return _MAP['g']
def geo_xy(lon, lat):
    lon_px, lat_px = MM.geo(*MAPC)
    return 540 + (lon - MAPC[0]) / lon_px, 960 - (lat - MAPC[1]) / lat_px
def map_view(z, fx_, fy, tx, ty):
    a = 2 / z
    return map_img().transform((W, H), Image.AFFINE, (a, 0, 2 * fx_ - tx * a, 0, a, 2 * fy - ty * a), Image.BILINEAR)
ALESIA = (4.50, 47.54)
def pin(pn, x, y, t, t0, col=RUST):
    if t < t0: return
    u = t - t0; drop = 1 - spring(u, 1.5, 7); py = y - 220 * drop
    rp = eo3(P(u, 0.12, 0.6))
    if 0 < rp < 1: pn.circ(x, y, 24 + 90 * rp, outline=col + (int(255 * (1 - rp)),), width=6)
    pn.poly([(x, py), (x - 22, py - 44), (x + 22, py - 44)], fill=col, outline=INK, width=3)
    pn.circ(x, py - 56, 25, fill=col, outline=INK, width=4); pn.circ(x, py - 56, 9, fill=PARCH)
def sc_map(base, pn, t):
    zp = eio(P(t, T['s2'], 1.6)); z = lerp(1.0, 1.25, zp)
    f_ = geo_xy(*ALESIA); f0 = (540, 960)
    fx_, fy = lerp(f0[0], f_[0], zp), lerp(f0[1], f_[1], zp); tx, ty = 540, 820
    fx_ = min(max(fx_, tx / z), W - (W - tx) / z); fy = min(max(fy, ty / z), H - (H - ty) / z)
    base.paste(map_view(z, fx_, fy, tx, ty))
    def xy(lon, lat):
        px, py = geo_xy(lon, lat); return tx + (px - fx_) * z, ty + (py - fy) * z
    label(pn, 330, 1120, 'GAUL', 100, P(t, T['s2'] + 0.1, 0.3))
    ax, ay = xy(*ALESIA)
    # the Gallic army (token) withdraws onto Alesia; Roman arrows close in behind it
    gp = eio(P(t, T['caesar2'] - 0.3, 1.2))
    gx, gy = lerp(ax - 40, ax, gp), lerp(ay + 260, ay, gp)
    if t > T['caesar2'] - 0.3:
        pn.circ(gx, gy, 26, fill=(60, 90, 140), outline=INK, width=4)
    for k_, (dx, dy) in enumerate(((-160, 330), (150, 300))):
        p_ = eio(P(t, T['cornered'] - 0.2 + k_ * 0.15, 0.9))
        if p_ > 0: arrow_line(pn, (ax + dx, ay + dy), (ax + dx * 0.25, ay + dy * 0.25 + 40), RUST, 16, 46, p=p_)
    pin(pn, ax, ay - 30, t, T['army2'])
    label(pn, ax, ay + 70, 'ALESIA', 46, P(t, T['army2'] + 0.15, 0.3))
    tag(pn, 760, 380, '52 BC', 70, pop(t, T['n52']), rot_=3)

# Shot 4 (WS, low angle): the hill town, Gauls on its wall
def sc_hilltop(base, pn, t):
    bgp(base, 'alday', 0.3)
    ground(pn, 1300)
    oppidum(pn, 540, 1300, 1240, 520, gauls=6, t=t)
    tag(pn, 540, 360, 'MONT AUXOIS', 52, pop(t, T['hilltop'] + 0.1), rot_=-3, sub='BURGUNDY, FRANCE')
def cam_hilltop(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 1000, ox, oy)

# Shot 5 (MS): Caesar weighs the hill
def sc_caesar(base, pn, t):
    bgp(base, 'alday', 0.3)
    oppidum(pn, 760, 1000, 700, 260)
    ex = 'thinking' if t < T['strong'] - 0.05 else 'determined'
    al.caesar(pn, 340, 1820, 4.0, 1, t, ex, 'cross')
    tag(pn, 760, 380, 'JULIUS CAESAR', 50, pop(t, T['judged']), rot_=3, sub='PROCONSUL OF GAUL')

# Shot 6 (graphic, overhead): the inner ring traces
def sc_ring_inner(base, pn, t):
    sc_plan(base, pn, t, eio(P(t, T['s5'], T['instead'] - T['s5'] + 0.3)), 0.0)
    tag(pn, 540, 330, 'INNER RING', 56, pop(t, T['ringed']), rot_=-3, sub='CAESAR: 11 ROMAN MILES')

# Shot 7 (FS): a legionary swings the dolabra; the ditch deepens in front of him
def sc_dig(base, pn, t):
    bgp(base, 'alday', 0.4)
    ground(pn, GROUND)
    dp = eio(P(t, T['s6'], 1.0))
    pn.poly([(600, GROUND), (1100, GROUND), (1100, GROUND + 260 * dp), (690, GROUND + 260 * dp)], fill=(76, 58, 42), outline=INK, width=3)
    a0 = T['strike'] - 0.5; d0 = T['strike'] - 0.16
    if t < a0: sw = 0.35
    elif t < d0: sw = lerp(0.35, 0.0, eio(P(t, a0, d0 - a0)))
    elif t < T['strike']: sw = ei2(P(t, d0, T['strike'] - d0))
    elif t < T['strike'] + 0.24: sw = 1.0
    else: sw = lerp(1.0, 0.45, eio(P(t, T['strike'] + 0.24, 0.5)))
    al.legionary_dig(pn, 400, GROUND, 2.9, 'rleg23c', sw=sw, t=t)
    if t >= T['strike']:
        particles(pn, 'dust', 700, GROUND + 10, t, T['strike'], 1.0, seed=3, ground=GROUND + 40)
    tag(pn, 760, 290, '20 FT WIDE', 56, pop(t, T['ditch'] + 0.1), rot_=3, sub='STRAIGHT SIDES')
def cam_dig(t, sc_, ox, oy): return camfocus(sc_, 540, 900, 540, 900, ox, oy)

# Shot 8 (WS): the rampart rises in turf courses as a soldier brings earth
def sc_rampart(base, pn, t):
    bgp(base, 'alday', 0.3)
    ground(pn, 1250)
    b = 0.333 * eio(P(t, T['s7'], T['high'] - T['s7'] + 0.3))
    PR.siege_line_elevation(pn, -60, 1140, 1250, 60, build=b, towers=False, cervi=False)
    x = lerp(-80, 420, eio(P(t, T['s7'], 1.6)))
    al.legionary_basket(pn, x, 1330, 2.3, walk=(t - T['s7']) * 1.4, t=t)
    tag(pn, 760, 290, '~12 FT', 64, pop(t, T['twelve']), rot_=-3, sub='EARTH AND TURF')

# Shot 9 (EWS, pan): towers rise along the line
def sc_towers(base, pn, t):
    u = eio(P(t, T['s8'], 2.2))
    bgp(base, 'alday', 0.25, dx=lerp(-60, 60, u) * 0.3)
    pn.push(lerp(0, -380, u), 0, 1)
    ground(pn, 1250)
    tb = clamp(0.667 + 0.333 * eio(P(t, T['wooden'] - 0.1, T['eighty'] - T['wooden'] + 0.3)))
    PR.siege_line_elevation(pn, -100, 1700, 1250, 26, build=tb)
    pn.pop()
    tag(pn, 540, 420, '~80 FT APART', 60, pop(t, T['eighty']), rot_=3)

# Shot 10 (FS, tracking, night): riders slip out through a gap in the unfinished line
def sc_riders(base, pn, t):
    u = t - T['s9']
    bgp(base, 'alnight', 0.2, dx=-u * 40)
    pn.push(-u * 260, 0, 1)
    ground(pn, 1300, night=1.0)
    PR.siege_line_elevation(pn, 300, 760, 1300, 22, build=0.5, night=1.0, towers=False)
    PR.siege_line_elevation(pn, 1500, 2100, 1300, 22, build=0.5, night=1.0, towers=False)
    pn.pop()
    for i, (x0, ph0) in enumerate(((180, 0.0), (-60, 0.37))):
        x = x0 + u * 120
        al.rider(pn, x, 1320 - i * 30, 2.1 - i * 0.25, 'gcav23', ph=(u * 1.9 + ph0) % 1, gallop=1.0, t=t)
    night_tint(pn, 60)
    tag(pn, 760, 420, 'TO CALL FOR HELP', 50, pop(t, T['help']), rot_=-3)
def cam_riders(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 1000, ox, oy)

# Shot 11 (graphic, overhead): the outer ring, arrows pointing outward
def sc_ring_outer(base, pn, t):
    sc_plan(base, pn, t, 1.0, eio(P(t, T['s10'], T['outward'] - T['s10'] + 0.4)))
    if t > T['outward'] - 0.1:
        for a in np.linspace(0, 6.28, 9)[:-1]:
            p_ = eio(P(t, T['outward'] - 0.1, 0.5))
            r0, r1 = 3.45, 4.0
            arrow_line(pn, (PC[0] + math.cos(a) * r0 * KM * 1.12, PC[1] + math.sin(a) * r0 * KM * 0.92),
                       (PC[0] + math.cos(a) * r1 * KM * 1.12, PC[1] + math.sin(a) * r1 * KM * 0.92), RUST, 8, 26, p=p_)
    tag(pn, 540, 300, 'OUTER RING', 56, pop(t, T['second']), rot_=3, sub='FACING OUTWARD')

# Shot 12 (graphic): scale along the outer ring, PROVEN stamp
def sc_thirteen(base, pn, t):
    sc_plan(base, pn, t, 1.0, 1.0)
    stamp(pn, 540, 330, 'PROVEN', t - T['thirteen'], 110)
    tag(pn, 540, 1250, 'EXCAVATED ~21 km', 50, pop(t, T['thirteen'] + 0.25), rot_=2, sub='CAESAR: 14 ROMAN MILES')

# Shot 13 (WS, high angle): legions between the two rings
def rampart_mini(pn, x, y, s, f=1, night=0.0):
    """One rampart in section facing f (+1 faces right): earth bank, breastwork on the outer edge, tower."""
    rh = 12 * PR.PES * s
    pts = [(x - f * 2.2 * s, y), (x - f * 0.3 * s, y - rh), (x + f * 3.4 * s, y - rh), (x + f * 5.4 * s, y)]
    pn.poly(pts, fill=PR.EARTH, outline=INK, width=2.6)
    bx0 = x - f * 0.3 * s
    PR.breastwork(pn, min(bx0, bx0 + f * 0.7 * s), max(bx0, bx0 + f * 0.7 * s), y - rh, s, h=1.5, merlon=0.7, gap=0.3)
    PR.roman_tower(pn, x + f * 1.8 * s, y - rh, s * 0.8, h=5.0, w=2.4)
def sc_between(base, pn, t):
    bgp(base, 'alday', 0.3)
    ground(pn, 1200)
    rampart_mini(pn, 230, 1200, 30, f=1)
    rampart_mini(pn, 850, 1200, 30, f=-1)
    label(pn, 120, 1260, 'TOWN', 40, 1.0, (60, 48, 34)); label(pn, 930, 1260, 'RELIEF ARMY', 30, 1.0, (60, 48, 34))
    for i in range(8):
        for j in range(2):
            x = 360 + i * 46 + j * 23; y = 1200 + j * 40
            figure(pn, x, y, 0.42, 1 if i % 2 else -1, pose('idle'), 'rleg23a', 'neutral', blink=blink_at(t, i + j))
    label(pn, 540, 1120, 'LEGIONS', 34, P(t, T['legions'], 0.3), (150, 54, 40))
    for sd in (-1, 1):
        p_ = eio(P(t, T['rings'] - 0.1, 0.4))
        arrow_line(pn, (540 + sd * 120, 1060), (540 + sd * 260, 1060), RUST, 8, 26, p=p_)
def cam_between(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 1000, ox, oy)

# Shot 14 (graphic): traps assemble outward from the wall (section, SIMPLIFIED)
def sc_traps(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    tr = eio(P(t, T['buried'] - 0.1, T['traps'] - T['buried'] + 0.6))
    L = []
    PR.siege_line_section(pn, 900, 980, 34, traps=tr, labels=lambda n, p: L.append((n, p)))
    for n, (x, y) in L: label(pn, x, y, n, 26, 1.0, (40, 30, 22))
    label(pn, 120, 560, '< TOWN', 36, 1.0)
    pn.text(540, 480, 'SIMPLIFIED', 26, MUTED, 'Black', 'mm', True)
    tag(pn, 540, 360, 'TRAPS', 64, pop(t, T['traps']), rot_=-3)

# Shot 15 (insert): rows of sharpened branches
def sc_cippi(base, pn, t):
    bgp(base, 'alday', 0.2)
    ground(pn, 1250)
    pn.rect(-40, 1250, 1120, 1520, fill=(80, 62, 44))
    for r_ in range(5):
        for i in range(6):
            p_ = pop(t, T['s14'] + 0.08 * (r_ + i * 0.3))
            if p_ <= 0: continue
            x = 120 + i * 170 + r_ * 22; y = 1260 + r_ * 50
            PR.cippus(pn, x, y + 120 * (1 - min(1, p_)), 120 - r_ * 8, seed=r_ * 7 + i)
    tag(pn, 760, 420, 'CIPPI', 60, pop(t, T['branches']), rot_=3, sub='"GRAVESTONES"')

# Shot 16 (insert): brushwood slides off a lilium, the stake shows
def sc_lilia(base, pn, t):
    bgp(base, 'alday', 0.2)
    pn.rect(-40, 1060, 1120, 1700, fill=PR.EARTH)
    pn.line([(-40, 1060), (1120, 1060)], INK, 4)
    cov = 1 - eio(P(t, T['pits'] - 0.1, 0.5))
    PR.lilium(pn, 540, 1060, 420, cover=0.0)
    if cov > 0:
        pn.push((1 - cov) * 600, 0, 1)
        PR.lilium(pn, 540, 1060, 420, cover=1.0, cut=False)
        pn.pop()
    tag(pn, 760, 420, 'LILIA', 60, pop(t, T['stakes']), rot_=-3, sub='"LILIES", 3 FT DEEP')

# Shot 17 (ECU): the iron hook catches the light
def sc_hooks(base, pn, t):
    bgp(base, 'alday', 0.2)
    pn.rect(-40, 1000, 1120, 1800, fill=PR.EARTH)
    pn.line([(-40, 1000), (1120, 1000)], INK, 4)
    PR.stimulus(pn, 540, 1000, 1500, cut=True)
    g = P(t, T['hooks'] - 0.05, 0.5)
    if 0 < g < 1:
        pn.circ(560, 820, 20 + 60 * math.sin(g * math.pi), fill=(255, 250, 230, int(160 * math.sin(g * math.pi))))
    tag(pn, 760, 420, 'STIMULI', 60, pop(t, T['hooks'] + 0.1), rot_=3, sub='"GOADS", FOUND AT ALESIA')
def cam_hooks(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.08, eio(P(t, T['s16'], 2.0))) * sc_, 540, 900, 540, 900, ox, oy)

# Shot 18 (WS, dusk): the relief army charges the outer line from the right
def sc_relief(base, pn, t):
    u = t - T['s17']
    bgp(base, 'aldusk', 0.3)
    ground(pn, 1250, dusk=1.0)
    PR.siege_line_elevation(pn, -200, 300, 1250, 30, build=1.0)
    for r_ in range(3):
        for i in range(6):
            x = 1180 + i * 110 + r_ * 50 - min(u, 2.4) * 330; y = 1220 + r_ * 60
            if x < 360: x = 360 + (i % 3) * 14
            al.gaul_charge(pn, x, y, 0.9 + r_ * 0.12, 'gaulr%d' % (1 + (i + r_) % 3), t=t, f=-1, thrust=0.5 + 0.5 * math.sin(u * 6 + i))
    if t > T['hit18']:
        impact(pn, 330, 1150, t, T['hit18'], 0.9, seed=5)
        particles(pn, 'dust', 330, 1250, t, T['hit18'], 1.2, seed=8, ground=1290)

# Shot 19 (graphic): both attacks hit at once, inside and outside
def sc_both(base, pn, t):
    sc_plan(base, pn, t, 1.0, 1.0)
    for k_, a in enumerate((2.6, 3.4, 4.0)):    # relief army from the plain (west and north west)
        p_ = eio(P(t, T['s19'] - 0.3 + k_ * 0.1, 0.6))
        arrow_line(pn, (PC[0] + math.cos(a) * 4.4 * KM * 1.12, PC[1] + math.sin(a) * 4.4 * KM * 0.92),
                   (PC[0] + math.cos(a) * 3.4 * KM * 1.12, PC[1] + math.sin(a) * 3.4 * KM * 0.92), (60, 90, 140), 16, 44, p=p_)
    for k_, a in enumerate((2.8, 3.6)):          # the town from the hill
        p_ = eio(P(t, T['inner'] - 0.2 + k_ * 0.1, 0.6))
        arrow_line(pn, (PC[0] + math.cos(a) * 0.9 * KM * 1.12, PC[1] + math.sin(a) * 0.9 * KM * 0.92),
                   (PC[0] + math.cos(a) * 2.2 * KM * 1.12, PC[1] + math.sin(a) * 2.2 * KM * 0.92), (60, 90, 140), 16, 44, p=p_)
    tag(pn, 540, 330, 'AT THE SAME TIME', 54, pop(t, T['same']), rot_=-3)
def cam_both(t, sc_, ox, oy): return camfocus(sc_, 540, 860, 540, 860, ox, oy)

# Shot 20 (CU): a legionary braced behind his shield; the line bends, then holds
def sc_hold(base, pn, t):
    bgp(base, 'aldusk', 0.2)
    ex = 'fear' if T['bent'] - 0.05 < t < T['held'] - 0.05 else ('determined' if t >= T['held'] - 0.05 else 'angry')
    figure(pn, 560, 2550, 6.2, 1, pose('brace'), 'rleg23a', ex, blink=blink_at(t, 0.3))
    if t > T['bent']:
        impact(pn, 300, 1050, t, T['bent'], 1.0, seed=2)
        particles(pn, 'sparks', 300, 1050, t, T['bent'], 0.8, seed=6)

# Shot 21 (AS): Vercingetorix with his sword, then (insert) it drops at Caesar's feet
def sc_verc(base, pn, t):
    bgp(base, 'alday', 0.3)
    ground(pn, 1700)
    al.verc_surrender(pn, 540, 1760, 4.8, lay=0.0, t=t, expr='sad')
    tag(pn, 540, 330, 'VERCINGETORIX', 56, pop(t, T['verc'] + 0.05), rot_=-3)
def caliga(pn, x, y, k, f=1):
    pn.push(x, y, k)
    pn.poly([(-f * 10, -60), (f * 16, -60), (f * 22, -14), (f * 70, -8), (f * 74, 6), (-f * 14, 6)], fill=(120, 80, 48), outline=INK, width=3)
    for i in range(4): pn.line([(-f * 6 + f * i * 12, -54), (f * 24 + f * i * 12, -12)], (80, 52, 30), 3)
    for i in range(6): pn.circ(-f * 8 + f * i * 14, 7, 2.6, fill=IRON)
    pn.pop()
def sc_drop(base, pn, t):
    bgp(base, 'alday', 0.2)
    ground(pn, 1250)
    pn.push(540, 1250, 2.6)
    for sd in (-1, 1):   # camp stool legs behind
        pn.line([(-60 * sd, 0), (50 * sd, -150)], INK, 9); pn.line([(-60 * sd, 0), (50 * sd, -150)], (160, 120, 70), 6)
    pn.pop()
    caliga(pn, 420, 1250, 2.0, -1); caliga(pn, 660, 1250, 2.0, 1)
    u = eio(P(t, T['surrendered'] - 0.25, 0.4)) ** 1.5
    y = lerp(560, 1236, u)
    PR.gallic_sword(pn, 180, y, -2 + 6 * u, 360, sheath=True)
    if t > T['surrendered'] + 0.15:
        particles(pn, 'dust', 540, 1250, t, T['surrendered'] + 0.15, 1.0, seed=9, ground=1270)
    tag(pn, 540, 360, 'SURRENDERED', 56, pop(t, T['surrendered'] + 0.2), rot_=3, sub='CAESAR 7.89')

SCENES = [
    (0.0, sc_open, cam_open, None),
    (T['s1'], sc_hill_wide, cam_hill_wide, None),
    (T['s2'], sc_map, None, 'slide'),             # chapter: the history
    (T['s3'], sc_hilltop, cam_hilltop, None),
    (T['s4'], sc_caesar, None, None),
    (T['s5'], sc_ring_inner, None, None),
    (T['s6'], sc_dig, cam_dig, None),
    (T['s7'], sc_rampart, None, None),
    (T['s8'], sc_towers, None, None),
    (T['s9'], sc_riders, cam_riders, 'slide'),   # chapter: the call for help (night)
    (T['s10'], sc_ring_outer, None, 'dissolve'),
    (T['s11'], sc_thirteen, None, None),
    (T['s12'], sc_between, cam_between, None),
    (T['s13'], sc_traps, None, 'slide'),          # chapter: the traps
    (T['s14'], sc_cippi, None, None),
    (T['s15'], sc_lilia, None, None),
    (T['s16'], sc_hooks, cam_hooks, None),
    (T['s17'], sc_relief, None, 'slide'),         # chapter: the battle
    (T['s19'], sc_both, cam_both, None),
    (T['s21'], sc_hold, None, None),
    (T['s22'], sc_verc, None, None),
    (T['surrendered'] - 0.3, sc_drop, None, None),
    (T['s23'], sc_loop, cam_loop, 'dissolve'),
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
                cand = [x['w'] for x in part if x['w'].strip('.,:').lower() not in STOP]
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
    C = [(0.0, 'scratch', 0.6), (0.0, 'drum', 0.7), (T['miles0'], 'pop', 0.5), (T['s1'], 'wind', 0.4), (T['hill1'], 'thud', 0.5),
         (T['n52'], 'pop', 0.5), (T['cornered'], 'swish', 0.5), (T['army2'], 'thud', 0.6), (T['s3'], 'horn', 0.4), (T['hilltop'] + 0.1, 'pop', 0.4),
         (T['judged'], 'pop', 0.4), (T['s5'], 'scratch', 0.6), (T['ringed'], 'pop', 0.4),
         (T['strike'] - 0.2, 'swish', 0.6), (T['strike'], 'dig', 1.0), (T['ditch'] + 0.1, 'pop', 0.4),
         (T['rampart'], 'thud', 0.5), (T['twelve'], 'pop', 0.5), (T['high'], 'thud', 0.4),
         (T['wooden'], 'hammer', 0.5), (T['tower'], 'hammer', 0.5), (T['eighty'], 'pop', 0.5),
         (T['s9'] - 0.12, 'hooves', 0.9), (T['help'], 'pop', 0.4),
         (T['s10'], 'scratch', 0.6), (T['second'], 'pop', 0.4), (T['outward'], 'swish', 0.5),
         (T['thirteen'], 'stamp', 0.9), (T['thirteen'] + 0.25, 'pop', 0.4),
         (T['legions'], 'murmur', 0.5), (T['rings'], 'swish', 0.4),
         (T['buried'], 'dig', 0.5), (T['traps'], 'pop', 0.5),
         (T['s14'], 'creak', 0.6), (T['branches'], 'pop', 0.4), (T['pits'] - 0.1, 'rustle', 0.7), (T['stakes'], 'pop', 0.4),
         (T['hooks'] - 0.05, 'clink', 0.8), (T['hooks'] + 0.1, 'pop', 0.4),
         (T['s17'] - 0.12, 'horn', 0.8), (T['relief'], 'roar', 0.7), (T['hit18'], 'crash', 0.9),
         (T['inner'] - 0.2, 'roar', 0.5), (T['same'], 'pop', 0.4), (T['time20'], 'crash', 0.6),
         (T['bent'], 'crash', 1.0), (T['held'], 'thud', 0.6),
         (T['verc'] + 0.05, 'pop', 0.4), (T['surrendered'] + 0.15, 'clang', 0.9), (T['surrendered'] + 0.2, 'pop', 0.4),
         (T['s23'] - 0.12, 'scratch', 0.6), (T['s23'], 'drum', 0.6)]
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

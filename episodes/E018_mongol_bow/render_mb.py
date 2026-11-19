"""E018 Mongol composite bow: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import props as PR
from props import tag, stamp, callout, arrow as arrow_line, mongol_bow, mongol_arrow, MARROW_L, limb_layers, stele, horse
import mb
from mb import mongol_archer, mounted_archer
import env as E
import lb
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

# ---------------- beat table (all from measured word onsets) ----------------
T = dict(
    over0=w(0, 0), five0=w(0, 1), hundred0=w(0, 2), metres0=w(0, 3),
    s1=S(1), how=w(1, 2), far=w(1, 3), mongol1=w(1, 5), archer1=w(1, 6), shot1=w(1, 7), arrow1=w(1, 9),
    s2=S(2), y1225=w(2, 1),
    s3=S(3), shot3=w(3, 2), carved=w(3, 4), granite=w(3, 7), stone3=w(3, 8),
    s4=S(4), stone4=w(4, 1), sits=w(4, 3), museum=w(4, 6), saint=w(4, 8), peter=w(4, 9),
    s5=S(5), yis=w(5, 3),
    s6=S(6), nephew=w(6, 1), genghis=w(6, 3), khan=w(6, 4),
    s7=S(7), bows7=w(7, 1), short7=w(7, 3), shoot7=w(7, 6), gallop7=w(7, 9), horse7=w(7, 10),
    s8=S(8), curves=w(8, 2), wrong=w(8, 4), way=w(8, 5),
    s9=S(9), away=w(9, 0), archer9=w(9, 3),
    s10=S(10), bends=w(10, 2), back10=w(10, 4), itself=w(10, 6),
    s11=S(11), loaded=w(11, 3), even=w(11, 6), draw11=w(11, 7),
    s12=S(12), three=w(12, 1), layers=w(12, 2), work=w(12, 5),
    s13=S(13), horn13=w(13, 0), inside=w(13, 3), squeezed=w(13, 4),
    s14=S(14), sinew14=w(14, 0), outside=w(14, 3), stretched=w(14, 4),
    s15=S(15), core=w(15, 2), wood15=w(15, 4), bamboo=w(15, 6), holds=w(15, 7), together=w(15, 9),
    s16=S(16), energy=w(16, 5), wood16=w(16, 7), alone=w(16, 8),
    s17=S(17), short17=w(17, 2), pulls=w(17, 4), long17=w(17, 7), one17=w(17, 8),
    s18=S(18), glued=w(18, 0), dried=w(18, 2), months=w(18, 4),
    s19=S(19), saddle=w(19, 6), could=w(19, 7), throw=w(19, 8), arrow19=w(19, 10), over19=w(19, 11), five19=w(19, 12),
    hundred19=w(19, 13), metres19=w(19, 14),
    end=VO_END,
)
T['rel1'] = T['shot1'] + 0.02             # release on "shot"
T['rel6'] = T['gallop7'] + 0.04            # release on "galloping"
T['rel19'] = T['throw'] + 0.02
T['land0'] = None
CAM.drift = 0.5

GY = 1250                 # ground line on outdoor scenes
FLOOR_C = (206, 190, 158)

# ---------------- shared helpers ----------------
def bgp(base, img, par=0.5):
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def floor(pn, y, col=FLOOR_C, line=True):
    pn.rect(-400, y, 1480, 2800, fill=col)
    if line: pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def cap_shade(pn, a=90):
    """Darken the caption zone a little so white captions read over light ground."""
    for i in range(8):
        y0 = 1330 + i * 30
        pn.rect(-300, y0, 1380, y0 + 30, fill=(20, 14, 10, int(a * min(1, (i + 1) / 5))))
    pn.rect(-300, 1570, 1380, 2600, fill=(20, 14, 10, a))

def keys(t, ks):
    """Pose to pose keys: [(time, value, ease), ...]; ease applies into that key. Never linear on figures."""
    if t <= ks[0][0]: return ks[0][1]
    for (t0, v0, _), (t1, v1, e) in zip(ks, ks[1:]):
        if t < t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return lerp(v0, v1, (e or eio)(u))
    return ks[-1][1]

def dim(pn, x0, x1, y, label, p, col=INK, sz=40, below=False, tick=18, vertical=False):
    if p <= 0: return
    e = eo3(p)
    if vertical:
        ye = lerp(x0, x1, e)
        pn.line([(y - tick, x0), (y + tick, x0)], col, 4)
        pn.line([(y, x0), (y, ye)], col, 4)
        if e > 0.98: pn.line([(y - tick, x1), (y + tick, x1)], col, 4)
        if p > 0.5:
            s = eoback(clamp((p - 0.5) / 0.5)); wv = pn.tw(label, sz, 'Black', True) + 30
            pn.push(y + (wv / 2 + 24) * (1 if below else -1), (x0 + x1) / 2, s)
            pn.rect(-wv / 2, -sz * 0.72, wv / 2, sz * 0.72, fill=(250, 244, 228), outline=col, width=3.4, r=10)
            pn.text(0, 2, label, sz, col, 'Black', 'mm', True); pn.pop()
        return
    xe = lerp(x0, x1, e)
    pn.line([(x0, y - tick), (x0, y + tick)], col, 4)
    pn.line([(x0, y), (xe, y)], col, 4)
    if e > 0.98: pn.line([(x1, y - tick), (x1, y + tick)], col, 4)
    if p > 0.5:
        s = eoback(clamp((p - 0.5) / 0.5)); wv = pn.tw(label, sz, 'Black', True) + 30
        ly = y + (sz * 1.0 if below else -sz * 1.0)
        pn.push((x0 + x1) / 2, ly, s)
        pn.rect(-wv / 2, -sz * 0.72, wv / 2, sz * 0.72, fill=(250, 244, 228), outline=col, width=3.4, r=10)
        pn.text(0, 2, label, sz, col, 'Black', 'mm', True); pn.pop()

def ring(pn, x, y, t, t0, col=AMBER, r0=18, r1=70):
    u = t - t0
    if u < 0 or u > 0.6: return
    e = eo3(u / 0.6)
    pn.circ(x, y, lerp(r0, r1, e), outline=col + (int(255 * (1 - e)),), width=6)

def xmark(pn, x, y, p, s=22, col=RUST):
    if p <= 0: return
    e = eoback(p); pn.push(x, y, e)
    for a, b in (((-s, -s), (s, s)), ((-s, s), (s, -s))):
        pn.line([a, b], INK, 13); pn.line([a, b], col, 8)
    pn.pop()

def bar(pn, x, y, wd, ht, v, label, col=RUST, sub=None):
    """Unnumbered gauge (never an invented number): vertical bar filling to v in 0..1."""
    pn.rect(x - wd / 2 - 6, y - ht - 6, x + wd / 2 + 6, y + 6, fill=(250, 244, 228), outline=INK, width=4, r=10)
    if v > 0.005:
        pn.rect(x - wd / 2, y - ht * clamp(v, 0, 1.08), x + wd / 2, y, fill=col, r=6)
        pn.rect(x - wd / 2 + 4, y - ht * clamp(v, 0, 1.08) + 4, x - wd / 2 + 12, y - 4, fill=light(col, 0.4), r=3)
    pn.text(x, y + 44, label, 30, INK, 'Black', 'mm', True)
    if sub: pn.text(x, y + 78, sub, 22, MUTED, 'Bold', 'mm', sp=2)

# ---------------- the steppe world (tracking shots) ----------------
_W = {}
def world_layers():
    if 'sky' in _W: return _W
    sk = E.sky((178, 196, 212), (236, 224, 198), glow=(255, 236, 196), gy=0.5)
    E.clouds(sk, 5, (250, 244, 232, 210), n=8, y0=160, y1=640)
    _W['sky'] = E.grade(sk, blur=2.0, sat=0.8, bright=0.96, cap=False)
    WW = 7000
    far = Image.new('RGBA', (WW, H), (0, 0, 0, 0)); E.hill_layer(far, 1010, 70, (170, 172, 158), 31, w=WW, freqs=(0.9 * 6, 2.2 * 6, 4.6 * 6, 9.0 * 6))
    near = Image.new('RGBA', (WW, H), (0, 0, 0, 0)); E.hill_layer(near, 1120, 46, (152, 150, 112), 32, w=WW, freqs=(1.2 * 6, 3.0 * 6, 6.5 * 6))
    _W['far'] = far.filter(ImageFilter.GaussianBlur(4)); _W['near'] = near.filter(ImageFilter.GaussianBlur(2.5))
    return _W

GRS = (156, 150, 98); GRS_D = (126, 120, 78); GRS_L = (184, 176, 118)
def steppe(base, pn, t, camx=0.0, tufts=True, par=True):
    L_ = world_layers()
    base.paste(bg_cam(L_['sky'], 0.15))
    for name, f in (('far', 0.12), ('near', 0.38)):
        off = int(camx * f) % (L_[name].width - W - 10) if par else 0
        crop = L_[name].crop((off, 0, off + W, H))
        base.alpha_composite(bg_cam(crop, 0.4 if name == 'far' else 0.6))
    # ground in the vector layer, moving at 1.0 with tufts and stones as speed reference
    pn.rect(-400, GY - 30, 1480, 2800, fill=GRS)
    pn.line([(-400, GY - 30), (1480, GY - 30)], lerpc(GRS, INK, .35), 3, caps=False)
    pn.rect(-400, GY + 140, 1480, 2800, fill=GRS_D)
    if tufts:
        sp = 150
        i0 = int((camx - 600) // sp); i1 = int((camx + 1700) // sp)
        for i in range(i0, i1):
            rnd = random.Random(i * 7919)
            for row, (yy, s) in enumerate(((GY - 18, 0.8), (GY + 60, 1.1), (GY + 190, 1.5))):
                xx = i * sp + rnd.uniform(0, sp) - camx * (0.92 if row == 0 else 1.0 if row == 1 else 1.12)
                if -60 < xx < 1140:
                    for k in range(-2, 3):
                        pn.line([(xx + k * 4 * s, yy), (xx + k * 7 * s, yy - (16 - abs(k) * 3) * s)], GRS_L if k % 2 else GRS_D, 3 * s)
                    if rnd.random() < 0.35:
                        pn.ell(xx + 40 * s, yy + 4, 9 * s, 5 * s, fill=(146, 138, 120), outline=INK, width=1.6)

# ---------------- arrow flight with a distance counter (hook and finale) ----------------
def counter(pn, v, a=1.0, y=300):
    if a <= 0: return
    pn.push(540, y, 0.85 + 0.15 * eoback(a))
    pn.rect(-250, -100, 250, 100, fill=(24, 20, 16, int(225 * a)), outline=(250, 244, 228, int(255 * a)), width=5, r=18)
    txt = f'{int(round(v)):d}'
    pn.text(-30, -4, txt, 150, AMBER + (int(255 * a),), 'Black', 'mm', True)
    pn.text(150, 22, 'M', 72, (250, 244, 228, int(255 * a)), 'Black', 'mm', True)
    pn.pop()

def eo2(x): return 1 - (1 - clamp(x)) ** 2
XTOT = 9600.0; HMAX = 560.0

def flight_state(u, h0=0.0):
    """Arrow along its flight: u 0..1. World x slows with drag (eo2), height is a parabola from h0 to the ground."""
    x = XTOT * eo2(u)
    h = 4 * HMAX * u * (1 - u) + h0 * (1 - u)
    du = 1e-3
    x2 = XTOT * eo2(min(1, u + du)); h2 = 4 * HMAX * (u + du) * (1 - u - du) + h0 * (1 - u - du)
    ang = math.atan2(-(h2 - h), x2 - x)
    return x, h, ang

def flight_frame(base, pn, t, u, landed_t=None, h0=0.0, x_scr=540.0, camx_extra=0.0, ground_y=GY):
    x, h, ang = flight_state(u, h0)
    camx = x + camx_extra
    steppe(base, pn, t, camx)
    y = ground_y - 40 - h
    k = 2.7
    if landed_t is None:
        sp = 1 - u
        speed_lines(pn, x_scr, y, math.cos(ang), math.sin(ang), t, length=320, n=8, spread=60, seed=11, alpha=210)
        pn.push(x_scr, y, k); mongol_arrow(pn, (-math.cos(ang) * MARROW_L * 0.6, -math.sin(ang) * MARROW_L * 0.6), ang); pn.pop()
    else:
        # stuck in the ground at the landing angle, with a small quiver
        q = math.sin((t - landed_t) * 40) * math.exp(-(t - landed_t) * 6) * 0.05
        a2 = ang + q
        tip = (x_scr, ground_y - 30 + 22)
        nock = (tip[0] - math.cos(a2) * MARROW_L * 0.75 * k, tip[1] - math.sin(a2) * MARROW_L * 0.75 * k)
        pn.push(nock[0], nock[1], k); mongol_arrow(pn, (0, 0), a2, L=MARROW_L * 0.75 + 4); pn.pop()
        impact(pn, tip[0], tip[1] - 10, t, landed_t, 1.0, seed=3)
        particles(pn, 'dust', tip[0], tip[1], t, landed_t, 1.3, seed=4, ground=tip[1] + 8)
    return x, h, ang

# ---------------- 1. hook: an arrow already deep in its flight, counter running past 500 ----------------
U0 = 0.46; U_H = 0.741
HOOK_RATE = (U_H - U0) / (T['hundred0'] - 0.0)
T['land0'] = (1 - U0) / HOOK_RATE
def hook_u(t): return U0 + HOOK_RATE * t
def sc_hook(base, pn, t):
    u = hook_u(t)
    landed = t >= T['land0']
    flight_frame(base, pn, t, min(1.0, u), landed_t=T['land0'] if landed else None)
    cap_shade(pn, 70)
    v = 536 * eo2(min(1.0, u))
    hud_counter[0] = (v, 1.0)
    tag(pn, 760, 640, 'EST. 536 M', 54, pop(t, T['metres0'] - 0.05), rot_=4, sub='ABOUT 586 YARDS')
def cam_hook(t, sc, ox, oy):
    return sc, ox, oy

hud_counter = [None]
def hud_hook(pn, t):
    if hud_counter[0]: counter(pn, *hud_counter[0])

# ---------------- 2. Yisungge draws and shoots ----------------
ARX, ARK = 290, 1.85
def shoot_draw(t, t_rel, t_start=None):
    """Draw curve for a shot released at t_rel: lift and draw in (eased), short hold at anchor, release."""
    t_start = t_start if t_start is not None else t_rel - 1.3
    if t < t_start: return 0.0, 0.0
    if t < t_rel - 0.35: return eio(P(t, t_start, t_rel - 0.35 - t_start)), 0.0
    if t < t_rel: return 1.0, 0.0
    return 1.0, eo3(P(t, t_rel, 0.18))

def crowd(pn, t, y=GY - 120, k=0.5, cheer_t=None, n=7, x0=600):
    for i in range(n):
        x = x0 + i * 70
        ch = cheer_t is not None and t > cheer_t + i * 0.05
        p = pose('cheer') if ch and int((t - cheer_t) * 4 + i) % 2 else pose('idle')
        figure(pn, x, y + (i % 2) * 10, k, -1, p, 'mongol3' if i % 3 else 'yisungge', 'happy' if ch else 'neutral', blink=blink_at(t, i))

def sc_shot(base, pn, t):
    steppe(base, pn, t, 0.0, par=False)
    crowd(pn, t, cheer_t=T['rel1'] + 0.5)
    d_, rel = shoot_draw(t, T['rel1'], T['how'])
    aim = 0.42
    expr = 'determined' if t < T['rel1'] + 0.6 else 'proud'
    look = (0.9, -0.3)
    mongol_archer(pn, ARX, GY, ARK, 1, d_, 'yisungge', expr, rel=rel, aim=aim, arrow_on=t < T['rel1'], look=look,
                  blink=blink_at(t, 2), vib=(t - T['rel1']) * 1.0 if T['rel1'] <= t < T['rel1'] + 0.4 else 0.0)
    if T['rel1'] <= t < T['rel1'] + 0.5:
        # the arrow leaves along the aim line, fast
        u = (t - T['rel1'])
        J0 = joints(pose('idle', torso=-2, head=1), 1)
        hands = lb.archer_hands(1, 1.0, J0['neck'], aim=aim)
        g = hands['F']; s = hands['B']
        ang = math.atan2(g[1] - s[1], g[0] - s[0])
        dist = 4200 * u
        nx = ARX + (s[0] + math.cos(ang) * dist) * ARK; ny = GY + (s[1] + math.sin(ang) * dist) * ARK
        pn.push(nx, ny, ARK); mongol_arrow(pn, (0, 0), ang); pn.pop()
        speed_lines(pn, nx, ny, math.cos(ang), math.sin(ang), t, length=300, n=7, spread=30, seed=5)
        if u < 0.12: ring(pn, ARX + g[0] * ARK, GY + g[1] * ARK, t, T['rel1'], WHITE, 20, 90)
    cap_shade(pn, 60)
    tag(pn, 730, 560, 'LIKELY 1224 OR 1225', 42, pop(t, T['y1225'] - 0.05), rot_=-3, sub='AFTER THE KHWAREZM CAMPAIGN')
def cam_shot(t, sc, ox, oy):
    z = keys(t, [(T['s1'], 1.18, None), (T['rel1'] - 0.05, 1.28, eio), (T['rel1'] + 0.6, 1.08, eio)])
    return camfocus(z * sc, ARX + 140, GY - 300, 470, 900, ox, oy)

# ---------------- 3. the shot carved into granite ----------------
STX, STK = 560, 2.15
def sc_carve(base, pn, t):
    steppe(base, pn, t, 0.0, tufts=True, par=False)
    cv = clamp(P(t, T['carved'] - 0.15, T['stone3'] - T['carved'] + 0.1))
    stele(pn, STX, GY + 40, STK, carve=cv)
    # carve point: a bright incision with stone chips, straight ahead particles
    if 0 < cv < 1:
        k5 = clamp(cv * 5); i = min(4, int(cv * 5)); u = k5 - int(k5) if cv * 5 < 5 else 1
        w_, h_ = 74 * PR.CM, 202 * PR.CM
        starts = (-h_ + 22, -h_ + 56, -h_ + 56, -h_ + 38, -h_ + 56); ends = (-h_ * 0.18, -h_ * 0.12, -h_ * 0.30, -h_ * 0.20, -h_ * 0.55)
        xs = [-w_ / 2 + 16 + j * (w_ - 32) / 4 for j in range(5)]
        i = min(4, int(cv * 5)); u = cv * 5 - i
        cx = STX + xs[i] * STK; cy = GY + 40 + lerp(starts[i], ends[i], u) * STK
        pn.circ(cx, cy, 10, fill=(255, 236, 190, 220))
        particles(pn, 'chips', cx, cy, t, t - (t * 7 % 0.14), 0.7, seed=int(t * 7), col=(200, 190, 180))
    cap_shade(pn, 60)
    if t >= T['stone3'] + 0.05:
        stamp(pn, 540, 700, 'PROVEN', t - (T['stone3'] + 0.05), 120, rot_=-7)
def cam_carve(t, sc, ox, oy):
    z = keys(t, [(T['s3'], 1.0, None), (T['stone3'], 1.12, eio)])
    return camfocus(z * sc, STX, GY - 260, 540, 860, ox, oy)

# ---------------- 4. still in a museum in Saint Petersburg ----------------
def sc_museum(base, pn, t):
    bgp(base, mb.env_museum(), 0.3)
    pn.rect(-400, 1222, 1480, 2800, fill=(84, 62, 48, 0))
    # plinth and stele
    stele(pn, 420, 1250, 1.9, carve=1.0, base=False)
    pn.rect(420 - 140, 1250, 420 + 140, 1290, fill=(56, 44, 38), outline=INK, width=3, r=4)
    for px in (150, 690):     # rope barrier posts
        pn.rect(px - 8, 1180, px + 8, 1330, fill=(150, 116, 60), outline=INK, width=2.4)
        pn.circ(px, 1176, 12, fill=(196, 150, 72), outline=INK, width=2.4)
    pn.line(PR.smooth([(150, 1190), (420, 1236), (690, 1190)], False, 8), (150, 40, 36), 6, caps=False)
    # the Keeper walks in from the right and stops to look up at the stone
    arrive = T['sits']
    if t < arrive:
        u = eo3(P(t, T['s4'] - 0.2, arrive - T['s4'] + 0.2))
        x = lerp(1200, 880, u)
        s_ = math.sin(t * 9)
        p = pose('walk', thF=20 * s_, thB=-20 * s_, shF=-max(0, -s_) * 26, shB=-max(0, s_) * 26, uaF=-14 * s_, uaB=14 * s_)
        figure(pn, x, 1370, 1.75, -1, p, 'mkeeper', 'neutral', look=(-0.8, -0.2), blink=blink_at(t, 1))
    else:
        ex = 'awe' if t > T['museum'] else 'surprised'
        p = pose('point', torso=-3, head=-6) if t > T['museum'] + 0.4 else pose('idle', head=-6)
        figure(pn, 880, 1370, 1.75, -1, p, 'mkeeper', ex, look=(-0.7, -0.6), blink=blink_at(t, 1))
    cap_shade(pn, 70)
    tag(pn, 700, 470, 'HERMITAGE MUSEUM', 50, pop(t, T['saint'] - 0.08), rot_=3, sub='ON DISPLAY THERE SINCE 1936')
def cam_museum(t, sc, ox, oy):
    z = keys(t, [(T['s4'], 1.0, None), (T['museum'], 1.08, eio)])
    return camfocus(z * sc, 600, 1000, 540, 960, ox, oy)

# ---------------- 5. Yisungge, son of Qasar, nephew of Genghis Khan ----------------
OUT.update({
    'genghis': dict(tunic=(232, 228, 214), sleeve=(232, 228, 214), hose=(80, 70, 60), boot=(46, 34, 28), hat='mongol', cap=(238, 234, 222),
                    fur=(176, 164, 140), trim=(200, 180, 120), braids=(150, 146, 140), beard=(160, 156, 150), beard_style='long',
                    wide_belt=(70, 44, 30), plaques=(236, 196, 96)),
    'qasar':   dict(tunic=(72, 92, 70), sleeve=(72, 92, 70), hose=(80, 70, 60), boot=(46, 34, 28), hat='mongol', cap=(92, 60, 46),
                    fur=(140, 106, 70), trim=(200, 160, 96), braids=(60, 48, 36), beard=(60, 48, 36), beard_style='goatee',
                    wide_belt=(70, 44, 30), plaques=(214, 176, 90)),
})
def step(pn, x, y, wdt=230):
    pn.rect(x - wdt / 2, y, x + wdt / 2, y + 46, fill=(176, 160, 130), outline=INK, width=3, r=6)
    pn.rect(x - wdt / 2 + 8, y + 8, x + wdt / 2 - 8, y + 14, fill=light((176, 160, 130), 0.3), r=3)

def sc_family(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    floor(pn, 1300)
    tree = P(t, T['nephew'] - 0.1, 0.45)
    et = eio(tree)
    yx = lerp(540, 780, et); yk = lerp(1.75, 1.3, et); yy = 1300
    ys = pop(t, T['yis'] - 0.12)
    if ys > 0:
        figure(pn, yx, yy, yk * ys, -1 if tree > 0.5 else 1, pose('idle', head=3), 'yisungge',
               'proud' if t < T['nephew'] else 'happy', look=(-0.7, -0.2) if tree > 0.5 else (0.3, 0), blink=blink_at(t, 3))
    if tree > 0:
        a = eoback(tree)
        # Qasar on a stepped platform above Yisungge, Genghis Khan beside Qasar (brothers)
        pn.rect(560, 760, 1000, 800, fill=(176, 160, 130), outline=INK, width=3, r=6)
        pn.rect(80, 760, 520, 800, fill=(176, 160, 130), outline=INK, width=3, r=6)
        for x_ in (600, 960, 120, 480): pn.rect(x_ - 10, 800, x_ + 10, 1300, fill=WOOD, outline=INK, width=3)
        figure(pn, 780, 760, 1.15 * a, -1, pose('idle'), 'qasar', 'neutral', look=(-0.6, 0), blink=blink_at(t, 4))
        gk = pop(t, T['genghis'] - 0.1)
        if gk > 0:
            figure(pn, 300, 760, 1.2 * gk, 1, pose('idle', head=-2), 'genghis', 'determined', look=(0.6, 0), blink=blink_at(t, 5))
        lc = (120, 96, 66)
        arrow_line(pn, (780, 830), (780, 900), lc, 7, 24, p=clamp(tree * 1.3))
        if gk > 0:
            pn.line([(420, 600), (lerp(420, 660, eo3(gk)), 600)], lc, 7)
            pn.text(540, 560, 'BROTHERS', 34, MUTED, 'Black', 'mm', True)
            pn.text(300, 850, 'GENGHIS KHAN', 40, INK, 'Black', 'mm', True)
        pn.text(780, 850, 'QASAR', 40, INK + (int(255 * clamp(tree * 2)),), 'Black', 'mm', True)
    tag(pn, 360, 1000, 'SON OF QASAR', 50, pop(t, T['yis'] + 0.45) * (1 - P(t, T['nephew'] - 0.1, 0.15)), rot_=-4)
    tag(pn, 300, 1120, 'YISÜNGGE', 46, pop(t, T['nephew'] + 0.15), rot_=3, sub='c. 1190 TO c. 1270')
    cap_shade(pn, 40)
    pn.text(540, 300, 'PORTRAITS SIMPLIFIED', 26, MUTED + (int(200 * clamp(tree * 2)),), 'Bold', 'mm', sp=3)

# ---------------- 6. short enough to shoot from a galloping horse ----------------
HV = 950.0
def sc_gallop(base, pn, t):
    t0 = T['s7']
    camx = HV * (t - t0 + 2.0)
    steppe(base, pn, t, camx)
    ph = (t * 2.3) % 1.0
    d_, rel = shoot_draw(t, T['rel6'], T['shoot7'] - 0.25)
    if t > T['rel6'] + 0.6: d_, rel = 0.0, 0.0
    hx, hy = 470, GY + 70
    info = mounted_archer(pn, hx, hy, 1.15, 1, ph, 1.0, d_, 'yisungge', 'determined', rel=rel, aim=0.06,
                          arrow_on=t < T['rel6'] or t > T['rel6'] + 0.6, blink=blink_at(t, 2),
                          vib=(t - T['rel6']) if T['rel6'] <= t < T['rel6'] + 0.4 else 0.0)
    # dust kicked up behind the hooves
    for j in range(4):
        tt0 = t - ((t * 2.3 + j * 0.25) % 1.0) / 2.3
        particles(pn, 'dust', hx - 150 + j * 30, GY + 70, t, tt0, 0.6, seed=40 + j, ground=GY + 76)
    speed_lines(pn, hx - 60, GY - 120, 1, 0, t, length=380, n=8, spread=200, seed=9, alpha=150)
    if T['rel6'] <= t < T['rel6'] + 0.45:
        u = t - T['rel6']
        ax_ = hx + 240 + 3600 * u; ay_ = hy - 330 - 120 * u
        pn.push(ax_, ay_, 1.15); mongol_arrow(pn, (0, 0), -0.06); pn.pop()
        speed_lines(pn, ax_, ay_, 1, -0.06, t, length=300, n=6, spread=24, seed=7)
    cap_shade(pn, 60)
    if 'bow' in info:
        bw = info['bow']['grip']
        gx = hx + (bw[0] - 0) * 0 + 0
    tg = pop(t, T['short7'] - 0.05) * (1 - P(t, T['shoot7'] - 0.2, 0.2))
    tag(pn, 790, 520, 'ABOUT 4.5 FT', 50, tg, rot_=3, sub='ALONG THE CURVE')
def cam_gallop(t, sc, ox, oy):
    z = keys(t, [(T['s7'], 1.06, None), (T['rel6'] - 0.1, 1.16, eio), (T['rel6'] + 0.7, 1.06, eio)])
    return camfocus(z * sc, 520, 1000, 520, 940, ox, oy)

# ---------------- 7 and 8. unstrung it curves the wrong way; stringing bends it back ----------------
KX, KY, KK = 290, 1300, 2.45
def bow_state(t):
    """-1 unstrung until 'bends', eased to braced by 'itself' with a small overshoot and settle."""
    if t < T['bends'] - 0.1: return -1.0
    u = P(t, T['bends'] - 0.1, T['itself'] - T['bends'] + 0.2)
    return lerp(-1.0, 0.0, eoback(u, 1.2))

def sc_reflex(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    floor(pn, KY)
    st = bow_state(t)
    drawing = t > T['even'] - 0.15
    dr = 0.42 * eio(P(t, T['even'] - 0.15, 0.55)) if drawing else 0.0
    J0 = joints(pose('idle'), 1)
    hands = {'F': (88, -150)}
    if drawing:
        hb = lb.archer_hands(1, dr, J0['neck'])
        hands = {'F': hb['F'], 'B': hb['B'], 'elB': hb['elB']}
    info = {}
    def held(pn_, J):
        g = J['haF']
        if drawing:
            s = J['haB']; s_ = PR.mbow_string_bend(g, s)
            info['b'] = mongol_bow(pn_, g[0], g[1], 1, s_, string_to=s)
        else:
            info['b'] = mongol_bow(pn_, g[0], g[1], 1, st, strung=st > -0.15, hl_back=0.0)
    ex = 'thinking' if t < T['wrong'] else ('surprised' if t < T['s10'] else ('determined' if t < T['loaded'] else 'smug'))
    figure(pn, KX, KY, KK, 1, pose('idle', head=2), 'mkeeper', ex, look=(0.9, -0.1), hands=hands, held=held, blink=blink_at(t, 1))
    gxw, gyw = KX + hands['F'][0] * KK, KY + hands['F'][1] * KK
    # 7: the curve goes the wrong way, away from the archer
    if t < T['s10']:
        a = P(t, T['curves'] - 0.1, 0.5)
        if a > 0:
            pts = [(gxw + 40 + 150 * math.sin(math.radians(a_ * a)), gyw - 150 * math.cos(math.radians(a_ * a)) * 0 + (-120 + 240 * (a_ / 180)))
                   for a_ in range(0, 181, 15)]
        aw = P(t, T['away'] - 0.05, 0.4)
        if aw > 0:
            arrow_line(pn, (gxw + 170, gyw), (gxw + 470, gyw), RUST, 12, 40, p=eo3(aw))
            pn.text(gxw + 330, gyw - 60, 'AWAY', 50, RUST + (int(255 * clamp(aw * 2)),), 'Black', 'mm', True)
        tag(pn, 760, 520, 'REFLEX', 60, pop(t, T['wrong'] - 0.05), rot_=-4, sub='TIPS CURL TOWARD THE TARGET')
    else:
        # 8: bending arrows while it is strung, then a tension gauge fills
        ba = P(t, T['bends'] - 0.15, 0.35) * (1 - P(t, T['loaded'] - 0.2, 0.2))
        if ba > 0:
            for sg in (-1, 1):
                a0 = (gxw + 170, gyw + sg * 200); a1 = (gxw + 40, gyw + sg * 222)
                arrow_line(pn, a0, a1, (40, 90, 150), 10, 30, p=eo3(ba))
        v = 0.62 * eoback(P(t, T['loaded'] - 0.1, 0.4)) + 0.3 * eio(P(t, T['even'] - 0.15, 0.6))
        if t > T['loaded'] - 0.15:
            bar(pn, 930, 1180, 80, 460, v, 'TENSION', RUST, 'ILLUSTRATIVE')
    cap_shade(pn, 40)
def cam_reflex(t, sc, ox, oy):
    z = keys(t, [(T['s8'], 1.0, None), (T['wrong'], 1.08, eio), (T['s10'], 1.0, eio), (T['loaded'], 1.08, eio)])
    return camfocus(z * sc, 540, 960, 540, 940, ox, oy)

# ---------------- 9. three layers: horn squeezed, sinew stretched, core holds them ----------------
LX, LY, LN, LT = 540, 900, 760, 150
def sc_layers(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    floor(pn, 1300)
    # where this piece comes from: the braced bow in a round inset, box on the upper limb
    ia = 1 - P(t, T['inside'] - 0.2, 0.3)
    if ia > 0:
        pn.circ(200, 420, 150, fill=(250, 244, 228, int(255 * ia)), outline=INK + (int(255 * ia),), width=4)
        pn.push(200, 420, 1.25 * ia)
        mongol_bow(pn, 0, 0, 1, 0.0)
        pn.rect(-30, -84, 24, -40, outline=AMBER, width=5, r=4)
        pn.pop()
        pn.line([(200 - 3 * 1.25, 420 - 62 * 1.25), (LX - LN / 2 + 20, LY - 90)], AMBER + (int(160 * ia),), 4)
    # the limb piece: exploded on "three", together and bent later
    sep = 60 * eoback(P(t, T['three'] - 0.05, 0.35)) * (1 - eio(P(t, T['inside'] - 0.1, 0.4)))
    bend = 0.0
    bend = 0.8 * eio(P(t, T['squeezed'] - 0.15, 0.35)) * (1 - eio(P(t, T['s15'] - 0.3, 0.3)))
    hlh = win(t, T['horn13'] - 0.05, T['s14'], 0.15, 0.2)
    hls = win(t, T['sinew14'] - 0.05, T['s15'], 0.15, 0.2)
    hlc = win(t, T['core'] - 0.05, T['holds'] + 0.4, 0.15, 0.2)
    birch = t > T['together'] - 0.05
    if sep > 0.5:
        # three separate layers floating apart with numbers (exploded view)
        for i, (o0, o1, col, hl) in enumerate(((LT * 0.12, LT * 0.5, PR.SINEW, hls), (-LT * 0.2, LT * 0.12, PR.MCORE, hlc), (-LT * 0.5, -LT * 0.2, PR.MHORN, hlh))):
            dy = (-sep, 0, sep)[i]
            pn.rect(LX - LN / 2, LY - o1 + dy, LX + LN / 2, LY - o0 + dy, fill=lerpc(col, AMBER, hl), outline=INK, width=3)
            n_ = pop(t, T['three'] + 0.1 * i)
            if n_ > 0:
                pn.push(LX - LN / 2 - 50, LY - (o0 + o1) / 2 + dy, n_)
                pn.circ(0, 0, 30, fill=INK); pn.text(0, 2, str(i + 1), 40, PARCH, 'Black', 'mm', True); pn.pop()
    else:
        ctr, nrm = limb_layers(pn, LX, LY, LN, LT, bend=bend, hl_horn=hlh, hl_sinew=hls, hl_core=hlc,
                               arrows=0.0, t=t, birch=birch)
        # squeezed: compression arrows on the belly; stretched: tension arrows on the back
        ca = P(t, T['squeezed'] - 0.1, 0.3) * (1 - P(t, T['s14'] - 0.1, 0.15))
        ta = P(t, T['stretched'] - 0.1, 0.3) * (1 - P(t, T['s15'] - 0.2, 0.15))
        n = len(ctr) - 1
        for i0, sg in ((3, -1), (n - 3, 1)):
            (cx, cy), (nx, ny) = ctr[i0], nrm[i0]
            tx, ty = ctr[i0 + 1][0] - ctr[i0 - 1][0], ctr[i0 + 1][1] - ctr[i0 - 1][1]; Ln = math.hypot(tx, ty); tx, ty = tx / Ln, ty / Ln
            if ca > 0:
                pC = (cx + nx * (-LT * 0.5 - 40), cy + ny * (-LT * 0.5 - 40))
                arrow_line(pn, (pC[0] + sg * tx * 110, pC[1] + sg * ty * 110), pC, (40, 90, 150), 10, 32, p=eo3(ca))
            if ta > 0:
                pT = (cx + nx * (LT * 0.5 + 44), cy + ny * (LT * 0.5 + 44))
                arrow_line(pn, pT, (pT[0] + sg * tx * 110, pT[1] + sg * ty * 110), RUST, 10, 32, p=eo3(ta))
    callout(pn, LX + 200, LY + LT * 0.36 + 12, 820, 1180, 'HORN · BELLY', P(t, T['horn13'] - 0.05, 0.4) * (1 - P(t, T['s14'], 0.2)), 38, hl=True)
    callout(pn, LX + 200, LY - LT * 0.32 - 8, 820, 610, 'SINEW · BACK', P(t, T['sinew14'] - 0.05, 0.4) * (1 - P(t, T['s15'], 0.2)), 38, hl=True)
    callout(pn, LX - 120, LY + 4, 300, 1180, 'CORE', P(t, T['core'] - 0.05, 0.4) * (1 - P(t, T['together'], 0.2)), 40, hl=True)
    if birch:
        callout(pn, LX - 200, LY - LT * 0.5 - 10, 330, 620, 'BIRCH BARK WRAP', P(t, T['together'] - 0.05, 0.4), 36)
    cap_shade(pn, 40)
def cam_layers(t, sc, ox, oy):
    z = keys(t, [(T['s12'], 1.0, None), (T['squeezed'], 1.07, eio), (T['s14'], 1.0, eio), (T['stretched'], 1.07, eio), (T['s15'], 1.0, eio)])
    return camfocus(z * sc, LX, LY, 540, 900, ox, oy)

# ---------------- 10. more energy than wood alone: a short bow pulls like a long one ----------------
def sc_compare(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    floor(pn, 1300)
    grow = eio(P(t, T['short17'] + 0.1, T['pulls'] - T['short17'] + 0.2))
    # rack: two posts and a bar, bows hang by their grips
    pn.rect(150, 300, 930, 330, fill=WOOD, outline=INK, width=3, r=4)
    for px in (150, 930): pn.rect(px - 14, 300, px + 14, 1300, fill=WOOD, outline=INK, width=3)
    # left: the composite bow (short), right: a plain wooden bow (short, then long)
    pn.push(330, 720, 2.3); mongol_bow(pn, 0, 0, 1, 0.0); pn.pop()
    L_self = lerp(190, 330, grow)
    pn.push(740, 720, 1.75); lb.longbow(pn, 0, 0, 1, 0.0, L=L_self, w0=lerp(11, 12, grow)); pn.pop()
    for bx in (330, 740): pn.line([(bx, 330), (bx, 720 - 8)], ROPE, 3)
    pn.text(330, 1060, 'HORN + SINEW', 38, INK, 'Black', 'mm', True)
    pn.text(740, 1060, 'WOOD ONLY', 38, INK, 'Black', 'mm', True)
    # energy gauges, unnumbered
    ea = P(t, T['energy'] - 0.2, 0.5)
    if ea > 0:
        v_c = 0.85 * eoback(ea)
        v_w = lerp(0.42 * eoback(ea), 0.85, eio(P(t, T['pulls'] - 0.1, 0.6)))
        bar(pn, 330, 1260, 90, 150, v_c, '', RUST)
        bar(pn, 740, 1260, 90, 150, v_w, '', (150, 110, 60))
    if t > T['long17'] - 0.1:
        pn.push(535, 1185, pop(t, T['long17'] - 0.1)); pn.text(0, 0, '=', 90, INK, 'Black', 'mm', True); pn.pop()
    tag(pn, 540, 470, 'ENERGY STORED', 40, pop(t, T['energy'] - 0.1) * (1 - P(t, T['s17'], 0.15)), rot_=-2, sub='ILLUSTRATIVE, NOT TO SCALE')
    cap_shade(pn, 40)
def cam_compare(t, sc, ox, oy):
    z = keys(t, [(T['s16'], 1.0, None), (T['long17'], 1.06, eio)])
    return camfocus(z * sc, 540, 800, 540, 860, ox, oy)

# ---------------- 11. glued and dried for months (inside a ger) ----------------
def ger(base, pn, t):
    base.paste(Image.new('RGB', (W, H), (110, 84, 62)))
    # felt wall with the lattice (khana) showing, roof poles to the crown, warm light from the crown
    pn.rect(-300, 300, 1380, 1260, fill=(196, 176, 142))
    for x in range(-300, 1400, 80):
        pn.line([(x, 360), (x + 220, 1240)], (150, 110, 70), 6, caps=False)
        pn.line([(x + 220, 360), (x, 1240)], (150, 110, 70), 6, caps=False)
    pn.rect(-300, 300, 1380, 360, fill=(164, 60, 48))
    for x in range(-300, 1400, 120):
        pn.line([(540, -200), (x, 320)], (170, 70, 52), 8, caps=False)
    pn.rect(-300, 1240, 1380, 2800, fill=(150, 70, 56))
    for x in range(-200, 1300, 160):
        pn.poly([(x, 1300), (x + 60, 1270), (x + 120, 1300), (x + 60, 1330)], fill=(200, 160, 90))
    lx = 540 + 260 * math.sin((t - T['s18']) * 0.9)
    pn.poly([(470, -100), (610, -100), (lx + 300, 1260), (lx - 300, 1260)], fill=(255, 236, 190, 40))

def sc_glue(base, pn, t):
    ger(base, pn, t)
    # the unstrung bow, bound to a forming board with cords while the sinew dries (reconstruction)
    pn.push(540, 760, 2.1)
    pn.rect(-150, -14, 150, 14, fill=WOOD, outline=INK, width=3, r=4)
    mongol_bow(pn, 0, 0, 1, -0.55, strung=False, hl_back=win(t, T['glued'] - 0.1, T['dried'], 0.1, 0.2) * 0.6)
    for x_ in (-110, 0, 110):
        pn.line([(x_, -16), (x_ + 6, 16)], PR.ROPE if hasattr(PR, 'ROPE') else ROPE, 3)
    pn.pop()
    pn.line([(540, 300), (540, 740)], (90, 70, 50), 4)
    # glue pot on a low table
    pn.rect(250, 1180, 520, 1210, fill=WOOD, outline=INK, width=3, r=4)
    for lx_ in (270, 500): pn.rect(lx_ - 8, 1210, lx_ + 8, 1260, fill=WOOD_D, outline=INK, width=2)
    pn.ell(380, 1150, 70, 22, fill=(120, 80, 50), outline=INK, width=3)
    pn.rect(310, 1100, 450, 1150, fill=(120, 80, 50), outline=INK, width=3, r=10)
    pn.ell(380, 1100, 70, 20, fill=(176, 120, 50), outline=INK, width=3)
    for i in range(3):
        ph = (t * 0.7 + i * 0.33) % 1.0
        pn.circ(380 + 20 * math.sin(i * 2 + t * 2), 1080 - 120 * ph, 10 + 8 * ph, fill=(255, 250, 240, int(110 * (1 - ph))))
    # months: moons appear one by one
    for i in range(4):
        a = pop(t, T['dried'] + 0.18 * i)
        if a <= 0: continue
        cx = 300 + i * 160; cy = 470
        pn.push(cx, cy, a)
        pn.circ(0, 0, 40, fill=(250, 240, 200), outline=INK, width=3)
        pn.circ(18 - i * 8, -6, 36, fill=(196, 176, 142))
        pn.pop()
    tag(pn, 760, 1040, 'ANIMAL GLUE', 48, pop(t, T['glued'] + 0.1) * (1 - P(t, T['months'] - 0.1, 0.15)), rot_=4, string_to=(430, 1110))
    tag(pn, 760, 1040, 'MONTHS TO CURE', 44, pop(t, T['months'] + 0.05), rot_=-3, sub='BOUND TO A FORM: RECONSTRUCTION')
    cap_shade(pn, 60)

# ---------------- 12 and 13. finale: small enough for the saddle; the shot again ----------------
def sc_saddle(base, pn, t):
    t0 = T['s19']
    camx = HV * (t - t0 + 6.0)
    steppe(base, pn, t, camx)
    ph = (t * 2.3) % 1.0
    hx, hy = 520, GY + 70
    mounted_archer(pn, hx, hy, 1.2, 1, ph, 1.0, 0.0, 'yisungge', 'happy', arrow_on=True, blink=blink_at(t, 2))
    for j in range(4):
        tt0 = t - ((t * 2.3 + j * 0.25) % 1.0) / 2.3
        particles(pn, 'dust', hx - 160 + j * 30, GY + 70, t, tt0, 0.6, seed=50 + j, ground=GY + 76)
    speed_lines(pn, hx - 60, GY - 120, 1, 0, t, length=380, n=8, spread=200, seed=9, alpha=150)
    cap_shade(pn, 60)
def cam_saddle(t, sc, ox, oy):
    z = keys(t, [(T['s19'], 1.1, None), (T['saddle'], 1.18, eio)])
    return camfocus(z * sc, 560, 1000, 540, 940, ox, oy)

FIN_RATE = U_H / (T['hundred19'] - T['rel19'])
T['land19'] = T['rel19'] + 1.0 / FIN_RATE
def sc_final(base, pn, t):
    trel = T['rel19']
    if t < trel + 0.12:
        steppe(base, pn, t, 0.0, par=False)
        d_ = 1.0 if t > T['could'] - 0.05 else 0.8
        rel = eo3(P(t, trel, 0.18))
        mongol_archer(pn, ARX, GY, ARK, 1, 1.0, 'yisungge', 'determined', rel=rel, aim=0.42, arrow_on=t < trel, blink=0.0,
                      vib=(t - trel) if t >= trel else 0.0)
        cap_shade(pn, 60)
        return
    u = FIN_RATE * (t - trel)
    landed = t >= T['land19']
    flight_frame(base, pn, t, min(1.0, u), landed_t=T['land19'] if landed else None, h0=60)
    cap_shade(pn, 70)
    hud_counter[0] = (536 * eo2(min(1.0, u)), P(t, trel + 0.1, 0.25))
    tag(pn, 760, 640, 'EST. 536 M', 54, pop(t, T['land19'] + 0.1), rot_=4, sub='ABOUT 586 YARDS')
def cam_final(t, sc, ox, oy):
    if t < T['rel19'] + 0.12:
        return camfocus(1.22 * sc, ARX + 140, GY - 300, 470, 900, ox, oy)
    return sc, ox, oy

# ---------------- scene list ----------------
SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['s1'], sc_shot, cam_shot, None),
    (T['s3'], sc_carve, cam_carve, None),
    (T['s4'], sc_museum, cam_museum, 'slide'),      # chapter: the stone today
    (T['s5'], sc_family, None, 'dissolve'),
    (T['s7'], sc_gallop, cam_gallop, 'slide'),      # chapter: the bow on horseback
    (T['s8'], sc_reflex, cam_reflex, 'slide'),      # chapter: how it works
    (T['s12'], sc_layers, cam_layers, None),
    (T['s16'], sc_compare, cam_compare, None),
    (T['s18'], sc_glue, None, 'dissolve'),
    (T['s19'], sc_saddle, cam_saddle, 'slide'),     # chapter: back to the shot
    (T['could'] - 0.02, sc_final, cam_final, None),
]
HUD = {sc_hook: hud_hook, sc_final: hud_hook}
SLIDE = 0.35
DISS = 0.3

CAM.punch = [(T['hundred0'], 0.05), (T['rel1'], 0.06), (T['stone3'] + 0.05, 0.07), (T['rel6'], 0.05), (T['loaded'], 0.05),
             (T['hundred19'], 0.06)]
CAM.shake = [(T['land0'], 12, 0.35), (T['stone3'] + 0.05, 8, 0.25), (T['land19'], 12, 0.35)]
FLASH = [(T['land0'], 0.12, (255, 240, 214), 100)]

def scene_idx(t):
    return max(i for i, s in enumerate(SCENES) if s[0] <= t)

def render_scene(i, t):
    _, fn, cam, _ = SCENES[i]
    CAM.extra = cam; CAM.set(t)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay)
    hud_counter[0] = None
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
    C = [(0.0, 'whiz', 1.0), (0.02, 'whooshlow', 0.5), (T['hundred0'] - 0.05, 'riser', 0.3), (T['land0'], 'thunk', 1.0), (T['land0'] + 0.01, 'thud', 0.7),
         (T['metres0'] - 0.05, 'pop', 0.5),
         (T['how'] - 0.1, 'cloth', 0.4), (T['how'] + 0.2, 'stretch', 0.7), (T['rel1'] - 0.02, 'twang', 1.0), (T['rel1'] + 0.02, 'whiz', 0.8),
         (T['rel1'] + 0.5, 'rumble', 0.25), (T['rel1'] + 0.6, 'cheer', 0.5), (T['y1225'] - 0.05, 'pop', 0.5),
         (T['s3'] + 0.05, 'wind', 0.4)]
    for i in range(10): C.append((T['carved'] - 0.1 + i * (T['stone3'] - T['carved']) / 10, 'chisel', 0.6))
    C += [(T['stone3'] + 0.05, 'stamp', 1.0),
          (T['s4'] + 0.1, 'footsteps', 0.6), (T['museum'] - 0.05, 'chime', 0.3), (T['saint'] - 0.1, 'pop', 0.5),
          (T['yis'] - 0.12, 'pop', 0.6), (T['yis'] + 0.45, 'pop', 0.4), (T['nephew'] - 0.1, 'slide', 0.5), (T['nephew'] + 0.1, 'pop', 0.4),
          (T['genghis'] - 0.1, 'pop', 0.6), (T['khan'], 'horn', 0.3),
          (T['s7'], 'gallop', 0.9), (T['short7'] - 0.05, 'pop', 0.5), (T['shoot7'] - 0.2, 'stretch', 0.7), (T['rel6'] - 0.02, 'twang', 0.9),
          (T['rel6'] + 0.02, 'whiz', 0.8),
          (T['curves'] - 0.1, 'creak', 0.6), (T['wrong'] - 0.05, 'pop', 0.5), (T['away'] - 0.05, 'swish', 0.6),
          (T['bends'] - 0.1, 'creak', 0.8), (T['itself'] - 0.1, 'stretch', 0.7), (T['itself'] + 0.05, 'twang', 0.5),
          (T['loaded'] - 0.1, 'riser', 0.5), (T['even'] - 0.1, 'stretch', 0.6),
          (T['three'] - 0.05, 'pop', 0.5), (T['three'] + 0.05, 'pop', 0.4), (T['three'] + 0.15, 'pop', 0.4),
          (T['horn13'] - 0.05, 'clink', 0.4), (T['inside'] - 0.1, 'slide', 0.4), (T['squeezed'] - 0.1, 'squeeze', 0.8),
          (T['sinew14'] - 0.05, 'clink', 0.4), (T['stretched'] - 0.1, 'stretch', 0.8),
          (T['core'] - 0.05, 'knock', 0.6), (T['holds'], 'squeeze', 0.5), (T['together'] - 0.05, 'paper', 0.5),
          (T['energy'] - 0.2, 'riser', 0.5), (T['energy'] + 0.1, 'pop', 0.5), (T['short17'] + 0.1, 'creak', 0.6), (T['pulls'], 'stretch', 0.5),
          (T['long17'] - 0.1, 'chime', 0.5),
          (T['glued'], 'slosh', 0.5), (T['glued'] + 0.1, 'pop', 0.4)]
    for i in range(4): C.append((T['dried'] + 0.18 * i, 'tick', 0.6))
    C += [(T['months'] + 0.05, 'pop', 0.4),
          (T['s19'], 'gallop', 0.9), (T['could'] - 0.05, 'stretch', 0.6), (T['rel19'] - 0.02, 'twang', 1.0), (T['rel19'] + 0.02, 'whiz', 1.0),
          (T['hundred19'] - 0.1, 'riser', 0.3), (T['land19'], 'thunk', 1.0), (T['land19'] + 0.01, 'thud', 0.7), (T['land19'] + 0.1, 'pop', 0.4)]
    # counter ticks while it runs
    for t0, t1 in ((0.0, T['land0']), (T['rel19'] + 0.1, T['land19'])):
        k = t0
        while k < t1: C.append((round(k, 3), 'tick', 0.25)); k += 0.11
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
        for k, v in sorted(T.items(), key=lambda x: x[1] if x[1] is not None else 0): print(f'{v:6.2f} {k}')

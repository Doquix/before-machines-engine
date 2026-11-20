"""E020 Colosseum lifts: beat table and scenes (imported by render_cl.py)."""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
from props import tag, stamp, arrow as arrow_line
import cl
from cl import (venabulum, lion, tiger, venator, capstan, lift_shaft, lift_cage, trapdoor, arena_floor, torch, pulley, pusher, crowd,
                SAND, SAND_D, OAK, OAK_L, TUFA, BRICK)
import env
from fx import smear, speed_lines, focus_lines, impact, particles
from detail import shade, light, rope, wood_plank, rivet

env.env_arena = cl.env_arena; env.env_hypogeum = cl.env_hypogeum; env.env_section = cl.env_section

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
PH = {}
for wd in WORDS: PH.setdefault(wd['p'], []).append(wd['t'])
def w(p, i): return PH[p][i]
def S(p): return CAPS[p]['s']
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))

T = dict(
    s0=S(0), gladiator=w(0, 1), tigers=w(0, 2), burst=w(0, 3), trap0=w(0, 6), floor0=w(0, 11),
    s1=S(1), real=w(1, 3),
    s2=S(2), colosseum=w(2, 2), machine=w(2, 5), ride=w(2, 7), day=w(2, 9),
    s3=S(3), elevator3=w(3, 1),
    s4=S(4), sand4=w(4, 2), hypogeum=w(4, 5),
    s5=S(5), maze=w(5, 1), tunnels=w(5, 3), cells=w(5, 5),
    s6=S(6), lion6=w(6, 1), waited=w(6, 2), wooden=w(6, 5), cage6=w(6, 6),
    s7=S(7), nothing=w(7, 0), bigger=w(7, 1), fit=w(7, 3),
    s8=S(8), beside=w(8, 0), stood=w(8, 2), capstan8=w(8, 4),
    s9=S(9), upright=w(9, 1), winch=w(9, 2), two9=w(9, 3), stories=w(9, 4), tall=w(9, 5),
    s10=S(10), eight=w(10, 0), pushed=w(10, 2), bars=w(10, 4), circle=w(10, 7),
    s11=S(11), four=w(11, 0), each=w(11, 2), level=w(11, 3),
    s12=S(12), ropes=w(12, 0), wound=w(12, 1), shaft=w(12, 4),
    s13=S(13), cage13=w(13, 2), climbed=w(13, 3), twenty=w(13, 5), feet=w(13, 7),
    s14=S(14), top=w(14, 2), trap14=w(14, 4), swung=w(14, 6), down=w(14, 7), ramp=w(14, 10),
    s15=S(15), lion15=w(15, 1), ran=w(15, 2), straight=w(15, 5), light15=w(15, 8),
    s16=S(16), fifty=w(16, 1), thousand=w(16, 2), people=w(16, 3), appear=w(16, 6), nowhere=w(16, 8),
    s17=S(17), dozens=w(17, 0), lifts=w(17, 3), hidden=w(17, 5), floor17=w(17, 8),
    s18=S(18), hunter=w(18, 2), never=w(18, 3), where=w(18, 5), next18=w(18, 7), rise=w(18, 10),
    s19=S(19), opens=w(19, 3), gladiator19=w(19, 5), watching=w(19, 8), roman=w(19, 10), elevator19=w(19, 11),
    end=VO_END,
)
CAM.drift = 0.5
CAM.punch = [(T['burst'], 0.07), (T['real'], 0.06), (T['eight'], 0.05), (T['swung'] + 0.25, 0.05), (T['light15'], 0.07), (T['roman'], 0.06)]
CAM.shake = [(T['burst'] + 0.05, 9, 0.3), (T['burst'] + 0.87, 12, 1.5), (T['swung'] + 0.3, 7, 0.25)]
FLASH = [(T['light15'], 0.14, (255, 244, 214), 100)]

FLOOR = 1250       # arena floor line in arena scenes
HFLOOR = 1380      # hypogeum floor line in section scenes

def bgp(base, name, par=0.5):
    img = env.get(name)
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def antic(t, t0, d=0.35, back=0.18, ad=0.35):
    u = (t - t0) / d
    if u <= 0: return 0.0
    if u < ad: return -back * eio(u / ad)
    v = clamp((u - ad) / (1 - ad))
    return lerp(-back, 1.0, eoback(v, 1.6))

def vdim(pn, x, y0, y1, label, p, col=INK, sz=40, tick=18):
    """Vertical dimension line drawing upward from y0 to y1 with a label beside it."""
    if p <= 0: return
    e = eo3(p); ye = lerp(y0, y1, e)
    pn.line([(x - tick, y0), (x + tick, y0)], INK, 9); pn.line([(x - tick, y0), (x + tick, y0)], col, 4)
    pn.line([(x, y0), (x, ye)], INK, 9); pn.line([(x, y0), (x, ye)], col, 4)
    if e > 0.98: pn.line([(x - tick, y1), (x + tick, y1)], INK, 9); pn.line([(x - tick, y1), (x + tick, y1)], col, 4)
    if p > 0.5:
        s = eoback(clamp((p - 0.5) / 0.5))
        wv = pn.tw(label, sz, 'Black', True) + 30
        pn.push(x, (y0 + y1) / 2, s)
        pn.rect(-wv / 2, -sz * 0.72, wv / 2, sz * 0.72, fill=(250, 244, 228), outline=INK, width=3.4, r=10)
        pn.text(0, 2, label, sz, INK, 'Black', 'mm', True)
        pn.pop()

def xmark(pn, x, y, p, s=40, col=RUST):
    if p <= 0: return
    e = eoback(p); pn.push(x, y, e)
    for a, b in (((-s, -s), (s, s)), ((-s, s), (s, -s))):
        pn.line([a, b], INK, 20); pn.line([a, b], col, 13)
    pn.pop()

def check(pn, x, y, p, s=40, col=(70, 150, 70)):
    if p <= 0: return
    e = eoback(p); pn.push(x, y, e)
    pts = [(-s, 0), (-s * .3, s * .7), (s, -s * .8)]
    pn.line(pts, INK, 20); pn.line(pts, col, 13)
    pn.pop()

def ground_mass(pn, y, gap=None, col=SAND, under=(74, 54, 40)):
    """Arena floor with the hypogeum dark below it: everything stands on something."""
    pn.rect(-400, y + 40, 1480, 2800, fill=under)
    if gap:
        pn.rect(gap[0], y + 30, gap[1], 2800, fill=(30, 22, 18))
    arena_floor(pn, y, -400, 1480, gap=gap, depth=40)

def ghost_shaft(pn, x, y, w=220, a=1.0):
    """Shaft walls under a trap door opening, receding into the dark."""
    for i in range(6):
        yy = y + 40 + i * 60
        pn.line([(x - w / 2, yy), (x + w / 2, yy)], (90, 64, 48, int(120 * a * (1 - i / 6))), 3, caps=False)

# ---------------- arena floor seen from a low angle: trap door set into the sand ----------------
HOLE = dict(cx=560, y0=1230, y1=1310, w0=250, w1=300)
def hole_pts(H_=HOLE, cx=None):
    cx = H_['cx'] if cx is None else cx
    return [(cx - H_['w0'] / 2, H_['y0']), (cx + H_['w0'] / 2, H_['y0']), (cx + H_['w1'] / 2, H_['y1']), (cx - H_['w1'] / 2, H_['y1'])]

def sand_grain(pn, y0, seed=3):
    rnd = random.Random(seed)
    for _ in range(140):
        x = rnd.uniform(-60, 1140); y = rnd.uniform(y0, 1920)
        pn.ell(x, y, rnd.uniform(3, 9), rnd.uniform(1, 2.4), fill=SAND_D + (120,))

def hole_and_door(pn, op, cx=None, H_=HOLE):
    """Dark opening in the sand with its wooden frame; the door is hinged on the far edge and swings up toward the camera."""
    p = hole_pts(H_, cx)
    cxx = H_['cx'] if cx is None else cx
    if op > 0:
        pn.poly(p, fill=(26, 18, 14), outline=INK, width=4)
        # inner walls of the shaft in perspective
        pn.poly([p[0], p[1], (p[1][0] - 12, p[1][1] + 40), (p[0][0] + 12, p[0][1] + 40)], fill=(70, 48, 36))
        for i in range(3):
            yy = p[0][1] + 10 + i * 12
            pn.line([(p[0][0] + 6, yy), (p[1][0] - 6, yy)], (96, 66, 48), 2, caps=False)
    # frame timbers around the opening
    for a_, b_ in ((p[0], p[1]), (p[3], p[2])):
        pn.line([a_, b_], INK, 15); pn.line([a_, b_], OAK, 10)
    e = clamp(op)
    # door panel: near edge lifts from the near frame up past the far edge
    lift = 330 * math.sin(e * math.pi * 0.5 * 1.05)
    ny = lerp(p[3][1], p[0][1] - lift, e)
    nw = lerp(H_['w1'], H_['w0'] * 1.08, e)
    door = [p[0], p[1], (cxx + nw / 2, ny), (cxx - nw / 2, ny)]
    if e < 0.02:
        door = p
    pn.poly(door, fill=OAK_L, outline=INK, width=4)
    n = 5
    for i in range(1, n):
        u = i / n
        pn.line([(lerp(door[0][0], door[1][0], u), door[0][1]), (lerp(door[3][0], door[2][0], u), door[3][1])], shade(OAK_L, 0.3), 2.4, caps=False)
    if e > 0.3:   # underside battens show once the door stands up
        for u in (0.3, 0.7):
            pn.line([(lerp(door[0][0], door[3][0], u), lerp(door[0][1], door[3][1], u)), (lerp(door[1][0], door[2][0], u), lerp(door[1][1], door[2][1], u))], shade(OAK, 0.2), 7, caps=False)
    for x_ in (door[0][0] + 30, door[1][0] - 30):
        pn.circ(x_, door[0][1], 6, fill=IRON, outline=INK, width=2)
    return p

def clipped(pn, ycut, fn):
    """Draw fn(pen) on a temp layer and keep only what is above world y = ycut (out of the shaft)."""
    tmp = new_layer(); p2 = Pen(tmp, cam=pn.cam); p2.T = pn.T
    fn(p2)
    yy = int(max(0, min(tmp.height, pn.xy(0, ycut)[1])))
    if yy < tmp.height:
        tmp.paste((0, 0, 0, 0), (0, yy, tmp.width, tmp.height))
    pn.img.alpha_composite(tmp)

# ---------------- 0. hook: tigers burst up through trap doors ----------------
def tiger_path(t):
    """Returns x, y, gait, ph, f, expr, tilt. Rising nose first out of the shaft, then a leap onto the sand."""
    t0, t1, t2 = T['burst'] - 0.42, T['burst'], T['burst'] + 0.55
    if t < t0: return 560, 1760, 'crouch', 0.0, 1, 'angry', -1.0
    if t < t1:
        u = ei2(P(t, t0, t1 - t0)); return 560, lerp(1760, 1420, u), 'leap', 0.2, 1, 'roar', -1.0
    if t < t2:
        u = P(t, t1, t2 - t1)
        x = lerp(560, 820, eio(u)); y = lerp(1420, 1330, eio(u)) - 200 * math.sin(u * math.pi)
        return x, y, 'leap', 0.35 + 0.6 * u, 1, 'roar', lerp(-1.0, 0.0, eio(u))
    return 820, 1330, 'stand', 0.0, -1, ('roar' if (t - t2) % 1.6 < 0.7 else 'angry'), 0.0

def eyes_in_hole(pn, t, t0, t1, cx=560, y=1268):
    a = min(P(t, t0, 0.2), 1 - P(t, t1 - 0.1, 0.1))
    if a <= 0: return
    bl = 1 if (t * 3.1) % 1 > 0.08 else 0.2
    for sd in (-1, 1):
        pn.ell(cx + sd * 22, y, 10, 6 * bl, fill=(250, 196, 70, int(255 * a)))
        pn.circ(cx + sd * 22, y, 2.6 * bl, fill=INK + (int(255 * a),))

FIGHT0 = None
def fight_times():
    t2 = T['burst'] + 0.55            # tiger lands
    return t2, t2 + 0.32, T['s1'] - 0.05   # lands, cloud starts, cloud bursts

def hook(base, pn, t, after=False):
    bgp(base, 'arena', 0.35)
    sand_grain(pn, 1080)
    op = 1.0 if after else clamp(eoback(P(t, 0.0, 0.34), 1.3))
    p = hole_and_door(pn, op)
    land, c0, c1 = fight_times()
    if after:
        # aftermath (12 principles): the cloud bursts; both bodies are thrown out on arcs, accelerate into the ground,
        # bounce once and settle (follow through), then hold still so the moment reads
        cl.poof(pn, 470, 1120, t, c1)
        def throw(t0, p0, p1, h, dur, bounce):
            u = (t - t0) / dur
            if u <= 0: return p0, False, 0.0
            if u < 1:
                e = ei2(u)
                return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], e) - h * math.sin(u * math.pi) * (1 - u * 0.3)), False, 0.0
            v = t - t0 - dur
            return (p1[0], p1[1] - bounce * abs(math.sin(v * 14)) * math.exp(-v * 9)), True, v
        vp, v_land, v_age = throw(c1, (470, 1150), (380, 1365), 110, 0.38, 26)
        tp, t_land, t_age = throw(c1 + 0.04, (500, 1180), (830, 1360), 80, 0.42, 18)
        venabulum(pn, 560, 1380, 0.05 + 0.6 * math.exp(-max(0, t - c1 - 0.3) * 8) * math.sin(max(0, t - c1 - 0.3) * 30), back=150, L=300)
        if t_land:
            particles(pn, 'dust', tp[0], 1370, t, c1 + 0.46, 1.0, seed=12, ground=1374)
        cl.tiger(pn, tp[0], tp[1], 1.25, -1, gait='lie', expr='dead' if t_age > 0.12 else 'roar', t=0.0)
        if t_land:
            cl.claw_marks(pn, tp[0] + 20, tp[1] - 62, s=1.2, ang=1.1)
            cl.claw_marks(pn, tp[0] + 90, tp[1] - 50, s=0.9, ang=0.7, n=2, L=40)
            cl.claw_marks(pn, tp[0] - 128, tp[1] - 128, s=0.7, ang=-0.3, n=2, L=30)
        if v_land:
            particles(pn, 'dust', vp[0] + 60, 1375, t, c1 + 0.38, 1.0, seed=13, ground=1379)
        if v_age > 0.12 or not v_land and False:
            cl.dead_venator(pn, vp[0], vp[1], 1.6, 1, t)
        else:
            J = figure(pn, vp[0], vp[1], 1.6, 1, dict(cl.LIE), 'venator', 'pain', look=(0, -0.5), blink=0.0)
            cl.leg_wraps(pn, vp[0], vp[1], 1.6, J)
        return
    if t < 0.4: particles(pn, 'dust', 560, HOLE['y0'], t, 0.05, 1.1, seed=3, ground=HOLE['y1'])
    x, y, g, ph, f, e_, tl = tiger_path(t)
    eyes_in_hole(pn, t, 0.45, T['burst'] - 0.42)
    if 0.45 < t < T['burst'] - 0.42:
        particles(pn, 'dust', 560, HOLE['y0'], t, 0.5 + int((t - 0.5) / 0.35) * 0.35, 0.4, seed=int(t * 3), ground=HOLE['y1'])
    if t < c0:
        if t > land:   # anticipation: the tiger turns and sinks back on its haunches, then lunges on an arc
            ad = 0.14
            if t < land + ad:
                u = eio(P(t, land, ad)); x = 820 + 18 * u; y = 1330; g, ph, f, e_, tl = 'crouch', 0.0, -1, 'angry', 0.0
            else:
                u = ei2(P(t, land + ad, c0 - land - ad))
                x = lerp(838, 470, u); y = 1330 - 90 * math.sin(u * math.pi); g, ph, f, e_, tl = 'leap', 0.3 + 0.6 * u, -1, 'roar', 0.15 * math.sin(u * math.pi)
                speed_lines(pn, x + 220, y - 130, 1, 0, t, length=220, n=5, spread=120, seed=6)
        crouch_ = 0.0 if not (land < t < land + 0.14) else eio(P(t, land, 0.14))
        draw = lambda p2: tiger(p2, x, y, 1.45, f, gait=g, ph=ph, expr=e_, t=t, look=(-0.7 if f < 0 else 0.6, 0), body_tilt=tl, crouch=crouch_)
        if t < T['burst'] + 0.25: clipped(pn, HOLE['y1'] - 4, draw)
        else: draw(pn)
        ex = 'determined' if t < T['burst'] else ('fear' if t < land else 'terrified')
        lean = antic(t, land, c0 - land + 0.05, 0.25)
        venator(pn, 175 + 60 * max(0, lean), 1400, 1.75, 1, t, ang=0.18, expr=ex, look=(0.9, 0.2) if t < T['burst'] else (0.9, -0.3))
        if t >= T['burst']:
            particles(pn, 'dust', 560, HOLE['y1'], t, T['burst'], 1.6, seed=5, ground=HOLE['y1'] + 40)
            if t < T['burst'] + 0.4: speed_lines(pn, 700, 1150, 1, -0.6, t, length=260, n=5, spread=140, seed=2)
            impact(pn, 600, 1180, t, T['burst'], 1.2, seed=4)
    else:
        impact(pn, 430, 1120, t, c0, 1.3, seed=7)
        particles(pn, 'dust', 430, 1360, t, c0, 1.6, seed=8, ground=1364)
        cl.fight_cloud(pn, 470, 1120, t, c0, R=210, seed=3, burst=c1)
        pn.ell(430, 1380, 300, 26, fill=(20, 14, 10, 50))

def sc_hook(base, pn, t): hook(base, pn, t)

def sc_real(base, pn, t):
    hook(base, pn, t, after=True)
    if t < T['s1'] + 0.3: cl.fight_cloud(pn, 470, 1120, t, fight_times()[1], R=210, seed=3, burst=fight_times()[2])
    stamp(pn, 540, 860, 'REAL', t - T['real'], sz=130)
def cam_real(t, sc, ox, oy):
    z = 1.0 + 0.08 * eio(P(t, T['s1'], 1.2))
    return camfocus(z, 560, 1330, 560, 1300, ox, oy)

# ---------------- 2. under the Colosseum: down the shaft ----------------
SEC_TOP = 470
def section_base(base, pn, t, gap=(430, 650), shaft_x=540, door=1.0):
    bgp(base, 'section', 0.0)
    pn.rect(-400, SEC_TOP - 6, 1480, SEC_TOP + 40, fill=SAND)
    arena_floor(pn, SEC_TOP, -400, 1480, gap=gap, depth=40)
    lift_shaft(pn, shaft_x, SEC_TOP + 40, HFLOOR, w=gap[1] - gap[0])
    pn.rect(-400, HFLOOR, 1480, 2800, fill=(84, 66, 50))
    pn.line([(-400, HFLOOR), (1480, HFLOOR)], INK, 5)
    for xx in range(-20, 1100, 120): pn.line([(xx, HFLOOR + 4), (xx + 60, HFLOOR + 40)], (64, 50, 38), 3)
    if door: trapdoor(pn, gap[1], SEC_TOP, gap[1] - gap[0] - 6, op=door, f=-1)

def sc_down(base, pn, t):
    section_base(base, pn, t)
    pulley(pn, 540, SEC_TOP + 70, ang=t)
    top = lift_cage(pn, 540, HFLOOR - 4, 0.9, inside=lambda p: lion(p, -6, -6, 0.6, 1, gait='crouch', expr='angry', t=t))
    rope(pn, [(540, SEC_TOP + 92), top], 4.5)
    torch(pn, 200, 900, t); torch(pn, 880, 900, t + 1.1)
    if t > T['machine']:
        ring_ = eo3(P(t, T['machine'], 0.5))
        pn.circ(540, HFLOOR - 160, lerp(90, 210, ring_), outline=AMBER + (int(255 * (1 - ring_)),), width=7)
def cam_down(t, sc, ox, oy):
    u = eio(P(t, T['s2'] + 0.3, 1.6))
    z = lerp(1.7, 1.0, u); fy = lerp(SEC_TOP + 60, 860, u)
    return camfocus(z, 540, fy, 540, 860, ox, oy)

# ---------------- 3. an elevator ----------------
def modern_car(pn, x, yb, k, a=1.0):
    pn.push(x, yb, k)
    A = int(255 * a)
    pn.rect(-110, -150, 110, 0, fill=(176, 182, 190, A), outline=INK + (A,), width=4, r=4)
    pn.rect(-96, -136, -2, -6, fill=(150, 156, 166, A), outline=INK + (A,), width=2.6)
    pn.rect(2, -136, 96, -6, fill=(150, 156, 166, A), outline=INK + (A,), width=2.6)
    pn.line([(0, -150), (0, -260)], INK + (A,), 4)
    pn.rect(-30, -170, 30, -150, fill=(110, 114, 122, A), outline=INK + (A,), width=2.4)
    pn.circ(70, -160, 6, fill=(250, 200, 80, A))
    pn.pop()

def sc_elevator(base, pn, t):
    bgp(base, 'parch', 0.0)
    pn.rect(-400, 1180, 1480, 2800, fill=(214, 200, 168)); pn.line([(-400, 1180), (1480, 1180)], lerpc((214, 200, 168), INK, .45), 4)
    m = eio(P(t, T['elevator3'] + 0.15, 0.35))
    if m < 1: modern_car(pn, 540, 1180, 2.2, 1 - m)
    if m > 0:
        top = lift_cage(pn, 540, 1180, 2.2 * (0.96 + 0.04 * m), inside=lambda p: lion(p, -6, -6, 0.6, 1, gait='stand', t=t) if m > 0.6 else None)
        rope(pn, [(540, 600), top], 6)

# ---------------- 4. the hypogeum corridor ----------------
def sc_corridor(base, pn, t):
    bgp(base, 'hypogeum', 1.0)
    pn.rect(-400, 1300, 1480, 2800, fill=(70, 54, 40))
    pn.line([(-400, 1300), (1480, 1300)], INK, 5)
    torch(pn, 150, 760, t, 1.6); torch(pn, 930, 760, t + 0.7, 1.6)
    u = t - T['s4']
    sp_ = math.sin(u * 8)
    p = pose('walk', thF=18 * sp_, thB=-18 * sp_, shF=-max(0, -sp_) * 24, shB=-max(0, sp_) * 24, uaF=-14 * sp_, uaB=14 * sp_)
    figure(pn, 540, 1300 + 6 * abs(math.sin(u * 8)), 1.9, 1, p, 'rkeeper', 'awe', look=(math.sin(u * 1.4), -0.5), blink=blink_at(t))
    tag(pn, 540, 520, 'HYPOGEUM', 70, pop(t, T['hypogeum'] - 0.1), rot_=-3, sub='GREEK FOR "UNDERGROUND"')
def cam_corridor(t, sc, ox, oy):
    z = 1.0 + 0.12 * eio(P(t, T['s4'], 2.2))
    return camfocus(z, 540, 900, 540, 900, ox, oy)

# ---------------- 5. a maze of tunnels and cells (simplified plan) ----------------
def sc_plan(base, pn, t):
    bgp(base, 'parch', 0.0)
    cx, cy, rx, ry = 540, 860, 470, 300
    def ell(rx_, ry_, p, col, wd):
        n = 90; m = max(2, int(n * p))
        pts = [(cx + rx_ * math.cos(2 * math.pi * i / n - math.pi / 2), cy + ry_ * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(m + 1)]
        pn.line(pts, INK, wd + 4); pn.line(pts, col, wd)
    pn.ell(cx, cy, rx, ry, fill=(226, 206, 160))
    ell(rx, ry, 1.0, (196, 170, 120), 10)
    p1 = P(t, T['maze'] - 0.1, 0.8); p2 = P(t, T['tunnels'], 0.7); p3 = P(t, T['cells'] - 0.1, 0.6)
    # central corridor and parallel corridors
    for i, dy in enumerate((0, -70, 70, -140, 140)):
        e = eo3(clamp(p1 * 1.6 - i * 0.15))
        half = (rx - 60 - abs(dy) * 0.6)
        if e > 0: pn.line([(cx - half * e, cy + dy), (cx + half * e, cy + dy)], (70, 52, 38), 16 if dy == 0 else 10)
    for k_, (rr, a) in enumerate(((0.78, 0.0), (0.62, 0.3))):
        ell(rx * rr, ry * rr, eo3(clamp(p2 * 1.3 - k_ * 0.2)), (70, 52, 38), 9)
    rnd = random.Random(4)
    for i in range(28):
        if p3 * 28 < i: break
        a = rnd.uniform(0, 2 * math.pi); r_ = rnd.uniform(0.66, 0.9)
        x = cx + rx * r_ * math.cos(a); y = cy + ry * r_ * math.sin(a)
        s = pop(t, T['cells'] - 0.1 + i * 0.02)
        pn.push(x, y, s); pn.rect(-14, -10, 14, 10, fill=(110, 80, 56), outline=INK, width=2.4); pn.pop()
    tag(pn, 830, 1220, 'SIMPLIFIED', 40, pop(t, T['tunnels']), rot_=4)

# ---------------- 6. a lion waited in a wooden cage ----------------
def sc_cage(base, pn, t):
    bgp(base, 'hypogeum', 0.5)
    pn.rect(-400, 1270, 1480, 2800, fill=(70, 54, 40)); pn.line([(-400, 1270), (1480, 1270)], INK, 5)
    torch(pn, 120, 700, t, 1.5)
    pace = math.sin((t - T['s6']) * 1.6) * 30
    look = (0.8, 0) if t < T['cage6'] else (0.2, 0.4)
    ex = 'angry' if t > T['wooden'] else 'neutral'
    def inside(p):
        lion(p, pace, -6, 0.68, 1 if math.cos((t - T['s6']) * 1.6) > 0 else -1, gait='stand', t=t, look=look, expr=ex)
    top = lift_cage(pn, 560, 1270, 2.3, inside=inside)
    rope(pn, [(560, 300), top], 7)
def cam_cage(t, sc, ox, oy):
    z = 1.0 + 0.1 * eio(P(t, T['s6'], 2.0))
    return camfocus(z, 560, 1000, 560, 980, ox, oy)

# ---------------- 7. nothing bigger would fit ----------------
def elephant(pn, x, y, k, f=-1):
    """Elephant silhouette for the size check: grey body, ear, trunk, tusk, legs (diagram detail)."""
    s = f; G = (150, 150, 152); Gd = shade(G, .2)
    pn.push(x, y, k)
    body = cl._cr([(s * 100, -150), (s * 40, -200), (-s * 70, -196), (-s * 140, -150), (-s * 140, -80), (-s * 90, -60), (s * 70, -60), (s * 120, -90)], 6)
    for lx in (-110, -60, 40, 85):
        pn.rect(s * lx - 20, -90, s * lx + 20, 0, fill=Gd if lx in (-60, 85) else G, outline=INK, width=3)
        for j in range(3): pn.line([(s * lx - 12 + j * 10, -4), (s * lx - 12 + j * 10, -12)], INK, 2, caps=False)
    pn.poly(body, fill=G, outline=INK, width=3.4)
    pn.poly([(s * 110, -180), (s * 160, -170), (s * 175, -120), (s * 182, -60), (s * 200, -30), (s * 188, -26), (s * 162, -60), (s * 150, -118)], fill=G, outline=INK, width=3)
    pn.ell(s * 92, -150, 42, 52, fill=Gd, outline=INK, width=3)
    pn.poly([(s * 156, -108), (s * 196, -92), (s * 194, -84), (s * 156, -96)], fill=(244, 238, 222), outline=INK, width=2)
    pn.ell(s * 138, -158, 6, 6, fill=WHITE, outline=INK, width=2); pn.circ(s * 140, -158, 3, fill=INK)
    for i in range(4): pn.line([(-s * 40 + s * i * 30, -190), (-s * 50 + s * i * 30, -150)], Gd, 2, caps=False)
    pn.line([(-s * 140, -140), (-s * 162, -100)], INK, 6); pn.line([(-s * 140, -140), (-s * 162, -100)], G, 3)
    pn.pop()

def sc_fit(base, pn, t):
    bgp(base, 'parch', 0.0)
    pn.rect(-400, 1180, 1480, 2800, fill=(214, 200, 168)); pn.line([(-400, 1180), (1480, 1180)], lerpc((214, 200, 168), INK, .45), 4)
    top = lift_cage(pn, 380, 1180, 1.7, inside=lambda p: lion(p, -6, -6, 0.6, 1, gait='stand', t=t, look=(1, 0)))
    check(pn, 380, 760, P(t, T['nothing'] + 0.1, 0.3))
    # the elephant slides in, bumps the cage and bounces back
    tin = T['bigger'] - 0.2
    if t > tin:
        u = P(t, tin, 0.45); x = lerp(1300, 820, eo3(u))
        if t > tin + 0.45: x = 820 + 26 * math.sin((t - tin - 0.45) * 18) * math.exp(-(t - tin - 0.45) * 6)
        elephant(pn, x, 1180, 1.25, -1)
        if t > tin + 0.45: impact(pn, 600, 1000, t, tin + 0.45, 0.6, seed=2, lines=False)
    xmark(pn, 820, 760, P(t, T['fit'], 0.3))

# ---------------- 8 to 11. the capstan, two stories, the crew ----------------
CP_X, CP_K, LVL = 380, 1.3, 300
CREW = [('operae', 'operae2', 'operae3', 'operae4'), ('operae5', 'operae6', 'operae7', 'operae8')]
def capstan_ang(t):
    return 0.0 if t < T['s10'] else (t - T['s10']) * 1.25

def crew_draw(pn, t, ang, level, side, k=CP_K, alpha_back=True):
    """Workers on one level. side -1 draws those behind the post, +1 those in front."""
    yb = HFLOOR - level * LVL * k
    for j in range(4):
        a = ang + j * math.pi / 2
        depth = math.sin(a)
        if (depth < 0) != (side < 0): continue
        bx = CP_X + math.cos(a) * 210 * k
        f = 1 if -math.sin(a) * 0 + math.cos(a + math.pi / 2) > 0 else -1     # travel direction across the screen
        kk = k * (0.8 + 0.2 * (depth + 1) / 2)
        x = bx - f * 46 * kk
        ex = ('exhausted' if j == 1 else 'determined') if t > T['pushed'] else 'neutral'
        pusher(pn, x, yb, kk / 1.0, f, (t * 0.9 + j * 0.25) % 1.0, CREW[level][j], ex, t, bar_h=-150 * k / kk - 4)

def sc_capstan(base, pn, t):
    section_base(base, pn, t, gap=(1300, 1500), shaft_x=1400, door=0)
    ang = capstan_ang(t)
    b1, b2, b3 = pop(t, T['beside'] - 0.05), pop(t, T['stood']), pop(t, T['capstan8'] - 0.1)
    crew_on = t > T['eight'] - 0.15
    if b1 > 0:
        pn.push(CP_X, HFLOOR, b1); pn.push(-CP_X, -HFLOOR, 1.0)
        def front(level, side):
            if crew_on: crew_draw(pn, t, ang, level, side)
        capstan(pn, CP_X, HFLOOR, CP_K, ang=ang, levels=2, lvl_h=LVL, rope_turns=0.3 if b3 > 0 else 0.0,
                bar_len=210 * clamp(b2), show_front=front if crew_on else None)
        pn.pop(); pn.pop()
    tag(pn, 790, 700, 'CAPSTAN', 56, pop(t, T['capstan8'] - 0.05), rot_=-3, sub='VERTICAL WINCH', string_to=(CP_X + 30, HFLOOR - 480))
    # two stories: the Keeper points from the right, a dimension climbs the post
    if T['upright'] - 0.3 < t < T['eight'] - 0.2:
        a_ = P(t, T['upright'] - 0.3, 0.3)
        figure(pn, 900, HFLOOR, 1.5, -1, 'point', 'rkeeper', 'thinking' if t < T['two9'] else 'happy', look=(-0.9, -0.4), blink=blink_at(t))
    vdim(pn, CP_X + 300, HFLOOR, HFLOOR - 2 * LVL * CP_K, '2 LEVELS', P(t, T['two9'] - 0.1, 0.7) * (1 if t < T['eight'] - 0.2 else 0))
    # four on each level: numbered markers over the front workers
    for lv, t0 in ((0, T['four']), (1, T['level'] - 0.1)):
        for j in range(4):
            s = pop(t, t0 + j * 0.12)
            if s <= 0: continue
            yy = HFLOOR - lv * LVL * CP_K - 330
            xx = CP_X - 210 + j * 140
            pn.push(xx, yy, s); pn.circ(0, 0, 26, fill=AMBER, outline=INK, width=4); pn.text(0, 2, str(j + 1), 30, INK, 'Black', 'mm', True); pn.pop()
def cam_capstan(t, sc, ox, oy):
    if t < T['s9']: return camfocus(1.08, CP_X + 140, 1050, 540, 1000, ox, oy)
    u = eio(P(t, T['s9'], 1.4))
    z = lerp(1.08, 1.0, u)
    return camfocus(z, lerp(CP_X + 140, 540, u), lerp(1050, 960, u), 540, lerp(1000, 960, u), ox, oy)

# ---------------- 12, 13. ropes wound round the shaft, the cage climbs ----------------
SH_X = 830
def cage_y(t):
    u = eio(P(t, T['climbed'] - 0.1, T['feet'] + 0.5 - T['climbed']))
    return lerp(HFLOOR - 4, SEC_TOP + 40 + 150 * 0.95 + 75, u)

def sc_lift(base, pn, t):
    section_base(base, pn, t, gap=(SH_X - 110, SH_X + 110), shaft_x=SH_X, door=0)
    ang = (t - T['s10']) * 1.25
    k = 0.95
    capstan(pn, 300, HFLOOR, k, ang=ang, levels=2, lvl_h=LVL, rope_turns=clamp(P(t, T['climbed'] - 0.1, 1.6)), bar_len=210,
            show_front=lambda lv, sd: crew_draw_small(pn, t, ang, lv, sd, k))
    cy = cage_y(t)
    pulley(pn, SH_X, SEC_TOP + 70, ang=-ang * 2)
    top = lift_cage(pn, SH_X, cy, 0.95, inside=lambda p: lion(p, -6, -6, 0.6, 1, gait='crouch', expr='angry', t=t))
    rope(pn, [(SH_X, SEC_TOP + 92), top], 4.5)
    drum = (300 + 30 * k, HFLOOR - LVL * k - 70 * k)
    rp = P(t, T['ropes'] - 0.1, 0.5)
    rope(pn, [drum, (lerp(drum[0], SH_X - 22, rp), lerp(drum[1], SEC_TOP + 70, rp))], 4.5)
    if rp >= 1: rope(pn, [(SH_X - 22, SEC_TOP + 70), (SH_X, SEC_TOP + 48)], 4.5)
    vdim(pn, SH_X + 165, HFLOOR, SEC_TOP + 130, '7.6 m', P(t, T['twenty'], 0.8))
    if T['climbed'] - 0.1 < t < T['feet'] + 0.6:
        speed_lines(pn, SH_X, cy + 40, 0, 1, t, length=120, n=4, spread=120, seed=8, alpha=120)

def crew_draw_small(pn, t, ang, level, side, k):
    yb = HFLOOR - level * LVL * k
    for j in range(4):
        a = ang + j * math.pi / 2
        depth = math.sin(a)
        if (depth < 0) != (side < 0): continue
        bx = 300 + math.cos(a) * 210 * k
        f = 1 if math.cos(a + math.pi / 2) > 0 else -1
        kk = k * (0.86 + 0.14 * (depth + 1) / 2)
        pusher(pn, bx - f * 46 * kk, yb, kk, f, (t * 0.9 + j * 0.25) % 1.0, CREW[level][j], 'determined', t, bar_h=-150 * k / kk - 4)

def cam_lift(t, sc, ox, oy):
    u = eio(P(t, T['climbed'] - 0.1, T['feet'] + 0.5 - T['climbed']))
    fy = lerp(1050, 760, u)
    return camfocus(1.0, 540, fy, 540, lerp(900, 800, u), ox, oy)

# ---------------- 14. at the top, the trap door swings down into a ramp ----------------
RFLOOR = 760
def door_op(t): return P(t, T['swung'] - 0.05, 0.42)
def sc_ramp(base, pn, t):
    bgp(base, 'section', 0.0)
    sk = env.get('arena').crop((0, 300, W, 300 + RFLOOR))
    base.paste(sk, (0, 0))
    gap = (300, 790)
    pn.rect(-400, RFLOOR + 40, 1480, 2800, fill=(64, 48, 38))
    lift_shaft(pn, (gap[0] + gap[1]) / 2, RFLOOR + 40, 2000, w=gap[1] - gap[0])
    op = door_op(t)
    cage_x, cage_b, ck = 650, RFLOOR + 330, 1.5
    if op > 0:   # daylight falls in through the opening onto the cage
        pn.poly([(gap[0] + 10, RFLOOR + 40), (gap[1] - 10, RFLOOR + 40), (gap[1] - 10, cage_b), (gap[0] + 60, cage_b)], fill=(255, 236, 190, int(60 * op)))
    gate = P(t, T['ramp'] + 0.1, 0.4)
    def inside(p):
        lion(p, -4, -6, 0.62, -1, gait='crouch', expr='angry' if t < T['ramp'] else 'roar', t=t, look=(-0.8, -0.6))
    lift_cage(pn, cage_x, cage_b, ck, gate=gate, inside=inside)
    pn.rect(-400, RFLOOR - 8, 1480, RFLOOR + 40, fill=SAND)
    arena_floor(pn, RFLOOR, -400, 1480, gap=gap, depth=40)
    end = trapdoor(pn, gap[0], RFLOOR + 20, 330, op=op, f=1)
    if op > 0.6: particles(pn, 'dust', end[0], end[1], t, T['swung'] + 0.3, 0.8, seed=6)
    tag(pn, 760, 1260, 'RAMP SLOTS', 40, pop(t, T['ramp'] + 0.2), rot_=4, sub='CUT IN THE SHAFT WALLS (BESTE)')

def cam_ramp(t, sc, ox, oy):
    return camfocus(1.25, 540, 960, 540, 900, ox, oy)

# ---------------- 15. the lion runs up into the light ----------------
H15 = dict(cx=330, y0=1230, y1=1310, w0=250, w1=300)
def sc_run(base, pn, t):
    bgp(base, 'arena', 0.35)
    sand_grain(pn, 1080, 7)
    hole_and_door(pn, 1.0, H_=H15)
    t0 = T['ran'] - 0.1
    if t < t0:
        clipped(pn, H15['y1'], lambda p2: lion(p2, 330, 1420, 1.3, 1, gait='crouch', expr='angry', t=t))
    else:
        u = P(t, t0, 0.45)
        if u < 1:
            x = lerp(330, 470, u); y = lerp(1420, 1340, eo3(u)) - 120 * math.sin(u * math.pi); g, ph = 'leap', 0.3 + 0.6 * u
            clipped(pn, H15['y1'] + (0 if u < 0.5 else 300), lambda p2: lion(p2, x, y, 1.3, 1, gait=g, ph=ph, expr='roar', t=t))
        else:
            x = 470 + (t - t0 - 0.45) * 460; y = 1340; g, ph = 'run', ((t - t0) * 2.4) % 1.0
            lion(pn, x, y, 1.3, 1, gait=g, ph=ph, expr='roar' if T['straight'] < t < T['light15'] + 0.4 else 'angry', t=t)
            particles(pn, 'dust', x - 160, 1340, t, t0 + 0.45 + int((t - t0) * 3) / 3, 1.0, seed=int(t * 3), ground=1344)
            speed_lines(pn, x - 280, 1200, -1, 0, t, length=240, n=5, spread=130, seed=4)
    a = P(t, T['light15'] - 0.2, 0.5)
    if a > 0: base.alpha_composite(Image.new('RGBA', (W, H), (255, 244, 214, int(40 * a))))
def cam_run(t, sc, ox, oy):
    t0 = T['ran'] - 0.1
    x = 470 if t < t0 + 0.45 else min(1000, 470 + (t - t0 - 0.45) * 460)
    return camfocus(1.0, lerp(540, x, 0.45), 1100, 540, 1100, ox, oy)

# ---------------- 16. fifty thousand people ----------------
def sc_crowd(base, pn, t):
    bgp(base, 'arena', 0.2)
    pn.rect(-400, 280, 1480, 1060, fill=(196, 180, 150))
    def wave(t_, c, r):
        t0 = T['fifty'] + c * 0.035 + r * 0.02
        u = t_ - t0
        return 0.0 if u < 0 else (eoback(clamp(u / 0.25)) if u < 0.8 else max(0.0, 1 - (u - 0.8) / 0.4) * 0.6 + 0.4 * (0.5 + 0.5 * math.sin(u * 9 + c)))
    for r in range(9):
        y = 330 + r * 82
        pn.rect(-400, y + 2, 1480, y + 14, fill=(170, 152, 120))
        crowd(pn, -10 + (r % 2) * 15, y, 38, 1, dx=30, dy=0, t=t, wave=lambda tt, c, rr, r_=r: wave(tt, c, r_), seed=r + 1)
    pn.rect(-400, 1060, 1480, 1110, fill=(214, 200, 170), outline=INK, width=4)
    pn.rect(-400, 1110, 1480, 2800, fill=SAND); sand_grain(pn, 1110, 12)
    lion(pn, 540, FLOOR, 0.8, 1 if (t - T['s16']) % 3 < 1.5 else -1, gait='stand', expr='roar' if (t * 1.3) % 2 < 0.8 else 'angry', t=t, look=(0.3, -0.6))
    tag(pn, 820, 1290, 'ESTIMATES VARY', 34, pop(t, T['people'] + 0.2), rot_=4)
def cam_crowd(t, sc, ox, oy):
    z = 1.0 + 0.06 * eio(P(t, T['s16'], 3.0))
    return camfocus(z, 540, 800, 540, 800, ox, oy)

# ---------------- 17. dozens of lifts under one floor ----------------
DOORS = None
def door_spots():
    global DOORS
    if DOORS is None:
        DOORS = []
        cx, cy, rx, ry = 540, 860, 470, 300
        for ring_, n in ((0.86, 18), (0.66, 10)):
            for i in range(n):
                a = 2 * math.pi * (i + 0.5 * (ring_ < 0.8)) / n
                DOORS.append((cx + rx * ring_ * math.cos(a), cy + ry * ring_ * math.sin(a)))
    return DOORS
def sc_dozens(base, pn, t):
    bgp(base, 'parch', 0.0)
    cx, cy, rx, ry = 540, 860, 470, 300
    pn.ell(cx, cy, rx + 60, ry + 50, fill=(196, 178, 140), outline=INK, width=6)
    pn.ell(cx, cy, rx, ry, fill=SAND, outline=INK, width=6)
    hid = P(t, T['hidden'], 0.6)
    for i, (x, y) in enumerate(door_spots()):
        s = pop(t, T['dozens'] - 0.1 + i * 0.035)
        if s <= 0: continue
        pn.push(x, y, s)
        a = int(255 * (1 - 0.7 * hid))
        pn.rect(-17, -12, 17, 12, fill=(110, 76, 50, a), outline=INK + (a,), width=3)
        pn.line([(-17, 0), (17, 0)], (80, 56, 38, a), 2, caps=False)
        pn.pop()
    if hid > 0:
        rnd = random.Random(2)
        for _ in range(160):
            x = cx + rnd.uniform(-1, 1) * rx * 0.95; y = cy + rnd.uniform(-1, 1) * ry * 0.95
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.9:
                pn.circ(x, y, 2.4, fill=SAND_D + (int(220 * hid),))
    tag(pn, 540, 1230, 'ESTIMATES: 24 TO 40+', 44, pop(t, T['lifts']), rot_=-3, sub='ANIMAL LIFTS, DEPENDING ON THE SOURCE')

# ---------------- 18. a hunter never knew where the next lion would rise ----------------
def sc_hunter(base, pn, t):
    bgp(base, 'arena', 0.5)
    sand_grain(pn, 1080, 9)
    for cx_, y0 in ((140, 1150), (930, 1150)):
        hole_and_door(pn, 0.0, cx=cx_, H_=dict(cx=cx_, y0=y0, y1=y0 + 50, w0=170, w1=200))
    nx = 900
    Hn = dict(cx=nx, y0=1380, y1=1460, w0=250, w1=300)
    op = 0.22 * eo3(P(t, T['next18'], 0.5))
    hole_and_door(pn, op, H_=Hn)
    if t > T['rise'] - 0.25:
        for sd in (-1, 1): pn.ell(nx + sd * 22, 1400, 9, 5, fill=(250, 190, 60))
    dart = math.sin((t - T['where']) * 7) if t > T['where'] else 0.6
    ex = 'neutral' if t < T['never'] else ('worried' if t < T['next18'] else 'fear')
    venator(pn, 380, 1380, 2.3, 1, t, ang=0.1, expr=ex, look=(dart, 0.2))
def cam_hunter(t, sc, ox, oy):
    return camfocus(1.0 + 0.05 * eio(P(t, T['s18'], 3)), 540, 900, 540, 900, ox, oy)

# ---------------- 19. when that floor opens: a Roman elevator (loops to the hook) ----------------
def sc_end(base, pn, t):
    bgp(base, 'arena', 0.35)
    sand_grain(pn, 1080)
    op = clamp(eoback(P(t, T['opens'] - 0.1, 0.34), 1.3))
    hole_and_door(pn, op)
    eyes_in_hole(pn, t, T['opens'] + 0.2, T['watching'] - 0.3)
    rise = eio(P(t, T['watching'] - 0.3, 0.9))
    y = lerp(1760, 1430, rise)
    clipped(pn, HOLE['y1'] - 4, lambda p2: tiger(p2, 560, y, 1.45, 1, gait='leap', ph=0.2, body_tilt=-1.0,
                                                  expr='roar' if rise > 0.7 else 'angry', t=t))
    venator(pn, 175, 1400, 1.75, 1, t, ang=0.18, expr='fear' if rise > 0.6 else ('worried' if t > T['opens'] else 'determined'), look=(0.9, 0.3))
    if op > 0 and t < T['opens'] + 0.5:
        particles(pn, 'dust', 560, HOLE['y0'], t, T['opens'] + 0.15, 1.0, seed=3, ground=HOLE['y1'])

# ---------------- SHOT SIZE PLAN (camera framing; a reframe inside a scene is a cut) ----------------
def cam_hook(t, sc, ox, oy):        # MEDIUM WIDE on the trap door, slow push to MEDIUM as the tiger rises
    z = 1.0 + 0.1 * eio(P(t, 0.3, T['burst']))
    return camfocus(z, 520, 1300, 520, 1300, ox, oy)
def cam_elevator(t, sc, ox, oy):    # INSERT: tight on the car, the morph fills the frame
    return camfocus(1.35, 540, 1000, 540, 960, ox, oy)
def cam_plan(t, sc, ox, oy):        # GRAPHIC: top down plan, slow push
    return camfocus(1.0 + 0.08 * eio(P(t, T['s5'], 2.2)), 540, 860, 540, 900, ox, oy)
def cam_cage(t, sc, ox, oy):        # CLOSE UP on the lion's face through the bars, eased back to MEDIUM on "cage"
    u = eio(P(t, T['cage6'] - 0.2, 0.5))
    return camfocus(lerp(1.6, 1.05, u), lerp(580, 560, u), lerp(1110, 1000, u), 540, lerp(980, 980, u), ox, oy)
def cam_fit(t, sc, ox, oy):         # MEDIUM diagram
    return camfocus(1.0, 540, 960, 540, 960, ox, oy)
def cam_capstan(t, sc, ox, oy):
    if t < T['s9']:                 # WIDE: the machine assembles
        return camfocus(0.98, CP_X + 160, 1000, 540, 980, ox, oy)
    if t < T['s10']:                # MEDIUM: the Keeper and the two story post
        return camfocus(1.12, 650, 1030, 540, 980, ox, oy)
    if t < T['s11']:                # MEDIUM CLOSE: faces of the lower crew straining on "Eight men pushed"
        return camfocus(1.75, CP_X, HFLOOR - 300, 540, 1000, ox, oy)
    u = eio(P(t, T['s11'], 0.5))    # WIDE again for the count, four and four
    return camfocus(lerp(1.15, 0.98, u), CP_X + 160, 1020, 540, 980, ox, oy)
def cam_lift(t, sc, ox, oy):
    if t < T['s13']:                # INSERT: rope winding onto the drum
        return camfocus(2.1, 300, 1040, 540, 960, ox, oy)
    u = eio(P(t, T['climbed'] - 0.1, T['feet'] + 0.5 - T['climbed']))   # MEDIUM: tracking the cage up
    return camfocus(1.15, SH_X - 60, lerp(1080, 760, u), 540, lerp(980, 860, u), ox, oy)
def cam_ramp(t, sc, ox, oy):        # MEDIUM CLOSE on the cage, pulling to MEDIUM as the ramp lands
    u = eio(P(t, T['swung'] - 0.2, 0.7))
    return camfocus(lerp(1.7, 1.25, u), lerp(640, 540, u), lerp(1000, 960, u), 540, 920, ox, oy)
def cam_crowd(t, sc, ox, oy):       # CLOSE on cheering faces, pulling out to WIDE on "people"
    z = 1.0 + 0.08 * eio(P(t, T['s16'], 3.0))     # WIDE: the whole cavea
    return camfocus(z, 540, 800, 540, 800, ox, oy)
def cam_dozens(t, sc, ox, oy):      # GRAPHIC: overhead plan, punch in on "hidden"
    return camfocus(1.0 + 0.06 * eio(P(t, T['s17'], 2.8)) + 0.07 * eio(P(t, T['hidden'], 0.4)), 540, 860, 540, 900, ox, oy)
def cam_hunter(t, sc, ox, oy):      # CLOSE UP on the hunter, to EXTREME CLOSE on his eyes at "where"
    u = eio(P(t, T['where'] - 0.15, 0.35))
    return camfocus(lerp(1.0, 1.9, u), lerp(540, 400, u), lerp(900, 1380 - 2.3 * 236, u), 540, lerp(900, 820, u), ox, oy)
def cam_end(t, sc, ox, oy):         # MEDIUM WIDE, the same framing as the opening for the loop
    return camfocus(1.0, 520, 1300, 520, 1300, ox, oy)

SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['s1'], sc_real, cam_real, None),
    (T['s2'], sc_down, cam_down, 'slide'),
    (T['s3'], sc_elevator, cam_elevator, None),
    (T['s4'], sc_corridor, cam_corridor, 'dissolve'),
    (T['s5'], sc_plan, cam_plan, 'dissolve'),
    (T['s6'], sc_cage, cam_cage, 'dissolve'),
    (T['s7'], sc_fit, cam_fit, 'dissolve'),
    (T['s8'], sc_capstan, cam_capstan, 'slide'),
    (T['s12'], sc_lift, cam_lift, None),
    (T['s14'], sc_ramp, cam_ramp, 'slide'),
    (T['s15'], sc_run, cam_run, 'dissolve'),
    (T['s16'], sc_crowd, cam_crowd, None),
    (T['s17'], sc_dozens, cam_dozens, 'slide'),
    (T['s18'], sc_hunter, cam_hunter, None),
    (T['s19'], sc_end, cam_end, None),
]

"""E016 English longbow at Agincourt: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
from props import tag, stamp, callout, arrow as arrow_line
import lb
from lb import longbow, arrow, archer_hands, stuck_arrow, butt, scroll, bunting, skeleton, banner_fr, furrows, rain, mud_band
from lb import log_end, mallet, wedge, trestle, pulley_frame, counter, limb_segment, double_arrow, SAP, HEART, ARROW_L, BOW_L
import env
import make_map as MM
import fx
from fx import smear, speed_lines, focus_lines, impact, particles
from detail import rope as rope_line, shade, light

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
    pull0=w(0, 0), bow0=w(0, 2), force=w(0, 6), of0=w(0, 7), lifting=w(0, 8), grown=w(0, 10), man=w(0, 11),
    wt=S(1), around1=w(1, 1), n150=w(1, 2), pounds1=w(1, 3),
    lbs=S(2), english2=w(2, 3), longbow=w(2, 4),
    about3=w(3, 0), six=w(3, 1), feet=w(3, 5), yew=w(3, 7),
    bowyer_s=S(4), cut=w(4, 2), stave=w(4, 4), so4=w(4, 5), pale=w(4, 6), sapwood4=w(4, 7), target=w(4, 10),
    dark=w(5, 1), heartwood5=w(5, 2), archer5=w(5, 5),
    bend_s=S(6), stretching=w(6, 2), heart7=w(7, 0), crushing=w(7, 2),
    spr_s=S(8), wood8=w(8, 4), spring=w(8, 8),
    train_s=S(9), draw9=w(9, 2), weight=w(9, 4), years=w(9, 6), training=w(9, 8),
    law_s=S(10), law=w(10, 2), ordered=w(10, 3), men10=w(10, 4), practise=w(10, 6), archery=w(10, 7), holidays=w(10, 9),
    bones_s=S(11), later=w(11, 2), show=w(11, 5), heavier=w(12, 1), bones=w(12, 2), drawing=w(12, 5), arm=w(12, 6),
    map_s=S(13), october=w(13, 1), d25=w(13, 2), y1415=w(13, 3), at13=w(13, 4), agincourt=w(13, 5),
    ratio_s=S(14), four=w(14, 1), five=w(14, 3), henry=w(14, 5), men14=w(14, 8), archers14=w(14, 10),
    fr_s=S(15), french=w(15, 1), knights=w(15, 2), foot=w(15, 5),
    rain_s=S(16), ploughed=w(16, 2), field=w(16, 3), soaked=w(16, 4), night=w(16, 7), rain=w(16, 9),
    mud_s=S(17), mud=w(17, 1), slowed=w(17, 2), down=w(17, 4),
    vol_s=S(18), arrows18=w(18, 2), kept=w(18, 3), coming=w(18, 4),
    fin_s=S(19), those=w(19, 3), arrows19=w(19, 4), began=w(19, 5), pull19=w(19, 8), n150b=w(19, 11), pounds19=w(19, 12),
    end=VO_END,
)
T['release'] = T['spring'] - 0.02
T['thunk'] = T['release'] + 0.3
T['strike'] = T['cut'] - 0.02
VOLLEYS = [T['vol_s'] - 0.05, T['arrows18'] - 0.02, T['kept'], T['coming'] - 0.04]
FLIGHT = 0.62
CAM.drift = 0.5
CAM.punch = [(T['force'], 0.05), (T['n150'], 0.07), (T['release'], 0.06), (T['agincourt'], 0.06), (VOLLEYS[3] + FLIGHT, 0.07), (T['n150b'], 0.05)]
CAM.shake = [(T['strike'], 8, 0.3), (T['thunk'], 12, 0.35), (VOLLEYS[0] + FLIGHT, 10, 0.4), (VOLLEYS[3] + FLIGHT, 14, 0.45)]
FLASH = [(VOLLEYS[0] + FLIGHT, 0.12, (255, 240, 214), 100)]

GROUND = 1300          # standard ground line for full figure scenes
FLOOR_C = (206, 190, 158)

def bgp(base, name, par=0.5):
    base.paste(bg_cam(env.get(name), par))

def floor(pn, y, col=FLOOR_C, line=True):
    pn.rect(-400, y, 1480, 2800, fill=col)
    if line: pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def grass_ground(pn, y, t=0.0, col=lb.GRASS):
    pn.rect(-400, y, 1480, 2800, fill=col)
    pn.line([(-400, y), (1480, y)], lerpc(col, INK, .4), 4, caps=False)
    rnd = random.Random(8)
    for i in range(70):
        x = rnd.uniform(-60, 1140); yy = y + 10 + rnd.uniform(0, 700)
        sw = math.sin(t * 2 + i) * 3
        pn.line([(x, yy), (x + sw - 4, yy - 12 - (yy - y) / 50)], lerpc(col, INK, .25), 3)
        pn.line([(x + 6, yy), (x + 8 + sw, yy - 10 - (yy - y) / 60)], lb.GRASS_L, 3)
    for i in range(8):
        x = rnd.uniform(-40, 1120); yy = y + 30 + rnd.uniform(0, 500)
        pn.ell(x, yy, 14, 7, fill=(150, 146, 136), outline=INK, width=2)

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def walk_pose(t, rate=9.0, amp=22, base='walk', **over):
    s = math.sin(t * rate)
    p = pose(base, thF=amp * s, thB=-amp * s, shF=-max(0, -s) * 30, shB=-max(0, s) * 30,
             uaF=-18 * s, faF=-10 * s + 6, uaB=18 * s, faB=10 * s + 6)
    p.update(over); return p

# ---------------- the archer (held object: hands on the grip and the string by IK) ----------------
def archer(pn, x, y, k, f, draw, t, out=KEEPER, expr='determined', look=(0.9, 0.0), arrow_on=True, rel=None, tremble=0.0,
           blink=None, alpha_arrow=1.0, p=None, aim=0.0):
    """Front-on archer with correct form: bow arm straight and level, arrow level under the chin, string hand drawn to
    the jaw, draw elbow raised back on the arrow line. rel: seconds since release (follow through, string vibrates).
    Returns world positions: grip, string hand, nock and arrow angle."""
    p = p or pose('idle', torso=-2 * draw, head=1 * draw)
    J0 = joints(p, f, 1.0)
    fol = 0.0 if rel is None else eo3(clamp(rel / 0.12))
    hands = archer_hands(f, draw if rel is None else 1.0, J0['neck'], fol, aim)
    if tremble > 0:
        dxy = (tremble * 1.4 * math.sin(t * 47), tremble * 1.0 * math.cos(t * 41))
        hands['B'] = (hands['B'][0] + dxy[0], hands['B'][1] + dxy[1])
        hands['elB'] = (hands['elB'][0] + dxy[0] * 1.5, hands['elB'][1] + dxy[1])
        hands['F'] = (hands['F'][0], hands['F'][1] + tremble * 0.8 * math.sin(t * 37 + 1))
    info = {}
    def held(pn_, J):
        g = J['haF']; s = J['haB']
        if rel is None:
            bend = lb.string_bend(f, g, s)
            ang = math.atan2(g[1] - s[1], g[0] - s[0])
            longbow(pn_, g[0], g[1], f, bend, string_to=s, tilt=ang if f > 0 else ang + math.pi)
            if arrow_on and alpha_arrow > 0:
                arrow(pn_, s, ang)
            info.update(nock=s, ang=ang)
        else:
            vib = max(0.0, 1 - rel / 0.45)
            longbow(pn_, g[0], g[1], f, 0.0, vib=vib * 0.9 + 1e-3 if vib > 0 else 0.0, tilt=-f * aim)
            info.update(nock=s, ang=0.0)
        info['grip'] = g
    J = figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink_at(t, x * 0.01) if blink is None else blink, hands=hands, held=held)
    W_ = lambda pt: (x + pt[0] * k, y + pt[1] * k)
    return dict(grip=W_(info['grip']), nock=W_(info['nock']), ang=info['ang'], J=J,
                tip=W_((info['nock'][0] + math.cos(info['ang']) * (ARROW_L + 6), info['nock'][1] + math.sin(info['ang']) * (ARROW_L + 6))))

def archer_geom(x, y, k, f, draw, p=None):
    """Arrow tip and nock in world space for an archer at this draw, without drawing (pure, for flights)."""
    p = p or pose('idle', torso=-2 * draw, head=1 * draw)
    J0 = joints(p, f, 1.0)
    J = joints(p, f, 1.0, archer_hands(f, draw, J0['neck']))
    g, s_ = J['haF'], J['haB']
    ang = math.atan2(g[1] - s_[1], g[0] - s_[0])
    tip = (s_[0] + math.cos(ang) * (ARROW_L + 6), s_[1] + math.sin(ang) * (ARROW_L + 6))
    return (x + tip[0] * k, y + tip[1] * k), (x + s_[0] * k, y + s_[1] * k), ang

def draw_curve(t, t0, t1):
    return eio(P(t, t0, max(0.05, t1 - t0)))

# ---------------- 1. hook: pulling the bow ----------------
HK = dict(x=400, y=GROUND + 40, k=2.0)
def hook_frame(base, pn, t, t_draw, t_full, expr_at=None, t_pain=None):
    bgp(base, 'green', 0.35)
    grass_ground(pn, GROUND - 60, t)
    butt(pn, 960, GROUND - 40, 0.55)
    d = draw_curve(t, t_draw, t_full) if t_draw is not None else 0.0
    full = d > 0.97
    ex = 'determined'
    if t_pain is not None and t > t_pain: ex = 'pain'
    archer(pn, HK['x'], HK['y'], HK['k'], 1, d, t, expr=ex, look=(1.0, 0.0), tremble=1.0 if full else 0.0)

def sc_hook(base, pn, t):
    hook_frame(base, pn, t, T['pull0'], T['force'] - 0.12, t_pain=T['force'] - 0.05)

def cam_hook(t, sc, ox, oy):
    return camfocus(1.32 * sc * (1 + 0.05 * eio(P(t, 0, T['of0']))), 480, 1080, CX, 930, ox, oy)

# ---------------- 2. the force of lifting a grown man ----------------
LF = dict(px=380, top=560, ax=760, k=1.6)
def sc_lift(base, pn, t):
    bgp(base, 'green', 0.35)
    grass_ground(pn, GROUND - 60, t)
    k = LF['k']
    wheel, wr = pulley_frame(pn, LF['px'], LF['top'], GROUND, 1.25)
    rise = eio(P(t, T['lifting'] - 0.05, T['man'] - T['lifting'] + 0.25))
    # the grown man on a plank seat, hanging from the left fall of the rope
    seat_y = GROUND - 120 - 230 * rise
    mx = wheel[0] - wr
    def seat(pn_, J):
        pass
    # rope: from the seat up over the wheel and down to the archer's hands
    ax, ay, ak = LF['ax'], GROUND + 30, k
    pull = rise
    p = pose('pull', torso=-14 - 8 * pull)
    hF = ((wheel[0] + wr + 70 - ax) / ak + 30 * pull, (ay - 330 - ay) / ak + 40 * pull)
    hB = (hF[0] + 14, hF[1] + 26)
    hands = {'F': hF, 'B': hB}
    J0 = joints(p, -1, 1.0, hands)
    hw = (ax + J0['haF'][0] * ak, ay + J0['haF'][1] * ak)
    rope_line(pn, [(mx, seat_y - 150), (mx, wheel[1])], 6)
    rope_line(pn, [(wheel[0] + wr, wheel[1]), hw], 6)
    # the man: sitting, hands on the rope at his chest, legs dangling
    sp = pose('idle', thF=78, shF=-8, thB=70, shB=-4)
    swing = 6 * math.sin(t * 5) * rise
    man_expr = 'worried' if t < T['grown'] else 'surprised'
    pn.rect(mx - 70, seat_y - 4, mx + 70, seat_y + 12, fill=lb.WOOD if hasattr(lb, 'WOOD') else WOOD, outline=INK, width=3)
    for sd in (-1, 1): rope_line(pn, [(mx + sd * 60, seat_y), (mx, seat_y - 150)], 4)
    figure(pn, mx + swing, seat_y + 2, 1.15, 1, sp, 'villager', man_expr, look=(0.2, 0.8 if t < T['grown'] else -0.4), blink=blink_at(t, 2),
           hands={'F': (8, -150), 'B': (-6, -138)}, held=lambda pn_, J: None)
    # the archer hauls with both hands, leaning back
    figure(pn, ax, ay, ak, -1, p, KEEPER, 'pain' if t > T['lifting'] else 'determined', look=(-0.6, -0.6), blink=blink_at(t, 1),
           hands=hands, grip=lambda pn_, J: None)
    if T['lifting'] - 0.05 < t < T['man']:
        speed_lines(pn, mx, seat_y + 60, 0, -1, t, length=160, n=5, spread=70, seed=3)
    particles(pn, 'dust', mx, GROUND - 60, t, T['lifting'], 0.8, seed=4, ground=GROUND - 56)

# ---------------- 3. about 150 pounds (ritual screen, stamp) ----------------
def sc_weight(base, pn, t):
    base.paste(bg_cam(env.get('ritual'), 0.3))
    v = 150 * eo3(P(t, T['around1'] - 0.15, T['n150'] - T['around1'] + 0.15))
    d = v / 150
    # the bow fixed at its grip on a peg, weights hung from the string: how draw weight is measured
    gx, gy, k = 540, 690, 1.45
    pn.rect(gx - 30, 540, gx + 30, gy - 8, fill=WOOD_D, outline=INK, width=3)
    pn.circ(gx, gy - 6, 16, fill=IRON, outline=INK, width=3)
    pn.push(gx, gy, k)
    B = longbow(pn, 0, 0, 1, d, string_to=(0, 24 + 86 * d), tilt=-math.pi / 2)
    pn.pop()
    sx, sy = gx, gy + (24 + 86 * d) * k
    n = int(round(5 * d + 0.0001))
    hook_y = sy + 30
    pn.line([(sx, sy), (sx, hook_y)], IRON, 5)
    for i in range(5):
        a = clamp(5 * d - i)
        if a <= 0: continue
        yy = hook_y + 10 + i * 56
        sc_ = eoback(a)
        pn.push(sx, yy + 26, sc_)
        pn.rect(-78, -26, 78, 26, fill=IRON, outline=INK, width=3, r=6)
        pn.rect(-70, -20, 70, -12, fill=light(IRON, 0.35), r=3)
        pn.pop()
        if a < 1: particles(pn, 'sparks', sx, yy + 50, t, T['around1'] - 0.15 + i * 0.12, 0.4, seed=i)
    counter(pn, 540, 330, v)
    impact(pn, 540, 330, t, T['n150'], 1.2, seed=5, col=(255, 220, 170))
    stamp(pn, 800, 500, 'LIKELY', t - (T['n150'] - 0.06), sz=96)
    tag(pn, 540, 1275, 'BASED ON BOWS FROM 1545', 50, pop(t, T['pounds1']), rot_=-2, sub='RAISED WITH THE MARY ROSE WRECK')

# ---------------- 4. the English longbow, six and a half feet of yew ----------------
BW = dict(x=400, y=GROUND, k=1.6)
def yew_sprig(pn, x, y, s, t, a=1.0):
    if a <= 0: return
    pn.push(x, y, s * eoback(clamp(a)))
    pn.line([(-120, 60), (120, -40)], INK, 9); pn.line([(-120, 60), (120, -40)], (110, 74, 46), 5)
    for i in range(14):
        u = i / 13; bx = lerp(-110, 110, u); by = lerp(56, -36, u)
        for sd in (-1, 1):
            tip = (bx + 8 + sd * 4, by + sd * 30)
            pn.poly([(bx - 3, by), (tip[0] - 4, tip[1]), (tip[0] + 4, tip[1]), (bx + 3, by)], fill=(48, 86, 52), outline=INK, width=1.6)
    for (bx, by) in ((-40, 52), (30, 28), (80, 2)):
        pn.circ(bx, by + 20, 11, fill=(204, 46, 48), outline=INK, width=2)
        pn.circ(bx, by + 20, 4, fill=(60, 40, 30))
    pn.pop()

def sc_bow(base, pn, t):
    bgp(base, 'parch', 0.0)
    floor(pn, GROUND)
    x, y, k = BW['x'], BW['y'], BW['k']
    rise = eoback(P(t, T['english2'] - 0.15, 0.4)) if t > T['english2'] - 0.15 else 0.0
    glow = win(t, T['longbow'] - 0.05, T['longbow'] + 0.7, 0.1, 0.4)
    gl = (72, -150)
    def held(pn_, J):
        if rise <= 0: return
        g = J['haF']
        pn_.push(g[0], g[1] + 152 * (1 - min(1, rise)), 1.0)
        longbow(pn_, 0, 0, 1, 0.0, hl_back=glow * 0.5, hl_belly=glow * 0.3)
        pn_.pop()
    ex = 'neutral' if t < T['longbow'] else ('proud' if t < T['yew'] else 'happy')
    figure(pn, x, y, k, 1, 'idle', KEEPER, ex, look=(0.9, -0.3), blink=blink_at(t, 0.3),
           hands={'F': gl} if rise > 0 else None, held=held if rise > 0 else None)
    # dimension: tip to tip
    top = (x + (gl[0] - 24) * k + 70, y + (gl[1] - 152) * k); bot = (top[0], y + (gl[1] + 152) * k)
    a = eio(P(t, T['about3'] - 0.1, T['feet'] - T['about3'] + 0.1))
    if a > 0:
        mid = (top[1] + bot[1]) / 2
        y0 = lerp(mid, top[1], a); y1 = lerp(mid, bot[1], a)
        pn.line([(top[0], y0), (top[0], y1)], RUST, 7)
        for yy, dr in ((y0, -1), (y1, 1)):
            pn.poly([(top[0], yy + dr * 6), (top[0] - 16, yy - dr * 22), (top[0] + 16, yy - dr * 22)], fill=RUST)
            pn.line([(top[0] - 34, yy), (top[0] + 34, yy)], RUST, 5)
        tag(pn, top[0] + 190, mid - 40, 'ABOUT 2 M', 54, pop(t, T['feet']), rot_=3)
    yew_sprig(pn, 790, 700, 1.1, t, P(t, T['yew'] - 0.08, 0.35))
    if t > T['yew'] - 0.08:
        particles(pn, 'sparks', 790, 700, t, T['yew'] - 0.02, 0.5, seed=7, col=(120, 200, 110))

def cam_bow(t, sc, ox, oy):
    return camfocus(lerp(1.3, 1.36, eio(P(t, T['lbs'], 3.8))) * sc, 560, 1000, CX, 900, ox, oy)

def cam_lift(t, sc, ox, oy):
    return camfocus(1.2 * sc, 580, 960, CX, 880, ox, oy)

def cam_spring(t, sc, ox, oy):
    return camfocus(1.22 * sc, 580, 1060, CX, 960, ox, oy)

def cam_train(t, sc, ox, oy):
    return camfocus(lerp(1.3, 1.18, eio(P(t, T['years'] - 0.1, 0.8))) * sc, 520, 1080, CX, 940, ox, oy)

def cam_ratio(t, sc, ox, oy):
    return camfocus(lerp(1.08, 1.12, eio(P(t, T['ratio_s'], 3.4))) * sc, 510, 1140, CX, 1010, ox, oy)

def cam_rain(t, sc, ox, oy):
    return camfocus(lerp(1.3, 1.38, eio(P(t, T['rain_s'], 3.0))) * sc, 540, 1170, CX, 1010, ox, oy)

# ---------------- 5. the bowyer splits the stave ----------------
LOG = dict(x=470, y=1110, r=130)
BWY = dict(x=690, y=GROUND, k=1.7)
WEDGE_TOP = (LOG['x'], LOG['y'] - LOG['r'] + 6 - 54)
def bowyer_rig(t):
    """Pose, IK hand target (local) and mallet direction for the bowyer's wind up and strike."""
    k = BWY['k']
    p = pose('idle', torso=lerp(-2, 8, P(t, T['strike'] - 0.12, 0.12)))
    J0 = joints(p, -1, 1.0)
    S_ = (BWY['x'] + J0['shF'][0] * k, BWY['y'] + J0['shF'][1] * k)
    dx, dy = S_[0] - WEDGE_TOP[0], S_[1] - WEDGE_TOP[1]; D = math.hypot(dx, dy)
    hit = (WEDGE_TOP[0] + dx / D * 58 * k, WEDGE_TOP[1] + dy / D * 58 * k)
    hit_l = ((hit[0] - BWY['x']) / k, (hit[1] - BWY['y']) / k)
    up_l = (J0['neck'][0] - 52, J0['neck'][1] - 46)
    rest_l = (J0['neck'][0] - 46, J0['neck'][1] + 60)
    if t < T['strike'] - 0.12:
        u = eio(P(t, T['bowyer_s'] - 0.1, 0.5)); h = (lerp(rest_l[0], up_l[0], u), lerp(rest_l[1], up_l[1], u)); d_ = (-0.25, -1)
    elif t < T['strike']:
        u = ei3(P(t, T['strike'] - 0.12, 0.12)); h = (lerp(up_l[0], hit_l[0], u), lerp(up_l[1], hit_l[1], u))
        d_ = (lerp(-0.25, -dx / D, u), lerp(-1, -dy / D, u))
    else:
        u = eio(P(t, T['strike'] + 0.15, 0.4)); h = (lerp(hit_l[0], rest_l[0], u), lerp(hit_l[1], rest_l[1], u))
        d_ = (lerp(-dx / D, -0.6, u), lerp(-dy / D, 0.8, u))
    L = math.hypot(*d_) or 1
    return p, h, (d_[0] / L, d_[1] / L)

def sc_bowyer(base, pn, t):
    bgp(base, 'workshop', 0.0)
    floor(pn, GROUND, (124, 98, 70))
    split = eo3(P(t, T['strike'], 0.5))
    trestle(pn, LOG['x'], LOG['y'] + LOG['r'] - 6, 180, GROUND - (LOG['y'] + LOG['r'] - 6))
    log_end(pn, LOG['x'], LOG['y'], LOG['r'], split=split if split > 0 else 0.0, glow_sap=win(t, T['stave'] - 0.1, 99, 0.3, 0.1) * 0.4)
    wy = LOG['y'] - LOG['r'] + 6 + 30 * eo3(P(t, T['strike'], 0.08))
    if split < 0.6: wedge(pn, LOG['x'], wy, 1.6)
    BX, BY, BK = BWY['x'], BWY['y'], BWY['k']
    p, h, dr = bowyer_rig(t)
    def mal(pn_, J): mallet(pn_, J['haF'], (J['haF'][0] - dr[0] * 10, J['haF'][1] - dr[1] * 10), 1.0)
    if T['strike'] - 0.14 < t < T['strike'] + 0.04:
        sm = []
        for dt in (0.12, 0.08, 0.04, 0.0):
            p_, h_, d2 = bowyer_rig(t - dt)
            J_ = joints(p_, -1, 1.0, {'F': h_})
            hh = J_['haF']; tip = (hh[0] + d2[0] * 62, hh[1] + d2[1] * 62)
            sm.append(((BX + hh[0] * BK, BY + hh[1] * BK), (BX + tip[0] * BK, BY + tip[1] * BK)))
        smear(pn, sm, alpha=200)
    figure(pn, BX, BY, BK, -1, p, 'bowyer', 'determined' if t < T['strike'] + 0.2 else 'happy', look=(-0.9, 0.3), blink=blink_at(t, 1.5),
           hands={'F': h}, held=mal)
    impact(pn, WEDGE_TOP[0], WEDGE_TOP[1] + 10, t, T['strike'], 0.75, seed=11)
    particles(pn, 'chips', LOG['x'], LOG['y'] - LOG['r'] + 10, t, T['strike'], 1.1, seed=12, cone=math.pi * 0.9, ground=GROUND)
    particles(pn, 'sparks', WEDGE_TOP[0], WEDGE_TOP[1], t, T['strike'], 0.6, seed=13)

def cam_bowyer(t, sc, ox, oy):
    m = eio(P(t, T['strike'] + 0.2, 0.9))
    return camfocus(lerp(1.15, 1.32, m) * sc, lerp(560, LOG['x'], m), lerp(1060, LOG['y'], m), CX, lerp(940, 900, m), ox, oy)

# ---------------- 6. sapwood faces the target, heartwood faces the archer ----------------
def d_section(pn, x, y, r, t, hb, hh):
    """Cross section of the limb: flat back of pale sapwood toward the target (right), rounded belly of heartwood toward
    the archer (left)."""
    pn.circ(x + 8, y + 10, r * 1.04, fill=(0, 0, 0, 50))
    pts_belly = [(x - r * 0.25 + math.cos(math.radians(a)) * r, y + math.sin(math.radians(a)) * r * 0.82) for a in range(90, 271, 6)]
    seam = x + r * 0.25
    belly = [(seam, y - r * 0.82)] + pts_belly[::-1][::-1] + [(seam, y + r * 0.82)]
    belly = [(seam, y + r * 0.82)] + [(x - r * 0.25 + math.cos(math.radians(a)) * r * 1.0, y + math.sin(math.radians(a)) * r * 0.82) for a in range(90, 271, 6)] + [(seam, y - r * 0.82)]
    back = [(seam, y - r * 0.82), (x + r * 0.62, y - r * 0.74), (x + r * 0.7, y), (x + r * 0.62, y + r * 0.74), (seam, y + r * 0.82)]
    pn.poly(belly, fill=lerpc(HEART, AMBER, hh))
    pn.poly(back, fill=lerpc(SAP, AMBER, hb))
    for k_ in (0.35, 0.6, 0.85):        # growth rings curving across both woods
        pn.arc(x + r * 1.6, y, r * (1.2 + k_), 152, 208, shade(HEART, 0.22) + (180,), 2)
    pn.line([(seam, y - r * 0.82), (seam, y + r * 0.82)], INK + (120,), 2.4)
    pn.poly(belly[:-1] + back[1:], outline=INK, width=5)

def sc_layers(base, pn, t):
    bgp(base, 'parch', 0.0)
    floor(pn, GROUND)
    hb = win(t, T['pale'] - 0.1, 99, 0.25, 0.1); hh = win(t, T['heartwood5'] - 0.1, 99, 0.25, 0.1)
    A = archer(pn, 230, GROUND, 1.75, 1, 0.9, t, expr='determined', look=(1, 0), tremble=0.3)
    tg = butt(pn, 900, GROUND, 1.1)
    if t > T['target'] - 0.1:
        u = P(t, T['target'] - 0.1, 0.6)
        ring = (u > 0) and (u < 1)
        if ring: pn.circ(tg[0], tg[1], 40 + 110 * u, outline=AMBER + (int(255 * (1 - u)),), width=8)
    # the inset: a cut through the limb
    cx, cy, r = 600, 520, 170
    a = pop(t, T['so4'] + 0.05, 0.35)
    g = A['grip']
    limb_pt = (g[0] + 6, g[1] - 150)
    if a > 0:
        pn.line([limb_pt, (cx - r * 0.9, cy + r * 0.4)], INK + (int(160 * min(1, a)),), 3)
        pn.circ(*limb_pt, 9, outline=INK, width=3)
        pn.push(cx, cy, a)
        d_section(pn, 0, 0, r, t, hb * 0.55, hh * 0.45)
        pn.pop()
    # direction arrows: back toward the target, belly toward the archer
    if hb > 0:
        arrow_line(pn, (cx + r * 0.8, cy), (cx + r * 0.8 + 150, cy), RUST, 9, 28, p=eo3(P(t, T['target'] - 0.15, 0.35)))
        callout(pn, cx + r * 0.45, cy - r * 0.55, cx + 190, cy - 250, 'BACK', P(t, T['sapwood4'], 0.5), 48, hl=True)
    if hh > 0:
        arrow_line(pn, (cx - r * 1.2, cy), (cx - r * 1.2 - 150, cy), RUST, 9, 28, p=eo3(P(t, T['archer5'] - 0.15, 0.35)))
        callout(pn, cx - r * 0.6, cy - r * 0.5, cx - 300, cy - 250, 'BELLY', P(t, T['heartwood5'], 0.5), 48, hl=True)
    if t > T['archer5'] - 0.05:
        u = P(t, T['archer5'] - 0.05, 0.6)
        if u < 1: pn.circ(230, GROUND - 400, 70 + 130 * u, outline=AMBER + (int(255 * (1 - u)),), width=8)

# ---------------- 7. stretching and crushing ----------------
def sc_bend(base, pn, t):
    bgp(base, 'parch', 0.0)
    b = 0.75 * eio(P(t, T['bend_s'] - 0.05, T['stretching'] - T['bend_s'] + 0.1))
    b *= 1 + 0.06 * math.sin(t * 3)
    th_hl = win(t, T['stretching'] - 0.12, 99, 0.2, 0.1); cr_hl = win(t, T['crushing'] - 0.12, 99, 0.2, 0.1)
    cx, cy = 540, 820
    G = limb_segment(pn, cx, cy, 430, 110, b, th_hl * 0.5, cr_hl * 0.5)
    top, bot = G['top'], G['bot']
    if th_hl > 0:
        for i0, i1 in ((3, 12), (18, 27)):
            a_, b_ = top[i0], top[i1]
            off = lambda p_: (p_[0], p_[1] - 50)
            s_ = clamp(th_hl * 1.4)
            m = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2 - 50)
            double_arrow(pn, (lerp(m[0], a_[0], s_), lerp(m[1], a_[1] - 50, s_)), (lerp(m[0], b_[0], s_), lerp(m[1], b_[1] - 50, s_)), RUST, 9, 26, out=True)
        tag(pn, 540, 470, 'TENSION', 62, pop(t, T['stretching']) * (1 - P(t, T['crushing'] - 0.2, 0.2)), rot_=-3)
    if cr_hl > 0:
        for i0, i1 in ((5, 13), (17, 25)):
            a_, b_ = bot[i0], bot[i1]
            double_arrow(pn, (a_[0], a_[1] + 60), (b_[0], b_[1] + 60), RUST, 9, 26, out=False)
        tag(pn, 540, 1180, 'COMPRESSION', 62, pop(t, T['crushing']), rot_=3)
    # the limb stores the energy: it springs back at the end of the line
    pn.text(540, 300, '', 10, INK)

def cam_bend(t, sc, ox, oy):
    return sc * lerp(1.0, 1.06, eio(P(t, T['bend_s'], 3.4))), ox, oy

# ---------------- 8. like a spring: the release ----------------
SP = dict(x=250, y=GROUND + 20, k=1.55, tx=930)
def arrow_flight(t, A0, t0, x1, y1, dur=0.3):
    u = clamp((t - t0) / dur)
    x0, y0 = A0
    x = lerp(x0, x1, u); y = lerp(y0, y1, u) - 40 * math.sin(math.pi * u)
    return x, y, u

def sc_spring(base, pn, t):
    bgp(base, 'green', 0.35)
    grass_ground(pn, GROUND - 40, t)
    tg = butt(pn, SP['tx'], GROUND - 30, 0.85, hit=((-4, 2, 0.06),) if t > T['thunk'] else ())
    released = t >= T['release']
    d = draw_curve(t, T['spr_s'] - 0.05, T['wood8'] + 0.3)
    A = archer(pn, SP['x'], SP['y'], SP['k'], 1, d, t, expr='determined' if not released else 'smug', look=(1, 0),
               rel=(t - T['release']) if released else None, tremble=0.6 if d > 0.97 and not released else 0.0)
    if released and t < T['thunk'] + 0.02:
        tip0 = archer_geom(SP['x'], SP['y'], SP['k'], 1, 1.0)[0]
        x, y, u = arrow_flight(t, tip0, T['release'], tg[0] - 8, tg[1] + 2, T['thunk'] - T['release'])
        ang = math.atan2((tg[1] - tip0[1]) - 40 * math.pi * math.cos(math.pi * u), tg[0] - tip0[0])
        arrow(pn, (x - math.cos(ang) * ARROW_L * 1.55, y - math.sin(ang) * ARROW_L * 1.55), ang, ARROW_L * 1.55 - 6)
        speed_lines(pn, x - 60, y, math.cos(ang), math.sin(ang), t, length=300, n=7, spread=26, seed=21)
    if released:
        impact(pn, A['grip'][0] + 10, A['grip'][1], t, T['release'], 0.5, seed=22, col=(255, 255, 255))
    impact(pn, tg[0], tg[1], t, T['thunk'], 1.0, seed=23)
    particles(pn, 'dust', tg[0], tg[1] + 10, t, T['thunk'], 0.9, seed=24, ground=GROUND - 30)
    particles(pn, 'chips', tg[0], tg[1], t, T['thunk'], 0.7, seed=25, col=(214, 196, 140))

# ---------------- 9. years of training ----------------
def sc_train(base, pn, t):
    bgp(base, 'green', 0.35)
    grass_ground(pn, GROUND - 40, t)
    butt(pn, 950, GROUND - 30, 0.7)
    grow = 0.0
    steps = [T['years'] - 0.05, T['years'] + 0.22, T['years'] + 0.5]
    for i, s0 in enumerate(steps):
        grow += eoback(P(t, s0, 0.25)) / 3
    k = lerp(1.15, 1.62, grow)
    adult = t > steps[1] + 0.05
    if t < T['years'] - 0.05:
        d = 0.32 * eio(P(t, T['draw9'] - 0.15, 0.4)) + 0.04 * math.sin(t * 30) * P(t, T['draw9'], 0.2)
        ex = 'determined' if t < T['draw9'] else 'pain'
        trem = 1.5 if t > T['draw9'] else 0.0
    elif t < T['training'] - 0.1:
        d = 0.15; ex = 'determined'; trem = 0.0
    else:
        d = eio(P(t, T['training'] - 0.1, 0.45)); ex = 'proud' if t > T['training'] + 0.5 else 'determined'; trem = 0.0
    out = 'archer3' if adult else 'boy'
    archer(pn, 360, GROUND + 10, k, 1, d, t, out=out, expr=ex, look=(1, 0), tremble=trem)
    for i, s0 in enumerate(steps):
        particles(pn, 'dust', 360, GROUND + 6, t, s0, 0.35 + 0.08 * i, seed=30 + i, ground=GROUND + 8, col=(196, 190, 150))
        impact(pn, 360, GROUND - 200 * lerp(1.15, 1.62, (i + 1) / 3), t, s0, 0.35, seed=33 + i, col=(255, 240, 200), lines=True)

# ---------------- 10. the law: archery practice on holidays ----------------
def sc_law(base, pn, t):
    bgp(base, 'green', 0.3)
    grass_ground(pn, GROUND - 40, t)
    tg = butt(pn, 910, GROUND - 30, 1.15, hit=tuple(h for tt, h in ((T['archery'] + 0.3, (-10, 4, 0.08)), (T['holidays'] + 0.12, (12, -10, 0.04))) if t > tt))
    op = eio(P(t, T['law'] - 0.2, 0.45))
    scroll(pn, 540, 250, 440, op, seal=P(t, T['ordered'] - 0.05, 0.3))
    tag(pn, 300, 600, '1363', 70, pop(t, T['men10']), rot_=-5, sub="EDWARD III'S ORDER")
    bunting(pn, -20, 1100, 660, t, P(t, T['holidays'] - 0.15, 0.6))
    for i, (x, out, rel_t) in enumerate(((160, 'archer2', T['archery']), (450, 'villager', T['holidays'] - 0.05))):
        d = draw_curve(t, T['practise'] - 0.5 + i * 0.15, rel_t - 0.1)
        released = t > rel_t
        A = archer(pn, x, GROUND + 10, 1.3, 1, d, t, out=out, expr='determined' if not released else 'happy', look=(1, 0),
                   rel=(t - rel_t) if released else None, arrow_on=t > T['law_s'] + 0.2)
        if released and t < rel_t + 0.3:
            t0 = archer_geom(x, GROUND + 10, 1.3, 1, 1.0)[0]
            hx = tg[0] + (-10 if i == 0 else 12); hy = tg[1] + (4 if i == 0 else -10)
            u = (t - rel_t) / 0.3
            px = lerp(t0[0], hx, u); py = lerp(t0[1], hy, u) - 30 * math.sin(math.pi * u)
            arrow(pn, (px - ARROW_L * 1.3, py), 0.0, ARROW_L * 1.3 - 6)
            speed_lines(pn, px - 40, py, 1, 0, t, length=200, n=5, spread=16, seed=40 + i)
        impact(pn, tg[0], tg[1], t, rel_t + 0.3, 0.6, seed=44 + i)

# ---------------- 11. the skeletons ----------------
def sc_bones(base, pn, t):
    bgp(base, 'lab', 0.0)
    floor(pn, GROUND + 60, (150, 140, 124))
    # light box standing on the floor
    pn.rect(170, 380, 910, GROUND + 60, fill=(236, 240, 236), outline=INK, width=5, r=10)
    pn.rect(190, 400, 890, GROUND + 40, outline=(200, 210, 210), width=3, r=6)
    a = pop(t, T['bones_s'] - 0.05, 0.35)
    thick = eio(P(t, T['heavier'] - 0.05, T['bones'] - T['heavier'] + 0.2))
    drw = eio(P(t, T['drawing'] - 0.1, 0.45))
    hl = win(t, T['heavier'] - 0.05, 99, 0.2, 0.1)
    if a > 0:
        pn.push(540, GROUND + 30, a)
        skeleton(pn, 0, 0, 2.15, arm_thick=thick, hl=hl * 0.6, draw=0.0)
        pn.pop()
    if thick > 0:
        impact(pn, 540 + 60 * 2.15, GROUND + 30 - 238 * 2.15, t, T['bones'], 0.45, seed=51, col=(255, 230, 170), lines=True)

def cam_bones(t, sc, ox, oy):
    m = eio(P(t, T['heavier'] - 0.2, 0.6))
    return camfocus(lerp(1.0, 1.22, m) * sc, lerp(540, 600, m), lerp(860, 660, m), CX, lerp(CY, 820, m), ox, oy)

# ---------------- 12. the map: Agincourt ----------------
_MAP = {}
def map_img(name):
    if name not in _MAP: _MAP[name] = Image.open(f'map_{name}.png').convert('RGB')
    return _MAP[name]
LV = {l[0]: l for l in MM.LEVELS}
def geo_xy(lon, lat, lev='ov'):
    _, c_lon, c_lat, span, _ = LV[lev]
    lon_px, lat_px = MM.geo(c_lon, c_lat, span)
    return 540 + (lon - c_lon) / lon_px, 960 - (lat - c_lat) / lat_px
AGIN = (2.14, 50.46); LONDON = (-0.13, 51.51); CALAIS = (1.86, 50.95)

class MapView:
    def __init__(s, z, fx_, fy, tx, ty): s.z, s.fx, s.fy, s.tx, s.ty = z, fx_, fy, tx, ty
    def img_of(s, lev):
        if lev == 'ov':
            z, fx_, fy = s.z, s.fx, s.fy
        else:
            r = LV['ov'][3] / LV[lev][3]
            lon, lat = s.geo(s.fx, s.fy)
            fx_, fy = geo_xy(lon, lat, lev); z = s.z / r
        a = 2 / z
        return map_img(lev).transform((W, H), Image.AFFINE, (a, 0, 2 * fx_ - s.tx * a, 0, a, 2 * fy - s.ty * a), Image.BILINEAR)
    def geo(s, px, py):
        _, c_lon, c_lat, span, _ = LV['ov']; lon_px, lat_px = MM.geo(c_lon, c_lat, span)
        return c_lon + (px - 540) * lon_px, c_lat - (py - 960) * lat_px
    def img(s):
        r = LV['ov'][3] / LV['det'][3]
        m = clamp((s.z - r * 1.0) / (r * 0.12))
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

def sc_map(base, pn, t):
    r = LV['ov'][3] / LV['det'][3]
    zp = eio(P(t, T['d25'] - 0.1, T['at13'] - T['d25'] + 0.1))
    z = lerp(1.0, r * 1.25, zp)
    f0 = geo_xy(0.9, 50.3); f1 = geo_xy(*AGIN)
    fx_, fy = lerp(f0[0], f1[0], zp), lerp(f0[1], f1[1], zp)
    mv = MapView(z, fx_, fy, 540, lerp(960, 900, zp))
    base.paste(mv.img())
    la = 1 - P(t, T['d25'] + 0.3, 0.3)
    label(pn, *mv.xy(-0.9, 51.9), 'ENGLAND', 56, P(t, T['map_s'] + 0.05, 0.3) * la)
    label(pn, *mv.xy(2.3, 49.0), 'FRANCE', 64, P(t, T['october'], 0.3) * la)
    a = mv.xy(*AGIN)
    pin(pn, *a, t, T['agincourt'] - 0.12)
    sp_ = eoback(P(t, T['agincourt'] + 0.12, 0.4)) if t > T['agincourt'] + 0.12 else 0
    if sp_ > 0:
        pn.push(a[0], a[1] - 40, sp_)
        for sd in (-1, 1):
            rnd = random.Random(7 + sd)
            for i in range(9):
                pn.circ(sd * 200 + rnd.uniform(-60, 60), rnd.uniform(-260, 220), rnd.uniform(40, 62), fill=(78, 98, 64, 235))
        for rI in range(3):
            pn.rect(-110 + rI * 8, -300 + rI * 40, 110 - rI * 8, -276 + rI * 40, fill=(52, 74, 140), outline=INK, width=3, r=6)
        pn.rect(-120, 230, 120, 254, fill=(190, 40, 36), outline=INK, width=3, r=6)
        pn.pop()
        label(pn, 540, 1250, 'SIMPLIFIED', 34, sp_ * 0.9)
    tag(pn, 540, 470, 'AZINCOURT', 70, pop(t, T['agincourt'] + 0.3), rot_=-3, sub='THE FRENCH SPELLING')

# ---------------- 13. four in five were archers ----------------
def royal_banner(pn, x, y, k, t):
    """Arms of Henry V: quarterly, France modern (blue, gold lis) and England (red, gold lions)."""
    pn.line([(x, y), (x, y - 300 * k)], INK, 9 * k); pn.line([(x, y), (x, y - 300 * k)], WOOD, 5 * k)
    w_, h_ = 150 * k, 120 * k; x0, y0 = x + 5 * k, y - 290 * k
    wav = lambda u: 6 * k * math.sin(t * 4 + u * 4) * u
    for qi, (u0, v0) in enumerate(((0, 0), (0.5, 0), (0, 0.5), (0.5, 0.5))):
        fr = qi in (0, 3)
        pts = [(x0 + (u0 + du) * w_, y0 + (v0 + dv) * h_ + wav(u0 + du)) for du, dv in ((0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5))]
        pn.poly(pts, fill=(40, 62, 130) if fr else (176, 34, 38))
        cx_ = x0 + (u0 + 0.25) * w_; cy_ = y0 + (v0 + 0.25) * h_ + wav(u0 + 0.25)
        if fr: lb.fleur(pn, cx_, cy_ + 2 * k, 0.9 * k, (232, 184, 60))
        else: lion(pn, cx_, cy_, 1.2 * k)
    pn.poly([(x0, y0 + wav(0)), (x0 + w_, y0 + wav(1)), (x0 + w_, y0 + h_ + wav(1)), (x0, y0 + h_ + wav(0))], outline=INK, width=3)

def sc_ratio(base, pn, t):
    bgp(base, 'agin', 0.3)
    grass_ground(pn, 1060, t, (120, 124, 80))
    rows = [(1120, 0.62), (1215, 0.72), (1310, 0.82)]
    for ri, (y, k) in enumerate(rows):
        for c in range(5):
            x = 120 + c * 190 + (ri % 2) * 24
            is_arch = c < 4
            arm = t > T['four'] - 0.1 + c * 0.08 and is_arch
            ex = 'determined'
            if is_arch:
                if arm:
                    def held(pn_, J, k_=k):
                        g = J['haF']; longbow(pn_, g[0], g[1], 1, 0.0)
                    figure(pn, x, y, k, 1, 'idle', ('archer', 'archer2', 'archer3')[(c + ri) % 3], ex, blink=blink_at(t, c + ri),
                           hands={'F': (50, -150)}, held=held)
                else:
                    figure(pn, x, y, k, 1, 'idle', ('archer', 'archer2', 'archer3')[(c + ri) % 3], 'neutral', blink=blink_at(t, c + ri))
            elif ri == 0:
                figure(pn, x, y, k, 1, 'idle', 'engma', ex, blink=blink_at(t, c + ri), hands={'F': (40, -140)},
                       held=lambda pn_, J: royal_banner(pn_, J['haF'][0], J['haF'][1] + 40, 1.0, t))
            else:
                figure(pn, x, y, k, 1, 'idle', 'engma', ex, blink=blink_at(t, c + ri))
    # highlight the four archer columns, then the fifth
    a = win(t, T['four'] - 0.05, T['henry'] + 0.2, 0.15, 0.3)
    if a > 0:
        pn.rect(50, 830, 810, 1345, outline=AMBER + (int(230 * a),), width=9, r=30)
    b = win(t, T['five'] - 0.05, T['henry'] + 0.2, 0.15, 0.3)
    if b > 0:
        pn.rect(830, 830, 970, 1345, outline=(240, 240, 240, int(200 * b)), width=7, r=24)
        tag(pn, 900, 770, '1', 60, pop(t, T['five']), rot_=4)
    if a > 0: tag(pn, 430, 770, '4', 60, pop(t, T['four']) * a, rot_=-4)
    ar = win(t, T['archers14'] - 0.1, 99, 0.15, 0.2)
    if ar > 0:
        for ri, (y, k) in enumerate(rows):
            for c in range(4):
                x = 120 + c * 190 + (ri % 2) * 24
                pn.circ(x, y - 218 * k, 58 * k, outline=AMBER + (int(200 * ar * (0.6 + 0.4 * math.sin(t * 8))),), width=4)

def hud_ratio(pn, t):
    tag(pn, 540, 300, 'ABOUT 5,000 ARCHERS', 58, pop(t, T['men14']), rot_=-2, sub='ESTIMATES VARY')

# ---------------- 14. the French, most on foot ----------------
def french_rows(pn, t, speed=1.0, sink=0.0, x_off=0.0, expr='determined', cower=0.0):
    rows = [(1110, 0.42, 7, 0), (1200, 0.5, 6, 1), (1300, 0.6, 5, 2)]
    outs = ('french1', 'french2', 'french3')
    for ri, (y, k, n, s_) in enumerate(rows):
        for i in range(n):
            x = 120 + i * (900 / (n - 1 if n > 1 else 1)) - 60 * s_ + x_off * k + (ri % 2) * 40
            ph = t * 7 * speed + i * 1.3 + ri
            p = walk_pose(ph / 7, 7, 16 * speed) if speed > 0 else pose('idle')
            if cower > 0: p = mix(p, 'cower', cower)
            yy = y + sink * 30 * k
            def bnr(pn_, J, k_=k):
                h = J['haF']
                pn_.line([(h[0], h[1] + 40), (h[0], h[1] - 300)], INK, 9); pn_.line([(h[0], h[1] + 40), (h[0], h[1] - 300)], WOOD, 5)
            carry = (ri == 0 and i == 3)
            if carry:
                J = figure(pn, x, yy, k, -1, p, outs[(i + ri) % 3], expr, look=(-1, 0), blink=blink_at(t, i + ri), hands={'F': (-24, -150)}, held=bnr)
                hx, hy = x + J['haF'][0] * k, yy + J['haF'][1] * k
                banner_fr(pn, hx, hy - 300 * k + 330 * k * 0.0 + 300 * k - 300 * k, k * 0.95, t) if False else None
                lb.banner_fr(pn, hx, hy + 40 * k, k, t)
            else:
                figure(pn, x, yy, k, -1, p, outs[(i + ri) % 3], expr, look=(-1, 0), blink=blink_at(t, i + ri))

def sc_french(base, pn, t):
    bgp(base, 'agin', 0.3)
    grass_ground(pn, 1060, t, (120, 124, 80))
    adv = (t - T['fr_s']) * 40
    french_rows(pn, t, 1.0, x_off=-adv)
    st = T['foot'] - 0.02
    for i, x in enumerate(range(140, 1000, 170)):
        particles(pn, 'dust', x, 1305, t, st, 0.7, seed=60 + i, cone=math.pi * 0.7, ground=1320)

def cam_french(t, sc, ox, oy):
    return camfocus(lerp(1.36, 1.44, eio(P(t, T['fr_s'], 1.9))) * sc, 540, 1180, CX, 1010, ox, oy)

# ---------------- 15. the ploughed field, soaked by rain ----------------
def sc_rainfield(base, pn, t):
    wet = eio(P(t, T['soaked'] - 0.1, T['rain'] - T['soaked'] + 0.2))
    if wet <= 0: bgp(base, 'agin', 0.3)
    elif wet >= 1: bgp(base, 'aginrain', 0.3)
    else: base.paste(Image.blend(bg_cam(env.get('agin'), 0.3), bg_cam(env.get('aginrain'), 0.3), wet))
    furrows(pn, 1060, t, wet)
    adv = (t - T['rain_s']) * lerp(40, 20, wet)
    french_rows(pn, t, lerp(1.0, 0.6, wet), sink=wet * 0.6, x_off=-adv - 70)
    rain(pn, t, eio(P(t, T['soaked'] - 0.1, 0.6)) * (0.5 + 0.5 * P(t, T['night'] - 0.1, 0.4)))
    TINT[0] = (30, 34, 50, int(70 * wet))

# ---------------- 16. the mud slowed them down (close up) ----------------
def sc_mud(base, pn, t):
    bgp(base, 'aginrain', 0.2)
    furrows(pn, 1000, t, 1.0)
    k = 2.9
    lift = [T['mud_s'] + 0.1, T['slowed'] + 0.05, T['down'] + 0.05]
    p = pose('walk', torso=10, head=-4, uaF=30, faF=50, uaB=-30, faB=-10)
    for i, s0 in enumerate(lift):
        u = P(t, s0, 0.45)
        if 0 < u < 1:
            amt = math.sin(math.pi * u)
            if i % 2 == 0: p = dict(p, thF=lerp(p['thF'], 40, amt), shF=lerp(p['shF'], -40, amt))
            else: p = dict(p, thB=lerp(p['thB'], 30, amt), shB=lerp(p['shB'], -50, amt))
    ex = 'exhausted' if t < T['slowed'] else ('worried' if t < T['down'] else 'fear')
    figure(pn, 520, 1345, k, -1, p, 'french1', ex, look=(-0.4, 0.5), blink=blink_at(t, 3), shadow=False)
    mud_band(pn, 1262, t)
    for i, s0 in enumerate(lift):
        particles(pn, 'debris', 520 + (-60 if i % 2 == 0 else 60), 1268, t, s0 + 0.18, 1.0, seed=70 + i, cone=math.pi * 0.6, ground=1280, col=lb.MUD_D)
        particles(pn, 'splash', 520 + (-60 if i % 2 == 0 else 60), 1268, t, s0 + 0.2, 0.7, seed=73 + i, cone=math.pi * 0.6, col=(150, 132, 104))
    rain(pn, t, 0.8, seed=5)
    TINT[0] = (30, 34, 50, 60)

# ---------------- 17. and the arrows kept coming ----------------
def volley_arrows(pn, t, t0, n, seed, x0r, x1r, ytop):
    rnd = random.Random(seed)
    for i in range(n):
        lx = rnd.uniform(*x0r); ly = rnd.uniform(1180, 1230)
        tx = rnd.uniform(*x1r); ty = rnd.uniform(1150, 1290)
        d = FLIGHT * rnd.uniform(0.9, 1.08); s0 = t0 + rnd.uniform(0, 0.08)
        u = (t - s0) / d
        if u < 0: continue
        if u >= 1:
            stuck_arrow(pn, tx, ty, math.radians(rnd.uniform(55, 75)), ARROW_L * 0.32, 0.55)
            continue
        h = ytop + rnd.uniform(-40, 40)
        x = lerp(lx, tx, u); y = lerp(ly, ty, u) - 4 * (min(ly, ty) - h) * u * (1 - u)
        dx = tx - lx; dy = (ty - ly) - 4 * (min(ly, ty) - h) * (1 - 2 * u)
        ang = math.atan2(dy, dx)
        L = ARROW_L * 0.5
        arrow(pn, (x - math.cos(ang) * L, y - math.sin(ang) * L), ang, L - 4, w=2.6)

def sc_volley(base, pn, t):
    bgp(base, 'aginrain', 0.3)
    furrows(pn, 1060, t, 1.0)
    # English archers at the left, the French line at the right
    for i in range(5):
        x = 110 + i * 64; y = 1250 + (i % 2) * 40
        cyc = [v for v in VOLLEYS if v <= t + 0.6]
        nxt = min([v for v in VOLLEYS if v > t - 0.0] + [99])
        last = max([v for v in VOLLEYS if v <= t] + [-9])
        rel = t - last if 0 <= t - last < 0.25 else None
        d = clamp(1 - (nxt - t) / 0.35) if rel is None else 1.0
        archer(pn, x, y, 0.5, 1, d, t, out=('archer', 'archer2', 'archer3')[i % 3], expr='determined', look=(1, -0.5), rel=rel, blink=0,
               p=pose('idle', torso=-6, head=-8), aim=0.62)
    hit = P(t, VOLLEYS[0] + FLIGHT, 0.3)
    for i in range(6):
        x = 640 + i * 75; y = 1230 + (i % 2) * 50
        p = mix(walk_pose(t + i, 7, 10), 'cower', eoback(hit)) if hit > 0 else walk_pose(t + i, 7, 10)
        figure(pn, x, y, 0.5, -1, p, ('french1', 'french2', 'french3')[i % 3], 'terrified' if hit > 0 else 'determined', look=(-0.6, -0.8), blink=0)
    for j, v in enumerate(VOLLEYS):
        volley_arrows(pn, t, v, 14, 80 + j, (130, 400), (620, 1000), 470 - j * 30)
        th = v + FLIGHT
        for k_ in range(3):
            xx = 680 + k_ * 140 + j * 20
            particles(pn, 'sparks', xx, 1150, t, th + k_ * 0.03, 0.5, seed=90 + j * 3 + k_, cone=math.pi * 1.2)
        impact(pn, 800 + j * 40, 1140, t, th, 0.45 if j < 3 else 0.8, seed=95 + j)
        particles(pn, 'debris', 820, 1260, t, th, 0.6, seed=99 + j, ground=1300, col=lb.MUD_D)
    focus_lines(pn, 840, 1150, t, VOLLEYS[3] + FLIGHT, 0.25)
    rain(pn, t, 0.6, seed=7)

def cam_volley(t, sc, ox, oy):
    return camfocus(lerp(1.12, 1.18, eio(P(t, T['vol_s'], 1.8))) * sc, 560, 1060, CX, 980, ox, oy)

# ---------------- 18. every one of those arrows ----------------
FOCUS_ARROW = (540, 1150)
def sc_arrows(base, pn, t):
    bgp(base, 'aginrain', 0.2)
    furrows(pn, 1000, t, 1.0)
    rnd = random.Random(12)
    pts = []
    for i in range(60):
        x = rnd.uniform(-40, 1120); y = rnd.uniform(1030, 1700)
        pts.append((y, x, rnd.uniform(50, 75), rnd.uniform(0.5, 1.1)))
    for y, x, a, s in sorted(pts):
        if abs(x - FOCUS_ARROW[0]) < 120 and abs(y - FOCUS_ARROW[1]) < 160: continue
        s2 = 0.55 + (y - 1000) / 420
        stuck_arrow(pn, x, y, math.radians(a), ARROW_L * 0.8, s2)
    # the arrow we follow
    stuck_arrow(pn, FOCUS_ARROW[0] + 30, FOCUS_ARROW[1] + 60, math.radians(64), ARROW_L * 0.85, 1.25)
    rain(pn, t, 0.5, seed=9)
    TINT[0] = (30, 34, 50, 50)

def cam_arrows(t, sc, ox, oy):
    m = eio(P(t, T['fin_s'], T['began'] - T['fin_s']))
    return camfocus(lerp(1.05, 1.8, m) * sc, FOCUS_ARROW[0], FOCUS_ARROW[1], CX, lerp(1050, 900, m), ox, oy)

# ---------------- 19. final: began with a pull of around 150 pounds ----------------
def sc_final(base, pn, t):
    hook_frame(base, pn, t, T['pull19'] - 0.1, T['n150b'] - 0.05, t_pain=T['n150b'] - 0.05)

def cam_final(t, sc, ox, oy):
    return camfocus(1.32 * sc * (1 + 0.05 * eio(P(t, T['pull19'] - 0.2, 1.4))), 480, 1080, CX, 930, ox, oy)

# (start, fn, cam, transition)
SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['of0'], sc_lift, cam_lift, None),
    (T['wt'], sc_weight, None, 'dissolve'),
    (T['lbs'], sc_bow, cam_bow, 'dissolve'),
    (T['bowyer_s'], sc_bowyer, cam_bowyer, 'slide'),     # chapter: how it was made
    (T['so4'], sc_layers, None, None),
    (T['bend_s'], sc_bend, cam_bend, None),
    (T['spr_s'], sc_spring, cam_spring, None),
    (T['train_s'], sc_train, cam_train, 'slide'),             # chapter: who could draw it
    (T['law_s'], sc_law, None, None),
    (T['bones_s'], sc_bones, cam_bones, None),
    (T['map_s'], sc_map, None, 'slide'),                 # chapter: Agincourt
    (T['ratio_s'], sc_ratio, cam_ratio, None),
    (T['fr_s'], sc_french, cam_french, None),
    (T['rain_s'], sc_rainfield, cam_rain, None),
    (T['mud_s'], sc_mud, None, None),
    (T['vol_s'], sc_volley, cam_volley, None),
    (T['fin_s'], sc_arrows, cam_arrows, 'slide'),        # chapter: back to the bow
    (T['began'], sc_final, cam_final, 'dissolve'),
]
def hud_bones(pn, t):
    tag(pn, 540, 250, 'MARY ROSE CREW', 60, pop(t, T['later']), rot_=-3, sub='THE SHIP SANK IN 1545')

HUD = {sc_ratio: hud_ratio, sc_bones: hud_bones}
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
    if TINT[0] and TINT[0][3] > 0: base.alpha_composite(Image.new('RGBA', (W, H), TINT[0]))
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
    C = [(0.0, 'whooshlow', 0.35), (T['pull0'], 'creak', 0.9), (T['pull0'] + 0.5, 'creak', 0.6), (T['force'], 'thud', 0.6),
         (T['of0'], 'ratchetrun', 0.5), (T['lifting'], 'creak', 0.7), (T['grown'], 'cloth', 0.5), (T['man'], 'pop', 0.3)]
    for i in range(5): C.append((T['around1'] - 0.15 + i * 0.12, 'clank', 0.5))
    C += [(T['n150'] - 0.06, 'stamp', 1.0), (T['pounds1'], 'pop', 0.5),
          (T['english2'] - 0.15, 'whooshlow', 0.5), (T['longbow'], 'shimmer', 0.4), (T['about3'] - 0.1, 'slide', 0.5), (T['feet'], 'pop', 0.5),
          (T['yew'] - 0.08, 'chime', 0.4),
          (T['bowyer_s'] + 0.1, 'cloth', 0.4), (T['strike'], 'knock', 1.0), (T['strike'] + 0.01, 'crack', 0.9), (T['stave'], 'scrape', 0.3),
          (T['so4'] + 0.05, 'pop', 0.4), (T['sapwood4'], 'pop', 0.4), (T['target'] - 0.1, 'whooshlow', 0.4), (T['heartwood5'], 'pop', 0.4),
          (T['archer5'] - 0.05, 'chime', 0.3),
          (T['bend_s'], 'creak', 0.7), (T['stretching'], 'pop', 0.5), (T['stretching'] + 0.05, 'stretch', 0.5), (T['crushing'], 'pop', 0.5),
          (T['crushing'] + 0.05, 'squeeze', 0.5),
          (T['spr_s'], 'creak', 0.8), (T['release'], 'twang', 1.0), (T['release'] + 0.02, 'whiz', 0.8), (T['thunk'], 'thunk', 1.0),
          (T['draw9'] - 0.15, 'creak', 0.5), (T['weight'], 'cloth', 0.4)]
    for i in range(3): C.append((T['years'] - 0.05 + i * 0.27, 'pop', 0.5 + 0.1 * i))
    C += [(T['training'] - 0.1, 'creak', 0.6), (T['training'] + 0.45, 'chime', 0.3),
          (T['law'] - 0.2, 'paper', 0.6), (T['ordered'] - 0.05, 'thud', 0.5), (T['men10'], 'pop', 0.5),
          (T['archery'], 'twang', 0.7), (T['archery'] + 0.3, 'thunk', 0.7), (T['holidays'] - 0.05, 'twang', 0.6), (T['holidays'] + 0.25, 'thunk', 0.6),
          (T['holidays'] - 0.1, 'bell', 0.5),
          (T['bones_s'] - 0.05, 'clack', 0.6), (T['later'], 'pop', 0.5), (T['heavier'] - 0.05, 'riser', 0.4), (T['bones'], 'pop', 0.6),
          (T['drawing'] - 0.1, 'clack', 0.5),
          (T['map_s'] + 0.05, 'paper', 0.5), (T['d25'] - 0.1, 'whooshlow', 0.5), (T['agincourt'] - 0.12, 'thud', 0.7), (T['agincourt'] + 0.3, 'pop', 0.5)]
    for c in range(4): C.append((T['four'] - 0.1 + c * 0.08, 'tick', 0.4))
    C += [(T['five'], 'pop', 0.4), (T['henry'], 'cloth', 0.4), (T['men14'], 'pop', 0.5), (T['archers14'] - 0.1, 'chime', 0.3),
          (T['fr_s'], 'march', 0.8), (T['knights'], 'clank', 0.4), (T['foot'] - 0.02, 'thud', 0.6), (T['foot'], 'march', 0.6),
          (T['rain_s'], 'march', 0.5), (T['soaked'] - 0.1, 'rain', 0.8), (T['night'], 'rumble', 0.5),
          (T['mud_s'], 'rain', 0.6)]
    for i, s0 in enumerate((T['mud_s'] + 0.1, T['slowed'] + 0.05, T['down'] + 0.05)): C.append((s0 + 0.18, 'squelch', 0.8))
    C += [(T['vol_s'] - 0.12, 'rain', 0.5)]
    for v in VOLLEYS:
        C += [(v, 'twang', 0.6), (v + 0.05, 'volley', 0.8), (v + FLIGHT, 'clatter', 0.7)]
    C += [(VOLLEYS[3] + FLIGHT, 'hit', 0.8),
          (T['fin_s'], 'rain', 0.5), (T['arrows19'], 'shimmer', 0.4), (T['began'] - 0.05, 'whooshlow', 0.4),
          (T['pull19'] - 0.1, 'creak', 0.9), (T['n150b'] - 0.05, 'thud', 0.8), (T['pounds19'], 'creak', 0.4)]
    starts = {round(st, 3) for st, _, _, org in SCENES[1:]}
    C = [((c[0] - 0.12) if (round(c[0], 3) in starts and c[1] != 'whoosh') else c[0], c[1], c[2]) for c in C]
    for st, _, _, org in SCENES[1:]:
        if org == 'slide': C.append((st, 'whoosh', 0.35))
    C = sorted(set(C))
    json.dump(dict(cues=C, T=T, dur=DUR, nf=NF, volleys=VOLLEYS, flight=FLIGHT), open('cues.json', 'w'), indent=1)
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

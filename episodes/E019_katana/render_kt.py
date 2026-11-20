"""E019 katana: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import props as PR
from props import (tag, stamp, callout, arrow as arrow_line, katana, katana_section, quench_trough, steam, forge_hearth,
                   tongs, hera, K_NAG, K_TANG, K_SORI, CM)
import kt
from kt import smith_tongs, arm_in, env_forge, shimenawa
import env as E
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

T = dict(
    curve0=w(0, 1), sword0=w(0, 5), made=w(0, 8), tub0=w(0, 11), water0=w(0, 13),
    s1=S(1), moment=w(1, 2), blade1=w(1, 4), slightly=w(1, 7), curved=w(1, 8),
    s2=S(2), paints=w(2, 2), clay2=w(2, 5),
    s3=S(3), thick=w(3, 0), spine3=w(3, 3),
    s4=S(4), thin=w(4, 0), edge4=w(4, 3),
    s5=S(5), heats=w(5, 2), around=w(5, 5), f1500=w(5, 6), fahr=w(5, 8),
    s6=S(6), plunges=w(6, 1), water6=w(6, 4),
    s7=S(7), bare=w(7, 1), cools7=w(7, 3), instant=w(7, 6),
    s8=S(8), turns=w(8, 1), mart=w(8, 3),
    s9=S(9), steel=w(9, 0), hard9=w(9, 3), glass=w(9, 5),
    s10=S(10), changes=w(10, 2), swells=w(10, 4),
    s11=S(11), spine11=w(11, 1), clay11=w(11, 4),
    s12=S(12), slowly=w(12, 1), softer=w(12, 4),
    s13=S(13), first=w(13, 2), dips=w(13, 6), wrong=w(13, 8), way=w(13, 9),
    s14=S(14), swelling=w(14, 2), wins=w(14, 4),
    s15=S(15), pushes=w(15, 1), whole=w(15, 3), arc=w(15, 7),
    s16=S(16), outside=w(16, 3),
    s17=S(17), polishing=w(17, 1),
    s18=S(18), line=w(18, 1), hard18=w(18, 3), soft=w(18, 5),
    s19=S(19), pale=w(19, 3), wave=w(19, 4),
    s20=S(20), hamon=w(20, 1),
    s21=S(21), quench21=w(21, 1), hard21=w(21, 6), edge21=w(21, 7),
    s22=S(22), tough=w(22, 1), spine22=w(22, 2), shape=w(22, 5),
    s23=S(23), came=w(23, 3), tub23=w(23, 7), water23=w(23, 9),
    end=VO_END,
)
CAM.drift = 0.5
GY = 1300
FLOOR_C = (206, 190, 158)
SORI0 = 0.35 * K_SORI          # forged: a slight curve only

# ---------------- 0 and 9. the forge: the plunge and the lift ----------------
SMX, SMK = 250, 2.3
TRX = SMX + 480
def forge_room(base, pn, t, cap=70):
    bgp(base, env_forge(), 0.3)
    shimenawa(pn, 330, t)
    pn.rect(-400, GY, 1480, 2800, fill=(84, 66, 50))
    pn.line([(-400, GY), (1480, GY)], (50, 38, 28), 4, caps=False)

def quench_shot(base, pn, t, t_in, t_lift, sori_of_t, steam_t, heat0=1.0, end_hold=False):
    """The Keeper plunges the glowing, clay coated blade into the trough at t_in and lifts it out curved at t_lift."""
    forge_room(base, pn, t)
    pl = eio(P(t, t_in - 0.5, 0.5)) if t_in is not None else 1.0
    lf = eio(P(t, t_lift, 0.6)) if t_lift is not None else 0.0
    in_water = t >= (t_in if t_in is not None else -9) and lf < 0.6
    heat = heat0 * (1 - P(t, t_in if t_in is not None else -9, 0.25)) if heat0 else 0.0
    sori = sori_of_t(t)
    quench_trough(pn, TRX, GY, SMK, front=False)
    expr = 'determined' if lf < 0.5 else 'smug'
    smith_tongs(pn, SMX, GY, SMK, 1, pl, 'kkeeper', expr, sori=sori, heat=heat, clay=1.0, hard=0.0 if heat > 0.2 else 1.0,
                look=(0.8, 0.5), blink=blink_at(t, 1), lift=lf, wet=lf)
    quench_trough(pn, TRX, GY, SMK, front=True, ripple=clamp(1 - (t - (t_in or 0)) * 0.8) if in_water else 0.0, t=t)
    if steam_t is not None:
        steam(pn, TRX + 60, GY - 70 * SMK, t, steam_t, 1.05, 320, seed=3)
    if lf > 0.6:
        steam(pn, TRX - 40, GY - 150 * SMK, t, t_lift + 0.4, 0.6, 220, seed=9)
    cap_shade(pn, 60)

def sori_hook(t):
    # under water: dips, then curves; already curved by the lift
    u = P(t, 0.15, 1.6)
    if u < 0.3: return lerp(SORI0, -0.6 * K_SORI, eio(u / 0.3))
    return lerp(-0.6 * K_SORI, K_SORI, eio((u - 0.3) / 0.7))
def sc_hook(base, pn, t):
    quench_shot(base, pn, t, 0.0, T['made'] - 0.2, sori_hook, -0.35)
    if t > T['made'] + 0.5:
        # the straight line it started as, against the curve it came out with
        a = P(t, T['tub0'] - 0.3, 0.5)
        tag(pn, 560, 420, 'MOSTLY FROM THE QUENCH', 40, pop(t, T['water0'] - 0.05), rot_=3, sub='NOT THE HAMMER')
def cam_hook(t, sc, ox, oy):
    z = keys(t, [(0.0, 1.25, None), (0.4, 1.12, eio), (T['made'], 1.08, eio), (T['tub0'], 1.14, eio)])
    return camfocus(z * sc, 560, GY - 260, 540, 900, ox, oy)

def sc_end(base, pn, t):
    quench_shot(base, pn, t, T['s23'] - 0.6, T['came'] - 0.1, lambda t: K_SORI, T['s23'] - 0.6, heat0=1.0)
def cam_end(t, sc, ox, oy):
    z = keys(t, [(T['s23'], 1.08, None), (T['tub23'], 1.16, eio), (DUR, 1.2, eio)])
    return camfocus(z * sc, 560, GY - 260, 540, 900, ox, oy)

# ---------------- 1. before that moment: only slightly curved ----------------
BX, BY, BK = 210, 930, 6.6
def bench(pn, y):
    pn.rect(-300, y, 1380, y + 70, fill=WOOD, outline=INK, width=4)
    pn.rect(-300, y + 70, 1380, 2800, fill=(70, 54, 42))
    for i in range(6):
        pn.line([(-300, y + 14 + i * 10), (1380, y + 16 + i * 10)], light(WOOD, 0.15), 1.4, caps=False)

def sc_slight(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    bench(pn, 960)
    sl = pop(t, T['s1'] - 0.05)
    R = katana(pn, BX, BY, BK, 0.0, 1, sori=SORI0)
    # straightedge from the tang notch to the tip, then the gap the slight curve leaves
    a = P(t, T['blade1'] - 0.1, 0.5)
    if a > 0:
        p0 = R['machi']; p1 = R['tip']
        pn.line([p0, (lerp(p0[0], p1[0], eo3(a)), lerp(p0[1], p1[1], eo3(a)))], RUST, 5)
    g = P(t, T['slightly'] - 0.1, 0.4)
    if g > 0:
        mid = R['spine_mid']; chord_y = lerp(R['machi'][1], R['tip'][1], 0.5) - K_WB_half()
        dim(pn, chord_y - 2, mid[1], 640, 'SLIGHT', g, RUST, 36, vertical=True)
    tag(pn, 470, 720, 'FORGED: ABOUT 70 CM', 40, pop(t, T['moment'] + 0.05), rot_=-3, sub='BLADE LENGTH')
    cap_shade(pn, 40)
def K_WB_half(): return PR.K_WB * BK / 2
def cam_slight(t, sc, ox, oy):
    z = keys(t, [(T['s1'], 1.25, None), (T['slightly'], 1.4, eio)])
    return camfocus(z * sc, 560, 900, 540, 860, ox, oy)

# ---------------- 2. the clay: painted on, thick on the spine, thin on the edge ----------------
def sc_clay(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    bench(pn, 960)
    cx = eio(P(t, T['paints'] - 0.2, T['thick'] - T['paints'] - 0.1))
    R = katana(pn, BX, BY, BK, 0.0, 1, sori=SORI0, clay=1.0, clay_x=max(0.02, cx))
    # the spatula rides along the spine side, the forearm comes in from the bottom right
    hx = BX + K_NAG * BK * cx; hy = BY - 6 + 3 * math.sin(t * 9)
    hera(pn, hx, hy, -0.25, 2.2)
    hand = (hx + 72 * 2.2 * math.cos(-0.25), hy + 72 * 2.2 * math.sin(-0.25))
    arm_in(pn, (hand[0] + 800, hand[1] + 880), hand, w=58)
    cap_shade(pn, 40)
def cam_clay(t, sc, ox, oy):
    z = keys(t, [(T['s2'], 1.12, None), (T['clay2'], 1.18, eio)])
    return camfocus(z * sc, 600, 930, 540, 860, ox, oy)

SEC_X, SEC_Y, SEC_S = 560, 800, 19.0
def sc_section(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    floor(pn, 1300)
    cl = eio(P(t, T['s3'] - 0.1, 0.5))
    R = katana_section(pn, SEC_X, SEC_Y, SEC_S, clay=cl)
    H_ = R['H']
    a1 = P(t, T['thick'] - 0.05, 0.4)
    callout(pn, SEC_X + 70, SEC_Y - H_ / 2 - 30, 860, 420, 'THICK', a1, 46, hl=True)
    callout(pn, SEC_X + 10, SEC_Y + H_ / 2 + 8, 860, 1130, 'THIN', P(t, T['thin'] - 0.05, 0.4), 46, hl=True)
    pn.text(SEC_X, SEC_Y - H_ / 2 - 120, 'SPINE', 34, MUTED, 'Black', 'mm', True)
    pn.text(SEC_X, SEC_Y + H_ / 2 + 90, 'EDGE', 34, MUTED, 'Black', 'mm', True)
    pn.text(SEC_X - 300, 1240, 'CROSS SECTION, ENLARGED', 24, MUTED, 'Bold', 'mm', sp=3)
    cap_shade(pn, 30)
def cam_section(t, sc, ox, oy):
    z = keys(t, [(T['s3'], 1.0, None), (T['thin'], 1.08, eio)])
    return camfocus(z * sc, SEC_X, SEC_Y, 540, 860, ox, oy)

# ---------------- 3. heated to about 1,500 F, then plunged ----------------
def sc_heat(base, pn, t):
    bgp(base, env_forge(), 0.3)
    pn.rect(-400, 1180, 1480, 2800, fill=(84, 66, 50))
    bel = 0.5 + 0.5 * math.sin((t - T['s5']) * 5.2)
    Fh = forge_hearth(pn, 560, 1180, 2.6, glow=1.0, t=t, bellows=bel)
    heat = eio(P(t, T['heats'] - 0.2, T['fahr'] - T['heats'] + 0.2))
    fx_, fy_ = Fh['fire']
    # blade laid through the charcoal, the tongs come in from the left edge holding the tang
    bk = 3.2
    machi = (fx_ - K_NAG * bk * 0.55, fy_ + 4)
    katana(pn, machi[0], machi[1], bk, 0.0, 1, sori=SORI0, clay=1.0, heat=heat)
    tongs(pn, (-80, fy_ - 90), (machi[0] - K_TANG * bk + 24, machi[1] - 2), w=2.4)
    for i in range(3):
        tt0 = t - ((t * 1.7 + i * 0.33) % 1.0)
        particles(pn, 'sparks', fx_ + (i - 1) * 80, fy_ - 30, t, tt0, 0.8, seed=20 + i)
    g = P(t, T['around'] - 0.2, 0.4)
    if g > 0:
        pn.push(540, 650, eoback(g))
        pn.rect(-200, -64, 200, 64, fill=(24, 20, 16, 230), outline=(250, 244, 228), width=4, r=14)
        pn.text(0, -2, 'ABOUT 800 °C', 52, lerpc((255, 120, 40), (255, 214, 120), heat), 'Black', 'mm', True)
        pn.pop()
    tag(pn, 360, 780, 'JUDGED BY COLOUR', 36, pop(t, T['fahr'] + 0.1), rot_=-3, sub='NO THERMOMETER')
    cap_shade(pn, 60)
def cam_heat(t, sc, ox, oy):
    z = keys(t, [(T['s5'], 1.3, None), (T['fahr'], 1.42, eio)])
    return camfocus(z * sc, 500, 1060, 540, 900, ox, oy)

def sc_plunge(base, pn, t):
    quench_shot(base, pn, t, T['plunges'] + 0.15, None, lambda t: SORI0, T['plunges'] + 0.15)
def cam_plunge(t, sc, ox, oy):
    z = keys(t, [(T['s6'], 1.08, None), (T['plunges'] + 0.15, 1.2, eio)])
    return camfocus(z * sc, 560, GY - 260, 540, 900, ox, oy)

# ---------------- 4 and 5. inside the steel: the edge hardens and swells, the spine stays softer ----------------
def water_tank(pn):
    pn.rect(-300, 330, 1380, 1300, fill=(196, 216, 222))
    for i in range(14):
        rnd = random.Random(i)
        pn.line([(-300, 360 + i * 68), (1380, 360 + i * 68 + rnd.uniform(-6, 6))], (180, 204, 212), 3, caps=False)
    pn.line([(-300, 330), (1380, 330)], (110, 150, 170), 6, caps=False)
    pn.text(160, 380, 'IN THE WATER', 30, (90, 120, 140), 'Black', 'mm', True)

def sc_inside(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    water_tank(pn)
    floor(pn, 1300)
    hard = eio(P(t, T['instant'] - 0.3, 0.35))
    sw = eoback(P(t, T['swells'] - 0.1, 0.45)) if t > T['swells'] - 0.1 else 0.0
    spine_hl = win(t, T['spine11'] - 0.05, T['s13'], 0.2, 0.2)
    # heat: the edge drops at once; the clay wrapped body cools slowly over the scene
    body_heat = 1 - 0.85 * P(t, T['s7'], T['softer'] - T['s7'] + 0.5)
    R = katana_section(pn, SEC_X, SEC_Y, SEC_S, clay=1.0, hard=hard, swell=sw, heat=body_heat * 0.9, hl_spine=spine_hl,
                       arrows=sw * (1 - P(t, T['spine11'] - 0.2, 0.2)))
    H_ = R['H']
    # bubbles on the bare edge (instant cooling)
    if t > T['bare'] - 0.2:
        for i in range(10):
            ph = (t * 1.6 + i * 0.1) % 1.0
            pn.circ(SEC_X + (i - 5) * 6 + math.sin(t * 7 + i) * 8, SEC_Y + H_ / 2 - ph * 260, 5 + 6 * ph, outline=(250, 254, 255, int(220 * (1 - ph))), width=2)
    callout(pn, SEC_X + 20, SEC_Y + H_ / 2 - 60, 820, 1180, 'HARD BUT BRITTLE', P(t, T['mart'] - 0.05, 0.4) * (1 - P(t, T['s10'], 0.2)), 34, hl=True)
    # nearly as hard as glass: a glass shard beside it
    g = pop(t, T['glass'] - 0.1) * (1 - P(t, T['s10'], 0.2))
    if g > 0:
        pn.push(200, 1080, g * 1.8)
        pn.poly([(-50, 40), (-10, -60), (40, -30), (60, 40)], fill=(220, 236, 244, 200), outline=INK, width=3)
        pn.line([(-20, -30), (10, 20)], WHITE, 3)
        pn.pop()
        pn.text(330, 1080, '≈', 100, INK + (int(255 * g),), 'Black', 'mm', True)
    tag(pn, 300, 520, 'PEARLITE', 44, pop(t, T['softer'] - 0.05), rot_=-3, sub='SOFTER, TOUGHER STEEL')
    if t >= T['swells'] - 0.05 and t < T['s11']:
        pn.text(SEC_X, SEC_Y + H_ / 2 + 120, 'SWELLS', 50, RUST, 'Black', 'mm', True)
    cap_shade(pn, 30)
def cam_inside(t, sc, ox, oy):
    z = keys(t, [(T['s7'], 1.0, None), (T['instant'], 1.12, eio), (T['s9'], 1.0, eio), (T['swells'], 1.12, eio), (T['s11'], 1.0, eio)])
    return camfocus(z * sc, SEC_X, SEC_Y + 60, 540, 880, ox, oy)

# ---------------- 6. first it dips the wrong way, then the edge wins: an arc, edge outside ----------------
EX = 3.0                         # curve exaggerated three times for the diagram (said on screen)
UX, UY, UK = 240, 820, 5.8
def sori_under(t):
    d = eio(P(t, T['first'] - 0.1, T['way'] - T['first'] + 0.1))
    u = eio(P(t, T['pushes'] - 0.1, T['arc'] - T['pushes'] + 0.2))
    s = lerp(SORI0, -0.5 * K_SORI, d)
    return lerp(s, K_SORI, u) * EX

def sc_under(base, pn, t):
    base.paste(bg_cam(E.get('parch'), 0.2))
    water_tank(pn)
    floor(pn, 1300)
    sr = sori_under(t)
    hl = win(t, T['swelling'] - 0.1, T['s17'], 0.2, 0.3)
    R = katana(pn, UX, UY, UK, 0.0, 1, sori=sr, clay=1.0, hard=1.0, hl_edge=hl * 0.8, wscale=1.8)
    # the straight line it would be, to read the bend against
    p0 = R['machi']; p1 = R['tip']
    for i in range(24):
        u0, u1 = i / 24, (i + 0.5) / 24
        pn.line([(lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0)), (lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1))], MUTED, 3)
    if T['dips'] - 0.1 < t < T['s14']:
        xmark(pn, R['mid'][0], R['mid'][1] - 120, P(t, T['wrong'] - 0.05, 0.3), 26)
        arrow_line(pn, (R['mid'][0], R['mid'][1] + 30), (R['mid'][0], R['mid'][1] - 60), (40, 90, 150), 9, 28, p=P(t, T['dips'] - 0.1, 0.3))
    if t > T['pushes'] - 0.2:
        a = P(t, T['pushes'] - 0.2, 0.3) * (1 - P(t, T['s16'] + 0.3, 0.2))
        for xx in (0.3, 0.5, 0.7):
            px = lerp(p0[0], p1[0], xx)
            arrow_line(pn, (px, R['edge_mid'][1] - 20), (px, R['edge_mid'][1] + 60), RUST, 9, 28, p=eo3(a))
    if t > T['outside'] - 0.1:
        dim(pn, R['spine_mid'][1] - (R['spine_mid'][1] - lerp(p0[1], p1[1], 0.5)) - 10, R['spine_mid'][1], 980, 'SORI', P(t, T['outside'] - 0.05, 0.4), RUST, 34, vertical=True)
        callout(pn, R['edge_mid'][0] + 60, R['edge_mid'][1] + 10, 700, 1180, 'EDGE: OUTSIDE', P(t, T['outside'] - 0.05, 0.4), 38, hl=True)
    if t >= T['arc'] + 0.05:
        stamp(pn, 540, 470, 'PROVEN', t - (T['arc'] + 0.05), 110, rot_=-6)
    pn.text(540, 1250, 'CURVE AND WIDTH EXAGGERATED', 24, MUTED, 'Bold', 'mm', sp=3)
    cap_shade(pn, 30)
def cam_under(t, sc, ox, oy):
    z = keys(t, [(T['s13'], 1.0, None), (T['wrong'], 1.06, eio), (T['s14'], 1.0, eio), (T['arc'], 1.08, eio)])
    return camfocus(z * sc, 540, 860, 540, 860, ox, oy)

def xmark(pn, x, y, p, s=22, col=RUST):
    if p <= 0: return
    e = eoback(p); pn.push(x, y, e)
    for a, b in (((-s, -s), (s, s)), ((-s, s), (s, -s))):
        pn.line([a, b], INK, 13); pn.line([a, b], col, 8)
    pn.pop()

# ---------------- 7 and 8. polished: the hamon; one quench, three results ----------------
PX, PY, PK = 140, 840, 6.0
def sc_polish(base, pn, t):
    base.paste(Image.new('RGB', (W, H), (34, 30, 28)))
    pn.rect(-300, 1060, 1380, 2800, fill=(52, 44, 38))
    for i in range(5): pn.line([(-300, 1080 + i * 14), (1380, 1080 + i * 14)], (60, 50, 44), 2, caps=False)
    for sx in (300, 820):
        pn.rect(sx - 16, PY + 18, sx + 16, 1060, fill=WOOD_D, outline=INK, width=3)
        pn.rect(sx - 40, PY + 10, sx + 40, PY + 26, fill=(150, 40, 36), outline=INK, width=2, r=6)
    px_ = eio(P(t, T['s17'] - 0.1, T['line'] - T['s17'] + 0.1))
    hm = eio(P(t, T['line'] - 0.05, T['wave'] - T['line'] + 0.3))
    R = katana(pn, PX, PY, PK, 0.0, 1, sori=K_SORI, polish=1.0, polish_x=max(0.02, px_), hamon=hm, habaki=True, wscale=1.5)
    # light glint sweeping along the polished steel
    a1 = P(t, T['hard18'] - 0.05, 0.4) * (1 - P(t, T['s21'] - 0.2, 0.2))
    callout(pn, PX + K_NAG * PK * 0.45, PY + 30, 420, 1010, 'HARD', a1, 40, hl=True)
    callout(pn, PX + K_NAG * PK * 0.55, PY + 4, 690, 650, 'SOFT', P(t, T['soft'] - 0.05, 0.4) * (1 - P(t, T['s21'] - 0.2, 0.2)), 40)
    tag(pn, 540, 560, 'TEMPER LINE', 44, pop(t, T['hamon'] - 0.05) * (1 - P(t, T['s21'] - 0.1, 0.15)), rot_=3, sub='VISIBLE ONLY AFTER POLISHING')
    # one quench, three results
    for i, (key, lab) in enumerate((('hard21', 'HARD EDGE'), ('tough', 'TOUGH SPINE'), ('shape', 'ITS SHAPE'))):
        a = pop(t, T[key] - 0.08)
        if a <= 0: continue
        y = 1170 + i * 0
        x = 270 + i * 275
        pn.push(x, 600, a * 0.85)
        pn.rect(-140, -46, 140, 46, fill=(250, 244, 228), outline=INK, width=4, r=12)
        pn.circ(-104, 0, 22, fill=(70, 140, 80), outline=INK, width=3)
        pn.line([(-114, 0), (-106, 9), (-92, -10)], WHITE, 6)
        pn.text(24, 2, lab, 28, INK, 'Black', 'mm', True)
        pn.pop()
    if t > T['tough'] - 0.1:
        pn.poly([R['W'](K_NAG * 0.1, -PR.K_WB * 0.5), R['W'](K_NAG * 0.9, -PR.K_WB * 0.5), R['W'](K_NAG * 0.9, -PR.K_WB * 0.05), R['W'](K_NAG * 0.1, -PR.K_WB * 0.05)],
                fill=(80, 140, 200, int(90 * P(t, T['tough'] - 0.1, 0.3) * (1 - P(t, T['shape'] - 0.1, 0.3)))))
    if t > T['shape'] - 0.1:
        p0 = R['machi']; p1 = R['tip']
        a = P(t, T['shape'] - 0.1, 0.4)
        for i in range(24):
            u0, u1 = i / 24, (i + 0.5) / 24
            pn.line([(lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0) - 4), (lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1) - 4)], AMBER + (int(255 * a),), 3)
    cap_shade(pn, 30)
def cam_polish(t, sc, ox, oy):
    z = keys(t, [(T['s17'], 1.25, None), (T['hamon'], 1.38, eio), (T['s21'], 1.15, eio), (T['shape'], 1.2, eio)])
    return camfocus(z * sc, 560, 800, 540, 860, ox, oy)

SCENES = [
    (0.0, sc_hook, cam_hook, None),
    (T['s1'], sc_slight, cam_slight, None),
    (T['s2'], sc_clay, cam_clay, None),
    (T['s3'], sc_section, cam_section, None),
    (T['s5'], sc_heat, cam_heat, 'slide'),          # chapter: the quench
    (T['s6'], sc_plunge, cam_plunge, None),
    (T['s7'], sc_inside, cam_inside, 'dissolve'),   # into the steel (brightness jump)
    (T['s13'], sc_under, cam_under, 'slide'),       # chapter: the curve forms
    (T['s17'], sc_polish, cam_polish, 'dissolve'),
    (T['s23'] - 0.25, sc_end, cam_end, 'slide'),    # back to the tub
]
HUD = {}
SLIDE = 0.35
DISS = 0.3
CAM.punch = [(T['water0'], 0.05), (T['plunges'] + 0.15, 0.06), (T['instant'], 0.05), (T['swells'], 0.05), (T['arc'] + 0.05, 0.07), (T['hamon'], 0.05)]
CAM.shake = [(T['plunges'] + 0.15, 7, 0.25), (T['arc'] + 0.05, 6, 0.2)]
FLASH = [(T['plunges'] + 0.15, 0.12, (255, 240, 214), 100)]
hud_counter = [None]

def cues():
    C = [(0.0, 'sizzle', 1.0), (0.02, 'splash', 0.7), (0.05, 'hiss', 0.8), (T['made'] - 0.2, 'drip', 0.6), (T['water0'] - 0.05, 'pop', 0.5),
         (T['s1'] + 0.05, 'clank', 0.5), (T['blade1'] - 0.1, 'scrape', 0.4), (T['slightly'] - 0.1, 'pop', 0.4), (T['moment'] + 0.05, 'pop', 0.4),
         (T['paints'] - 0.2, 'smear', 0.7), (T['paints'] + 0.6, 'smear', 0.6), (T['clay2'], 'smear', 0.5),
         (T['thick'] - 0.05, 'pop', 0.5), (T['thin'] - 0.05, 'pop', 0.5),
         (T['s5'], 'fire', 0.8), (T['heats'], 'bellows', 0.6), (T['heats'] + 0.6, 'bellows', 0.6), (T['heats'] + 1.2, 'bellows', 0.6),
         (T['around'] - 0.2, 'pop', 0.5), (T['fahr'] + 0.1, 'pop', 0.4),
         (T['plunges'] + 0.15, 'sizzle', 1.0), (T['plunges'] + 0.15, 'splash', 0.9), (T['plunges'] + 0.17, 'hiss', 0.8),
         (T['bare'] - 0.2, 'bubbles', 0.6), (T['instant'], 'crack', 0.4), (T['mart'] - 0.05, 'pop', 0.4), (T['glass'] - 0.1, 'clink', 0.7),
         (T['swells'] - 0.1, 'squeeze', 0.8), (T['spine11'] - 0.05, 'shimmer', 0.4), (T['softer'] - 0.05, 'pop', 0.5),
         (T['first'] - 0.1, 'creak', 0.7), (T['wrong'] - 0.05, 'pop', 0.5), (T['pushes'] - 0.1, 'stretch', 0.8), (T['arc'] + 0.05, 'stamp', 1.0),
         (T['outside'] - 0.05, 'pop', 0.5),
         (T['s17'], 'whetstone', 0.6), (T['s17'] + 0.5, 'whetstone', 0.5), (T['line'], 'shimmer', 0.6), (T['hamon'] - 0.05, 'chime', 0.5),
         (T['hard21'] - 0.08, 'pop', 0.5), (T['tough'] - 0.08, 'pop', 0.5), (T['shape'] - 0.08, 'pop', 0.6),
         (T['s23'] - 0.6, 'sizzle', 0.9), (T['s23'] - 0.6, 'splash', 0.7), (T['came'] - 0.1, 'drip', 0.6), (T['tub23'], 'hiss', 0.5)]
    starts = {round(st, 3) for st, _, _, org in SCENES[1:]}
    C = [((c[0] - 0.12) if (round(c[0], 3) in starts and c[1] != 'whoosh') else c[0], c[1], c[2]) for c in C]
    for st, _, _, org in SCENES[1:]:
        if org == 'slide': C.append((st, 'whoosh', 0.35))
    C = sorted(set(C))
    json.dump(dict(cues=C, T=T, dur=DUR, nf=NF), open('cues.json', 'w'), indent=1)
    print(len(C), 'cues', 'dur', DUR, 'frames', NF)

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

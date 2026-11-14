"""Skeleton rig, poses, expressions and the medieval wardrobe (E013 Warwolf, 1304)."""
import math
from lib import *

L = dict(head=46, neck=8, torso=70, ua=40, fa=38, th=48, sh=46)
POSES = {
    'idle':    dict(torso=0, head=0, uaF=14, faF=6, uaB=-14, faB=-6, thF=5, shF=0, thB=-5, shB=0),
    'point':   dict(torso=4, head=0, uaF=92, faF=98, uaB=-10, faB=-6, thF=8, shF=0, thB=-6, shB=0),
    'stop':    dict(torso=-4, head=-4, uaF=62, faF=165, uaB=-8, faB=-4, thF=6, shF=0, thB=-6, shB=0),
    'wave':    dict(torso=0, head=0, uaF=150, faF=172, uaB=-10, faB=-6, thF=5, shF=0, thB=-5, shB=0),
    'crank':   dict(torso=18, head=-8, uaF=62, faF=96, uaB=55, faB=90, thF=24, shF=0, thB=-18, shB=-8),
    'hold':    dict(torso=6, head=6, uaF=48, faF=108, uaB=40, faB=100, thF=6, shF=0, thB=-6, shB=0),
    'pull':    dict(torso=-16, head=-6, uaF=40, faF=70, uaB=30, faB=64, thF=26, shF=10, thB=-22, shB=-6),
    'reach':   dict(torso=10, head=4, uaF=78, faF=88, uaB=60, faB=84, thF=10, shF=0, thB=-10, shB=0),
    'cross':   dict(torso=-3, head=-5, uaF=28, faF=-30, uaB=26, faB=-28, thF=4, shF=0, thB=-4, shB=0),
    'cower':   dict(torso=8, head=8, uaF=20, faF=150, uaB=14, faB=150, thF=14, shF=-6, thB=-10, shB=-14),
    'look':    dict(torso=-2, head=-6, uaF=120, faF=210, uaB=-8, faB=-4, thF=5, shF=0, thB=-5, shB=0),
    'walk':    dict(torso=4, head=0, uaF=20, faF=30, uaB=-20, faB=-10, thF=22, shF=4, thB=-20, shB=-30),
    'spear':   dict(torso=0, head=0, uaF=30, faF=80, uaB=-8, faB=-4, thF=5, shF=0, thB=-5, shB=0),
    'cheer':   dict(torso=-4, head=-8, uaF=160, faF=170, uaB=150, faB=165, thF=6, shF=0, thB=-6, shB=0),
}
def mix(a, b, x):
    A, B = POSES[a] if isinstance(a, str) else a, POSES[b] if isinstance(b, str) else b
    return {k: lerp(A[k], B[k], x) for k in A}
def pose(name, **over):
    p = dict(POSES[name]); p.update(over); return p

def d(a, f):  # direction from angle (deg from straight down, forward positive)
    r = math.radians(a); return f * math.sin(r), math.cos(r)

def ik(sx, sy, tx, ty, l1, l2, f, bend=1):
    dx, dy = tx - sx, ty - sy; D = max(1e-3, math.hypot(dx, dy)); D2 = min(D, l1 + l2 - 0.5)
    a = math.atan2(dy, dx)
    c = clamp((l1 * l1 + D2 * D2 - l2 * l2) / (2 * l1 * D2), -1, 1)
    b = math.acos(c) * bend * -f
    ex, ey = sx + l1 * math.cos(a + b), sy + l1 * math.sin(a + b)
    hx, hy = sx + dx / D * D2, sy + dy / D * D2
    return (ex, ey), (hx, hy)

def joints(p, f=1, legs=1.0, hands=None):
    th, sh = L['th'] * legs, L['sh'] * legs
    J = {}
    pel = (0.0, 0.0)
    def chain(o, a1, l1, a2, l2):
        d1 = d(a1, f); k1 = (o[0] + d1[0] * l1, o[1] + d1[1] * l1)
        d2 = d(a2, f); k2 = (k1[0] + d2[0] * l2, k1[1] + d2[1] * l2)
        return k1, k2
    J['kneeF'], J['footF'] = chain(pel, p['thF'], th, p['shF'], sh)
    J['kneeB'], J['footB'] = chain(pel, p['thB'], th, p['shB'], sh)
    low = max(J['footF'][1], J['footB'][1])
    for k in list(J): J[k] = (J[k][0], J[k][1] - low)
    J['pelvis'] = (0.0, -low)
    t = math.radians(p['torso'])
    nx = J['pelvis'][0] + f * math.sin(t) * L['torso']; ny = J['pelvis'][1] - math.cos(t) * L['torso']
    J['neck'] = (nx, ny)
    ht = math.radians(p['torso'] + p['head'])
    J['head'] = (nx + f * math.sin(ht) * (L['neck'] + L['head']), ny - math.cos(ht) * (L['neck'] + L['head']))
    sF = (nx + f * 19, ny + 7); sB = (nx - f * 19, ny + 7)
    J['shF'], J['shB'] = sF, sB
    J['elF'], J['haF'] = chain(sF, p['uaF'], L['ua'], p['faF'], L['fa'])
    J['elB'], J['haB'] = chain(sB, p['uaB'], L['ua'], p['faB'], L['fa'])
    if hands:
        for side in ('F', 'B'):
            if side in hands and hands[side] is not None:
                J['el' + side], J['ha' + side] = ik(*J['sh' + side], *hands[side], L['ua'], L['fa'], f)
    return J

EXPR = {  # brow tilt (deg, + = inner up), brow raise, lid, mouth, eye scale, pupil scale
    'neutral':    (0, 0, 0.0, 'flat', 1.0, 1.0),
    'happy':      (4, 3, 0.0, 'smile', 1.0, 1.0),
    'surprised':  (6, 9, 0.0, 'O', 1.15, 0.85),
    'confused':   ('mix', 3, 0.0, 'wavy', 1.0, 1.0),
    'worried':    (22, 3, 0.0, 'frown', 1.0, 1.0),
    'fear':       (28, 8, 0.0, 'grim', 1.18, 0.7),
    'determined': (-24, -2, 0.15, 'flat', 1.0, 1.0),
    'smug':       ('smug', 1, 0.42, 'smirk', 1.0, 1.0),
    'thinking':   ('mix', 2, 0.1, 'side', 1.0, 1.0),
    'angry':      (-28, -3, 0.2, 'frown', 1.0, 1.0),
}

def face(pn, hx, hy, f, expr='neutral', look=(0.6, 0), blink=0.0, glasses=False, r=36, beard=None):
    bt, br, lid, mouth, es, ps = EXPR[expr]
    ex0 = hx + f * 7
    for i, side in enumerate((-1, 1)):
        ex = ex0 + side * 12.5; ey = hy - 3
        rx, ry = 7.6 * es, 9.6 * es
        pn.ell(ex, ey, rx, ry, fill=WHITE, outline=INK, width=2.6)
        lidv = max(lid, blink)
        px = ex + clamp(look[0] * f, -1, 1) * 3.4; py = ey + look[1] * 3.4 + 1
        pn.circ(px, py, 4.4 * ps, fill=INK)
        if lidv > 0.02:
            yl = ey - ry + 2 * ry * lidv
            pts = [(ex - rx - 1, ey - ry - 2), (ex + rx + 1, ey - ry - 2), (ex + rx + 1, yl), (ex - rx - 1, yl)]
            pn.poly(pts, fill=SKIN)
            pn.line([(ex - rx, yl), (ex + rx, yl)], INK, 2.4)
        # brows
        if bt == 'mix': tilt = 14 if side == 1 else -10; raise_ = br + (5 if side == 1 else 0)
        elif bt == 'smug': tilt = -12 if side == -1 else 4; raise_ = br + (5 if side == 1 else -1)
        else: tilt = bt; raise_ = br
        by = ey - ry - 5 - raise_
        inner = -side  # inner edge is toward nose
        a = math.radians(tilt)
        dx, dy = 8 * math.cos(a), 8 * math.sin(a)
        p0 = (ex - 8, by + (dy if inner == -1 else -dy) * 0.5)
        p1 = (ex + 8, by + (-dy if inner == -1 else dy) * 0.5)
        pn.line([p0, p1], INK, 4.2)
    if glasses:
        for side in (-1, 1):
            pn.circ(ex0 + side * 12.5, hy - 3, 12, outline=INK, width=2.6)
        pn.line([(ex0 - 1.5, hy - 5), (ex0 + 1.5, hy - 5)], INK, 2.6, caps=False)
        pn.line([(ex0 - f * 24, hy - 5), (hx - f * r * 0.92, hy - 9)], INK, 2.4)
    if beard:
        bx = hx + f * 6
        pn.poly([(bx - 20, hy + 26), (bx + 20, hy + 26), (bx + 17, hy + r + 4), (bx + f * 2, hy + r + 16), (bx - 17, hy + r + 4)],
                fill=beard, outline=INK, width=2.4)
    mx, my = hx + f * 8, hy + 17
    if mouth == 'flat': pn.line([(mx - 7, my), (mx + 7, my)], INK, 3.2)
    elif mouth == 'smile': pn.arc(mx, my - 6, 9, 20, 160, INK, 3.2)
    elif mouth == 'frown': pn.arc(mx, my + 7, 8, 200, 340, INK, 3.2)
    elif mouth == 'O': pn.ell(mx, my + 1, 5, 6.5, fill=INK)
    elif mouth == 'grim':
        pn.rect(mx - 9, my - 4, mx + 9, my + 5, fill=WHITE, outline=INK, width=2.4, r=3)
        pn.line([(mx - 9, my + 0.5), (mx + 9, my + 0.5)], INK, 1.8, caps=False)
    elif mouth == 'smirk': pn.line([(mx - 7, my + 1), (mx + 3, my + 1), (mx + 8, my - 3)], INK, 3.2)
    elif mouth == 'wavy': pn.line([(mx - 8, my), (mx - 3, my - 2), (mx + 2, my + 2), (mx + 7, my)], INK, 3)
    elif mouth == 'side': pn.line([(mx - 1, my + 1), (mx + 8, my - 1)], INK, 3.2)

# ---------------- wardrobe ----------------
OUT = {
    'keeper':  dict(tunic=(94, 108, 80), sleeve=(94, 108, 80), hose=(240, 232, 214), boot=(70, 48, 30), hat='pilos', cap=(160, 128, 84), glasses=True, clavi=(190, 150, 70)),
    'byz1':    dict(tunic=(128, 76, 54), sleeve=(128, 76, 54), hose=(240, 232, 214), boot=(70, 48, 30), hat='pilos', cap=(120, 96, 70), clavi=(214, 190, 140)),
    'byz2':    dict(tunic=(78, 92, 116), sleeve=(78, 92, 116), hose=(240, 232, 214), boot=(70, 48, 30), hat=None, hair=(60, 44, 32), clavi=(214, 190, 140)),
    'kalli':   dict(tunic=(206, 192, 158), sleeve=(206, 192, 158), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, hair=(64, 48, 36), cloak=(132, 62, 50), beard=(74, 56, 42)),
    'arab':    dict(tunic=(224, 214, 192), sleeve=(224, 214, 192), hose=(240, 232, 214), boot=(90, 64, 40), hat='turban', cap=(240, 236, 224), beard=(54, 42, 34)),
    'arab2':   dict(tunic=(150, 120, 86), sleeve=(150, 120, 86), hose=(240, 232, 214), boot=(90, 64, 40), hat='turban', cap=(206, 196, 170), beard=(40, 32, 26)),
    'bulgar':  dict(tunic=(124, 84, 52), sleeve=(124, 84, 52), hose=(84, 74, 60), boot=(60, 44, 30), hat='fur', cap=(150, 42, 40), fur=(96, 72, 48), trim=(196, 160, 96), beard=(56, 42, 30)),
    'bulgar2': dict(tunic=(70, 86, 72), sleeve=(70, 86, 72), hose=(84, 74, 60), boot=(60, 44, 30), hat='fur', cap=(40, 70, 110), fur=(120, 92, 60), trim=(196, 160, 96), beard=(80, 60, 40)),
}
EPISODE_OUTFIT = 'keeper'
MAIL = (150, 154, 160); MAIL_D = (108, 112, 120); GOLD = (232, 184, 60)

BONE = (240, 232, 214)
def limb(pn, pts, col, w=6):
    col = BONE if (col is None or col == INK) else col
    pn.line(pts, INK, w + 5.5); pn.line(pts, col, w)

def lion(pn, x, y, s):
    # small heraldic lion passant guardant, simplified
    g = GOLD
    pn.ell(x, y, 9 * s, 4.5 * s, fill=g)
    pn.circ(x + 9 * s, y - 3 * s, 4 * s, fill=g)
    for dx in (-6, -2, 4, 7): pn.line([(x + dx * s, y + 2 * s), (x + dx * s, y + 7 * s)], g, 1.8 * s)
    pn.line([(x - 9 * s, y - 1 * s), (x - 13 * s, y - 7 * s), (x - 10 * s, y - 10 * s)], g, 1.8 * s)

def figure(pn, x, y, k, f=1, p='idle', out='keeper', expr='neutral', look=(0.6, 0), blink=0.0, legs=1.0,
           hands=None, held=None, back=None, arms_front=False, alpha=255, shadow=True):
    if isinstance(p, str): p = POSES[p]
    O = OUT[out]
    pn.push(x, y, k)
    if shadow:
        pn.ell(f * 6, 3, 46, 9, fill=(20, 14, 10, 70))
    J = joints(p, f, legs * (1.18 if out == 'edward' else 1.0), hands)
    if back: back(pn, J)
    if O.get('cloak'):
        nk_, pl_ = J['neck'], J['pelvis']
        pn.poly([(nk_[0] - 20, nk_[1] + 2), (nk_[0] + 20, nk_[1] + 2), (pl_[0] + f * 20, pl_[1] + 58), (pl_[0] - f * 62, pl_[1] + 62)],
                fill=O['cloak'], outline=INK, width=3)
    # legs
    hose = MAIL if O['hose'] == 'mail' else O['hose']
    for s in ('B', 'F'):
        limb(pn, [J['pelvis'], J['knee' + s], J['foot' + s]], hose, 6)
        fx, fy = J['foot' + s]
        pn.ell(fx + f * 6, fy - 3, 11, 6, fill=O['boot'], outline=INK, width=2.6)
    # arms behind clothing
    def arm(s):
        limb(pn, [J['sh' + s], J['el' + s], J['ha' + s]], None, 5.5)
    if not arms_front:
        arm('B'); arm('F')
    # body garment
    t = math.radians(p['torso'])
    ux, uy = f * math.sin(t), -math.cos(t)          # up along torso
    nx_, ny_ = -uy, ux                                # sideways
    nk = J['neck']; pl = J['pelvis']
    hl_ = 58 if O.get('long') else 30
    hem = (pl[0] - ux * hl_, pl[1] - uy * hl_)
    sw, hw = 21, 31 + (6 if O.get('long') else 0)
    body = [(nk[0] + nx_ * sw - ux * 2, nk[1] + ny_ * sw - uy * 2), (nk[0] - nx_ * sw - ux * 2, nk[1] - ny_ * sw - uy * 2),
            (hem[0] - nx_ * hw, hem[1] - ny_ * hw), (hem[0] + nx_ * hw, hem[1] + ny_ * hw)]
    if O.get('mail'):
        pn.poly(body, fill=MAIL, outline=INK, width=3.2)
        sc_ = [(lerp(body[0][0], body[3][0], .06), lerp(body[0][1], body[3][1], .06)),
               (lerp(body[1][0], body[2][0], .06), lerp(body[1][1], body[2][1], .06)),
               (hem[0] - nx_ * (hw - 3) + ux * 4, hem[1] - ny_ * (hw - 3) + uy * 4), (hem[0] + nx_ * (hw - 3) + ux * 4, hem[1] + ny_ * (hw - 3) + uy * 4)]
        pn.poly(sc_, fill=O['tunic'], outline=INK, width=2.6)
        if O.get('lions'):
            for i in range(3):
                c = (lerp(nk[0], pl[0], 0.22 + i * 0.27), lerp(nk[1], pl[1], 0.22 + i * 0.27))
                lion(pn, c[0], c[1], 0.9)
        belt = (lerp(nk[0], pl[0], 0.9), lerp(nk[1], pl[1], 0.9))
        pn.line([(belt[0] - nx_ * 22, belt[1] - ny_ * 22), (belt[0] + nx_ * 22, belt[1] + ny_ * 22)], (70, 46, 30), 5)
    else:
        pn.poly(body, fill=O['tunic'], outline=INK, width=3.2)
        if O.get('quilt'):
            for i in (-2, -1, 0, 1, 2):
                a = (nk[0] + nx_ * i * 7 - ux * 4, nk[1] + ny_ * i * 7 - uy * 4)
                b = (hem[0] + nx_ * i * 10 + ux * 3, hem[1] + ny_ * i * 10 + uy * 3)
                pn.line([a, b], lerpc(O['tunic'], INK, 0.35), 1.8, caps=False)
            for j in (0.33, 0.62):
                a = (lerp(body[0][0], body[3][0], j), lerp(body[0][1], body[3][1], j))
                b = (lerp(body[1][0], body[2][0], j), lerp(body[1][1], body[2][1], j))
                pn.line([a, b], lerpc(O['tunic'], INK, 0.35), 1.8, caps=False)
        if O.get('clavi'):
            for sd in (-1, 1):
                a_ = (nk[0] + nx_ * sd * 9 - ux * 1, nk[1] + ny_ * sd * 9 - uy * 1)
                b_ = (hem[0] + nx_ * sd * 12 + ux * 3, hem[1] + ny_ * sd * 12 + uy * 3)
                pn.line([a_, b_], O['clavi'], 4.5, caps=False)
        if O.get('trim'):
            a_ = (nk[0] + nx_ * 14 - ux * 2, nk[1] + ny_ * 14 - uy * 2); b_ = (hem[0] - nx_ * 22 + ux * 2, hem[1] - ny_ * 22 + uy * 2)
            pn.line([a_, b_], O['trim'], 6, caps=False)
            pn.line([(hem[0] - nx_ * hw, hem[1] - ny_ * hw), (hem[0] + nx_ * hw, hem[1] + ny_ * hw)], O['trim'], 6, caps=False)
        if O.get('apron'):
            ap = [(lerp(body[0][0], body[1][0], .2) + ux * -16, lerp(body[0][1], body[1][1], .2) + uy * -16),
                  (lerp(body[0][0], body[1][0], .8) + ux * -16, lerp(body[0][1], body[1][1], .8) + uy * -16),
                  (lerp(body[3][0], body[2][0], .75) + ux * 4, lerp(body[3][1], body[2][1], .75) + uy * 4),
                  (lerp(body[3][0], body[2][0], .25) + ux * 4, lerp(body[3][1], body[2][1], .25) + uy * 4)]
            pn.poly(ap, fill=O['apron'], outline=INK, width=2.4)
        belt = (lerp(nk[0], pl[0], 0.88), lerp(nk[1], pl[1], 0.88))
        pn.line([(belt[0] - nx_ * 21, belt[1] - ny_ * 21), (belt[0] + nx_ * 21, belt[1] + ny_ * 21)], (70, 46, 30), 4)
    if arms_front:
        arm('B'); arm('F')
    # sleeves on upper arm bones (and full mail sleeves)
    for s in ('B', 'F'):
        if O['sleeve'] == 'mail':
            limb(pn, [J['sh' + s], J['el' + s], J['ha' + s]], MAIL, 13)
        else:
            sh_, el_ = J['sh' + s], J['el' + s]
            limb(pn, [sh_, (lerp(sh_[0], el_[0], 0.42), lerp(sh_[1], el_[1], 0.42))], O['sleeve'], 13)
        hx_, hy_ = J['ha' + s]
        pn.circ(hx_, hy_, 5.2, fill=BONE, outline=INK, width=2.4)
    # head and headwear
    hx, hy = J['head']; r = L['head']
    hat = O['hat']
    if hat == 'crown' or O.get('mail'):
        pn.circ(hx, hy + 2, r + 7, fill=MAIL, outline=INK, width=3.2)
        pn.ell(hx + f * 5, hy + 4, r * 0.8, r * 0.86, fill=SKIN, outline=INK, width=2.6)
    elif hat == 'hood':
        pn.circ(hx, hy + 1, r + 7, fill=O['hood'], outline=INK, width=3.2)
        pn.poly([(hx - 30, hy + 26), (hx + 30, hy + 26), (hx + 40, hy + 50), (hx - 40, hy + 50)], fill=O['hood'], outline=INK, width=3)
        pn.ell(hx + f * 6, hy + 4, r * 0.78, r * 0.84, fill=SKIN, outline=INK, width=2.6)
    else:
        if O.get('hair'):
            pn.circ(hx - f * 3, hy - 3, r + 3, fill=O['hair'], outline=INK, width=3)
        pn.circ(hx, hy, r, fill=SKIN, outline=INK, width=3.4)
        if O.get('hair'):
            pn.poly([(hx - r * .95, hy - 6), (hx - r * .7, hy - r * .78), (hx, hy - r - 3), (hx + r * .7, hy - r * .78), (hx + r * .95, hy - 6),
                     (hx + r * .55, hy - r * .55), (hx - r * .55, hy - r * .55)], fill=O['hair'])
    fk = r / 36
    pn.push(hx, hy + (3 if hat in ('crown', 'hood') else 0), fk)
    face(pn, 0, 0, f, expr, look, blink, O.get('glasses', False), 36, O.get('beard'))
    pn.pop()
    if hat == 'crown':
        cy = hy - r - 2
        pts = [(hx - 26, cy + 10), (hx - 26, cy - 8), (hx - 18, cy + 1), (hx - 9, cy - 13), (hx, cy), (hx + 9, cy - 13),
               (hx + 18, cy + 1), (hx + 26, cy - 8), (hx + 26, cy + 10)]
        pn.poly(pts, fill=GOLD, outline=INK, width=2.6)
        for dx in (-13, 0, 13): pn.circ(hx + dx, cy + 5, 2.6, fill=RUST)
    elif hat == 'coif':
        pn.arc(hx, hy, r + 1, 180, 360, (240, 234, 220), 11)
        pn.arc(hx, hy, r + 6, 186, 354, INK, 2.6)
        pn.line([(hx - r + 2, hy + 4), (hx - r + 6, hy + r - 2)], (240, 234, 220), 5)
    elif hat == 'kettle':
        cy = hy - r * 0.45
        pn.poly([(hx - 30, cy), (hx - 26, cy - 22), (hx - 12, cy - 33), (hx + 12, cy - 33), (hx + 26, cy - 22), (hx + 30, cy)],
                fill=IRON, outline=INK, width=3)
        pn.ell(hx, cy + 1, 50, 8, fill=(124, 128, 136), outline=INK, width=3)
        pn.line([(hx, cy - 33), (hx, cy - 2)], lerpc(IRON, INK, .4), 2.4, caps=False)
    elif hat == 'pilos':
        pn.poly([(hx - r - 2, hy - 8), (hx - r * .8, hy - r * .9), (hx - r * .3, hy - r - 12), (hx + r * .3, hy - r - 12),
                 (hx + r * .8, hy - r * .9), (hx + r + 2, hy - 8)], fill=O['cap'], outline=INK, width=3)
        pn.line([(hx - r - 2, hy - 8), (hx + r + 2, hy - 8)], lerpc(O['cap'], INK, .35), 4)
    elif hat == 'turban':
        c = O['cap']; cd = lerpc(c, INK, .2)
        pn.poly([(hx - f * (r + 2), hy - r * .6), (hx - f * (r + 14), hy + 8), (hx - f * (r + 2), hy + 18)], fill=c, outline=INK, width=2.6)
        pn.ell(hx, hy - r * .8, r + 8, r * .44, fill=c, outline=INK, width=3)
        for i in range(2):
            pn.arc(hx, hy - r * .8 - 30 + i * 9, r + 2, 60, 120, cd, 2.6)
        pn.ell(hx - f * 2, hy - r * 1.08, r * .62, r * .34, fill=c, outline=INK, width=3)
    elif hat == 'fur':
        pn.ell(hx, hy - r * .78, r * .86, r * .82, fill=O['cap'], outline=INK, width=3)
        pn.rect(hx - r - 6, hy - r * .78, hx + r + 6, hy - r * .78 + 24, fill=O['fur'], outline=INK, width=3, r=12)
        for i in range(9):
            xx = hx - r + i * r / 4
            pn.line([(xx, hy - r * .78 + 4), (xx + 4, hy - r * .78 + 18)], lerpc(O['fur'], INK, .3), 2, caps=False)
    if held: held(pn, J)
    pn.pop()
    return J

def blink_at(t, seed=0.0):
    ph = (t + seed * 1.37) % 3.3
    return 1.0 if ph < 0.06 else (0.6 if ph < 0.11 else 0.0)

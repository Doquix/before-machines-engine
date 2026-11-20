"""Skeleton rig, poses, expressions and the medieval wardrobe (E013 Warwolf, 1304)."""
import math, random
from lib import *
from detail import lod, shade, light, rivet, scratches

L = dict(head=46, neck=0, torso=100, ua=38.5, fa=37, th=37, sh=35.5)
SHO = 28; SHO_Y = 21; HIP = 10   # E012 frontal rig: shoulders at the torso edges, hips apart
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
    'brace':   dict(torso=6, head=-2, uaF=70, faF=90, uaB=24, faB=60, thF=22, shF=-4, thB=-18, shB=-12),
    'slash':   dict(torso=10, head=0, uaF=100, faF=96, uaB=10, faB=40, thF=24, shF=0, thB=-20, shB=-10),
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
    J['kneeF'], J['footF'] = chain((f * HIP, 0.0), p['thF'], th, p['shF'], sh)
    J['kneeB'], J['footB'] = chain((-f * HIP, 0.0), p['thB'], th, p['shB'], sh)
    low = max(J['footF'][1], J['footB'][1])
    for k in list(J): J[k] = (J[k][0], J[k][1] - low)
    J['pelvis'] = (0.0, -low)
    t = math.radians(p['torso'])
    nx = J['pelvis'][0] + f * math.sin(t) * L['torso']; ny = J['pelvis'][1] - math.cos(t) * L['torso']
    J['neck'] = (nx, ny)
    ht = math.radians(p['torso'] + p['head'])
    J['head'] = (nx + f * math.sin(ht) * (L['neck'] + L['head']), ny - math.cos(ht) * (L['neck'] + L['head']))
    sF = (nx + f * SHO, ny + SHO_Y); sB = (nx - f * SHO, ny + SHO_Y)
    J['shF'], J['shB'] = sF, sB
    J['elF'], J['haF'] = chain(sF, p['uaF'], L['ua'], p['faF'], L['fa'])
    J['elB'], J['haB'] = chain(sB, p['uaB'], L['ua'], p['faB'], L['fa'])
    if hands:
        for side in ('F', 'B'):
            if side in hands and hands[side] is not None:
                # natural elbows: hang down when there is a choice, otherwise bend outward on their own side
                out_ = f if side == 'F' else -f
                e1, h1 = ik(*J['sh' + side], *hands[side], L['ua'], L['fa'], out_)
                e2, h2 = ik(*J['sh' + side], *hands[side], L['ua'], L['fa'], -out_)
                if abs(e1[1] - e2[1]) > 10:
                    e1, h1 = (e1, h1) if e1[1] > e2[1] else (e2, h2)
                J['el' + side], J['ha' + side] = e1, h1
        # explicit elbow (figure local units): for limbs that point into depth, drawn foreshortened, e.g. the raised
        # draw elbow of an archer at full draw, level with the arrow
        for side in ('F', 'B'):
            if hands.get('el' + side) is not None:
                J['el' + side] = hands['el' + side]
    return J

# ---------------- face: expressions ----------------
# Each expression: brows (tilt deg, + = inner end up, or a named pair), brow raise, lid (0..1), eyes (shape), mouth,
# eye scale, pupil scale, extras, and the bold expression to fall back to when the face is too small to read.
def X(brow=0, raise_=0, lid=0.0, eyes='open', mouth='flat', es=1.0, ps=1.0, extras=(), small=None, look=None):
    return dict(brow=brow, raise_=raise_, lid=lid, eyes=eyes, mouth=mouth, es=es, ps=ps, extras=tuple(extras), small=small, look=look)

EXPR = {
    'dead': X(0, 0, 0.0, 'x', 'wavy'),
    # the original ten
    'neutral':    X(0, 0, 0.0, 'open', 'flat'),
    'happy':      X(4, 3, 0.0, 'open', 'smile'),
    'surprised':  X(6, 9, 0.0, 'open', 'O', 1.15, 0.85),
    'confused':   X('mix', 3, 0.0, 'open', 'wavy'),
    'worried':    X(22, 3, 0.0, 'open', 'frown'),
    'fear':       X(28, 8, 0.0, 'open', 'grim', 1.18, 0.7),
    'determined': X(-24, -2, 0.15, 'open', 'flat'),
    'smug':       X('smug', 1, 0.42, 'open', 'smirk'),
    'thinking':   X('mix', 2, 0.1, 'open', 'side'),
    'angry':      X(-28, -3, 0.2, 'open', 'frown'),
    # E015 additions
    'seasick':    X(20, 2, 0.32, 'open', 'puff', 1.0, 0.8, ('green', 'sweat'), small='worried', look=(0.0, 0.5)),
    'pain':       X(24, 1, 0.0, 'squeeze', 'grit', extras=('sweat', 'stress'), small='fear'),
    'terrified':  X(30, 11, 0.0, 'open', 'scream', 1.28, 0.42, ('sweat', 'lines')),
    'awe':        X(10, 9, 0.0, 'sparkle', 'ooh', 1.16, 1.15, small='surprised', look=(0.0, -0.6)),
    'proud':      X(6, 4, 0.0, 'arc', 'grin', small='happy'),
    'sly':        X('smug', 0, 0.48, 'open', 'sly', 1.0, 0.95, small='smug', look=(1.0, 0.1)),
    'exhausted':  X(14, -1, 0.5, 'open', 'pant', 1.0, 0.9, ('sweat', 'sweat2'), small='worried', look=(0.0, 0.4)),
    'skeptical':  X('skeptic', 1, 0.28, 'open', 'side', small='smug', look=(0.8, 0.0)),
    'disgusted':  X(-18, -2, 0.0, 'squint', 'curl', small='angry'),
    'laughing':   X(10, 6, 0.0, 'arc', 'laugh', extras=('tears_small',)),
    'embarrassed':X(16, 2, 0.1, 'open', 'wobble', 1.0, 0.9, ('blush', 'sweat'), small='worried', look=(0.9, 0.6)),
    'crying':     X(28, 4, 0.0, 'squeeze', 'cry', extras=('tears',), small='worried'),
    'bored':      X(-4, -3, 0.56, 'open', 'flat', 1.0, 0.95, small='neutral', look=(0.9, 0.2)),
}
SMALL_FACE_PX = 58      # head diameter on screen below which subtle expressions fall back to their bold version
EXTRAS_PX = 80          # extras (sweat, tears, blush, lines) only when the head is at least this big

# ---------------- face: facial hair ----------------
# Styles drawn in the channel's own shapes. The mouth always keeps a patch of bare skin (locked rule: the mouth is
# drawn on skin, never on top of the beard), so every expression still reads through any beard.
BEARDS = ('stubble', 'short', 'full', 'long', 'goatee', 'vandyke', 'chinstrap', 'mustache', 'handlebar', 'walrus', 'mutton')

def _jaw(r, a0, a1, rr=None, n=16, dy=0.0):
    rr = rr or r
    return [(math.cos(math.radians(a0 + (a1 - a0) * i / n)) * rr, math.sin(math.radians(a0 + (a1 - a0) * i / n)) * rr + dy) for i in range(n + 1)]

def _mustache(pn, f, col, style='chevron', r=36):
    mx, my = f * 2, 12
    if style == 'handlebar':
        for sd in (-1, 1):
            pts = [(mx, my - 1), (mx + sd * 8, my - 2), (mx + sd * 16, my + 1), (mx + sd * 21, my - 3), (mx + sd * 22, my - 9), (mx + sd * 18, my - 7),
                   (mx + sd * 17, my - 2), (mx + sd * 9, my + 3), (mx, my + 2)]
            pn.poly(pts, fill=col, outline=INK, width=2)
    elif style == 'walrus':
        pn.poly([(mx - 17, my + 6), (mx - 13, my - 4), (mx, my - 5), (mx + 13, my - 4), (mx + 17, my + 6), (mx + 8, my + 3), (mx, my + 4), (mx - 8, my + 3)],
                fill=col, outline=INK, width=2)
    else:   # chevron
        pn.poly([(mx - 13, my + 2), (mx - 9, my - 4), (mx + 9, my - 4), (mx + 13, my + 2), (mx, my + 1)], fill=col, outline=INK, width=2)

def facial_hair(pn, f, style, col, r=36, detail=True, mouth_open=False):
    """Draw facial hair in face local units (head radius r, face centred at 0, 0). Returns the mouth skin patch size."""
    hl = lerpc(col, (255, 248, 230), 0.22); dk = lerpc(col, INK, 0.35)
    patch = (12, 7) if not mouth_open else (14, 12)
    if style == 'stubble':
        rnd = random.Random(5)
        pn.poly(_jaw(r - 1, 8, 172) + [(-r * 0.7, 10), (r * 0.7, 10)][::-1], fill=col + (70,))
        if detail:
            for _ in range(46):
                a = math.radians(rnd.uniform(14, 166)); rr = rnd.uniform(r * 0.5, r * 0.95)
                pn.circ(math.cos(a) * rr, math.sin(a) * rr + 2, 0.9, fill=dk + (150,))
        return None
    if style == 'chinstrap':
        pn.line(_jaw(r - 3, 4, 176), col, 7, caps=True)
        pn.line(_jaw(r - 3, 4, 176), dk, 1.6, caps=False)
        return None
    if style in ('mustache', 'handlebar', 'walrus'):
        _mustache(pn, f, col, {'mustache': 'chevron'}.get(style, style), r)
        return None
    if style == 'goatee' or style == 'vandyke':
        pts = [(f * 2 - 12, 20), (f * 2 + 12, 20), (f * 2 + 11, 31), (f * 2 + 1, 40 + (8 if style == 'vandyke' else 0)), (f * 2 - 9, 31)]
        pn.poly(pts, fill=col, outline=INK, width=2.4)
        if detail: pn.line([(f * 2 - 3, 26), (f * 2 - 1, 36)], hl, 1.6, caps=False)
        _mustache(pn, f, col, 'chevron' if style == 'goatee' else 'handlebar', r)
        return patch
    if style == 'mutton':      # big sideburns joined by a moustache, bare chin
        for sd in (-1, 1):
            pn.poly([(sd * (r - 1), -6), (sd * (r + 1), 8), (sd * (r - 4), 22), (sd * 16, 18), (sd * 14, 10), (sd * (r - 10), 4)], fill=col, outline=INK, width=2.4)
        _mustache(pn, f, col, 'walrus', r)
        return None
    # short, full, long: jaw beard with sideburns up to the ears and a moustache
    ext = {'short': 3, 'full': 9, 'long': 22}[style]
    jaw = _jaw(r + 1, 2, 178, n=20)
    chin = [(p[0], p[1] + ext * max(0.0, math.sin(math.radians(2 + 176 * i / 20))) ** 2) for i, p in enumerate(jaw)]
    if style == 'long':
        mid = len(chin) // 2
        chin[mid] = (chin[mid][0] + f * 2, chin[mid][1] + 8)
    top = [(r - 2, -6), (r * 0.62, 6), (r * 0.25, 9), (-r * 0.25, 9), (-r * 0.62, 6), (-(r - 2), -6)]
    pn.poly([(r, -8)] + chin[1:-1] + [(-r, -8)] + top[::-1], fill=col, outline=INK, width=2.6)
    if detail:
        for i, x in enumerate((-18, -8, 4, 14)):       # strand marks
            pn.line([(x, 24 + ext * 0.3), (x + f * 2, 30 + ext * 0.8)], hl, 1.6, caps=False)
            pn.line([(x + 4, 22 + ext * 0.2), (x + 5, 27 + ext * 0.6)], dk, 1.4, caps=False)
    _mustache(pn, f, col, 'chevron', r)
    return patch

# ---------------- face ----------------
def face(pn, hx, hy, f, expr='neutral', look=(0.6, 0), blink=0.0, glasses=False, r=36, beard=None, beard_style=None, t=0.0):
    E = EXPR.get(expr, EXPR['neutral'])
    head_px = 2 * r * pn.k()
    if head_px < SMALL_FACE_PX and E['small']:
        E = EXPR[E['small']]
    extras_on = head_px >= EXTRAS_PX
    detail = head_px >= 110
    if E['look'] is not None: look = E['look']
    bt, br, lid, es, ps = E['brow'], E['raise_'], E['lid'], E['es'], E['ps']
    eyes, mouth, ext = E['eyes'], E['mouth'], E['extras'] if extras_on else ()
    if 'green' in ext:      # queasy tint under the eyes and on the cheeks
        for side in (-1, 1): pn.ell(hx + f * 2 + side * 15, hy + 9, 9, 6, fill=(126, 176, 96, 80))
        pn.ell(hx + f * 2, hy + 4, 22, 3, fill=(126, 176, 96, 60))
    ex0 = hx + f * 2
    for side in (-1, 1):
        ex = ex0 + side * 12.5; ey = hy - 3
        rx, ry = 7.6 * es, 9.6 * es
        if eyes in ('open', 'sparkle'):
            pn.ell(ex, ey, rx, ry, fill=WHITE, outline=INK, width=2.6)
            px = ex + clamp(look[0] * f, -1, 1) * 3.4; py = ey + look[1] * 3.4 + 1
            pn.circ(px, py, 4.4 * ps, fill=INK)
            if eyes == 'sparkle':
                pn.circ(px - 1.6, py - 1.8, 1.7, fill=WHITE); pn.circ(px + 1.4, py + 1.2, 0.9, fill=WHITE)
            lidv = max(lid, blink)
            if lidv > 0.02:
                yl = ey - ry + 2 * ry * lidv
                pn.poly([(ex - rx - 1, ey - ry - 2), (ex + rx + 1, ey - ry - 2), (ex + rx + 1, yl), (ex - rx - 1, yl)], fill=CUR['skin'])
                pn.line([(ex - rx, yl), (ex + rx, yl)], INK, 2.4)
        elif eyes == 'arc':        # closed happy eyes
            pn.arc(ex, ey + 4, 7, 200, 340, INK, 3.2)
        elif eyes == 'squeeze':    # squeezed shut: > <
            d_ = -side
            pn.line([(ex - d_ * 6, ey - 5), (ex + d_ * 5, ey), (ex - d_ * 6, ey + 5)], INK, 3.0)
        elif eyes == 'x':          # knocked out or dead: crossed eyes
            for a_, b_ in (((-6, -6), (6, 6)), ((-6, 6), (6, -6))):
                pn.line([(ex + a_[0], ey + a_[1]), (ex + b_[0], ey + b_[1])], INK, 3.4)
        elif eyes == 'squint':
            pn.ell(ex, ey + 1, rx, ry * 0.42, fill=WHITE, outline=INK, width=2.6)
            pn.circ(ex + clamp(look[0] * f, -1, 1) * 2.5, ey + 1, 3.2, fill=INK)
        # brows
        if bt == 'mix': tilt = 14 if side == 1 else -10; raise_ = br + (5 if side == 1 else 0)
        elif bt == 'smug': tilt = -12 if side == -1 else 4; raise_ = br + (5 if side == 1 else -1)
        elif bt == 'skeptic': tilt = (-14 if side == -1 else 8); raise_ = br + (9 if side == f else -2)
        else: tilt = bt; raise_ = br
        by = ey - ry - 5 - raise_
        inner = -side
        a = math.radians(tilt)
        dy = 8 * math.sin(a)
        # positive tilt lifts the inner end (toward the nose): worried, sad; negative drops it: angry, determined
        pn.line([(ex - 8, by + (-dy if inner == -1 else dy) * 0.5), (ex + 8, by + (dy if inner == -1 else -dy) * 0.5)], INK, 4.2)
    if glasses:
        for side in (-1, 1):
            pn.circ(ex0 + side * 12.5, hy - 3, 12, outline=INK, width=2.6)
        pn.line([(ex0 - 1.5, hy - 5), (ex0 + 1.5, hy - 5)], INK, 2.6, caps=False)
        pn.line([(ex0 - f * 24, hy - 5), (hx - f * r * 0.92, hy - 9)], INK, 2.4)
    if 'blush' in ext:
        for side in (-1, 1): pn.ell(ex0 + side * 17, hy + 9, 7, 3.6, fill=(236, 120, 110, 140))
    mx, my = hx + f * 2, hy + 17
    big_mouth = mouth in ('scream', 'laugh', 'cry', 'pant', 'ooh')
    if beard:
        style = beard_style or 'short'
        pn.push(hx, hy, 1.0)
        patch = facial_hair(pn, f, style, beard, r, detail, big_mouth)
        pn.pop()
        if patch:      # bare skin around the mouth so the expression still reads
            pn.ell(mx, my + (2 if big_mouth else 0), patch[0], patch[1], fill=CUR['skin'])
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
    elif mouth == 'puff':      # cheeks puffed, lips pressed, about to be sick
        for side in (-1, 1): pn.circ(mx + side * 10, my - 1, 5.5, fill=lerpc(SKIN, (150, 190, 110), 0.35), outline=INK, width=1.6)
        pn.line([(mx - 5, my), (mx - 2, my - 1.5), (mx + 2, my + 1.5), (mx + 5, my)], INK, 3)
    elif mouth == 'grit':
        pn.rect(mx - 10, my - 4, mx + 10, my + 4, fill=WHITE, outline=INK, width=2.4, r=2)
        for xx in (-5, 0, 5): pn.line([(mx + xx, my - 4), (mx + xx, my + 4)], INK, 1.6, caps=False)
        pn.line([(mx - 10, my), (mx + 10, my)], INK, 1.6, caps=False)
    elif mouth == 'scream':
        pn.ell(mx, my + 4, 8, 11, fill=INK)
        pn.rect(mx - 6, my - 6, mx + 6, my - 3, fill=WHITE, r=1)
        pn.ell(mx, my + 10, 4.5, 3.2, fill=(200, 80, 80))
    elif mouth == 'ooh': pn.ell(mx, my + 2, 6, 7.5, fill=INK); pn.ell(mx, my + 5, 3.5, 2.4, fill=(200, 80, 80))
    elif mouth == 'grin':
        pn.poly([(mx - 11, my - 3), (mx + 11, my - 3), (mx + 7, my + 5), (mx - 7, my + 5)], fill=WHITE, outline=INK, width=2.6)
        pn.line([(mx - 9, my + 0.5), (mx + 9, my + 0.5)], INK, 1.4, caps=False)
    elif mouth == 'sly': pn.line([(mx - 9, my + 2), (mx + 2, my + 1), (mx + 9, my - 4)], INK, 3.2); pn.line([(mx + 9, my - 4), (mx + 11, my - 6)], INK, 2)
    elif mouth == 'pant':
        pn.ell(mx, my + 2, 6, 5, fill=INK); pn.ell(mx, my + 4.5, 3.4, 2, fill=(200, 80, 80))
    elif mouth == 'curl':      # one side of the upper lip pulled up
        pn.line([(mx - 9, my + 2), (mx - 2, my + 1), (mx + 4, my - 3), (mx + 9, my - 1)], INK, 3.2)
        pn.line([(mx + 3, my - 3), (mx + 5, my - 7)], INK, 1.8)
    elif mouth == 'laugh':
        pn.poly([(mx - 11, my - 3), (mx + 11, my - 3), (mx + 8, my + 6), (mx, my + 10), (mx - 8, my + 6)], fill=INK)
        pn.rect(mx - 9, my - 3, mx + 9, my, fill=WHITE)
        pn.ell(mx, my + 6, 5, 3, fill=(200, 80, 80))
    elif mouth == 'wobble': pn.line([(mx - 8, my + 1), (mx - 4, my - 1), (mx, my + 1), (mx + 4, my - 1), (mx + 8, my + 1)], INK, 2.8)
    elif mouth == 'cry':
        pn.poly([(mx - 9, my + 5), (mx - 5, my - 2), (mx + 5, my - 2), (mx + 9, my + 5)], fill=INK)
        pn.ell(mx, my + 4, 4, 2, fill=(200, 80, 80))
    # extras
    if 'sweat' in ext: _drop(pn, hx - f * (r - 4), hy - 14)
    if 'sweat2' in ext: _drop(pn, hx + f * (r - 2), hy - 20, 0.8)
    if 'tears' in ext:
        for side in (-1, 1):
            x_ = ex0 + side * 13
            pn.line([(x_, hy + 2), (x_ + side * 1.5, hy + 22)], (150, 200, 240, 220), 4.5)
            _drop(pn, x_ + side * 2, hy + 26 + 3 * math.sin(t * 6 + side), 0.6, (150, 200, 240))
    if 'tears_small' in ext:
        for side in (-1, 1): _drop(pn, ex0 + side * 21, hy - 4, 0.55, (150, 200, 240))
    if 'stress' in ext:      # three short marks beside the head
        bx_, by_ = hx + f * (r + 6), hy - r * 0.7
        for i in range(3):
            a = math.radians(-60 + i * 30) if f > 0 else math.radians(240 - i * 30)
            pn.line([(bx_ + math.cos(a) * 4, by_ + math.sin(a) * 4), (bx_ + math.cos(a) * 12, by_ + math.sin(a) * 12)], INK, 2.6)
    if 'lines' in ext:       # shock lines above the head
        for i, dx in enumerate((-16, 0, 16)):
            pn.line([(hx + dx * 1.2, hy - r - 12 - abs(dx) * 0.2), (hx + dx * 1.5, hy - r - 24 - abs(dx) * 0.3)], INK, 2.8)

def _drop(pn, x, y, s=1.0, col=(170, 214, 240)):
    pn.poly([(x, y - 9 * s), (x + 4.5 * s, y), (x + 3 * s, y + 4 * s), (x, y + 5 * s), (x - 3 * s, y + 4 * s), (x - 4.5 * s, y)], fill=col, outline=INK, width=1.6)
    pn.circ(x - 1.4 * s, y + 0.5 * s, 1.1 * s, fill=WHITE)

# ---------------- wardrobe ----------------
OUT = {
    'keeper':  dict(tunic=(94, 108, 80), sleeve=(94, 108, 80), hose=(240, 232, 214), boot=(70, 48, 30), hat='pilos', cap=(160, 128, 84), glasses=True, clavi=(190, 150, 70)),
    'byz1':    dict(tunic=(128, 76, 54), sleeve=(128, 76, 54), hose=(240, 232, 214), boot=(70, 48, 30), hat='pilos', cap=(120, 96, 70), clavi=(214, 190, 140)),
    'byz2':    dict(tunic=(78, 92, 116), sleeve=(78, 92, 116), hose=(240, 232, 214), boot=(70, 48, 30), hat=None, hair=(60, 44, 32), clavi=(214, 190, 140)),
    'kalli':   dict(tunic=(206, 192, 158), sleeve=(206, 192, 158), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, hair=(64, 48, 36), cloak=(132, 62, 50), beard=(74, 56, 42)),
    'arab':    dict(tunic=(224, 214, 192), sleeve=(224, 214, 192), hose=(240, 232, 214), boot=(90, 64, 40), hat='turban', cap=(240, 236, 224), beard=(54, 42, 34)),
    'arab2':   dict(tunic=(150, 120, 86), sleeve=(150, 120, 86), hose=(240, 232, 214), boot=(90, 64, 40), hat='turban', cap=(206, 196, 170), beard=(40, 32, 26)),
    'bulgar':  dict(tunic=(124, 84, 52), sleeve=(124, 84, 52), hose=(84, 74, 60), boot=(60, 44, 30), hat='fur', cap=(150, 42, 40), fur=(96, 72, 48), trim=(196, 160, 96), beard=(56, 42, 30)),
    # E015 Roman Republic and Carthage, 260 BC
    'legion':  dict(tunic=(150, 58, 44), sleeve=(150, 58, 44), hose=(240, 232, 214), boot=(96, 66, 40), hat='montefortino', cap=(196, 146, 66), plume=(40, 30, 24), pect=True, glasses=True, scutum=(150, 58, 44)),
    'legion2': dict(tunic=(150, 58, 44), sleeve=(150, 58, 44), hose=(240, 232, 214), boot=(96, 66, 40), hat='montefortino', cap=(190, 140, 62), plume=(40, 30, 24), pect=True, scutum=(150, 58, 44)),
    'legion3': dict(tunic=(214, 200, 168), sleeve=(214, 200, 168), hose=(240, 232, 214), boot=(96, 66, 40), hat='montefortino', cap=(184, 136, 60), plume=(120, 40, 34), pect=True, scutum=(140, 56, 42), beard=(70, 52, 38), beard_style='stubble'),
    'rower':   dict(tunic=(206, 192, 158), sleeve=(206, 192, 158), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, hair=(70, 52, 38), beard=(70, 52, 38), beard_style='short'),
    'punic':   dict(tunic=(232, 224, 206), sleeve=(232, 224, 206), hose=(240, 232, 214), boot=(110, 80, 50), hat=None, hair=(40, 30, 24), beard=(44, 34, 26), beard_style='full', clavi=(104, 46, 92)),
    'punic2':  dict(tunic=(104, 46, 92), sleeve=(104, 46, 92), hose=(240, 232, 214), boot=(110, 80, 50), hat='cone', cap=(206, 192, 160), beard=(60, 44, 32), beard_style='long'),
    'bulgar2': dict(tunic=(70, 86, 72), sleeve=(70, 86, 72), hose=(84, 74, 60), boot=(60, 44, 30), hat='fur', cap=(40, 70, 110), fur=(120, 92, 60), trim=(196, 160, 96), beard=(80, 60, 40)),
}
# E016 Agincourt, 1415
OUT.update({
    'archer':  dict(tunic=(222, 214, 192), sleeve=(222, 214, 192), hose=(118, 96, 70), boot=(70, 48, 30), hat='kettle', glasses=True, cross=(190, 40, 36)),
    'archer2': dict(tunic=(146, 112, 74), sleeve=(146, 112, 74), hose=(84, 92, 70), boot=(70, 48, 30), hat='hood', hood=(108, 118, 84), cross=(190, 40, 36),
                    beard=(90, 64, 40), beard_style='stubble'),
    'archer3': dict(tunic=(196, 184, 156), sleeve=(196, 184, 156), hose=(126, 72, 54), boot=(70, 48, 30), hat=None, hair=(150, 104, 56), cross=(190, 40, 36),
                    beard=(150, 104, 56), beard_style='short'),
    'boy':     dict(tunic=(172, 146, 104), sleeve=(172, 146, 104), hose=(120, 100, 74), boot=(70, 48, 30), hat=None, hair=(160, 112, 60)),
    'bowyer':  dict(tunic=(132, 104, 76), sleeve=(132, 104, 76), hose=(98, 86, 66), boot=(70, 48, 30), hat=None, hair=(96, 74, 52), apron=(170, 140, 100),
                    beard=(96, 74, 52), beard_style='full'),
    'villager':dict(tunic=(120, 128, 150), sleeve=(120, 128, 150), hose=(110, 90, 66), boot=(70, 48, 30), hat=None, hair=(70, 52, 38), beard=(70, 52, 38), beard_style='short'),
    'engma':   dict(tunic=(232, 226, 210), sleeve='mail', hose='mail', boot=(110, 114, 122), hat='bascinet', cap=(176, 180, 188), mail=True, cross=(190, 40, 36)),
    'french1': dict(tunic=(52, 74, 140), sleeve='mail', hose='mail', boot=(110, 114, 122), hat='bascinet', cap=(176, 180, 188), mail=True),
    'french2': dict(tunic=(150, 40, 40), sleeve='mail', hose='mail', boot=(110, 114, 122), hat='bascinet', cap=(170, 174, 182), mail=True),
    'french3': dict(tunic=(226, 218, 196), sleeve='mail', hose='mail', boot=(110, 114, 122), hat='bascinet', cap=(176, 180, 188), mail=True),
})
# E017 Macedon and the Greek city states, 4th century BC
_BRZ = (196, 150, 72); _LIN = (234, 226, 204)
OUT.update({
    'phalanx':  dict(tunic=_LIN, sleeve=(150, 54, 42), hose=(240, 232, 214), boot=(110, 80, 50), hat='phrygian', cap=_BRZ,
                     greaves=_BRZ, ptery=(238, 230, 210), skirt=(150, 54, 42), glasses=True),
    'phalanx2': dict(tunic=_LIN, sleeve=(150, 54, 42), hose=(240, 232, 214), boot=(110, 80, 50), hat='phrygian', cap=(188, 142, 66),
                     greaves=_BRZ, ptery=(238, 230, 210), skirt=(150, 54, 42)),
    'phalanx3': dict(tunic=(220, 210, 186), sleeve=(132, 48, 40), hose=(240, 232, 214), boot=(110, 80, 50), hat='phrygian', cap=(200, 156, 80),
                     greaves=_BRZ, ptery=(226, 216, 192), skirt=(132, 48, 40), beard=(80, 60, 42), beard_style='stubble'),
    'hoplite':  dict(tunic=(226, 218, 196), sleeve=(70, 92, 128), hose=(240, 232, 214), boot=(110, 80, 50), hat='pilosb', cap=(186, 144, 70),
                     greaves=_BRZ, ptery=(230, 222, 200), skirt=(70, 92, 128), beard=(62, 46, 34), beard_style='full'),
    'hoplite2': dict(tunic=(214, 204, 178), sleeve=(112, 74, 52), hose=(240, 232, 214), boot=(110, 80, 50), hat='pilosb', cap=(176, 136, 66),
                     greaves=_BRZ, ptery=(220, 210, 186), skirt=(112, 74, 52), beard=(90, 66, 44), beard_style='short', plume=(150, 40, 36)),
})
EPISODE_OUTFIT = 'phalanx'
MAIL = (150, 154, 160); MAIL_D = (108, 112, 120); GOLD = (232, 184, 60)

BONE = (240, 232, 214)
CUR = {'skin': SKIN, 'bone': BONE}   # per figure skin tone (OUT key 'skin'); limbs follow it
LINE_LIMBS = True   # E020 user rule: bare limbs are thin black ink lines (clothing colours keep their fill)
def limb(pn, pts, col, w=6):
    bare = (col is None or col == INK or col == BONE or col == CUR['bone'])
    if bare and LINE_LIMBS:
        pn.line(pts, INK, 4.6); return
    col = CUR['bone'] if bare else col
    pn.line(pts, INK, w + 5.5); pn.line(pts, col, w)

def lion(pn, x, y, s):
    # small heraldic lion passant guardant, simplified
    g = GOLD
    pn.ell(x, y, 9 * s, 4.5 * s, fill=g)
    pn.circ(x + 9 * s, y - 3 * s, 4 * s, fill=g)
    for dx in (-6, -2, 4, 7): pn.line([(x + dx * s, y + 2 * s), (x + dx * s, y + 7 * s)], g, 1.8 * s)
    pn.line([(x - 9 * s, y - 1 * s), (x - 13 * s, y - 7 * s), (x - 10 * s, y - 10 * s)], g, 1.8 * s)

def _ell_pts(cx, cy, rx, ry, a0, a1, n=18):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def scutum(pn, sx, sy, col, f=1, rx=30, ry=58, seed=3):
    """Mid Republican scutum after Polybius 6.23: curved oval board covered in hide, wooden spine, iron rim at the
    top and bottom edges, iron boss. Light from the upper left; the right side turns away into shade."""
    L = lod(pn, 2 * ry)
    pn.ell(sx + f * 5, sy + 6, rx, ry, fill=(20, 14, 10, 60))
    pn.ell(sx, sy, rx, ry, fill=col, outline=INK, width=3.4)
    # curvature: shaded crescent on the right, lit band on the left
    pn.poly(_ell_pts(sx, sy, rx - 2, ry - 2, -80, 80) + _ell_pts(sx + rx * 0.28, sy, rx * 0.55, ry * 0.86, 80, -80), fill=shade(col, 0.3))
    pn.poly(_ell_pts(sx, sy, rx - 3, ry - 3, 115, 245) + _ell_pts(sx - rx * 0.42, sy, rx * 0.4, ry * 0.8, 245, 115), fill=light(col, 0.18))
    if L >= 1:
        # iron edging along the top and bottom rims
        for a0, a1 in ((200, 340), (20, 160)):
            pn.line(_ell_pts(sx, sy, rx - 1, ry - 1, a0, a1, 14), IRON, 4.2, caps=False)
            pn.line(_ell_pts(sx, sy, rx - 3.5, ry - 3.5, a0 + 8, a1 - 8, 12), lerpc(IRON, WHITE, .35), 1.4, caps=False)
        pn.ell(sx, sy, rx - 6, ry - 6, outline=lerpc(col, WHITE, .22), width=1.6)
    # wooden spine with a lit left face
    pn.line([(sx, sy - ry + 7), (sx, sy + ry - 7)], shade(col, 0.4), 5, caps=False)
    pn.line([(sx - 1.6, sy - ry + 8), (sx - 1.6, sy + ry - 8)], light(col, 0.25), 1.6, caps=False)
    # iron boss with rivets
    pn.ell(sx, sy, 11, 15, fill=IRON, outline=INK, width=2.6)
    pn.ell(sx + 2.5, sy + 2, 7, 10, fill=shade(IRON, 0.25))
    pn.ell(sx - 3, sy - 4, 3.2, 5, fill=light(IRON, 0.6))
    if L >= 1:
        for a in (45, 135, 225, 315):
            rivet(pn, sx + math.cos(math.radians(a)) * 9, sy + math.sin(math.radians(a)) * 13, 1.5, IRON)
    if L >= 2:
        scratches(pn, sx - 10, sy - 26, ry, seed)
        scratches(pn, sx + 8, sy + 28, ry, seed + 4, n=2)

def figure(pn, x, y, k, f=1, p='idle', out='keeper', expr='neutral', look=(0.6, 0), blink=0.0, legs=1.0,
           hands=None, held=None, back=None, arms_front=None, alpha=255, shadow=True, grip=None, shield=True,
           mid=None, b_behind=False, b_hide=False, f_behind=False):
    """mid(pn, J): drawn over the clothing and under the front arm (a shield worn on the back arm, a pelta on its strap).
    b_behind: the back arm stays behind the clothing and mid layer (its hand is still drawn on top unless b_hide).
    f_behind: the same for the front arm (a shield worn on the front arm, with the hand reaching out past its rim)."""
    if isinstance(p, str): p = POSES[p]
    O = OUT[out]
    CUR['skin'] = O.get('skin', SKIN); CUR['bone'] = lerpc(BONE, CUR['skin'], 0.85) if O.get('skin') else BONE
    # holding something: arms and hands go in front of the clothing so the grip reads
    if arms_front is None: arms_front = bool(held or hands or grip)
    pn.push(x, y, k)
    if shadow:
        pn.ell(f * 6, 3, 46, 9, fill=(20, 14, 10, 70))
    lk = legs * (1.18 if out == 'edward' else 1.0)
    carry = bool(O.get('scutum') and shield)
    if carry and not (hands and hands.get('B') is not None):
        # the shield hand holds the horizontal grip behind the boss: place it by IK, rest beside the hip,
        # following the pose's own back hand a little so the shield still moves with the action
        J0 = joints(p, f, lk); pe = J0['pelvis']
        Ji = joints(dict(p, uaB=POSES['idle']['uaB'], faB=POSES['idle']['faB']), f, lk)
        gx = pe[0] - f * 58 + 0.45 * (J0['haB'][0] - Ji['haB'][0])
        gy = pe[1] - 23 + 0.45 * (J0['haB'][1] - Ji['haB'][1])
        hands = dict(hands or {}); hands['B'] = (gx, gy)
    J = joints(p, f, lk, hands)
    if back: back(pn, J)
    if O.get('cloak'):
        nk_, pl_ = J['neck'], J['pelvis']
        pn.poly([(nk_[0] - 20, nk_[1] + 2), (nk_[0] + 20, nk_[1] + 2), (pl_[0] + f * 20, pl_[1] + 58), (pl_[0] - f * 62, pl_[1] + 62)],
                fill=O['cloak'], outline=INK, width=3)
    # legs
    hose = MAIL if O['hose'] == 'mail' else O['hose']
    for s in ('B', 'F'):
        hp_ = (J['pelvis'][0] + (f * HIP if s == 'F' else -f * HIP), J['pelvis'][1])
        limb(pn, [hp_, J['knee' + s], J['foot' + s]], hose, 6.5)
        fx, fy = J['foot' + s]
        pn.ell(fx + f * 6, fy - 3, 11, 6, fill=O['boot'], outline=INK, width=2.6)
        if O.get('greaves'):   # bronze greaves sprung over the shin, knee to ankle
            kx, ky = J['knee' + s]; g_ = O['greaves']
            ax_, ay_ = lerp(kx, fx, 0.9), lerp(ky, fy, 0.9)
            pn.line([(kx, ky + 1), (ax_, ay_)], INK, 15)
            pn.line([(kx, ky + 1), (ax_, ay_)], g_, 10)
            pn.line([(kx - 2.2, ky + 4), (lerp(kx, ax_, .8) - 2.2, lerp(ky, ay_, .8))], light(g_, 0.5), 2.4, caps=False)
    # arms behind clothing
    def arm(s):
        limb(pn, [J['sh' + s], J['el' + s], J['ha' + s]], None, 6.5)
    if not arms_front or carry or b_behind:
        arm('B')
        if b_behind and not carry:
            sh_, el_ = J['shB'], J['elB']
            limb(pn, [sh_, (lerp(sh_[0], el_[0], 0.38), lerp(sh_[1], el_[1], 0.38))], O['sleeve'], 12)
    if not arms_front or f_behind:
        arm('F')
        if f_behind:
            sh_, el_ = J['shF'], J['elF']
            limb(pn, [sh_, (lerp(sh_[0], el_[0], 0.38), lerp(sh_[1], el_[1], 0.38))], O['sleeve'], 12)
    # body garment
    t = math.radians(p['torso'])
    ux, uy = f * math.sin(t), -math.cos(t)          # up along torso
    nx_, ny_ = -uy, ux                                # sideways
    nk = J['neck']; pl = J['pelvis']
    hl_ = 24
    hem = (pl[0] - ux * hl_, pl[1] - uy * hl_)
    sw, hw = 25, 35
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
        if O.get('cross'):
            cc = O['cross']; c_ = (lerp(nk[0], pl[0], 0.42), lerp(nk[1], pl[1], 0.42))
            pn.line([(nk[0] - ux * 10, nk[1] - uy * 10), (lerp(nk[0], pl[0], 0.8), lerp(nk[1], pl[1], 0.8))], cc, 8, caps=False)
            pn.line([(c_[0] - nx_ * 17, c_[1] - ny_ * 17), (c_[0] + nx_ * 17, c_[1] + ny_ * 17)], cc, 8, caps=False)
        belt = (lerp(nk[0], pl[0], 0.9), lerp(nk[1], pl[1], 0.9))
        pn.line([(belt[0] - nx_ * 22, belt[1] - ny_ * 22), (belt[0] + nx_ * 22, belt[1] + ny_ * 22)], (70, 46, 30), 5)
    else:
        pn.poly(body, fill=O['tunic'], outline=INK, width=3.2)
        garment_details(pn, O, body, nk, pl, hem, ux, uy, nx_, ny_, hw, f)
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
        if O.get('pect'):
            c_ = (lerp(nk[0], pl[0], 0.3), lerp(nk[1], pl[1], 0.3)); hs = 15
            sq = [(c_[0] + (nx_ * a_ + ux * b_) * hs, c_[1] + (ny_ * a_ + uy * b_) * hs) for a_, b_ in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
            for sd in (-1, 1):
                pn.line([(nk[0] + nx_ * sd * 20, nk[1] + ny_ * sd * 20), (c_[0] + nx_ * sd * 13 + ux * 13, c_[1] + ny_ * sd * 13 + uy * 13)], (90, 60, 36), 3.4)
            pn.poly(sq, fill=(196, 146, 66), outline=INK, width=2.8)
            pn.circ(c_[0], c_[1], 4, fill=(150, 104, 44))
        if O.get('cross'):     # red cross of St George, worn by the English army in France (ordinance of 1385)
            cc = O['cross']; c_ = (lerp(nk[0], pl[0], 0.42), lerp(nk[1], pl[1], 0.42))
            pn.line([(nk[0] - ux * 8, nk[1] - uy * 8), (lerp(nk[0], pl[0], 0.8), lerp(nk[1], pl[1], 0.8))], cc, 8, caps=False)
            pn.line([(c_[0] - nx_ * 19, c_[1] - ny_ * 19), (c_[0] + nx_ * 19, c_[1] + ny_ * 19)], cc, 8, caps=False)
        if O.get('ptery'):     # linothorax: layered linen corselet, shoulder yoke tied down on the chest, pteruges at the hem
            pc = O['ptery']; sk = O.get('skirt', (150, 54, 42))
            pn.poly([(hem[0] - nx_ * (hw + 2), hem[1] - ny_ * (hw + 2)), (hem[0] + nx_ * (hw + 2), hem[1] + ny_ * (hw + 2)),
                     (hem[0] + nx_ * (hw + 4) - ux * 26, hem[1] + ny_ * (hw + 4) - uy * 26), (hem[0] - nx_ * (hw + 4) - ux * 26, hem[1] - ny_ * (hw + 4) - uy * 26)],
                    fill=sk, outline=INK, width=2.6)
            for i in range(7):
                c0 = -hw + 2 + i * (2 * hw - 4) / 6
                a_ = (hem[0] + nx_ * c0 + ux * 4, hem[1] + ny_ * c0 + uy * 4)
                b_ = (hem[0] + nx_ * c0 - ux * 18, hem[1] + ny_ * c0 - uy * 18)
                pn.line([a_, b_], INK, 10, caps=False); pn.line([a_, b_], pc, 6.4, caps=False)
            for sd in (-1, 1):
                a_ = (nk[0] + nx_ * sd * 22 - ux * 3, nk[1] + ny_ * sd * 22 - uy * 3)
                b_ = (lerp(nk[0], pl[0], 0.3) + nx_ * sd * 8, lerp(nk[1], pl[1], 0.3) + ny_ * sd * 8)
                pn.line([a_, b_], INK, 9); pn.line([a_, b_], shade(O['tunic'], 0.1), 5.5)
            pn.line([(lerp(nk[0], pl[0], 0.3) - nx_ * 8, lerp(nk[1], pl[1], 0.3) - ny_ * 8),
                     (lerp(nk[0], pl[0], 0.3) + nx_ * 8, lerp(nk[1], pl[1], 0.3) + ny_ * 8)], (150, 54, 42), 3)
        belt = (lerp(nk[0], pl[0], 0.88), lerp(nk[1], pl[1], 0.88))
        pn.line([(belt[0] - nx_ * 21, belt[1] - ny_ * 21), (belt[0] + nx_ * 21, belt[1] + ny_ * 21)], (70, 46, 30), 4)
    if carry:
        # Republican scutum on its grip: the fist is behind the boss, the forearm behind the board, the sleeve cap
        # and upper arm show above the rim, the rim clears the shoulder at the top and the knees at the bottom
        sh_, el_ = J['shB'], J['elB']
        limb(pn, [sh_, (lerp(sh_[0], el_[0], 0.38), lerp(sh_[1], el_[1], 0.38))], O['sleeve'], 12)
        sx_, sy_ = J['haB']
        scutum(pn, sx_, sy_, O['scutum'], f)
    if mid: mid(pn, J)
    if arms_front:
        if held: held(pn, J)          # the prop sits under the hands
        if grip: grip(pn, J)
        if not carry and not b_behind: arm('B')
        if not f_behind: arm('F')
    # sleeves on upper arm bones (and full mail sleeves)
    for s in (('F',) if carry else ('B', 'F')):
        if (s == 'B' and b_behind) or (s == 'F' and f_behind):
            if not b_hide:
                hx_, hy_ = J['ha' + s]; pn.circ(hx_, hy_, 5.2, fill=BONE, outline=INK, width=2.4)
            continue
        if O['sleeve'] == 'mail':
            limb(pn, [J['sh' + s], J['el' + s], J['ha' + s]], MAIL, 13)
        else:
            sh_, el_ = J['sh' + s], J['el' + s]
            limb(pn, [sh_, (lerp(sh_[0], el_[0], 0.38), lerp(sh_[1], el_[1], 0.38))], O['sleeve'], 12)
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
        hair_back(pn, hx, hy, r, f, O)
        if O.get('ears'):
            for sd in (-1, 1):
                pn.ell(hx + sd * (r - 1), hy + 4, 7, 10, fill=CUR['skin'], outline=INK, width=2.6)
                pn.arc(hx + sd * (r - 1), hy + 4, 4, 300 if sd > 0 else 120, 60 if sd > 0 else 240, lerpc(CUR['skin'], INK, .4), 1.6)
        pn.circ(hx, hy, r, fill=CUR['skin'], outline=INK, width=3.4)
        hair_front(pn, hx, hy, r, f, O)
    fk = r / 36
    pn.push(hx, hy + (3 if hat in ('crown', 'hood') else 0), fk)
    features(pn, f, O)
    face(pn, 0, 0, f, expr, look, blink, O.get('glasses', False), 36, O.get('beard'), O.get('beard_style'))
    if O.get('nose'): nose(pn, f, O['nose'])
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
    elif hat == 'montefortino':
        c = O['cap']; cd = lerpc(c, INK, .3); by = hy - 27; HL = lod(pn, 2 * r)
        dome = [(hx - r - 3, by), (hx - r * .9, by - 20), (hx - r * .55, by - 36), (hx, by - 44),
                (hx + r * .55, by - 36), (hx + r * .9, by - 20), (hx + r + 3, by)]
        pn.poly(dome, fill=c, outline=INK, width=3)
        pn.poly([(hx + r * .2, by - 42), (hx + r * .55, by - 36), (hx + r * .9, by - 20), (hx + r + 2, by - 1), (hx + r * .45, by - 1)], fill=shade(c, 0.25))
        pn.poly([(hx - r * .7, by - 22), (hx - r * .42, by - 36), (hx - r * .22, by - 38), (hx - r * .5, by - 18)], fill=light(c, 0.55))
        pn.line([(hx - r - 8, by), (hx + r + 8, by)], cd, 6)
        if HL >= 1:   # cast cable pattern on the rim
            for i in range(13):
                xx = hx - r - 4 + i * (2 * r + 8) / 12
                pn.circ(xx, by - 0.5, 1.7, fill=light(c, 0.35))
        for sd in (-1, 1):   # cheek guards hinge at the brim and sit outside the eyes
            cg = [(hx + sd * (r - 9), by + 2), (hx + sd * (r + 3), by + 2), (hx + sd * (r + 1), hy + 20), (hx + sd * (r - 7), hy + 16)]
            pn.poly(cg, fill=c if sd < 0 else shade(c, 0.15), outline=INK, width=2.6)
            if HL >= 1:   # three embossed discs, the usual Italic cheek piece
                cx_ = hx + sd * (r - 3)
                for dy in (-6, 4, 14):
                    pn.circ(cx_, hy + dy - 8, 2.4, fill=light(c, 0.3), outline=cd, width=1)
        pn.circ(hx, by - 46, 7, fill=c, outline=INK, width=2.6)        # crest knob
        pn.circ(hx - 2, by - 48, 2.4, fill=light(c, 0.6))
        if O.get('plume'):
            for a_ in (-14, 0, 14):
                aa = math.radians(a_)
                pn.line([(hx, by - 50), (hx + math.sin(aa) * 30, by - 50 - math.cos(aa) * 34)], O['plume'], 5)
                if HL >= 1: pn.line([(hx + math.sin(aa) * 6, by - 56), (hx + math.sin(aa) * 26, by - 50 - math.cos(aa) * 30)], light(O['plume'], 0.3), 1.6)
    elif hat == 'bascinet':
        c = O.get('cap', (170, 174, 182)); HL = lod(pn, 2 * r)
        top = (hx - f * 4, hy - r - 30)
        dome = [(hx - r - 6, hy - 2), (hx - r - 4, hy - r * .55), (hx - r * .55, hy - r - 8), top, (hx + r * .55, hy - r - 8),
                (hx + r + 4, hy - r * .55), (hx + r + 6, hy - 2)]
        inner = [(hx + r * .78, hy - 4), (hx + r * .62, hy - r * .55), (hx, hy - r * .78), (hx - r * .62, hy - r * .55), (hx - r * .78, hy - 4)]
        pn.poly(dome + inner, fill=c, outline=INK, width=3)
        pn.poly([(hx + r * .2, hy - r - 14), top, (hx + r * .55, hy - r - 8), (hx + r + 4, hy - r * .55), (hx + r + 6, hy - 2), (hx + r * .78, hy - 4),
                 (hx + r * .62, hy - r * .55)], fill=shade(c, 0.22))
        pn.poly([(hx - r * .5, hy - r - 6), (hx - r * .15, hy - r - 18), (hx - r * .05, hy - r - 12), (hx - r * .4, hy - r + 2)], fill=light(c, 0.6))
        # raised houndskull visor: pivots at the temples, snout pointing up and forward
        vz = [(hx - r * .7, hy - r * .62), (hx - r * .5, hy - r - 16), (hx + f * r * .1, hy - r - 34), (hx + f * r * .55, hy - r - 26),
              (hx + r * .6, hy - r - 10), (hx + r * .7, hy - r * .62)]
        pn.poly(vz, fill=light(c, 0.12), outline=INK, width=2.8)
        if HL >= 1:
            pn.line([(hx - r * .3, hy - r - 18), (hx + f * r * .25, hy - r - 24)], INK, 2.2)
            for sd in (-1, 1): rivet(pn, hx + sd * r * .74, hy - r * .6, 3.2, c)
    elif hat == 'phrygian':
        # Phrygian (Thracian) helmet, bronze: skull raised from one sheet, tall apex curling forward, short brim peak,
        # neck guard and long cheek pieces (Alexander sarcophagus; Macedonian infantry, late 4th century BC)
        c = O['cap']; cd = lerpc(c, INK, .3); HL = lod(pn, 2 * r); by = hy - 24
        rel = [(-r - 4, 4), (-r - 2, -22), (-r * .6, -46), (-2, -60), (r * .45, -74), (r * .95, -70), (r * 1.02, -56), (r * .8, -50),
               (r * .9, -30), (r + 4, 4)]
        skull = [(hx + f * dx, by + dy) for dx, dy in rel]
        pn.poly(skull, fill=c, outline=INK, width=3)
        pn.poly([(hx + f * r * .1, by - 58), (hx + f * r * .45, by - 72), (hx + f * r * .9, by - 68), (hx + f * r * .75, by - 52),
                 (hx + f * r * .85, by - 28), (hx + f * (r + 3), by + 2), (hx + f * r * .3, by + 2)], fill=shade(c, 0.22))
        pn.poly([(hx - f * r * .6, by - 30), (hx - f * r * .35, by - 48), (hx - f * r * .1, by - 52), (hx - f * r * .35, by - 26)], fill=light(c, 0.55))
        pn.line([(hx - r - 6, by + 3), (hx + r + 6, by + 3)], cd, 6)
        pn.poly([(hx + f * r * .3, by + 1), (hx + f * (r + 16), by + 6), (hx + f * r * .3, by + 9)], fill=c, outline=INK, width=2.4)   # brim peak
        if HL >= 1:
            pn.line([(hx - f * r * .5, by - 6), (hx + f * r * .6, by - 6)], light(c, 0.35), 1.6, caps=False)
        for sd in (-1, 1):   # cheek pieces outside the eyes
            cg = [(hx + sd * (r - 8), by + 6), (hx + sd * (r + 3), by + 6), (hx + sd * (r + 2), hy + 24), (hx + sd * (r - 5), hy + 20)]
            pn.poly(cg, fill=c if sd * f < 0 else shade(c, 0.15), outline=INK, width=2.6)
            if HL >= 1: pn.line([(hx + sd * (r - 2), by + 12), (hx + sd * (r - 2), hy + 14)], light(c, 0.3), 1.4, caps=False)
        if O.get('plume'):
            for a_ in (-10, 6):
                aa = math.radians(a_)
                pn.line([(hx - f * 4, by - 60), (hx - f * 4 + math.sin(aa) * 26, by - 60 - math.cos(aa) * 24)], O['plume'], 5)
    elif hat == 'pilosb':
        # bronze pilos helmet: conical skull set off from a narrow brim by a rib (hoplites, later 5th and 4th century BC)
        c = O['cap']; cd = lerpc(c, INK, .3); by = hy - 26; HL = lod(pn, 2 * r)
        cone = [(hx - r - 4, by), (hx - r * .8, by - 28), (hx - r * .25, by - 66), (hx + r * .25, by - 66), (hx + r * .8, by - 28), (hx + r + 4, by)]
        pn.poly(cone, fill=c, outline=INK, width=3)
        pn.poly([(hx + r * .12, by - 64), (hx + r * .25, by - 66), (hx + r * .8, by - 28), (hx + r + 3, by - 1), (hx + r * .35, by - 1)], fill=shade(c, 0.25))
        pn.poly([(hx - r * .62, by - 26), (hx - r * .25, by - 58), (hx - r * .1, by - 58), (hx - r * .4, by - 22)], fill=light(c, 0.55))
        pn.line([(hx - r - 9, by + 1), (hx + r + 9, by + 1)], cd, 7)
        if HL >= 1: pn.line([(hx - r - 4, by - 5), (hx + r + 4, by - 5)], light(c, 0.3), 1.8, caps=False)
        pn.circ(hx, by - 67, 5, fill=c, outline=INK, width=2.2)
        if O.get('plume'):
            pn.poly([(hx - 4, by - 70), (hx + 4, by - 70), (hx - f * 34, by - 96), (hx - f * 44, by - 88)], fill=O['plume'], outline=INK, width=2.4)
    elif hat == 'cone':
        pn.poly([(hx - r - 2, hy - 10), (hx - r * .5, hy - r * .9), (hx + f * 4, hy - r - 26), (hx + r * .5, hy - r * .9), (hx + r + 2, hy - 10)],
                fill=O['cap'], outline=INK, width=3)
    elif hat == 'fur':
        pn.ell(hx, hy - r * .78, r * .86, r * .82, fill=O['cap'], outline=INK, width=3)
        pn.rect(hx - r - 6, hy - r * .78, hx + r + 6, hy - r * .78 + 24, fill=O['fur'], outline=INK, width=3, r=12)
        for i in range(9):
            xx = hx - r + i * r / 4
            pn.line([(xx, hy - r * .78 + 4), (xx + 4, hy - r * .78 + 18)], lerpc(O['fur'], INK, .3), 2, caps=False)
    if held and not arms_front: held(pn, J)
    pn.pop()
    CUR['skin'] = SKIN; CUR['bone'] = BONE
    return J

def blink_at(t, seed=0.0):
    ph = (t + seed * 1.37) % 3.3
    return 1.0 if ph < 0.06 else (0.6 if ph < 0.11 else 0.0)


# ---------------- variety: hair styles, face features, garment details ----------------
# OUT keys: skin (tone), hair (colour), hair_style ('crop' default, 'curly', 'receding', 'bald', 'tousled', 'long', 'fringe',
# 'grey_temples'), ears, nose ('button', 'long', 'hook', 'broad'), age (0..1 forehead and eye lines), scar, mole,
# brows (thick brow overlay colour), and garment keys exomis, patches, hem, neckerchief, belt (colour), sash.
def hair_back(pn, hx, hy, r, f, O):
    h = O.get('hair'); st = O.get('hair_style', 'crop')
    if not h: return
    if st == 'long':
        pn.poly([(hx - r - 4, hy - 8), (hx + r + 4, hy - 8), (hx + r + 2, hy + r * 0.9), (hx - r - 2, hy + r * 0.9)], fill=h, outline=INK, width=3)
        pn.circ(hx - f * 2, hy - 4, r + 4, fill=h, outline=INK, width=3)
    elif st == 'curly':
        for i in range(13):
            a = math.pi * (0.95 + 1.1 * i / 12)
            pn.circ(hx + math.cos(a) * (r + 1), hy - 4 + math.sin(a) * (r + 1), 10, fill=h, outline=INK, width=2.6)
        pn.circ(hx, hy - 4, r + 2, fill=h)
    elif st in ('receding', 'bald'):
        for sd in (-1, 1):
            pn.ell(hx + sd * (r - 4), hy - 2, 11, 18, fill=h, outline=INK, width=2.6)
    else:
        pn.circ(hx - f * 3, hy - 3, r + 3, fill=h, outline=INK, width=3)

def hair_front(pn, hx, hy, r, f, O):
    h = O.get('hair'); st = O.get('hair_style', 'crop')
    if not h: return
    hl = lerpc(h, (255, 248, 230), 0.25); dk = lerpc(h, INK, 0.35)
    if st == 'crop' or st == 'grey_temples':
        pn.poly([(hx - r * .95, hy - 6), (hx - r * .7, hy - r * .78), (hx, hy - r - 3), (hx + r * .7, hy - r * .78), (hx + r * .95, hy - 6),
                 (hx + r * .55, hy - r * .55), (hx - r * .55, hy - r * .55)], fill=h)
        if st == 'grey_temples':
            for sd in (-1, 1): pn.ell(hx + sd * (r * .82), hy - 10, 6, 10, fill=(190, 186, 178))
    elif st == 'curly':
        for i in range(7):
            a = math.pi * (1.15 + 0.7 * i / 6)
            pn.circ(hx + math.cos(a) * (r * .78), hy - 2 + math.sin(a) * (r * .78), 9, fill=h, outline=INK, width=2.2)
            pn.circ(hx + math.cos(a) * (r * .78) - 2, hy - 4 + math.sin(a) * (r * .78), 3, fill=hl)
    elif st == 'tousled':
        pts = [(hx - r * .98, hy - 4)]
        for i in range(8):
            a = math.pi * (1.0 + i / 7)
            rr = r + (9 if i % 2 else 2)
            pts.append((hx + math.cos(a) * rr, hy - 3 + math.sin(a) * rr))
        pts += [(hx + r * .98, hy - 4), (hx + r * .5, hy - r * .5), (hx + r * .1, hy - r * .35), (hx - r * .3, hy - r * .55), (hx - r * .6, hy - r * .45)]
        pn.poly(pts, fill=h, outline=INK, width=2.8)
        pn.line([(hx - r * .3, hy - r * .9), (hx - r * .1, hy - r * .6)], hl, 2.4)
    elif st == 'fringe':
        pn.poly([(hx - r * .97, hy - 2), (hx - r * .75, hy - r * .8), (hx, hy - r - 3), (hx + r * .75, hy - r * .8), (hx + r * .97, hy - 2),
                 (hx + r * .8, hy - r * .42)] + [(hx + r * (.6 - .24 * i), hy - r * (.42 if i % 2 else .52)) for i in range(7)] + [(hx - r * .85, hy - r * .42)],
                fill=h, outline=INK, width=2.6)
    elif st == 'long':
        pn.poly([(hx - r * .95, hy - 2), (hx - r * .7, hy - r * .8), (hx, hy - r - 4), (hx + r * .7, hy - r * .8), (hx + r * .95, hy - 2),
                 (hx + r * .2, hy - r * .6), (hx - r * .1, hy - r * .48)], fill=h)
    elif st == 'receding':
        pn.arc(hx, hy, r - 2, 200, 235, h, 7); pn.arc(hx, hy, r - 2, 305, 340, h, 7)
        pn.arc(hx - r * .2, hy - r * .55, 10, 200, 320, lerpc(CUR['skin'], INK, .25), 1.6)
    elif st == 'bald':
        pn.arc(hx - r * .25, hy - r * .45, 9, 210, 300, (255, 255, 255, 140), 3)

def features(pn, f, O):
    """Face local units (head r 36 at 0, 0). Drawn under the eyes and mouth."""
    ag = O.get('age', 0)
    if ag > 0:
        c = lerpc(CUR['skin'], INK, 0.32)
        for i in range(1 + int(ag * 2)):
            pn.arc(f * 2, 4 - i * 4, 30, 250, 290, c, 1.6)   # forehead lines sit above the brows
        for sd in (-1, 1):
            ex = f * 2 + sd * 12.5
            pn.line([(ex + sd * 11, -6), (ex + sd * 15, -9)], c, 1.4, caps=False)
            pn.line([(ex + sd * 11, -2), (ex + sd * 15, -1)], c, 1.4, caps=False)
    if O.get('scar'):
        pn.line([(f * 16, -22), (f * 22, -6)], lerpc(CUR['skin'], (170, 80, 70), .55), 2.4, caps=False)
        for i in range(3): pn.line([(f * (16.5 + i * 2.3) - 2, -19 + i * 5), (f * (16.5 + i * 2.3) + 2, -18 + i * 5)], lerpc(CUR['skin'], (170, 80, 70), .55), 1.4, caps=False)
    if O.get('mole'):
        pn.circ(f * -14, 12, 2, fill=lerpc(CUR['skin'], INK, .6))
    if O.get('cheeks'):
        for sd in (-1, 1): pn.ell(f * 2 + sd * 18, 9, 6, 3.4, fill=O['cheeks'] + (90,))

def nose(pn, f, kind):
    c = lerpc(CUR['skin'], INK, 0.5)
    x = f * 4
    if kind == 'button': pn.arc(x, 6, 3.6, 20, 160, c, 2.2)
    elif kind == 'long': pn.line([(x - f * 1, -2), (x + f * 4, 9), (x - f * 1, 10)], c, 2.2)
    elif kind == 'hook': pn.line([(x - f * 2, -4), (x + f * 4, 3), (x + f * 4, 8), (x - f * 1, 10)], c, 2.2)
    elif kind == 'broad':
        pn.arc(x - 4, 8, 3, 90, 200, c, 2); pn.arc(x + 4, 8, 3, -20, 90, c, 2); pn.line([(x - 3, 10), (x + 3, 10)], c, 2)

def garment_details(pn, O, body, nk, pl, hem, ux, uy, nx_, ny_, hw, f):
    col = O['tunic']; dk = lerpc(col, INK, 0.3); lt = lerpc(col, (255, 250, 236), 0.2)
    # rendered cloth (E020 user rule): one shadow tone on the side away from the light (light from screen right),
    # a lit edge on the near side, a darker band above the hem, a neckline and shoulder seams; outline redrawn on top
    sh_c = lerpc(col, (40, 30, 40), 0.24); hi_c = lerpc(col, (255, 244, 220), 0.32)
    R0, L0, L1, R1 = body
    mid_t = (lerp(L0[0], R0[0], 0.36), lerp(L0[1], R0[1], 0.36)); mid_b = (lerp(L1[0], R1[0], 0.3), lerp(L1[1], R1[1], 0.3))
    pn.poly([L0, mid_t, (lerp(mid_t[0], mid_b[0], 0.5) + nx_ * 3, lerp(mid_t[1], mid_b[1], 0.5) + ny_ * 3), mid_b, L1], fill=sh_c)
    pn.poly([(lerp(L0[0], R0[0], 0.84), lerp(L0[1], R0[1], 0.84)), R0, R1, (lerp(L1[0], R1[0], 0.86), lerp(L1[1], R1[1], 0.86))], fill=hi_c)
    hb0 = (lerp(L0[0], L1[0], 0.9), lerp(L0[1], L1[1], 0.9)); hb1 = (lerp(R0[0], R1[0], 0.9), lerp(R0[1], R1[1], 0.9))
    pn.poly([hb0, hb1, R1, L1], fill=lerpc(col, INK, 0.16) + (150,))
    nc = (nk[0] - ux * 2, nk[1] - uy * 2)
    pn.line([(nc[0] - nx_ * 11, nc[1] - ny_ * 11), (nc[0] - ux * 7, nc[1] - uy * 7), (nc[0] + nx_ * 11, nc[1] + ny_ * 11)], INK, 2.2)
    for sd in (-1, 1):
        a_ = (nk[0] + nx_ * sd * 20 - ux * 2, nk[1] + ny_ * sd * 20 - uy * 2)
        pn.line([a_, (a_[0] - ux * 12 + nx_ * sd * 3, a_[1] - uy * 12 + ny_ * sd * 3)], dk + (170,), 1.6, caps=False)
    pn.poly(body, fill=None, outline=INK, width=3.2)
    q = lambda a, b: (a[0] * (1 - b) + 0, 0)
    # cloth folds from the belt down
    for i in (-1, 0, 1):
        a_ = (lerp(nk[0], pl[0], 0.9) + nx_ * i * 12, lerp(nk[1], pl[1], 0.9) + ny_ * i * 12)
        b_ = (hem[0] + nx_ * i * 18 + ux * 2, hem[1] + ny_ * i * 18 + uy * 2)
        pn.line([a_, b_], dk + (150,), 1.8, caps=False)
    if O.get('exomis'):   # labourer's tunic fastened on one shoulder: the other shoulder and part of the chest bare
        sd = -1 if f > 0 else 1
        p0 = (nk[0] + nx_ * sd * 26 - ux * 2, nk[1] + ny_ * sd * 26 - uy * 2)
        p1 = (nk[0] - nx_ * sd * 4 - ux * 1, nk[1] - ny_ * sd * 4 - uy * 1)
        p2 = (lerp(nk[0], pl[0], 0.42) + nx_ * sd * 27, lerp(nk[1], pl[1], 0.42) + ny_ * sd * 27)
        pn.poly([p0, p1, p2], fill=CUR['skin'], outline=INK, width=2.4)
        pn.line([p1, p2], dk, 3)
        pn.circ(nk[0] - nx_ * sd * 14, nk[1] - ny_ * sd * 14 + 4, 3.2, fill=(150, 120, 80), outline=INK, width=1.4)
    if O.get('hem'):
        pn.line([(hem[0] - nx_ * (hw - 1), hem[1] - ny_ * (hw - 1)), (hem[0] + nx_ * (hw - 1), hem[1] + ny_ * (hw - 1))], O['hem'], 5, caps=False)
    if O.get('patches'):
        for (u, v, w_, h_) in ((0.62, 12, 9, 7), (0.8, -16, 7, 6)):
            cx_, cy_ = lerp(nk[0], hem[0], u) + nx_ * v, lerp(nk[1], hem[1], u) + ny_ * v
            pn.rect(cx_ - w_, cy_ - h_, cx_ + w_, cy_ + h_, fill=lerpc(col, (120, 100, 70), 0.45), outline=INK, width=1.6)
            for j in range(4):
                pn.line([(cx_ - w_ + 2 + j * w_ / 2, cy_ - h_ - 1), (cx_ - w_ + 2 + j * w_ / 2, cy_ - h_ + 2)], INK, 1.0, caps=False)
    if O.get('neckerchief'):
        c = O['neckerchief']
        pn.poly([(nk[0] - nx_ * 18, nk[1] - ny_ * 18 + 2), (nk[0] + nx_ * 18, nk[1] + ny_ * 18 + 2),
                 (nk[0] + nx_ * 4 - ux * 20, nk[1] + ny_ * 4 - uy * 20)], fill=c, outline=INK, width=2.2)
    if O.get('sash'):
        b = (lerp(nk[0], pl[0], 0.88), lerp(nk[1], pl[1], 0.88))
        pn.line([(b[0] - nx_ * 24, b[1] - ny_ * 24), (b[0] + nx_ * 24, b[1] + ny_ * 24)], INK, 11, caps=False)
        pn.line([(b[0] - nx_ * 23, b[1] - ny_ * 23), (b[0] + nx_ * 23, b[1] + ny_ * 23)], O['sash'], 7.5, caps=False)
        pn.line([(b[0] + nx_ * 10, b[1] + ny_ * 10), (b[0] + nx_ * 14 - ux * 16, b[1] + ny_ * 14 - uy * 16)], O['sash'], 5)

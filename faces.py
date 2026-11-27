"""Face system v2 (from E024): expressive faces in the house style, built from the principles of the anime "100 faces"
expression charts the user picked as reference, now drawn in the plain ink style of the "How do I feel right now?"
chart: white eyes with an ink outline and ONE solid ink pupil, no iris colour and NO eye highlights or sparkle (user
rule), an eye SHAPE per emotion, tapered brows, a small nose, open mouths with a coloured inside. Our own drawings.
No blush (user rule). Expression marks (sweat, tears, anger vein, shock lines) are ink or water coloured only.

face2(pn, f, expr, look, blink, r=36, beard=None, beard_style=None, t=0.0, mark=None)
Face local units: head radius r = 36, face centred at (0, 0); rig_cutout scales it to the real head.
mark: identity mark. The Keeper's is 'curl': one forehead curl that hangs out from under any helmet or fringe (drawn LAST,
over the helmet, by forehead_curl). He wears no glasses. 'brow_nick' (a scar gap in the brow) is kept but retired.
"""
import math
from lib import *
import rig as R

IRIS = (70, 46, 32); IRIS_D = (34, 22, 16); MOUTH_IN = (118, 36, 40); TONGUE = (222, 112, 104); TEETH = (252, 250, 244)
WATER = (150, 206, 238)

def S(eyes='open', brow=0, raise_=0, mouth='flat', es=1.0, ps=1.0, marks=(), look=None, lid=0.0):
    return dict(eyes=eyes, brow=brow, raise_=raise_, mouth=mouth, es=es, ps=ps, marks=tuple(marks), look=look, lid=lid)

# brow: tilt in degrees (+ inner end up = worried, - inner end down = angry); raise_: up is negative y units
SPEC = {
    'neutral':    S(),
    'happy':      S('happy', 8, -2, 'smile_open'),
    'laughing':   S('happy', 10, -4, 'laugh', marks=('shine',)),
    'surprised':  S('wide', 10, -6, 'o', es=1.12, ps=0.75),
    'awe':        S('stars', 8, -5, 'o_small', es=1.1),
    'confused':   S('open', 0, 0, 'wavy', marks=('question',), look=(0.6, -0.4)),
    'worried':    S('open', 16, -2, 'wavy', marks=('sweat',), lid=0.15),
    'fear':       S('wide', 20, -4, 'grit_open', es=1.08, ps=0.6, marks=('sweat', 'lines')),
    'terrified':  S('wide', 24, -6, 'scream', es=1.18, ps=0.5, marks=('sweat', 'lines', 'gloom')),
    'determined': S('angry', -16, 2, 'flat_firm', lid=0.25),
    'angry':      S('angry', -24, 3, 'grit', marks=('vein',), lid=0.3),
    'smug':       S('half', -6, 0, 'smirk', lid=0.45),
    'sly':        S('half', -10, 1, 'smirk', lid=0.5, look=(0.9, 0)),
    'thinking':   S('open', 6, -2, 'side', look=(0.7, -0.7)),
    'skeptical':  S('half', -4, 0, 'side', lid=0.4, marks=('one_brow',)),
    'bored':      S('half', 0, 2, 'flat', lid=0.55),
    'exhausted':  S('half', 14, 2, 'open_small', lid=0.6, marks=('sweat', 'gloom')),
    'proud':      S('happy', -4, -1, 'smile', marks=('shine',)),
    'disgusted':  S('squeeze', -14, 2, 'tongue', marks=('gloom',)),
    'pain':       S('squeeze', 18, 0, 'grit_open', marks=('sweat',)),
    'seasick':    S('half', 16, 0, 'wavy', lid=0.5, marks=('gloom', 'sweat')),
    'embarrassed': S('open', 14, -2, 'wavy', marks=('sweat', 'lines'), look=(0.8, 0.5), lid=0.2),
    'crying':     S('teary', 20, -2, 'cry', marks=('tears',)),
}

def _brow(pn, x, y, side, tilt, f, raise_, w=5.2, nick=False):
    """Tapered brow stroke: thick at the inner end, thin at the outer end."""
    a = math.radians(tilt) * (-side)
    L = 9.0
    pts_top, pts_bot = [], []
    for i in range(7):
        u = i / 6; px = x - side * (L / 2) + side * L * u * 1.0
        py = y + raise_ - math.tan(a) * (px - x) * 1.0 - 1.4 * math.sin(math.pi * u)
        th = lerp(w, w * 0.35, u if side > 0 else 1 - u) * 0.5
        pts_top.append((px, py - th)); pts_bot.append((px, py + th))
    pts = pts_top + pts_bot[::-1]
    pn.poly(pts, fill=INK)
    if nick:                      # identity scar: a small skin coloured gap across the brow
        cx, cy = x + side * 1.5, y + raise_
        pn.line([(cx - 0.8, cy - 3.2), (cx + 1.0, cy + 3.2)], R.FACE_SKIN or SKIN, 2.4, caps=False)   # stays inside the brow

def _eye(pn, x, y, sp, f, look, side, blink):
    kind, es, ps, lid = sp['eyes'], sp['es'], sp['ps'], max(sp['lid'], blink)
    rx, ry = 7.6 * es, 9.4 * es
    if kind == 'happy':          # closed, upturned arc
        pn.arc(x, y + 2, 5.6 * es, 200, 340, INK, 3.0); return
    if kind == 'squeeze':        # > <
        d = 5.0 * es
        pn.line([(x - side * d, y - 4), (x + side * d * 0.4, y), (x - side * d, y + 4)], INK, 2.8); return
    if blink > 0.8:
        pn.line([(x - rx, y + 1), (x + rx, y + 1)], INK, 2.8); return
    skin = R.FACE_SKIN or SKIN
    pn.ell(x, y, rx, ry, fill=WHITE, outline=INK, width=2.4)   # one even outline only: no lash rim (it read as a second brow)
    lx, ly = clamp(look[0] * f, -1, 1) * 2.8, look[1] * 2.8 + 0.6
    # pupils follow the "How do I feel" chart: one solid ink dot, no iris ring, no highlight
    if kind in ('open', 'angry', 'half', 'teary'):
        pn.circ(x + lx, y + ly, 3.9 * ps, fill=INK)
    elif kind == 'wide':
        pn.circ(x + lx * 0.6, y + ly * 0.6, 1.9 * ps + 0.5, fill=INK)
    elif kind == 'stars':          # awe: big solid pupils filling the eye (chart "Interested")
        pn.circ(x + lx * 0.4, y + ly * 0.4, 5.6, fill=INK)
    # lids: cover the top of the eye in skin (half lidded, angry cut inner side, worried cut outer side)
    if kind == 'angry' or (kind == 'open' and sp['brow'] < -10):
        pn.poly([(x - rx - 1, y - ry - 2), (x + rx + 1, y - ry - 2), (x + side * rx + side, y - ry * 0.2), (x - side * rx - side, y - ry * 0.75)], fill=skin)
    if lid > 0.05:
        yl = y - ry + 2 * ry * lid
        pn.poly([(x - rx - 1, y - ry - 2), (x + rx + 1, y - ry - 2), (x + rx + 1, yl), (x - rx - 1, yl)], fill=skin)
        pn.line([(x - rx - 0.5, yl), (x + rx + 0.5, yl)], INK, 2.6)
    if kind == 'teary':           # a water line on the lower lid
        pn.arc(x, y + 1.5, rx * 0.9, 25, 155, WATER, 3.0)

def _mouth(pn, f, kind, beard):
    mx, my = f * 1.5, 15.5
    def open_shape(w, h, tongue=True, teeth=False, dy=0.0):
        pts = [(mx + w * math.cos(math.radians(a)), my + dy + h * 0.25 + h * math.sin(math.radians(a))) for a in range(0, 361, 20)]
        pts = [(mx - w, my + dy)] + [(mx + w * math.cos(math.radians(a)), my + dy + h * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(mx + w, my + dy)]
        pts = [(mx + w * math.cos(math.radians(a)), my + dy + (h if 0 <= a <= 180 else h * 0.18) * math.sin(math.radians(a))) for a in range(0, 360, 15)]
        pn.poly(pts, fill=MOUTH_IN, outline=INK, width=2.2)
        if teeth: pn.poly([(mx - w * 0.82, my + dy - h * 0.08), (mx + w * 0.82, my + dy - h * 0.08), (mx + w * 0.7, my + dy + h * 0.22), (mx - w * 0.7, my + dy + h * 0.22)], fill=TEETH)
        if tongue: pn.ell(mx, my + dy + h * 0.62, w * 0.55, h * 0.3, fill=TONGUE)
    if kind == 'flat': pn.line([(mx - 5, my), (mx + 5, my)], INK, 2.6)
    elif kind == 'flat_firm': pn.line([(mx - 6, my + 0.5), (mx + 6, my - 0.5)], INK, 3.0)
    elif kind == 'smile': pn.arc(mx, my - 4, 7, 30, 150, INK, 2.8)
    elif kind == 'smile_open': open_shape(7.5, 6.5)
    elif kind == 'laugh': open_shape(9.5, 9, teeth=True)
    elif kind == 'o': pn.ell(mx, my + 2, 4.8, 6.2, fill=MOUTH_IN, outline=INK, width=2.2)
    elif kind == 'o_small': pn.ell(mx, my + 1, 2.8, 3.4, fill=MOUTH_IN, outline=INK, width=2)
    elif kind == 'open_small': pn.ell(mx, my + 1, 4.0, 2.6, fill=MOUTH_IN, outline=INK, width=2)
    elif kind == 'scream': open_shape(8.5, 12, tongue=True)
    elif kind == 'cry': open_shape(8, 7, tongue=True, dy=1)
    elif kind == 'wavy': pn.line([(mx - 7, my), (mx - 3.5, my - 2), (mx, my + 1), (mx + 3.5, my - 2), (mx + 7, my)], INK, 2.6)
    elif kind == 'side': pn.line([(mx - 2, my + 1), (mx + f * 6, my - 1.5)], INK, 2.8)
    elif kind == 'smirk': pn.line([(mx - 6, my + 1), (mx + 2, my + 1), (mx + 6.5, my - 2.5)], INK, 2.8)
    elif kind in ('grit', 'grit_open'):
        h = 4.5 if kind == 'grit' else 6.5
        pn.rect(mx - 9, my - h, mx + 9, my + h, fill=TEETH, outline=INK, width=2.2, r=2)
        for xx in (-4.5, 0, 4.5): pn.line([(mx + xx, my - h), (mx + xx, my + h)], INK, 1.3, caps=False)
        pn.line([(mx - 9, my), (mx + 9, my)], INK, 1.3, caps=False)
    elif kind == 'tongue':
        pn.line([(mx - 7, my - 1), (mx + 7, my - 1)], INK, 2.6); pn.ell(mx + f * 2, my + 2.5, 3.4, 3.4, fill=TONGUE, outline=INK, width=1.6)

def _marks(pn, sp, f, r):
    m = sp['marks']
    if 'sweat' in m:
        x, y = -f * (r * 0.72), -r * 0.35
        pn.poly([(x, y - 7), (x + 3.6, y + 1.5), (x, y + 4.5), (x - 3.6, y + 1.5)], fill=WATER, outline=INK, width=1.4)
    if 'tears' in m:
        for side in (-1, 1):
            x0 = f * 2 + side * 12
            pn.line([(x0, 6), (x0 + side * 0.8, 14), (x0 - side * 0.4, 24)], WATER, 3.2)
    if 'vein' in m:                # anger vein, ink: four curved ticks in a cross
        x, y = f * r * 0.55, -r * 0.62
        for a in (45, 135, 225, 315):
            ra = math.radians(a); ux, uy = math.cos(ra), math.sin(ra)
            pn.arc(x + ux * 4.2, y + uy * 4.2, 2.6, a + 90, a + 270, INK, 2.0)
    if 'lines' in m:               # shock lines above the head
        for i, a in enumerate((-60, -90, -120)):
            ra = math.radians(a)
            pn.line([(math.cos(ra) * (r + 6), math.sin(ra) * (r + 6)), (math.cos(ra) * (r + 13), math.sin(ra) * (r + 13))], INK, 2.4)
    if 'gloom' in m:               # vertical gloom strokes on the forehead
        for xx in (-8, -3, 2, 7):
            pn.line([(xx + f * 2, -r * 0.82), (xx + f * 2, -r * 0.45)], INK + (120,), 1.6)
    if 'question' in m:
        pn.text(-f * (r + 8), -r * 0.7, '?', 22, INK, 'Black')
    if 'shine' in m:               # small sparkle by the head
        x, y = -f * (r + 6), -r * 0.6
        pn.poly([(x, y - 6), (x + 1.6, y - 1.6), (x + 6, y), (x + 1.6, y + 1.6), (x, y + 6), (x - 1.6, y + 1.6), (x - 6, y), (x - 1.6, y - 1.6)], fill=INK)

def fringe(pn, hx, hy, r, hair):
    """Hair fringe on a bare head, cut high (bottom edge at 0.72 r) so the brows always sit on bare forehead."""
    pn.poly([(hx - r * .95, hy - 8), (hx - r * .7, hy - r * .8), (hx, hy - r - 3), (hx + r * .7, hy - r * .8), (hx + r * .95, hy - 8),
             (hx + r * .6, hy - r * .72), (hx - r * .6, hy - r * .72)], fill=hair)

def forehead_curl(pn, f, hair, r=36):
    """The Keeper's identity curl, face local units. Drawn after hair AND helmet so it shows in every costume.
    Sits between the brows (inner brow ends are at x = 9 from centre), hangs from y -29 to -17."""
    cx, cy, rr = f * 2.5, -20.5, 3.6
    pts = [(cx - f * 2.5, -30.5), (cx - f * 0.8, -27.0), (cx + f * 0.6, -24.4)]
    for i in range(11):                                   # open loop (a closed ring read as a hook): from top right, down, back up the left
        a = math.radians(-70 + i * 22)
        pts.append((cx + f * rr * math.cos(a), cy + rr * math.sin(a) + 0.3))
    pn.line(pts, INK, 6.6)
    pn.line(pts, hair, 3.2)

def face2(pn, f, expr='neutral', look=(0.6, 0), blink=0.0, r=36, beard=None, beard_style=None, t=0.0, mark=None, hair=(60, 44, 32)):
    sp = SPEC.get(expr, SPEC['neutral'])
    if sp['look'] is not None: look = sp['look']
    ex0 = f * 2.0
    for side in (-1, 1):
        _eye(pn, ex0 + side * 13.5, -2, sp, f, look, side, blink)
    br = sp['raise_']
    for side in (-1, 1):
        tilt = sp['brow']
        if 'one_brow' in sp['marks'] and side == f: tilt, rs = 10, br - 4
        else: rs = br
        _brow(pn, ex0 + side * 13.5, -15.0, side, tilt, f, rs, nick=(mark == 'brow_nick' and side == -f))
    pn.arc(f * 3.5, 6.5, 2.2, 200 if f > 0 else -20, 340 if f > 0 else 120, INK, 1.8)       # small nose
    mouth_open = sp['mouth'] in ('laugh', 'scream', 'cry', 'smile_open', 'grit_open', 'o')
    if beard:
        patch = R.facial_hair(pn, f, beard_style or 'full', beard, r, True, mouth_open)
        pn.ell(f * 1.5, 15.5, patch[0], patch[1], fill=R.FACE_SKIN or SKIN)
    _mouth(pn, f, sp['mouth'], beard)
    if 'pale' in sp['marks']:
        pn.poly([(-r * 0.75, -r * 0.55), (r * 0.75, -r * 0.55), (r * 0.6, -r * 0.2), (-r * 0.6, -r * 0.2)], fill=(120, 150, 190, 60))
    _marks(pn, sp, f, r)
    if mark == 'curl': forehead_curl(pn, f, hair, r)

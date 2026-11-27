"""Cutout rig (v2): solid vector body parts on the E012 skeleton.

Same skeleton, joints, poses, IK and faces as rig.py (head stays about a third of body height). What changes is how the
body is drawn: every body and costume piece is a closed vector shape stored in parts/body_v2.svg, one <g id="..."> per
part, with the pivot at the group's origin and the bone running down +y. The rig rotates each part onto its bone.

Edit a part in Inkscape: open parts/body_v2.svg, change the shapes inside a group (keep the group id and keep the pivot
marker where it is), save. The engine reads the file on every run, so every episode picks up the edit.
Rebuild the file from the defaults in this module with:  python3 rig_cutout.py --write-parts   (overwrites edits).

Path classes pick the colour from the outfit (skin, cloth, trim, linen, metal, hair); a class ending in _sh is the
shadow tone, authored on the -x side and always kept on the side away from the light (light from screen right).
A class of line or fold is a stroke only.
"""
import math, os, re, sys
import xml.etree.ElementTree as ET
from lib import *
import rig as R
import faces as F2
from detail import shade, light
from props import aspis, dory

PARTS_SVG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parts', 'body_v2.svg')
L = R.L
OUTLINE = 3.0

# ---------------- default part shapes (local units, pivot at 0,0, bone along +y) ----------------
def _capsule(Ln, w0, w1, n=10, x=0.0):
    r0, r1 = w0 / 2, w1 / 2; pts = []
    for i in range(n + 1):
        a = math.pi + math.pi * i / n; pts.append((x + r0 * math.cos(a), r0 * math.sin(a)))
    for i in range(n + 1):
        a = math.pi * i / n; pts.append((x + r1 * math.cos(a), Ln + r1 * math.sin(a)))
    return pts

def _ell(cx, cy, rx, ry, n=24, a0=0, a1=360):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + (0 if a1 - a0 == 360 else 1))]

def _strip(Ln, w0, w1, frac=0.38):
    """Shadow strip on the -x side of a tapered limb."""
    return [(-w0 / 2 + 1, 2), (-w0 / 2 + 1 + w0 * frac, 4), (-w1 / 2 + 1 + w1 * frac, Ln - 2), (-w1 / 2 + 1, Ln)]

def _defaults():
    P = {}
    S = lambda cls, pts, closed=True, w=OUTLINE: dict(cls=cls, pts=pts, closed=closed, w=w)
    # limbs: shoulder to elbow, elbow to wrist, hip to knee, knee to ankle
    P['upper_arm'] = [S('skin', _capsule(L['ua'], 15, 13)), S('skin_sh', _strip(L['ua'], 15, 13), w=0)]
    P['forearm'] = [S('skin', _capsule(L['fa'], 13, 11)), S('skin_sh', _strip(L['fa'], 13, 11), w=0)]
    P['thigh'] = [S('skin', _capsule(L['th'], 19, 15)), S('skin_sh', _strip(L['th'], 19, 15), w=0)]
    P['shin'] = [S('skin', _capsule(L['sh'], 15, 11)), S('skin_sh', _strip(L['sh'], 15, 11), w=0)]
    # mitten hands (pivot at the wrist): open hand, and a fist that wraps a shaft at y 8
    P['hand'] = [S('skin', [(3, 2), (9, -1), (12.5, 2.5), (11, 8), (5, 9)]), S('skin', _ell(-0.5, 8.5, 7.4, 9.0)),
                 S('line', [(-4, 13), (-4, 16.5)], False, 1.4), S('line', [(0, 14), (0, 17.5)], False, 1.4)]
    P['fist'] = [S('skin', _ell(0, 8, 8.2, 7.6)), S('line', [(-5.5, 5.5), (5.5, 5.5)], False, 1.6),
                 S('line', [(-5.5, 9.5), (5.5, 9.5)], False, 1.6)]
    # bare foot (pivot at the ankle, toes toward +x = the facing side)
    P['foot'] = [S('skin', _ell(4, 5, 12, 5.6, 24)),
                 S('line', [(9, 6), (12, 7)], False, 1.4)]
    # body under the clothes: neck (0,0) to pelvis (0,100)
    P['torso'] = [S('skin', [(-27, 10), (-29, 22), (-23, 70), (-25, 98), (25, 98), (23, 70), (29, 22), (27, 10), (8, 2), (-8, 2)])]
    # Greek chiton: short wool tunic, belted, hem at mid thigh (garments stop above the knee)
    P['chiton'] = [S('cloth', [(-12, 3), (-31, 12), (-30, 30), (-25, 64), (-28, 86), (-33, 114), (-14, 118), (0, 116),
                               (14, 118), (33, 114), (28, 86), (25, 64), (30, 30), (31, 12), (12, 3), (0, 9)]),
                   S('cloth_sh', [(-31, 12), (-30, 30), (-25, 64), (-28, 86), (-33, 114), (-23, 116), (-18, 88), (-17, 64), (-21, 26)], w=0),
                   S('trim', [(-33, 109), (-14, 113), (0, 111), (14, 113), (33, 109), (33, 114), (14, 118), (0, 116), (-14, 118), (-33, 114)], w=0),
                   S('fold', [(-10, 90), (-13, 113)], False, 1.8), S('fold', [(6, 92), (8, 113)], False, 1.8),
                   S('fold', [(18, 88), (23, 111)], False, 1.8),
                   S('belt', [(-26, 62), (26, 62), (26, 68), (-26, 68)], w=2.2)]
    # linothorax, tube and yoke type: linen body tube, shoulder yoke flaps tied down to the chest, two rows of pteruges
    pter = []
    for row, (y0, y1, n) in enumerate(((86, 102, 8), (95, 111, 9))):
        span = 60 + row * 6; dx = span / n
        for i in range(n):
            x0 = -span / 2 + i * dx + 0.8
            pter.append(S('linen' if row else 'linen2', [(x0, y0), (x0 + dx - 1.6, y0), (x0 + dx - 1.6, y1), (x0, y1)], w=1.8))
    P['linothorax'] = [q for q in pter if q['cls'] == 'linen'] + [q for q in pter if q['cls'] == 'linen2'] + [
        S('linen', [(-30, 22), (-29, 50), (-27, 88), (27, 88), (29, 50), (30, 22), (18, 14), (-18, 14)]),
        S('linen_sh', [(-30, 22), (-29, 50), (-27, 88), (-17, 88), (-20, 50), (-22, 22)], w=0),
        S('trim', [(-27, 80), (27, 80), (27, 86), (-27, 86)], w=0),
        S('trim', [(-29.5, 40), (29.5, 40), (29.4, 45), (-29.4, 45)], w=0),
        # yoke flaps over the shoulders, tied to the breast
        S('linen', [(-30, 10), (-12, 10), (-11, 36), (-24, 38), (-31, 24)], w=2.6),
        S('linen', [(30, 10), (12, 10), (11, 36), (24, 38), (31, 24)], w=2.6),
        S('metal', _ell(-17, 33, 3.2, 3.2, 12), w=1.6), S('metal', _ell(17, 33, 3.2, 3.2, 12), w=1.6),
        S('line', [(-17, 33), (-6, 45)], False, 1.6), S('line', [(17, 33), (6, 45)], False, 1.6)]
    # short chiton sleeve on the upper arm, open cuff
    P['sleeve'] = [S('cloth', [(-11, -4), (11, -4), (12, 15), (-12, 15)]), S('cloth_sh', [(-11, -4), (-4, -4), (-5, 15), (-12, 15)], w=0),
                   S('trim', [(-12, 12), (12, 12), (12, 15), (-12, 15)], w=0)]
    # bronze greave on the shin: knee boss at the top, follows the calf
    P['greave'] = [S('metal', [(-9.5, -3), (-6, -7), (6, -7), (9.5, -3), (9, 14), (7, 30), (5.5, 34), (-5.5, 34), (-7, 30), (-9, 14)]),
                   S('metal_sh', [(-9.5, -3), (-6, -7), (-3, -6), (-4, 14), (-3, 33), (-5.5, 34), (-7, 30), (-9, 14)], w=0),
                   S('line', [(-5, 1), (0, 3), (5, 1)], False, 1.6)]
    # helmets (pivot at the head centre, head radius 46)
    P['pilos'] = [S('metal', [(-49, -22), (-40, -52), (-17, -80), (17, -80), (40, -52), (49, -22)]),
                  S('metal_sh', [(-49, -22), (-40, -52), (-17, -80), (-6, -80), (-24, -50), (-30, -22)], w=0),
                  S('metal', [(-52, -26), (52, -26), (50, -18), (-50, -18)], w=2.6),
                  S('metal', _ell(0, -82, 5, 3.5, 12), w=2)]
    # Corinthian helmet worn pushed back on top of the head (as on Attic vases when not fighting): the face plate,
    # eye openings and nose guard sit above the brow, the crest on a holder above
    P['corinthian_up'] = [
        S('crest', [(-6, -94), (-9, -138), (0, -146), (9, -138), (6, -94)]),
        S('crest_sh', [(-6, -94), (-9, -138), (-3, -144), (-2, -94)], w=0),
        S('metal', [(-3, -96), (3, -96), (4, -84), (-4, -84)], w=2),
        S('metal', _ell(0, -52, 50, 36, 30, 180, 360) + [(50, -50), (46, -36), (34, -30), (20, -36), (8, -36), (4, -30), (-4, -30),
                                                        (-8, -36), (-20, -36), (-34, -30), (-46, -36), (-50, -50)]),
        S('metal_sh', _ell(0, -52, 49, 35, 12, 180, 240) + [(-26, -70), (-30, -50), (-46, -37), (-49, -50)], w=0),
        S('hole', _ell(-15, -50, 10, 5.5, 16, 180, 360) + [(-5, -44), (-22, -44)], w=1.8),
        S('hole', _ell(15, -50, 10, 5.5, 16, 180, 360) + [(22, -44), (5, -44)], w=1.8),
        S('line', [(-48, -55), (48, -55)], False, 1.4)]
    # long hair (Spartans, Xenophon Lac. Pol. 11.3): falls behind the head to the shoulders; pivot at the head centre
    P['hair_long'] = [S('hair', [(-50, -10), (-46, -36), (-26, -52), (0, -56), (26, -52), (46, -36), (50, -10), (50, 40), (40, 62),
                                 (22, 66), (-22, 66), (-40, 62), (-50, 40)]),
                      S('hair_sh', [(-50, -10), (-46, -36), (-30, -48), (-36, -10), (-38, 60), (-50, 40)], w=0),
                      S('line', [(-30, 30), (-28, 58)], False, 1.4), S('line', [(30, 30), (28, 58)], False, 1.4)]
    # faces come from faces.py (v2); the Keeper wears no glasses, his marker is OUT2 'mark'; hair under a helmet is not drawn
    return P

# ---------------- SVG writer and reader ----------------
def _hex(c): return '#%02x%02x%02x' % tuple(c[:3])
DEFAULT_COL = dict(skin=SKIN, cloth=(150, 54, 42), trim=(38, 30, 22), linen=(236, 228, 206), linen2=(214, 204, 178),
                   metal=(196, 150, 72), crest=(150, 40, 36), belt=(96, 64, 38), hole=(92, 64, 30), hair=(60, 44, 32))

def write_parts(path=PARTS_SVG):
    P = _defaults(); os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = 4; cw, chh = 170, 230
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols * cw}" height="{((len(P) + cols - 1) // cols) * chh}" '
           f'viewBox="0 0 {cols * cw} {((len(P) + cols - 1) // cols) * chh}">',
           '<!-- Before Machines cutout rig parts. One group per part; the group origin is the pivot (red dot), the bone runs '
           'down +y. Classes set the outfit colour. Edit shapes freely, keep ids and pivots. -->']
    for i, (name, subs) in enumerate(P.items()):
        gx = (i % cols) * cw + cw / 2; gy = (i // cols) * chh + (150 if name in ('pilos', 'corinthian_up') else 60)
        out.append(f'<g id="{name}" transform="translate({gx:.1f},{gy:.1f})">')
        for s in subs:
            d = 'M ' + ' L '.join(f'{x:.2f},{y:.2f}' for x, y in s['pts']) + (' Z' if s['closed'] else '')
            base = s['cls'].replace('_sh', '')
            col = DEFAULT_COL.get(base, (120, 120, 120))
            if s['cls'].endswith('_sh'): col = shade(col, 0.16)
            if s['cls'] in ('line', 'fold'):
                st = f'fill="none" stroke="{_hex(INK if s["cls"] == "line" else shade(DEFAULT_COL["cloth"], .35))}" stroke-width="{s["w"]}"'
            else:
                st = f'fill="{_hex(col)}"' + (f' stroke="{_hex(INK)}" stroke-width="{s["w"]}"' if s['w'] else '')
            out.append(f'  <path class="{s["cls"]}" d="{d}" {st} stroke-linejoin="round"/>')
        out.append('  <circle class="pivot" cx="0" cy="0" r="2.5" fill="#d02020"/>')
        out.append(f'  <text class="label" x="0" y="{-30 if name not in ("pilos", "corinthian_up") else 30}" font-size="11" '
                   f'text-anchor="middle" fill="#786955">{name}</text>')
        out.append('</g>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out)); return path

_NUM = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
def _parse_d(d, steps=10):
    """SVG path data to a list of (points, closed) subpaths. Supports M L H V C S Q T Z, absolute and relative."""
    toks = re.findall(r'[MmLlHhVvCcSsQqTtZzAa]|' + _NUM.pattern, d)
    subs = []; cur = []; x = y = 0.0; sx = sy = 0.0; cmd = None; i = 0; lc = None
    def num():
        nonlocal i; v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if re.match(r'[A-Za-z]', t): cmd = t; i += 1
        if cmd in 'Zz':
            if cur: subs.append((cur, True)); cur = []
            x, y = sx, sy; cmd = None; continue
        rel = cmd.islower(); C = cmd.upper()
        if C == 'M':
            if cur: subs.append((cur, False))
            nx, ny = num(), num(); x, y = (x + nx, y + ny) if rel else (nx, ny); sx, sy = x, y; cur = [(x, y)]
            cmd = 'l' if rel else 'L'; lc = None
        elif C == 'L':
            nx, ny = num(), num(); x, y = (x + nx, y + ny) if rel else (nx, ny); cur.append((x, y)); lc = None
        elif C == 'H':
            nx = num(); x = x + nx if rel else nx; cur.append((x, y)); lc = None
        elif C == 'V':
            ny = num(); y = y + ny if rel else ny; cur.append((x, y)); lc = None
        elif C in 'CS':
            if C == 'C':
                c1 = (num(), num())
                c1 = (x + c1[0], y + c1[1]) if rel else c1
            else:
                c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            c2 = (num(), num()); e = (num(), num())
            if rel: c2 = (x + c2[0], y + c2[1]); e = (x + e[0], y + e[1])
            for k in range(1, steps + 1):
                u = k / steps; a, b, c_, d_ = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
                cur.append((a * x + b * c1[0] + c_ * c2[0] + d_ * e[0], a * y + b * c1[1] + c_ * c2[1] + d_ * e[1]))
            lc = c2; x, y = e
        elif C in 'QT':
            if C == 'Q':
                c1 = (num(), num()); c1 = (x + c1[0], y + c1[1]) if rel else c1
            else:
                c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            e = (num(), num()); e = (x + e[0], y + e[1]) if rel else e
            for k in range(1, steps + 1):
                u = k / steps
                cur.append(((1 - u) ** 2 * x + 2 * u * (1 - u) * c1[0] + u * u * e[0], (1 - u) ** 2 * y + 2 * u * (1 - u) * c1[1] + u * u * e[1]))
            lc = c1; x, y = e
        elif C == 'A':   # arcs: approximated by a straight segment to the end point
            for _ in range(5): num()
            nx, ny = num(), num(); x, y = (x + nx, y + ny) if rel else (nx, ny); cur.append((x, y)); lc = None
    if cur: subs.append((cur, False))
    return subs

def _matrix(tr):
    if not tr: return (1, 0, 0, 1, 0, 0)
    m = (1, 0, 0, 1, 0, 0)
    for kind, args in re.findall(r'(\w+)\s*\(([^)]*)\)', tr):
        v = [float(a) for a in _NUM.findall(args)]
        if kind == 'translate': n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif kind == 'scale': n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif kind == 'matrix': n = tuple(v)
        elif kind == 'rotate':
            a = math.radians(v[0]); n = (math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
        else: continue
        a, b, c, d, e, f = m; A, B, C_, D, E_, F_ = n
        m = (a * A + c * B, b * A + d * B, a * C_ + c * D, b * C_ + d * D, a * E_ + c * F_ + e, b * E_ + d * F_ + f)
    return m

def _style(el):
    st = dict(re.findall(r'([\w-]+)\s*:\s*([^;]+)', el.get('style', '')))
    g = lambda k: st.get(k, el.get(k))
    return g('fill'), g('stroke'), g('stroke-width')

def _col(s):
    if not s or s == 'none': return None
    s = s.strip()
    if s.startswith('#') and len(s) == 7: return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    if s.startswith('#') and len(s) == 4: return tuple(int(c * 2, 16) for c in s[1:])
    return None

_CACHE = {}
def parts(path=PARTS_SVG):
    """Read the parts file (cached per modification time). Group transforms are layout only and are ignored."""
    if not os.path.exists(path): write_parts(path)
    key = (path, os.path.getmtime(path))
    if key in _CACHE: return _CACHE[key]
    ns = '{http://www.w3.org/2000/svg}'
    root = ET.parse(path).getroot(); P = {}
    for g in root.iter(ns + 'g'):
        gid = g.get('id') or g.get('{http://www.inkscape.org/namespaces/inkscape}label')
        if not gid: continue
        subs = []
        for el in g.iter(ns + 'path'):
            cls = (el.get('class') or '').split()[0] if el.get('class') else ''
            fill, stroke, sw = _style(el)
            m = _matrix(el.get('transform'))
            for pts, closed in _parse_d(el.get('d', '')):
                pts = [(m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]) for x, y in pts]
                subs.append(dict(cls=cls, pts=pts, closed=closed, fill=_col(fill), stroke=_col(stroke),
                                 w=float(_NUM.findall(sw)[0]) if sw else 0.0))
        if subs: P[gid] = subs
    _CACHE.clear(); _CACHE[key] = P
    return P

# ---------------- drawing ----------------
def draw_part(pn, name, a, b=None, f=1, O=None, ang=None, scale=1.0):
    """Draw part `name` with its pivot on point a and its +y axis toward point b (or at angle ang, radians from
    straight down, or upright when both are None). f mirrors it to the facing side."""
    O = O or {}
    if b is not None:
        dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1.0; dx, dy = dx / n, dy / n
    elif ang is not None:
        dx, dy = -math.sin(ang), math.cos(ang)
    else:
        dx, dy = 0.0, 1.0
    xa = (dy, -dx)                      # local +x on screen (before mirroring)
    flip_sh = (f * xa[0]) < 0           # keep shadow tones on screen left
    for s in parts()[name]:
        cls = s['cls']; sh = cls.endswith('_sh'); base = cls[:-3] if sh else cls
        mx = f * (-1 if (sh and flip_sh) else 1)
        pts = [(a[0] + (mx * x * xa[0] + y * dx) * scale, a[1] + (mx * x * xa[1] + y * dy) * scale) for x, y in s['pts']]
        if cls in ('line', 'fold') or (not s['closed'] and s['fill'] is None):
            col = INK if cls == 'line' else shade(O.get('cloth', s['stroke'] or INK), 0.35)
            pn.line(pts, s['stroke'] if (cls not in ('line', 'fold') and s['stroke']) else col, max(1.0, s['w']), caps=True)
            continue
        col = O.get(base, s['fill'] or DEFAULT_COL.get(base, (128, 128, 128)))
        if sh: col = shade(col, 0.16)
        if len(pts) >= 3:
            pn.poly(pts, fill=col, outline=INK if s['w'] else None, width=s['w'])

OUT2 = {
    # E024 Greek hoplites, late 5th century BC (Mantinea, 418 BC)
    'hop_keeper': dict(skin=SKIN, cloth=(150, 54, 42), trim=(64, 40, 30), linen=(238, 230, 208), linen2=(218, 208, 182),
                       metal=(196, 150, 72), crest=(40, 30, 24), belt=(96, 64, 38), helmet='corinthian_up', mark='curl',
                       armour='linothorax', greaves=True, beard=None),
    'hop_a': dict(skin=(228, 196, 160), cloth=(70, 92, 128), trim=(40, 50, 70), linen=(234, 226, 204), linen2=(212, 202, 176),
                  metal=(186, 144, 70), belt=(96, 64, 38), helmet='pilos', armour='linothorax', greaves=True,
                  beard=(62, 46, 34), beard_style='full'),
    'hop_b': dict(skin=(214, 172, 132), cloth=(112, 74, 52), trim=(70, 44, 30), linen=(230, 222, 198), linen2=(208, 198, 172),
                  metal=(200, 156, 78), crest=(150, 40, 36), belt=(80, 54, 32), helmet='corinthian_up', armour='linothorax',
                  greaves=True, beard=(90, 66, 44), beard_style='short'),
    'spartan1': dict(skin=(222, 186, 150), cloth=(160, 40, 36), trim=(90, 24, 20), linen=(232, 224, 200), linen2=(210, 200, 174),
                     metal=(194, 148, 70), belt=(80, 54, 32), helmet='pilos', armour='linothorax', greaves=True,
                     beard=(58, 42, 30), beard_style='short', hair=(58, 42, 30), hair_long=True),
    'spartan2': dict(skin=(206, 166, 128), cloth=(150, 36, 32), trim=(84, 22, 18), belt=(80, 54, 32), helmet=None, armour=None,
                     greaves=False, beard=(40, 30, 22), beard_style='long', hair=(40, 30, 22), hair_long=True),
    'hop_plain': dict(skin=SKIN, cloth=(206, 192, 158), trim=(120, 96, 64), belt=(96, 64, 38), helmet=None, armour=None,
                      greaves=False, beard=(70, 52, 38), beard_style='short', hair=(70, 52, 38)),
}

def _arm(pn, J, side, O, f, hand='hand', sleeve=True):
    sh_, el_, ha_ = J['sh' + side], J['el' + side], J['ha' + side]
    draw_part(pn, 'upper_arm', sh_, el_, f, O)
    draw_part(pn, 'forearm', el_, ha_, f, O)
    if sleeve and O.get('cloth'): draw_part(pn, 'sleeve', sh_, el_, f, O)
    if hand: draw_part(pn, hand, ha_, (ha_[0] + (ha_[0] - el_[0]), ha_[1] + (ha_[1] - el_[1])), f, O)

def _leg(pn, J, side, O, f):
    hip = (J['pelvis'][0] + (f if side == 'F' else -f) * R.HIP, J['pelvis'][1])
    draw_part(pn, 'thigh', hip, J['knee' + side], f, O)
    draw_part(pn, 'shin', J['knee' + side], J['foot' + side], f, O)
    if O.get('greaves'): draw_part(pn, 'greave', J['knee' + side], J['foot' + side], f, O)
    draw_part(pn, 'foot', J['foot' + side], None, f, O)

CLOSED_HELMETS = ('corinthian', 'great_helm', 'sallet_closed', 'armet', 'barbute_closed')
def helmet_open(name):
    """True if the forehead shows under this helmet ('_up' marks a closed helmet pushed up on the head)."""
    return name.endswith('_up') or not name.startswith(CLOSED_HELMETS)

def hoplite(pn, x, y, k, f=1, p='idle', out='hop_keeper', expr='determined', look=(0.7, 0), blink=0.0,
            spear_hand=None, spear_ang=None, spear_back=110, shield=True, shield_r=64, shield_dx=0.0, shadow=True,
            device=None, t=0.0, shield_fn=None, spear_fn=None, layer='all', hands_in=None, held_fn=None):
    """Greek hoplite on the cutout rig. Aspis on the back (left) forearm through the porpax, the hand on the antilabe
    hidden behind it; dory in the front hand, drawn before the hand so the fist wraps the shaft.
    spear_ang: radians, screen angle of the tip direction measured like props.dory (0 = toward +x).
    shield_fn(pn, cx, cy, r, f) and spear_fn(pn, gx, gy, ang, back) -> tip replace the flat props (3D props in the
    2.5D world). layer: 'all', 'spear' (only the spear, for drawing a whole rank's spears first) or 'body' (no spear)."""
    O = OUT2[out]
    if isinstance(p, str): p = R.POSES[p]
    p = dict(p); p['torso'] = p.get('torso', 0) + 1.0 * math.sin(t * 2.3 + x * 0.011)   # breathing
    # front on body: the anatomical left arm is on screen right, so the shield goes on whichever arm is screen right
    sS = 'F' if f == 1 else 'B'; sW = 'B' if sS == 'F' else 'F'
    J0 = R.joints(p, f)
    hands = {}
    if spear_hand is not None:     # (forward offset from the spear shoulder, height); forward = toward the facing side
        hands[sW] = (J0['sh' + sW][0] + f * spear_hand[0], spear_hand[1])
    if shield:   # shield forearm across the body toward the front, elbow low: the grip that carries the aspis
        hands[sS] = (J0['sh' + sS][0] + f * 30, J0['sh' + sS][1] + 34)
    if hands_in: hands.update(hands_in)
    J = R.joints(p, f, hands=hands or None)
    pn.push(x, y, k)
    if layer == 'spear':
        if spear_hand is not None:
            g = J['ha' + sW]; a_ = spear_ang if spear_ang is not None else -math.pi / 2
            (spear_fn or (lambda pn_, gx, gy, a, b: dory(pn_, gx, gy, a, back=b).get('tip')))(pn, g[0], g[1], a_, spear_back)
        pn.pop(); return dict(J=J, tip=None)
    if shadow: pn.ell(f * 6, 3, 48, 9, fill=(20, 14, 10, 70))
    # back to front: shield arm (hidden by the shield), legs, body, clothes, armour, spear, spear arm, shield, head
    if not held_fn: _arm(pn, J, sS, O, f, hand=None if shield else 'hand')
    _leg(pn, J, 'B', O, f); _leg(pn, J, 'F', O, f)
    nk, pe = J['neck'], J['pelvis']
    draw_part(pn, 'torso', nk, pe, f, O)
    if O.get('cloth'): draw_part(pn, 'chiton', nk, pe, f, O)
    if O.get('armour'): draw_part(pn, O['armour'], nk, pe, f, O)
    tip = None
    if held_fn:        # a wide object held open in both hands (book roll, map): arms behind it, only the fists wrap its edges
        for sd in (sS, sW):
            _arm(pn, J, sd, O, f, hand=None)
        held_fn(pn, J)
        for sd in (sS, sW):
            el, ha = J['el' + sd], J['ha' + sd]
            draw_part(pn, 'fist', ha, (ha[0] + (ha[0] - el[0]) * .3, ha[1] + 12), f, O)
    elif spear_hand is not None:
        g = J['ha' + sW]; a_ = spear_ang if spear_ang is not None else -math.pi / 2
        if layer != 'body':
            tip = spear_fn(pn, g[0], g[1], a_, spear_back) if spear_fn else dory(pn, g[0], g[1], a_, back=spear_back).get('tip')
        _arm(pn, J, sW, O, f, hand=None)
        el, ha = J['el' + sW], J['ha' + sW]
        draw_part(pn, 'fist', ha, (ha[0] + (ha[0] - el[0]), ha[1] + (ha[1] - el[1])), f, O)
    else:
        _arm(pn, J, sW, O, f, hand='hand')
    if shield:
        el, ha = J['el' + sS], J['ha' + sS]
        cx, cy = lerp(el[0], ha[0], 0.35) + f * shield_dx, lerp(el[1], ha[1], 0.35)
        if shield_fn: shield_fn(pn, cx, cy, shield_r, f)
        else: aspis(pn, cx, cy, shield_r, f, device=device)
    # head
    hx, hy = J['head']; r = L['head']
    if O.get('hair_long'):
        draw_part(pn, 'hair_long', (hx, hy), None, f, O)
    elif O.get('hair') and not O.get('helmet'):
        pn.circ(hx - f * 3, hy - 3, r + 3, fill=O['hair'], outline=INK, width=3)
    pn.circ(hx, hy, r, fill=O['skin'], outline=INK, width=3.4)
    if O.get('hair') and not O.get('helmet'):
        F2.fringe(pn, hx, hy, r, O['hair'])
    pn.push(hx, hy, r / 36)
    R.FACE_SKIN = O.get('skin')
    F2.face2(pn, f, expr, look, blink, 36, O.get('beard'), O.get('beard_style'), t, O.get('mark'), O.get('hair') or (60, 44, 32))
    pn.pop()
    if O.get('helmet'):
        tilt = math.radians(p.get('torso', 0) + p.get('head', 0)) * f
        draw_part(pn, O['helmet'], (hx, hy), None, f, O, ang=-tilt)
    # Keeper's curl over the brim: only for open faced or pushed up helmets. A closed helmet worn down (corinthian,
    # illyrian visor, great helm...) hides it, as it would in reality; he is then known by his clean shaven face and voice.
    if O.get('mark') == 'curl' and O.get('helmet') and helmet_open(O['helmet']):
        pn.push(hx, hy, r / 36); F2.forehead_curl(pn, f, O.get('hair') or (60, 44, 32)); pn.pop()
    pn.pop()
    W_ = lambda pt: (x + pt[0] * k, y + pt[1] * k)
    return dict(J=J, tip=W_(tip) if tip else None)

def exploded(pn, x, y, k=1.0, out='hop_keeper', cols=6, dx=150, dy=150, label=True):
    """Every part of an outfit laid out on its own, like a parts sheet."""
    O = OUT2[out]
    names = ['torso', 'chiton', 'linothorax', 'sleeve', 'upper_arm', 'forearm', 'hand', 'fist', 'thigh', 'shin', 'greave', 'foot']
    if O.get('helmet'): names.append(O['helmet'])
    for i, nm in enumerate(names):
        px, py = x + (i % cols) * dx, y + (i // cols) * dy
        oy = 110 if nm in ('pilos', 'corinthian_up') else (-40 if nm in ('torso', 'chiton', 'linothorax') else -10)
        pn.push(px, py + oy * k * 0.5, k * (0.9 if nm in ('torso', 'chiton', 'linothorax', 'pilos', 'corinthian_up') else 1.6))
        if nm in ('pilos', 'corinthian_up'): pn.circ(0, 0, 46, fill=O['skin'], outline=INK, width=3.4)
        draw_part(pn, nm, (0, 0), None, 1, O)
        pn.circ(0, 0, 3, fill=(208, 32, 32))
        pn.pop()
        if label: pn.text(px, py + dy * 0.5, nm.replace('_', ' ').upper(), 18, INK, 'Black')

if __name__ == '__main__' and '--write-parts' in sys.argv:
    print(write_parts())

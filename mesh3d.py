"""3D props for the 2.5D world: small polygon meshes drawn in the house style (flat tones, ink outlines).

A Mesh holds vertices (object space, rig units, Y down), faces (vertex index lists, each with a material) and
optional 3D polylines (cords, strings). draw_mesh projects it through a world25.Cam3 and paints it into a Pen:
faces sorted far to near, back faces culled unless the material is two sided, three tone toon shading with the
light from screen right, ink lines on silhouette, boundary and marked crease edges only (so the outline is the
same weight as the cutout rig's and never draws through nearer faces).

Every detail is geometry, so it is visible from any angle and at any distance: nothing switches on with size.
"""
import math
import numpy as np
from lib import *
from detail import shade, light

LIGHT = np.array([0.55, -0.55, -0.62]); LIGHT = LIGHT / np.linalg.norm(LIGHT)   # toward the light, camera space

MAT = {
    'bronze': dict(col=(196, 150, 72)), 'bronze_d': dict(col=(160, 116, 52)),
    'wood': dict(col=(150, 108, 66)), 'wood_l': dict(col=(186, 146, 96)), 'leather': dict(col=(112, 76, 46), two=True),
    'iron': dict(col=(112, 116, 124)), 'shaft': dict(col=(178, 140, 92)), 'stone': dict(col=(150, 146, 136)),
    'bronze2': dict(col=(196, 150, 72), two=True),
}

class Mesh:
    def __init__(s):
        s.V = []; s.F = []; s.L = []; s.creases = set(); s.dots = []
    def v(s, x, y, z): s.V.append((x, y, z)); return len(s.V) - 1
    def face(s, idx, mat, crease=()):
        s.F.append((tuple(idx), mat))
        for a, b in crease: s.creases.add((min(a, b), max(a, b)))
    def line(s, pts, col, w, normal=None, ink=True):
        """A cord or string (ink=True gives it an ink outline; False for surface marks such as fibres or text).
        With normal, it is drawn only when that side faces the camera."""
        s.L.append((np.array(pts, float), col, w, None if normal is None else np.array(normal, float), ink))
    def dot(s, p, r, mat, normal): s.dots.append((np.array(p, float), r, mat, np.array(normal, float)))
    def done(s):
        s.Vn = np.array(s.V, float)
        # edge -> faces map for silhouettes
        s.E = {}
        for fi, (idx, _) in enumerate(s.F):
            for i in range(len(idx)):
                a, b = idx[i], idx[(i + 1) % len(idx)]
                s.E.setdefault((min(a, b), max(a, b)), []).append(fi)
        return s

def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """Object to world rotation: roll about Z, then pitch about X, then yaw about Y (radians)."""
    cz, sz = math.cos(roll), math.sin(roll); cx, sx = math.cos(pitch), math.sin(pitch); cy, sy = math.cos(yaw), math.sin(yaw)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return Ry @ Rx @ Rz

def _to_cam(cam, P):
    dx = P[:, 0] - cam.x; dz = P[:, 2] - cam.z; co, si = math.cos(cam.yaw), math.sin(cam.yaw)
    return np.stack([dx * co + dz * si, P[:, 1] - cam.y, -dx * si + dz * co], 1)

def _tone(col, d):
    """Soft two sided toon ramp: lit edge toward the light, base in the middle, one shadow tone away from it."""
    d = max(-1.0, min(1.0, d))
    return light(col, 0.24 * (d - 0.35) / 0.65) if d > 0.35 else shade(col, 0.24 * (0.35 - d) / 1.35)

def draw_mesh(pn, cam, m, pos, R=None, scale=1.0, outline=3.0, overrides=None):
    """Draw mesh m at world position pos with rotation R into pen pn (screen design units, camera ignored)."""
    R = np.eye(3) if R is None else R
    Pw = (m.Vn * scale) @ R.T + np.asarray(pos, float)
    Pc = _to_cam(cam, Pw)
    if (Pc[:, 2] < 5).any(): return
    k = cam.F / Pc[:, 2]
    S = np.stack([cam.cx + Pc[:, 0] * k, cam.hy + Pc[:, 1] * k], 1)
    old = pn.T; pn.T = (1.0, 0.0, 0.0)
    # face normals and visibility in camera space
    info = []
    for fi, (idx, mat) in enumerate(m.F):
        p = Pc[list(idx)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if len(idx) > 3: n = n + np.cross(p[2] - p[0], p[3] - p[0])
        nn = np.linalg.norm(n)
        n = n / nn if nn > 1e-9 else n
        front = float(np.dot(n, -p.mean(0))) > 0
        info.append((n, front, float(p[:, 2].mean())))
    vis = [fi for fi, (idx, mat) in enumerate(m.F) if info[fi][1] or MAT[(overrides or {}).get(mat, mat)].get('two')]
    vis.sort(key=lambda fi: -info[fi][2])
    ow = outline * float(k.mean())
    for fi in vis:
        idx, mat = m.F[fi]; mat = (overrides or {}).get(mat, mat)
        n, front, _ = info[fi]
        if not front: n = -n
        col = _tone(MAT[mat]['col'], float(np.dot(n, LIGHT)))
        pts = [tuple(S[i]) for i in idx]
        pn.poly(pts, fill=col)
        for i in range(len(idx)):
            a, b = idx[i], idx[(i + 1) % len(idx)]; key = (min(a, b), max(a, b))
            fs = m.E[key]
            draw = len(fs) == 1 or key in m.creases or any(info[o][1] != info[fi][1] for o in fs if o != fi)
            if draw:
                pn.line([tuple(S[a]), tuple(S[b])], INK, max(0.8, ow * 0.85), caps=True)
    for p, r, mat, nrm in m.dots:     # rivets and studs: drawn when their face points at the camera
        pw = (p * scale) @ R.T + pos; nw = nrm @ R.T
        pc = _to_cam(cam, pw[None])[0]; nc = _to_cam(cam, (pw + nw)[None])[0] - pc
        if np.dot(nc, -pc) <= 0 or pc[2] < 5: continue
        kk = cam.F / pc[2]
        pn.circ(cam.cx + pc[0] * kk, cam.hy + pc[1] * kk, max(0.8, r * kk * scale), fill=light(MAT[mat]['col'], 0.3), outline=INK, width=max(0.4, 0.5 * kk))
    for pts, col, w, nrm, ink in m.L:     # cords and strings
        pw = (pts * scale) @ R.T + pos; pc = _to_cam(cam, pw)
        if nrm is not None:
            c0 = pc.mean(0); nc = _to_cam(cam, (pw.mean(0) + nrm @ R.T)[None])[0] - c0
            if np.dot(nc, -c0) <= 0: continue
        if (pc[:, 2] < 5).any(): continue
        kk = cam.F / pc[:, 2]
        sp = [(cam.cx + x * q, cam.hy + y * q) for (x, y, _), q in zip(pc, kk)]
        if ink: pn.line(sp, INK, (w + 1.6) * float(kk.mean()) * scale)
        pn.line(sp, col, w * float(kk.mean()) * scale)
    pn.T = old

# ---------------- builders ----------------
def lathe(m, prof, mat, seg=40, flip=False, crease_rings=()):
    """Revolve a profile of (r, z) points about the Z axis. Returns the ring index lists."""
    rings = []
    for (r, z) in prof:
        if r < 1e-6: rings.append([m.v(0, 0, z)] * seg); continue
        rings.append([m.v(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z) for i in range(seg)])
    for j in range(len(rings) - 1):
        A, B = rings[j], rings[j + 1]
        for i in range(seg):
            i2 = (i + 1) % seg
            q = [A[i], A[i2], B[i2], B[i]] if not flip else [A[i], B[i], B[i2], A[i2]]
            q2 = []
            for x in q:
                if x not in q2: q2.append(x)
            if len(q2) >= 3:
                cr = []
                if j in crease_rings: cr.append((A[i], A[i2]))
                if j + 1 in crease_rings: cr.append((B[i], B[i2]))
                m.face(q2, mat, cr)
    return rings

def aspis_mesh(r=64.0, depth=17.0, rim=8.0, seg=44, only_porpax=False):
    """Hoplite aspis (BM-P005): bronze faced dished bowl, flat offset rim (antyx), wooden interior, bronze porpax band
    at the centre and an antilabe cord near the rim. Object space: front faces -Z, centre at the origin,
    +X toward the antilabe side. About 0.85 m across at r 64."""
    m = Mesh(); rb = r - rim
    if only_porpax:     # just the band, to redraw over a forearm passing through it
        zc = -depth + 3; w = 6.0; n = 9; top = []; bot = []
        for i in range(n + 1):
            u = i / n; y = -15 + 30 * u; z = zc + 1 + 9 * math.sin(math.pi * u)
            top.append(m.v(-w, y, z)); bot.append(m.v(w, y, z))
        for i in range(n): m.face([top[i], top[i + 1], bot[i + 1], bot[i]], 'bronze2')
        return m.done()
    front = [(0, -depth), (rb * .3, -depth * .93), (rb * .6, -depth * .7), (rb * .85, -depth * .35), (rb, -1.0), (rb + .01, 0.0), (r, 0.0)]
    lathe(m, front, 'bronze', seg, crease_rings=(4,))
    # rim edge and back of the rim
    lathe(m, [(r, 0.0), (r, 2.2), (rb, 2.2)], 'bronze_d', seg, crease_rings=(0,))
    # interior (wood), facing +Z
    inner = [(rb, 2.2), (rb * .85, -depth * .35 + 2.6), (rb * .6, -depth * .7 + 2.8), (rb * .3, -depth * .93 + 3), (0, -depth + 3)]
    lathe(m, inner, 'wood', seg, crease_rings=(0,))
    # rivets round the rim front
    for i in range(18):
        a = 2 * math.pi * i / 18
        m.dot((math.cos(a) * (r - rim / 2), math.sin(a) * (r - rim / 2), -0.3), 1.3, 'bronze', (0, 0, -1))
    # porpax: bronze band at the centre, spanning across the forearm (along Y) so the arm passes under it along +X
    # toward the antilabe
    zc = -depth + 3; w = 6.0; n = 9
    top = []; bot = []
    for i in range(n + 1):
        u = i / n; y = -15 + 30 * u; z = zc + 1 + 9 * math.sin(math.pi * u)
        top.append(m.v(-w, y, z)); bot.append(m.v(w, y, z))
    for i in range(n): m.face([top[i], top[i + 1], bot[i + 1], bot[i]], 'bronze2')
    for y in (-15, 15): m.dot((0, y, zc + 1.2), 1.6, 'bronze', (0, 0, 1))
    # antilabe: cord grip near the rim, fixed at two rings
    xa = rb * .86; za = -depth * .3 + 3
    m.line([(xa, -13, za), (xa + 1, -9, za + 4.5), (xa + 1.5, 0, za + 6), (xa + 1, 9, za + 4.5), (xa, 13, za)], (196, 168, 112), 2.4, normal=(0, 0, 1))
    for y in (-13, 13): m.dot((xa, y, za), 1.8, 'bronze', (0, 0, 1))
    return m.done()

def _loft(m, sections, mat, close_ends=True, crease_ends=True):
    """Join cross sections (lists of 3D points, same count) into a closed tube."""
    rings = [[m.v(*p) for p in sec] for sec in sections]
    n = len(sections[0])
    for j in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            m.face([rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]], mat)
    if close_ends:
        m.face(rings[0][::-1], mat); m.face(rings[-1], mat)
    return rings

def dory_mesh(L=370.0, grip=110.0):
    """Dory (BM-P006): ash shaft, iron leaf head with socket, bronze sauroter. Object space along +X, origin at the
    grip, tip at +X (L - grip), butt at -grip. About 2.4 m long at L 370."""
    m = Mesh(); r = 2.0; n = 8
    x0, x1 = -grip + 34, L - grip - 46        # shaft between the sauroter and the head socket
    def ring(x, rr, sx=1.0, sy=1.0):
        return [(x, rr * sy * math.sin(2 * math.pi * i / n), rr * sx * math.cos(2 * math.pi * i / n)) for i in range(n)]
    _loft(m, [ring(x0, r), ring(x1, r)], 'shaft')
    # socket and leaf blade (lozenge section: wide in Y, thin in Z), iron
    hs = x1
    secs = [ring(hs, r + .6), ring(hs + 12, r + .3)]
    for t, w in ((0.0, 2.6), (0.25, 6.5), (0.55, 6.0), (0.85, 2.6), (1.0, 0.25)):
        x = hs + 12 + 34 * t; th = max(0.25, 1.6 * (1 - t) + .3)
        secs.append([(x, w * math.sin(2 * math.pi * i / n), th * math.cos(2 * math.pi * i / n)) for i in range(n)])
    _loft(m, secs, 'iron')
    # sauroter: four sided bronze spike at the butt
    b0 = x0; secs = []
    for t, w in ((0.0, 2.8), (0.2, 3.2), (0.3, 2.6), (1.0, 0.3)):
        x = b0 - 34 * t
        secs.append([(x, w, 0), (x, 0, w), (x, -w, 0), (x, 0, -w)])
    rings = [[m.v(*p) for p in sec] for sec in secs]
    for j in range(len(rings) - 1):
        for i in range(4):
            i2 = (i + 1) % 4
            m.face([rings[j][i2], rings[j][i], rings[j + 1][i], rings[j + 1][i2]], 'bronze')
    m.face(rings[0], 'bronze'); m.face(rings[-1][::-1], 'bronze')
    return m.done()

_CACHE = {}
def get(name):
    if name not in _CACHE:
        _CACHE[name] = {'aspis': aspis_mesh, 'dory': dory_mesh, 'porpax': lambda: aspis_mesh(only_porpax=True)}[name]()
    return _CACHE[name]

def dory_for(back):
    """Dory mesh with its grip `back` units from the butt end (cached per grip)."""
    key = ('dory', int(round(back)))
    if key not in _CACHE: _CACHE[key] = dory_mesh(grip=float(back))
    return _CACHE[key]

def pilos_mesh(r=48.0, h=66.0, seg=36):
    """Bronze pilos helmet (BM-P006): conical skull with a brim rib, open underneath. Object space: apex up (-Y),
    rim at Y 0, centred on the axis. Lathe about Y, built by revolving in XZ."""
    m = Mesh()
    prof = [(r + 3, 0.0), (r + 3, -5.0), (r, -6.0), (r * .82, -h * .42), (r * .5, -h * .78), (r * .18, -h * .97), (0.0, -h)]
    rings = []
    for (rr, y) in prof:
        rings.append([m.v(rr * math.cos(2 * math.pi * i / seg), y, rr * math.sin(2 * math.pi * i / seg)) for i in range(seg)] if rr > 0
                     else [m.v(0, y, 0)] * seg)
    for j in range(len(rings) - 1):
        A, B = rings[j], rings[j + 1]
        for i in range(seg):
            i2 = (i + 1) % seg
            q = [A[i], A[i2], B[i2], B[i]]; q2 = []
            for x in q:
                if x not in q2: q2.append(x)
            m.face(q2, 'bronze', [(A[i], A[i2])] if j in (1, 2) else [])
    # inside of the bowl (dark), two sided, slightly smaller
    inner = [m.v((r - 2) * math.cos(2 * math.pi * i / seg), 0.0, (r - 2) * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    top = m.v(0, -h + 6, 0)
    for i in range(seg):
        m.face([inner[(i + 1) % seg], inner[i], top], 'liner')
    m.dot((0, -h - 1, 0), 2.2, 'bronze', (0, -1, 0))
    return m.done()

def papyrus_mesh(w=70.0, h=52.0, r=6.0, seg=14):
    """Greek papyrus book roll held open (BM-P070): two rolled ends joined by the open sheet, text in columns.
    Object space: sheet faces -Z, rolls vertical at X = -w/2 and +w/2, centre at the origin."""
    m = Mesh()
    for sx in (-1, 1):
        cx = sx * w / 2
        top = [m.v(cx + r * math.cos(2 * math.pi * i / seg), -h / 2, r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        bot = [m.v(cx + r * math.cos(2 * math.pi * i / seg), h / 2, r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        for i in range(seg):
            i2 = (i + 1) % seg
            m.face([top[i], top[i2], bot[i2], bot[i]], 'papyrus')
        m.face(top[::-1], 'papyrus_d'); m.face(bot, 'papyrus_d')
    # open sheet, gently curved toward the reader
    n = 10; T = []; B = []
    for i in range(n + 1):
        u = i / n; x = -w / 2 + w * u; z = -r * 0.9 - 4 * math.sin(math.pi * u)
        T.append(m.v(x, -h / 2 + 3, z)); B.append(m.v(x, h / 2 - 3, z))
    for i in range(n):
        m.face([T[i], T[i + 1], B[i + 1], B[i]], 'papyrus2')
    for c in range(3):                        # three narrow text columns (strokes, not a transcription)
        x0 = -w / 2 + 12 + c * (w - 24) / 3
        for ln in range(9):
            y = -h / 2 + 9 + ln * 4.2
            u = (x0 + w / 2) / w
            z = -r * 0.9 - 4 * math.sin(math.pi * u) - 0.4
            m.line([(x0, y, z), (x0 + (w - 30) / 3 - 2 - (ln % 3) * 2, y, z)], (70, 56, 40), 0.9, normal=(0, 0, -1), ink=False)
    # outside (verso) seen by the viewer: plain papyrus with horizontal fibres and the sheet joins (kolleseis)
    def zs(xx): u = (xx + w / 2) / w; return -r * 0.9 - 4 * math.sin(math.pi * u) + 0.4
    for ln in range(7):
        y = -h / 2 + 7 + ln * 6.2
        xs = [-w / 2 + 4 + i * (w - 8) / 8 for i in range(9)]
        m.line([(xx, y + 0.6 * math.sin(xx * .3 + ln), zs(xx)) for xx in xs], (196, 176, 128), 0.7, normal=(0, 0, 1), ink=False)
    for xj in (-w / 6, w / 6):
        m.line([(xj, -h / 2 + 4, zs(xj)), (xj, h / 2 - 4, zs(xj))], (176, 154, 108), 1.1, normal=(0, 0, 1), ink=False)
    return m.done()

MAT.update({'liner': dict(col=(96, 66, 40)), 'papyrus': dict(col=(214, 196, 150)), 'papyrus_d': dict(col=(176, 156, 110)), 'papyrus2': dict(col=(228, 214, 172), two=True)})
_BUILD = {'pilos': pilos_mesh, 'papyrus': papyrus_mesh}
_get_old = get
def get(name):
    if name in _BUILD and name not in _CACHE: _CACHE[name] = _BUILD[name]()
    return _CACHE[name] if name in _CACHE else _get_old(name)

"""Emphasis marks: comic style bursts that point the eye at something (an open side, an impact, a key part).
Drawn in code in the house style (RUST fill, ink outline), inspired by the hand drawn marks in
assets/emphasis/reference_emphasis_marks.png. Each mark radiates out from an anchor point toward `ang`.

    burst(pn, x, y, s, ang, p, style)   p 0..1 pops it in (overshoot), t adds a gentle pulse
Styles: 'wedges' (three filled tapered wedges, the default), 'drops' (three filled teardrops), 'lines' (three
strokes), 'spikes' (three outlined spikes). Used for the open right side in E024 and from then on.
"""
import math
from lib import *

def _wedge(pn, x, y, ang, L, w0, w1, fill, outline=3.0):
    """Tapered wedge from a narrow end at (x, y) to a rounded broad end at length L along ang (degrees)."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    pts = [(x + nx * w0 / 2, y + ny * w0 / 2)]
    for i in range(13):            # rounded broad end
        b = math.pi / 2 - math.pi * i / 12
        pts.append((x + ux * L + (nx * math.sin(b) + ux * math.cos(b)) * w1 / 2 - ux * 0,
                    y + uy * L + (ny * math.sin(b) + uy * math.cos(b)) * w1 / 2))
    pts.append((x - nx * w0 / 2, y - ny * w0 / 2))
    pn.poly(pts[::-1], fill=fill, outline=INK if outline else None, width=outline)

def burst(pn, x, y, s=1.0, ang=180.0, p=1.0, style='wedges', t=0.0, col=RUST, gap=10.0):
    """Three marks fanning out from (x, y) toward ang (degrees, 0 = screen right, 90 = down)."""
    if p <= 0: return
    k = s * (eoback(min(1.0, p)) if p < 1 else 1.0) * (1 + 0.04 * math.sin(t * 7.0))
    spread = (-42, 0, 42); lens = (0.72, 1.0, 0.72)
    for d, ln in zip(spread, lens):
        a = ang + d; r = math.radians(a)
        x0, y0 = x + math.cos(r) * gap * k, y + math.sin(r) * gap * k
        L = 64 * ln * k
        if style == 'wedges':
            _wedge(pn, x0, y0, a, L, 4 * k, 22 * ln * k, col)
        elif style == 'drops':
            _wedge(pn, x0, y0, a, L * 0.85, 2 * k, 26 * ln * k, col)
        elif style == 'spikes':
            _wedge(pn, x0, y0, a, L, 3 * k, 18 * ln * k, (255, 250, 236), outline=3.4)
        else:   # lines
            pn.line([(x0, y0), (x0 + math.cos(r) * L, y0 + math.sin(r) * L)], INK, 7 * k)

def pop_env(t, t0, hold=0.7, pin=0.18, pout=0.16):
    """Scale envelope for a mark that pops on, holds, then pops off: 0 -> overshoot -> 1 ... 1 -> 0."""
    a = t - t0
    if a < 0 or a > pin + hold + pout: return 0.0
    if a < pin: return eoback(a / pin)
    if a < pin + hold: return 1.0
    u = (a - pin - hold) / pout
    return max(0.0, 1.0 + 0.12 * math.sin(math.pi * u) - u * 1.12)   # tiny swell, then gone

def ghost_rim(pn, cx, cy, r, s, col=RUST, width=6.0, n=18, t=0.0):
    """Minimal missing shield mark: one thin dashed ring the size of the shield that is not there.
    s is the pop scale from pop_env (0 hides it)."""
    if s <= 0.01: return
    rr = r * s; ph = t * 0.5
    for i in range(n):
        a0 = 2 * math.pi * i / n + ph; a1 = a0 + math.pi / n
        pn.line([(cx + rr * math.cos(a0), cy + rr * math.sin(a0)), (cx + rr * math.cos(a1), cy + rr * math.sin(a1))], col, width)

# ---------------- colour and symbol language (locked by the user from E024) ----------------
# Each meaning has a colour AND a shape, so it still reads for colour blind viewers. At most three of these colours on
# screen at once. Every mark pops on at its word and pops off (pop_env); none stays up after its moment.
RED = (214, 52, 44)        # danger, missing, exposed, wrong, myth
YELLOW = (250, 204, 40)    # covered, correct, success, proven, approved
BLUE = (84, 118, 158)      # estimate, hedge, uncertain (about, likely, disputed, sources suggest)
NEUTRAL = (255, 252, 244)  # look here, direction, reference (always with an ink outline)
STAMP_COL = dict(PROVEN=YELLOW, MYTH=RED, LIKELY=BLUE, DISPUTED=BLUE, VERIFY=BLUE)

def missing(pn, cx, cy, r, s, t=0.0, width=5.0):
    """RED dashed ring: something that should be there is not (the open side)."""
    ghost_rim(pn, cx, cy, r, s, col=RED, width=width, t=t)

def covered(pn, cx, cy, r, u, s=1.0, width=None):
    """YELLOW solid ring that closes (u 0..1 sweeps it shut): protected, correct, done. s is the pop scale.
    Line weight scales with the ring (about 8 percent of its radius, never under 8 px) and sits on a heavy ink
    outline, because yellow on bronze has little contrast."""
    if s <= 0.01 or u <= 0: return
    width = max(8.0, r * 0.08) if width is None else width
    rr = r * s; n = max(2, int(40 * u))
    pts = [(cx + rr * math.cos(-math.pi / 2 + 2 * math.pi * u * i / n), cy + rr * math.sin(-math.pi / 2 + 2 * math.pi * i * u / n)) for i in range(n + 1)]
    pn.line(pts, INK, width + 7); pn.line(pts, YELLOW, width)

def danger(pn, x, y, s, ang, p, t=0.0):
    """RED three wedge burst at an impact or threat, fanning out toward ang."""
    burst(pn, x, y, s, ang, p, 'wedges', t=t, col=RED)

def wrong(pn, a, b, u, width=16.0):
    """RED single bold slash drawn on from a to b (u 0..1): wrong, myth, not this."""
    if u <= 0: return
    e = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
    pn.line([a, e], INK, width + 6); pn.line([a, e], RED, width)

def hedge(pn, x0, x1, y, s, width=5.0):
    """BLUE dotted underline with a small tilde: an estimate or a hedge (about, likely)."""
    if s <= 0.01: return
    xe = lerp(x0, x1, min(1.0, s)); n = int((xe - x0) / 22)
    for i in range(n):
        pn.circ(x0 + 11 + i * 22, y, width * 1.2, fill=BLUE, outline=INK, width=2)
    if s >= 1: pn.text(x0 - 30, y - 8, '~', 64, BLUE, 'Black')

def look(pn, x0, y0, x1, y1, s, arm=34.0, width=6.0):
    """NEUTRAL four corner brackets around a part: look here."""
    if s <= 0.01: return
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2 * (1.25 - 0.25 * min(1, s)), (y1 - y0) / 2 * (1.25 - 0.25 * min(1, s))
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px, py = cx + sx * hx, cy + sy * hy
        pts = [(px, py - sy * arm), (px, py), (px - sx * arm, py)]
        pn.line(pts, INK, width + 4); pn.line(pts, NEUTRAL, width)

def direction(pn, x, y, ang, s, size=1.0, t=0.0):
    """NEUTRAL three chevrons pointing along ang (degrees), rippling forward: movement, which way."""
    if s <= 0.01: return
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    for i in range(3):
        k = size * s; off = (i - 1) * 34 * k + 6 * math.sin(t * 6 - i) * k
        cx_, cy_ = x + ux * off, y + uy * off
        pts = [(cx_ - ux * 14 * k + nx * 20 * k, cy_ - uy * 14 * k + ny * 20 * k), (cx_ + ux * 10 * k, cy_ + uy * 10 * k),
               (cx_ - ux * 14 * k - nx * 20 * k, cy_ - uy * 14 * k - ny * 20 * k)]
        pn.line(pts, INK, 13 * k); pn.line(pts, NEUTRAL, 8 * k)

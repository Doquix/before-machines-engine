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

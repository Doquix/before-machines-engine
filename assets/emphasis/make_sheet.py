"""Asset sheet for emphasis.py: every style, at two sizes and four directions."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')); sys.path.insert(0, ROOT)
from lib import *
import emphasis as EM, env
from PIL import Image
im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 80, 'EMPHASIS MARKS (emphasis.burst)', 44, INK, 'Black')
for r, style in enumerate(('wedges', 'drops', 'spikes', 'lines')):
    y = 300 + r * 380
    pn.text(540, y - 120, style.upper(), 34, INK, 'Black')
    for c, ang in enumerate((180, 0, -90, 90)):
        x = 140 + c * 260
        pn.circ(x, y, 6, fill=INK)
        EM.burst(pn, x, y, 1.4 if c < 2 else 1.0, ang, 1.0, style)
flatten(im, lay); im.convert('RGB').save(os.path.join(ROOT, 'assets', 'emphasis', 'emphasis_sheet.png')); print('ok')

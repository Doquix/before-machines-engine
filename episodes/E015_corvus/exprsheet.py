"""Expression and facial hair check sheets (docs/EXPRESSIONS.md): every face large, and small to test the fallback."""
import sys; sys.path.insert(0, '.')
from lib import *; from rig import *; import env
def head(pn, x, y, s, expr, beard=None, style=None, label=None, t=0.0):
    pn.push(x, y, s)
    pn.circ(0, 0, 46, fill=SKIN, outline=INK, width=3.4)
    pn.push(0, 0, 46 / 36); face(pn, 0, 0, 1, expr, (0.6, 0), 0, False, 36, beard, style, t); pn.pop()
    pn.pop()
    if label: pn.text(x, y + 46 * s + 26, label.upper(), 22, INK, 'Black', 'mm', True)
def sheet(path, items, s, cols, dx, dy, x0=110, y0=150, small=None):
    base = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    for i, it in enumerate(items):
        x = x0 + (i % cols) * dx; y = y0 + (i // cols) * dy
        head(pn, x, y, s, *it)
        if small: head(pn, x + 70 * s, y - 30 * s, small, it[0], it[1], it[2])
    flatten(base, lay); base.convert('RGB').save(path)
E = list(EXPR)
sheet('/tmp/expr_sheet.png', [(e, None, None, e) for e in E], 1.45, 4, 255, 238, x0=120, y0=140, small=0.42)
BC = (88, 64, 44)
sheet('/tmp/beard_sheet.png', [('neutral', BC, b, b) for b in BEARDS] + [('laughing', BC, 'full', 'full laughing'), ('terrified', BC, 'long', 'long terrified'),
      ('pain', (40, 32, 26), 'vandyke', 'vandyke pain')], 1.45, 4, 255, 300, x0=120, y0=150)

"""Sheet of the colour and symbol language (emphasis.py)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')); sys.path.insert(0, ROOT)
from lib import *
import emphasis as EM, env
im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 70, 'SYMBOL LANGUAGE', 46, INK, 'Black')
rows = [('MISSING, EXPOSED', 'red dashed ring', lambda x, y: EM.missing(pn, x, y, 70, 1.0)),
        ('DANGER, IMPACT', 'red burst', lambda x, y: EM.danger(pn, x + 40, y, 1.2, 180, 1.0)),
        ('WRONG, MYTH', 'red slash', lambda x, y: EM.wrong(pn, (x - 70, y - 60), (x + 70, y + 60), 1.0)),
        ('COVERED, CORRECT', 'yellow closed ring', lambda x, y: EM.covered(pn, x, y, 70, 1.0)),
        ('ESTIMATE, HEDGE', 'blue dotted line + ~', lambda x, y: EM.hedge(pn, x - 80, x + 100, y, 1.0)),
        ('LOOK HERE', 'white corner brackets', lambda x, y: EM.look(pn, x - 70, y - 50, x + 70, y + 50, 1.0)),
        ('DIRECTION', 'white chevrons', lambda x, y: EM.direction(pn, x, y, 0, 1.0, 1.4))]
for i, (lab, sub, fn) in enumerate(rows):
    y = 230 + i * 225
    fn(260, y)
    pn.text(480, y - 18, lab, 40, INK, 'Black', anchor='lm'); pn.text(480, y + 30, sub, 30, MUTED, 'Bold', anchor='lm')
flatten(im, lay); im.convert('RGB').save(os.path.join(ROOT, 'assets', 'emphasis', 'symbol_language.png')); print('ok')

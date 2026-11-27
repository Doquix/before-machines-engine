"""Face system v2 preview: the Keeper (no glasses, brow nick) in every expression, bearded Spartans, old vs new, phone size."""
import os, sys, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')); sys.path.insert(0, ROOT)
from lib import *
import rig as R, faces as FC, env
from PIL import Image

def head(pn, x, y, s, expr, skin=SKIN, hair=(70, 52, 38), beard=None, bs=None, mark=None, f=1, old=False, glasses=False):
    pn.push(x, y, s); r = 46
    pn.circ(-f * 3, -3, r + 3, fill=hair, outline=INK, width=3)
    pn.circ(0, 0, r, fill=skin, outline=INK, width=3.4)
    FC.fringe(pn, 0, 0, r, hair)
    pn.push(0, 0, r / 36); R.FACE_SKIN = skin
    if old: R.face(pn, 0, 0, f, expr, (0.6, 0), 0.0, glasses, 36, beard, bs)
    else: FC.face2(pn, f, expr, (0.6, 0), 0.0, 36, beard, bs, mark=mark)
    pn.pop(); pn.pop()

im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 56, 'FACES v2: THE KEEPER (no glasses, brow nick)', 36, INK, 'Black')
names = ['neutral', 'happy', 'laughing', 'proud', 'surprised', 'awe', 'confused', 'thinking', 'skeptical', 'smug', 'sly', 'bored',
         'determined', 'angry', 'worried', 'fear', 'terrified', 'pain', 'embarrassed', 'crying', 'exhausted', 'disgusted', 'seasick', 'neutral']
for i, n in enumerate(names[:24]):
    x = 100 + (i % 6) * 176; y = 200 + (i // 6) * 230
    head(pn, x, y, 1.55, n, mark='brow_nick')
    pn.text(x, y + 98, n.upper(), 20, INK, 'Black')
pn.text(540, 1150, 'BEARDED, SKIN TONES', 30, INK, 'Black')
for i, (n, sk, hc, bs) in enumerate([('determined', (228, 196, 160), (62, 46, 34), 'full'), ('angry', (206, 166, 128), (40, 30, 22), 'long'),
                                     ('fear', (214, 172, 132), (90, 66, 44), 'short'), ('embarrassed', (222, 186, 150), (58, 42, 30), 'short'),
                                     ('bored', (232, 196, 160), (110, 76, 44), 'full'), ('terrified', (190, 146, 108), (30, 24, 20), 'full')]):
    x = 100 + i * 176; head(pn, x, 1290, 1.55, n, skin=sk, hair=hc, beard=hc, bs=bs)
    pn.text(x, 1388, n.upper(), 20, INK, 'Black')
pn.text(270, 1470, 'OLD', 30, INK, 'Black'); pn.text(810, 1470, 'NEW', 30, INK, 'Black')
for j, n in enumerate(['neutral', 'fear']):
    head(pn, 160 + j * 220, 1600, 1.6, n, old=True, glasses=True)
    head(pn, 700 + j * 220, 1600, 1.6, n, mark='brow_nick')
pn.text(540, 1730, 'PHONE SIZE (as in a wide shot)', 26, INK, 'Black')
for i, n in enumerate(['neutral', 'happy', 'angry', 'fear', 'worried', 'surprised', 'bored', 'crying']):
    head(pn, 90 + i * 128, 1830, 0.62, n, mark='brow_nick')
flatten(im, lay)
out = os.path.join(ROOT, 'docs', 'reference', 'faces_v2_sheet.png'); im.convert('RGB').save(out); print(out)

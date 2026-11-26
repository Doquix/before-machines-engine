"""Action recipe sheets: fall and helmet_off, six frames each (anticipation, key, follow through, settle)."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from lib import *
import rig as R, rig_cutout as C, world25 as W25, mesh3d as M, actions as A, env
from PIL import Image
FLAT = W25.Cam3(0, 0, -3600, 0, F=3600, horizon=0, cx=0)
C.OUT2['spartan1_bare'] = dict(C.OUT2['spartan1'], helmet=None)

def hooks(x, y, k):
    wpt = lambda lx, ly, dz: (x + lx * k, y + ly * k, dz * k)
    return dict(shield_fn=lambda pn_, cx, cy, r, f: M.draw_mesh(pn_, FLAT, M.get('aspis'), wpt(cx, cy, -14),
                M.rot(-f * 0.22, 0, 0 if f == 1 else math.pi), scale=k * r / 64),
                spear_fn=lambda pn_, gx, gy, a, b: M.draw_mesh(pn_, FLAT, M.dory_for(b), wpt(gx, gy, -8), M.rot(0, 0, a), scale=k))

def sheet(name, times, draw):
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    pn.text(540, 70, name.upper().replace('_', ' '), 46, INK, 'Black')
    for i, t in enumerate(times):
        x = 190 + (i % 3) * 350; y = 780 + (i // 3) * 820
        pn.line([(x - 160, y), (x + 160, y)], INK, 3)
        draw(pn, x, y, t)
        pn.text(x, y + 40, f't {t:+.2f}', 26, INK, 'Bold')
    flatten(im, lay)
    out = os.path.join(ROOT, 'docs', 'reference', f'action_{name}.png'); im.convert('RGB').save(out); print(out)

def draw_fall(pn, x, y, t):
    k = 0.95; F_ = A.fall(t, 0.0, side=1)
    p = R.pose('brace', **{kk: v for kk, v in F_['pose'].items() if kk in R.POSES['brace']})
    def fn(p2):
        C.hoplite(p2, x, y, k, -1, p=p, out='hop_b', expr='terrified' if t > 0 else 'determined', spear_hand=None, **hooks(x, y, k))
    A.draw_rotated(pn, x, y, F_['deg'], fn)
sheet('fall', [-0.1, 0.06, 0.25, 0.45, 0.62, 0.9], draw_fall)

def draw_helm(pn, x, y, t):
    k = 0.95; H_ = A.helmet_off(t, 0.0, f=-1)
    out = 'spartan1' if H_['on_head'] else 'spartan1_bare'
    hands = {'F': H_['hand']} if H_['hand'] else None
    C.hoplite(pn, x, y, k, -1, out=out, expr='neutral', shield=False, hands_in=hands)
    if not H_['on_head']:
        hx, hy = H_['helmet']
        M.draw_mesh(pn, FLAT, M.get('pilos'), (x + hx * k, y + hy * k, -10), M.rot(*H_['rot']), scale=0.9 * k)
sheet('helmet_off', [0.1, 0.3, 0.5, 0.8, 1.1, 1.6], draw_helm)

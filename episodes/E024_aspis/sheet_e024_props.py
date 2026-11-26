"""E024 period props sheet: every outfit and prop of the episode, 3D props through mesh3d, tokens for the drift diagram."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from lib import *
import rig as R, rig_cutout as C, world25 as W25, mesh3d as M, props as PR, env

CAM.drift = 0; CAM.set(0)
SHEETCAM = W25.Cam3(0, 0, -3600, 0, F=3600, horizon=0, cx=0)   # world (x, y, 0) lands on screen (x, y) at scale 1

def hooks(x, y, k):
    wpt = lambda lx, ly, dz: (x + lx * k, y + ly * k, dz * k)
    def shield_fn(pn_, cx, cy, r, f):
        M.draw_mesh(pn_, SHEETCAM, M.get('aspis'), wpt(cx, cy, -14), M.rot(-f * 0.22, 0, 0 if f == 1 else math.pi), scale=k * r / 64)
    def spear_fn(pn_, gx, gy, a, back):
        M.draw_mesh(pn_, SHEETCAM, M.dory_for(back), wpt(gx, gy, -8), M.rot(0, 0, a), scale=k)
    return dict(shield_fn=shield_fn, spear_fn=spear_fn)

im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 64, 'E024 PERIOD PROPS', 46, INK, 'Black')
pn.text(540, 108, 'Mantinea, 418 BC  |  rig v2, 3D props', 24, INK, 'Bold')

# row 1: outfits
GY = 560; K = 0.92
row = [('hop_keeper', 'KEEPER'), ('hop_a', 'HOPLITE A'), ('hop_b', 'HOPLITE B'), ('spartan1', 'SPARTAN'), ('spartan2', 'SPARTAN, NO KIT')]
for i, (out, lab) in enumerate(row):
    x = 110 + i * 215
    if out == 'spartan2':
        C.hoplite(pn, x, GY, K, -1, p=R.pose('point'), out=out, expr='determined', shield=False)
    else:
        C.hoplite(pn, x, GY, K, -1, out=out, expr='neutral', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104,
                  **hooks(x, GY, K))
    pn.text(x, GY + 36, lab, 20, INK, 'Black')

# row 2: Keeper reading the book roll, dropped shield, dropped helmet, aspis interior
GY2 = 1060
x = 150; k = 1.0
def held(pn_, J):
    M.draw_mesh(pn_, SHEETCAM, M.get('papyrus'), (x, GY2 - 150 * k, -20 * k), M.rot(0, 0, 0), scale=1.55 * k)
C.hoplite(pn, x, GY2, k, -1, out='hop_keeper', expr='thinking', look=(0, 0.9), shield=False,
          hands_in={'F': (-54, -150), 'B': (54, -150)}, held_fn=held)
pn.text(x, GY2 + 36, 'BOOK ROLL', 20, INK, 'Black')
pn.rect(300, GY2 - 2, 1050, GY2 + 3, fill=(120, 100, 70))
M.draw_mesh(pn, SHEETCAM, M.get('aspis'), (450, GY2 - 22, 0), M.rot(0.3, math.radians(-72), 0), scale=1.0)
pn.text(450, GY2 + 36, 'DROPPED ASPIS', 20, INK, 'Black')
M.draw_mesh(pn, SHEETCAM, M.get('pilos'), (650, GY2 - 30, 0), M.rot(0.4, 0, math.radians(100)), scale=0.9)
pn.text(650, GY2 + 36, 'DROPPED PILOS', 20, INK, 'Black')
M.draw_mesh(pn, SHEETCAM, M.get('aspis'), (900, GY2 - 120, 0), M.rot(math.radians(150), math.radians(-6)), scale=1.4)
pn.text(900, GY2 + 36, 'PORPAX + ANTILABE', 20, INK, 'Black')

# row 3: top down tokens, before and after the drift
pn.text(540, 1200, 'TOP DOWN TOKENS (enemy up the screen)', 24, INK, 'Black')
for i in range(4):
    PR.phalanx_token(pn, 110 + i * 120, 1440, 0.85, open_side=1.0)
pn.text(330, 1530, 'OPEN ORDER: right sides bare', 20, INK, 'Bold')
for i in range(4):
    PR.phalanx_token(pn, 680 + i * 84, 1440, 0.85, open_side=0.0)
pn.text(780, 1530, 'DRIFTED: each right side tucked', 20, INK, 'Bold')
# scale bar (1 m = 154 units)
pn.line([(60, 1700), (60 + 154 * K, 1700)], INK, 3); pn.text(60 + 77 * K, 1724, '1 m (row 1)', 18, INK, 'Bold')
flatten(im, lay)
out = os.path.join(ROOT, 'docs', 'reference', 'e024_period_props.png')
im.convert('RGB').save(out); print(out)

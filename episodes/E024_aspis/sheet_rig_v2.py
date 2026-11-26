"""E024 rig test: old E017 rig against the new cutout rig (solid vector parts, head kept at a third of body height)."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'episodes', 'E017_sarissa')]
from lib import *
import rig as R, env
import rig_cutout as C
import sp as OLD

CAM.drift = 0; CAM.set(0)
im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 70, 'E024 RIG TEST', 46, INK, 'Black')
pn.text(540, 116, 'same skeleton and head size, solid vector parts', 26, INK, 'Bold')

# row 1: old against new, same scale and pose
GY = 700; K = 1.45
pn.text(270, 190, 'OLD (E017)', 30, INK, 'Black'); pn.text(800, 190, 'NEW (CUTOUT PARTS)', 30, RUST, 'Black')
R.figure(pn, 270, GY, K, 1, p=R.pose('idle', uaF=24, faF=16), out='hoplite', expr='determined')
C.hoplite(pn, 800, GY, K, 1, p=R.pose('idle', uaF=24, faF=16), out='hop_a', expr='determined', shield=False)
pn.text(540, GY + 60, 'kit off: the body itself', 24, INK, 'Bold')
pn.line([(540, 230), (540, GY + 20)], MUTED, 2)

# row 2: new rig action set (idle with spear grounded, walk, brace, overhand thrust)
GY2 = 1270; K2 = 1.0
xs = [140, 400, 660, 920]
C.hoplite(pn, xs[0], GY2, K2, -1, out='hop_keeper', expr='neutral', spear_hand=(6, -104), spear_ang=-math.pi / 2, spear_back=104)
C.hoplite(pn, xs[1], GY2, K2, -1, p=R.pose('walk'), out='hop_b', expr='determined', spear_hand=(10, -110),
          spear_ang=-math.pi / 2 - 0.22, spear_back=96)
C.hoplite(pn, xs[2], GY2, K2, -1, p=R.pose('brace'), out='hop_a', expr='determined', spear_hand=(22, -98),
          spear_ang=math.pi + 0.06, spear_back=140, shield_dx=6)
C.hoplite(pn, xs[3], GY2, K2, -1, p=R.pose('brace', torso=12, head=-6), out='hop_b', expr='angry', spear_hand=(40, -186),
          spear_ang=math.pi - 0.2, spear_back=130, shield_dx=8)
for x, t in zip(xs, ('IDLE', 'WALK', 'BRACE', 'THRUST')):
    pn.text(x, GY2 + 40, t, 24, INK, 'Black')

# scale bar: 1 m = 154 units at this scale (dory 2.4 m = 370 units)
bx = 60; by = GY2 + 90
pn.line([(bx, by), (bx + 154 * K2, by)], INK, 3); pn.line([(bx, by - 8), (bx, by + 8)], INK, 3)
pn.line([(bx + 154 * K2, by - 8), (bx + 154 * K2, by + 8)], INK, 3)
pn.text(bx + 77 * K2, by + 24, '1 m', 20, INK, 'Black')
pn.text(560, by + 4, 'aspis about 0.85 m across  |  man about 1.7 m', 22, INK, 'Bold', anchor='lm')

# row 3: the editable parts
pn.text(540, 1440, 'EDITABLE PARTS (parts/body_v2.svg, red dot = pivot)', 24, INK, 'Black')
C.exploded(pn, 115, 1570, 1.0, out='hop_keeper', cols=7, dx=142, dy=190)

flatten(im, lay)
out = os.path.join(ROOT, 'docs', 'reference', 'e024_rig_v2_sheet.png')
im.convert('RGB').save(out); print(out)

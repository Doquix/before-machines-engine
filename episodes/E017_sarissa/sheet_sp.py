"""E017 check sheet: phalangite with sarissa and pelta, hoplite with dory and aspis, props at three sizes."""
import math
from PIL import Image
from lib import *
from rig import *
import sp, env, props as PR
CAM.drift = 0; CAM.set(0)
im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
# row 1: phalangite poses
sp.phalangite(pn, 130, 640, 1.1, 1, 0.0, out='phalanx', expr='determined', back=120, L=380)
sp.phalangite(pn, 420, 640, 1.1, 1, 0.5, out='phalanx2', expr='neutral', back=120, L=380)
sp.phalangite(pn, 700, 640, 1.1, 1, upright=True, out='phalanx3', expr='happy', L=500)
sp.hoplite(pn, 930, 640, 1.1, -1, out='hoplite', expr='angry')
# row 2: walk + hoplite thrust + no shield
sp.phalangite(pn, 130, 1180, 1.1, 1, 0.0, p=pose('walk'), out='phalanx', back=120, L=380)
sp.hoplite(pn, 470, 1180, 1.1, 1, out='hoplite2', thrust=1.0, p=pose('brace'))
sp.phalangite(pn, 800, 1180, 1.1, 1, 0.0, shield=False, out='phalanx', expr='thinking', back=120, L=200)
# row 3: props at three sizes
PR.pelta(pn, 120, 1500, 30); PR.pelta(pn, 300, 1500, 70); PR.aspis(pn, 520, 1500, 90)
PR.aspis(pn, 700, 1500, 30)
PR.sarissa(pn, 300, 1760, 0.0, back=260, L=830 * 0.95)
PR.dory(pn, 300, 1850, 0.0, back=60, L=370)
pn.text(540, 80, 'E017 PERIOD PROPS', 44, INK, 'Black')
flatten(im, lay); im.convert('RGB').save('sheet_sp.png'); print('ok')

"""Three size check sheets for the E015 props (docs/PROP_DETAIL.md)."""
import sys; sys.path.insert(0, '.')
from lib import *; from rig import *; import cv, env
from render_cv import sword_held
def sheet(name, draw):
    base = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    draw(pn); flatten(base, lay); base.convert('RGB').save(name)
# 1: galley at three sizes, plus the bow at full screen
def g(pn):
    cv.galley(pn, 300, 260, 0.1, 0.3, 1, corvus_ang=72)
    cv.galley(pn, 520, 640, 0.42, 0.3, 1, corvus_ang=72)
    cv.galley(pn, -900, 1700, 2.2, 0.3, 1, corvus_ang=40, oars=True)
sheet('/tmp/ps_galley.png', g)
# 2: figure kit (scutum, helmet, sword) at three sizes
def f(pn):
    for x, y, k in ((130, 520, 0.45), (420, 820, 1.4)):
        figure(pn, x, y, k, 1, 'brace', 'legion', 'determined', held=lambda pn_, J: sword_held(pn_, J))
    figure(pn, 600, 1880, 4.2, 1, 'brace', 'legion', 'determined', held=lambda pn_, J: sword_held(pn_, J))
sheet('/tmp/ps_figure.png', f)
# 3: corvus close, spike and pestle
def c(pn):
    cv.corvus(pn, 260, 900, 1.0, 55, 1, ft=26)
    cv.spike_shape(pn, 300, 1150, math.pi / 2, 420)
    cv.pestle(pn, 800, 1300, 1.6, ang=math.pi, mortar=False)
    cv.spike_shape(pn, 900, 200, math.pi / 2, 60)
sheet('/tmp/ps_corvus.png', c)

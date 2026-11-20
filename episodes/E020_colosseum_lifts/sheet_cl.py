"""E020 check sheet: every period item, figures in full outfits, props at three sizes."""
import math
from PIL import Image
from lib import *
from rig import *
import cl, env, props as PR
CAM.drift = 0; CAM.set(0)
im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.text(540, 60, 'E020 PERIOD PROPS: COLOSSEUM LIFTS', 40, INK, 'Black')
# row 1: figures, every one different (face, hair, facial hair, skin, clothes)
y1 = 470
figure(pn, 95, y1, 1.0, 1, 'point', 'rkeeper', 'thinking', look=(0.9, 0))
for x_, o_, e_, ph_ in ((270, 'operae', 'determined', 0.0), (445, 'operae2', 'tired', 0.4), (620, 'operae3', 'determined', 0.7)):
    pn.line([(x_ + 20, y1 - 146), (x_ + 110, y1 - 146)], INK, 15); pn.line([(x_ + 20, y1 - 146), (x_ + 110, y1 - 146)], cl.OAK, 10)
    cl.pusher(pn, x_, y1, 1.0, 1, ph_, o_, e_)
figure(pn, 810, y1, 1.0, -1, 'idle', 'operae4', 'worried', look=(0.9, 0))
cl.venator(pn, 975, y1, 1.0, -1, ang=0.22)
for x_, t_ in ((95, 'KEEPER'), (270, 'CREW 1 exomis'), (445, 'CREW 2'), (620, 'CREW 3 exomis'), (810, 'CREW 4'), (975, 'VENATOR')):
    pn.text(x_, y1 + 40, t_, 18, MUTED, 'Bold')
# row 2: capstan two stories with crew, shaft with cage and trap door
y2 = 1180
cl.arena_floor(pn, 560, 600, 1060, gap=(760, 960))
cl.lift_shaft(pn, 860, 600, y2 + 10, w=230)
cl.pulley(pn, 860, 620)
top = cl.lift_cage(pn, 860, y2 - 120, 0.8, gate=0.0, inside=lambda p: cl.lion(p, 0, -6, 0.62, 1, gait='stand'))
cl.rope(pn, [(860, 642), top], 4.5)
cl.trapdoor(pn, 760, 560, 200, op=1.0, f=1)
cl.capstan(pn, 330, y2, 0.82, ang=0.4, rope_turns=0.6)
for lv in (0, 1):
    cl.pusher(pn, 230, y2 - lv * 246, 0.75, 1, 0.3 * lv, 'operae3' if lv else 'operae', bar_h=-170)
pn.line([(330 + 26, y2 - 0.82 * 300 - 60), (860 - 26, 642)], INK, 6.5); pn.line([(330 + 26, y2 - 0.82 * 300 - 60), (860 - 26, 642)], ROPE, 4)
pn.text(330, y2 + 40, 'CAPSTAN, 2 LEVELS', 18, MUTED, 'Bold'); pn.text(860, y2 + 40, 'SHAFT, CAGE, TRAP DOOR RAMP', 18, MUTED, 'Bold')
cl.torch(pn, 640, 1000, 0.3, 0.9)
# row 3: detailed cats
y3 = 1530
cl.lion(pn, 170, y3, 0.95, 1, gait='stand', t=0.4)
cl.lion(pn, 520, y3, 0.95, 1, gait='run', ph=0.3, expr='roar', t=0.2)
cl.tiger(pn, 870, y3 - 10, 0.95, 1, gait='leap', ph=0.45, expr='roar', t=0.1)
for i, op in enumerate((0, 0.5, 1.0)):
    cl.arena_floor(pn, 1700, 60 + i * 230, 60 + i * 230 + 200, gap=(110 + i * 230, 250 + i * 230), depth=30)
    cl.trapdoor(pn, 110 + i * 230, 1700, 140, op=op, f=1)
cl.venabulum(pn, 780, 1760, -0.05, back=120)
cl.lion(pn, 960, 1840, 0.4, -1, gait='crouch', expr='angry')
pn.text(540, 1890, 'cats, trap door 0 / 0.5 / 1, venabulum, capstan and cage at small size', 18, MUTED, 'Bold')
flatten(im, lay); im.convert('RGB').save('e020_period_props.png'); print('ok')

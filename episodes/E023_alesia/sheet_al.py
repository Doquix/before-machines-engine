"""E023 period prop sheet: two pages side by side, saved as e023_period_props.png."""
import math
from PIL import Image
import lib
lib.BLEND = True
from lib import *
from rig import *
import env, al, props as PR
import rig
rig.DEPTH_IK = True
CAM.drift = 0; CAM.set(0)
def page():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); return im, lay, Pen(lay, cam=False)
def lab(pn, x, y, t, sz=24): pn.text(x, y, t, sz, INK, 'Black', disp=True)

# ---- page 1: the siege line
im, lay, pn = page()
lab(pn, 540, 56, 'E023 PERIOD PROPS 1/2: THE ROMAN LINE', 38)
PR.siege_line_elevation(pn, 40, 1040, 560, 22, build=1.0)
lab(pn, 540, 600, 'RAMPART ~12 FT, BREASTWORK, CERVI, TOWERS ~80 FT APART (P054, P055)', 20)
L = []
PR.siege_line_section(pn, 960, 900, 26, labels=lambda n, p: L.append((n, p)))
for n, (x, y) in L: lab(pn, x, y, n, 18)
lab(pn, 540, 1140, 'SECTION, INNER LINE, TOWN TO THE LEFT (SIMPLIFIED)', 20)
for i in range(3): PR.cippus(pn, 140 + i * 70, 1480, 80, seed=i)
pn.line([(80, 1480), (340, 1480)], INK, 3)
lab(pn, 210, 1530, 'CIPPI (P056)', 22)
pn.rect(400, 1380, 760, 1500, fill=(150, 116, 78)); pn.line([(400, 1380), (760, 1380)], INK, 3)
PR.lilium(pn, 500, 1380, 120, cover=0.0); PR.lilium(pn, 670, 1380, 120, cover=1.0)
lab(pn, 580, 1530, 'LILIUM OPEN, COVERED (P057)', 22)
pn.rect(800, 1440, 1040, 1560, fill=(150, 116, 78)); pn.line([(800, 1440), (1040, 1440)], INK, 3)
PR.stimulus(pn, 880, 1440, 300); PR.stimulus(pn, 980, 1440, 300, cut=False)
lab(pn, 920, 1600, 'STIMULUS (P058)', 22)
PR.dolabra(pn, 90, 1760, -10, 280); PR.wicker_basket(pn, 560, 1700, 120, 90)
PR.camp_stool(pn, 820, 1840, 2.2)
lab(pn, 300, 1860, 'DOLABRA (P059)', 22); lab(pn, 560, 1860, 'BASKET', 22); lab(pn, 820, 1880, 'CAMP STOOL', 22)
flatten(im, lay); p1 = im.convert('RGB')

# ---- page 2: people
im, lay, pn = page()
lab(pn, 540, 56, 'E023 PERIOD PROPS 2/2: PEOPLE', 38)
pn.line([(30, 560), (1050, 560)], INK, 3)
al.legionary_dig(pn, 130, 560, 1.25, 'rleg23c', sw=0.0)
al.legionary_dig(pn, 350, 560, 1.25, 'rleg23c', sw=1.0)
al.legionary_basket(pn, 600, 560, 1.25)
al.legionary_wall(pn, 860, 560, 1.25)
lab(pn, 240, 600, 'DOLABRA UP, STRIKE', 20); lab(pn, 600, 600, 'BASKET ON SHOULDER', 20); lab(pn, 860, 600, 'SCUTUM (P065)', 20)
pn.line([(30, 1060), (1050, 1060)], INK, 3)
al.rider(pn, 300, 1060, 1.5, ph=0.3)
al.gaul_charge(pn, 720, 1060, 1.3, 'gaulr1', thrust=0.0)
al.gaul_charge(pn, 940, 1060, 1.3, 'gaulr2', thrust=1.0)
lab(pn, 300, 1100, 'GALLIC RIDER, HORNED SADDLE (P060)', 20); lab(pn, 830, 1100, 'RELIEF ARMY, LA TENE SHIELD (P064)', 20)
pn.line([(30, 1600), (1050, 1600)], INK, 3)
al.caesar(pn, 220, 1600, 1.45)
al.verc_surrender(pn, 520, 1600, 1.45, lay=0.0)
al.verc_surrender(pn, 760, 1600, 1.45, lay=1.0)
figure(pn, 990, 1600, 1.2, -1, pose('idle'), 'gaulr3', 'neutral')
lab(pn, 220, 1650, 'CAESAR (P061)', 22); lab(pn, 660, 1650, 'VERCINGETORIX (P062)', 22); lab(pn, 980, 1650, 'gaulr3', 20)
flatten(im, lay); p2 = im.convert('RGB')
out = Image.new('RGB', (2160, 1920)); out.paste(p1, (0, 0)); out.paste(p2, (1080, 0))
out.save('e023_period_props.png')
# before and after: the same holds with the old flat solver and the depth solver
im, lay, pn = page()
lab(pn, 540, 60, 'ARMS: FLAT SOLVER (LEFT) VS DEPTH SOLVER (RIGHT)', 30)
for row, fn in enumerate((lambda x, y: al.verc_surrender(pn, x, y, 1.6, lay=0.0), lambda x, y: al.legionary_basket(pn, x, y, 1.6),
                          lambda x, y: al.gaul_charge(pn, x, y, 1.6, 'gaulr1'))):
    y = 620 + row * 600
    pn.line([(30, y), (1050, y)], INK, 3)
    rig.DEPTH_IK = False; fn(270, y)
    rig.DEPTH_IK = True; fn(810, y)
flatten(im, lay); im.convert('RGB').save('e023_arm_fix.png'); print('ok')

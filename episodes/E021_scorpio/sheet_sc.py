"""E021 period prop sheet (BM-P034 to BM-P044): two pages side by side, saved as e021_period_props.png."""
import math
from PIL import Image
from lib import *
from rig import *
import env, sc, props as PR
CAM.drift = 0; CAM.set(0)
def page():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); return im, lay, Pen(lay, cam=False)
def lab(pn, x, y, t, sz=26): pn.text(x, y, t, sz, INK, 'Black', disp=True)

# ---- page 1: machine, crew, diagrams
im, lay, pn = page()
lab(pn, 540, 60, 'E021 PERIOD PROPS 1/2: SCORPIO AND CREW', 36)
sc.aimer(pn, 690, 520, 1.45, draw=1.0, bolt=True)
lab(pn, 300, 560, 'AIMER: L HAND STOCK, R HAND TRIGGER')
lab(pn, 300, 595, 'BM-P034, P037, P038 (rkeep21)', 22)
sc.winder(pn, 720, 1000, 1.45, winch_a=0.5, draw=0.5)
lab(pn, 300, 1040, 'CREWMAN: BOTH HANDS ON HANDSPIKES', 26)
lab(pn, 300, 1075, 'rcrew21', 22)
PR.scorpio(pn, 250, 1330, 1.0, draw=1.0, yaw=-38, pitch=22, bolt=True)
lab(pn, 250, 1365, 'OBLIQUE, FULL DRAW', 22)
PR.scorpio(pn, 250, 1640, 1.0, draw=0.0, slack=1.0, yaw=-38, pitch=22)
lab(pn, 250, 1675, 'RAIN: SLACK SPRINGS', 22)
PR.scorpio(pn, 720, 1260, 1.15, draw=1.0, yaw=0, pitch=90, stand=False, bolt=True)
lab(pn, 720, 1395, 'TOP VIEW, FULL DRAW', 22)
PR.scorpio(pn, 720, 1520, 1.15, draw=0.0, yaw=0, pitch=90, stand=False)
lab(pn, 720, 1640, 'TOP VIEW, AT REST', 22)
PR.catapult_bolt(pn, 470, 1760, 0.0, 300)
PR.catapult_bolt(pn, 830, 1760, 0.0, 120)
PR.catapult_bolt(pn, 960, 1760, 0.0, 50)
lab(pn, 640, 1820, 'BOLT (BM-P036) AT THREE SIZES', 22)
flatten(im, lay); p1 = im.convert('RGB')

# ---- page 2: spring cutaway, bolt head, Gauls, Avaricum, Hod Hill, modern
im, lay, pn = page()
lab(pn, 540, 60, 'E021 PERIOD PROPS 2/2: SPRING, GAUL, BRITAIN, MODERN', 34)
PR.skein_diagram(pn, 250, 330, 0.36, twist=0.3, labels=True, lab_p=1.0)
PR.skein_diagram(pn, 560, 330, 0.36, twist=1.0, arm=40, labels=False)
lab(pn, 400, 500, 'SPRING (BM-P035): RELAXED, WOUND', 22)
PR.bolt_head_insert(pn, 880, 300, 0.32, rust=0.7)
lab(pn, 880, 350, 'HOD HILL HEAD, 88 mm', 22)
PR.rubber_ecu(pn, 880, 470, 0.32, wind=0.8)
lab(pn, 880, 590, 'RUBBER ECU', 22)
# Avaricum strip: wall, tower, Gauls on the wall walk
PR.murus_gallicus(pn, 40, 1040, 820, 1100, walk=False)
PR.gallic_tower(pn, 120, 820, 0.7)
for i, (o, th) in enumerate((('gaul1', 0.3), ('gaul2', 0.9), ('gaul3', 0.0))):
    sc.gaul(pn, 330 + i * 190, 846, 1.0, o, throw=th, pitch=(i == 1))
PR.breastwork(pn, 40, 1040, 820)
lab(pn, 430, 1130, 'MURUS GALLICUS, HIDE TOWER, GAULS (BM-P039, P040)', 22)
PR.siege_terrace(pn, 840, 1060, 900, 940, 1100)
PR.siege_tower(pn, 960, 900, 0.5)
lab(pn, 950, 1160, 'TERRACE, TOWER (P041)', 20)
PR.roundhouse(pn, 230, 1500, 0.9, palisade=True, bolts=3)
lab(pn, 230, 1545, 'ROUNDHOUSE (P042)', 22)
PR.hodhill_plan(pn, 560, 1400, 0.33, line_p=1.0)
lab(pn, 560, 1560, 'HOD HILL PLAN (SIMPLIFIED)', 22)
sc.keeper_plane(pn, 880, 1620, 1.3, wind=0.6)
lab(pn, 880, 1660, 'KEEPER, MODERN (P043, P044)', 20)
PR.toy_plane(pn, 560, 1760, 2.4, prop_a=0.6, wind=0.9)
lab(pn, 560, 1840, 'TOY PLANE, WOUND', 22)
flatten(im, lay); p2 = im.convert('RGB')
out = Image.new('RGB', (2160, 1920)); out.paste(p1, (0, 0)); out.paste(p2, (1080, 0))
out.save('e021_period_props.png'); out.resize((1080, 960)).save('e021_period_props_small.png'); print('ok')

"""E022 period prop sheet (BM-P045 to BM-P053): two pages side by side, saved as e022_period_props.png."""
import math
from PIL import Image
from lib import *
from rig import *
import env, yk, props as PR
CAM.drift = 0; CAM.set(0)
def page():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); return im, lay, Pen(lay, cam=False)
def lab(pn, x, y, t, sz=26): pn.text(x, y, t, sz, INK, 'Black', disp=True)

# ---- page 1: the ice house complex and its diagrams
im, lay, pn = page()
lab(pn, 540, 60, 'E022 PERIOD PROPS 1/2: YAKHCHAL', 38)
# elevation: dome behind, shade wall, pool in front (day)
s = 26
PR.yakhchal_dome(pn, 760, 560, s)
PR.shade_wall(pn, 40, 640, 560, s, h=9.0)
PR.ice_pool(pn, 40, 640, 590, 690, skew=40, water=1.0, ice=0.0, night=0.0)
lab(pn, 540, 730, 'DOME (P045), SHADE WALL WITH NICHES (P046), POOL (P047)', 22)
# night: pool freezing
PR.ice_pool(pn, 60, 500, 790, 900, skew=30, water=1.0, ice=0.55, stars=40, night=1.0)
PR.ice_pool(pn, 560, 1020, 790, 900, skew=30, water=1.0, ice=1.0, crack=1.0, night=1.0)
lab(pn, 280, 935, 'NIGHT: SKIN OF ICE', 22); lab(pn, 790, 935, 'SHEET CUT INTO BLOCKS', 22)
# section of dome and pit
PR.yakhchal_section(pn, 300, 1300, 15, fill=0.75, cold=0.6)
lab(pn, 300, 1450, 'SECTION: PIT, ICE AND STRAW (P045, P049)', 22)
# wall end on and layers diagram
PR.wall_end_section(pn, 680, 1300, 26, h=9.0)
lab(pn, 680, 1340, 'WALL END ON', 22)
PR.pool_layers_section(pn, 780, 960, 1150, 260, layers=4.6, pour=0.6)
lab(pn, 880, 1340, '5 TO 10 cm A NIGHT', 22)
# qanat
PR.qanat_section(pn, 60, 1020, 1760, flow=0.8, hill=250)
lab(pn, 540, 1860, 'QANAT TO THE POOL (P048), VERTICAL SCALE EXAGGERATED', 22)
flatten(im, lay); p1 = im.convert('RGB')

# ---- page 2: people, tools, blocks, bowl
im, lay, pn = page()
lab(pn, 540, 60, 'E022 PERIOD PROPS 2/2: WORKERS AND TOOLS', 38)
pn.line([(30, 520), (1050, 520)], INK, 3)
yk.worker_pick(pn, 150, 520, 1.25, 'yakh1', sw=0.0)
yk.worker_pick(pn, 400, 520, 1.25, 'yakh1', sw=1.0)
yk.worker_carry(pn, 650, 520, 1.25, 'yakh2')
yk.worker_spade(pn, 900, 520, 1.25, 'yakh3')
lab(pn, 270, 556, 'PICK: UP, STRIKE', 22)
lab(pn, 650, 556, 'BLOCK CARRY', 22)
lab(pn, 900, 556, 'SPADE', 22)
pn.line([(30, 1020), (1050, 1020)], INK, 3)
yk.keeper_bowl(pn, 180, 1020, 1.45)
yk.keeper_point(pn, 430, 1020, 1.45)
figure(pn, 680, 1020, 1.45, -1, pose('idle'), 'yakh2', 'neutral')
figure(pn, 900, 1020, 1.45, 1, pose('idle'), 'yakh3', 'thinking')
lab(pn, 300, 1060, 'KEEPER pkeeper (P050, P053)', 22); lab(pn, 790, 1060, 'yakh2, yakh3 (P050)', 22)
PR.kolang(pn, 80, 1180, -8, 300); PR.bil(pn, 80, 1300, -4, 320, k=1.0)
lab(pn, 300, 1365, 'KOLANG AND BIL (P051) FULL SIZE', 22)
PR.ice_block(pn, 720, 1220, 220, 140, straw=0.8)
PR.ice_block(pn, 920, 1230, 90, 58)
PR.ice_block(pn, 1010, 1240, 36, 24)
lab(pn, 820, 1365, 'ICE BLOCK (P049) AT THREE SIZES', 22)
PR.sherbet_bowl(pn, 240, 1560, 120)
PR.sherbet_bowl(pn, 480, 1600, 40)
lab(pn, 330, 1720, 'SHERBET BOWL (P053)', 22)
night = [(28, 30, 48)]
pn.rect(600, 1430, 1040, 1820, fill=(26, 30, 52), outline=INK, width=3)
PR.stars(pn, 3, 40, 1440, 1660, x0=610, x1=1030)
PR.ice_pool(pn, 640, 1000, 1720, 1790, skew=20, water=1.0, ice=0.3, night=1.0)
PR.radiation_arrows(pn, 660, 1000, 1720, 1470, p=1.0)
lab(pn, 820, 1850, 'HEAT LEAVES UPWARD (DIAGRAM)', 22)
flatten(im, lay); p2 = im.convert('RGB')
out = Image.new('RGB', (2160, 1920)); out.paste(p1, (0, 0)); out.paste(p2, (1080, 0))
out.save('e022_period_props.png'); out.resize((1080, 960)).save('e022_period_props_small.png'); print('ok')

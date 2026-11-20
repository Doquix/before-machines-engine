"""E019 check sheets: smith with tongs (idle, mid plunge, full plunge), blade states, cross section, trough, forge, tools."""
import math
from PIL import Image
from lib import *
from rig import *
import kt, env, props as PR
CAM.drift = 0; CAM.set(0)

def sheet1():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    pn.text(540, 70, 'E019 POSE SHEET', 44, INK, 'Black')
    for i, pl in enumerate((0.0, 0.5, 1.0)):
        y = 560 + i * 560; x = 260
        pn.line([(0, y), (1080, y)], INK, 3)
        PR.quench_trough(pn, x + 360, y, 1.4, front=False)
        kt.smith_tongs(pn, x, y, 1.4, 1, pl, heat=1.0 if pl < 1 else 0.3, hard=1.0 if pl >= 1 else 0.0, clay=1.0)
        PR.quench_trough(pn, x + 360, y, 1.4, front=True, ripple=pl)
        pn.text(140, y - 470, f'plunge {pl}', 30, INK, 'Black')
    figure(pn, 960, 1700, 1.2, -1, 'point', 'kkeeper', 'happy', blink=0)
    figure(pn, 960, 1150, 1.0, -1, 'idle', 'kaji2', 'neutral', blink=0)
    flatten(im, lay); return im.convert('RGB')

def sheet2():
    im = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
    pn.text(540, 70, 'E019 PERIOD PROPS', 44, INK, 'Black')
    rows = [('FORGED: SLIGHT CURVE', dict(sori=0.4 * PR.K_SORI)), ('CLAY COAT', dict(sori=0.4 * PR.K_SORI, clay=1.0)),
            ('HEATED', dict(sori=0.4 * PR.K_SORI, clay=1.0, heat=1.0)), ('FIRST SECONDS: DIPS', dict(sori=-0.5 * PR.K_SORI, clay=1.0, hard=0.6)),
            ('QUENCHED: FULL CURVE', dict(sori=PR.K_SORI, clay=0.0, hard=1.0)), ('POLISHED: HAMON', dict(sori=PR.K_SORI, polish=1.0, hamon=1.0, habaki=True))]
    for i, (lab, kw) in enumerate(rows):
        y = 190 + i * 150
        PR.katana(pn, 230, y, 5.0, 0.0, 1, **kw)
        pn.text(540, y - 60, lab, 24, MUTED, 'Black')
    # small sizes
    PR.katana(pn, 80, 1120, 1.6, 0.0, 1, sori=PR.K_SORI, polish=1, hamon=1)
    PR.katana(pn, 80, 1170, 2.6, 0.0, 1, sori=PR.K_SORI, polish=1, hamon=1)
    # cross sections
    for i, (kw, lab) in enumerate(((dict(), 'BARE'), (dict(clay=1.0), 'CLAY'), (dict(clay=1.0, hard=1.0, swell=1.0, arrows=1.0), 'EDGE HARD'))):
        PR.katana_section(pn, 640 + i * 150, 1150, s=4.0, **kw)
        pn.text(640 + i * 150, 1260, lab, 22, INK, 'Black')
    # forge with bellows, tongs in the fire, trough, spatula
    F_ = PR.forge_hearth(pn, 300, 1820, 1.5, glow=1.0, bellows=0.5)
    PR.tongs(pn, (40, 1660), (F_['fire'][0] - 60, F_['fire'][1]))
    PR.katana(pn, F_['fire'][0] - 54, F_['fire'][1] + 2, 1.5, 0.0, 1, sori=0.4 * PR.K_SORI, clay=1.0, heat=0.8)
    pn.line([(560, 1820), (1080, 1820)], INK, 3)
    PR.quench_trough(pn, 820, 1820, 1.4, front=False, ripple=1.0, t=0.3)
    PR.quench_trough(pn, 820, 1820, 1.4, front=True)
    PR.steam(pn, 820, 1740, 0.8, 0.0, 1.0, 200)
    PR.hera(pn, 640, 1420, -0.3, 2.0)
    pn.text(760, 1500, 'HERA (CLAY SPATULA)', 22, INK, 'Black')
    flatten(im, lay); return im.convert('RGB')

a = sheet1(); b = sheet2()
o = Image.new('RGB', (2160, 1920)); o.paste(a, (0, 0)); o.paste(b, (1080, 0))
o.save('e019_period_props.png'); o.resize((1080, 960)).save('sheet_small.png'); print('ok')

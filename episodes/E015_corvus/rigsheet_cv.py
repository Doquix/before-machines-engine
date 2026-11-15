from lib import *; from rig import *
import env
base = env.get('parch').convert('RGBA'); lay = new_layer(); pn = Pen(lay, cam=False)
pn.rect(-10, 1300, 1090, 1930, fill=(206, 190, 158))
for i, (o, p, e) in enumerate((('legion', 'idle', 'smug'), ('legion2', 'brace', 'determined'), ('legion3', 'walk', 'neutral'), ('rower', 'pull', 'worried'), ('punic', 'point', 'happy'), ('punic2', 'cower', 'fear'))):
    x = 120 + (i % 3) * 420; y = 700 if i < 3 else 1300
    figure(pn, x if i<3 else x, y, 1.6, 1, p, o, e)
flatten(base, lay); base.convert('RGB').save('rig_sheet_cv.png')

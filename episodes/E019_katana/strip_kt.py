import sys
from PIL import Image, ImageDraw
sys.argv = ['x', 'T']
import render_kt as R
def strip(ts, name, crop=(0, 250, 1080, 1350)):
    ims = [R.frame(t).crop(crop).resize((270, int(270 * (crop[3] - crop[1]) / (crop[2] - crop[0])))) for t in ts]
    o = Image.new('RGB', (270 * len(ims), ims[0].height), 'white'); d = ImageDraw.Draw(o)
    for i, im in enumerate(ims): o.paste(im, (270 * i, 0)); d.text((270 * i + 4, 4), f'{ts[i]:.2f}', fill='red')
    o.save(name)
T = R.T
strip([0.0, 0.3, T['made'] - 0.3, T['made'], T['made'] + 0.2, T['made'] + 0.4, T['made'] + 0.7, T['tub0']], 'strip_lift.png', crop=(0, 450, 1080, 1450))
strip([T['s6'], T['plunges'] - 0.2, T['plunges'], T['plunges'] + 0.15, T['plunges'] + 0.3, T['plunges'] + 0.6, T['plunges'] + 1.0, T['s7'] - 0.05], 'strip_plunge.png', crop=(0, 450, 1080, 1450))

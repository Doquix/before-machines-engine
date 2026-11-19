import sys
from PIL import Image, ImageDraw
sys.argv = ['x', 'T']
import render_mb as R
def strip(ts, name, crop=(0, 250, 1080, 1350)):
    ims = [R.frame(t).crop(crop).resize((270, int(270 * (crop[3] - crop[1]) / (crop[2] - crop[0])))) for t in ts]
    o = Image.new('RGB', (270 * len(ims), ims[0].height), 'white'); d = ImageDraw.Draw(o)
    for i, im in enumerate(ims): o.paste(im, (270 * i, 0)); d.text((270 * i + 4, 4), f'{ts[i]:.2f}', fill='red')
    o.save(name)
T = R.T
strip([T['how'] - 0.1, T['how'] + 0.3, T['far'] + 0.4, T['mongol1'], T['rel1'] - 0.2, T['rel1'] + 0.034, T['rel1'] + 0.1, T['rel1'] + 0.3], 'strip_shot.png')
strip([T['shoot7'] - 0.3, T['shoot7'], T['shoot7'] + 0.3, T['rel6'] - 0.1, T['rel6'] + 0.034, T['rel6'] + 0.13, T['rel6'] + 0.3, T['rel6'] + 0.7], 'strip_gallop.png')
strip([T['bends'] - 0.1, T['bends'] + 0.2, T['back10'], T['back10'] + 0.3, T['itself'], T['itself'] + 0.2, T['even'], T['draw11'] + 0.2], 'strip_string.png')

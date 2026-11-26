"""E024 2.5D test: a hoplite phalanx on the Mantinea plain, camera dollies in and orbits slightly.
Figures are the approved cutout rig v2 (flat billboards); depth, parallax, haze and focus come from world25."""
import math, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from lib import *
import rig as R, rig_cutout as C, world25 as W25

OUT = '/tmp/e024_25d'; os.makedirs(OUT, exist_ok=True)
SKY = (238, 224, 190)
sc = W25.Scene(sky_top=(146, 176, 206), sky_bot=SKY)
sc.ridge(42000, 5200, (120, 134, 160), seed=3)
sc.ridge(20000, 1700, (138, 146, 156), seed=5)
sc.ridge(7500, 260, (176, 160, 112), seed=8)
sc.ground((200, 176, 116), (188, 164, 104))
sc.tufts(900, -5000, 5000, 300, 9000, (150, 128, 76), seed=11)
sc.tufts(60, -900, 900, 140, 420, (120, 100, 58), seed=12, size=2.6)   # foreground grass, out of focus

OUTS = ['hop_a', 'hop_b', 'hop_a', 'hop_keeper', 'hop_b', 'hop_a', 'hop_b']
def hop(out, front, i, r):
    def draw(pn, sx, sy, k):
        t = 0.0
        if front:
            C.hoplite(pn, sx, sy, k, -1, p=R.pose('brace'), out=out, expr='determined', spear_hand=(22, -98),
                      spear_ang=math.pi + 0.06, spear_back=140, shield_dx=6, t=t)
        else:
            C.hoplite(pn, sx, sy, k, -1, out=out, expr='neutral', spear_hand=(6, -104),
                      spear_ang=-math.pi / 2, spear_back=104, t=t)
    return draw
for r in range(3):                      # three ranks, rank spacing about 1 m
    for i in range(7):
        X = (i - 3) * 100 + r * 18
        sc.card(X, 1400 + r * 154, hop(OUTS[(i + r) % len(OUTS)], r == 0, i, r))

T, FPS = 4.0, 30
N = int(T * FPS)
for n in range(N):
    u = eio(n / (N - 1))
    cam = W25.orbit(0, -150, 1400, lerp(3600, 1450, u), lerp(-0.24, 0.14, u), F=3600, horizon=980, eye=-175)
    sc.render(cam).save(f'{OUT}/f{n:04d}.png')
    if n in (0, N // 2, N - 1): print('frame', n, flush=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{OUT}/f%04d.png', '-c:v', 'libx264',
                '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(HERE, 'test_25d.mp4')], check=True)
print('done')

"""E024 check: the 3D aspis and dory turning (front, edge, interior with porpax and antilabe)."""
import math, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..')))
from lib import *
import world25 as W25, mesh3d as M
from PIL import Image
OUT = '/tmp/e024_tt'; os.makedirs(OUT, exist_ok=True)
cam = W25.Cam3(0, -150, -700, 0, F=2400, horizon=860)
N = 90
for n in range(N):
    u = eio(n / (N - 1)); yaw = math.radians(lerp(-20, 200, u))
    im = Image.new('RGBA', (W, H), PARCH + (255,)); lay = new_layer(); pn = Pen(lay, cam=False)
    M.draw_mesh(pn, cam, M.get('aspis'), (0, -260, 0), M.rot(yaw, math.radians(-8)))
    M.draw_mesh(pn, cam, M.dory_for(110), (-40, 170, 0), M.rot(yaw * 0.5, 0, 0), scale=0.75)
    pn.text(540, 1500, 'ASPIS  |  DORY', 44, INK, 'Black')
    flatten(im, lay); im.convert('RGB').save(f'{OUT}/f{n:04d}.png')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{OUT}/f%04d.png', '-c:v', 'libx264', '-preset', 'veryfast',
                '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(HERE, 'aspis_turntable.mp4')], check=True)
print('done')

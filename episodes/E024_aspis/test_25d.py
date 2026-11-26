"""E024 2.5D test: a hoplite phalanx on the Mantinea plain, camera dollies in and orbits (capped at 15 degrees).
Figures are the approved cutout rig v2 (flat billboards); shields and spears are 3D meshes (mesh3d); depth,
parallax, haze and focus come from world25. Every detail is drawn at every distance (no popping)."""
import math, os, sys, subprocess, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT)
from lib import *
import rig as R, rig_cutout as C, world25 as W25, mesh3d as M

OUT = '/tmp/e024_25d'; os.makedirs(OUT, exist_ok=True)
sc = W25.Scene(sky_top=(146, 176, 206), sky_bot=(238, 224, 190))
sc.ridge(42000, 5200, (112, 126, 156), seed=3)
sc.ridge(22000, 2600, (122, 132, 140), seed=5)
sc.ridge(9000, 650, (160, 148, 104), seed=8)
sc.ground((200, 176, 116), (188, 164, 104))
rnd = random.Random(4)
for i in range(34):                       # oak groves on the plain, both sides and behind
    X = rnd.choice([-1, 1]) * rnd.uniform(350, 2400); Z = rnd.uniform(2600, 9000)
    sc.card(X, Z, W25.oak(sc, seed=i, size=rnd.uniform(.85, 1.25)))
for i in range(70):
    X = rnd.uniform(-1600, 1600); Z = rnd.uniform(-400, 3000)
    if 900 < Z < 2000 and abs(X) < 500: continue
    sc.card(X, Z, W25.rock(sc, seed=i, size=rnd.uniform(.35, 1.1)))
sc.tufts(1100, -5000, 5000, 300, 9000, (150, 128, 76), seed=11)
sc.tufts(60, -900, 900, 140, 420, (120, 100, 58), seed=12, size=2.6)

OUTS = ['hop_a', 'hop_b', 'hop_a', 'hop_keeper', 'hop_b', 'hop_a', 'hop_b']
def rank_draw(Xs, Z, outs, front):
    def draw(pn, cam):
        co, si = math.cos(cam.yaw), math.sin(cam.yaw)
        def member(X, out, layer):
            pr = cam.proj(X, 0, Z)
            if pr is None: return
            sx, sy, k, zr = pr
            wpt = lambda lx, ly, dz: (X + lx * co, ly, Z + lx * si + dz)
            def shield_fn(pn_, cx, cy, r, f):
                M.draw_mesh(pn_, cam, M.get('aspis'), wpt(cx, cy, -14), M.rot(-f * 0.22, 0, 0 if f == 1 else math.pi), scale=r / 64)
            def spear_fn(pn_, gx, gy, a, back):
                M.draw_mesh(pn_, cam, M.dory_for(back), wpt(gx, gy, -8), M.rot(0, 0, a)); return None
            kw = dict(shield_fn=shield_fn, spear_fn=spear_fn, layer=layer)
            if front:
                C.hoplite(pn, sx, sy, k, -1, p=R.pose('brace', torso=8, head=-4), out=out, expr='determined', spear_hand=(40, -186),
                          spear_ang=math.pi - 0.2, spear_back=130, shield_dx=8, **kw)
            else:
                C.hoplite(pn, sx, sy, k, -1, out=out, expr='neutral', spear_hand=(6, -104),
                          spear_ang=-math.pi / 2, spear_back=104, **kw)
        for X, out in zip(Xs, outs): member(X, out, 'spear')           # all spears first
        for X, out in sorted(zip(Xs, outs), key=lambda q: -q[0]):       # bodies right to left: each shield overlaps its right neighbour
            member(X, out, 'body')
    return draw
for r in range(3):                                  # three ranks, about 1 m apart
    Xs = [(i - 3) * 100 + r * 18 for i in range(7)]
    outs = [OUTS[(i + r) % len(OUTS)] for i in range(7)]
    sc.group(0, 1400 + r * 154, rank_draw(Xs, 1400 + r * 154, outs, r == 0))

T, FPS = 4.0, 30
N = int(sys.argv[1]) if len(sys.argv) > 1 else int(T * FPS)
for n in range(N):
    u = eio(n / max(1, N - 1))
    cam = W25.orbit(0, -150, 1400, lerp(3600, 1450, u), lerp(-0.26, 0.22, u), F=3600, horizon=1100, eye=-175)
    sc.render(cam).save(f'{OUT}/f{n:04d}.png')
if N == int(T * FPS):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{OUT}/f%04d.png', '-c:v', 'libx264',
                    '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(HERE, 'test_25d.mp4')], check=True)
print('done')

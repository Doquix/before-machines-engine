"""Motion test (reference for the 12 principles): one sarissa thrust at three levels.
Row A: linear, arms only.  Row B: E017 strike() as shipped.  Row C: all principles (keyed easing, anticipation in the
whole body, planted feet by leg IK, overlap via damped springs on torso, head, pelta and shaft, hold, settle).
Run from a build folder holding the engine modules and sp.py:
  python3 motion_test_sp.py sheet
  python3 motion_test_sp.py video | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -crf 18 -pix_fmt yuv420p motion_test.mp4
Reference output: docs/reference/e017_thrust_motion_test.png"""
import sys, math
import numpy as np
from PIL import Image
from lib import *
from rig import *
import env as E
import sp
from props import sarissa, pelta, SARISSA_L

ROW_H = 640
K = 1.25
X0 = 250
CYC = 2.6
HZ = FOLLOW_HZ

# ---------------- the three performances (thrust 0 = rest, 1 = full extension) ----------------
HIT = 1.0
def thrust_A(t):   # linear: no wind up, no hold, even spacing
    return keys(t, [(0.62, 0, lin), (HIT, 1, lin), (1.55, 0, lin)])

def strike(t, t_hit, wind=0.16, hold=0.18, back=0.4):   # verbatim from E017 render_sp.py
    if t < t_hit - wind - 0.12: return 0.0
    if t < t_hit - 0.12: return -back * eio(P(t, t_hit - wind - 0.12, wind))
    if t < t_hit: return lerp(-back, 1.0, ei2(P(t, t_hit - 0.12, 0.12)))
    if t < t_hit + hold: return 1.0
    return lerp(1.0, 0.25, eio(P(t, t_hit + hold, 0.4)))
def thrust_B(t): return strike(t, HIT)

def thrust_C(t):   # anticipation 9 f, drive 5 f accelerating, hold 7 f, recover 15 f, settle via springs
    return keys(t, [(0.55, 0, lin), (0.83, -0.35, eio), (HIT, 1.0, ei2), (1.24, 1.0, lin), (1.74, 0.0, eio)])

TS = np.arange(0, CYC, 1 / HZ)
def precompute():
    th = np.array([thrust_C(t) for t in TS])
    body = follow(th, 3.2, 0.55)              # weight and lean follow the arms, about 2 frames late
    lean = 6 + 9 * body                      # torso angle, brace base 6 deg
    head_follow = follow(lean, 2.6, 0.5)      # head lags the torso
    drop = 4 + 4 * np.clip(body, 0, None)    # stance sits a little, loads more on the lunge        # front knee loads on the lunge
    shx = 12 * body + 100 * np.sin(np.radians(lean))
    pel = follow(shx, 2.2, 0.32)              # pelta on its strap swings behind the shoulder and settles
    hand = 38 * th + 16 * body
    shaft = follow(hand, 5.5, 0.22)           # long ash shaft: the point whips a little on the stop
    return dict(th=th, body=body, lean=lean, head=head_follow - lean, drop=drop,
                pdx=np.clip(pel - shx, -16, 16), flex=6 + np.clip((shaft - hand) * 0.35, -9, 9))
PC = precompute()
def at(name, t): return float(np.interp(t, TS, PC[name]))

# ---------------- figure with planted feet ----------------
BR = pose('brace', torso=6, head=0)

def thruster(pn, x, y, t, th, body=0.0, lean=6.0, head=0.0, drop=0.0, pdx=0.0, flex=6.0, expr='determined', reach=46):
    p = dict(BR); p['torso'] = lean + 1.2 * math.sin(t * 2.3); p['head'] = head
    dx = 12 * body
    p.update(plant_legs(BR, dx, drop, spread=14))   # wider fighting stance, feet planted
    # hands: same two handed hold as sp.pike_hands, carried forward by the arms (th) and the body (dx)
    bx = -12 + reach * th + dx; by = -92 + drop * 0.6
    hands = {'B': (bx, by), 'F': (bx + 52, by)}
    info = {}
    def mid(pn_, J):
        nk, sh = J['neck'], J['shF']
        pelta(pn_, sh[0] + 4 - pdx, sh[1] + 22 + abs(pdx) * 0.25, 40, 1, strap_to=(nk[0], nk[1] + 2))
    def held(pn_, J):
        g = J['haB']
        info.update(sarissa(pn_, g[0], g[1], 0.0, back=240, L=SARISSA_L, flex=flex))
    J = figure(pn, x, y, K, 1, p, 'phalanx', expr, look=(1.0, 0), blink=blink_at(t, 0.3),
               hands=hands, held=held, mid=mid, f_behind=True)
    tip = info.get('tip', (0, 0))
    return (x + tip[0] * K, y + tip[1] * K), (x + J['haB'][0] * K, y + J['haB'][1] * K)

ROWS = [('LINEAR', 'arms only, even spacing, no wind up'),
        ('E017 NOW', 'wind up and hold, arms only'),
        ('ALL 12 APPLIED', 'body drives, parts lag and settle')]

_BG = {}
def row_bg(i):
    if i not in _BG:
        im = E.get('plain').crop((0, 700, W, 700 + ROW_H)).convert('RGBA')
        _BG[i] = im
    return _BG[i]

def draw_row(base, pn, i, t, trails, label_speed):
    oy = i * ROW_H; gy = oy + 520
    base.paste(row_bg(i), (0, oy))
    pn.rect(0, gy - 6, W, oy + ROW_H, fill=(200, 176, 116))
    pn.line([(0, gy - 6), (W, gy - 6)], (150, 126, 76), 3)
    if i == 0: tip, hand = thruster(pn, X0, gy, t, thrust_A(t))
    elif i == 1:
        th = thrust_B(t); p_lean = 6 + 6 * th
        tip, hand = thruster(pn, X0, gy, t, th, lean=p_lean)
    else:
        th = at('th', t)
        ex = 'angry' if HIT - 0.12 <= t < 1.45 else 'determined'
        tip, hand = thruster(pn, X0, gy, t, th, at('body', t), at('lean', t), at('head', t), at('drop', t), at('pdx', t),
                             at('flex', t), ex)
    trails[i].append((tip, hand))
    for j, (tp, hd) in enumerate(trails[i]):   # spacing trail of the rear hand, one dot per frame
        pn.circ(hd[0], gy + 60, 5, fill=(170, 60, 40, 220))
    pn.text(W - 40, gy + 96, 'one dot per frame: close dots = slow, wide gaps = fast', 24, (90, 60, 30), 'Bold', 'rm', True)
    # label
    pn.rect(28, oy + 26, 28 + 44 + 27 * len(ROWS[i][0]), oy + 86, fill=(30, 24, 18, 215), r=12)
    pn.text(48, oy + 56, ROWS[i][0], 40, (246, 178, 52), 'Black', 'lm', True)
    pn.text(48, oy + 112, ROWS[i][1], 30, (40, 30, 22), 'Bold', 'lm', True)
    if label_speed: pn.text(W - 40, oy + 56, label_speed, 34, (40, 30, 22), 'Black', 'rm', True)
    if i: pn.line([(0, oy), (W, oy)], (30, 24, 18), 6)

def render(t, trails, label_speed=''):
    CAM.drift = 0.0; CAM.set(0)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay, cam=False)
    for i in range(3): draw_row(base, pn, i, t, trails, label_speed)
    flatten(base, lay)
    return base.convert('RGB')

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        for i, t in enumerate([0.5, 0.83, 0.97, 1.04, 1.2, 1.6, 2.0]):
            render(t, [[], [], []]).save(f'motion_sheet_{i}.png')
    elif mode == 'video':
        out = sys.stdout.buffer
        segs = [(1.0, ''), (1.0, ''), (0.5, 'HALF SPEED')]
        for spd, lab in segs:
            trails = [[], [], []]
            n = int(round(CYC / spd * FPS))
            for fi in range(n):
                t = fi / FPS * spd
                out.write(render(t, trails, lab).tobytes())

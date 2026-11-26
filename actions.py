"""Action recipes (render skill, gate 2): tested physical actions reused across episodes instead of motion invented
inside an episode. Each recipe returns what the scene needs at time t (pose overrides, a whole body rotation about the
feet, prop positions, event times for SFX and effects). Reference sheets: docs/reference/action_<name>.png.

fall:        hit, recoil, knees give, the whole body topples sideways about the feet with gravity, impact, bounce, settle.
helmet_off:  the hand reaches the brim, lifts the helmet off and out to the side, lowers it and lets go; it falls,
             lands on its rim, tips onto its side and rocks to rest.
draw_rotated: draw a figure on its own layer and rotate it about a screen point (used by fall).
"""
import math
from PIL import Image
from lib import *

def draw_rotated(pn, px, py, deg, fn):
    """Draw fn(pen) on a fresh layer with pn's transform, rotate it deg (counterclockwise) about design point
    (px, py) in pn's local space, and composite it onto pn's image."""
    if abs(deg) < 0.05:
        fn(pn); return
    tmp = Image.new('RGBA', pn.img.size)
    p2 = Pen(tmp, cam=pn.cam); p2.T = pn.T; p2.stack = list(pn.stack)
    fn(p2)
    X, Y = pn.xy(px, py)
    tmp = tmp.rotate(deg, resample=Image.BICUBIC, center=(X, Y))
    pn.img.alpha_composite(tmp)

def fall(t, t_hit, side=1, dur=0.5, max_deg=84.0):
    """side +1 topples to screen left (counterclockwise), -1 to screen right.
    Returns dict(deg, pose, t_impact, impact) where pose holds joint overrides for rig poses."""
    a = t - t_hit
    t_imp = t_hit + 0.12 + dur
    if a < 0: return dict(deg=0.0, pose={}, t_impact=t_imp, impact=False)
    recoil = eo3(clamp(a / 0.12)) * (1 - clamp((a - 0.12) / 0.25))
    u = clamp((a - 0.12) / dur)
    deg = max_deg * ei2(u)                       # gravity: accelerates into the ground
    if u >= 1:                                   # impact, one small bounce, settle
        b = a - 0.12 - dur
        deg = max_deg - 7 * math.sin(math.pi * clamp(b / 0.2)) * (1 if b < 0.2 else 0)
    knees = eo3(clamp((a - 0.05) / 0.3))
    pose = dict(torso=-14 * recoil + 10 * knees, head=-10 * recoil + 8 * u,
                uaF=14 + 70 * recoil + 40 * u, faF=6 + 60 * recoil, uaB=-14 + 30 * recoil, faB=-6 + 20 * recoil,
                thF=5 + 18 * knees, shF=-24 * knees, thB=-5 + 10 * knees, shB=-16 * knees)
    return dict(deg=side * deg, pose=pose, t_impact=t_imp, impact=u >= 1)

def helmet_off(t, t0, f=-1, ground_y=0.0, release=0.85):
    """Hand (the screen side arm given by f) to the brim, lift off and out, lower, let go, fall, tip, rest.
    Coordinates in figure local units (feet at 0,0; Y down). Returns dict(on_head, hand, helmet, rot, t_land).
    helmet: rim centre of the helmet (local); rot: (yaw, pitch, roll) for mesh3d.rot."""
    a = t - t0
    head_rim = (0.0, -240.0)                     # pilos brim on the head (head centre -218, brim 22 above)
    rest = (f * 34.0, -104.0)
    grab = (f * 40.0, -222.0)
    up = (f * 84.0, -238.0)
    low = (f * 86.0, -150.0)
    keys = [(0.0, rest), (0.25, grab), (0.5, up), (0.8, low)]
    def K(x):
        if x <= 0: return rest
        for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
            if x < tb:
                u = eio((x - ta) / (tb - ta)); return (lerp(pa[0], pb[0], u), lerp(pa[1], pb[1], u))
        return low
    hand = K(a)
    if a < 0.25:
        return dict(on_head=True, hand=hand if a > 0 else None, helmet=head_rim, rot=(0, 0, 0), t_land=None)
    if a < release:
        u = eio(clamp((a - 0.25) / 0.25))
        hx, hy = hand
        hel = (lerp(head_rim[0], hx + f * 6, u), lerp(head_rim[1], hy - 2, u))
        return dict(on_head=False, hand=hand, helmet=hel, rot=(0.0, 0.0, f * 0.35 * u), t_land=None)
    # let go: falls from the hand, lands on its rim, tips onto its side, rocks
    hx, hy = K(release)
    x0, y0 = hx + f * 6, hy - 2
    fall_t = 0.38; d = a - release
    t_land = t0 + release + fall_t
    if d < fall_t:
        u = ei2(d / fall_t)
        return dict(on_head=False, hand=low if d < 0.15 else rest, helmet=(x0 + f * 10 * u, lerp(y0, ground_y, u)),
                    rot=(0.0, 0.0, f * 0.35), t_land=t_land)
    e = d - fall_t
    tip = eo3(clamp(e / 0.3))
    rock = 0.18 * math.exp(-e * 5) * math.sin(e * 18) if e > 0.3 else 0.0
    return dict(on_head=False, hand=rest, helmet=(x0 + f * (10 + 18 * tip), ground_y - 4 * (1 - tip)),
                rot=(-0.6, -0.6 * tip, f * (0.35 + 1.25 * tip) + rock), t_land=t_land)

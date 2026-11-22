"""E021 Roman scorpio: figures that operate the scorpio, Gallic defenders, the modern Keeper with his toy plane.
CARRY lines (period library BM-P034, BM-P039, BM-P043) are in each docstring."""
import math
from lib import *
from rig import *
import props as PR

def _loc(pt, x, y, k): return ((pt[0] - x) / k, (pt[1] - y) / k)

def aimer(pn, sx, sy, k, out='rkeep21', draw=1.0, trigger=0.0, expr='determined', t=0.0, bolt=True, yaw=-8, pitch=16,
          scorp=True, look=(0.9, 0.0), stand_dx=-215, slack=0.0, twist=0.0, bolt_out=None, aim=0.0):
    """Scorpio with its aimer. CARRY (BM-P034): the aimer stands at the rear of the stock, LEFT hand (front arm F) flat
    on the stock behind the slider, RIGHT hand (back arm B) on the trigger lever; body leans slightly into the machine.
    Depiction: no Republican picture of a crew; posture after Vitruvius 10.10 and Schramm's Saalburg reconstruction.
    (sx, sy) is the ground point under the scorpio stand; the figure stands stand_dx units behind it."""
    R = PR.scorpio(pn, sx, sy, k, draw=draw, bolt=bolt, trigger=trigger, yaw=yaw, pitch=pitch, slack=slack, twist=twist,
                   bolt_out=bolt_out, aim=aim, H0=92) if scorp else None
    fx, fy = sx + stand_dx * k, sy
    hands = {'F': _loc(R['stock'], fx, fy, k), 'B': _loc(R['trigger'], fx, fy, k)} if R else None
    p = pose('hold', torso=6 + 1.2 * math.sin(t * 2.3), head=4)
    J = figure(pn, fx, fy, k, 1, p, out, expr, look=look, blink=blink_at(t, 0.4), hands=hands)
    return R

def winder(pn, sx, sy, k, out='rcrew21', winch_a=0.0, draw=0.5, expr='determined', t=0.0, yaw=-8, pitch=16, bolt=False):
    """Scorpio in the oblique crew view with the crewman at the rear windlass. CARRY: BOTH hands on two neighbouring
    handspikes of the near windlass wheel at waist height, standing to the side of the stock, knees bent, leaning back
    against the pull (the winch drags the slider and string back)."""
    R = PR.scorpio(pn, sx, sy, k, draw=draw, winch_a=winch_a, yaw=yaw, pitch=pitch, bolt=bolt, H0=92)
    pr = PR.Proj(yaw, pitch, PR.CM_U)
    def spoke(a_):   # near wheel handspike end in world screen space (machine not tilted)
        p3 = (-108 + math.cos(a_) * 17, -13, -5 + math.sin(a_) * 17 + 92)
        v = pr.v(p3); return (sx + v[0] * k, sy + v[1] * k)
    g1, g2 = spoke(winch_a), spoke(winch_a + math.pi / 2)
    fx, fy = R['winch'][0] - 62 * k, sy + 10 * k
    hands = {'F': _loc(g1, fx, fy, k), 'B': _loc(g2, fx, fy, k)}
    p = pose('pull', torso=-10 + 3 * math.sin(winch_a * 2), head=4)
    figure(pn, fx, fy, k, 1, p, out, expr, blink=blink_at(t, 1.3), hands=hands)
    return R

def gaul(pn, x, y, k, out='gaul1', throw=0.0, lump=True, pitch=False, expr='determined', t=0.0, f=-1, hit=0.0):
    """Gallic defender at Avaricum throwing tallow or pitch onto the fire (Caesar 7.25). CARRY (BM-P039): the lump is
    held in the RIGHT hand (back arm B); throw 0..1 goes from the wind up (lump behind the head side) to the release
    (arm forward and down); the free hand reaches forward for balance. hit 0..1 slumps the figure back (no gore)."""
    up = (f * -76, -226); fwd = (f * 42, -150)
    if throw < 0.5: g = lerp2_((f * 26, -132), up, eio(throw / 0.5))
    else: g = lerp2_(up, fwd, ei2((throw - 0.5) / 0.5))
    p = pose('reach', torso=lerp(-10, 14, throw) - 26 * hit, head=-4 - 10 * hit, thF=14, thB=-12)
    hands = {'B': g, 'F': (f * 60, -150 + 40 * hit)}
    J = figure(pn, x, y, k, f, p, out, expr if hit < 0.3 else 'fear', blink=blink_at(t, x * 0.01), hands=hands)
    if lump and throw < 0.78:     # small object in the fist: drawn over the sleeve so it reads
        PR.tallow_lump(pn, x + J['haB'][0] * k, y + (J['haB'][1] - 3) * k, 11 * k, pitch)
    return J

def keeper_plane(pn, x, y, k, wind=0.0, prop_a=0.0, launch=0.0, expr='happy', t=0.0, out='kmod'):
    """Modern Keeper with the rubber powered plane. CARRY (BM-P043): LEFT hand (front arm F) holds the fuselage under
    the wing at chest height, RIGHT index finger (back arm B) on the propeller; launch 0..1 pushes the left hand forward
    and up and lets go (the plane is then drawn by the scene)."""
    gx, gy = lerp(30, 104, eio(launch)), lerp(-142, -176, eio(launch))
    def held(pn_, J):
        if launch < 0.85:
            R = PR.toy_plane(pn_, J['haF'][0] - 4 * 1.3, J['haF'][1] + 2, 1.3, prop_a, wind, ang=math.radians(-8 * launch))
            held.R = R
    held.R = None
    hub_local = (gx + 62, gy + 1)
    hands = {'F': (gx, gy), 'B': hub_local if launch < 0.15 else (-34, -126)}
    p = pose('hold', torso=-2 + 6 * launch, head=6)
    figure(pn, x, y, k, 1, p, out, expr, blink=blink_at(t, 0.2), hands=hands, held=held)
    return held.R

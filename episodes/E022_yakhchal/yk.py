"""E022 Persian yakhchal: ice house workers and the Keeper with their tools and loads.
CARRY lines (period library BM-P050 to BM-P053) are in each docstring. Figure local units: origin at the feet,
y negative is up; waist about -90, chest about -135, shoulders about -150."""
import math
from lib import *
from rig import *
import props as PR

def _loc(pt, x, y, k): return ((pt[0] - x) / k, (pt[1] - y) / k)

PICK_L = 135.0     # about 90 cm haft at 0.66 cm per unit

def pick_geom(sw, f=1):
    """Haft end (local) and angle for a pick swing: sw 0 = wound up (haft over the back shoulder, head up and back),
    1 = strike (hands low in front, head in the ice ahead of the feet). Arc through a breakdown pose."""
    keys = [(0.0, (-14, -168), -112), (0.5, (6, -150), -20), (1.0, (30, -112), 50)]
    if sw <= 0.5: a, b, u = keys[0], keys[1], sw / 0.5
    else: a, b, u = keys[1], keys[2], (sw - 0.5) / 0.5
    ex = lerp(a[1][0], b[1][0], u); ey = lerp(a[1][1], b[1][1], u); ang = lerp(a[2], b[2], u)
    if f < 0: ex = -ex; ang = 180 - ang
    return (ex, ey), ang

def worker_pick(pn, x, y, k, out='yakh1', sw=0.0, expr='determined', t=0.0, f=1):
    """Worker chopping the pool ice into blocks with a pick (kolang, BM-P051). CARRY: both hands on the haft, RIGHT hand
    (back arm B) at the butt end, LEFT hand (front arm F) about 40 percent up; the pick swings in front of the body and
    strikes the ice ahead of the feet; knees bend on the strike. No period depiction of yakhchal ice cutting found:
    the written source is Iranica (ice "chopped into blocks"); grip follows ordinary two handed pick use."""
    (ex, ey), ang = pick_geom(sw, f)
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
    hB = (ex + ux * 10, ey + uy * 10); hF = (ex + ux * PICK_L * 0.42, ey + uy * PICK_L * 0.42)
    p = pose('reach', torso=lerp(-8, 16, sw), head=lerp(-6, 6, sw), thF=lerp(8, 20, sw), shF=lerp(0, -14, sw), thB=lerp(-6, -16, sw), shB=lerp(0, -10, sw))
    def held(pn_, J): PR.kolang(pn_, ex, ey, ang, PICK_L)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, x * 0.01), hands={'B': hB, 'F': hF}, held=held)

def worker_carry(pn, x, y, k, out='yakh2', expr='determined', t=0.0, f=1, walk=0.0, straw=0.4):
    """Worker carrying an ice block into the ice house (BM-P049). CARRY: block held in front of the belly with BOTH
    hands under its sides at waist height, elbows bent, upper body leaning back against the weight, short steps.
    Reconstruction: no depiction of the carry found; Hosseini and Namazian (2012) describe a sloped north door for
    moving the ice in."""
    ph = walk * math.pi * 2
    p = pose('hold', torso=-7 + 1.5 * math.sin(ph * 2), head=4, thF=6 + 14 * math.sin(ph), shF=-6 * max(0, math.sin(ph)),
             thB=-6 - 14 * math.sin(ph), shB=-6 * max(0, -math.sin(ph)))
    bx, by = f * 6, -100
    hands = {'F': (bx + f * 34, by + 8), 'B': (bx - f * 30, by + 10)}
    def held(pn_, J): PR.ice_block(pn_, bx, by, 64, 40, ang=0, straw=straw, seed=4)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, 0.7), hands=hands, held=held)

def worker_spade(pn, x, y, k, out='yakh3', push=0.0, expr='neutral', t=0.0, f=1):
    """Worker opening the earth dam of the channel with a spade (bil, BM-P051) so qanat water runs into the pool.
    CARRY: LEFT hand (front arm F) low on the shaft, RIGHT hand (back arm B) on the top end; blade in the bank ahead
    of the front foot; push 0..1 levers the handle back. Practice reconstructed (the bil is the ordinary Iranian
    irrigation spade; Iranica notes water came from qanats)."""
    ang = lerp(62, 52, push) if f > 0 else 180 - lerp(62, 52, push)
    top = (f * lerp(-8, -20, push), lerp(-160, -150, push))
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
    hB = (top[0] + ux * 6, top[1] + uy * 6); hF = (top[0] + ux * 150 * 0.45, top[1] + uy * 150 * 0.45)
    p = pose('reach', torso=lerp(14, 4, push), head=6, thF=18, shF=-12, thB=-12, shB=-4)
    def held(pn_, J): PR.bil(pn_, top[0], top[1], ang, 150)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, 1.9), hands={'B': hB, 'F': hF}, held=held)

def keeper_bowl(pn, x, y, k, out='pkeeper', expr='happy', t=0.0, f=1, lift=0.0, ice=True):
    """The Keeper with a bowl of iced sherbet (BM-P053). CARRY: bowl held at chest height in BOTH hands, fingers under
    the foot ring and the outer wall; lift 0..1 raises it toward the mouth. Reconstruction (Fryer, late 17th c.:
    Persians cooled sherbets with ice)."""
    by = lerp(-114, -150, lift); bx = f * 6
    hands = {'F': (bx + f * 30, by + 12), 'B': (bx - f * 28, by + 14)}
    p = pose('hold', torso=-2, head=lerp(2, -6, lift))
    def held(pn_, J): PR.sherbet_bowl(pn_, bx, by, 34, ice=ice)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, 0.3), hands=hands, held=held)

def keeper_point(pn, x, y, k, out='pkeeper', expr='neutral', t=0.0, f=1, p_='point'):
    return figure(pn, x, y, k, f, pose(p_), out, expr, blink=blink_at(t, 0.2))

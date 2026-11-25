"""E023 Caesar's double walls at Alesia: figures with their kit. CARRY lines (period library) in each docstring.
Figure local units: origin at the feet, y negative is up; waist about -90, chest about -135, shoulders about -150."""
import math
from lib import *
from rig import *
import props as PR

DOL_L = 100.0      # dolabra haft, about 65 cm at 0.66 cm per unit

def dig_geom(sw, f=1):
    keys = [(0.0, (-12, -166), -108), (0.5, (6, -150), -20), (1.0, (28, -110), 52)]
    if sw <= 0.5: a, b, u = keys[0], keys[1], sw / 0.5
    else: a, b, u = keys[1], keys[2], (sw - 0.5) / 0.5
    ex = lerp(a[1][0], b[1][0], u); ey = lerp(a[1][1], b[1][1], u); ang = lerp(a[2], b[2], u)
    if f < 0: ex = -ex; ang = 180 - ang
    return (ex, ey), ang

def legionary_dig(pn, x, y, k, out='rleg23c', sw=0.0, expr='determined', t=0.0, f=1):
    """Legionary digging the ditch with a dolabra (BM-P059). CARRY: both hands on the haft, RIGHT hand (back arm B) at the
    butt, LEFT hand (front arm F) about 45 percent up; swung down in front of the body, pick end into the earth ahead
    of the feet; knees bend on the strike. Depiction: legionaries digging and building on Trajan's Column (early 2nd c.
    AD, later than Alesia, VERIFY); shield off while working."""
    (ex, ey), ang = dig_geom(sw, f)
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
    hB = (ex + ux * 8, ey + uy * 8); hF = (ex + ux * DOL_L * 0.45, ey + uy * DOL_L * 0.45)
    p = pose('reach', torso=lerp(-8, 16, sw), head=lerp(-6, 6, sw), thF=lerp(8, 20, sw), shF=lerp(0, -14, sw), thB=lerp(-6, -16, sw), shB=lerp(0, -10, sw))
    def held(pn_, J):
        d = PR.dolabra(pn_, ex, ey, ang, DOL_L, flip=(f > 0))
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, x * 0.01), hands={'B': hB, 'F': hF}, held=held, shield=False)

def legionary_basket(pn, x, y, k, out='rleg23b', expr='neutral', t=0.0, f=1, walk=0.0, earth=1.0):
    """Legionary carrying spoil in a wicker basket. CARRY: basket on the LEFT shoulder (front side), steadied by the LEFT
    hand on its rim; the RIGHT arm swings free; slight lean away from the load. Depiction: soldiers carrying baskets of
    earth on their shoulders, Trajan's Column (later, VERIFY for 52 BC); Josephus lists the basket in the kit."""
    ph = walk * math.pi * 2
    p = pose('walk' if walk else 'idle', torso=-4)
    bx, by = f * 44, -172
    hands = {'F': (bx - f * 4, by + 16)}
    def held(pn_, J): PR.wicker_basket(pn_, bx, by, 46, 34, earth)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, 0.4), hands=hands, held=held, shield=False)

def legionary_wall(pn, x, y, k, out='rleg23a', expr='determined', t=0.0, f=1, p_='brace'):
    """Legionary on the rampart walk with his scutum (BM-P065). CARRY: scutum on the LEFT arm by its horizontal grip
    behind the boss, rim clear of the shoulder and knees (rig standard, E015); right hand free or on the gladius."""
    return figure(pn, x, y, k, f, pose(p_), out, expr, blink=blink_at(t, 0.8))

def rider(pn, x, y, k, out='gcav23', ph=0.0, gallop=1.0, f=1, t=0.0, expr='determined', night=0.0):
    """Gallic horseman riding out at night (BM-P060). CARRY: astride the four horned saddle, thighs held between the
    horns (no stirrups), both hands low on the reins in front of the body. Spear and shield left off for the night ride
    (reconstruction). Horse: small Gallic horse, drawn with the engine horse in a dark bay."""
    J0 = {}
    def rider_near(pn_):
        seat = (8 * f, -216)
        pn_.push(seat[0], seat[1] + 4, 0.8)
        p = pose('hold', torso=-6, thF=70, shF=-30, thB=64, shB=-34)
        figure(pn_, 0, 72, 1.0, f, p, out, expr, blink=blink_at(t, 1.1), hands={'F': (f * 30, -110), 'B': (f * 22, -104)}, shadow=False)
        pn_.pop()
    return PR.horse(pn, x, y, k * 0.62, f, ph, gallop, saddle=True, rider_near=rider_near, col=(96, 64, 44), saddle_type='horned')

def gaul_charge(pn, x, y, k, out='gaulr1', expr='angry', t=0.0, f=1, thrust=0.0):
    """Relief army warrior attacking the outer line (BM-P064). CARRY: La Tene shield on the LEFT arm by the grip behind
    the boss; spear in the RIGHT hand, overarm, point toward the enemy; thrust 0..1. Depiction: Gallic warriors with long
    shields and spears on the Arc of Orange reliefs (about 20 to 30 AD, VERIFY); Vachères warrior (shield)."""
    hand = (f * lerp(14, 44, thrust), lerp(-98, -104, thrust)); hB = (-f * 8, -92)
    ang = -10                                    # point slightly up toward the rampart
    p = pose('reach', torso=lerp(-4, 12, thrust), thF=lerp(6, 22, thrust), shF=lerp(0, -16, thrust), thB=-10, shB=-6)
    def held(pn_, J):
        a_ = math.radians(ang if f > 0 else 180 - ang)
        bx_, by_ = hB[0] - math.cos(a_) * 60, hB[1] - math.sin(a_) * 60
        PR.spear(pn_, bx_, by_, ang if f > 0 else 180 - ang, 240)
    return figure(pn, x, y, k, f, p, out, expr, blink=blink_at(t, 0.2), hands={'F': hand}, held=held)

def verc_surrender(pn, x, y, k, lay=0.0, t=0.0, f=1, expr='sad'):
    """Vercingetorix gives up his arms (BM-P062). CARRY: the sheathed long sword held flat across the body in BOTH hands
    at waist height, then lowered to the ground in front of Caesar's feet (lay 0..1); shield left off. Written sources:
    Caesar 7.89 (the leaders and arms handed over); Plutarch, Caesar 27 and Florus 1.45 (he threw his arms at Caesar's
    feet). No contemporary depiction (reconstruction)."""
    if lay < 0.5:
        hF = (f * 34, -104); hB = (-f * 30, -100)
        p = pose('hold', head=4)
        def held(pn_, J): PR.gallic_sword(pn_, hB[0] - f * 12, -104, 0 if f > 0 else 180, 110, sheath=True)
        return figure(pn, x, y, k, f, p, 'verc23', expr, blink=blink_at(t, 0.5), hands={'F': hF, 'B': hB}, held=held, shield=False)
    u = eio(clamp((lay - 0.5) * 2))
    sy_ = lerp(-104, 4, u ** 1.6)                # the sword falls to the ground in front of his feet
    pn.push(x, y, k); PR.gallic_sword(pn, -f * 42 + f * 30 * u, sy_, (0 if f > 0 else 180) + f * 8 * u, 110, sheath=True); pn.pop()
    p = pose('idle', head=lerp(4, 14, u))
    return figure(pn, x, y, k, f, p, 'verc23', expr, blink=blink_at(t, 0.5), shield=False)

def caesar(pn, x, y, k, f=1, t=0.0, expr='smug', p_='cross'):
    """Caesar (BM-P061): bronze muscled cuirass with pteruges over a red tunic, red general's cloak (paludamentum), bare
    head. CARRY: arms folded or a hand on the hip; no weapon in hand. Caesar 7.88: the colour of his cloak made him
    recognisable in the battle. At the surrender (7.89) he sat before the camp: shown only from the chest up, so the
    camp stool (props.camp_stool) appears in the wide shot only."""
    return figure(pn, x, y, k, f, pose(p_), 'caesar23', expr, blink=blink_at(t, 0.6))

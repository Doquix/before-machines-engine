"""E021 Roman scorpio: beat table, scenes, captions, cue sheet, frame renderer.
Modes: still t1 t2 ... | seg a b (raw rgb24 to stdout) | cues | T"""
import json, sys, math, random, re
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from rig import *
import props as PR
from props import tag, stamp, callout, arrow as arrow_line
import sc
import env
import make_map as MM
from fx import smear, speed_lines, focus_lines, impact, particles
from detail import shade, light

TM = json.load(open('timing.json'))
WORDS, CAPS, VO_END = TM['words'], TM['caps'], TM['dur']
def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())
def w(p, word, n=0):
    hits = [x['t'] for x in WORDS if x['p'] == p and norm(x['w']) == norm(word)]
    return hits[n]
def S(p): return CAPS[p]['s']
DUR = round(VO_END + 1.0, 3)
NF = int(round(DUR * FPS))

T = dict(
    wind0=w(0, 'Wind'), propeller=w(0, 'propeller'),
    s1=S(1), rubber=w(1, 'rubber'), twists=w(1, 'twists'), tight1=w(1, 'tight'), knots=w(1, 'knots'),
    s2=S(2), go=w(2, 'go'), stored=w(2, 'stored'), twist2=w(2, 'twist'),
    s3=S(3), spins=w(3, 'spins'), across=w(3, 'across'), yard=w(3, 'yard'),
    s4=S(4), roman=w(4, 'Roman'), weapon=w(4, 'weapon'), same=w(4, 'same'), twist4=w(4, 'twist'),
    s5=S(5), scorpio5=w(5, 'scorpio'), no5=w(5, 'no'), bending=w(5, 'bending'), bow5=w(5, 'bow'),
    s6=S(6), arm6=w(6, 'arm'), inside=w(6, 'inside'), thick=w(6, 'thick'), bundle6=w(6, 'bundle'), animal=w(6, 'animal'), sinew6=w(6, 'sinew'),
    s7=S(7), wound=w(7, 'wound'), tight7=w(7, 'tight'), winch=w(7, 'winch'),
    s8=S(8), pull=w(8, 'Pull'), bowstring=w(8, 'bowstring'), back8=w(8, 'back'),
    s9=S(9), arms9=w(9, 'arms'), twist9=w(9, 'twist'), bundles9=w(9, 'bundles'), harder=w(9, 'harder'),
    s10=S(10), hit10=w(10, 'Hit'), trigger=w(10, 'trigger'),
    s11=S(11), spin11=w(11, 'spin'), forward=w(11, 'forward'), hurling=w(11, 'hurling'), iron=w(11, 'iron'), bolt11=w(11, 'bolt'),
    s12=S(12), caesar=w(12, 'Caesar'), wrote=w(12, 'wrote'), n52=w(12, '52'), bc=w(12, 'BC'),
    s13=S(13), scorpio13=w(13, 'scorpio'), killed=w(13, 'killed'), gallic=w(13, 'Gallic'), defender13=w(13, 'defender'),
    s14=S(14), after=w(14, 'after'), defender14=w(14, 'defender'),
    s15=S(15), same15=w(15, 'same'), spot=w(15, 'spot'), wall=w(15, 'wall'),
    s16=S(16), britain=w(16, 'Britain'), hod=w(16, 'Hod'), hill=w(16, 'Hill'),
    s17=S(17), found=w(17, 'found'), eleven=w(17, 'eleven'), bolt17=w(17, 'bolt'), heads=w(17, 'heads'), clustered=w(17, 'clustered'), hut=w(17, 'hut'),
    s18=S(18), likely=w(18, 'likely'), shot=w(18, 'shot'), n170=w(18, '170'), metres=w(18, 'metres'),
    s19=S(19), weak=w(19, 'weak'), spring19=w(19, 'spring'), itself=w(19, 'itself'),
    s20=S(20), rain=w(20, 'Rain'), loosened=w(20, 'loosened'), sinew20=w(20, 'sinew'),
    s21=S(21), slack=w(21, 'slack'), bundle21=w(21, 'bundle'), threw=w(21, 'threw'), nothing=w(21, 'nothing'),
    s22=S(22), dry=w(22, 'Dry'), whole=w(22, 'whole'), machine=w(22, 'machine'),
    s23=S(23), wind23=w(23, 'Wind'), tight23=w(23, 'tight'),
    s24=S(24), let24=w(24, 'Let'), go24=w(24, 'go'),
    end=VO_END,
)
T['release'] = T['spin11'] - 0.04                    # trigger lets go as "spin" starts
T['strike'] = T['bolt11'] + 0.12                     # bolt hits the post
T['hit1'] = T['killed'] + 0.06; T['hit2'] = T['defender14'] + 0.26
T['flop'] = T['threw'] - 0.05
T['snap'] = T['go24'] + 0.02
CAM.drift = 0.5
CAM.punch = [(T['knots'], 0.05), (T['release'], 0.06), (T['strike'], 0.08), (T['hit1'], 0.06), (T['hit2'], 0.06), (T['eleven'], 0.04),
             (T['weak'], 0.04), (T['snap'], 0.06)]
CAM.shake = [(T['strike'], 12, 0.3), (T['release'], 6, 0.2), (T['hit1'], 7, 0.25), (T['hit2'], 7, 0.25), (T['nothing'], 5, 0.2)]
FLASH = [(T['strike'], 0.1, (255, 240, 214), 90), (T['snap'], 0.12, (255, 244, 220), 110)]
GROUND = 1340

def bgp(base, name, par=0.5):
    img = env.get(name)
    s = 1 + (CAM.s - 1) * par; ox = CAM.ox * par; oy = CAM.oy * par
    s = max(s, 1 + 2 * abs(ox) / W + 0.01, 1 + 2 * abs(oy) / H + 0.01)
    a = 1 / s
    base.paste(img.transform((W, H), Image.AFFINE, (a, 0, CX - (CX + ox) * a, 0, a, CY - (CY + oy) * a), Image.BILINEAR))

def camfocus(z, fx_, fy, tx, ty, ox, oy):
    return z, (tx - CX) - (fx_ - CX) * z + ox * .3, (ty - CY) - (fy - CY) * z + oy * .3

def antic(t, t0, d=0.35, back=0.18, ad=0.35):
    u = (t - t0) / d
    if u <= 0: return 0.0
    if u < ad: return -back * eio(u / ad)
    v = clamp((u - ad) / (1 - ad))
    return lerp(-back, 1.0, eoback(v, 1.6))

def steps(t, t0, t1, n):
    """Ratchet: n quick eased steps between t0 and t1 (winding motions)."""
    u = clamp((t - t0) / (t1 - t0)) * n
    i = int(u); f = u - i
    return clamp((i + eo3(clamp(f / 0.45))) / n) if i < n else 1.0

def ring(pn, x, y, t, t0, col=AMBER, r0=18, r1=70):
    u = t - t0
    if u < 0 or u > 0.6: return
    e = eo3(u / 0.6)
    pn.circ(x, y, lerp(r0, r1, e), outline=col + (int(255 * (1 - e)),), width=6)

def xmark(pn, x, y, p, s=22, col=RUST):
    if p <= 0: return
    e = eoback(p); pn.push(x, y, e)
    for a, b in (((-s, -s), (s, s)), ((-s, s), (s, -s))):
        pn.line([a, b], INK, 13); pn.line([a, b], col, 8)
    pn.pop()

def ground(pn, y, col=(140, 124, 92)):
    pn.rect(-400, y, 1480, 2800, fill=col)
    pn.line([(-400, y), (1480, y)], lerpc(col, INK, .45), 4, caps=False)

def twist_arrow(pn, cx, cy, r, p, col=RUST, sgn=1, w_=7):
    """Curved arrow round a spring, drawn over p in 0..1."""
    if p <= 0: return
    a0 = 200; a1 = a0 + sgn * 240 * eo3(p)
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * 0.35 * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 24)]
    pn.line(pts, INK, w_ + 5); pn.line(pts, col, w_)
    if p > 0.6:
        e = pts[-1]; pv = pts[-3]; ang = math.atan2(e[1] - pv[1], e[0] - pv[0])
        hd = [(e[0] + math.cos(ang) * 18, e[1] + math.sin(ang) * 18), (e[0] + math.cos(ang + 2.4) * 18, e[1] + math.sin(ang + 2.4) * 18),
              (e[0] + math.cos(ang - 2.4) * 18, e[1] + math.sin(ang - 2.4) * 18)]
        pn.poly(hd, fill=col, outline=INK, width=3)

def rain(pn, t, amt=1.0, seed=3):
    if amt <= 0: return
    rnd = random.Random(seed)
    for i in range(int(130 * amt)):
        x0, sp, ph = rnd.uniform(-100, 1180), rnd.uniform(1600, 2200), rnd.random()
        y = ((ph * 2200 + t * sp) % 2300) - 200; x = x0 + y * 0.18
        pn.line([(x, y), (x - 9, y - 48)], (210, 220, 232, int(150 * amt)), 2.4, caps=False)

# ======================= scenes =======================
# 1. Wind a toy plane's propeller: close on the plane, finger turns the prop in ratchet steps, rubber already knotted
def sc_wind(base, pn, t):
    bgp(base, 'yard', 0.3)
    wind = lerp(0.55, 0.8, steps(t, 0, T['s1'], 7))
    pa = steps(t, 0, T['s1'], 7) * 7 * math.pi
    R = PR.toy_plane(pn, 470, 1000, 6.2, prop_a=pa, wind=wind, ang=math.radians(-4))
    # the Keeper's finger on the blade tip (a line hand comes in from the right edge)
    hub = R['hub']; tipy = hub[1] - 11 * PR.CM_U * 6.2 * math.cos(pa)
    pn.line([(1200, 700), (hub[0] + 60, tipy - 30), (hub[0] + 8, tipy)], INK, 7)
    pn.arc(hub[0] + 4, tipy + 4, 10, 120, 330, INK, 5)
    tag(pn, 300, 560, 'RUBBER MOTOR', 50, pop(t, T['propeller'] - 0.1), rot_=-3)
def cam_wind(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.08, eio(P(t, 0, T['s1']))) * sc_, 540, 1000, 540, 980, ox, oy)

# 2. and the rubber band twists into tight knots: ECU of the rubber motor
def sc_knots(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    wind = lerp(0.6, 1.0, steps(t, T['s1'], T['knots'] + 0.1, 6))
    PR.rubber_ecu(pn, 540, 900, 1.25, wind=wind, t=t)
    tag(pn, 540, 1260, 'TWIST = STORED ENERGY', 54, pop(t, T['knots'] - 0.05), rot_=-2)
def cam_knots(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.12, eio(P(t, T['s1'], T['s2'] - T['s1']))) * sc_, 540, 900, 540, 900, ox, oy)

# 3. Let go, and that stored twist: Keeper launches the plane
KP = dict(x=360, y=GROUND + 40, k=2.0)
def plane_flight(t):
    u = P(t, T['go'], T['s4'] - T['go'])
    return u
def sc_launch(base, pn, t):
    bgp(base, 'yard', 0.4)
    la = antic(t, T['go'] - 0.18, 0.4, 0.12)
    R = sc.keeper_plane(pn, KP['x'], KP['y'], KP['k'], wind=1.0, prop_a=0.0, launch=clamp(la), expr='happy' if t < T['go'] else 'laughing', t=t)
    if t >= T['go'] + 0.18:
        u = t - (T['go'] + 0.18)
        px = KP['x'] + 260 + u * 520; py = KP['y'] - 360 - u * 120 - 30 * math.sin(u * 3)
        PR.toy_plane(pn, px, py, 2.6, prop_a=u * 60, wind=max(0, 1 - u * 0.5), ang=math.radians(-6), blur=1.0)
        speed_lines(pn, px - 90, py, -1, 0.1, t, length=200, n=5, spread=60, seed=3)
def cam_launch(t, sc_, ox, oy): return camfocus(sc_ * lerp(1.0, 0.92, eio(P(t, T['go'], 1.2))), 540, 1100, 540, 1050, ox, oy)

# 4. spins it across the yard: tracking shot, rubber unwinds
def sc_fly(base, pn, t):
    u = t - T['s3']
    img = env.get('yard'); sh = int((u * 260) % W)
    strip = Image.new('RGB', (W, H)); strip.paste(img, (-sh, 0)); strip.paste(img, (W - sh, 0)); base.paste(strip)
    wind = clamp(1 - u / (T['s4'] - T['s3']))
    y = 820 + 40 * math.sin(u * 2.2)
    R = PR.toy_plane(pn, 470, y, 5.0, prop_a=u * 80, wind=wind, ang=math.radians(-4 + 3 * math.sin(u * 2)), blur=1.0)
    speed_lines(pn, 120, y, -1, 0, t, length=320, n=8, spread=260, seed=5)
    tag(pn, 540, 1260, 'TWIST BECOMES SPIN', 50, pop(t, T['spins'] + 0.1), rot_=-3)

# 5a. Roman engineers built a weapon on that same twist: the knotted rubber again (same framing as beat 2)
def sc_same(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    PR.rubber_ecu(pn, 540, 900, 1.25, wind=1.0, t=t)
    tag(pn, 540, 1260, '1ST CENTURY BC', 54, pop(t, T['roman']), rot_=-3, sub='ROMAN ARMY')
# 5b. ...dissolves into a sinew spring in the same place (match)
def sc_skein_in(base, pn, t):
    bgp(base, 'rcamp', 0.3)
    tw = steps(t, T['weapon'], T['twist4'] + 0.2, 4)
    PR.skein_diagram(pn, 540, 900, 1.05, twist=lerp(0.4, 0.9, tw), arm=0, labels=False)
    tag(pn, 540, 1300, 'SAME TWIST', 56, pop(t, T['same'] - 0.05), rot_=-2)
def cam_skein_in(t, sc_, ox, oy): return camfocus(lerp(1.06, 1.0, eio(P(t, T['weapon'], 1.4))) * sc_, 540, 900, 540, 900, ox, oy)

# 6. The scorpio had no bending bow: the machine assembles; a ghost bow is crossed out
def sc_reveal(base, pn, t):
    bgp(base, 'rcamp', 0.4)
    ground(pn, GROUND + 60)
    gb = P(t, T['no5'] - 0.1, 0.25) * (1 - P(t, T['bow5'] + 0.35, 0.3))
    a = eoback(P(t, T['s5'] - 0.02, 0.4))
    PR.scorpio(pn, 600, GROUND + 60 + (1 - a) * 300, 3.4, draw=0.0, yaw=-36, pitch=20, ghost_bow=gb, H0=110)
    xmark(pn, 860, 760, P(t, T['bow5'], 0.25), 60)
    tag(pn, 540, 470, 'SCORPIO', 72, pop(t, T['scorpio5']), rot_=-3, sub='ROMAN BOLT THROWER')
    tag(pn, 820, 640, 'NO BOW', 54, pop(t, T['bow5'] + 0.05), rot_=4)
def cam_reveal(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.06, eio(P(t, T['s5'], 2))) * sc_, 600, 900, 540, 900, ox, oy)

# 7. Each wooden arm sat inside a thick bundle of animal sinew: labelled cutaway (diagram beat, holds 0.5 s)
def sc_cutaway(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.15))
    PR.skein_diagram(pn, 470, 900, 1.25, twist=0.5, arm=0, labels=False)
    callout(pn, 860, 900, 820, 1290, 'WOODEN ARM', p=pop(t, T['arm6']), sz=46)
    callout(pn, 390, 1020, 200, 1330, 'SINEW BUNDLE', p=pop(t, T['bundle6']), sz=46)
    callout(pn, 330, 580, 230, 420, 'BRONZE WASHER', p=pop(t, T['animal'] - 0.1), sz=40)
    tag(pn, 760, 470, 'TENDON CORD', 46, pop(t, T['sinew6']), rot_=3, sub='ALSO HORSE HAIR')

# 8. wound tight with a winch: close on the washer and lever bar turning, ratchet steps
def sc_wound(base, pn, t):
    bgp(base, 'rcamp', 0.3)
    tw = steps(t, T['s7'] + 0.1, T['winch'] + 0.2, 4)
    ox_, oy_ = PR.scorpio_pt('washer_top', 5.2, -30, 34, 0.0, 110)
    R = PR.scorpio(pn, 600 - ox_, 820 - oy_, 5.2, draw=0.0, yaw=-30, pitch=34, twist=tw * 0.9, H0=110, stand=True)
    # a lever bar on the washer, two line hands pushing it round
    wt = R['washer_top']
    pn.line([(wt[0] - 380, wt[1] + 160), (wt[0] - 120, wt[1] + 40)], INK, 7)
    pn.line([(wt[0] - 360, wt[1] + 230), (wt[0] - 100, wt[1] + 70)], INK, 7)
    tag(pn, 540, 470, 'WOUND BY A WINCH', 54, pop(t, T['winch'] - 0.05), rot_=-3)
    for i in range(4):
        ti = lerp(T['s7'] + 0.1, T['winch'] + 0.2, (i + .5) / 4)
        ring(pn, wt[0], wt[1], t, ti, AMBER, 30, 120)

# 9. Pull the bowstring back: the crewman winds the windlass, the slider and string come back
def sc_pull(base, pn, t):
    bgp(base, 'rcamp', 0.4)
    ground(pn, GROUND + 60)
    d = steps(t, T['pull'] - 0.05, T['back8'] + 0.35, 5)
    sc.winder(pn, 800, GROUND + 60, 2.1, winch_a=d * 5 * math.pi / 2, draw=d, t=t, expr='pain' if 0 < d < 1 else 'determined')
    tag(pn, 540, 520, 'STRING BACK', 56, pop(t, T['back8']), rot_=-3)
def cam_pull(t, sc_, ox, oy): return camfocus(lerp(1.08, 1.14, eio(P(t, T['s8'], 1.4))) * sc_, 560, 1150, 540, 1020, ox, oy)

# 10. and the arms twist those bundles even harder: top view diagram
def sc_top(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.15))
    d = eio(P(t, T['arms9'] - 0.1, T['harder'] - T['arms9'] + 0.2))
    R = PR.scorpio(pn, 620, 960, 4.2, draw=lerp(0.15, 1.0, d), yaw=0, pitch=90, stand=False)
    for key, sg in (('skein_l', -1), ('skein_r', 1)):
        cx_, cy_ = R[key]
        twist_arrow(pn, cx_, cy_, 120, P(t, T['twist9'] - 0.05, 0.5), RUST, sg)
    tag(pn, 540, 1460, 'EVEN MORE TWIST', 58, pop(t, T['harder']), rot_=-2)
    callout(pn, *R['tip_r'], 900, 1240, 'ARM', p=pop(t, T['arms9']), sz=40)

# 11. Hit the trigger: close on the claw and trigger lever under the aimer's hand
def sc_trigger(base, pn, t):
    bgp(base, 'rcamp', 0.3)
    tr = eo3(P(t, T['trigger'] + 0.05, 0.12))
    ox_, oy_ = PR.scorpio_pt('trigger', 5.6, -8, 16, 1.0, 92)
    R = PR.scorpio(pn, 600 - ox_, 980 - oy_, 5.6, draw=1.0, bolt=True, trigger=tr, yaw=-8, pitch=16, H0=92)
    tp = R['trigger']
    pn.line([(tp[0] - 420, tp[1] + 420), (tp[0] - 120, tp[1] + 160), (tp[0] - 6, tp[1] + 6)], INK, 8)
    if tr > 0: ring(pn, tp[0], tp[1], t, T['trigger'] + 0.05, RUST, 30, 130)
    tag(pn, 540, 470, 'TRIGGER', 60, pop(t, T['hit10']), rot_=-3)

# 12. and they spin forward, hurling an iron tipped bolt: release, then a tracking shot on the bolt, then the post
SH = dict(x=760, k=1.9)
def sc_fire(base, pn, t):
    u = t - T['release']; TR = T['strike'] - T['release']
    if u < 0.32:
        bgp(base, 'rcamp', 0.4)
        ground(pn, GROUND + 60)
        R = sc.aimer(pn, SH['x'], GROUND + 60, SH['k'], draw=1.0 if u < 0 else 0.0, bolt=u < 0, trigger=1.0 if u >= -0.1 else 0,
                     expr='determined' if u < 0 else 'laughing', t=t, look=(1, -0.05))
        if u >= 0:
            mx, my = R['muzzle']; bx = mx + u * 2600
            PR.catapult_bolt(pn, bx - 300 * 0.62, my - 4, 0.0, 300 * 0.62)
            speed_lines(pn, bx - 240, my, -1, 0, t, length=300, n=6, spread=40, seed=9)
            impact(pn, mx, my, t, T['release'], 0.6, seed=1, lines=False)
        return
    # tracking: the bolt holds the frame centre, the camp streams past, the post arrives at the end
    v = (u - 0.32)
    img = env.get('rcamp'); sh = int((v * 2600) % W)
    strip = Image.new('RGB', (W, H)); strip.paste(img, (-sh, 0)); strip.paste(img, (W - sh, 0)); base.paste(strip)
    ground(pn, GROUND + 60)
    for i in range(8):     # ground marks streaming past
        gx = (i * 160 - v * 2600) % 1400 - 160
        pn.line([(gx, GROUND + 120 + (i % 3) * 60), (gx + 90, GROUND + 120 + (i % 3) * 60)], (120, 104, 76), 6)
    arrive = TR - 0.32 - 0.25
    post_x = 860 + max(0.0, (arrive - v)) * 2600 if v < arrive else 860
    stuck = t >= T['strike']
    by = 960
    if post_x < 1300:
        pn.rect(post_x + 40, 560, post_x + 140, GROUND + 70, fill=WOOD, outline=INK, width=4)
        pn.line([(post_x + 62, 600), (post_x + 70, GROUND + 40)], shade(WOOD, 0.3), 2, caps=False)
        pn.line([(post_x + 100, 620), (post_x + 96, GROUND + 30)], shade(WOOD, 0.3), 2, caps=False)
    if not stuck:
        bx = 640 if v < arrive else lerp(640, post_x + 40, clamp((t - (T['strike'] - 0.25)) / 0.25))
        PR.catapult_bolt(pn, bx - 560, by, 0.0, 560)
        speed_lines(pn, bx - 600, by, -1, 0, t, length=460, n=9, spread=80, seed=9)
    else:
        PR.catapult_bolt(pn, post_x + 70 - 560, by, 0.0, 560)
        impact(pn, post_x + 40, by, t, T['strike'], 1.2, seed=3)
        particles(pn, 'chips', post_x + 40, by, t, T['strike'], 1.3, seed=5)
        focus_lines(pn, post_x + 40, by, t, T['strike'], 0.25)
    tag(pn, 540, 470, 'IRON TIPPED BOLT', 56, pop(t, T['iron'] - 0.05), rot_=-3)
def cam_fire(t, sc_, ox, oy): return camfocus(sc_, 540, 1000, 540, 1000, ox, oy)

# 13. Caesar wrote that in 52 BC: map of Gaul, pin on Avaricum
_MAP = {}
def map_img():
    if 'eu' not in _MAP: _MAP['eu'] = Image.open('map_eu.png').convert('RGB')
    return _MAP['eu']
MAPC = (0.4, 49.0, 12.0)
def geo_xy(lon, lat):
    lon_px, lat_px = MM.geo(*MAPC)
    return 540 + (lon - MAPC[0]) / lon_px, 960 - (lat - MAPC[1]) / lat_px
def mclamp(z, fx_, fy, tx, ty):
    fx_ = min(max(fx_, tx / z), W - (W - tx) / z); fy = min(max(fy, ty / z), H - (H - ty) / z)
    return fx_, fy
def map_view(z, fx_, fy, tx, ty):
    a = 2 / z
    return map_img().transform((W, H), Image.AFFINE, (a, 0, 2 * fx_ - tx * a, 0, a, 2 * fy - ty * a), Image.BILINEAR)
def pin(pn, x, y, t, t0, col=RUST):
    if t < t0: return
    u = t - t0; drop = 1 - spring(u, 1.5, 7); py = y - 220 * drop
    rp = eo3(P(u, 0.12, 0.6))
    if 0 < rp < 1: pn.circ(x, y, 24 + 90 * rp, outline=col + (int(255 * (1 - rp)),), width=6)
    pn.poly([(x, py), (x - 22, py - 44), (x + 22, py - 44)], fill=col, outline=INK, width=3)
    pn.circ(x, py - 56, 25, fill=col, outline=INK, width=4); pn.circ(x, py - 56, 9, fill=PARCH)
def label(pn, x, y, txt, sz, a=1.0, col=(60, 48, 34)):
    if a <= 0: return
    pn.text(x, y, txt, sz, col + (int(230 * a),), 'Black', 'mm', True, sp=4)
AVARICUM = (2.40, 47.08); HODHILL = (-2.22, 50.89)
def sc_map_gaul(base, pn, t):
    zp = eio(P(t, T['s12'], 1.6)); z = lerp(1.0, 1.5, zp)
    f = geo_xy(*AVARICUM); f0 = geo_xy(0.8, 48.6)
    fx_, fy = lerp(f0[0], f[0], zp), lerp(f0[1], f[1], zp); tx, ty = 540, 900
    fx_, fy = mclamp(z, fx_, fy, tx, ty)
    base.paste(map_view(z, fx_, fy, tx, ty))
    def xy(lon, lat):
        px, py = geo_xy(lon, lat); return tx + (px - fx_) * z, ty + (py - fy) * z
    label(pn, *xy(1.0, 48.0), 'GAUL', 80, P(t, T['s12'] + 0.1, 0.3))
    pin(pn, *xy(*AVARICUM), t, T['wrote'])
    label(pn, xy(*AVARICUM)[0], xy(*AVARICUM)[1] + 60, 'AVARICUM', 44, P(t, T['wrote'] + 0.15, 0.3))
    label(pn, xy(*AVARICUM)[0], xy(*AVARICUM)[1] + 110, '(BOURGES)', 30, P(t, T['wrote'] + 0.25, 0.3))
    tag(pn, 540, 1240, '52 BC', 72, pop(t, T['n52']), rot_=-3, sub='CAESAR, GALLIC WAR 7.25')

# 14 and 15. one scorpio killed Gallic defender after defender: night, the wall, fire below
WL = dict(y=1060, x=520)
def gaul_state(t):
    """Which defender stands in the spot, their throw phase and hit state."""
    h1, h2 = T['hit1'], T['hit2']
    if t < h1 + 0.6:
        th = clamp((t - (h1 - 0.9)) / 0.8); return [('gaul1', th, clamp((t - h1) / 0.35), 0)]
    if t < h2 + 0.6:
        st = clamp((t - (T['after'] - 0.25)) / 0.4)
        th = clamp((t - (h2 - 0.75)) / 0.7)
        return [('gaul2', th if st >= 1 else 0, clamp((t - h2) / 0.35), 1 - st)]
    st = clamp((t - (h2 + 0.6)) / 0.4)
    return [('gaul3', 0.25 * st, 0, 1 - st)]
def sc_wall(base, pn, t):
    bgp(base, 'avaricum', 0.3)
    PR.gallic_tower(pn, 140, WL['y'] - 70, 1.0, 3)
    PR.gallic_tower(pn, 960, WL['y'] - 70, 1.0, 3)
    PR.murus_gallicus(pn, -40, 1120, WL['y'], 1900, walk=False)
    for out, th, hit, off in gaul_state(t):
        x = WL['x'] + off * 360
        if hit < 1:
            J = sc.gaul(pn, x, WL['y'] + 90 + hit * 180, 1.9, out, throw=th, pitch=(out == 'gaul2'), t=t, hit=hit, expr='angry')
    PR.breastwork(pn, -40, 1120, WL['y'] + 6, 120)
    # fire glow from the terrace below
    fl = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 7.3)
    for i in range(5):
        pn.circ(200 + i * 180, 1900, 260, fill=(246, 150, 50, int(26 * fl)))
    rnd = random.Random(int(t * 8))
    for i in range(14):
        ex = rnd.uniform(0, 1080); ey = 1900 - ((t * 240 + i * 137) % 900)
        pn.circ(ex, ey, 4, fill=(255, 190, 90, 200))
    for hk in ('hit1', 'hit2'):
        th_ = T[hk]
        if th_ - 0.12 <= t < th_:      # bolt streak from the right
            u = (t - (th_ - 0.12)) / 0.12
            bx = lerp(1300, WL['x'] + 30, u)
            PR.catapult_bolt(pn, bx, WL['y'] - 190, math.pi, 240)
            speed_lines(pn, bx + 240, WL['y'] - 190, 1, 0, t, length=300, n=6, spread=40, seed=2)
        if t >= th_: impact(pn, WL['x'] + 30, WL['y'] - 190, t, th_, 0.9, seed=4)
    tag(pn, 540, 430, 'GALLIC DEFENDERS', 50, pop(t, T['gallic'] - 0.1), rot_=-3, sub='THROWING TALLOW ON THE FIRE')
    if t >= T['after']: tag(pn, 760, 640, 'AND THE NEXT', 46, pop(t, T['after']), rot_=4)
def cam_wall(t, sc_, ox, oy): return camfocus(1.05 * sc_, 540, 1000, 540, 980, ox, oy)

# 16. at the same spot on the wall: sight line from the scorpio to one marked stone, three hit marks
def sc_spot(base, pn, t):
    bgp(base, 'avaricum', 0.3)
    PR.murus_gallicus(pn, -40, 1120, 820, 1900, walk=False)
    PR.breastwork(pn, -40, 1120, 826, 90)
    sx, sy = 520, 690
    n = 0
    for i, ti in enumerate((T['s15'] + 0.1, T['same15'] + 0.05, T['spot'])):
        if t >= ti:
            ring(pn, sx + (i - 1) * 30, sy + (i % 2) * 20, t, ti, RUST, 30, 150)
            pn.circ(sx + (i - 1) * 30, sy + (i % 2) * 20, 16, fill=(30, 24, 20), outline=RUST, width=4)
    a = P(t, T['s15'], 0.4)
    if a > 0:
        for i in range(20):
            u0, u1 = i / 20, (i + 0.5) / 20
            if u0 > a: break
            pn.line([(lerp(1240, sx, u0), lerp(1500, sy, u0)), (lerp(1240, sx, min(u1, a)), lerp(1500, sy, min(u1, a)))], RUST, 6)
    pn.circ(sx, sy, 110 + 8 * math.sin(t * 6), outline=AMBER, width=8)
    tag(pn, 540, 470, 'SAME SPOT', 66, pop(t, T['spot'] - 0.05), rot_=-3)

# 17. In Britain, at Hod Hill: the map pans north across the Channel
def sc_map_brit(base, pn, t):
    zp = eio(P(t, T['s16'], T['hill'] - T['s16'] + 0.4)); z = lerp(1.5, 2.2, zp)
    a_ = geo_xy(*AVARICUM); b_ = geo_xy(*HODHILL)
    fx_, fy = lerp(a_[0], b_[0], zp), lerp(a_[1], b_[1], zp); tx, ty = 540, 900
    fx_, fy = mclamp(z, fx_, fy, tx, ty)
    base.paste(map_view(z, fx_, fy, tx, ty))
    def xy(lon, lat):
        px, py = geo_xy(lon, lat); return tx + (px - fx_) * z, ty + (py - fy) * z
    label(pn, *xy(-1.2, 51.6), 'BRITAIN', 70, P(t, T['britain'] - 0.05, 0.3))
    pin(pn, *xy(*HODHILL), t, T['hod'])
    label(pn, xy(*HODHILL)[0], xy(*HODHILL)[1] + 60, 'HOD HILL', 48, P(t, T['hod'] + 0.15, 0.3))
    tag(pn, 540, 1300, 'AD 44', 72, pop(t, T['hill'] + 0.05), rot_=-3, sub='ROMAN INVASION OF BRITAIN')

# 18 and 19. eleven bolt heads in one hut; likely shot from around 170 metres (site plan, scale line, DISPUTED)
def sc_plan(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.15))
    nb = clamp((t - T['eleven']) / (T['clustered'] - T['eleven'] + 0.2)) if t >= T['eleven'] else 0
    hut = PR.hodhill_plan(pn, 540, 900, 1.05, p_bolts=nb, fort=P(t, T['s18'], 0.3), label=True)
    pn.text(160, 380, 'N', 44, INK, 'Black', 'mm', True); pn.line([(160, 470), (160, 410)], INK, 6)
    # scale line: about 170 m, from the west of the hut
    lp = P(t, T['shot'], T['n170'] - T['shot'] + 0.2)
    if lp > 0:
        a_ = (hut[0] - 230 * 1.05 * 0.82, hut[1] - 230 * 1.05 * 0.57); b_ = hut
        for i in range(16):
            u0, u1 = i / 16, (i + 0.55) / 16
            if u0 > lp: break
            pn.line([lerp2(a_, b_, u0), lerp2(a_, b_, min(u1, lp))], RUST, 7, caps=False)
        tag(pn, a_[0] - 40, a_[1] - 80, 'ABOUT 170 m', 44, pop(t, T['n170']), rot_=-4)
def hud_plan(pn, t):
    if t >= T['hut']:
        s_ = pop(t, T['hut'])
        pn.push(560, 560, s_)
        pn.rect(-300, -120, 300, 120, fill=PARCH, outline=INK, width=4, r=14)
        PR.bolt_head_insert(pn, 0, -14, 0.82, rust=0.7)
        pn.text(0, 84, 'HEAD 88 mm (BRITISH MUSEUM)', 26, INK, 'Black', 'mm', True)
        pn.pop()
    if t >= T['eleven'] and t < T['hut']: tag(pn, 540, 470, '11 BOLT HEADS', 60, pop(t, T['eleven']), rot_=3)
    stamp(pn, 560, 1640, 'DISPUTED', t - (T['metres'] - 0.02), 84)
    if t >= T['metres'] + 0.2:
        pn.text(560, 1745, 'AN ATTACK, OR LATER TARGET PRACTICE?', 30, INK, 'Black', 'mm', True)
def lerp2(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
def cam_plan(t, sc_, ox, oy):
    z = lerp(1.0, 1.75, eio(P(t, T['found'], T['eleven'] - T['found'] + 0.3)))
    z = lerp(z, 1.4, eio(P(t, T['shot'] - 0.2, 0.6)))
    hx, hy = 540 + 230 * 1.05, 900 + 250 * 1.05
    return camfocus(z * sc_, lerp(540, hx - 60, P(z, 1.0, 0.4)), lerp(900, hy - 40, P(z, 1.0, 0.4)), 540, 1000, ox, oy)

# 20. The weak point was the spring itself: back at camp, grey; push in on the springs
def sc_weak(base, pn, t):
    bgp(base, 'rcamp_rain', 0.3)
    ox_, oy_ = PR.scorpio_pt('frame', 4.0, -30, 24, 0.0, 110)
    PR.scorpio(pn, 540 - ox_, 980 - oy_, 4.0, draw=0.0, yaw=-30, pitch=24, H0=110)
    tag(pn, 540, 470, 'WEAK POINT', 64, pop(t, T['weak']), rot_=-3)
    tag(pn, 760, 640, 'THE SPRING', 50, pop(t, T['spring19']), rot_=4)
def cam_weak(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.15, eio(P(t, T['s19'], 2.2))) * sc_, 560, 1000, 540, 960, ox, oy)

# 21. Rain loosened the sinew: the Keeper looks up, the springs sag
def sc_rain(base, pn, t):
    bgp(base, 'rcamp_rain', 0.4)
    ground(pn, GROUND + 60, (110, 100, 80))
    sl = eio(P(t, T['loosened'] - 0.1, 1.0))
    look = (0.2, -1.0) if t < T['sinew20'] else (0.8, 0.3)
    sc.aimer(pn, 760, GROUND + 60, 2.3, draw=0.0, bolt=False, slack=sl, expr='worried', t=t, look=look)
    rain(pn, t, 1.0)
    tag(pn, 540, 470, 'WET SINEW GOES SLACK', 52, pop(t, T['sinew20']), rot_=-3)

# 22. and a slack bundle threw nothing: fires, the bolt dribbles out and drops
def sc_flop(base, pn, t):
    bgp(base, 'rcamp_rain', 0.4)
    ground(pn, GROUND + 60, (110, 100, 80))
    u = t - T['flop']
    bo = None if u < 0 else min(110, u * 260)
    R = sc.aimer(pn, 700, GROUND + 60, 2.3, draw=0.25 if u < 0 else 0.0, bolt=u < 0, slack=1.0, trigger=1.0 if u >= 0 else 0,
                 expr='worried' if u < 0.3 else 'skeptical', t=t, look=(1, 0.3))
    if u >= 0:
        mx, my = R['muzzle']
        drop = clamp((u - 0.25) / 0.3)
        x_ = mx - 40 + min(160, u * 300); y_ = my + ei2(drop) * (GROUND + 50 - my)
        ang = lerp(0, 0.5, drop)
        PR.catapult_bolt(pn, x_ - 120 * math.cos(ang), y_ - 120 * math.sin(ang), ang, 125)
        if drop >= 1: particles(pn, 'dust', x_, GROUND + 60, t, T['flop'] + 0.55, 0.7, seed=6, ground=GROUND + 64)
    rain(pn, t, 1.0)
    stamp(pn, 540, 520, 'NOTHING', t - T['nothing'], 96)

# 23. Dry sinew was the whole machine: the Keeper close, thinking; dry spring beside him
def sc_dry(base, pn, t):
    bgp(base, 'rcamp', 0.3)
    p = pose('idle', head=6)
    figure(pn, 360, 2050, 4.2, 1, p, 'rkeep21', 'thinking' if t < T['whole'] else 'smug', look=(0.9, -0.2), blink=blink_at(t, 0.3))
    PR.skein_diagram(pn, 860, 900, 0.75, twist=0.9, labels=False)
    tag(pn, 760, 560, 'DRY = POWER', 56, pop(t, T['dry'] + 0.05), rot_=3)

# 24 and 25. Wind it tight. Let it go: the spring winds in steps, then snaps; fades back into the opening
def sc_end(base, pn, t):
    base.paste(bg_cam(env.get('parch'), 0.2))
    tw = steps(t, T['s23'], T['tight23'] + 0.25, 4)
    if t >= T['snap']: tw = max(0.0, 1 - (t - T['snap']) / 0.12)
    PR.skein_diagram(pn, 540, 900, 1.05, twist=lerp(0.4, 1.0, tw), arm=0 if t < T['snap'] else -10 * math.exp(-(t - T['snap']) * 8), labels=False)
    if t >= T['snap']:
        impact(pn, 900, 900, t, T['snap'], 1.0, seed=7)
        speed_lines(pn, 900, 900, 1, 0, t, length=300, n=7, spread=200, seed=7)
def cam_end(t, sc_, ox, oy): return camfocus(lerp(1.0, 1.1, eio(P(t, T['s23'], 1.5))) * sc_, 540, 900, 540, 900, ox, oy)

SCENES = [
    (0.0, sc_wind, cam_wind, None),
    (T['s1'], sc_knots, cam_knots, None),
    (T['s2'], sc_launch, cam_launch, None),
    (T['s3'], sc_fly, None, None),
    (T['s4'], sc_same, cam_knots, 'slide'),          # chapter: to Rome
    (T['weapon'] - 0.1, sc_skein_in, cam_skein_in, 'dissolve'),
    (T['s5'], sc_reveal, cam_reveal, None),
    (T['s6'], sc_cutaway, None, None),
    (T['s7'], sc_wound, None, None),
    (T['s8'], sc_pull, cam_pull, None),
    (T['s9'], sc_top, None, None),
    (T['s10'], sc_trigger, None, None),
    (T['s11'], sc_fire, cam_fire, None),
    (T['s12'], sc_map_gaul, None, 'slide'),          # chapter: Caesar at Avaricum
    (T['s13'], sc_wall, cam_wall, None),
    (T['s15'], sc_spot, None, None),
    (T['s16'], sc_map_brit, None, 'slide'),          # chapter: Britain
    (T['s17'], sc_plan, cam_plan, None),
    (T['s19'], sc_weak, cam_weak, 'slide'),          # chapter: the weak point
    (T['s20'], sc_rain, None, None),
    (T['s21'], sc_flop, None, None),
    (T['s22'], sc_dry, None, None),
    (T['s23'], sc_end, cam_end, None),
]
HUD = {sc_plan: hud_plan}
SLIDE = 0.35
DISS = 0.3

def scene_idx(t): return max(i for i, s in enumerate(SCENES) if s[0] <= t)

def render_scene(i, t):
    _, fn, cam, _ = SCENES[i]
    CAM.extra = cam; CAM.set(t)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay)
    fn(base, pn, t)
    if fn in HUD: HUD[fn](Pen(lay, cam=False), t)
    flatten(base, lay)
    return base
# ---------------- captions (word by word) ----------------
STOP = set('a an the of on in to and is it its was had his he them then that this did let at into off out up how here now for like even just according so were could with each'.split())
def build_chunks():
    chunks = []
    for pi, c in enumerate(CAPS):
        ws = [x for x in WORDS if x['p'] == pi]
        n = max(1, math.ceil(len(ws) / 4))
        size = math.ceil(len(ws) / n)
        for j in range(n):
            part = ws[j * size:(j + 1) * size]
            if not part: continue
            kw = None
            for x in part:
                if x['kw']: kw = x['w']
            if kw is None:
                cand = [x['w'] for x in part if x['w'].strip('.,').lower() not in STOP]
                kw = max(cand, key=len) if cand else None
            chunks.append(dict(words=part, kw=kw, s=part[0]['t']))
    for i, ch in enumerate(chunks):
        nxt = chunks[i + 1]['s'] if i + 1 < len(chunks) else VO_END + 0.25
        ch['e'] = min(nxt, ch['words'][-1]['t'] + 1.6)
    return chunks
CHUNKS = build_chunks()

def draw_captions(img, t):
    ch = None
    for c in CHUNKS:
        if c['s'] - 0.02 <= t < c['e']: ch = c
    if ch is None: return
    lay = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    size = 76
    f = F('Black', size * SS, True)
    texts = [x['w'] for x in ch['words']]
    sp_ = f.getlength(' ')
    widths = [f.getlength(x) for x in texts]
    total = sum(widths) + sp_ * (len(texts) - 1)
    k = min(1.0, 960 * SS / total)
    if k < 1:
        f = F('Black', size * SS * k, True); sp_ = f.getlength(' '); widths = [f.getlength(x) for x in texts]; total = sum(widths) + sp_ * (len(texts) - 1)
    x = W * SS / 2 - total / 2; y = 1440 * SS
    for wd, wdt in zip(ch['words'], widths):
        a = P(t, wd['t'] - 0.03, 0.14)
        if a > 0:
            s = eoback(a, 2.2)
            col = AMBER if wd['w'] == ch['kw'] else WHITE
            fs = F('Black', f.size * (0.72 + 0.28 * s), True)
            cx = x + wdt / 2
            d.text((cx, y), wd['w'], font=fs, fill=col + (int(255 * min(1, a * 2)),), anchor='mm',
                   stroke_width=int(8 * SS * 0.9), stroke_fill=(16, 12, 10, int(235 * min(1, a * 2))))
        x += wdt + sp_
    img.alpha_composite(lay.resize((W, H), Image.BOX))

_OPEN = None
def frame(t):
    global _OPEN
    i = scene_idx(t)
    img = render_scene(i, t)
    st, _, _, org = SCENES[i]
    if i > 0 and org == 'slide' and t < st + SLIDE:
        prev = render_scene(i - 1, t)
        u = eio(P(t, st, SLIDE)); dx = int(round(W * u))
        comp = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        comp.paste(prev, (-dx, 0)); comp.paste(img, (W - dx, 0))
        img = comp
    elif i > 0 and org == 'dissolve' and t < st + DISS:
        prev = render_scene(i - 1, t)
        img = Image.blend(prev, img, eio(P(t, st, DISS)))
    for t0, dur, col, st_ in FLASH:
        if t0 <= t < t0 + dur:
            a = 1 - (t - t0) / dur
            img.alpha_composite(Image.new('RGBA', (W, H), col + (int(st_ * a),)))
    if t < VO_END + 0.4: draw_captions(img, t)
    fo = P(t, DUR - 0.7, 0.65)
    if fo > 0:
        if _OPEN is None:
            _OPEN = render_scene(0, 0.0).convert('RGB').convert('RGBA')
        img = Image.blend(img, _OPEN, eio(fo))
    return img.convert('RGB')


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'still':
        for a in sys.argv[2:]:
            t = float(a); frame(t).save(f'still_{t:06.2f}.png')
    elif mode == 'seg':
        a, b = int(sys.argv[2]), int(sys.argv[3])
        out = sys.stdout.buffer
        for n in range(a, b): out.write(frame(n / FPS).tobytes())
    elif mode == 'T':
        for k, v in sorted(T.items(), key=lambda x: x[1]): print(f'{v:6.2f} {k}')

def cues():
    C = [(0.0, 'ratchet', 0.6), (0.35, 'ratchet', 0.5), (0.7, 'ratchet', 0.5), (1.05, 'ratchet', 0.5), (T['propeller'], 'pop', 0.4),
         (T['s1'], 'stretch', 0.6), (T['twists'], 'creak', 0.6), (T['tight1'], 'stretch', 0.5), (T['knots'], 'squeeze', 0.7), (T['knots'], 'pop', 0.5),
         (T['go'] - 0.05, 'swish', 0.6), (T['go'] + 0.1, 'buzz', 0.7), (T['s3'], 'buzz', 0.8), (T['spins'] + 0.1, 'pop', 0.4),
         (T['roman'], 'pop', 0.5), (T['weapon'] - 0.1, 'shimmer', 0.4), (T['same'], 'pop', 0.4), (T['twist4'], 'creak', 0.6),
         (T['s5'], 'thud', 0.7), (T['s5'] + 0.1, 'clack', 0.5), (T['scorpio5'], 'pop', 0.5), (T['bow5'], 'stamp', 0.7),
         (T['arm6'], 'pop', 0.5), (T['bundle6'], 'pop', 0.5), (T['animal'] - 0.1, 'pop', 0.4), (T['sinew6'], 'pop', 0.5),
         (T['winch'] - 0.05, 'pop', 0.4)]
    for i in range(4): C.append((lerp(T['s7'] + 0.1, T['winch'] + 0.2, (i + .2) / 4), 'ratchet', 0.7))
    C.append((T['s7'], 'creak', 0.6))
    for i in range(5): C.append((lerp(T['pull'] - 0.05, T['back8'] + 0.35, (i + .2) / 5), 'ratchet', 0.7))
    C += [(T['pull'], 'creak', 0.6), (T['back8'], 'pop', 0.4),
          (T['arms9'], 'creak', 0.7), (T['twist9'], 'stretch', 0.6), (T['harder'], 'pop', 0.5),
          (T['hit10'], 'pop', 0.4), (T['trigger'] + 0.05, 'clack', 0.8),
          (T['release'], 'twang', 1.0), (T['release'] + 0.01, 'clank', 0.6), (T['release'] + 0.05, 'whiz', 0.8),
          (T['strike'], 'thunk', 1.0), (T['strike'] + 0.01, 'crack', 0.6), (T['iron'], 'pop', 0.4),
          (T['wrote'], 'paper', 0.4), (T['wrote'] + 0.05, 'pop', 0.5), (T['n52'], 'pop', 0.5),
          (T['s13'], 'fire', 0.6), (T['gallic'] - 0.1, 'pop', 0.4),
          (T['hit1'] - 0.12, 'whiz', 0.8), (T['hit1'], 'thunk', 0.9), (T['hit1'] + 0.2, 'thud', 0.6),
          (T['after'], 'pop', 0.4), (T['hit2'] - 0.12, 'whiz', 0.8), (T['hit2'], 'thunk', 0.9), (T['hit2'] + 0.2, 'thud', 0.6),
          (T['s15'], 'slide', 0.4), (T['s15'] + 0.1, 'tick', 0.6), (T['same15'] + 0.05, 'tick', 0.6), (T['spot'], 'tick', 0.6), (T['spot'], 'pop', 0.5),
          (T['britain'], 'paper', 0.4), (T['hod'], 'pop', 0.5), (T['hill'] + 0.05, 'pop', 0.5),
          (T['eleven'], 'pop', 0.5)]
    for i in range(11): C.append((T['eleven'] + i * (T['clustered'] - T['eleven'] + 0.2) / 11, 'clink', 0.35))
    C += [(T['hut'], 'pop', 0.5), (T['shot'], 'slide', 0.5), (T['n170'], 'pop', 0.5), (T['metres'] - 0.02, 'stamp', 0.9),
          (T['weak'], 'pop', 0.5), (T['spring19'], 'pop', 0.4), (T['s20'], 'rain', 0.7), (T['s21'], 'rain', 0.7), (T['loosened'], 'creak', 0.5),
          (T['sinew20'], 'pop', 0.4), (T['flop'], 'clack', 0.6), (T['flop'] + 0.02, 'stretch', 0.5), (T['flop'] + 0.55, 'thud', 0.5),
          (T['nothing'], 'stamp', 0.8),
          (T['dry'] + 0.05, 'pop', 0.5), (T['whole'], 'chime', 0.3)]
    for i in range(4): C.append((lerp(T['s23'], T['tight23'] + 0.25, (i + .2) / 4), 'ratchet', 0.7))
    C += [(T['snap'], 'twang', 0.9), (T['snap'] + 0.02, 'whoosh', 0.5)]
    for st, _, _, org in SCENES[1:]:
        if org == 'slide': C.append((st, 'whoosh', 0.35))
    C = sorted(set(C))
    json.dump(dict(cues=C, T=T, dur=DUR, nf=NF), open('cues.json', 'w'), indent=1)
    print(len(C), 'cues', 'dur', DUR, 'frames', NF)
if __name__ == '__main__' and sys.argv[1] == 'cues': cues()

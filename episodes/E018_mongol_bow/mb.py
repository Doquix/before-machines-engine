"""E018 Mongol composite bow (Yisungge's shot, c. 1225): held object rigs (Mongol archer on foot and mounted),
environments and map levels. Props live in the engine props.py (BM-P007 to BM-P014)."""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import props as PR
from props import mongol_bow, mongol_arrow, mbow_string_bend, thumb_ring, combat_quiver, bow_case, horse, stele, MARROW_L
import lb
import env as E
from detail import shade, light

RIDE = dict(torso=0, head=0, uaF=14, faF=6, uaB=-14, faB=-6, thF=55, shF=-20, thB=50, shB=-24)

def mongol_archer(pn, x, y, k, f=1, draw=0.0, out='mkeeper', expr='determined', rel=0.0, aim=0.0, p=None, arrow_on=True,
                  gear=True, look=(0.9, 0.0), blink=0.0, shadow=True, legs=1.0, vib=0.0, arrow_alpha=1.0):
    """Mongol archer, thumb draw. CARRY (BM-P007 to P010): bow in the LEFT hand (front, F, toward the target), arm locked
    straight; arrow on the RIGHT side of the bow (thumb draw), level just under the chin; right (back, B) hand hooks the
    string with the thumb, thumb ring on, drawn back to the jaw with the elbow raised in line behind it. Combat quiver on
    the RIGHT hip (B side), bottom forward, fletchings up and back; empty bow case on the LEFT hip (F side)."""
    p = p or pose('idle', torso=-2 * draw, head=draw)
    J0 = joints(p, f, legs)
    hands = lb.archer_hands(f, draw, J0['neck'], rel=rel, aim=aim)
    info = {}
    def mid(pn_, J):
        if gear:
            combat_quiver(pn_, J, f, n=6, arrows=5 if arrow_on else 6)
            bow_case(pn_, J, f)
    def held(pn_, J):
        g = J['haF']; s = J['haB']
        st = mbow_string_bend(g, s) if rel <= 0 else 0.0
        tilt = math.atan2(s[1] - g[1], f * (g[0] - s[0])) * 0 + (-f * aim if aim else 0.0)
        B = mongol_bow(pn_, g[0], g[1], f, st, string_to=s if rel <= 0 else None, tilt=tilt, vib=vib)
        if arrow_on and rel <= 0:
            ang = math.atan2(g[1] - s[1], g[0] - s[0])
            mongol_arrow(pn_, s, ang)
        info['bow'] = B
    J = figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink, hands=hands, held=held, mid=mid, shadow=shadow, legs=legs)
    # thumb ring on the drawing hand, drawn last so it reads
    pn.push(x, y, k); s = J['haB']; thumb_ring(pn, s[0] - f * 1, s[1] - 3.5); pn.pop()
    info['J'] = J
    return info

def mounted_archer(pn, x, y, k, f=1, ph=0.0, gallop=1.0, draw=0.0, out='yisungge', expr='determined', rel=0.0, aim=0.0,
                   arrow_on=True, look=(0.9, 0.0), blink=0.0, vib=0.0):
    """Horse archer at the gallop: short stirrups, rider rises in them, upper body steady while the horse moves.
    The rider's far leg lines up behind the near one (front on rig); reins rest on the bow hand side."""
    info = {}
    def rider(pn_):
        hs = info['seat_local']
        p = dict(RIDE); p['torso'] = -2 * draw + 2
        J0 = joints(p, f, 1.0)
        yy = hs[1] - J0['pelvis'][1]
        info.update(mongol_archer(pn_, hs[0], yy, 1.0, f, draw, out, expr, rel, aim, p=p, arrow_on=arrow_on,
                                  look=look, blink=blink, shadow=False, vib=vib))
    # seat in horse local units (horse() calls rider_near inside its own push)
    g = gallop
    bob = -10 * g * math.sin(2 * math.pi * ph * 2) ** 2
    info['seat_local'] = (f * 6, -210 + bob + 2 * g * math.sin(2 * math.pi * ph * 2))
    p_ = dict(RIDE); J0 = joints(p_, f, 1.0); hs = info['seat_local']
    foot = (hs[0] + J0['footF'][0] - J0['pelvis'][0] + f * 6, hs[1] + J0['footF'][1] - J0['pelvis'][1])
    H = horse(pn, x, y, k, f, ph, gallop, rider_near=rider, stirrup_at=foot)
    info['horse'] = H
    return info

# ---------------- environments ----------------
def env_steppe(dusk=0.0):
    """Open steppe: wide pale sky, low rolling hills, short dry grass."""
    def mk():
        im = E.sky((196, 206, 214), (232, 222, 196), glow=(250, 232, 190), gy=0.42)
        E.clouds(im, 3, (246, 240, 228), n=6, y0=160, y1=560)
        E.hill_layer(im, 900, 60, (168, 170, 150), 21)
        E.hill_layer(im, 990, 50, (150, 150, 112), 22)
        E.hill_layer(im, 1080, 36, (140, 138, 92), 23)
        return E.grade(im, blur=3.0, sat=0.78, bright=0.94)
    return cache(('steppe', dusk), mk, 4)

def env_museum():
    """Museum gallery: warm walls, a doorway, spot lit plinth area, dark floor (Hermitage hall, simplified)."""
    def mk():
        im = Image.new('RGB', (W, H), (150, 128, 104)); d = ImageDraw.Draw(im)
        for i in range(H):
            c = lerpc((92, 72, 58), (168, 146, 118), min(1, i / 1100))
            d.line([(0, i), (W, i)], fill=c)
        d.rectangle([0, 1220, W, H], fill=(84, 62, 48))
        for x0 in range(-60, W, 180):
            d.polygon([(x0, 1220), (x0 + 180, 1220), (x0 + 260, H), (x0 + 60, H)], fill=(92, 68, 52) if (x0 // 180) % 2 else (80, 60, 46))
        d.rectangle([0, 1200, W, 1222], fill=(60, 44, 34))
        for x0 in (60, 820):                      # framed panels / doorway
            d.rectangle([x0, 520, x0 + 200, 1100], outline=(120, 96, 74), width=10)
        d.rectangle([0, 360, W, 380], fill=(130, 106, 84))
        g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
        gd.polygon([(420, 0), (660, 0), (860, 1300), (220, 1300)], fill=110)
        g = g.filter(ImageFilter.GaussianBlur(70))
        im = Image.composite(Image.new('RGB', (W, H), (250, 232, 196)), im, g)
        return E.grade(im, blur=3.0, sat=0.8, bright=0.95)
    return cache(('museum',), mk, 4)

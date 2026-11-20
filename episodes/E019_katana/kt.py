"""E019 katana quench: the smith rig (holding the blade in tongs, the plunge), close up arm, environments.
Props live in the engine props.py (BM-P015 to BM-P021)."""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from lib import *
from rig import *
import props as PR
from props import katana, katana_section, quench_trough, steam, forge_hearth, tongs, hera, K_NAG, K_TANG, K_SORI
import env as E
from detail import shade, light

def smith_tongs(pn, x, y, k, f=1, plunge=0.0, out='kkeeper', expr='determined', sori=0.4 * K_SORI, heat=0.0, clay=1.0,
                hard=0.0, look=(0.8, 0.4), blink=0.0, wet=0.0, lift=0.0):
    """CARRY (BM-P019): both hands on the tong handles, BACK hand at the handle end, FRONT hand forward on the handles;
    the jaws clamp the tang; the blade runs on in line, EDGE DOWN. plunge 0..1: torso leans in, the hands drop and the
    blade tilts down into the trough in front (+f). lift 0..1 brings it back up. Weight on the front leg."""
    p_ = clamp(plunge - lift)
    e = eio(p_)
    a = lerp(0.10, 0.26, e)                            # tongs angle below horizontal: a shallow plunge along the trough
    lean = lerp(4, 34, e)
    p = pose('idle', torso=lean, head=lerp(4, 10, e), thF=lerp(8, 34, e), shF=lerp(0, -16, e), thB=lerp(-6, -10, e), shB=lerp(0, -22, e))
    J0 = joints(p, f)
    nk = J0['neck']
    bx = nk[0] + f * lerp(12, 22, e); by = nk[1] + lerp(66, 84, e)
    d_ = (f * math.cos(a), math.sin(a))
    B = (bx, by); Fh = (bx + d_[0] * 34, by + d_[1] * 34)
    jaw = (Fh[0] + d_[0] * 46, Fh[1] + d_[1] * 46)
    info = {}
    def held(pn_, J):
        tongs(pn_, J['haB'], jaw, w=1.0)
        tang_end = (jaw[0] - d_[0] * 6, jaw[1] - d_[1] * 6)
        machi = (tang_end[0] + d_[0] * K_TANG, tang_end[1] + d_[1] * K_TANG)
        info['blade'] = katana(pn_, machi[0], machi[1], 1.0, a * f if f == 1 else -a, f, sori=sori, heat=heat, clay=clay, hard=hard, wet=wet)
        tongs(pn_, J['haB'], jaw, w=1.0)
    J = figure(pn, x, y, k, f, p, out, expr, look=look, blink=blink, hands={'F': Fh, 'B': B}, held=held)
    info['J'] = J
    return info

def arm_in(pn, frm, hand, col=(196, 184, 156), w=26):
    """A forearm entering from the frame edge for close ups: sleeve tube to the wrist, then the hand on the tool."""
    pn.line([frm, hand], INK, w + 6); pn.line([frm, hand], col, w)
    pn.circ(hand[0], hand[1], w * 0.55, fill=SKIN, outline=INK, width=3)

# ---------------- environments ----------------
def env_forge():
    """Smithy interior, dim (the quench is judged by colour, so the room is kept dark): plank walls, a shimenawa rope
    over the work area, earth floor."""
    def mk():
        im = Image.new('RGB', (W, H), (54, 42, 34)); d = ImageDraw.Draw(im)
        for x0 in range(0, W, 120):
            d.rectangle([x0, 0, x0 + 116, 1240], fill=(70, 54, 42) if (x0 // 120) % 2 else (62, 48, 38))
            d.line([(x0, 0), (x0, 1240)], fill=(40, 30, 24), width=4)
        d.rectangle([0, 1240, W, H], fill=(84, 66, 50))
        for i in range(30):
            d.line([(0, 1240 + i * 24), (W, 1240 + i * 24)], fill=(78, 60, 46), width=2)
        d.rectangle([0, 360, W, 384], fill=(96, 74, 54))
        g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
        gd.ellipse([180, 760, 1000, 1500], fill=120)
        g = g.filter(ImageFilter.GaussianBlur(120))
        im = Image.composite(Image.new('RGB', (W, H), (190, 120, 70)), im, g)
        return E.grade(im, blur=3.0, sat=0.8, bright=0.95)
    return cache(('forge19',), mk, 4)

def shimenawa(pn, y=420, t=0.0):
    pts = PR.smooth([(-40, y), (270, y + 40), (540, y + 52), (810, y + 40), (1120, y)], False, 10)
    pn.line(pts, INK, 22); pn.line(pts, (214, 196, 150), 16)
    for i in range(0, len(pts), 3):
        px, py = pts[i]; pn.line([(px - 6, py - 6), (px + 6, py + 6)], (176, 156, 110), 3, caps=False)
    for xx in (300, 540, 780):
        yy = y + 46 + (6 if xx == 540 else 0)
        sw = math.sin(t * 2 + xx) * 4
        pn.poly([(xx - 14, yy), (xx + 14, yy), (xx + 10 + sw, yy + 30), (xx + 18 + sw, yy + 30), (xx + 6 + sw, yy + 62), (xx - 8 + sw, yy + 62)],
                fill=(246, 244, 236), outline=INK, width=2)

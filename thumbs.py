"""Before Machines mystery thumbnail format (first used E021, 2026-11-22).

The episode's hero item is hidden as a solid dark silhouette with a warm rim glow and a big gold question mark on it,
the Keeper stands beside it in period kit with a SURPRISED face, and ONE short phrase at the top (one or two lines,
all gold) teases the mechanism without naming it. Every line must be true: hide the answer, never invent one.

Usage (from an episode folder, after the period kit is approved):
    import thumbs
    thumbs.mystery(draw_item=lambda pn: PR.scorpio(pn, x, y, 4.4, ...), env_name='rcamp', outfit='rkeep21',
                   lines=("ROME'S SNIPER", 'RIFLE?'), sizes=(130, 130), colors=(thumbs.GOLD, thumbs.GOLD), qmark=(470, 1020), out='E021_thumb')
Writes OUT_mystery_vertical.png (1080x1920, the Short's cover) and OUT_mystery_16x9.png (1280x720).
"""
import glob
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from lib import *
from rig import *
import env

GOLD = (255, 210, 60); WHITE = (255, 255, 255); SIL = (26, 22, 28); GLOW = (255, 190, 90)

def outlined(pn, x, y, txt, sz, col):
    for dx in range(-9, 10, 3):
        for dy in range(-9, 10, 3):
            if dx * dx + dy * dy <= 81: pn.text(x + dx, y + dy, txt, sz, INK, 'Black', 'mm', True)
    pn.text(x, y, txt, sz, col, 'Black', 'mm', True)

def _font(sz):
    fp = [f for f in glob.glob('/usr/share/fonts/**/*.[ot]tf', recursive=True) if 'Inter' in f and 'Black' in f]
    return ImageFont.truetype(fp[0], sz) if fp else ImageFont.load_default()

def mystery(draw_item, env_name, outfit, lines, qmark=(470, 1020), keeper=(870, 1900, 3.2), out='thumb', dim=0.35,
            sizes=(170, 100, 76), colors=None):
    """lines: three short lines, top to bottom (big gold, white, gold). draw_item(pn) draws the hero item at full
    detail; only its outline is used (alpha above 90, so ground shadows drop out)."""
    CAM.drift = 0; CAM.set(0)
    im = Image.blend(env.get(env_name).convert('RGBA'), Image.new('RGBA', (W, H), (40, 34, 30, 255)), dim)
    lay = new_layer(); draw_item(Pen(lay, cam=False))
    a = lay.resize((W, H), Image.BOX).split()[3].point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.GaussianBlur(1.2))
    glow = a.filter(ImageFilter.GaussianBlur(26)).point(lambda v: min(255, int(v * 1.6)))
    L = lambda c: Image.new('L', (W, H), c)
    im.alpha_composite(Image.merge('RGBA', (L(GLOW[0]), L(GLOW[1]), L(GLOW[2]), glow)))
    im.alpha_composite(Image.merge('RGBA', (L(SIL[0]), L(SIL[1]), L(SIL[2]), a)))
    lay2 = new_layer(); pn = Pen(lay2, cam=False)
    outlined(pn, qmark[0], qmark[1], '?', 380, GOLD)
    kx, ky, kk = keeper
    figure(pn, kx, ky, kk, -1, pose('idle', head=-6), outfit, 'surprised', look=(-0.9, -0.4))
    cols = colors or (GOLD, WHITE, GOLD)
    for y, col, txt, sz in zip((230, 400, 545), cols, lines, sizes):
        outlined(pn, 540, y, txt, sz, col)
    flatten(im, lay2)
    v = im.convert('RGB'); v.save(f'{out}_mystery_vertical.png')
    h = Image.new('RGB', (1280, 720))
    bg = Image.blend(env.get(env_name).convert('RGB'), Image.new('RGB', (W, H), (40, 34, 30)), dim)
    h.paste(bg.resize((1280, 2276)).crop((0, 800, 1280, 1520)))
    h.paste(v.crop((0, 560, 1080, 1920)).resize((540, 680)), (740, 40))
    d = ImageDraw.Draw(h)
    hs = [140, 66, 66] if len(lines) == 3 else [120] * len(lines)
    hy = (200, 350, 470) if len(lines) == 3 else (250, 410, 570)
    for y, col, sz, txt in zip(hy, cols, hs, lines):
        d.text((380, y), txt, font=_font(sz), fill=col, anchor='mm', stroke_width=10, stroke_fill=INK)
    h.save(f'{out}_mystery_16x9.png')
    return v, h

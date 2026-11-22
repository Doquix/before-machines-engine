"""Before Machines mystery thumbnail format (first used E021, 2026-11-22).

The episode's hero item is hidden as a solid dark silhouette with a warm rim glow and a big gold question mark on it,
no character (the item alone carries the frame; keeper=(x, y, k) adds the Keeper only if asked), and ONE short phrase at the top (one or two lines,
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

def mystery(draw_item, env_name, outfit, lines, qmark=(540, 1020), keeper=None, out='thumb', dim=0.35,
            sizes=(170, 100, 76), colors=None, fit=(70, 660, 1010, 1820)):
    """lines: three short lines, top to bottom (big gold, white, gold). draw_item(pn) draws the hero item at full
    detail; only its outline is used (alpha above 90, so ground shadows drop out)."""
    CAM.drift = 0; CAM.set(0)
    im = Image.blend(env.get(env_name).convert('RGBA'), Image.new('RGBA', (W, H), (40, 34, 30, 255)), dim)
    lay = new_layer(); draw_item(Pen(lay, cam=False))
    a = lay.resize((W, H), Image.BOX).split()[3].point(lambda v: 255 if v > 90 else 0)
    fit_px = None; fit_sc = 1.0
    if fit:   # scale and centre the whole silhouette inside the fit box so the item is fully visible
        bb = a.getbbox()
        if bb:
            x0, y0, x1, y1 = fit
            sc_ = min((x1 - x0) / (bb[2] - bb[0]), (y1 - y0) / (bb[3] - bb[1]))
            piece = a.crop(bb).resize((int((bb[2] - bb[0]) * sc_), int((bb[3] - bb[1]) * sc_)), Image.LANCZOS)
            a = Image.new('L', (W, H), 0)
            px, py = (x0 + x1 - piece.width) // 2, (y0 + y1 - piece.height) // 2
            a.paste(piece, (px, py)); a = a.point(lambda v: 255 if v > 127 else 0)
            fit_px, fit_sc = (px, py), 1.0
            import numpy as np
            m = np.asarray(a) > 0; ys_, xs_ = np.nonzero(m)
            top = ys_ < np.percentile(ys_, 55)          # centre of the upper body, not the stand
            qmark = (int(xs_[top].mean()), int(ys_[top].mean()) + 50)
    a = a.filter(ImageFilter.GaussianBlur(1.2))
    glow = a.filter(ImageFilter.GaussianBlur(26)).point(lambda v: min(255, int(v * 1.6)))
    L = lambda c: Image.new('L', (W, H), c)
    im.alpha_composite(Image.merge('RGBA', (L(GLOW[0]), L(GLOW[1]), L(GLOW[2]), glow)))
    im.alpha_composite(Image.merge('RGBA', (L(SIL[0]), L(SIL[1]), L(SIL[2]), a)))
    lay2 = new_layer(); pn = Pen(lay2, cam=False)
    outlined(pn, qmark[0], qmark[1], '?', 380, GOLD)
    if keeper:
        kx, ky, kk = keeper
        figure(pn, kx, ky, kk, -1, pose('idle', head=-6), outfit, 'surprised', look=(-0.9, -0.4))
    cols = colors or (GOLD, WHITE, GOLD)
    for y, col, txt, sz in zip((230, 400, 545), cols, lines, sizes):
        outlined(pn, 540, y, txt, sz, col)
    flatten(im, lay2)
    v = im.convert('RGB'); v.save(f'{out}_mystery_vertical.png')
    # 16:9: same silhouette refitted on the right, phrase on the left sized to fit its half
    h = Image.blend(env.get(env_name).convert('RGB').resize((1280, 2276)).crop((0, 800, 1280, 1520)),
                    Image.new('RGB', (1280, 720), (40, 34, 30)), dim).convert('RGBA')
    bb = a.getbbox()
    if bb:
        bx0, by0, bx1, by1 = 690, 70, 1240, 670
        sc2 = min((bx1 - bx0) / (bb[2] - bb[0]), (by1 - by0) / (bb[3] - bb[1]))
        sz2 = (int((bb[2] - bb[0]) * sc2), int((bb[3] - bb[1]) * sc2))
        m2 = Image.new('L', (1280, 720), 0); px2, py2 = (bx0 + bx1 - sz2[0]) // 2, (by0 + by1 - sz2[1]) // 2
        m2.paste(a.crop(bb).resize(sz2, Image.LANCZOS), (px2, py2))
        g2 = m2.filter(ImageFilter.GaussianBlur(16)).point(lambda v: min(255, int(v * 1.6)))
        L2 = lambda c: Image.new('L', (1280, 720), c)
        h.alpha_composite(Image.merge('RGBA', (L2(GLOW[0]), L2(GLOW[1]), L2(GLOW[2]), g2)))
        h.alpha_composite(Image.merge('RGBA', (L2(SIL[0]), L2(SIL[1]), L2(SIL[2]), m2)))
        qx2 = px2 + (qmark[0] - fit_px[0]) * sc2 / fit_sc if fit_px else (bx0 + bx1) // 2
        qy2 = py2 + (qmark[1] - fit_px[1]) * sc2 / fit_sc if fit_px else (by0 + by1) // 2
    d = ImageDraw.Draw(h)
    if bb: d.text((qx2, qy2), '?', font=_font(230), fill=GOLD, anchor='mm', stroke_width=10, stroke_fill=INK)
    cols = colors or (GOLD, WHITE, GOLD)
    n = len(lines); fs = 150
    while fs > 40 and max(d.textlength(t_, font=_font(fs)) for t_ in lines) > 620: fs -= 6
    y0 = 360 - (n - 1) * fs * 0.55
    for i, (txt, col) in enumerate(zip(lines, cols)):
        d.text((345, y0 + i * fs * 1.1), txt, font=_font(fs), fill=col, anchor='mm', stroke_width=10, stroke_fill=INK)
    h = h.convert('RGB')
    h.save(f'{out}_mystery_16x9.png')
    return v, h

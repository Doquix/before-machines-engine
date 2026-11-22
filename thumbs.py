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
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageChops
import random, math
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
            sizes=(170, 100, 76), colors=None, fit=(70, 660, 1010, 1820), drama=True, reticle=None):
    """lines: three short lines, top to bottom (big gold, white, gold). draw_item(pn) draws the hero item at full
    detail; only its outline is used (alpha above 90, so ground shadows drop out)."""
    CAM.drift = 0; CAM.set(0)
    im = Image.blend(env.get(env_name).convert('RGBA'), Image.new('RGBA', (W, H), (40, 34, 30, 255)), dim)
    if drama:
        im = _drama_bg(im, dim)
    bgd = im.copy()
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
    if drama:   # hot back light behind the item: a second, wider, redder glow
        g2 = a.filter(ImageFilter.GaussianBlur(70)).point(lambda v: min(255, int(v * 1.3)))
        im.alpha_composite(Image.merge('RGBA', (L(230), L(70), L(30), g2)))
        im.alpha_composite(Image.merge('RGBA', (L(GLOW[0]), L(GLOW[1]), L(GLOW[2]), glow)))
    im.alpha_composite(Image.merge('RGBA', (L(SIL[0]), L(SIL[1]), L(SIL[2]), a)))
    if drama:
        sh_ = ImageChops.offset(a, -7, 7)                    # light from the top right: a thin lit edge
        rim = ImageChops.subtract(a, sh_).filter(ImageFilter.GaussianBlur(1.5))
        im.alpha_composite(Image.merge('RGBA', (L(255), L(214), L(130), rim)))
        im = _embers(im)
        if reticle: im = _reticle(im, qmark[0], qmark[1] - 20, reticle if isinstance(reticle, (int, float)) else 230)
        im = _vignette(im)
    lay2 = new_layer(); pn = Pen(lay2, cam=False)
    outlined(pn, qmark[0], qmark[1], '?', 380, GOLD)
    if keeper:
        kx, ky, kk = keeper
        figure(pn, kx, ky, kk, -1, pose('idle', head=-6), outfit, 'surprised', look=(-0.9, -0.4))
    cols = colors or (GOLD, WHITE, GOLD)
    if drama:
        tl = new_layer(); tp = Pen(tl, cam=False)
        for y, txt, sz in zip((230, 400, 545), lines, sizes): tp.text(540, y, txt, sz, (255, 90, 30), 'Black', 'mm', True)
        halo = tl.resize((W, H), Image.BOX).filter(ImageFilter.GaussianBlur(28)); im.alpha_composite(halo); im.alpha_composite(halo)
    for y, col, txt, sz in zip((230, 400, 545), cols, lines, sizes):
        outlined(pn, 540, y, txt, sz, col)
    flatten(im, lay2)
    v = im.convert('RGB'); v.save(f'{out}_mystery_vertical.png')
    # 16:9: same silhouette refitted on the right, phrase on the left sized to fit its half
    h = Image.blend(env.get(env_name).convert('RGB').resize((1280, 2276)).crop((0, 800, 1280, 1520)),
                    Image.new('RGB', (1280, 720), (40, 34, 30)), dim).convert('RGBA')
    if drama:   # reuse the vertical's graded look: crop its middle band as the backdrop, darkened
        hb = bgd.crop((0, 760, 1080, 1368)).resize((1280, 720))
        hb.alpha_composite(Image.new('RGBA', (1280, 720), (10, 6, 8, 70)))
        h = hb
    bb = a.getbbox()
    if bb:
        bx0, by0, bx1, by1 = 690, 70, 1240, 670
        sc2 = min((bx1 - bx0) / (bb[2] - bb[0]), (by1 - by0) / (bb[3] - bb[1]))
        sz2 = (int((bb[2] - bb[0]) * sc2), int((bb[3] - bb[1]) * sc2))
        m2 = Image.new('L', (1280, 720), 0); px2, py2 = (bx0 + bx1 - sz2[0]) // 2, (by0 + by1 - sz2[1]) // 2
        m2.paste(a.crop(bb).resize(sz2, Image.LANCZOS), (px2, py2))
        g2 = m2.filter(ImageFilter.GaussianBlur(16)).point(lambda v: min(255, int(v * 1.6)))
        L2 = lambda c: Image.new('L', (1280, 720), c)
        if drama: h.alpha_composite(Image.merge('RGBA', (L2(230), L2(70), L2(30), m2.filter(ImageFilter.GaussianBlur(45)))))
        h.alpha_composite(Image.merge('RGBA', (L2(GLOW[0]), L2(GLOW[1]), L2(GLOW[2]), g2)))
        h.alpha_composite(Image.merge('RGBA', (L2(SIL[0]), L2(SIL[1]), L2(SIL[2]), m2)))
        if drama: h.alpha_composite(Image.merge('RGBA', (L2(255), L2(214), L2(130), ImageChops.subtract(m2, ImageChops.offset(m2, -4, 4)))))
        qx2 = px2 + (qmark[0] - fit_px[0]) * sc2 / fit_sc if fit_px else (bx0 + bx1) // 2
        qy2 = py2 + (qmark[1] - fit_px[1]) * sc2 / fit_sc if fit_px else (by0 + by1) // 2
    d = ImageDraw.Draw(h)
    if bb and drama and reticle:
        R_ = 150; c_ = (230, 40, 30)
        d.ellipse([qx2 - R_, qy2 - R_, qx2 + R_, qy2 + R_], outline=c_, width=7)
        d.ellipse([qx2 - R_ * .45, qy2 - R_ * .45, qx2 + R_ * .45, qy2 + R_ * .45], outline=c_, width=4)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.line([(qx2 + dx * R_ * .2, qy2 + dy * R_ * .2), (qx2 + dx * R_ * 1.25, qy2 + dy * R_ * 1.25)], fill=c_, width=6)
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


def _drama_bg(im, dim):
    """Dark storm grade: crush the background toward night red, with a hot spot of light behind the item."""
    base = Image.blend(im, Image.new('RGBA', (W, H), (16, 10, 12, 255)), 0.55)
    glow = Image.new('L', (W, H), 0); d = ImageDraw.Draw(glow)
    d.ellipse([60, 520, 1020, 1640], fill=255); glow = glow.filter(ImageFilter.GaussianBlur(160))
    hot = Image.new('RGBA', (W, H), (190, 70, 30, 255)); hot.putalpha(glow.point(lambda v: int(v * 0.75)))
    base.alpha_composite(hot)
    # light shafts from the top right
    sh = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sh)
    for x0, w in ((760, 120), (900, 70), (620, 60)):
        d.polygon([(x0, 0), (x0 + w, 0), (x0 - 340 + w * 2, H), (x0 - 520, H)], fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(40))
    lite = Image.new('RGBA', (W, H), (255, 200, 140, 255)); lite.putalpha(sh)
    base.alpha_composite(lite)
    return base

def _embers(im, n=55, seed=11):
    """Sparks rising in the hot light (tails point down, they drift up)."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(40, W - 40), rnd.uniform(560, H - 80); r = rnd.choice((2, 2, 3, 3, 4))
        col = rnd.choice(((255, 190, 90), (255, 150, 70), (255, 226, 160)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (rnd.randint(170, 255),))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4))); im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))
    return im

def _reticle(im, x, y, r=130):
    """Red scope reticle (sniper hint) on a target point."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); c = (230, 40, 30, 235)
    d.ellipse([x - r, y - r, x + r, y + r], outline=c, width=9)
    d.ellipse([x - r * .45, y - r * .45, x + r * .45, y + r * .45], outline=c, width=5)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([(x + dx * r * .2, y + dy * r * .2), (x + dx * r * 1.25, y + dy * r * 1.25)], fill=c, width=8)
    g = lay.filter(ImageFilter.GaussianBlur(8)); im.alpha_composite(g); im.alpha_composite(lay)
    return im

def _vignette(im):
    v = Image.new('L', (W, H), 0); d = ImageDraw.Draw(v)
    d.ellipse([-260, -160, W + 260, H + 160], fill=255); v = v.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new('RGBA', (W, H), (6, 4, 6, 255)); dark.putalpha(v.point(lambda p: int((255 - p) * 0.9)))
    im.alpha_composite(dark)
    return im

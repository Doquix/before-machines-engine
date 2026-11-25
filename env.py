"""Painted environments, cached, blurred and graded so figures read clearly."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from lib import W, H, INK, PARCH

def sky(top, bot, glow=None, gy=0.45):
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(top) + (np.array(bot) - np.array(top)) * yy ** 0.9
    arr = np.repeat(arr, W, axis=1)
    if glow:
        Y, X = np.mgrid[0:H, 0:W]
        d = np.sqrt(((X / W - 0.62)) ** 2 + ((Y / H - gy) * 1.6) ** 2)
        arr = arr + np.array(glow) * np.exp(-(d / 0.35) ** 2)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')

def ridge(w, base, amp, seed, freqs=(0.9, 2.2, 4.6, 9.0), pts=200):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in freqs]
    out = []
    for i in range(pts + 1):
        x = i / pts
        y = sum(math.sin(x * f * 6.28 + p) / (1 + j * 1.6) for j, (f, p) in enumerate(zip(freqs, ph)))
        out.append((x * w, base - amp * y))
    return out

def hill_layer(img, base, amp, col, seed, w=W, freqs=(0.9, 2.2, 4.6, 9.0)):
    d = ImageDraw.Draw(img)
    pts = ridge(w, base, amp, seed, freqs)
    d.polygon(pts + [(w, H), (0, H)], fill=col)

def clouds(img, seed, col, n=7, y0=150, y1=650):
    rnd = random.Random(seed)
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for _ in range(n):
        cx, cy = rnd.uniform(-100, img.width + 100), rnd.uniform(y0, y1); s = rnd.uniform(0.7, 1.6)
        for _ in range(6):
            dx, dy = rnd.uniform(-120, 120) * s, rnd.uniform(-20, 20) * s; r = rnd.uniform(40, 80) * s
            d.ellipse([cx + dx - r * 1.6, cy + dy - r * .6, cx + dx + r * 1.6, cy + dy + r * .6], fill=col)
    lay = lay.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(lay)

def tent(d, x, y, s, col, stripe):
    w = 70 * s; hw = 46 * s; rh = 60 * s
    d.rectangle([x - w, y - hw, x + w, y], fill=col, outline=INK, width=max(1, int(3 * s)))
    for i in range(-3, 4, 2):
        d.rectangle([x + i * w / 4 - w / 8, y - hw, x + i * w / 4 + w / 8, y], fill=stripe)
    d.polygon([(x - w - 8 * s, y - hw), (x, y - hw - rh), (x + w + 8 * s, y - hw)], fill=col, outline=INK)
    d.line([(x, y - hw - rh), (x, y - hw - rh - 30 * s)], fill=INK, width=max(1, int(3 * s)))
    d.polygon([(x, y - hw - rh - 30 * s), (x + 26 * s, y - hw - rh - 24 * s), (x, y - hw - rh - 16 * s)], fill=(176, 34, 38))
    d.polygon([(x - w * .25, y), (x, y - hw * .8), (x + w * .25, y)], fill=(40, 30, 24))

def grade(img, blur=3.5, sat=0.72, bright=0.9, cap=True):
    im = img.convert('RGB')
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(0.86)
    im = ImageEnhance.Brightness(im).enhance(bright)
    arr = np.asarray(im).astype(np.float32)
    Y, X = np.mgrid[0:H, 0:W]
    vig = np.clip(np.sqrt((X / W - .5) ** 2 + ((Y / H - .48) * 1.3) ** 2) / .85, 0, 1) ** 2
    arr *= (1 - 0.38 * vig)[..., None]
    if cap:
        z = np.exp(-((Y - 1450) / 210.0) ** 2)
        arr *= (1 - 0.32 * z)[..., None]
    n = np.random.default_rng(9).standard_normal((H, W, 1)) * 2.0
    return Image.fromarray(np.clip(arr + n, 0, 255).astype(np.uint8))

DUSK = ((70, 84, 112), (232, 170, 120), (60, 30, 0))
OCHIL = (92, 98, 118); FAR = (118, 116, 122); CARSE = (104, 112, 80); CARSE2 = (82, 92, 64)

def env_dusk():
    im = sky(DUSK[0], DUSK[1], DUSK[2], 0.5)
    clouds(im, 3, (250, 214, 186, 120))
    hill_layer(im, 1020, 70, OCHIL, 4)
    hill_layer(im, 1120, 40, FAR, 8, freqs=(1.4, 3.3, 6.0))
    hill_layer(im, 1240, 14, CARSE, 2, freqs=(1.5, 4.0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(2)
    for _ in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(1260, 1900)
        d.ellipse([x - 60, y - 6, x + 60, y + 6], fill=CARSE2)
    return grade(im, blur=3)

def env_camp():
    im = sky(DUSK[0], DUSK[1], DUSK[2], 0.42)
    clouds(im, 5, (250, 214, 186, 110))
    hill_layer(im, 900, 60, OCHIL, 4)
    hill_layer(im, 1030, 26, FAR, 8, freqs=(1.4, 3.3, 6.0))
    d = ImageDraw.Draw(im)
    # distant crag with castle silhouette at upper right
    crag = [(700, 1040), (760, 900), (820, 860), (900, 850), (960, 880), (1010, 960), (1080, 1040)]
    d.polygon(crag, fill=(74, 70, 78))
    for x0, w_, h_ in ((800, 160, 40), (830, 24, 70), (920, 24, 64), (870, 30, 54)):
        d.rectangle([x0, 850 - h_, x0 + w_, 852], fill=(84, 80, 90))
    hill_layer(im, 1180, 16, CARSE, 2, freqs=(1.5, 4.0))
    d = ImageDraw.Draw(im)
    for i, (x, y, s) in enumerate(((120, 1150, 0.9), (330, 1130, 0.7), (520, 1160, 1.0), (960, 1170, 0.95), (720, 1120, 0.6))):
        tent(d, x, y, s, (226, 214, 188), (176, 60, 52) if i % 2 else (90, 96, 140))
    # palisade stakes
    for x in range(-10, W + 20, 26):
        h_ = 70 + (x * 37 % 23)
        d.polygon([(x, 1240), (x + 10, 1240 - h_), (x + 20, 1240)], fill=(96, 70, 46), outline=INK)
    d.rectangle([0, 1240, W, H], fill=CARSE2)
    rnd = random.Random(4)
    for _ in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(1250, 1900)
        d.ellipse([x - 40, y - 4, x + 40, y + 4], fill=(70, 80, 56))
    return grade(im, blur=4)

def env_wallview():
    """Looking out from the castle wall: wide plain far below with the English camp."""
    im = sky((96, 112, 140), (226, 186, 148), (40, 20, 0), 0.6)
    clouds(im, 8, (246, 222, 200, 120), y0=200, y1=900)
    hill_layer(im, 1000, 40, FAR, 3, freqs=(1.1, 2.7, 6.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1040, W, H], fill=CARSE)
    hill_layer(im, 1060, 8, CARSE2, 9, freqs=(3.0, 7.0))
    d = ImageDraw.Draw(im)
    for i, x in enumerate(range(80, 1050, 110)):
        tent(d, x, 1160 + (i % 3) * 18, 0.32, (226, 214, 188), (176, 60, 52))
    return grade(im, blur=4.5)

def env_parch():
    base = np.array(PARCH, np.float32)
    Y, X = np.mgrid[0:H, 0:W]
    g = np.exp(-(((X / W - .5) ** 2) + ((Y / H - .45) * 1.2) ** 2) / .3)
    arr = np.zeros((H, W, 3), np.float32) + base * (0.86 + 0.14 * g)[..., None]
    im = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im, 'RGBA')
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(120, 100, 70, 28), width=2)
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(120, 100, 70, 28), width=2)
    return grade(im, blur=0, sat=0.9, bright=0.97)

def env_ritual():
    Y, X = np.mgrid[0:H, 0:W]
    d = np.sqrt(((X - 540) / W) ** 2 + ((Y - 820) / W) ** 2)
    a = np.arctan2(Y - 820, X - 540)
    rays = 0.5 + 0.5 * np.sign(np.sin(a * 14))
    base = np.array((34, 26, 22), np.float32); glow = np.array((120, 60, 34), np.float32)
    arr = base + glow * np.exp(-(d / 0.5) ** 2)[..., None] * (0.75 + 0.25 * rays[..., None])
    return grade(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), blur=2, sat=1.0, bright=1.0)

def parallax_layers():
    """Wide layers for the tracking shot: far hills (0.12), near hills (0.38), ground drawn live."""
    WW = 4200
    far = Image.new('RGBA', (WW, H), (0, 0, 0, 0)); hill_layer(far, 1000, 80, OCHIL, 4, w=WW)
    near = Image.new('RGBA', (WW, H), (0, 0, 0, 0)); hill_layer(near, 1180, 50, (88, 98, 70), 7, w=WW, freqs=(1.2, 3.0, 6.5))
    far = far.filter(ImageFilter.GaussianBlur(4)); near = near.filter(ImageFilter.GaussianBlur(2.5))
    sk = sky(DUSK[0], DUSK[1], DUSK[2], 0.5); clouds(sk, 3, (250, 214, 186, 120))
    return grade(sk, blur=2, cap=False), far, near

ENV = {}
def get(name):
    if name not in ENV:
        ENV[name] = globals()['env_' + name]()
    return ENV[name]

if __name__ == '__main__':
    names = ['dusk', 'camp', 'wallview', 'parch', 'ritual']
    ims = [get(n).resize((270, 480)) for n in names]
    o = Image.new('RGB', (270 * len(ims), 480))
    for i, im in enumerate(ims): o.paste(im, (i * 270, 0))
    o.save('env_sheet.png')

# ---------------- E021 Roman scorpio ----------------
GREY = ((150, 160, 170), (214, 208, 190), (20, 16, 6))
def env_yard():
    """Modern back yard: pale sky, wooden fence, lawn, a shrub or two."""
    im = sky((150, 190, 222), (232, 236, 226), (30, 20, 0), 0.5)
    clouds(im, 11, (255, 255, 255, 150), n=6, y0=200, y1=700)
    d = ImageDraw.Draw(im)
    hill_layer(im, 1040, 18, (138, 160, 120), 3, freqs=(1.2, 3.0))
    d = ImageDraw.Draw(im)
    for cx, cy, r in ((140, 1000, 120), (930, 990, 140), (300, 1010, 80)):
        d.ellipse([cx - r, cy - r * .8, cx + r, cy + r * .8], fill=(92, 120, 76))
    for x in range(-20, W + 40, 64):    # fence boards
        d.polygon([(x, 1180), (x, 1030), (x + 28, 1010), (x + 58, 1030), (x + 58, 1180)], fill=(196, 168, 128), outline=(120, 96, 70))
    d.rectangle([0, 1070, W, 1084], fill=(170, 142, 104)); d.rectangle([0, 1140, W, 1154], fill=(170, 142, 104))
    d.rectangle([0, 1180, W, H], fill=(122, 156, 92))
    rnd = random.Random(6)
    for _ in range(260):
        x, y = rnd.uniform(0, W), rnd.uniform(1190, 1900)
        d.line([(x, y), (x + rnd.uniform(-4, 4), y - rnd.uniform(8, 18))], fill=(96, 130, 70), width=2)
    return grade(im, blur=3, sat=0.8)

def _rcamp(top, bot, glow, dark=1.0):
    im = sky(top, bot, glow, 0.4)
    clouds(im, 21, (236, 232, 224, 120), n=8)
    hill_layer(im, 950, 60, (126, 134, 128), 4)
    hill_layer(im, 1060, 26, (112, 120, 100), 8, freqs=(1.4, 3.3, 6.0))
    d = ImageDraw.Draw(im)
    for i, (x, y, s) in enumerate(((140, 1150, 0.8), (380, 1130, 0.6), (820, 1150, 0.85), (1000, 1125, 0.55))):
        w_ = 80 * s; h_ = 70 * s          # leather tents (papilio): low ridge tents
        d.polygon([(x - w_, y), (x - w_ * .7, y - h_), (x + w_ * .7, y - h_), (x + w_, y)], fill=(176, 140, 100), outline=INK)
        d.polygon([(x - w_ * .2, y), (x, y - h_ * .8), (x + w_ * .2, y)], fill=(70, 52, 38))
        for k in range(-2, 3): d.line([(x + k * w_ * .3, y), (x + k * w_ * .24, y - h_)], fill=(150, 116, 80), width=2)
    for x in range(-10, W + 20, 24):    # stake rampart of the camp
        d.polygon([(x, 1240), (x + 9, 1186 - (x * 37 % 17)), (x + 18, 1240)], fill=(110, 84, 56), outline=INK)
    d.rectangle([0, 1240, W, H], fill=(140, 124, 92))
    rnd = random.Random(4)
    for _ in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(1250, 1900)
        d.ellipse([x - 40, y - 4, x + 40, y + 4], fill=(120, 106, 78))
    return grade(im, blur=4, bright=0.92 * dark)
def env_rcamp(): return _rcamp((150, 168, 186), (226, 216, 194), (40, 24, 0))
def env_rcamp_rain(): return _rcamp((96, 104, 114), (160, 160, 156), None, 0.85)

def env_avaricum():
    """Night at Avaricum: dark sky, fire glow low on the left where the terrace burns."""
    im = sky((18, 20, 34), (70, 46, 40), (120, 50, 10), 0.75)
    d = ImageDraw.Draw(im, 'RGBA')
    rnd = random.Random(3)
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 800); r = rnd.choice((1, 1, 2))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 226, 210, 160))
    hill_layer(im, 1180, 30, (30, 26, 34), 5)
    return grade(im, blur=2, sat=0.9, bright=1.0, cap=False)

def env_downs():
    """Dorset downs for Hod Hill: grey green sky, chalk ridges."""
    im = sky((160, 176, 186), (224, 222, 204), (20, 14, 0), 0.5)
    clouds(im, 31, (244, 244, 236, 130), n=7)
    hill_layer(im, 1000, 90, (128, 146, 106), 4, freqs=(0.6, 1.5, 3.0))
    hill_layer(im, 1120, 50, (116, 136, 92), 9, freqs=(0.8, 2.0, 4.0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1250, W, H], fill=(110, 130, 84))
    return grade(im, blur=3.5, sat=0.8)

# ---------------- E022 Persian yakhchal: central plateau desert (Yazd) ----------------
def _ykmount(im, base, col, seed, amp=70):
    hill_layer(im, base, amp, col, seed, freqs=(0.7, 1.9, 4.2, 9.0))

def _ykstars(im, seed, n=420, band=True):
    d = ImageDraw.Draw(im, 'RGBA'); rnd = random.Random(seed)
    if band:   # faint Milky Way band across the sky
        lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for i in range(60):
            u = i / 60; x = -100 + u * (W + 200); y = 150 + u * 520 + rnd.uniform(-40, 40)
            r = rnd.uniform(70, 140); dl.ellipse([x - r, y - r * .5, x + r, y + r * .5], fill=(150, 160, 200, 18))
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 1000) ** 1.0; r = rnd.choice((0.8, 1, 1, 1.4, 2.0))
        a = int(rnd.uniform(120, 255) * (1 - y / 1300))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 238, 255, a))

def env_ykday():
    """Winter day on the plateau: pale sky, blue grey mountains far off, flat ochre plain."""
    im = sky((150, 178, 206), (236, 226, 204), (40, 26, 0), 0.55)
    clouds(im, 41, (250, 248, 240, 90), n=4, y0=250, y1=600)
    _ykmount(im, 1000, (150, 156, 170), 5, 80)
    _ykmount(im, 1060, (176, 164, 140), 9, 26)
    d = ImageDraw.Draw(im); d.rectangle([0, 1100, W, H], fill=(198, 172, 128))
    rnd = random.Random(2)
    for _ in range(120):
        x, y = rnd.uniform(0, W), rnd.uniform(1110, 1900); d.ellipse([x - 30, y - 3, x + 30, y + 3], fill=(184, 158, 116))
    return grade(im, blur=3.5, sat=0.8)

def env_yknight():
    """Clear winter night: deep blue sky full of stars, dark mountains, dim plain."""
    im = sky((8, 12, 30), (36, 48, 82), (10, 14, 30), 0.7)
    _ykstars(im, 7)
    _ykmount(im, 1000, (22, 26, 44), 5, 80)
    _ykmount(im, 1060, (34, 38, 56), 9, 26)
    d = ImageDraw.Draw(im); d.rectangle([0, 1100, W, H], fill=(44, 46, 62))
    return grade(im, blur=1.2, sat=1.0, bright=1.0, cap=True)

def env_yknightsky():
    """Sky only, for the tilt up into the stars (no horizon)."""
    im = sky((6, 10, 26), (24, 32, 62), None, 0.7)
    _ykstars(im, 13, n=650)
    return grade(im, blur=0.8, sat=1.0, bright=1.0, cap=True)

def env_ykdawn():
    """Winter dawn: cold blue above, warm band at the horizon, for harvesting the ice."""
    im = sky((70, 96, 140), (236, 186, 140), (70, 40, 10), 0.6)
    _ykmount(im, 1000, (96, 98, 122), 5, 80)
    _ykmount(im, 1060, (130, 116, 110), 9, 26)
    d = ImageDraw.Draw(im); d.rectangle([0, 1100, W, H], fill=(160, 134, 110))
    return grade(im, blur=3.5, sat=0.85)

def env_yksummer():
    """Midsummer: white hot sky, washed out mountains, bright plain."""
    im = sky((196, 206, 214), (248, 232, 196), (60, 40, 0), 0.5)
    _ykmount(im, 1000, (204, 196, 186), 5, 80)
    _ykmount(im, 1060, (214, 192, 150), 9, 26)
    d = ImageDraw.Draw(im); d.rectangle([0, 1100, W, H], fill=(226, 196, 140))
    return grade(im, blur=4, sat=0.85, bright=1.02)

# ---------------- E023 Alesia, Burgundy, late summer 52 BC ----------------
def env_alday():
    """Late summer day in the Auxois hills: soft blue sky, rolling green and gold hills, a hazy far ridge."""
    im = sky((132, 168, 204), (230, 226, 206), (40, 30, 0), 0.5)
    clouds(im, 23, (252, 250, 244, 120), n=6, y0=220, y1=700)
    hill_layer(im, 960, 60, (128, 146, 150), 3, freqs=(0.5, 1.2, 2.4, 4.0))
    hill_layer(im, 1040, 50, (128, 146, 96), 7, freqs=(0.5, 1.2, 2.4, 4.0))
    hill_layer(im, 1110, 30, (150, 156, 90), 11, freqs=(0.5, 1.2, 2.4, 4.0))
    d = ImageDraw.Draw(im); d.rectangle([0, 1160, W, H], fill=(140, 150, 86))
    return grade(im, blur=3.5, sat=0.8)

def env_alnight():
    """Moonlit night over the hills: deep blue, stars, a moon low on the right, black hill shapes."""
    im = sky((10, 16, 36), (40, 56, 90), (20, 24, 40), 0.7)
    _ykstars(im, 29, n=260, band=False)
    dm = ImageDraw.Draw(im, 'RGBA')
    dm.ellipse([780, 300, 880, 400], fill=(236, 232, 210, 255))
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); dl.ellipse([700, 220, 960, 480], fill=(220, 220, 200, 50))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)))
    hill_layer(im, 980, 60, (26, 32, 50), 3, freqs=(0.5, 1.2, 2.4, 4.0))
    hill_layer(im, 1060, 45, (32, 40, 52), 7, freqs=(0.5, 1.2, 2.4, 4.0))
    d = ImageDraw.Draw(im); d.rectangle([0, 1120, W, H], fill=(34, 42, 50))
    return grade(im, blur=1.2, sat=1.0, bright=1.0, cap=True)

def env_aldusk():
    """Battle at dusk: smoky orange sky, dark hills, haze."""
    im = sky((90, 70, 76), (232, 150, 96), (90, 40, 10), 0.6)
    clouds(im, 31, (120, 90, 90, 110), n=7, y0=200, y1=800)
    hill_layer(im, 980, 60, (96, 74, 78), 3, freqs=(0.5, 1.2, 2.4, 4.0))
    hill_layer(im, 1060, 45, (88, 80, 62), 7, freqs=(0.5, 1.2, 2.4, 4.0))
    d = ImageDraw.Draw(im); d.rectangle([0, 1120, W, H], fill=(98, 96, 62))
    return grade(im, blur=3.0, sat=0.85)

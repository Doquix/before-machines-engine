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

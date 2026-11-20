"""Style frame test (E020 polish): painted, blurred arena background + a rendered character
(specific face with shading, shaped hair, rendered clothing, thin line limbs, scene lighting)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H, S = 1080, 1920, 2           # supersample 2x
WW, HH = W * S, H * S
INK = (28, 22, 18)
rnd = random.Random(4)

def bez(p0, p1, p2, p3=None, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts

def sc(pts): return [(x * S, y * S) for x, y in pts]

def noise(w, h, scales=((8, 1.0), (24, 0.5), (64, 0.25), (160, 0.12)), seed=1):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); tot = 0
    for s, a in scales:
        g = r.random((s * h // w + 2, s + 2)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * a; tot += a
    return acc / tot

def lerpc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ======================= background: Colosseum interior, late afternoon =======================
def background():
    w, h = W, H
    img = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    top, mid, low = np.array([62, 92, 140]), np.array([236, 176, 112]), np.array([250, 214, 160])
    sky = np.where(yy < 0.22, top + (mid - top) * (yy / 0.22), mid + (low - mid) * np.clip((yy - 0.22) / 0.2, 0, 1))
    img[:] = sky[:, None, :]
    # clouds: fractal noise, lit from the low sun on the right
    n = noise(w, h, seed=3)
    cl = np.clip((n - 0.52) * 3.2, 0, 1)[..., None] * (yy < 0.42)[..., None]
    cloud_col = np.array([255, 226, 190]) * 0.55 + np.array([120, 90, 110]) * 0.45
    img = img * (1 - cl * 0.8) + cloud_col * cl * 0.8
    sun = np.exp(-(((np.arange(w)[None, :] - 860) / 260) ** 2 + ((np.arange(h)[:, None] - 520) / 260) ** 2))[..., None]
    img = img + np.array([255, 210, 140]) * sun * 0.55
    bg = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(bg, 'RGBA')
    # far wall of the cavea: tiers of arches receding in a shallow curve
    def tier(y0, hgt, arch_w, col, dark, n_off=0):
        for x in range(-arch_w, w + arch_w, arch_w):
            curve = 40 * math.cos((x - w / 2) / w * math.pi)
            yb = y0 - curve
            d.rectangle([x, yb - hgt, x + arch_w, yb], fill=col)
            ax0, ax1 = x + arch_w * 0.18, x + arch_w * 0.82
            d.rectangle([ax0, yb - hgt * 0.62, ax1, yb], fill=dark)
            d.ellipse([ax0, yb - hgt * 0.62 - (ax1 - ax0) / 2, ax1, yb - hgt * 0.62 + (ax1 - ax0) / 2], fill=dark)
            d.line([(x, yb - hgt), (x + arch_w, yb - hgt)], fill=lerpc(col, (255, 230, 190), 0.4), width=5)
            d.rectangle([x - 4, yb - hgt, x + 6, yb], fill=lerpc(col, (90, 60, 50), 0.25))   # pilaster
    tier(560, 120, 92, (196, 150, 112), (104, 72, 62))
    tier(680, 120, 104, (206, 160, 118), (96, 64, 54))
    tier(810, 130, 118, (214, 168, 124), (88, 58, 48))
    # seating band with a crowd of tiny figures
    for row in range(7):
        y = 830 + row * 26
        d.rectangle([0, y, w, y + 26], fill=lerpc((190, 150, 112), (168, 126, 94), row / 7))
        for x in range(rnd.randint(0, 14), w, 14):
            c = rnd.choice([(150, 60, 50), (210, 196, 170), (120, 110, 90), (230, 220, 200), (90, 70, 60), (180, 140, 60)])
            d.ellipse([x, y + 2, x + 9, y + 11], fill=lerpc(c, (200, 170, 140), 0.3))
            d.rectangle([x + 1, y + 10, x + 8, y + 24], fill=c)
    # velarium masts and a red awning edge
    for x in range(30, w, 150):
        d.line([(x, 400), (x, 560)], fill=(120, 84, 60), width=6)
    d.polygon([(0, 380), (w, 360), (w, 410), (0, 430)], fill=(160, 54, 40, 210))
    # podium wall
    d.rectangle([0, 1010, w, 1090], fill=(214, 186, 150))
    for x in range(0, w, 160):
        d.rectangle([x + 20, 1026, x + 140, 1080], fill=(178, 146, 112))
    d.line([(0, 1010), (w, 1010)], fill=(250, 230, 200), width=4)
    # sand: warm gradient, raking light, footprints, texture
    sand = np.zeros((H - 1090, w, 3), np.float32)
    ys = np.linspace(0, 1, H - 1090)[:, None]
    sand[:] = (np.array([226, 186, 128]) * (1 - ys) + np.array([196, 150, 98]) * ys)[:, None, :]
    tex = noise(w, H - 1090, scales=((60, 1), (180, 0.6), (420, 0.4)), seed=8)[..., None]
    sand = sand * (0.9 + 0.2 * tex)
    bg.paste(Image.fromarray(np.clip(sand, 0, 255).astype(np.uint8)), (0, 1090))
    d = ImageDraw.Draw(bg, 'RGBA')
    for _ in range(90):
        x, y = rnd.uniform(0, w), rnd.uniform(1110, H)
        s = 0.4 + (y - 1090) / 900
        d.ellipse([x, y, x + 18 * s, y + 7 * s], fill=(150, 108, 70, 90))
    # depth of field + grade
    far = bg.filter(ImageFilter.GaussianBlur(7))
    mask = Image.new('L', (w, H), 0); md = ImageDraw.Draw(mask)
    for y in range(H):
        md.line([(0, y), (w, y)], fill=int(255 * np.clip((y - 1050) / 500, 0, 1)))
    near = bg.filter(ImageFilter.GaussianBlur(1.2))
    out = Image.composite(near, far, mask)
    return out

# ======================= trap door set in the sand (detailed, light from the right) =======================
def trapdoor(d, cx, y0, y1, w0, w1, op):
    p = [(cx - w0 / 2, y0), (cx + w0 / 2, y0), (cx + w1 / 2, y1), (cx - w1 / 2, y1)]
    d.polygon(sc(p), fill=(18, 12, 10))
    d.polygon(sc([p[0], p[1], (p[1][0] - 14, p[1][1] + 46), (p[0][0] + 14, p[0][1] + 46)]), fill=(62, 42, 32))
    for a, b in ((p[0], p[1]), (p[3], p[2]), (p[0], p[3]), (p[1], p[2])):
        d.line(sc([a, b]), fill=INK, width=18 * S // 2)
        d.line(sc([a, b]), fill=(132, 92, 58), width=11 * S // 2)
    # door panel standing open, planks, battens, iron strap hinges, light on the right edge
    lift = 360 * op
    q = [p[0], p[1], (cx + w0 * 0.54, y0 - lift), (cx - w0 * 0.54, y0 - lift)]
    d.polygon(sc(q), fill=(150, 104, 64), outline=INK, width=6 * S)
    for i in range(1, 6):
        u = i / 6
        a = (q[0][0] + (q[1][0] - q[0][0]) * u, q[0][1]); b = (q[3][0] + (q[2][0] - q[3][0]) * u, q[3][1])
        d.line(sc([a, b]), fill=(104, 70, 42), width=3 * S)
        d.line(sc([(a[0] + 4, a[1]), (b[0] + 4, b[1])]), fill=(186, 140, 92), width=1 * S)
    for u in (0.22, 0.72):
        a = (q[0][0], q[0][1] + (q[3][1] - q[0][1]) * u); b = (q[1][0], q[1][1] + (q[2][1] - q[1][1]) * u)
        d.line(sc([a, b]), fill=INK, width=20 * S // 2); d.line(sc([a, b]), fill=(118, 82, 50), width=13 * S // 2)
        for k in range(5):
            x = a[0] + (b[0] - a[0]) * (0.1 + 0.2 * k)
            d.ellipse(sc([(x - 3, a[1] - 3), (x + 3, a[1] + 3)]), fill=(70, 70, 74))
    for x in (q[0][0] + 36, q[1][0] - 36):
        d.rectangle(sc([(x - 9, y0 - 70), (x + 9, y0 + 4)]), fill=(84, 86, 92), outline=INK, width=3 * S)
    d.line(sc([q[1], q[2]]), fill=(236, 186, 120), width=4 * S)
    # glowing eyes in the dark
    for sd in (-1, 1):
        d.ellipse(sc([(cx + sd * 30 - 13, y0 + 34), (cx + sd * 30 + 13, y0 + 44)]), fill=(255, 196, 70))
        d.ellipse(sc([(cx + sd * 30 - 3, y0 + 34), (cx + sd * 30 + 3, y0 + 44)]), fill=(20, 10, 8))
    return p

# ======================= the venator, rendered =======================
SKIN, SKIN_SH, SKIN_HI = (214, 160, 116), (166, 112, 80), (238, 192, 150)
HAIR, HAIR_HI = (54, 36, 26), (110, 78, 56)
TUN, TUN_SH, TUN_HI = (196, 176, 134), (150, 128, 90), (226, 210, 172)
CLAV = (150, 52, 40)
def limb(d, pts, w=7):
    d.line(sc(pts), fill=INK, width=int(w * S), joint='curve')
    for p in (pts[0], pts[-1]):
        d.ellipse(sc([(p[0] - w / 2, p[1] - w / 2), (p[0] + w / 2, p[1] + w / 2)]), fill=INK)

def hand(d, x, y, r=15, ang=0.0, col=SKIN):
    d.ellipse(sc([(x - r, y - r * 0.85), (x + r, y + r * 0.85)]), fill=col, outline=INK, width=4 * S)
    for k in (-1, 0, 1):
        a = (x + math.cos(ang) * r * 0.2 + k * 6 * math.sin(ang), y + math.sin(ang) * r * 0.2 - k * 6 * math.cos(ang))
        d.line(sc([a, (a[0] + math.cos(ang) * 8, a[1] + math.sin(ang) * 8)]), fill=INK, width=2 * S)

def venabulum(d, a, b):
    d.line(sc([a, b]), fill=INK, width=13 * S)
    d.line(sc([a, b]), fill=(140, 96, 58), width=8 * S)
    d.line(sc([(a[0], a[1] - 2), (b[0], b[1] - 2)]), fill=(186, 136, 88), width=2 * S)
    ux, uy = b[0] - a[0], b[1] - a[1]; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L; nx, ny = -uy, ux
    s = (b[0] - ux * 20, b[1] - uy * 20)
    d.line(sc([s, (b[0] + ux * 6, b[1] + uy * 6)]), fill=INK, width=15 * S); d.line(sc([s, (b[0] + ux * 6, b[1] + uy * 6)]), fill=(96, 98, 106), width=10 * S)
    lug = (b[0] - ux * 2, b[1] - uy * 2)
    d.line(sc([(lug[0] - nx * 20, lug[1] - ny * 20), (lug[0] + nx * 20, lug[1] + ny * 20)]), fill=INK, width=10 * S)
    d.line(sc([(lug[0] - nx * 19, lug[1] - ny * 19), (lug[0] + nx * 19, lug[1] + ny * 19)]), fill=(120, 122, 130), width=5 * S)
    q = lambda u, v: (b[0] + ux * u + nx * v, b[1] + uy * u + ny * v)
    blade = [q(4, 0), q(30, 17), q(62, 11), q(96, 0), q(62, -11), q(30, -17)]
    d.polygon(sc(blade), fill=(170, 174, 182), outline=INK, width=4 * S)
    d.polygon(sc([q(6, 0), q(30, 15), q(62, 9), q(96, 0)]), fill=(214, 218, 226))
    d.line(sc([q(6, 0), q(94, 0)]), fill=(110, 112, 120), width=2 * S)
    d.line(sc([q(30, -16), q(62, -10)]), fill=(255, 236, 200), width=2 * S)   # rim light from the sun

def venator(d, img, x, y, k=1.0, look=1):
    """Front body, three quarter head turned toward +x. Feet at (x, y). Head about 45% of the figure."""
    P = lambda u, v: (x + u * k, y + v * k)
    # legs: thin ink lines, wrappings, shoes
    for hx, fx in ((-30, -58), (30, 52)):
        hip, knee, foot = P(hx, -260), P(hx * 1.4, -140), P(fx, -14)
        limb(d, [hip, knee, foot], 7 * k)
        for i in range(5):
            u = 0.12 + i * 0.16
            c = (knee[0] + (foot[0] - knee[0]) * u, knee[1] + (foot[1] - knee[1]) * u)
            d.polygon(sc([(c[0] - 13 * k, c[1] - 6 * k), (c[0] + 13 * k, c[1] - 1 * k), (c[0] + 13 * k, c[1] + 7 * k), (c[0] - 13 * k, c[1] + 2 * k)]),
                      fill=(184, 156, 112), outline=INK, width=3 * S)
        sh = P(fx + (12 if fx > 0 else -12), -6)
        d.chord(sc([(sh[0] - 32 * k, sh[1] - 24 * k), (sh[0] + 32 * k, sh[1] + 16 * k)]), 180, 360, fill=(92, 60, 36), outline=INK, width=4 * S)
        d.rectangle(sc([(sh[0] - 32 * k, sh[1] - 4 * k), (sh[0] + 32 * k, sh[1] + 2 * k)]), fill=(60, 40, 26))
    # tunic: a shaped block with a belt, clavi, folds and one shadow tone (light from the right)
    tun = bez(P(-34, -566), P(-80, -566), P(-104, -548), P(-112, -520), n=8) + [P(-128, -488), P(-100, -470), P(-98, -430)] + \
          [P(-112, -400), P(-126, -250)] + [P(122, -254), P(110, -400)] + [P(98, -430), P(100, -470), P(128, -490)] + \
          bez(P(110, -520), P(104, -548), P(80, -566), P(34, -566), n=8)
    d.polygon(sc(tun), fill=TUN)
    d.polygon(sc([P(-34, -566), P(-80, -566), P(-104, -548), P(-112, -520), P(-128, -488), P(-100, -470), P(-98, -430), P(-112, -400), P(-126, -250),
                  P(-64, -252), P(-52, -400), P(-40, -470)]), fill=TUN_SH)
    d.polygon(sc([P(84, -560), P(104, -548), P(110, -520), P(128, -490), P(112, -484), P(96, -520)]), fill=TUN_HI)
    d.polygon(sc([P(98, -430), P(110, -400), P(122, -254), P(104, -254), P(96, -400)]), fill=TUN_HI)
    for cx_ in (-42, 46):   # clavi stripes
        d.polygon(sc([P(cx_ - 8, -562), P(cx_ + 8, -562), P(cx_ * 0.92 + 8, -400), P(cx_ * 1.12 + 12, -252), P(cx_ * 1.12 - 12, -252), P(cx_ * 0.92 - 8, -400)]), fill=CLAV)
    for sx in (-1, 1):       # sleeve hem line
        d.line(sc([P(sx * 128, -488), P(sx * 100, -470)]), fill=INK, width=4 * S)
    for u, sx in ((-80, -1), (-10, 1), (60, 1), (96, -1)):   # folds from the belt
        d.line(sc(bez(P(u * 0.9, -400), P(u + sx * 8, -330), P(u * 1.05, -256))), fill=(118, 98, 66), width=3 * S)
    d.line(sc(bez(P(-30, -546), P(0, -520), P(30, -546))), fill=INK, width=4 * S)    # neckline
    d.polygon(sc(tun), outline=INK, width=6 * S)
    # hem: slightly ragged
    hem = [P(-122, -246)] + [P(-122 + i * 24, -246 + (6 if i % 2 else -2)) for i in range(1, 10)] + [P(118, -250)]
    d.line(sc(hem), fill=INK, width=6 * S)
    # belt with bronze buckle and a hanging strap
    d.polygon(sc([P(-114, -422), P(106, -426), P(108, -398), P(-112, -394)]), fill=(92, 58, 34), outline=INK, width=4 * S)
    d.rectangle(sc([P(-6, -428), P(26, -394)]), fill=(198, 150, 64), outline=INK, width=4 * S)
    d.rectangle(sc([P(2, -420), P(18, -402)]), fill=(92, 58, 34))
    d.line(sc([P(70, -398), P(64, -350)]), fill=INK, width=8 * S); d.line(sc([P(70, -398), P(64, -350)]), fill=(92, 58, 34), width=5 * S)
    # arms (behind the spear for the far hand), spear, hands
    shL, shR = P(-104, -480), P(104, -480)
    hB, hF = P(-30, -380), P(120, -456)
    limb(d, [shL, P(-110, -440), hB], 7 * k)
    limb(d, [shR, P(140, -500), hF], 7 * k)
    venabulum(d, P(-150, -300), P(330, -560))
    hand(d, *hB, r=17 * k, ang=-0.5); hand(d, *hF, r=17 * k, ang=-0.5)
    # ---------------- head (three quarter, turned right) ----------------
    hc = P(6, -720); R = 150 * k
    # hair back mass: irregular silhouette behind the head
    back = []
    for i in range(26):
        a = math.pi * (0.62 + 1.38 * i / 25)
        rr = R * (1.06 + 0.07 * math.sin(i * 2.7) + (0.06 if i % 3 == 0 else 0))
        back.append((hc[0] - R * 0.06 + math.cos(a) * rr, hc[1] - R * 0.08 + math.sin(a) * rr * 0.98))
    back += [(hc[0] + R * 0.7, hc[1] - R * 0.1), (hc[0] - R * 0.6, hc[1] + R * 0.4)]
    d.polygon(sc(back), fill=HAIR, outline=INK, width=6 * S)
    # ear (on the far left side, we see the left ear)
    ear = (hc[0] - R * 0.86, hc[1] + R * 0.05)
    d.ellipse(sc([(ear[0] - 26 * k, ear[1] - 36 * k), (ear[0] + 22 * k, ear[1] + 34 * k)]), fill=SKIN, outline=INK, width=5 * S)
    d.arc(sc([(ear[0] - 14 * k, ear[1] - 22 * k), (ear[0] + 10 * k, ear[1] + 20 * k)]), 60, 300, fill=SKIN_SH, width=4 * S)
    # face shape: jaw on the right comes forward (three quarter)
    face = bez((hc[0] - R * 0.84, hc[1] - R * 0.35), (hc[0] - R * 0.95, hc[1] + R * 0.9), (hc[0] - R * 0.1, hc[1] + R * 1.12), (hc[0] + R * 0.52, hc[1] + R * 0.78), n=30)
    face += bez((hc[0] + R * 0.52, hc[1] + R * 0.78), (hc[0] + R * 0.86, hc[1] + R * 0.55), (hc[0] + R * 0.92, hc[1] + R * 0.0), (hc[0] + R * 0.82, hc[1] - R * 0.42), n=20)
    face += bez((hc[0] + R * 0.82, hc[1] - R * 0.42), (hc[0] + R * 0.4, hc[1] - R * 0.9), (hc[0] - R * 0.5, hc[1] - R * 0.86), (hc[0] - R * 0.84, hc[1] - R * 0.35), n=20)
    d.polygon(sc(face), fill=SKIN)
    # shadow side of the face (left, away from the sun) and a warm rim on the right cheek
    sh_poly = bez((hc[0] - R * 0.84, hc[1] - R * 0.35), (hc[0] - R * 0.95, hc[1] + R * 0.9), (hc[0] - R * 0.1, hc[1] + R * 1.12), (hc[0] + R * 0.05, hc[1] + R * 1.05), n=24) + \
        bez((hc[0] + R * 0.05, hc[1] + R * 1.05), (hc[0] - R * 0.42, hc[1] + R * 0.6), (hc[0] - R * 0.5, hc[1] + R * 0.0), (hc[0] - R * 0.56, hc[1] - R * 0.5), n=20)
    d.polygon(sc(sh_poly), fill=SKIN_SH)
    d.line(sc(bez((hc[0] + R * 0.84, hc[1] - R * 0.3), (hc[0] + R * 0.94, hc[1] + R * 0.1), (hc[0] + R * 0.6, hc[1] + R * 0.74))), fill=SKIN_HI, width=6 * S)
    # stubble: fine dots on the jaw, clipped to the face
    stub = Image.new('RGBA', img.size, (0, 0, 0, 0)); sd_ = ImageDraw.Draw(stub)
    for _ in range(520):
        a = rnd.uniform(0.15, 2.4); r_ = rnd.uniform(0.62, 1.05)
        px, py = hc[0] - R * 0.15 + math.cos(a) * R * 0.8 * r_, hc[1] + R * 0.35 + math.sin(a) * R * 0.68 * r_
        sd_.ellipse(sc([(px, py), (px + 2.2, py + 2.2)]), fill=(96, 64, 46, 255))
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).polygon(sc(face), fill=255)
    stub.putalpha(ImageChops.multiply(stub.split()[3], m))
    img.alpha_composite(stub); d = ImageDraw.Draw(img)
    d.polygon(sc(face), outline=INK, width=6 * S)
    # hair front: swept locks of different lengths, parting on the left, forehead showing
    hl = [(-0.92, -0.18), (-0.86, -0.62), (-0.55, -0.98), (-0.12, -1.08), (0.3, -1.02), (0.66, -0.84), (0.9, -0.5), (0.92, -0.26),
          (0.74, -0.42), (0.78, -0.3), (0.56, -0.46), (0.5, -0.36), (0.3, -0.5), (0.2, -0.4), (0.02, -0.54), (-0.14, -0.44),
          (-0.3, -0.58), (-0.5, -0.5), (-0.62, -0.32), (-0.78, -0.12)]
    front = [(hc[0] + R * u, hc[1] + R * v) for u, v in hl]
    d.polygon(sc(front), fill=HAIR, outline=INK, width=6 * S)
    # sideburn down to the ear
    d.polygon(sc([(hc[0] - R * 0.84, hc[1] - R * 0.2), (hc[0] - R * 0.7, hc[1] - R * 0.12), (hc[0] - R * 0.72, hc[1] + R * 0.28),
                  (hc[0] - R * 0.8, hc[1] + R * 0.3)]), fill=HAIR, outline=INK, width=4 * S)
    for (u0, v0), (u1, v1) in (((-0.5, -0.9), (-0.38, -0.6)), ((-0.2, -0.98), (-0.08, -0.6)), ((0.14, -0.96), (0.24, -0.6)),
                               ((0.46, -0.86), (0.54, -0.56)), ((-0.74, -0.6), (-0.62, -0.36))):
        a = (hc[0] + R * u0, hc[1] + R * v0); b = (hc[0] + R * u1, hc[1] + R * v1)
        d.line(sc(bez(a, ((a[0] + b[0]) / 2 + 10, (a[1] + b[1]) / 2), b)), fill=(28, 18, 12), width=3 * S)
    d.line(sc(bez((hc[0] - R * 0.2, hc[1] - R * 0.98), (hc[0] + R * 0.2, hc[1] - R * 1.0), (hc[0] + R * 0.5, hc[1] - R * 0.8))), fill=HAIR_HI, width=7 * S)
    # brows: heavy, angled down toward the nose (determined), set on a brow ridge line
    ex1, ex2, ey = hc[0] - R * 0.18, hc[0] + R * 0.38, hc[1] - R * 0.05
    d.line(sc(bez((ex1 - 52, ey - 52), (ex1 - 10, ey - 66), (ex1 + 36, ey - 40))), fill=INK, width=13 * S)
    d.line(sc(bez((ex2 - 34, ey - 42), (ex2 + 6, ey - 64), (ex2 + 44, ey - 54))), fill=INK, width=13 * S)
    # eyes: white ovals, small pupils looking right, heavy upper lids
    for ex, rx in ((ex1, 46), (ex2, 40)):
        d.ellipse(sc([(ex - rx, ey - 30), (ex + rx, ey + 30)]), fill=(250, 248, 240), outline=INK, width=5 * S)
        d.ellipse(sc([(ex + rx * 0.35 * look - 10, ey - 8), (ex + rx * 0.35 * look + 10, ey + 12)]), fill=INK)
        d.chord(sc([(ex - rx, ey - 30), (ex + rx, ey + 30)]), 200, 340, fill=SKIN_SH if ex == ex1 else SKIN, outline=INK, width=5 * S)
    # nose (three quarter, slight hook): bridge line from between the eyes, rounded tip, nostril wing, shadow on the far side
    nb = (hc[0] + R * 0.12, hc[1] + R * 0.0)
    bridge = bez(nb, (nb[0] + 16, nb[1] + 18), (nb[0] + 34, nb[1] + 46), (nb[0] + 30, nb[1] + 70), n=14)
    tip = bez((nb[0] + 30, nb[1] + 70), (nb[0] + 26, nb[1] + 84), (nb[0] + 8, nb[1] + 86), n=8)
    d.polygon(sc([(nb[0] - 2, nb[1] + 14)] + bridge + tip + [(nb[0] - 6, nb[1] + 80)]), fill=SKIN_SH)
    d.line(sc(bridge + tip), fill=INK, width=5 * S)
    d.arc(sc([(nb[0] - 14, nb[1] + 70), (nb[0] + 8, nb[1] + 90)]), 100, 290, fill=INK, width=4 * S)   # nostril wing
    # cheekbone and nose to mouth folds, forehead lines, scar
    d.line(sc(bez((hc[0] + R * 0.52, hc[1] + R * 0.2), (hc[0] + R * 0.62, hc[1] + R * 0.5), (hc[0] + R * 0.5, hc[1] + R * 0.68))), fill=(120, 78, 56), width=4 * S)
    d.line(sc(bez((hc[0] - R * 0.1, hc[1] + R * 0.38), (hc[0] - R * 0.18, hc[1] + R * 0.56), (hc[0] - R * 0.08, hc[1] + R * 0.7))), fill=(120, 78, 56), width=4 * S)
    for i in range(2):
        yy_ = hc[1] - R * (0.5 + i * 0.11)
        d.line(sc(bez((hc[0] - R * 0.3, yy_), (hc[0] + R * 0.05, yy_ - 10), (hc[0] + R * 0.45, yy_))), fill=(150, 98, 70), width=3 * S)
    sc0 = (hc[0] + R * 0.5, hc[1] - R * 0.28)
    d.line(sc([sc0, (sc0[0] + 26, sc0[1] + 70)]), fill=(150, 66, 56), width=5 * S)
    for i in range(3):
        m = (sc0[0] + 6 + i * 7, sc0[1] + 16 + i * 18)
        d.line(sc([(m[0] - 8, m[1] + 2), (m[0] + 8, m[1] - 2)]), fill=(150, 66, 56), width=2 * S)
    # mouth: short tight line set off centre toward the turned side, lower lip shadow
    mc = (hc[0] + R * 0.24, hc[1] + R * 0.66)
    d.line(sc(bez((mc[0] - 44, mc[1] + 4), (mc[0], mc[1] - 6), (mc[0] + 36, mc[1] + 6))), fill=INK, width=6 * S)
    d.line(sc(bez((mc[0] - 22, mc[1] + 22), (mc[0], mc[1] + 28), (mc[0] + 20, mc[1] + 22))), fill=(120, 78, 56), width=4 * S)
    # sweat bead
    sw = (hc[0] - R * 0.48, hc[1] - R * 0.34)
    d.polygon(sc([(sw[0], sw[1] - 16), (sw[0] + 10, sw[1] + 4), (sw[0], sw[1] + 12), (sw[0] - 10, sw[1] + 4)]), fill=(200, 230, 250), outline=INK, width=3 * S)

def main(out='style_frame.png'):
    bg = background()
    canvas = bg.resize((WW, HH), Image.BICUBIC)
    # character layer at 2x with its own soft cast shadow toward the camera left (sun is behind on the right)
    lay = Image.new('RGBA', (WW, HH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    trapdoor(d, 800, 1420, 1540, 300, 360, 1.0)
    fig = Image.new('RGBA', (WW, HH), (0, 0, 0, 0)); fd = ImageDraw.Draw(fig)
    venator(fd, fig, 330, 1560, k=1.28, look=1)
    # cast shadow: the figure's silhouette squashed onto the sand, toward the lower left
    a = fig.split()[3]
    g = 1556 * S; shx, shy = -0.28, 0.36          # sun behind on the right: shadow falls toward the lower left, foreshortened
    shadow = Image.new('RGBA', (WW, HH), (40, 22, 12, 0)); shadow.putalpha(a.point(lambda v: int(v * 0.4)).filter(ImageFilter.MaxFilter(9)))
    # output (X, Y) with Y >= g samples the figure at (X + shx * (Y - g) / shy, g - (Y - g) / shy)
    shadow = shadow.transform((WW, HH), Image.AFFINE, (1, -shx / shy, shx / shy * g, 0, -1 / shy, g + g / shy), Image.BILINEAR)
    shadow = shadow.filter(ImageFilter.GaussianBlur(8 * S))
    canvas.alpha_composite(shadow)
    cd_ = Image.new('RGBA', (WW, HH), (0, 0, 0, 0)); ImageDraw.Draw(cd_).ellipse([(330 - 120) * S, (1556 - 14) * S, (330 + 120) * S, (1556 + 18) * S], fill=(40, 22, 12, 110))
    canvas.alpha_composite(cd_.filter(ImageFilter.GaussianBlur(6 * S)))
    canvas.alpha_composite(lay)
    # scene light on the figure: warm multiply on the whole figure, darker toward the feet (bounce from sand)
    tint = Image.new('RGBA', (WW, HH), (255, 232, 200, 255))
    figt = ImageChops.multiply(fig, tint); figt.putalpha(fig.split()[3])
    canvas.alpha_composite(figt)
    out_im = canvas.resize((W, H), Image.LANCZOS).convert('RGB')
    # grade: warm highlights, cool shadows, vignette, fine grain
    arr = np.asarray(out_im, np.float32)
    lum = arr.mean(axis=2, keepdims=True) / 255
    arr = arr + (lum > 0.6) * np.array([8, 4, -6]) + (lum < 0.3) * np.array([-6, -2, 8])
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.55) / (H * 0.62)) ** 2)
    arr = arr * np.clip(v, 0.55, 1)[..., None]
    arr += np.random.default_rng(2).normal(0, 3.0, arr.shape)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(out)

if __name__ == '__main__':
    main()

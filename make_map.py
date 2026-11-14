"""Prerender map levels from real coastline data (global-land-mask, ~1 km)."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from global_land_mask import globe
from scipy import ndimage

W, H = 1080, 1920
# (name, center lon, center lat, lat span, render scale)
LEVELS = [('ov', 32.6, 37.0, 17.5, 2)]
SEA = np.array((58, 74, 82)); SEA2 = np.array((40, 54, 62))
LAND = np.array((222, 208, 176)); LAND2 = np.array((196, 180, 146))
INK = (60, 48, 34)

def geo(c_lon, c_lat, span):
    lat_px = span / H
    lon_px = lat_px / math.cos(math.radians(c_lat))
    return lon_px, lat_px

def render(name, c_lon, c_lat, span, sc):
    w, h = W * sc, H * sc
    lon_px, lat_px = geo(c_lon, c_lat, span)
    # sample mask on a grid no finer than ~0.5 km then smooth
    step = max(1, int(round((0.006 / lat_px) / sc)))
    gw, gh = w // step + 2, h // step + 2
    lons = c_lon + (np.arange(gw) * step - w / 2) * lon_px / sc
    lats = c_lat - (np.arange(gh) * step - h / 2) * lat_px / sc
    LON, LAT = np.meshgrid(lons, lats)
    m = globe.is_land(LAT, LON).astype(np.float32)
    sig = max(0.6, 1.2 * (0.012 / (lat_px / sc * step)))
    m = ndimage.gaussian_filter(m, min(sig, 3))
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    land = m > 0.5
    # distance from coast in sea for ripple lines
    dist = ndimage.distance_transform_edt(~land) / sc
    dl = ndimage.distance_transform_edt(land) / sc
    yy, xx = np.mgrid[0:h, 0:w]
    g = np.exp(-(((xx / w - .5) ** 2) + ((yy / h - .45) * 1.2) ** 2) / 0.35)[..., None]
    sea = SEA2 + (SEA - SEA2) * g
    ripple = np.zeros_like(dist)
    for k, d0 in enumerate((10, 24, 42, 66)):
        ripple += np.clip(1 - np.abs(dist - d0) / 1.6, 0, 1) * (0.55 - k * 0.1)
    sea = sea + ripple[..., None] * 38
    shade = np.clip(dl / 60, 0, 1)[..., None]
    rng = np.random.default_rng(3)
    grain = ndimage.gaussian_filter(rng.standard_normal((h // 4, w // 4)), 2)
    grain = np.asarray(Image.fromarray(((grain - grain.min()) / np.ptp(grain) * 255).astype(np.uint8)).resize((w, h))) / 255.0
    landc = LAND2 + (LAND - LAND2) * (0.35 + 0.65 * shade) + (grain[..., None] - .5) * 18
    img = np.where(land[..., None], landc, sea)
    # coastline ink
    edge = np.clip(1 - np.abs(dl - dist) / 1.4, 0, 1) * (dist < 3)
    edge = np.maximum(edge, ((dl > 0) & (dl < 2.2)).astype(float))
    img = img * (1 - edge[..., None] * 0.85) + np.array(INK) * edge[..., None] * 0.85
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, 'RGBA')
    # graticule
    stepdeg = 2 if span > 6 else (0.5 if span > 2 else 0.25)
    def px(lon, lat): return ((lon - c_lon) / lon_px * sc + w / 2, (c_lat - lat) / lat_px * sc + h / 2)
    lon0 = math.floor((c_lon - span) / stepdeg) * stepdeg
    lat0 = math.floor((c_lat - span) / stepdeg) * stepdeg
    for i in range(int(2 * span / stepdeg) + 3):
        x, _ = px(lon0 + i * stepdeg, c_lat); d.line([(x, 0), (x, h)], fill=(30, 30, 30, 34), width=sc)
        _, y = px(c_lon, lat0 + i * stepdeg); d.line([(0, y), (w, y)], fill=(30, 30, 30, 34), width=sc)
    # vignette
    vig = np.clip(np.sqrt((xx / w - .5) ** 2 + ((yy / h - .5) * 1.4) ** 2) / .8, 0, 1) ** 2
    arr = np.asarray(im).astype(np.float32) * (1 - 0.35 * vig[..., None])
    Image.fromarray(arr.astype(np.uint8)).save(f'map_{name}.png')
    print(name, 'done', step, round(sig, 2))

if __name__ == '__main__':
    for L in LEVELS: render(*L)

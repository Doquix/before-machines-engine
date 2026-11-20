"""E020 Colosseum lifts: frame renderer. Modes: still t1 t2 ... | seg a b | cues | T"""
from scenes_cl import *
HUD = {}
TINT = [None]
SLIDE = 0.35
DISS = 0.3

def scene_idx(t):
    return max(i for i, s in enumerate(SCENES) if s[0] <= t)

def render_scene(i, t):
    _, fn, cam, _ = SCENES[i]
    CAM.extra = cam; CAM.set(t)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    lay = new_layer(); pn = Pen(lay)
    TINT[0] = None
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

# ---------------- SFX cue sheet ----------------
def cues():
    C = [(0.0, 'thud', 0.9), (0.02, 'creak', 0.6), (0.05, 'whooshlow', 0.4),
         (T['burst'] - 0.45, 'rumble', 0.4), (T['burst'] - 0.1, 'whoosh', 0.6), (T['burst'], 'roar', 1.0), (T['burst'] + 0.05, 'thud', 0.7),
         (T['burst'] + 0.55, 'thud', 0.5), (T['burst'] + 0.6, 'swish', 0.6), (T['burst'] + 0.87, 'hit', 1.0), (T['burst'] + 0.88, 'roar', 0.8),
         (T['s1'] - 0.05, 'puff', 0.9), (T['s1'] + 0.3, 'chime', 0.3),
         (T['real'], 'stamp', 1.0),
         (T['s2'] + 0.3, 'creak', 0.5), (T['s2'] + 0.8, 'rumble', 0.3), (T['machine'], 'pop', 0.5),
         (T['elevator3'] - 0.05, 'bell', 0.6), (T['elevator3'] + 0.2, 'creak', 0.6),
         (T['s4'], 'hiss', 0.3), (T['hypogeum'] - 0.1, 'pop', 0.5),
         (T['maze'] - 0.1, 'paper', 0.5), (T['tunnels'], 'slide', 0.4), (T['cells'] - 0.1, 'tick', 0.4),
         (T['lion6'], 'roar', 0.35), (T['cage6'], 'knock', 0.5),
         (T['nothing'] + 0.1, 'pop', 0.5), (T['bigger'] - 0.2, 'slide', 0.6), (T['bigger'] + 0.25, 'thud', 0.8), (T['fit'], 'pop', 0.6),
         (T['beside'] - 0.05, 'knock', 0.6), (T['stood'], 'knock', 0.6), (T['capstan8'] - 0.1, 'clack', 0.6), (T['capstan8'], 'pop', 0.5),
         (T['upright'] - 0.3, 'cloth', 0.4), (T['two9'] - 0.1, 'riser', 0.4),
         (T['eight'] - 0.15, 'footsteps', 0.6), (T['pushed'], 'creak', 0.7), (T['bars'], 'creak', 0.6), (T['circle'], 'creak', 0.6),
         (T['ropes'] - 0.1, 'stretch', 0.6), (T['wound'], 'ratchetrun', 0.6), (T['climbed'] - 0.1, 'ratchetrun', 0.7),
         (T['climbed'] + 0.6, 'creak', 0.6), (T['twenty'], 'pop', 0.5),
         (T['swung'] - 0.05, 'creak', 0.7), (T['swung'] + 0.3, 'thud', 0.9), (T['swung'] + 0.32, 'rubble', 0.4), (T['ramp'] + 0.1, 'clack', 0.6),
         (T['ramp'] + 0.2, 'pop', 0.4),
         (T['ran'] - 0.1, 'whoosh', 0.6), (T['ran'] + 0.4, 'footsteps', 0.6), (T['straight'], 'roar', 0.9), (T['light15'], 'shimmer', 0.6),
         (T['fifty'] - 0.05, 'rumble', 0.6), (T['thousand'], 'roarlong', 0.25), (T['people'] + 0.2, 'pop', 0.4),
         (T['dozens'] - 0.1, 'tick', 0.5), (T['hidden'], 'scrape', 0.4), (T['lifts'], 'pop', 0.5),
         (T['never'], 'creak', 0.4), (T['next18'], 'creak', 0.7), (T['rise'] - 0.2, 'roar', 0.4),
         (T['opens'] - 0.1, 'thud', 0.9), (T['opens'] - 0.08, 'creak', 0.6), (T['watching'] - 0.2, 'ratchetrun', 0.6), (T['roman'], 'pop', 0.5)]
    for i in range(14):    # brawl: hits, clatter and growls while the cloud churns
        tb = T['burst'] + 0.95 + i * 0.13
        if tb < T['s1'] - 0.1: C.append((tb, ('hit', 'clank', 'thud', 'swish', 'clatter', 'roar')[i % 6], 0.55 if i % 6 != 5 else 0.4))
    for i in range(28): C.append((T['dozens'] - 0.1 + i * 0.035, 'tick', 0.25))
    for i in range(4): C += [(T['four'] + i * 0.12, 'pop', 0.4), (T['level'] - 0.1 + i * 0.12, 'pop', 0.4)]
    for b in np.arange(T['pushed'], T['s14'] - 0.3, 0.8): C.append((b, 'creak', 0.35))
    starts = {round(st, 3) for st, _, _, org in SCENES[1:]}
    C = [((c[0] - 0.12) if (round(c[0], 3) in starts and c[1] != 'whoosh') else c[0], c[1], c[2]) for c in C]
    for st, _, _, org in SCENES[1:]:
        if org == 'slide': C.append((st, 'whoosh', 0.35))
    C = sorted(set(C))
    json.dump(dict(cues=C, T=T, dur=DUR, nf=NF), open('cues.json', 'w'), indent=1)
    print(len(C), 'cues', 'dur', DUR, 'frames', NF)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'still':
        for a in sys.argv[2:]:
            t = float(a); frame(t).save(f'still_{t:06.2f}.png')
    elif mode == 'seg':
        a, b = int(sys.argv[2]), int(sys.argv[3])
        out = sys.stdout.buffer
        for n in range(a, b):
            out.write(frame(n / FPS).tobytes())
    elif mode == 'cues':
        cues()
    elif mode == 'T':
        for k, v in sorted(T.items(), key=lambda x: x[1]): print(f'{v:6.2f} {k}')

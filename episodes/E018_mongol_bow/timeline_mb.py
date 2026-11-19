"""E018 Mongol bow: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.04, "Over five hundred metres.", "hundred"),
 (2.29, "That is how far one Mongol archer shot an arrow,", "Mongol"),
 (5.66, "around 1225,", "1225"),
 (7.27, "and the shot was carved into a granite stone.", "granite"),
 (10.30, "That stone still sits in a museum in Saint Petersburg.", "museum"),
 (13.62, "The archer was Yisüngge,", "Yisüngge"),
 (15.40, "a nephew of Genghis Khan.", "nephew"),
 (17.58, "Mongol bows were short enough to shoot from a galloping horse.", "galloping"),
 (21.32, "Unstrung, it curves the wrong way,", "wrong"),
 (23.56, "away from the archer.", "away"),
 (25.00, "Stringing it bends it back against itself,", "back"),
 (27.64, "so it is loaded before you even draw.", "loaded"),
 (30.16, "Then three layers do the work.", "three"),
 (32.41, "Horn on the inside, squeezed.", "Horn"),
 (34.73, "Sinew on the outside, stretched.", "Sinew"),
 (37.24, "A thin core of wood or bamboo holds them together.", "core"),
 (40.58, "Horn and sinew store more energy than wood alone,", "energy"),
 (43.72, "so a short bow pulls like a long one.", "long"),
 (46.31, "Glued and dried for months,", "months"),
 (48.31, "a bow small enough for the saddle could throw an arrow over five hundred metres.", "hundred"),
]
SIL = [(1.92, 2.29), (5.40, 5.66), (7.03, 7.27), (9.96, 10.30), (13.21, 13.62), (15.18, 15.40), (16.98, 17.58), (21.03, 21.32),
       (23.37, 23.56), (24.70, 25.00), (27.47, 27.64), (29.76, 30.16), (32.09, 32.41), (33.61, 33.82), (34.45, 34.73),
       (36.07, 36.29), (36.92, 37.24), (40.23, 40.58), (43.54, 43.72), (46.01, 46.31), (48.13, 48.31)]
TARGET = {}
OVR = {(7, 'a'): 19.72, (7, 'galloping'): 19.80, (7, 'horse.'): 20.43, (4, 'a'): 11.55, (4, 'museum'): 11.66,
       (4, 'Saint'): 12.29, (4, 'Petersburg.'): 12.55, (5, 'was'): 14.21, (5, 'Yisüngge,'): 14.44, (15, 'A'): 37.24, (15, 'thin'): 37.36,
       (17, 'a'): 45.32, (17, 'long'): 45.40}
DRAMA = {9.96: 0.45, 16.98: 0.45, 21.03: 0.45, 29.76: 0.45, 48.13: 0.40}

first = np.argmax(db > -45) * 0.01
end_sound = len(db) * 0.01 - np.argmax(db[::-1] > -45) * 0.01
keep = []; cur = max(0.0, first - 0.04)
for s, e in SIL:
    target = DRAMA.get(s, TARGET.get(s, 0.20)); dur = e - s
    if dur > target:
        cut0 = s + 0.06; cut1 = cut0 + (dur - target)
        keep.append((cur, cut0)); cur = cut1
    elif s in DRAMA and dur < target:
        mid = s + dur / 2
        keep.append((cur, mid)); keep.append(('pad', target - dur)); cur = mid
keep.append((cur, min(end_sound + 0.15, len(x) / SR)))

fade = int(0.012 * SR)
out = []; tmap = []; tnew = 0.0
for a, b in keep:
    if a == 'pad':
        out.append(np.zeros(int(b * SR))); tnew += int(b * SR) / SR; continue
    seg = x[int(a * SR):int(b * SR)].copy()
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    out.append(seg); tmap.append((a, b, tnew)); tnew += len(seg) / SR
y = np.concatenate(out)
lead = 0.12
y = np.concatenate([np.zeros(int(lead * SR)), y])
sf.write('vo_tight.wav', y, SR, subtype='PCM_24')

def M(t):
    for a, b, n in tmap:
        if t < a: return n + lead
        if t <= b: return n + (t - a) + lead
    a, b, n = tmap[-1]; return n + (b - a) + lead

ASR = []
for ln in open('asr.txt'):
    t, w = ln.split(None, 1); ASR.append((float(t), re.sub(r'\(\d\)', '', w.strip())))

def norm(w): return re.sub(r'[^a-z0-9]', '', w.lower())

def phrase_end(i):
    nxt = PHR[i + 1][0] if i + 1 < len(PHR) else end_sound + 0.3
    ends = [s for s, e in SIL if PHR[i][0] < s < nxt]
    return ends[-1] if ends else (nxt - 0.05 if i + 1 < len(PHR) else end_sound)

caps = []; words = []
for i, (s0, txt, kw) in enumerate(PHR):
    e = phrase_end(i)
    ws = txt.split()
    aw = [(t, w) for t, w in ASR if s0 - 0.05 <= t < e]
    on = [None] * len(ws); on[0] = s0
    sm = difflib.SequenceMatcher(None, [norm(w) for w in ws], [norm(w) for _, w in aw])
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): on[a + k] = aw[b + k][0] if a + k else s0
    # interpolate unmatched by syllable-ish length
    idx = [j for j, v in enumerate(on) if v is not None]
    for j in range(len(ws)):
        if on[j] is None:
            lo = max(k for k in idx if k < j); his = [k for k in idx if k > j]
            hi = his[0] if his else None
            t1 = on[hi] if hi is not None else e
            n_ = (hi if hi is not None else len(ws)) - lo
            on[j] = on[lo] + (t1 - on[lo]) * (j - lo) / n_
    for j, w in enumerate(ws):
        if (i, w) in OVR: on[j] = OVR[(i, w)]
    for j, w in enumerate(ws):
        words.append({'w': w, 't': round(M(on[j]), 3), 'p': i, 'kw': re.sub(r'[^\w]', '', w) == kw})
    caps.append({'s': round(M(s0), 3), 'e': round(M(e), 3), 't': txt, 'k': kw})

_fa = [w for w in words if w['p'] == 17 and w['w'] == 'a']
if _fa:
    _so = [w for w in words if w['p'] == 17 and w['w'] == 'so'][0]['t']; _sh = [w for w in words if w['p'] == 17 and w['w'] == 'short'][0]['t']
    _fa[0]['t'] = round((_so + _sh) / 2, 3)
json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2))
for c in caps:
    print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")
    print('        ', ' '.join(f"{w['w']}@{w['t']:.2f}" for w in words if w['p'] == caps.index(c)))

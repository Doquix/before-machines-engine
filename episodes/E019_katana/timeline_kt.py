"""E019 katana: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.05, "The curve of a samurai sword was mostly made in a tub of water.", "water"),
 (4.26, "Before that moment, the blade is only slightly curved.", "slightly"),
 (7.70, "The smith paints it with clay,", "clay"),
 (9.51, "thick along the spine,", "thick"),
 (10.88, "thin along the edge.", "thin"),
 (12.50, "Then he heats it to around 1,500 degrees Fahrenheit", "1,500"),
 (16.40, "and plunges it into water.", "plunges"),
 (18.50, "The bare edge cools in an instant", "instant"),
 (20.66, "and turns into martensite,", "martensite,"),
 (22.36, "steel nearly as hard as glass.", "glass."),
 (24.96, "As it changes, it swells.", "swells."),
 (27.22, "The spine, wrapped in clay,", "spine,"),
 (29.07, "cools slowly and stays softer.", "softer."),
 (31.50, "In the first seconds the blade dips the wrong way.", "wrong"),
 (34.42, "Then the swelling edge wins", "wins"),
 (36.20, "and pushes the whole blade into an arc,", "arc,"),
 (38.70, "edge on the outside.", "outside."),
 (40.27, "After polishing,", "polishing,"),
 (41.34, "the line where hard meets soft", "hard"),
 (43.15, "shows as a pale wave,", "wave,"),
 (44.99, "the hamon.", "hamon."),
 (46.01, "One quench gave the sword a hard edge,", "quench"),
 (48.35, "a tough spine and its shape.", "shape."),
 (50.76, "All of it came out of a tub of water.", "water."),
]
SIL = [(3.87, 4.26), (5.22, 5.38), (7.32, 7.70), (9.30, 9.51), (10.69, 10.88), (12.16, 12.50), (18.10, 18.50), (22.13, 22.36),
       (24.59, 24.96), (25.84, 25.99), (26.83, 27.22), (28.90, 29.07), (31.10, 31.50), (34.10, 34.42), (38.47, 38.70),
       (39.87, 40.27), (41.21, 41.34), (44.71, 44.99), (45.60, 46.01), (48.22, 48.35), (49.32, 49.48), (50.34, 50.76), (51.21, 51.34)]
TARGET = {}
OVR = {(0, 'tub'): 2.97, (0, 'of'): 3.24, (5, '1,500'): 13.98, (13, 'blade'): 32.66, (13, 'dips'): 33.05, (10, 'swells.'): 26.24,
       (22, 'tough'): 48.46, (22, 'spine'): 48.74, (8, 'martensite,'): 21.36, (23, 'tub'): 52.04}
DRAMA = {12.16: 0.45, 18.10: 0.45, 31.10: 0.45, 39.87: 0.45, 50.34: 0.40}

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

_last = [w for w in words if w['p'] == 23]
for w_, to in zip(_last, (50.74, 50.96, 51.04, 51.36, 51.60, 51.75, 51.81, 52.00, 52.30, 52.46)):
    w_['t'] = round(M(to), 3)
caps[23]['e'] = round(M(52.95), 3)
json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2))
for c in caps:
    print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")
    print('        ', ' '.join(f"{w['w']}@{w['t']:.2f}" for w in words if w['p'] == caps.index(c)))

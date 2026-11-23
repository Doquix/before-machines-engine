"""E022 yakhchal: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.05, "This ice was frozen by the night sky.", "night"),
 (3.19, "In the deserts of Persia,", "Persia"),
 (4.65, "winter nights hover around freezing.", "freezing"),
 (7.24, "So builders dug long, shallow pools,", "pools"),
 (10.25, "fed by underground canals,", "canals"),
 (11.96, "and raised a tall mud brick wall", "wall"),
 (14.11, "along the south side.", "south"),
 (15.61, "By day, the wall threw shade over the water.", "shade"),
 (18.68, "By night, the water lost its heat", "heat"),
 (20.72, "straight up into the clear, dry sky,", "sky"),
 (23.50, "and a thin skin of ice formed,", "ice"),
 (25.53, "even when the air was likely a little above freezing.", "likely"),
 (28.60, "Each night workers poured on", "poured"),
 (30.37, "a few more inches of water.", "inches"),
 (32.22, "Layer by layer,", "Layer"),
 (33.31, "the ice grew to about twenty inches thick.", "twenty"),
 (36.05, "Then they cut it into blocks", "blocks"),
 (37.68, "and carried it into a domed pit,", "pit"),
 (39.72, "packed with straw.", "straw"),
 (41.11, "Some of these domes stand almost sixty feet tall.", "sixty"),
 (44.44, "In midsummer, whole towns drank iced sherbet,", "sherbet"),
 (47.77, "all thanks to the night sky.", "sky"),
]
SIL = [(2.59, 3.21), (4.57, 4.78), (6.85, 7.28), (7.65, 7.81), (11.79, 11.99), (15.24, 15.65), (18.34, 18.72), (19.26, 19.46),
       (23.34, 23.52), (25.36, 25.56), (28.14, 28.64), (29.22, 29.35), (31.89, 32.24), (35.73, 36.10), (39.60, 39.80), (40.76, 41.13),
       (44.04, 44.47), (45.21, 45.35), (47.55, 47.81)]
TARGET = {}
OVR = {(4, 'fed'): 10.25, (12, 'poured'): 29.66, (16, 'Then'): 36.05, (17, 'carried'): 37.85, (17, 'domed'): 38.60, (17, 'pit,'): 39.36,
       (20, 'drank'): 46.29, (20, 'sherbet,'): 46.99, (21, 'night'): 48.63, (21, 'sky.'): 49.02, (9, 'dry'): 22.41, (9, 'clear,'): 21.79,
       (5, 'tall'): 12.67, (19, 'domes'): 41.64, (8, 'heat'): 20.44, (18, 'straw.'): 40.24, (17, 'a'): 38.36, (17, 'into'): 38.20, (12, 'on'): 30.05, (3, 'dug'): 8.20, (3, 'long,'): 8.47}
DRAMA = {15.24: 0.45, 25.36: 0.40, 28.14: 0.45, 44.04: 0.45}

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
    ends = [s for s, e in SIL if PHR[i][0] < s < nxt and e > nxt - 0.6]
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

json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2))
for c in caps:
    print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")
    print('        ', ' '.join(f"{w['w']}@{w['t']:.2f}" for w in words if w['p'] == caps.index(c)))

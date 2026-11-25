"""E023 Alesia: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.07, "Twenty two miles of wall,", "miles"),
 (2.22, "built to trap one hill.", "hill"),
 (4.50, "In 52 BC, Julius Caesar cornered a Gallic army", "Caesar"),
 (8.37, "on a hilltop town in eastern France.", "hilltop"),
 (10.90, "He judged it too strong to storm.", "strong"),
 (13.33, "So he ringed the hill instead:", "ringed"),
 (15.70, "a deep ditch,", "ditch"),
 (16.76, "a rampart about twelve feet high,", "twelve"),
 (18.84, "and a wooden tower about every eighty feet.", "tower"),
 (21.50, "Then Gallic riders slipped out at night to call for help.", "riders"),
 (24.98, "Caesar's answer was a second wall, facing outward,", "second"),
 (28.17, "about thirteen miles around.", "thirteen"),
 (30.30, "His legions now sat between two rings.", "rings"),
 (33.17, "In front of both, they buried traps:", "traps"),
 (35.47, "rows of sharpened branches,", "branches"),
 (37.24, "hidden pits with stakes,", "pits"),
 (38.82, "and iron hooks set in wood.", "hooks"),
 (40.90, "When the relief army came,", "relief"),
 (42.25, "it hit the outer wall", "outer"),
 (43.49, "while the town hit the inner one,", "inner"),
 (45.21, "at the same time.", "same"),
 (46.63, "The lines bent, but held.", "held"),
 (48.68, "Their leader, Vercingetorix, surrendered.", "surrendered"),
 (51.29, "All of it came down to twenty two miles of wall.", "miles"),
]
SIL = [(1.85, 2.24), (3.85, 4.53), (5.87, 6.05), (10.58, 10.95), (11.53, 11.66), (13.04, 13.36), (13.70, 13.82), (15.35, 15.69), (16.56, 16.76),
       (18.62, 18.85), (21.18, 21.55), (24.58, 25.00), (26.93, 27.13), (28.02, 28.20), (29.94, 30.32), (32.85, 33.20), (34.03, 34.19),
       (35.26, 35.48), (37.10, 37.28), (38.67, 38.85), (40.50, 40.94), (42.16, 42.30), (45.05, 45.24), (46.22, 46.65), (47.53, 47.76),
       (48.30, 48.71), (50.94, 51.33), (52.43, 52.56)]
TARGET = {}
OVR = {(2, '52'): 4.63, (2, 'BC,'): 5.28, (2, 'cornered'): 6.91, (2, 'a'): 7.43, (3, 'France.'): 10.00, (1, 'hill.'): 3.46,
       (5, 'ringed'): 13.92, (6, 'deep'): 15.76, (6, 'ditch,'): 16.11, (7, 'rampart'): 17.17, (9, 'riders'): 22.38,
       (10, 'wall,'): 26.62, (12, 'sat'): 31.19, (15, 'pits'): 37.56, (15, 'stakes,'): 38.10, (16, 'hooks'): 39.32,
       (16, 'set'): 39.80, (16, 'wood.'): 40.16, (21, 'lines'): 46.70, (21, 'bent,'): 47.07, (22, 'Vercingetorix,'): 49.33,
       (13, 'they'): 34.15, (13, 'buried'): 34.27, (14, 'sharpened'): 35.96}
DRAMA = {3.85: 0.45, 21.18: 0.45, 32.85: 0.45, 40.50: 0.45, 46.22: 0.40}

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

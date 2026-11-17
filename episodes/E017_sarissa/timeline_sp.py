"""E017 sarissa: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.04, "Two walls of shields slam together,", "together"),
 (2.60, "and only the first two ranks can reach the enemy.", "two"),
 (5.49, "Philip the Second of Macedon and the kings after him fixed that with length.", "length"),
 (10.08, "His soldiers carried the sarissa,", "sarissa"),
 (12.08, "a pike around 18 feet long,", "18"),
 (14.31, "gripped in both hands.", "both"),
 (15.99, "The Greek spears facing them were closer to eight feet.", "eight"),
 (19.08, "Packed about three feet apart,", "three"),
 (20.80, "the first five ranks all had points sticking out past the front man.", "five"),
 (24.96, "An enemy who dodged one point met the next,", "next"),
 (27.78, "then the next.", "next"),
 (29.19, "The ranks behind tilted their pikes up like a roof to knock down arrows.", "roof"),
 (33.74, "A spike on the back end balanced the weight and could be planted in the ground.", "spike"),
 (37.84, "Both hands were busy,", "busy"),
 (39.16, "so each man hung a small shield, about two feet wide, from his neck.", "neck"),
 (43.52, "From the front,", "front"),
 (44.42, "enemy spears rarely got close enough to touch a shield.", "touch"),
]
SIL = [(2.43, 2.60), (5.07, 5.49), (9.71, 10.08), (11.85, 12.06), (14.14, 14.31), (15.63, 15.99), (18.69, 19.08), (20.66, 20.80),
       (24.57, 24.96), (27.53, 27.78), (28.81, 29.19), (33.40, 33.74), (37.49, 37.84), (39.01, 39.16), (43.19, 43.52), (44.24, 44.42)]
TARGET = {}
OVR = {(4, '18'): 12.99}
DRAMA = {5.07: 0.45, 18.69: 0.45, 28.81: 0.40, 43.19: 0.45}

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

json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2))
for c in caps:
    print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")
    print('        ', ' '.join(f"{w['w']}@{w['t']:.2f}" for w in words if w['p'] == caps.index(c)))

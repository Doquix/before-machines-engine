"""E020 Colosseum lifts: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.04, "In Gladiator, tigers burst up through trap doors in the arena floor.", "tigers"),
 (4.62, "That part was real.", "real"),
 (6.22, "Under the Colosseum sat a machine you ride every day:", "machine"),
 (9.84, "an elevator.", "elevator"),
 (11.03, "Below the sand was the hypogeum,", "hypogeum"),
 (13.22, "a maze of tunnels and cells.", "maze"),
 (15.78, "A lion waited in a wooden cage.", "lion"),
 (18.15, "Nothing bigger would fit.", "bigger"),
 (19.76, "Beside it stood a capstan,", "capstan"),
 (21.50, "an upright winch two stories tall.", "two"),
 (24.15, "Eight men pushed its bars in a circle,", "Eight"),
 (26.46, "four on each level.", "four"),
 (28.00, "Ropes wound around the shaft,", "Ropes"),
 (29.86, "and the cage climbed about twenty five feet.", "twenty"),
 (32.52, "At the top, a trap door swung down into a ramp.", "ramp"),
 (35.99, "The lion ran up it, straight into the light,", "light"),
 (38.75, "and fifty thousand people watched it appear from nowhere.", "fifty"),
 (42.63, "Dozens of these lifts were hidden under one floor,", "Dozens"),
 (45.40, "so a hunter never knew where the next lion would rise.", "never"),
 (48.68, "When that floor opens in Gladiator, you are watching a Roman elevator.", "elevator"),
]
SIL = [(0.966, 1.183), (4.272, 4.619), (5.659, 6.216), (9.510, 9.840), (10.58, 11.03), (13.008, 13.22), (15.258, 15.78),
       (17.910, 18.150), (19.318, 19.76), (21.316, 21.50), (23.782, 24.15), (26.293, 26.46), (27.653, 28.0), (29.70, 29.86),
       (32.165, 32.52), (33.155, 33.355), (35.699, 35.99), (37.21, 37.366), (38.579, 38.75), (39.431, 39.587),
       (42.262, 42.63), (45.26, 45.40), (48.267, 48.68), (50.504, 50.706)]
TARGET = {}
OVR = {(6, 'waited'): 16.31, (6, 'in'): 16.57, (6, 'wooden'): 16.93, (6, 'cage.'): 17.39}
DRAMA = {5.659: 0.45, 19.318: 0.45, 32.165: 0.45, 42.262: 0.45, 48.267: 0.42}

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
    if i + 1 == len(PHR): return end_sound
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

"""E016 longbow: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.04, "Pulling this bow back took the force of lifting a grown man,", "force"),
 (3.93, "likely around 150 pounds.", "150"),
 (6.67, "This is the English longbow,", "longbow"),
 (8.73, "about six and a half feet of yew.", "yew"),
 (11.13, "The bowyer cut each stave so pale sapwood faced the target", "sapwood"),
 (14.87, "and dark heartwood faced the archer.", "heartwood"),
 (17.24, "Sapwood resists stretching,", "stretching"),
 (19.10, "heartwood resists crushing,", "crushing"),
 (20.90, "so one piece of wood worked like a spring.", "spring"),
 (23.83, "Nobody could draw that weight without years of training,", "training"),
 (26.91, "so English law ordered men to practise archery on holidays.", "law"),
 (30.68, "Skeletons of later English archers show it,", "Skeletons"),
 (33.20, "with heavier bones in the drawing arm.", "bones"),
 (35.61, "On October 25, 1415, at Agincourt,", "Agincourt"),
 (39.01, "nearly four in five of Henry the Fifth's men were archers.", "archers"),
 (42.88, "The French knights, most on foot,", "foot"),
 (44.77, "crossed a ploughed field soaked by a night of rain.", "rain"),
 (48.02, "The mud slowed them down,", "mud"),
 (49.58, "and the arrows kept coming.", "arrows"),
 (51.44, "Every one of those arrows began with a pull of around 150 pounds.", "150"),
]
SIL = [(3.68, 3.93), (6.18, 6.67), (8.50, 8.73), (10.57, 11.13), (14.66, 14.87), (16.80, 17.24), (18.81, 19.10), (20.64, 20.90),
       (23.29, 23.83), (26.70, 26.91), (30.31, 30.68), (32.99, 33.20), (35.05, 35.61), (38.82, 39.01), (42.44, 42.88), (44.58, 44.77),
       (47.59, 48.02), (49.38, 49.58), (51.04, 51.44)]
TARGET = {}
# numbers read as several words: onset of the first spoken word (original time, from asr.txt)
OVR = {(1, '150'): 4.56, (13, '25,'): 36.13, (13, '1415,'): 36.81, (13, 'at'): 37.96, (13, 'Agincourt,'): 38.13, (19, '150'): 54.28}
DRAMA = {6.18: 0.32, 10.57: 0.45, 23.29: 0.45, 35.05: 0.45, 47.59: 0.36, 51.04: 0.42}

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

"""E021 scorpio: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.06, "Wind a toy plane's propeller", "propeller"),
 (1.83, "and the rubber band twists into tight knots.", "knots"),
 (4.66, "Let go, and that stored twist", "twist"),
 (6.66, "spins it across the yard.", "spins"),
 (8.71, "Roman engineers built a weapon on that same twist.", "Roman"),
 (12.18, "The scorpio had no bending bow.", "scorpio"),
 (14.59, "Each wooden arm sat inside a thick bundle of animal sinew,", "sinew"),
 (18.11, "wound tight with a winch.", "winch"),
 (19.94, "Pull the bowstring back,", "bowstring"),
 (21.32, "and the arms twist those bundles even harder.", "harder"),
 (24.05, "Hit the trigger,", "trigger"),
 (24.91, "and they spin forward, hurling an iron tipped bolt.", "bolt"),
 (28.45, "Caesar wrote that in 52 BC,", "Caesar"),
 (30.76, "one scorpio killed Gallic defender", "killed"),
 (32.98, "after defender", "defender"),
 (33.91, "at the same spot on the wall.", "spot"),
 (35.98, "In Britain, at Hod Hill,", "Hod"),
 (37.72, "archaeologists found eleven bolt heads clustered in one hut,", "eleven"),
 (41.45, "likely shot from around 170 metres.", "170"),
 (44.62, "The weak point was the spring itself.", "weak"),
 (46.99, "Rain loosened the sinew,", "Rain"),
 (48.57, "and a slack bundle threw nothing.", "nothing"),
 (50.54, "Dry sinew was the whole machine.", "Dry"),
 (52.92, "Wind it tight.", "tight"),
 (54.02, "Let it go.", "go"),
]
SIL = [(4.33, 4.68), (8.15, 8.72), (11.84, 12.23), (14.27, 14.63), (17.99, 18.15), (19.61, 19.96), (21.21, 21.34), (23.77, 24.08),
       (26.14, 26.26), (27.96, 28.46), (30.72, 30.87), (35.55, 36.01), (37.54, 37.76), (41.27, 41.48), (44.16, 44.66), (46.70, 47.01),
       (48.41, 48.54), (50.20, 50.54), (52.61, 52.95), (53.69, 54.04)]
TARGET = {}
OVR = {(12, '52'): 29.43, (12, 'BC,'): 30.10, (18, '170'): 42.62, (0, 'Wind'): 0.06}
DRAMA = {8.15: 0.45, 27.96: 0.45, 35.55: 0.45, 44.16: 0.45, 52.61: 0.40}

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

"""E015 corvus: tighten pauses, chapter holds, word onsets from pocketsphinx timestamps (asr.txt)."""
import json, re, difflib
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.04, "Rome could win almost any fight on land.", "land"),
 (2.84, "At sea, it had almost no experience.", "sea"),
 (5.71, "Carthage ruled the water.", "Carthage"),
 (7.63, "Its crews could ram a ship and row away", "ram"),
 (9.93, "before a single Roman sword got close.", "sword"),
 (12.73, "So in 260 BC,", "260"),
 (14.79, "the Romans changed the rules.", "rules"),
 (16.89, "On each prow they mounted a tall pole with a pulley.", "pulley"),
 (20.31, "Hanging from it was a wooden bridge", "bridge"),
 (22.06, "about 36 feet long and 4 feet wide,", "36"),
 (24.91, "with a knee high rail on each side.", "rail"),
 (27.08, "At its tip sat an iron spike, shaped like a pestle.", "spike"),
 (30.69, "When an enemy ship came near, the crew let the rope go.", "rope"),
 (34.12, "The bridge swung down,", "down"),
 (35.52, "the spike punched into the deck,", "punched"),
 (37.32, "and the two ships were locked together.", "locked"),
 (39.49, "Then the legionaries walked across.", "legionaries"),
 (41.88, "Off Mylae in Sicily,", "Mylae"),
 (43.40, "Carthage lost around fifty ships.", "fifty"),
 (45.82, "The sea battle had become a land battle.", "land"),
 (48.57, "And on land, Rome rarely lost.", "rarely"),
]
SIL = [(1.22, 1.40), (2.50, 2.88), (5.41, 5.78), (7.30, 7.66), (12.32, 12.77), (14.65, 14.83), (16.46, 16.93),
       (19.88, 20.34), (24.70, 24.93), (26.74, 27.13), (30.29, 30.73), (32.18, 32.38), (33.74, 34.15), (35.40, 35.57),
       (37.14, 37.36), (39.13, 39.51), (41.51, 41.93), (43.28, 43.45), (45.52, 45.88), (48.16, 48.59)]
TARGET = {1.22: 0.10}
DRAMA = {12.32: 0.45, 16.46: 0.42, 30.29: 0.45, 41.51: 0.45, 48.16: 0.42}

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
        words.append({'w': w, 't': round(M(on[j]), 3), 'p': i, 'kw': re.sub(r'[^\w]', '', w) == kw})
    caps.append({'s': round(M(s0), 3), 'e': round(M(e), 3), 't': txt, 'k': kw})

json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2))
for c in caps:
    print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")
    print('        ', ' '.join(f"{w['w']}@{w['t']:.2f}" for w in words if w['p'] == caps.index(c)))

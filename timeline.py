"""Tighten pauses, build time map, phrase list and word onsets for E014 Greek fire."""
import json, re
import numpy as np, soundfile as sf

SR = 48000
x, sr = sf.read('vo_orig.wav'); assert sr == SR
hop = int(0.01 * SR)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

PHR = [
 (0.10, "Everyone says the secret of Greek fire was the liquid.", "liquid"),
 (3.616, "The real secret was the machine that fired it.", "machine"),
 (6.791, "Around 672 AD,", "672"),
 (8.79, "a refugee architect named Kallinikos", "Kallinikos"),
 (11.12, "reached Constantinople from Syria.", "Constantinople"),
 (13.407, "Arab fleets were about to besiege the city.", "besiege"),
 (16.270, "Byzantine warships carried a bronze tube on the bow.", "bronze"),
 (19.665, "Behind it, sources suggest,", "suggest"),
 (21.518, "the liquid was heated in a sealed tank while a crew worked a pump.", "pump"),
 (25.462, "Pressure built.", "Pressure"),
 (26.544, "A jet shot out, was lit at the nozzle, and spread across the water.", "lit"),
 (30.852, "Water could not put it out.", "Water"),
 (32.599, "Only sand, vinegar or urine could, according to later accounts.", "vinegar"),
 (36.793, "It needed calm seas and close range, so crews had to get near.", "calm"),
 (41.189, "In 812, a Bulgar army captured siphons and fuel.", "812"),
 (45.121, "They could not make them work.", "work"),
 (46.662, "The liquid was never the whole secret.", "whole"),
 (48.977, "It was the machine that fired it.", "machine"),
]
SIL = [(3.306, 3.616), (6.330, 6.791), (8.53, 8.79), (11.02, 11.12), (13.094, 13.407), (15.880, 16.270), (19.333, 19.665),
       (21.281, 21.518), (25.094, 25.462), (26.295, 26.544), (30.542, 30.852), (32.327, 32.599), (36.459, 36.793),
       (40.822, 41.189), (44.798, 45.121), (46.323, 46.662), (48.690, 48.977)]
DRAMA = {6.330: 0.45, 19.333: 0.42, 26.295: 0.45, 30.542: 0.45, 40.822: 0.45, 46.323: 0.42}   # before "Water could not", "In 812", "The liquid was never"

# lead in: find first sound
first = np.argmax(db > -45) * 0.01
end_sound = len(db) * 0.01 - np.argmax(db[::-1] > -45) * 0.01
keep = []  # (orig_start, orig_end)
cur = max(0.0, first - 0.04)
for s, e in SIL:
    target = DRAMA.get(s, 0.20)
    dur = e - s
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
lead = 0.12   # tiny breath so the opening thud lands first
y = np.concatenate([np.zeros(int(lead * SR)), y])
sf.write('vo_tight.wav', y, SR, subtype='PCM_24')

def M(t):
    for a, b, n in tmap:
        if t < a: return n + lead - (0 if not tmap or a == tmap[0][0] else 0)
        if t <= b: return n + (t - a) + lead
    a, b, n = tmap[-1]; return n + (b - a) + lead

# word onsets: syllable weights inside each phrase, snapped to energy dips
def syl(w):
    w = re.sub(r'[^a-z0-9]', '', w.lower())
    if w.isdigit(): return 4
    v = len(re.findall(r'[aeiouy]+', w))
    if w.endswith('e') and v > 1 and not w.endswith('le'): v -= 1
    return max(1, v)

def phrase_end(i):
    nxt = PHR[i + 1][0] if i + 1 < len(PHR) else end_sound + 0.3
    ends = [s for s, e in SIL if PHR[i][0] < s < nxt]
    return ends[0] if ends else end_sound

caps = []; words = []
for i, (s0, txt, kw) in enumerate(PHR):
    s = max(s0, first) if i == 0 else s0
    # refine onset: first frame above -40 dB after s
    k = int(s * 100)
    while k < len(db) - 1 and db[k] < -40: k += 1
    s = k * 0.01
    e = phrase_end(i)
    ws = txt.split(); wt = np.array([syl(w) + 0.35 for w in ws], float)
    cum = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
    on = []
    for j, w in enumerate(ws):
        t = s + cum[j] * (e - s)
        if j > 0:
            lo, hi = int((t - 0.09) * 100), int((t + 0.09) * 100)
            seg = db[lo:hi]
            if len(seg): t = (lo + int(np.argmin(seg))) * 0.01 + 0.02
        on.append(t)
    for j, w in enumerate(ws):
        words.append({'w': w, 't': round(M(on[j]), 3), 'p': i, 'kw': re.sub(r'[^\w]', '', w) == kw})
    caps.append({'s': round(M(s), 3), 'e': round(M(e), 3), 't': txt, 'k': kw})

json.dump({'caps': caps, 'words': words, 'dur': round(len(y) / SR, 3)}, open('timing.json', 'w'), indent=1)
print('orig', round(len(x) / SR, 2), 'new', round(len(y) / SR, 2), 'first', first)
for c in caps: print(f"{c['s']:6.2f} {c['e']:6.2f}  {c['t']}")

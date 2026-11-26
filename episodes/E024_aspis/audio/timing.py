"""E024 word timings: phrase spans from silencedetect (-45 dB, 60 ms) on the ElevenLabs voice, words split by syllable
weight, each onset snapped to the lowest energy point within 90 ms. Good to roughly 0.1 s. Writes words.json."""
import json, re
import numpy as np, soundfile as sf

x, sr = sf.read('vo_orig.wav')
hop = int(0.005 * sr)
env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop] + 1e-9
db = 20 * np.log10(env)

# (start, end, text): spans measured from the pauses
PHR = [
    (0.12, 2.53, "A Greek soldier carried a shield"),
    (2.61, 4.01, "that left his own right side open."),
    (4.39, 7.50, "Around three feet across and about sixteen pounds,"),
    (7.67, 10.13, "the hoplite shield had no handle in the middle."),
    (10.44, 13.21, "His forearm went through a bronze band at the center,"),
    (13.35, 15.49, "and his hand gripped a cord near the rim."),
    (15.80, 17.54, "So the shield sat to his left,"),
    (17.68, 19.73, "and its left half covered the next man."),
    (20.04, 22.88, "His own right side depended on the man to his right."),
    (23.19, 25.55, "Thucydides described the result"),
    (25.55, 27.36, "at Mantinea in 418 BC."),
    (27.74, 29.04, "Each man edged right"),
    (29.12, 31.92, "to tuck his open side behind his neighbor's shield,"),
    (32.10, 34.67, "and both armies drifted right as they closed."),
    (35.00, 35.74, "Break the line,"),
    (35.87, 37.81, "and every right side was bare."),
    (38.15, 41.18, "That is why Spartans shamed a man who dropped his shield,"),
    (41.41, 42.18, "not his helmet."),
    (42.50, 44.16, "The helmet protected one man."),
    (44.45, 46.30, "The shield protected the line."),
]
SPOKEN = {'418': 'four eighteen', 'BC': 'bee see'}

def syl(w):
    w = SPOKEN.get(w, w).lower()
    n = 0
    for part in w.split():
        part = re.sub(r'[^a-z]', '', part)
        g = re.findall(r'[aeiouy]+', part)
        k = len(g) - (1 if part.endswith('e') and len(g) > 1 and not part.endswith('le') else 0)
        n += max(1, k)
    return n

def snap(t, win=0.09):
    i0, i1 = int((t - win) / 0.005), int((t + win) / 0.005)
    i0 = max(0, i0); i1 = min(len(db) - 1, i1)
    if i1 <= i0: return t
    j = i0 + int(np.argmin(db[i0:i1]))
    return j * 0.005

out = []
for i, (a, b, text) in enumerate(PHR):
    toks = text.split(); wts = [syl(re.sub(r'[^\w]', '', w)) for w in toks]
    tot = sum(wts); t = a; words = []
    for j, (w, k) in enumerate(zip(toks, wts)):
        on = a if j == 0 else snap(t)
        words.append(dict(w=w, t=round(on, 3)))
        t += (b - a) * k / tot
    out.append(dict(i=i + 1, start=a, end=b, text=text, words=words))
json.dump(out, open('words.json', 'w'), indent=1)
for p in out: print(p['i'], p['start'], ' '.join(f"{w['w']}@{w['t']:.2f}" for w in p['words']))

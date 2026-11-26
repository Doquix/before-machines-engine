"""E024 sound: synthesized SFX on the beat table, a D dorian bed (drone, plucked string, low drums in the battle),
ducked under the voice. Writes mix_raw.wav (mastering is done with ffmpeg as in the render skill)."""
import json, math, os, sys
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000; END = 47.4; N = int(END * SR)
rng = np.random.default_rng(7)
vo, sr = sf.read(os.path.join(HERE, 'vo_orig.wav')); assert sr == SR
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
WORDS = json.load(open(os.path.join(HERE, 'words.json')))
w = lambda b, i: WORDS[b - 1]['words'][i]['t']; bs = lambda b: WORDS[b - 1]['start']

sfx = np.zeros(N); mus = np.zeros(N)
def add(buf, t, x, g=1.0):
    i = int(t * SR); j = min(N, i + len(x))
    if 0 <= i < N: buf[i:j] += g * x[:j - i]
def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)
def lp(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')
def noise(d): return rng.standard_normal(int(d * SR))
def clank(d=0.9, f0=420):
    t = np.arange(int(d * SR)) / SR
    x = sum(a * np.sin(2 * math.pi * f0 * r * t + rng.random() * 6) * np.exp(-t * dk) for r, a, dk in
            ((1, 1, 6), (2.76, .6, 9), (5.4, .4, 14), (8.9, .25, 20)))
    return x * env(len(t), 0.002, 0.5) + 0.3 * lp(noise(d), 3) * env(len(t), 0.001, 0.02)
def thud(d=0.5, f=60):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * math.pi * (f + 40 * np.exp(-t * 30)) * t) * env(len(t), 0.002, 0.12) + 0.2 * lp(noise(d), 40) * env(len(t), .001, .05)
def whoosh(d=0.45):
    n = int(d * SR); x = noise(d); t = np.arange(n) / n
    out = np.zeros(n); k = 2
    for s in range(0, n, 2400):          # moving low pass
        kk = int(lerp(60, 6, math.sin(math.pi * s / n)))
        out[s:s + 2400] = lp(x, max(2, kk))[s:s + 2400]
    return out * np.sin(math.pi * t) ** 2
def lerp(a, b, u): return a + (b - a) * u
def mx(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o
def tick(): return clank(0.15, 1800) * 0.5
def scratch(d=0.35): x = noise(d); return (x - lp(x, 4)) * env(len(x), 0.01, 0.2) * 0.6
def rustle(d=0.6):
    x = noise(d); x = x - lp(x, 6); g = (rng.random(len(x)) < 0.002).astype(float); g = lp(g, 900) * 40
    return x * np.clip(g, 0, 1) * 0.5
def stampfx(): return mx(thud(0.6, 50) * 1.2, clank(0.3, 900) * 0.3)
def scrape(d=0.7):
    t = np.arange(int(d * SR)) / SR; x = noise(d)
    x = x[:len(t)]
    return (x - lp(x, 3)) * 0.3 * np.sin(math.pi * t / d) + 0.3 * np.sin(2 * math.pi * 1300 * t) * np.sin(math.pi * t / d) * 0.2
def drum(d=0.6): return thud(d, 48) * 1.3

# ---- events (times from the measured words) ----
add(sfx, 0.08, clank(0.8, 380), 0.5)
add(sfx, w(2, 6), thud(), 0.7)
for t in (bs(3), bs(10), bs(15), bs(17)): add(sfx, t - 0.12, whoosh(), 0.55)
add(sfx, w(3, 3), tick(), 0.6); add(sfx, w(3, 6), tick(), 0.6)
add(sfx, bs(4), whoosh(0.5), 0.25); add(sfx, w(4, 5) + 0.4, scratch(), 0.8)
add(sfx, w(5, 1), scrape(0.6), 0.5); add(sfx, w(5, 6), tick(), 0.5)
add(sfx, w(6, 3), clank(0.25, 260), 0.3); add(sfx, w(6, 5), tick(), 0.5)
add(sfx, bs(7) + 0.1, clank(0.7, 400), 0.35)
for j in range(3): add(sfx, bs(8) + 0.35 + 0.15 * j, clank(0.7, 360 + 40 * j), 0.45)
add(sfx, w(8, 4), stampfx(), 0.8)
add(sfx, w(9, 4), tick(), 0.4)
add(sfx, bs(10) + 0.1, rustle(0.8), 0.9); add(sfx, w(10, 1), tick(), 0.5)
add(sfx, bs(11) + 0.05, whoosh(0.6), 0.2); add(sfx, w(11, 1), drum(), 0.7)
for j in range(10): add(sfx, w(12, 2) + j * 0.1, lp(noise(0.12), 8) * env(int(.12 * SR), .005, .05), 0.35)
add(sfx, w(13, 1), scrape(0.8), 0.6)
for j in range(8): add(sfx, bs(14) + j * 0.36, drum(0.5), 0.55 if j % 2 == 0 else 0.35)
tb = w(15, 0)
add(sfx, tb - 0.3, whoosh(0.3), 0.6); add(sfx, tb + 0.02, clank(0.9, 300), 0.7)      # enemy spear drives in and strikes
add(sfx, tb + 0.05 + 0.12 + 0.7, thud(0.7, 50), 0.9); add(sfx, tb + 0.05 + 0.12 + 0.7, clank(0.8, 280), 0.4)   # he lands
add(sfx, w(16, 5), mx(clank(1.2, 520) * 0.6, thud(0.5, 70)), 0.6)
td = w(17, 8); add(sfx, td + 0.5, clank(1.1, 330), 0.8); add(sfx, td + 0.75, clank(0.6, 340), 0.35)
th = w(18, 1) - 0.35
add(sfx, th + 0.3, clank(0.3, 700), 0.2)                     # helmet lifted off
add(sfx, th + 0.85 + 0.38, clank(0.6, 560), 0.45)            # it lands on its rim
add(sfx, w(19, 3), scratch(0.5), 0.7)
for j in range(3): add(sfx, bs(20) + 0.45 + 0.12 * j, clank(0.8, 360 + 30 * j), 0.5)
# wind under the outdoor shots
wind = lp(noise(END), 120); wind /= np.abs(wind).max()
for a, b in ((0, bs(3)), (bs(15), bs(19)), (bs(20), END)):
    i, j = int(a * SR), int(b * SR); fade = np.minimum(1, np.minimum(np.arange(j - i), np.arange(j - i)[::-1]) / (0.2 * SR))
    sfx[i:j] += wind[i:j] * 0.08 * fade

# ---- music: D dorian ----
t = np.arange(N) / SR
drone = 0.5 * np.sin(2 * math.pi * 73.42 * t) + 0.35 * np.sin(2 * math.pi * 110.0 * t) + 0.12 * np.sin(2 * math.pi * 146.83 * t)
drone *= 0.6 + 0.4 * np.sin(2 * math.pi * t / 6.0) ** 2
mus += drone * 0.18
def pluck(f, d=1.6):
    n = int(d * SR); L = int(SR / f); buf = rng.uniform(-1, 1, L); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % L]; buf[i % L] = 0.996 * 0.5 * (buf[i % L] + buf[(i + 1) % L])
    return out
NOTES = [293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25]
seq = [0, 4, 3, 2, 0, 4, 5, 4, 3, 1, 0, 2, 4, 3, 2, 1]
tt = 0.3; i = 0
while tt < END - 1:
    if not (bs(14) - 0.2 < tt < bs(17)):
        add(mus, tt, pluck(NOTES[seq[i % len(seq)]] / 2), 0.22)
    tt += 1.45; i += 1
for j in range(int((bs(17) - bs(14)) / 0.72)):
    add(mus, bs(14) + j * 0.72, drum(0.7), 0.4)
# cut the bed briefly before the stamp
i0, i1 = int((w(8, 4) - 0.3) * SR), int((w(8, 4) + 0.25) * SR)
mus[i0:i1] *= np.linspace(1, 0, i1 - i0) ** 0.5 * 0
# ---- duck under the voice ----
ve = np.sqrt(lp(vo ** 2, int(0.05 * SR))); ve = ve / ve.max()
duck = 1 - 0.6 * np.clip(ve * 4, 0, 1); duck = lp(duck, int(0.08 * SR))
mix = vo * 1.0 + sfx * 0.55 + mus * duck * 0.6
fade = np.ones(N); k = int(0.5 * SR); fade[-k:] = np.linspace(1, 0.2, k)
mix *= fade
sf.write(os.path.join(HERE, 'mix_raw.wav'), (mix / max(1e-9, np.abs(mix).max()) * 0.8).astype(np.float32), SR)
print('ok')

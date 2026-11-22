"""E021 scorpio: SFX from the cue sheet, a modal music bed, ducking and mix (48 kHz stereo)."""
import json, math
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
CU = json.load(open('cues.json')); T = CU['T']; DUR = CU['dur']; FLIGHT_ = 0.5
N = int(DUR * SR) + SR
rng = np.random.default_rng(1)

def tt(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.003, dec=0.1):
    t = tt(d); return np.minimum(1, t / a) * np.exp(-t / dec)
def lp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2)); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = signal.butter(o, [f1 / (SR / 2), f2 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def sweep(f0, f1, d):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d); return np.sin(2 * np.pi * np.cumsum(f) / SR)
def noise(d): return rng.standard_normal(int(d * SR))

def s_thud(): d = 0.45; return sweep(95, 38, d) * env(d, .002, .12) + lp(noise(d), 300) * env(d, .001, .03) * 0.6
def s_pop(): d = 0.09; return sweep(950, 380, d) * env(d, .002, .03)
def s_tick(): d = 0.03; return np.sin(2 * np.pi * 2600 * tt(d)) * env(d, .001, .006)
def s_stamp(): d = 0.4; x = s_thud()[:int(d * SR)]; return x + bp(noise(d), 900, 3500) * env(d, .001, .04) * 0.8
def s_whoosh(down=False, d=0.42, lo=False):
    x = noise(d); out = np.zeros_like(x); n = 24; L = len(x) // n
    for i in range(n):
        u = i / n; f = (2600 - 2000 * u) if down else (500 + 2400 * math.sin(u * math.pi))
        if lo: f *= 0.35
        seg = bp(x[i * L:(i + 2) * L], max(80, f * 0.6), min(20000, f * 1.4))
        out[i * L:i * L + len(seg)] += seg[:len(out) - i * L] * 0.5
    e = np.sin(np.linspace(0, np.pi, len(out))) ** 2
    return out * e * 1.6
def s_hit():
    d = 1.0; return sweep(80, 32, d) * env(d, .002, .35) * 1.2 + lp(noise(d), 2500) * env(d, .001, .18) * 0.7 + np.pad(s_stamp(), (0, int(.6 * SR)))[:int(d * SR)] * .5
def s_clink():
    d = 0.5; t = tt(d); x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1870, 1), (2930, .6), (4210, .4), (5560, .25)))
    return x * env(d, .001, .09) * 0.5 + hp(noise(d), 4000) * env(d, .001, .01) * .3
def s_clack():
    d = 0.18; return lp(noise(d), 1800) * env(d, .001, .025) + np.sin(2 * np.pi * 420 * tt(d)) * env(d, .001, .03) * .6
def s_cloth():
    d = 0.5; x = bp(noise(d), 700, 3000); m = 0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt(d)); return x * m * np.sin(np.linspace(0, np.pi, len(x))) * .6
def s_creak():
    d = 0.6; t = tt(d); f = 140 + 40 * np.sin(2 * np.pi * 3 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * t)))
    return bp(x, 300, 1800) * np.sin(np.linspace(0, np.pi, len(x))) * .5
def s_ratchet():
    d = 0.06; return bp(noise(d), 1500, 5000) * env(d, .0005, .008) + np.sin(2 * np.pi * 900 * tt(d)) * env(d, .001, .01) * .4
def s_riser():
    d = 1.6; t = tt(d); return (hp(noise(d), 2000) * .4 + sweep(180, 900, d) * .3) * (t / d) ** 2
def s_shimmer():
    d = 0.8; t = tt(d); x = np.zeros_like(t)
    for _ in range(14):
        f = rng.uniform(3000, 8000); o = rng.uniform(0, .3)
        x += np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - o) / .2) * (t > o)
    return x * .05
def s_chime():
    d = 1.0; t = tt(d); x = np.zeros_like(t)
    for i, f in enumerate((587.3, 698.5, 880, 1174.7)):
        o = i * 0.06; x += np.sin(2 * np.pi * f * (t - o)) * np.exp(-np.maximum(0, t - o) / .35) * (t > o)
    return x * .3
def s_scrape():
    d = 0.7; x = bp(noise(d), 2000, 6000); m = 0.6 + 0.4 * np.sin(2 * np.pi * 40 * tt(d)); return x * m * np.sin(np.linspace(0, np.pi, len(x))) * .5
def s_rubble():
    d = 1.6; x = np.zeros(int(d * SR))
    for _ in range(26):
        o = int(rng.uniform(0, 1.1) * SR); c = s_clack() * rng.uniform(.3, 1)
        x[o:o + len(c)] += c[:len(x) - o]
    return x * .7 + lp(noise(d), 400) * env(d, .01, .5) * .8

def s_roar(d=0.9):
    x = noise(d); x = lp(x, 1400) * 0.7 + bp(x, 200, 600) * 0.6
    m = 0.75 + 0.25 * np.sin(2 * np.pi * 11 * tt(d)) * rng.uniform(.5, 1, len(x))
    return x * m * np.minimum(1, tt(d) / 0.05) * np.exp(-tt(d) / (d * 0.6))
def s_roarlong(): return s_roar(1.8)
def s_ignite():
    d = 0.6; return lp(noise(d), 3000) * env(d, .002, .08) + sweep(60, 180, d) * env(d, .01, .2) * .6 + s_roar(d) * .6
def s_hiss():
    d = 0.7; return hp(noise(d), 3000) * np.sin(np.linspace(0, np.pi, int(d * SR))) * .6
def s_slosh():
    d = 0.5; x = lp(noise(d), 900); m = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * tt(d)); return x * m * np.sin(np.linspace(0, np.pi, len(x)))
def s_paper():
    d = 0.4; return bp(noise(d), 1500, 6000) * (rng.uniform(0, 1, int(d * SR)) > 0.6) * np.sin(np.linspace(0, np.pi, int(d * SR))) * .7
def s_horn():
    d = 1.2; t = tt(d); x = sum(signal.sawtooth(2 * np.pi * f * t) * a for f, a in ((110, 1), (165, .5), (220, .3)))
    return lp(x, 900) * np.minimum(1, t / .2) * np.minimum(1, (d - t) / .3) * .5
def s_clank():
    d = 0.5; t = tt(d); x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((420, 1), (1130, .6), (1900, .4)))
    return x * env(d, .001, .12) + lp(noise(d), 2000) * env(d, .001, .02)
def s_pumpstroke():
    d = 0.22; return lp(noise(d), 700) * env(d, .01, .07) + sweep(160, 90, d) * env(d, .005, .06) * .5
def s_splash():
    d = 0.8; return bp(noise(d), 500, 5000) * env(d, .005, .2) + lp(noise(d), 300) * env(d, .002, .08) * .6
def s_pour():
    d = 0.7; x = bp(noise(d), 1200, 4500); m = 0.6 + 0.4 * (rng.uniform(0, 1, len(x)) > 0.5)
    return x * m * np.sin(np.linspace(0, np.pi, len(x))) * .6
def s_waves():
    d = 2.6; t = tt(d); return lp(noise(d), 600) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.6 * t)) * np.minimum(1, (d - t) / 0.8)
def s_dribble():
    d = 0.5; x = np.zeros(int(d * SR))
    for i in range(5):
        o = int(i * 0.09 * SR); c = s_pop()[:int(.06 * SR)] * .4; x[o:o + len(c)] += c
    return x
def s_puff():
    d = 0.6; return lp(noise(d), 500) * env(d, .01, .18)


def s_march():
    d = 0.9; x = np.zeros(int(d * SR))
    for i in range(4):
        o = int(i * 0.2 * SR); c = (lp(noise(0.12), 500) * env(0.12, .002, .03) + sweep(90, 50, 0.12) * env(0.12, .002, .04) * .6) * (1 - i * .12)
        x[o:o + len(c)] += c[:len(x) - o]
    return x
def s_oars():
    d = 1.4; x = np.zeros(int(d * SR))
    for i in range(4):
        o = int(i * 0.33 * SR); c = bp(noise(0.3), 400, 2500) * np.sin(np.linspace(0, np.pi, int(.3 * SR))) * .6
        x[o:o + len(c)] += c[:len(x) - o]
    return x
def s_crack():
    d = 0.6; x = np.zeros(int(d * SR))
    for i in range(7):
        o = int(rng.uniform(0, .25) * SR); c = bp(noise(0.05), 800, 6000) * env(0.05, .0005, .01)
        x[o:o + len(c)] += c[:len(x) - o]
    return x + lp(noise(d), 600) * env(d, .002, .12) * .6
def s_swish():
    d = 0.3; return bp(noise(d), 2500, 9000) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 2 * 1.2
def s_ratchetrun():
    d = 0.5; x = np.zeros(int(d * SR))
    for i in range(8):
        o = int(i * 0.055 * SR); c = s_ratchet(); x[o:o + len(c)] += c[:len(x) - o]
    return x
def s_knock():
    d = 0.15; return lp(noise(d), 1200) * env(d, .001, .02) + sweep(320, 180, d) * env(d, .001, .03) * .7
def s_slide():
    d = 0.5; return bp(noise(d), 300, 1500) * np.sin(np.linspace(0, np.pi, int(d * SR))) * .7
def s_footsteps():
    d = 1.2; x = np.zeros(int(d * SR))
    for i in range(5):
        o = int(i * 0.24 * SR); c = lp(noise(0.08), 900) * env(0.08, .001, .02)
        x[o:o + len(c)] += c[:len(x) - o]
    return x
def s_ropewhip():
    d = 0.5; return bp(noise(d), 1500, 7000) * env(d, .005, .12) + sweep(900, 200, d) * env(d, .002, .08) * .3
def s_sinking():
    d = 1.6; t = tt(d); return lp(noise(d), 700) * (0.4 + 0.6 * (rng.uniform(0, 1, len(t)) > 0.97)) * np.minimum(1, (d - t) / .5) * .7
def s_swordclash():
    c = s_clink(); return c + np.pad(c, (int(.07 * SR), 0))[:len(c)] * .6 + hp(noise(.5), 3000) * env(.5, .001, .03) * .4

def s_twang():
    d = 0.7; t = tt(d); f0 = 110
    x = sum(np.sin(2 * np.pi * f0 * h * t * (1 + 0.004 * np.exp(-t * 20))) / h for h in (1, 2, 3, 4, 6)) * np.exp(-t / 0.12)
    return x * 0.8 + bp(noise(d), 200, 1200) * env(d, .001, .03) * 0.6 + lp(noise(d), 180) * env(d, .001, .06) * 0.5
def s_whiz():
    d = 0.45; x = bp(noise(d), 1800, 7000) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 3
    t = tt(d); return x * 1.1 + np.sin(2 * np.pi * np.cumsum(900 - 500 * t / d) / SR) * np.sin(np.linspace(0, np.pi, len(t))) ** 4 * 0.15
def s_thunk():
    d = 0.4; return sweep(160, 70, d) * env(d, .001, .06) + lp(noise(d), 900) * env(d, .001, .03) * 0.9 + bp(noise(d), 2000, 5000) * env(d, .001, .008) * 0.4
def s_stretch():
    d = 0.6; t = tt(d); return np.sin(2 * np.pi * np.cumsum(180 + 260 * t / d) / SR) * np.sin(np.linspace(0, np.pi, len(t))) * 0.35 + s_creak()[:len(t)] * 0.5
def s_squeeze():
    d = 0.6; t = tt(d); return np.sin(2 * np.pi * np.cumsum(420 - 280 * t / d) / SR) * np.sin(np.linspace(0, np.pi, len(t))) * 0.35 + lp(noise(d), 500) * np.sin(np.linspace(0, np.pi, len(t))) * 0.3
def s_bell():
    d = 2.0; t = tt(d); x = sum(np.sin(2 * np.pi * f * t) * a * np.exp(-t / dc) for f, a, dc in ((392, 1, .9), (784, .5, .6), (1046, .35, .5), (1568, .2, .3), (466, .3, .7)))
    return x * 0.5
def s_rain():
    d = 3.2; t = tt(d); x = bp(noise(d), 1500, 9000) * 0.5 + lp(noise(d), 400) * 0.3
    drops = (rng.uniform(0, 1, len(t)) > 0.9985).astype(float); x += lp(drops, 3000) * 4
    return x * np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.6)
def s_rumble():
    d = 2.2; t = tt(d); return lp(noise(d), 120) * np.minimum(1, t / 0.3) * np.exp(-t / 0.9) * 2.0
def s_squelch():
    d = 0.4; t = tt(d); return (lp(noise(d), 700) * env(d, .004, .06) + np.sin(2 * np.pi * np.cumsum(260 - 180 * t / d) / SR) * env(d, .003, .08) * 0.6)
def s_volley():
    d = 0.9; x = np.zeros(int(d * SR))
    for i in range(10):
        o = int(rng.uniform(0, .12) * SR); c = s_whiz() * rng.uniform(0.4, 0.9)
        x[o:o + len(c)] += c[:len(x) - o]
    return x
def s_clatter():
    d = 0.8; x = np.zeros(int(d * SR))
    for i in range(14):
        o = int(rng.uniform(0, .3) * SR); c = (s_clink() if i % 3 == 0 else s_thunk() * 0.6)[:int(0.3 * SR)] * rng.uniform(0.3, 0.8)
        x[o:o + len(c)] += c[:len(x) - o]
    return x

def s_buzz():
    d = 1.6; t_ = tt(d); f = 95 + 20 * np.sin(t_ * 3)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.5 + bp(noise(d), 300, 1400) * 0.4
    return lp(x, 2400) * np.minimum(1, t_ / 0.05) * np.clip((d - t_) / 0.8, 0, 1)
def s_fire():
    d = 3.0; x = bp(noise(d), 200, 2500) * 0.3
    for _ in range(40):
        o = int(rng.uniform(0, d - 0.05) * SR); c = hp(noise(0.02), 2000) * env(0.02, .001, .004) * rng.uniform(.3, 1)
        x[o:o + len(c)] += c
    return x * np.minimum(1, tt(d) / 0.3) * np.clip((d - tt(d)) / 0.6, 0, 1)
SFX = dict(buzz=s_buzz, fire=s_fire, twang=s_twang, whiz=s_whiz, thunk=s_thunk, stretch=s_stretch, squeeze=s_squeeze, bell=s_bell, rain=s_rain, rumble=s_rumble,
           squelch=s_squelch, volley=s_volley, clatter=s_clatter,
march=s_march, oars=s_oars, crack=s_crack, swish=s_swish, ratchetrun=s_ratchetrun, knock=s_knock, slide=s_slide,
           footsteps=s_footsteps, ropewhip=s_ropewhip, sinking=s_sinking, swordclash=s_swordclash,
           roar=s_roar, roarlong=s_roarlong, ignite=s_ignite, hiss=s_hiss, slosh=s_slosh, paper=s_paper, horn=s_horn,
           clank=s_clank, pumpstroke=s_pumpstroke, splash=s_splash, pour=s_pour, waves=s_waves, dribble=s_dribble, puff=s_puff,
           thud=s_thud, pop=s_pop, tick=s_tick, stamp=s_stamp, whoosh=s_whoosh, whooshlow=lambda: s_whoosh(d=0.9, lo=True),
           hit=s_hit, clink=s_clink, clack=s_clack, cloth=s_cloth, creak=s_creak, ratchet=s_ratchet, riser=s_riser,
           shimmer=s_shimmer, chime=s_chime, scrape=s_scrape, rubble=s_rubble)

sfx = np.zeros((N, 2))
for i, (t0, name, g) in enumerate(CU['cues']):
    x = SFX[name](); x = x / (np.max(np.abs(x)) + 1e-9) * g
    pan = 0.5 + 0.18 * math.sin(i * 1.7)
    s = int(t0 * SR); e = min(N, s + len(x))
    sfx[s:e, 0] += x[:e - s] * (1 - pan) * 1.4; sfx[s:e, 1] += x[:e - s] * pan * 1.4


# ---------------- music bed: D dorian, low drums for the battle beats ----------------
BPM = 92; BEAT = 60 / BPM
mus = np.zeros((N, 2))
def add(x, t0, g=1.0, pan=0.5):
    s = int(t0 * SR); e = min(N, s + len(x))
    if e <= s: return
    mus[s:e, 0] += x[:e - s] * g * (1 - pan); mus[s:e, 1] += x[:e - s] * g * pan
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def pad(notes, d, g=0.12):
    t = tt(d); x = np.zeros_like(t)
    for m in notes:
        for det in (-0.08, 0.08): x += signal.sawtooth(2 * np.pi * hz(m + det) * t) * 0.5
    x = lp(x, 900); a = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
    return x * a * g / len(notes)
def pluck(m, d=0.9, g=0.25):
    n = int(SR / hz(m)); buf = rng.uniform(-1, 1, n); out = np.zeros(int(d * SR))
    for i in range(len(out)):
        out[i] = buf[i % n]; buf[i % n] = 0.996 * 0.5 * (buf[i % n] + buf[(i + 1) % n])
    return lp(out, 3000) * g
def drum(g=0.6):
    d = 0.5; return (sweep(110, 42, d) * env(d, .002, .16) + lp(noise(d), 200) * env(d, .001, .04) * .5) * g
def taiko(g=0.8):
    d = 0.9; return (sweep(70, 34, d) * env(d, .003, .3) + lp(noise(d), 500) * env(d, .002, .06) * .6) * g
def hat(): d = 0.05; return hp(noise(d), 7000) * env(d, .001, .012) * .12
def section_pad(t0, t1, chords, bars=1, g=0.12):
    t = t0; i = 0
    while t < t1:
        d = min(bars * 4 * BEAT, t1 - t)
        if d > 0.2: add(pad(chords[i % len(chords)], d + 0.3, g), t, 1.0, 0.5)
        t += bars * 4 * BEAT; i += 1
DM = [(38, 45, 50, 53), (36, 43, 48, 52), (34, 41, 46, 50), (36, 43, 48, 52)]
PL = {m: pluck(m) for m in (57, 60, 62, 64, 65, 67, 69, 72)}
# modern yard: light plucks only
for i, b in enumerate(np.arange(0.1, T['s4'] - 0.2, BEAT / 2)):
    m = (69, 72, 76 - 4, 72, 69, 65)[i % 6]
    if m in PL: add(PL[m], b, 0.55, 0.4 + 0.2 * (i % 2))
# Rome: modal pad and pulse
section_pad(T['s4'], T['s12'], DM, 1, 0.10)
for b in np.arange(T['s5'], T['s12'] - 0.1, BEAT): add(drum(0.3), b)
for i, b in enumerate(np.arange(T['s6'], T['s11'], BEAT / 2)): add(hat(), b, 1, 0.4)
add(taiko(1.1), T['release']); add(taiko(1.2), T['strike'])
# Avaricum: low drums, darker
section_pad(T['s12'], T['s16'], [(38, 45, 50), (34, 41, 46)], 1, 0.12)
for b in np.arange(T['s13'], T['s16'] - 0.2, BEAT / 2): add(drum(0.4 if int(round((b - T['s13']) / (BEAT / 2))) % 2 == 0 else 0.2), b)
add(taiko(1.0), T['hit1']); add(taiko(1.0), T['hit2'])
# Britain: sparse
section_pad(T['s16'], T['s19'], [(38, 45, 50, 53), (36, 43, 48, 52)], 1, 0.09)
for b in np.arange(T['s17'], T['s19'] - 0.2, BEAT): add(drum(0.22), b)
add(taiko(1.0), T['metres'])
# the weak point and the loop
section_pad(T['s19'], DUR, [(38, 45, 50, 53), (34, 41, 46, 50), (36, 43, 48, 52), (38, 45, 50, 53, 57)], 1, 0.10)
for b in np.arange(T['s22'], DUR - 0.6, BEAT): add(drum(0.3), b)
add(taiko(0.9), T['nothing']); add(taiko(1.2), T['snap'])
fo = np.clip((DUR - np.arange(N) / SR) / 1.0, 0, 1)
mus *= fo[:, None]
vo, sr = sf.read('vo_tight.wav'); assert sr == SR
vo = hp(vo, 80)
speech = np.abs(vo) > 10 ** (-40 / 20)
rms = np.sqrt(np.mean(vo[np.convolve(speech, np.ones(2400), 'same') > 0] ** 2))
vo = vo * (10 ** (-20 / 20) / rms)
V = np.zeros(N); V[:len(vo)] = vo
e = lp(lp(np.abs(V), 8), 4); e = e / (np.max(e) + 1e-9)
duck = 1 - 0.55 * np.clip(e * 4, 0, 1)
mix = V[:, None] * 1.0 + mus * 0.42 * duck[:, None] + sfx * 0.5
mix += rng.standard_normal((N, 2)) * 10 ** (-72 / 20)
mix = mix[:int(DUR * SR)]
mix = mix * (0.9 / max(0.9, np.max(np.abs(mix))))
sf.write('mix_raw.wav', mix, SR, subtype='PCM_24')
print('mix written', mix.shape, 'peak', np.max(np.abs(mix)))

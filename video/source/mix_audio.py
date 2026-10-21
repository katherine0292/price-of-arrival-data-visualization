"""Mix narration + original synthesized music + sound effects.

Sound-effect times mirror the animation cues in story.template.html.
Writes build/mix.wav (44.1 kHz stereo) and build/music_sfx.wav (no voice).
"""
import json, os, subprocess
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
TL = json.load(open(os.path.join(B, "timeline.json")))
SR = 44100
TOTAL = TL["total"]
N = int((TOTAL + 0.5) * SR)
rng = np.random.default_rng(7)

S = lambda g: TL["segs"][g]["s"]
E = lambda g: TL["segs"][g]["e"]
SC = lambda s: TL["scenes"][s]

def buf(): return np.zeros((N, 2), dtype=np.float64)

def add(track, t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0: return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    j0 = max(0, -i); i = max(0, i)
    n = min(len(sig) - j0, N - i)
    track[i:i + n] += sig[j0:j0 + n] * gain

def env(n, a, d_tau, sr=SR):
    t = np.arange(n) / sr
    e = np.exp(-t / d_tau)
    na = max(1, int(a * sr))
    e[:na] *= np.linspace(0, 1, na)
    return e

def lp(x, cutoff):  # one-pole low-pass
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    # vectorised via cumulative filter in blocks would be faster; signals here are short
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y

def fft_band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    # soft edges
    m = np.convolve(m, np.hanning(41) / np.hanning(41).sum(), mode="same")
    return np.fft.irfft(X * m, len(x))

# ------------------------------------------------------------------ SFX
def s_click():
    n = int(0.012 * SR)
    x = rng.standard_normal(n) * env(n, 0.0005, 0.0025)
    x = fft_band(np.pad(x, (0, 200)), 1500, 7000)
    return x * 0.6

def s_pop(f=760):
    n = int(0.12 * SR); t = np.arange(n) / SR
    fr = f * (1 + 0.6 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(n, 0.002, 0.035) * 0.5

def s_tick(f=1800):
    n = int(0.05 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * env(n, 0.001, 0.01) * 0.35

def s_ding(f=1318.5):
    n = int(1.2 * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / 0.15)
         + 0.25 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t / 0.08))
    return x * env(n, 0.002, 0.35) * 0.32

def s_whoosh(dur=0.7, lo=300, hi=3500):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = fft_band(x, lo, hi)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return x / (np.abs(x).max() + 1e-9) * shape * 0.35

def s_stamp():
    n = int(0.45 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (55 + 90 * np.exp(-t / 0.03)) * t) * env(n, 0.001, 0.09)
    m = int(0.05 * SR)
    noise = np.zeros(n); noise[:m] = fft_band(rng.standard_normal(m), 200, 2500) * env(m, 0.0005, 0.012)
    return (body * 0.9 + noise * 1.6) * 0.55

def s_type():
    n = int(0.03 * SR)
    x = fft_band(rng.standard_normal(n), 2000, 6000) * env(n, 0.0005, 0.004)
    return x * 0.5

def s_chime_up(base=523.25, steps=(0, 4, 7, 12, 16), gap=0.07):
    out = np.zeros(int((gap * len(steps) + 1.4) * SR))
    for k, st in enumerate(steps):
        d = s_ding(base * 2 ** (st / 12)) * 0.6
        i = int(k * gap * SR); out[i:i + len(d)] += d[:len(out) - i]
    return out

def s_plane(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = fft_band(rng.standard_normal(n), 120, 1800)
    hum = 0.3 * np.sin(2 * np.pi * (110 + 25 * t / dur) * t)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return (x / (np.abs(x).max() + 1e-9) * 0.8 + hum) * shape * 0.22

def s_scan(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 220 + 440 * (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12 + fft_band(rng.standard_normal(n), 2000, 5000) * 0.05
    shape = np.minimum(1, t / 0.2) * np.minimum(1, (dur - t) / 0.3)
    return x * shape

sfx = buf()

def flap_burst(t0, t1, rate=34, gain=0.35):
    t = t0
    while t < t1:
        add(sfx, t, s_click(), gain * (0.6 + 0.4 * rng.random()), pan=rng.uniform(-.5, .5))
        t += 1 / rate * (0.6 + 0.8 * rng.random())

# opening
flap_burst(0.35, 1.75, gain=0.45)
flap_burst(0.8, 2.2, gain=0.40)
for i in range(6): add(sfx, S("o1") + i * 0.42, s_pop(520 + 60 * i), 0.35, pan=[-.6, .6, -.7, .7, -.4, .4][i])
flap_burst(S("o4") + 0.05, S("o4") + 1.25, gain=0.42)
add(sfx, S("o5") - 0.1, s_whoosh(0.9, 200, 2500), 0.6)
add(sfx, S("o5") + 0.15, s_chime_up(), 0.55)
# mei
add(sfx, S("m1") - 0.3, s_whoosh(0.8), 0.6, pan=-0.3)
add(sfx, E("m2") - 0.2, s_stamp(), 0.9, pan=-0.2)
for g in ("m4", "m5", "m6", "m7"): add(sfx, S(g) - 0.05, s_pop(640), 0.45, pan=0.4)
t = S("m9") + 0.6
while t < S("m9") + 2.2:
    add(sfx, t, s_tick(2200), 0.35, pan=0.3); t += 0.05
add(sfx, S("m9") + 2.2, s_ding(1568), 0.7, pan=0.3)
for i in range(12): add(sfx, S("m10") + 0.3 + i * 0.1, s_tick(900), 0.4, pan=0.3)
# noise
for g, p in (("n2", -.5), ("n3", .2), ("n4", -.5)): add(sfx, S(g) - 0.05, s_pop(700), 0.5, pan=p)
add(sfx, S("n6") - 0.15, s_whoosh(0.8), 0.6)
add(sfx, S("n6") + 1.4, s_whoosh(1.0, 400, 4000), 0.4, pan=0.3)
for i in range(4):
    t0 = S("n7") + 0.3 + i * 0.75
    for k in range(10): add(sfx, t0 + k * 0.065, s_type(), 0.35)
# data
for i in range(5): add(sfx, S("d1") + 0.1 + i * 0.2, s_whoosh(0.35, 800, 5000), 0.4, pan=-0.6 + i * 0.3)
add(sfx, S("d3") + 1.8, s_whoosh(1.0, 200, 2000), 0.45)
add(sfx, S("d4") + 1.0, s_ding(1046.5), 0.6, pan=-0.6)
# act intros
for sid, intro in (("act1", "a1"), ("act2a", "b1"), ("act3a", "c1"), ("act4", "e1")):
    s0 = SC(sid)["s"]
    flap_burst(s0 + 0.15, s0 + 1.05, gain=0.38)
    add(sfx, E(intro) + 0.1, s_whoosh(0.8, 250, 3000), 0.5)
# act1
add(sfx, S("a4") - 0.1, s_plane(1.4), 0.6, pan=-0.6)
add(sfx, S("a5") + 0.1, s_pop(600), 0.55, pan=0.6)
add(sfx, S("a6") + 0.1, s_pop(480), 0.55, pan=0.6)
add(sfx, S("a7") + 0.1, s_ding(1174.7), 0.55, pan=0.5)
# act2a
add(sfx, S("b3") - 0.1, s_whoosh(1.2, 150, 1800), 0.5, pan=-0.4)
add(sfx, S("b3") + 1.7, s_ding(1318.5), 0.5, pan=0.3)
add(sfx, S("b4") + 1.9, s_ding(1568), 0.5, pan=0.3)
# act2b
add(sfx, SC("act2b")["s"] + 0.2, s_chime_up(659.3, (0, 3, 7, 10, 14, 17), 0.09), 0.35)
add(sfx, S("b6") + 0.1, s_pop(800), 0.4)
add(sfx, S("b7") + 0.1, s_pop(800), 0.4)
add(sfx, S("b8") + 0.35, s_stamp(), 0.9)
# act3a
add(sfx, S("c2") + 0.1, s_scan(2.8), 0.6, pan=-0.4)
for g in ("c3", "c4", "c5"): add(sfx, S(g) + 0.12 + 0.2, s_stamp(), 1.0, pan=0.4)
add(sfx, S("c6") + 0.1, s_pop(420), 0.45, pan=0.4)
# act3b
add(sfx, S("c8") + 1.4, s_pop(700), 0.55, pan=0.4)
add(sfx, S("c9") + 0.5, s_pop(820), 0.55, pan=0.4)
# act4
add(sfx, S("e2") + 2.4, s_pop(640), 0.5, pan=0.3)
add(sfx, S("e3") + 1.2, s_pop(760), 0.5, pan=0.3)
add(sfx, S("e5") - 0.1, s_whoosh(0.6, 300, 2500), 0.5, pan=-0.2)
add(sfx, S("e6") + 1.2, s_ding(1318.5), 0.5, pan=-0.6)
# aha
add(sfx, S("h1"), s_chime_up(783.99, (0, 4, 7, 11, 14, 19), 0.06), 0.55)
for i in range(4): add(sfx, S("h1") + 0.35 + i * 0.28, s_whoosh(0.5, 400, 4000), 0.35, pan=[-.7, .7, -.7, .7][i])
add(sfx, S("h3") + 0.1, s_whoosh(1.1, 200, 2500), 0.5)
add(sfx, S("h4") - 0.05, s_chime_up(523.25, (0, 7, 12, 16, 19, 24), 0.05), 0.6)
# plan
for g in ("p2", "p3", "p4", "p5"):
    add(sfx, S(g) - 0.1, s_whoosh(0.35, 800, 5000), 0.3)
    add(sfx, S(g) + 0.5, s_ding(1760), 0.35)
for i in range(3): add(sfx, S("p6") + 1.4 + i * 0.75, s_pop(560), 0.45, pan=0.4)
# land
land = SC("land")
add(sfx, land["s"] + 0.2, s_plane(max(3, S("l2") + 1.2 - land["s"])), 0.9, pan=0.0)
add(sfx, S("l3") - 0.05, s_chime_up(523.25, (0, 4, 7, 12), 0.09), 0.55)

# ------------------------------------------------------------------ MUSIC
BPM = 84; beat = 60 / BPM; bar = 4 * beat
mus = buf()
A4 = 440.0
nf = lambda m: A4 * 2 ** ((m - 69) / 12)
# Cmaj7 – Am7 – Fmaj7 – G6, voiced around middle C
CHORDS = [([48], [60, 64, 67, 71]), ([45], [60, 64, 67, 69]), ([41], [60, 65, 69, 72]), ([43], [59, 62, 67, 64])]

def pad_note(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for h, a in ((1, 1), (2, .35), (3, .12), (4, .05)):
        for det in (-0.12, 0.12):
            x += a * np.sin(2 * np.pi * f * h * (1 + det / 100) * t + rng.random() * 6.28)
    shape = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.8)
    return x * shape * 0.05

def keys_note(f, dur=0.9):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.2) + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.1)
    return x * env(n, 0.004, 0.32) * 0.09

def bass_note(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return x * env(n, 0.01, 0.6) * np.minimum(1, (dur - t) / 0.05).clip(0) * 0.16

def kick():
    n = int(0.3 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-t / 0.035)) / SR) * env(n, 0.001, 0.11) * 0.42

def snare():
    n = int(0.25 * SR)
    return fft_band(rng.standard_normal(n), 900, 5000) * env(n, 0.002, 0.06) * 0.1

def hat():
    n = int(0.06 * SR)
    return fft_band(rng.standard_normal(n), 6000, 11000) * env(n, 0.001, 0.015) * 0.07

KICK, SNARE = kick(), snare()
HATS = [hat() for _ in range(8)]
start_beat = SC("mei")["s"] - 2 * beat  # drums enter just before Mei
music_end = SC("credits")["e"]
arp_pat = [0, 1, 2, 3, 2, 1, 3, 2]
t = 0.0; b = 0
while t < music_end:
    roots, tones = CHORDS[b % 4]
    for m in tones: add(mus, t, pad_note(nf(m), bar + 0.8), 1.0, pan=rng.uniform(-.4, .4))
    if t > 1.2:
        for r in roots: add(mus, t, bass_note(nf(r), beat * 1.9)); add(mus, t + 2 * beat, bass_note(nf(r), beat * 1.9))
    if t >= start_beat:
        for k in range(8):
            if (b + k) % 3 == 2 and k % 2: continue  # leave little gaps so it breathes
            add(mus, t + k * beat / 2, keys_note(nf(tones[arp_pat[k]] + 12)), 0.9, pan=0.35 if k % 2 else -0.35)
        for k in range(4):
            if k in (0, 2): add(mus, t + k * beat, KICK, 1.0)
            if k in (1, 3): add(mus, t + k * beat, SNARE, 1.0)
        for k in range(8): add(mus, t + k * beat / 2 + (0.02 if k % 2 else 0), HATS[k], 1.0, pan=0.25)
    t += bar; b += 1

# master envelope for music: soft intro, lift at aha, fade out over credits
tt = np.arange(N) / SR
menv = np.clip(tt / 2.5, 0, 1) * 0.75 + 0.25 * np.clip((tt - SC("mei")["s"]) / 2, 0, 1)
aha = SC("aha")
menv *= 1 + 0.25 * np.clip((tt - aha["s"]) / 1.5, 0, 1) * np.clip((aha["e"] - tt) / 1.0, 0, 1)
cr = SC("credits")
menv *= np.clip((cr["e"] - 0.3 - tt) / 4.0, 0, 1)
mus *= menv[:, None]

# ------------------------------------------------------------------ VOICE
vo24 = np.zeros(int((TOTAL + 0.5) * 24000))
for gid in TL["order"]:
    a, sr = sf.read(os.path.join(B, "vo", gid + ".wav"), dtype="float64")
    i = int(TL["segs"][gid]["s"] * 24000)
    vo24[i:i + len(a)] += a[:len(vo24) - i]
rms = np.sqrt(np.mean(vo24[np.abs(vo24) > 0.01] ** 2))
vo24 *= 0.12 / rms
sf.write(os.path.join(B, "vo24.wav"), vo24.astype(np.float32), 24000)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(B, "vo24.wav"), "-ar", str(SR), "-af", "aresample=resampler=soxr", os.path.join(B, "vo44.wav")], check=True)
vo, _ = sf.read(os.path.join(B, "vo44.wav"), dtype="float64")
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]

# duck music under voice
blk = int(0.01 * SR)
nb = N // blk + 1
a = np.pad(np.abs(vo), (0, nb * blk - N)).reshape(nb, blk).mean(1)
from numpy.lib.stride_tricks import sliding_window_view
k = 35  # hold ~350 ms so the music doesn't pump between words
held = sliding_window_view(np.pad(a, (k // 2, k - k // 2 - 1), mode="edge"), k).max(1)
held = np.convolve(held, np.ones(8) / 8, mode="same")
envm = np.repeat(held, blk)[:N]
duck = 1 - 0.62 * np.clip(envm / 0.03, 0, 1)
mus *= duck[:, None]

voice = np.stack([vo, vo], 1)
mix = voice * 1.0 + mus * 0.42 + sfx * 0.6
bed = mus * 0.42 + sfx * 0.6
peak = np.abs(mix).max()
print(f"peak before limit {peak:.3f}")
lim = lambda x: np.tanh(x * 1.1) / np.tanh(1.1)
sf.write(os.path.join(B, "mix_raw.wav"), lim(mix / max(1.0, peak / 0.95)).astype(np.float32), SR)
sf.write(os.path.join(B, "music_sfx_raw.wav"), lim(bed / max(1.0, np.abs(bed).max() / 0.95)).astype(np.float32), SR)
for src, dst in (("mix_raw.wav", "mix.wav"), ("music_sfx_raw.wav", "music_sfx.wav")):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(B, src), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), os.path.join(B, dst)], check=True)
print("wrote mix.wav / music_sfx.wav", TOTAL)

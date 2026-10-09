"""Synthesises the game's sound effects into audio/*.wav.

They are simple placeholders: replace any file with your own sound of the
same name (sfxr.me, kenney.nl and freesound.org are good sources).

Run from the project root:  python3 tools/make_sfx.py
"""
import math
import random
import struct
import wave

RATE = 22050
rnd = random.Random(5)


def write(name, samples):
    with wave.open("audio/%s.wav" % name, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32000)) for s in samples))


def env(i, n, attack=.01, release=.6):
    t = i / n
    if t < attack:
        return t / attack
    return max(0.0, 1 - (t - attack) / (1 - attack)) ** (1 / max(release, .01))


def noise_lp(n, k):
    """Low-passed white noise: smaller k = darker."""
    out, y = [], 0.0
    for _ in range(n):
        y += k * (rnd.uniform(-1, 1) - y)
        out.append(y)
    return out


def step():
    n = int(RATE * .05)
    nz = noise_lp(n, .35)
    return [nz[i] * 2.2 * (1 - i / n) ** 3 for i in range(n)]


def rumble():
    n = int(RATE * 1.1)
    nz = noise_lp(n, .02)
    return [nz[i] * 9 * env(i, n, .15, .7) * (0.7 + 0.3 * math.sin(i / RATE * 2 * math.pi * 7)) for i in range(n)]


def growl():
    n = int(RATE * .7)
    out, ph = [], 0.0
    for i in range(n):
        f = 70 + 18 * math.sin(i / RATE * 2 * math.pi * 9) + rnd.uniform(-6, 6)
        ph += f / RATE
        saw = 2 * (ph % 1) - 1
        out.append((saw * .55 + rnd.uniform(-.25, .25)) * env(i, n, .2, .5))
    return out


def blip(freqs, dur=.08, kind="square", vol=.4):
    out = []
    for f in freqs:
        n = int(RATE * dur)
        for i in range(n):
            ph = i / RATE * f
            s = (1 if ph % 1 < .5 else -1) if kind == "square" else math.sin(2 * math.pi * ph)
            out.append(s * vol * (1 - i / n))
    return out


def caught():
    n = int(RATE * .8)
    out, ph = [], 0.0
    for i in range(n):
        f = 420 * (1 - i / n) + 60
        ph += f / RATE
        out.append((2 * (ph % 1) - 1) * .5 * env(i, n, .01, .8) + rnd.uniform(-.1, .1) * (1 - i / n))
    return out


def lights_off():
    n = int(RATE * .45)
    out = []
    for i in range(n):
        t = i / RATE
        out.append((math.sin(2 * math.pi * 55 * t) * .8 + rnd.uniform(-.3, .3) * (i < 600)) * (1 - i / n) ** 2)
    return out


def lights_on():
    n = int(RATE * .35)
    out = []
    for i in range(n):
        t = i / RATE
        hum = math.sin(2 * math.pi * 120 * t) * .25 + math.sin(2 * math.pi * 240 * t) * .1
        click = rnd.uniform(-1, 1) * .8 if i < 300 else 0
        out.append((hum + click) * env(i, n, .02, .5))
    return out


def tick():
    n = int(RATE * .03)
    return [rnd.uniform(-1, 1) * .6 * (1 - i / n) ** 2 + math.sin(2 * math.pi * 1800 * i / RATE) * .3 * (1 - i / n) for i in range(n)]


def gate():
    n = int(RATE * .9)
    out = []
    for i in range(n):
        t = i / RATE
        ring = sum(math.sin(2 * math.pi * f * t) * a for f, a in ((220, .4), (331, .25), (587, .15)))
        out.append((ring + (rnd.uniform(-1, 1) * .7 if i < 900 else 0)) * (1 - i / n) ** 2.5)
    return out


def heartbeat():
    out = []
    for gap in (0, .16):
        out += [0.0] * int(RATE * gap)
        n = int(RATE * .12)
        out += [math.sin(2 * math.pi * 50 * i / RATE) * .9 * (1 - i / n) ** 2 for i in range(n)]
    return out


write("step", step())
write("rumble", rumble())
write("growl", growl())
write("pickup", blip([880, 1320], .07))
write("caught", caught())
write("lights_off", lights_off())
write("lights_on", lights_on())
write("tick", tick())
write("gate", gate())
write("heartbeat", heartbeat())
write("level_clear", blip([523, 659, 784, 1046], .11, "square", .3))
print("wrote 11 sounds to audio/")

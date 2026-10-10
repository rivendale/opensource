#!/usr/bin/env python3
"""sfxr-lite: the small sound-effect synthesizer the game-sfx cases hand to the skill as `inputs/bin/sfx`. Standard library only, deterministic.

    sfx render PARAMS.sfx OUT.wav [--rate 48000] [--stereo]

A .sfx file is one line of `key=value` pairs: wave=square|saw|sine|noise  freq=Hz  slide=Hz-per-second  dur=seconds  vol=linear gain (1 = a full-scale square wave; low-passed or noisy sounds need more than 1 to be as loud; samples beyond full scale are clipped when written)  lp=Hz (one-pole low-pass, 0 = off)
tail=seconds of silence added at the end  seed=integer (noise).  The sound fades out linearly over `dur`. Output: 16-bit PCM WAV, mono unless --stereo.
"""
import math, random, struct, sys, wave

DEFAULTS = dict(wave="square", freq=440.0, slide=0.0, dur=0.25, vol=0.5, lp=0.0, tail=0.0, seed=1)


def parse(text):
    p = dict(DEFAULTS)
    for kv in text.split():
        k, v = kv.split("=", 1)
        if k not in DEFAULTS:
            raise SystemExit(f"unknown key {k}")
        p[k] = v if k == "wave" else (int(v) if k == "seed" else float(v))
    return p


def samples(p, rate=48000):
    r = random.Random(int(p["seed"]))
    n = int(p["dur"] * rate)
    out, ph, y = [], 0.0, 0.0
    a = 1.0 if p["lp"] <= 0 else 1 - math.exp(-2 * math.pi * p["lp"] / rate)
    for i in range(n):
        t = i / rate
        f = max(1.0, p["freq"] + p["slide"] * t)
        ph = (ph + f / rate) % 1.0
        w = p["wave"]
        x = (1.0 if ph < 0.5 else -1.0) if w == "square" else (2 * ph - 1) if w == "saw" else math.sin(2 * math.pi * ph) if w == "sine" else r.uniform(-1, 1)
        y += a * (x - y)
        out.append(y * p["vol"] * (1 - i / n))
    out += [0.0] * int(p["tail"] * rate)
    return out


def write_wav(path, s, rate=48000, stereo=False):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h" if not stereo else "<hh", *([max(-32768, min(32767, int(round(v * 32767))))] * (2 if stereo else 1))) for v in s))


def main(argv):
    if len(argv) < 4 or argv[1] != "render":
        print(__doc__)
        return 2
    rate = int(argv[argv.index("--rate") + 1]) if "--rate" in argv else 48000
    text = open(argv[2]).read()
    write_wav(argv[3], samples(parse(text), rate), rate, "--stereo" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

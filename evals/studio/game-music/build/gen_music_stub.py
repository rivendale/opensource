#!/usr/bin/env python3
"""gen-music: stands in for a local text-to-music model in the game-music cases.

    gen-music --prompt TEXT --out FILE.wav [--model NAME] [--seconds N] [--seed N]

Models are described by the cards in inputs/models/. It writes a mono 48 kHz WAV: a slow arpeggio whose notes depend on the seed. Read the card of the model
you use. The default model is the one named in inputs/models/README.md.
"""
import argparse, math, os, struct, sys, wave

DEFAULT = "@DEFAULT@"
ap = argparse.ArgumentParser()
ap.add_argument("--prompt", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--model", default=DEFAULT)
ap.add_argument("--seconds", type=float, default=16.0)
ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(here, "..", "models", a.model + ".md")):
    sys.exit("unknown model " + a.model)
rate = 48000
n = int(a.seconds * rate)
freqs = [220.0 * 2 ** (((a.seed * 3 + k * 4) % 12) / 12) for k in range(4)]
out = []
for i in range(n):
    t = i / rate
    k = int(t / 0.5) % 4
    tt = t % 0.5
    out.append(0.3 * math.exp(-tt * 4) * math.sin(2 * math.pi * freqs[k] * t))
with wave.open(a.out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in out))
print("wrote", a.out, "with", a.model)

#!/usr/bin/env python3
"""mus: the small score renderer the game-music cases hand to the skill as `inputs/bin/mus`. Standard library only, deterministic.

    mus render SCORE.score OUT.wav [--rate 48000]

A .score file: a header line `tempo=BPM beats=N key=NAME vol=gain`, then one note per line: `START DURATION PITCH` with START and DURATION in beats and PITCH like
A3, C#4, Bb2 (or `R` for a rest). Every note is a plucked tone (sine plus a third harmonic) with a 5 ms attack and release, so a note never starts or ends with a click.
The file lasts exactly N beats, so a loop of it repeats on the beat when no note rings past the end. `vol` is a linear gain (1 = a full-scale sine); samples beyond
full scale are clipped when written. 16-bit mono WAV.
"""
import math, struct, sys, wave

SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(p):
    n = SEMI[p[0]]
    i = 1
    while i < len(p) and p[i] in "#b":
        n += 1 if p[i] == "#" else -1
        i += 1
    return 12 * (int(p[i:]) + 1) + n


def parse(text):
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    head = dict(kv.split("=", 1) for kv in lines[0].split())
    notes = []
    for l in lines[1:]:
        s, d, p = l.split()
        if p != "R":
            notes.append((float(s), float(d), midi(p)))
    return {"tempo": float(head["tempo"]), "beats": float(head["beats"]), "key": head.get("key", ""), "vol": float(head.get("vol", 0.3))}, notes


def samples(text, rate=48000):
    h, notes = parse(text)
    spb = 60.0 / h["tempo"]
    n = int(round(h["beats"] * spb * rate))
    out = [0.0] * n
    for s, d, m in notes:
        f = 440.0 * 2 ** ((m - 69) / 12)
        a = int(s * spb * rate)
        L = int(d * spb * rate)
        att = int(0.005 * rate)
        for i in range(L):
            j = a + i
            if j >= n:
                break
            t = i / rate
            env = math.exp(-t * 5.0) * min(1.0, i / att) * min(1.0, (L - 1 - i) / att)
            out[j] += env * (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * 3 * f * t)) * h["vol"]
    return out


def write_wav(path, s, rate=48000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", max(-32768, min(32767, int(round(v * 32767))))) for v in s))


def main(argv):
    if len(argv) < 4 or argv[1] != "render":
        print(__doc__)
        return 2
    rate = int(argv[argv.index("--rate") + 1]) if "--rate" in argv else 48000
    write_wav(argv[3], samples(open(argv[2]).read(), rate), rate)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

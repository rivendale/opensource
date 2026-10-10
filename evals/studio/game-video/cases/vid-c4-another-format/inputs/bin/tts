#!/usr/bin/env python3
"""tts: the narration voice the game-video cases hand to the skill as `inputs/bin/tts`. Standard library only, deterministic.

    tts SCRIPT.txt OUT.wav

Reads the words of SCRIPT.txt (case and punctuation ignored) and speaks each as a short two-tone sound taken from the word list in `inputs/tts/lexicon.txt`
(0.3 s per word, 0.1 s between words, 48 kHz mono 16-bit WAV). A word that is not in the list is an error: the list is this voice's whole vocabulary.
"""
import math, os, re, struct, sys, wave

RATE = 48000


def tones(i):
    return 400 + 60 * (i % 8), 1400 + 150 * (i // 8)


def render(words, lexicon):
    out = [0.0] * int(0.2 * RATE)
    for w in words:
        if w not in lexicon:
            raise SystemExit(f"tts: no voice for the word {w!r}")
        f1, f2 = tones(lexicon.index(w))
        n = int(0.3 * RATE)
        fade = int(0.01 * RATE)
        for k in range(n):
            e = min(1.0, k / fade, (n - 1 - k) / fade)
            out.append(e * 0.3 * (math.sin(2 * math.pi * f1 * k / RATE) + math.sin(2 * math.pi * f2 * k / RATE)))
        out += [0.0] * int(0.1 * RATE)
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    here = os.path.dirname(os.path.abspath(__file__))
    lexicon = [l.strip() for l in open(os.path.join(here, "..", "tts", "lexicon.txt")) if l.strip()]
    words = re.findall(r"[a-z']+", open(argv[1]).read().lower())
    s = render(words, lexicon)
    with wave.open(argv[2], "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in s))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

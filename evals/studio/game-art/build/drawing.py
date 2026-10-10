"""Procedural pixel art for the game-art case inputs. Everything is drawn from rectangles so the cases are exactly reproducible."""
import numpy as np
from PIL import Image

PALETTE = ["1a1c2c", "5d275d", "b13e53", "ef7d57", "ffcd75", "a7f070", "38b764", "41a6f6"]
DARK, PURPLE, RED, ORANGE, YELLOW, LIME, GREEN, BLUE = PALETTE
PINK, MAGENTA, WHITE, SHINE = "ff77a8", "ff00ff", "ffffff", "f0f0f0"


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def canvas(w, h, fill=None):
    a = np.zeros((h, w, 4), np.uint8)
    if fill:
        a[..., :3] = rgb(fill)
        a[..., 3] = 255
    return a


def rect(a, x0, y0, x1, y1, color):
    """Fill [x0, x1) x [y0, y1) with an opaque color."""
    a[y0:y1, x0:x1, :3] = rgb(color)
    a[y0:y1, x0:x1, 3] = 255


def mask_of(w, h, boxes):
    m = np.zeros((h, w, 4), np.uint8)
    m[..., 3] = 255
    for x0, y0, x1, y1 in boxes:
        m[y0:y1, x0:x1, :3] = 255
    return m


def save(a, path):
    import pathlib
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a, "RGBA").save(path, optimize=False)


HAT = [(11, 2, 21, 6), (9, 6, 23, 8)]
HEAD = (12, 7, 20, 12)
CLOAK = (10, 11, 22, 26)
BOOTS = [(11, 26, 15, 30), (17, 26, 21, 30)]
SCARF = (12, 12, 24, 15)


def hero(hat=BLUE, cloak=RED, boots=DARK, scarf=None, layers=False):
    """32x32 hero. With layers=True returns three layers (body, cloak, hat) that composite to the same image."""
    def draw(parts):
        a = canvas(32, 32)
        for box, col in parts:
            rect(a, *box, col)
        return a
    body = [(HEAD, YELLOW)] + [(b, boots) for b in BOOTS]
    cl = [(CLOAK, cloak)]
    ht = [(b, hat) for b in HAT]
    sc = [(SCARF, scarf)] if scarf else []
    if layers:
        return draw(body), draw(cl), draw(ht)
    return draw(body + cl + sc + ht)


def hero_on_matte(matte=MAGENTA):
    a = canvas(32, 32, matte)
    h = hero(scarf=PINK)
    m = h[..., 3] > 0
    a[m] = h[m]
    return a


def crate16():
    a = canvas(16, 16, DARK)
    rect(a, 1, 1, 15, 15, ORANGE)
    rect(a, 1, 1, 15, 3, YELLOW)
    rect(a, 1, 13, 15, 15, RED)
    rect(a, 1, 7, 15, 9, RED)
    rect(a, 7, 1, 9, 15, RED)
    rect(a, 3, 3, 5, 5, LIME)
    rect(a, 11, 11, 13, 13, BLUE)
    return a


def upscale(a, f):
    return np.repeat(np.repeat(a, f, axis=0), f, axis=1)


def numbered_frame(n, size=32):
    """Frame n: a bar of n lit pixels on the top row and a block that moves with n, so every frame is different."""
    a = canvas(size, size)
    for i in range(n):
        rect(a, 1 + i * 2, 0, 2 + i * 2, 1, PALETTE[i % 8])
    rect(a, 2 + n, 10, 8 + n, 24, PALETTE[(n + 2) % 8])
    rect(a, 4 + n, 4, 7 + n, 10, YELLOW)
    return a


def varied_frame(n):
    """Frame n on a 40x40 canvas: a figure of its own width and height, at its own offset (the feet are on different rows)."""
    ws = [8, 9, 10, 11, 12, 13, 14, 11]
    hs = [24, 22, 20, 18, 16, 15, 14, 21]
    ox = [3, 8, 14, 5, 20, 11, 6, 17]
    oy = [4, 9, 6, 12, 2, 14, 10, 7]
    i = n - 1
    a = canvas(40, 40)
    rect(a, ox[i], oy[i], ox[i] + ws[i], oy[i] + hs[i], PALETTE[(i + 1) % 8])
    rect(a, ox[i] + 1, oy[i] + 1, ox[i] + 3, oy[i] + 3, YELLOW)
    return a


ICONS = {
    "sword": lambda a: (rect(a, 14, 3, 18, 22, "dddddd"), rect(a, 9, 22, 23, 25, ORANGE), rect(a, 14, 25, 18, 29, RED), rect(a, 15, 6, 17, 10, SHINE)),
    "shield": lambda a: (rect(a, 6, 4, 26, 20, BLUE), rect(a, 10, 20, 22, 27, BLUE), rect(a, 8, 6, 14, 12, SHINE), rect(a, 14, 8, 18, 22, YELLOW)),
    "potion": lambda a: (rect(a, 12, 3, 20, 8, "8899aa"), rect(a, 8, 8, 24, 27, GREEN), rect(a, 10, 10, 14, 14, SHINE), rect(a, 11, 3, 21, 5, DARK)),
    "key": lambda a: (rect(a, 5, 6, 15, 16, YELLOW), rect(a, 8, 9, 12, 13, SHINE), rect(a, 15, 10, 28, 13, YELLOW), rect(a, 24, 13, 28, 18, YELLOW)),
}


def icon(name):
    a = canvas(32, 32)
    ICONS[name](a)
    return a


def icons_on_white():
    """A 64x64 sheet, reading order sword, shield, potion, key, on pure white. The shine pixels are f0f0f0, not white."""
    a = canvas(64, 64, WHITE)
    for k, name in enumerate(["sword", "shield", "potion", "key"]):
        ic = icon(name)
        x, y = (k % 2) * 32, (k // 2) * 32
        m = ic[..., 3] > 0
        sub = a[y:y + 32, x:x + 32]
        sub[m] = ic[m]
    return a

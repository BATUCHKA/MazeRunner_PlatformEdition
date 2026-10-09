"""Builds art/maze_tiles.png from the 0x72 DungeonTileset II frames.

The pack's own wall autotiles draw thin ridges, but this maze uses walls that
are exactly one tile thick, so we compose full-block wall tiles here instead,
using the pack's brick face, wall cap and colours.

Atlas layout (16x16 tiles, 16 columns):
  row 0  normal walls    column = mask  (1=N wall, 2=E wall, 4=W wall, 8=front face)
  row 1  shifting walls  same masks, tinted purple so players can learn them
  row 2  floors: 0-7 floor variants, 8 safe room, 9 exit stairs, 10 shift hint

Run from the project root:  python3 tools/make_tiles.py
"""
from PIL import Image

T = 16
SRC = "art/0x72/"
OUT = "art/maze_tiles.png"

DARK = (34, 34, 34, 255)
CAP = (170, 141, 122, 255)
CAP_HI = (211, 191, 169, 255)
EDGE = (24, 20, 22, 255)

PURPLE = {
    (34, 34, 34): (38, 28, 46),
    (72, 59, 58): (70, 46, 82),
    (119, 92, 85): (118, 78, 128),
    (170, 141, 122): (172, 124, 170),
    (211, 191, 169): (222, 186, 222),
    (24, 20, 22): (22, 14, 28),
}


def load(name):
    return Image.open(SRC + name + ".png").convert("RGBA")


wall_mid = load("wall_mid")
wall_top_mid = load("wall_top_mid")


def wall_tile(mask):
    n, e, w, face = mask & 1, mask & 2, mask & 4, mask & 8
    im = Image.new("RGBA", (T, T), DARK)
    px = im.load()
    top_h = 5 if face else T
    # rims on the top surface where the neighbour is open floor
    if not n:
        for x in range(T):
            px[x, 0] = CAP_HI
            px[x, 1] = CAP
    if not w:
        for y in range(top_h):
            px[0, y] = CAP_HI
            px[1, y] = CAP
    if not e:
        for y in range(top_h):
            px[T - 1, y] = CAP
            px[T - 2, y] = CAP
    if face:
        # cap strip (front edge of the top surface) then the brick face
        strip = wall_top_mid.crop((0, T - 5, T, T))
        im.alpha_composite(strip, (0, 0))
        bricks = wall_mid.crop((0, 5, T, T))
        im.paste(bricks, (0, 5))
        if not w:
            for y in range(5, T):
                px[0, y] = EDGE
        if not e:
            for y in range(5, T):
                px[T - 1, y] = EDGE
    return im


def tint(im):
    out = im.copy()
    px = out.load()
    for y in range(T):
        for x in range(T):
            r, g, b, a = px[x, y]
            if (r, g, b) in PURPLE:
                px[x, y] = PURPLE[(r, g, b)] + (a,)
            elif a:
                px[x, y] = (int(r * .9), int(g * .7), int(b * 1.05) if b * 1.05 < 255 else 255, a)
    return out


def rune(im, face):
    px = im.load()
    glow = (226, 150, 255, 255)
    cy = 2 if face else 8
    for d in (-1, 0, 1):
        px[8 + d, cy + d] = glow
        px[8 + d, cy - d] = glow
    return im


def blend(im, color, k):
    out = im.copy()
    px = out.load()
    for y in range(T):
        for x in range(T):
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * (1 - k) + color[0] * k), int(g * (1 - k) + color[1] * k), int(b * (1 - k) + color[2] * k), a)
    return out


atlas = Image.new("RGBA", (T * 16, T * 3), (0, 0, 0, 0))
for m in range(16):
    t = wall_tile(m)
    atlas.paste(t, (m * T, 0))
    atlas.paste(rune(tint(t), m & 8), (m * T, T))

for i in range(8):
    atlas.paste(load("floor_%d" % (i + 1)), (i * T, 2 * T))
safe = blend(load("floor_1"), (60, 150, 150), .28)
sp = safe.load()
for x, y in ((3, 3), (12, 3), (3, 12), (12, 12)):
    sp[x, y] = (150, 230, 220, 255)
atlas.paste(safe, (8 * T, 2 * T))
atlas.paste(load("floor_stairs"), (9 * T, 2 * T))
hint = load("floor_1")
hp = hint.load()
for x, y in ((2, 2), (13, 2), (2, 13), (13, 13), (3, 2), (12, 2), (2, 3), (13, 3)):
    hp[x, y] = (150, 96, 170, 255)
atlas.paste(hint, (10 * T, 2 * T))

atlas.save(OUT)
print("wrote", OUT, atlas.size)

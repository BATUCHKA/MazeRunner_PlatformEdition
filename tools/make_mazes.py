"""Generates the three ring mazes into levels/*.gd.

Map legend (one character per 16x16 tile):
  #     wall                     .   floor
  @     player start             X   exit gate (on the outer edge)
  s     safe room floor          h   hunter spawn
  m     map piece                o   lantern oil
  1-4   shifting wall of group 1-4, CLOSED at the start (opens when the group flips)
  5-8   shifting wall of group 1-4, OPEN at the start   (closes when the group flips)

Every combination of group states is checked so that all open floor stays
connected to the exit: a shift can change your route but never trap you.

Run from the project root:  python3 tools/make_mazes.py
"""
import itertools
import random
from collections import deque

RINGS = [
    dict(file="outer_ring", title="Outer Ring", seed=11, w=45, h=27, loops=.14, groups=2, per_group=7,
         safe_rooms=2, hunters=1, maps=0, oil=0),
    dict(file="inner_ring", title="Inner Ring", seed=23, w=49, h=29, loops=.10, groups=4, per_group=9,
         safe_rooms=2, hunters=3, maps=4, oil=0),
    dict(file="the_core", title="The Core", seed=37, w=55, h=31, loops=.08, groups=4, per_group=14,
         safe_rooms=1, hunters=6, maps=0, oil=5),
]

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def carve(w, h, rnd):
    g = [["#"] * w for _ in range(h)]
    start = (1, 1)
    g[1][1] = "."
    stack = [start]
    while stack:
        x, y = stack[-1]
        opts = [(dx, dy) for dx, dy in DIRS if 0 < x + 2 * dx < w - 1 and 0 < y + 2 * dy < h - 1 and g[y + 2 * dy][x + 2 * dx] == "#"]
        if not opts:
            stack.pop()
            continue
        dx, dy = rnd.choice(opts)
        g[y + dy][x + dx] = "."
        g[y + 2 * dy][x + 2 * dx] = "."
        stack.append((x + 2 * dx, y + 2 * dy))
    return g


def bfs(passable, src, w, h):
    dist = {src: 0}
    q = deque([src])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if 0 <= n[0] < w and 0 <= n[1] < h and n not in dist and passable(n):
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def build(cfg):
    rnd = random.Random(cfg["seed"])
    w, h = cfg["w"], cfg["h"]
    g = carve(w, h, rnd)

    # braid: knock out some walls to create loops (alternative routes)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if g[y][x] != "#":
                continue
            horiz = g[y][x - 1] == "." and g[y][x + 1] == "." and g[y - 1][x] == "#" and g[y + 1][x] == "#"
            vert = g[y - 1][x] == "." and g[y + 1][x] == "." and g[y][x - 1] == "#" and g[y][x + 1] == "#"
            if (horiz or vert) and rnd.random() < cfg["loops"]:
                g[y][x] = "."

    # centre start room
    cx, cy = (w // 2) | 1, (h // 2) | 1
    for y in range(cy - 2, cy + 3):
        for x in range(cx - 2, cx + 3):
            g[y][x] = "s"
    # open a door on each side of the start room so it's well connected
    for dx, dy in DIRS:
        x, y = cx + 3 * dx, cy + 3 * dy
        if g[y][x] == "#":
            g[y][x] = "."
    g[cy][cx] = "@"

    floor = lambda c: g[c[1]][c[0]] != "#"
    dist = bfs(floor, (cx, cy), w, h)

    # extra safe rooms (3x3), far from the centre and from each other
    rooms = [(cx, cy)]
    tries = 0
    while len(rooms) < cfg["safe_rooms"] + 1 and tries < 500:
        tries += 1
        x, y = rnd.randrange(3, w - 3) | 1, rnd.randrange(3, h - 3) | 1
        if all(abs(x - rx) + abs(y - ry) > 16 for rx, ry in rooms):
            for yy in range(y - 1, y + 2):
                for xx in range(x - 1, x + 2):
                    g[yy][xx] = "s"
            rooms.append((x, y))

    # exit: an edge tile next to floor, as far from the start as possible
    dist = bfs(floor, (cx, cy), w, h)
    best = None
    for x in range(1, w - 1):
        for y in (0, h - 1):
            inner = (x, 1 if y == 0 else h - 2)
            if inner in dist and g[inner[1]][inner[0]] == "." and (best is None or dist[inner] > best[0]):
                best = (dist[inner], x, y)
    for y in range(1, h - 1):
        for x in (0, w - 1):
            inner = (1 if x == 0 else w - 2, y)
            if inner in dist and g[inner[1]][inner[0]] == "." and (best is None or dist[inner] > best[0]):
                best = (dist[inner], x, y)
    _, ex, ey = best
    g[ey][ex] = "X"

    # shifting walls
    def near_special(x, y):
        for yy in range(y - 1, y + 2):
            for xx in range(x - 1, x + 2):
                if g[yy][xx] in "s@X":
                    return True
        return False

    cands = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if near_special(x, y):
                continue
            c = g[y][x]
            horiz = g[y][x - 1] != "#" and g[y][x + 1] != "#" and g[y - 1][x] == "#" and g[y + 1][x] == "#"
            vert = g[y - 1][x] != "#" and g[y + 1][x] != "#" and g[y][x - 1] == "#" and g[y][x + 1] == "#"
            if c == "#" and (horiz or vert):
                cands.append((x, y, "closed"))
            elif c == "." and (horiz or vert):
                cands.append((x, y, "open"))
    rnd.shuffle(cands)

    shift = {}  # (x,y) -> (group, kind)

    def passable(c, states):
        x, y = c
        if c in shift:
            grp, kind = shift[c]
            closed = (kind == "closed") != states[grp]
            return not closed
        return g[y][x] != "#"

    def valid():
        exit_c = (ex, ey)
        for combo in itertools.product((False, True), repeat=cfg["groups"]):
            states = {i + 1: combo[i] for i in range(cfg["groups"])}
            p = lambda c: passable(c, states)
            reach = bfs(p, exit_c, w, h)
            for yy in range(h):
                for xx in range(w):
                    if p((xx, yy)) and (xx, yy) not in reach:
                        return False
        return True

    counts = {i: 0 for i in range(1, cfg["groups"] + 1)}
    for x, y, kind in cands:
        open_groups = [k for k, v in counts.items() if v < cfg["per_group"]]
        if not open_groups:
            break
        # don't put two shifting cells right next to each other
        if any((x + dx, y + dy) in shift for dx, dy in DIRS):
            continue
        grp = min(open_groups, key=lambda k: counts[k])
        shift[(x, y)] = (grp, kind)
        if valid():
            counts[grp] += 1
        else:
            del shift[(x, y)]
    for (x, y), (grp, kind) in shift.items():
        g[y][x] = str(grp if kind == "closed" else grp + 4)

    # place hunters, map pieces and oil on plain floor
    dist = bfs(lambda c: g[c[1]][c[0]] not in "#1234", (cx, cy), w, h)
    plain = [c for c, d in dist.items() if g[c[1]][c[0]] == "."]

    def place(char, n, min_start, spacing, prefer_dead_ends=False):
        pool = [c for c in plain if dist[c] >= min_start]
        if prefer_dead_ends:
            dead = [c for c in pool if sum(g[c[1] + dy][c[0] + dx] == "#" for dx, dy in DIRS) == 3]
            pool = dead + [c for c in pool if c not in dead]
        else:
            rnd.shuffle(pool)
        placed = []
        for c in pool:
            if len(placed) >= n:
                break
            if g[c[1]][c[0]] != ".":
                continue
            if all(abs(c[0] - p[0]) + abs(c[1] - p[1]) >= spacing for p in placed):
                g[c[1]][c[0]] = char
                placed.append(c)
        return placed

    place("h", cfg["hunters"], 16, 9)
    if cfg["maps"]:
        rnd.shuffle(plain)
        place("m", cfg["maps"], 10, 14, prefer_dead_ends=True)
    if cfg["oil"]:
        rnd.shuffle(plain)
        place("o", cfg["oil"], 8, 12, prefer_dead_ends=True)

    return ["".join(r) for r in g], counts


for cfg in RINGS:
    rows, counts = build(cfg)
    path = "levels/%s.gd" % cfg["file"]
    with open(path, "w") as f:
        f.write("# %s - generated by tools/make_mazes.py, but safe to edit by hand.\n" % cfg["title"])
        f.write("# Legend: # wall  . floor  @ start  X exit  s safe room  h hunter  m map piece  o oil\n")
        f.write("#         1-4 shifting wall (closed at start)  5-8 shifting wall (open at start)\n")
        f.write("# If you edit shifting walls, re-check that a shift can never wall off part of the maze.\n")
        f.write("extends RefCounted\n\n")
        f.write('const MAP := """\n')
        f.write("\n".join(rows))
        f.write('\n"""\n')
    print(path, "%dx%d" % (cfg["w"], cfg["h"]), "shift cells per group:", counts)

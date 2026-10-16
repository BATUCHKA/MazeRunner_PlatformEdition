# Blackout Maze

A top-down maze escape for Godot 4.7. Every few seconds the lights die. In the dark the purple walls shift and the monsters wake. Escape four rings in one run with 3 lives: Outer Ring (easy), Inner Ring (medium), The Core (hard) and The Abyss (nightmare). The title screen lets you start at any ring; the run then carries on through the rings after it.

## Play

Open the project in Godot and press **F5**.

| Key | Action |
|---|---|
| WASD / arrows | move (silent) |
| Shift | run (fast, but monsters hear it) |
| P / Esc | pause |

- **Teal rooms** are safe. Monsters can't enter them, and you respawn in the last one you stood in.
- **Purple walls** (with a rune) and floor tiles with purple corner dots swap places during blackouts.
- **The exit gate** shuts after a set number of blackouts, then reopens. Each time it shuts, the monsters get faster.
- **Map:** on Easy you start with a full map. On Medium you collect map pieces (chests). On Hard and Nightmare there's no map, and your lantern burns oil (flasks).
- The map only updates where you've been, so after a shift it shows how the maze *used to* look.

## Where things are

| Path | What |
|---|---|
| `scripts/game.gd` | Run state and **all difficulty numbers** (`LEVELS`) |
| `scripts/phase.gd` | The light → warning → dark cycle (a state machine) |
| `scripts/events.gd` | Signal bus |
| `scripts/level.gd` | Reads the map, paints tiles, wall shifts, gate, catching |
| `scripts/monster.gd` | Monster brain: frozen / wander / hunt (noise) / chase (sight) |
| `scripts/player.gd` | Movement, noise, lantern |
| `scripts/hud.gd`, `minimap.gd` | HUD, memory map and pause menu |
| `levels/*.gd` | The mazes as text. Edit them by hand (legend at the top of each file) |
| `tools/` | Python scripts that regenerate the mazes, tile atlas and sounds |
| `tests/smoke_test.gd` | Headless test that plays through all four rings |

## Regenerate assets

```sh
python3 tools/make_mazes.py   # new mazes (checks no shift can ever trap you)
python3 tools/make_tiles.py   # art/maze_tiles.png (needs Pillow)
python3 tools/make_sfx.py     # audio/*.wav placeholders
```

Run the test with:

```sh
/path/to/Godot --headless --path . --script res://tests/smoke_test.gd
```

Add `-- die` to the end of that command to test losing all 3 lives instead of escaping.

## Credits

The art is [16x16 DungeonTileset II](https://0x72.itch.io/dungeontileset-ii) by 0x72 (CC0). The wall tiles in `art/maze_tiles.png` are composed from its bricks and colours.

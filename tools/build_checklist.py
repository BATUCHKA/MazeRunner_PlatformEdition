"""Builds docs/blackout-maze-checklist.html, the step-by-step rebuild guide.

Code shown on the page is pulled straight from the project's scripts, so the
guide always matches the answer key. Edit the step text below, then run:
  python3 tools/build_checklist.py
"""
import html
import re

OUT = "docs/blackout-maze-checklist.html"


# ------------------------------------------------------------------ code extraction

def read(path):
    with open(path) as f:
        return f.read().replace("\t", "    ")


def whole(path):
    return read(path).rstrip() + "\n"


def header(path):
    """Everything above the first top-level function (minus its doc comment)."""
    lines = read(path).split("\n")
    out = []
    for line in lines:
        if re.match(r"(static )?func ", line):
            break
        out.append(line)
    # drop blank lines and the first function's ## doc comment
    while out and (out[-1].strip() == "" or (out[-1].startswith("##") and len(out) > 1 and not all(l.startswith(("##", "extends", "class_name")) for l in out))):
        out.pop()
    return "\n".join(out).rstrip() + "\n"


def funcs(path, *names):
    lines = read(path).split("\n")
    chunks = []
    for name in names:
        start = None
        for i, line in enumerate(lines):
            if re.match(r"(static )?func %s\(" % re.escape(name), line):
                start = i
                break
        if start is None:
            raise SystemExit("function %s not found in %s" % (name, path))
        # include doc comments directly above
        s = start
        while s > 0 and lines[s - 1].startswith("##"):
            s -= 1
        e = start + 1
        while e < len(lines) and (lines[e].strip() == "" or lines[e][0] in " \t"):
            e += 1
        chunk = lines[s:e]
        while chunk and chunk[-1].strip() == "":
            chunk.pop()
        chunks.append("\n".join(chunk))
    return "\n\n\n".join(chunks) + "\n"


# ------------------------------------------------------------------ html helpers

def esc(s):
    return html.escape(s, quote=False)


def code(label, src, lang="gd"):
    cls = ' class="gd"' if lang == "gd" else ""
    head = '<div class="codehead"><span>%s</span></div>' % esc(label) if label else ""
    return '%s<pre><code%s>%s</code></pre>' % (head, cls, esc(src.rstrip("\n")))


def tree(src):
    return '<pre class="tree"><code>%s</code></pre>' % esc(src.strip("\n"))


def li(items):
    return "".join("<li>%s</li>" % i for i in items)


STEPS = []
PHASES = []


def phase(title, intro=""):
    PHASES.append({"title": title, "intro": intro, "steps": []})


def step(title, goal="", do=(), codes=(), how=(), warn=(), test="", key="", milestone=False, extra="", sub=""):
    n = len(STEPS) + 1
    s = dict(n=n, title=title, goal=goal, do=do, codes=codes, how=how, warn=warn, test=test, key=key,
             milestone=milestone, extra=extra, sub=sub)
    STEPS.append(s)
    PHASES[-1]["steps"].append(s)


def render_step(s):
    tag = '<span class="tag ms">Milestone</span>' if s["milestone"] else ""
    sub = " <em>(%s)</em>" % s["sub"] if s["sub"] else ""
    out = ['<li class="step" data-step="%d">' % s["n"],
           '<label><input type="checkbox" id="s%d"><span class="box"></span><span class="sn">%02d</span>'
           '<span class="st">%s%s%s</span></label>' % (s["n"], s["n"], s["title"], sub, tag),
           '<div class="body">']
    if s["goal"]:
        out.append('<p class="goal">%s</p>' % s["goal"])
    if s["do"]:
        out.append('<h4>Do it</h4><ol class="do">%s</ol>' % li(s["do"]))
    for c in s["codes"]:
        out.append(c)
    if s["extra"]:
        out.append(s["extra"])
    if s["how"]:
        out.append('<h4>How it works</h4><ul class="how">%s</ul>' % li(s["how"]))
    if s["warn"]:
        out.append('<h4>Watch out</h4><ul class="warn">%s</ul>' % li(s["warn"]))
    if s["test"]:
        out.append('<p class="test"><b>Test:</b> %s</p>' % s["test"])
    if s["key"]:
        out.append('<p class="key"><b>Answer key:</b> %s</p>' % s["key"])
    out.append("</div></li>")
    return "\n".join(out)


# ================================================================== content

phase("Project setup")

step("Create a fresh project",
     goal="A clean Godot 4.7 project to rebuild the game in, separate from the finished one.",
     do=["Open Godot, click <b>Create New Project</b> (or <b>+ Create</b>). Name it something like <code>blackout-maze-mine</code>.",
         "Renderer: <b>Forward+</b> works on Mac. Pick <b>Compatibility</b> if you plan to export to the web.",
         "In the <b>FileSystem</b> dock (bottom left), right-click <code>res://</code> &rarr; <b>New &rarr; Folder</b> and make "
         "<code>scenes</code>, <code>scripts</code>, <code>art</code>, <code>levels</code>, <code>audio</code>, <code>tools</code> and <code>tests</code>.",
         "Optional but smart: in a terminal, run <code>git init</code> in the project folder and commit after every step."],
     how=["Godot calls the project folder <code>res://</code>. Every path in code starts from there, like <code>res://scenes/player.tscn</code>.",
          "Godot creates a hidden <code>.godot/</code> folder for imported files. Never edit it; it's rebuilt automatically."],
     warn=["Don't build inside <code>maze-runner--platform-edition</code>. Keep that as your untouched answer key."])

step("Set up the screen for pixel art",
     goal="A small 640&times;360 game screen, scaled up 2&times; in a 1280&times;720 window, with crisp pixels.",
     do=["<b>Project &rarr; Project Settings &rarr; General</b>. Turn on <b>Advanced Settings</b> (toggle at the top right).",
         "<b>Display &rarr; Window</b>: Viewport Width <code>640</code>, Viewport Height <code>360</code>.",
         "Same page: Window Width Override <code>1280</code>, Window Height Override <code>720</code>.",
         "Same page, Stretch: Mode <code>canvas_items</code>, Aspect <code>expand</code>.",
         "<b>Rendering &rarr; Textures</b>: Default Texture Filter <code>Nearest</code>."],
     how=["The game is designed at 640&times;360. <code>canvas_items</code> stretch scales everything up to fill the window.",
          "<b>Nearest</b> filtering keeps each pixel a sharp square instead of blurring it when scaled.",
          "At 16 px per tile, 640&times;360 shows 40&times;22 tiles. That's why the Outer Ring (45&times;27) almost fits on one screen."],
     test="Press F5 later and the window should open at 1280&times;720.")

step("Set up the Input Map",
     goal="Named actions instead of hard-coded keys, so code says <code>\"run\"</code> rather than <code>KEY_SHIFT</code>.",
     do=["<b>Project Settings &rarr; Input Map</b> tab.",
         "Type <code>move_left</code> in the <b>Add New Action</b> box and press <b>Add</b>. Repeat for "
         "<code>move_right</code>, <code>move_up</code>, <code>move_down</code>, <code>run</code>, <code>pause</code>.",
         "Click the <b>+</b> next to each action and press the key: A and &larr; for move_left, D and &rarr; for move_right, "
         "W and &uarr; for move_up, S and &darr; for move_down, Shift for run, P for pause."],
     how=["<code>Input.get_vector(\"move_left\", \"move_right\", \"move_up\", \"move_down\")</code> later turns the four actions into one direction vector.",
          "Esc already works as <code>ui_cancel</code>, a built-in action. The pause menu listens for both."],
     warn=["Action names must match exactly, including underscores. A typo gives no error, the key just does nothing."])

step("Bring in the art",
     goal="Copy only the sprites you'll use from the 0x72 DungeonTileset II pack.",
     do=["Create <code>art/0x72/</code> in the FileSystem dock.",
         "In Finder, open <code>0x72_DungeonTilesetII_v1.7/frames/</code>.",
         "Drag in the <code>idle_anim_f0</code>&ndash;<code>f3</code> and <code>run_anim_f0</code>&ndash;<code>f3</code> files for "
         "<code>knight_m</code>, <code>big_zombie</code>, <code>ogre</code> and <code>big_demon</code> (32 files).",
         "Also drag in <code>floor_1</code>&ndash;<code>floor_8</code>, <code>floor_stairs</code>, <code>wall_mid</code>, <code>wall_top_mid</code>, "
         "<code>chest_full_open_anim_f0</code>, <code>flask_big_yellow</code>, <code>ui_heart_full</code>, <code>ui_heart_empty</code>.",
         "Copy the pack's <code>README</code> in too, as <code>README_0x72.txt</code>, for credit."],
     how=["Godot imports each PNG automatically and makes a <code>.import</code> file next to it. Leave those alone.",
          "The knight is 16&times;28 px; the three monsters are 32&times;36, twice a tile wide. They look big and scary in 16 px corridors on purpose."],
     key="art/0x72/ (48 files)")

phase("Global scripts", "Autoloads are scripts Godot creates once at startup and keeps alive across scene changes. "
      "Everything else talks to them, so build them first. Register each one under <b>Project Settings &rarr; Globals &rarr; Autoload</b>: "
      "pick the file, type the exact name shown, click <b>Add</b>.")

step("Events, the signal bus", sub='autoload "Events"',
     goal="One place where game-wide signals live, so nodes can talk without holding references to each other.",
     do=["Right-click <code>scripts/</code> &rarr; <b>New Script</b>, inherits <code>Node</code>, name <code>events.gd</code>.",
         "Type the signals below.",
         "Register it as an autoload named <code>Events</code>."],
     codes=[code("scripts/events.gd", whole("scripts/events.gd"))],
     how=["A monster calls <code>Events.player_caught.emit()</code>; the level did <code>Events.player_caught.connect(_on_player_caught)</code>. Neither needs to find the other.",
          "Signals can carry values: <code>noise_made</code> sends where the noise happened."],
     key="scripts/events.gd")

step("Phase, the blackout state machine", sub='autoload "Phase"',
     goal="A timer-driven loop: Light &rarr; Warning &rarr; Dark &rarr; Light, broadcasting each change.",
     do=["New script <code>scripts/phase.gd</code> (inherits Node). Type the code.",
         "Register as autoload <code>Phase</code>."],
     codes=[code("scripts/phase.gd", whole("scripts/phase.gd"))],
     how=["<code>enum P</code> gives the three states names. Elsewhere you write <code>Phase.P.DARK</code>.",
          "The Timer is created in code and added as a child. Its <code>timeout</code> signal calls <code>_next()</code>, which picks the next state with <code>match</code>.",
          "<code>blackouts</code> counts finished dark phases. Wall shifts and the exit gate are scheduled from it.",
          "<code>fraction_left()</code> is 1.0 at the start of a phase and 0.0 at the end, which drives the HUD bar."],
     warn=["Inside this file, refer to the states as <code>P.LIGHT</code>; from other scripts, <code>Phase.P.LIGHT</code>.",
           "Because the Timer is a child of the autoload, pausing the game (step 40) pauses the cycle too. That's what you want."],
     test="Temporarily add <code>print(P.keys()[p])</code> in <code>_enter</code>, and <code>Phase.start(2, 1)</code> in any scene's <code>_ready</code>. Run it and watch LIGHT, WARNING, DARK repeat in the Output panel.",
     key="scripts/phase.gd")

step("Sounds and the Sfx player", sub='autoload "Sfx"',
     goal="Eleven sound effects, and a helper that plays them from anywhere.",
     do=["Get 11 WAV files into <code>audio/</code> named <code>step</code>, <code>rumble</code>, <code>growl</code>, <code>pickup</code>, <code>caught</code>, "
         "<code>lights_off</code>, <code>lights_on</code>, <code>tick</code>, <code>gate</code>, <code>heartbeat</code>, <code>level_clear</code>. "
         "Either make them on <a href=\"https://sfxr.me\">sfxr.me</a> and export WAV, or copy <code>tools/make_sfx.py</code> from the answer key and run <code>python3 tools/make_sfx.py</code>.",
         "New script <code>scripts/sfx.gd</code>, type the code, register as autoload <code>Sfx</code>."],
     codes=[code("scripts/sfx.gd", whole("scripts/sfx.gd"))],
     how=["<code>play()</code> reuses a pool of 8 players, so many sounds can overlap without creating nodes every time.",
          "<code>play_at()</code> makes an <code>AudioStreamPlayer2D</code> at a world position. It gets quieter with distance from the camera and pans left/right, so you can hear where a growl came from in the dark.",
          "<code>p.finished.connect(p.queue_free)</code> deletes the player when its sound ends.",
          "<code>PROCESS_MODE_ALWAYS</code> keeps sounds working while the game is paused."],
     warn=["If a file name doesn't match the list in <code>SOUNDS</code>, Godot errors at startup with a failed <code>load</code>."],
     test="Call <code>Sfx.play(\"pickup\")</code> from any <code>_ready</code> and you should hear a blip.",
     key="scripts/sfx.gd, tools/make_sfx.py")

step("Game, run state and the difficulty table", sub='autoload "Game"',
     goal="Everything that must survive moving from one ring to the next: lives, current ring, time, and every tuning number.",
     do=["New script <code>scripts/game.gd</code>, type the code, register as autoload <code>Game</code>.",
         "The scene paths point to files you'll make later. That's fine; they're only loaded when used."],
     codes=[code("scripts/game.gd", whole("scripts/game.gd"))],
     how=["<code>LEVELS</code> is the whole difficulty curve in one table. To tune the game later, you only touch these numbers.",
          "<code>groups: {1: 1, 2: 2}</code> means wall group 1 flips on every blackout and group 2 on every second one.",
          "<code>change_scene_to_file.call_deferred(...)</code> waits until the end of the frame to swap scenes, so nothing is freed while it's still running.",
          "<code>run_time</code> only counts while <code>running</code> is true and the game isn't paused."],
     key="scripts/game.gd")

phase("The player")

step("An Art helper that builds animations in code",
     goal="One function that turns the pack's numbered PNGs into idle and run animations for any character.",
     do=["New script <code>scripts/art.gd</code>. It doesn't extend anything; delete the <code>extends</code> line if Godot adds one.",
         "Type the code. Don't register it as an autoload: <code>class_name</code> makes it available everywhere already."],
     codes=[code("scripts/art.gd", whole("scripts/art.gd"))],
     how=["<code>class_name Art</code> registers a global type, so any script can call <code>Art.sprite_frames(\"ogre\")</code>.",
          "<code>static func</code> means you call it on the class itself, without making an instance.",
          "<code>\"res://art/0x72/%s_%s_anim_f%d.png\" % [character, anim, i]</code> fills in the blanks, building names like <code>ogre_run_anim_f2.png</code>."],
     warn=["If a character is missing a frame, <code>load()</code> returns null and the sprite flickers. Check the 32 files from step 4."],
     key="scripts/art.gd")

step("Player scene", sub="scenes/player.tscn",
     goal="The runner: a physics body with a sprite, a small collision circle at the feet, and a camera.",
     do=["<b>Scene &rarr; New Scene</b> &rarr; <b>Other Node</b> &rarr; <code>CharacterBody2D</code>. Rename it <code>Player</code>.",
         "Inspector: <b>Motion Mode</b> = <code>Floating</code>. Under <b>Collision</b>, Layer: only <b>2</b>; Mask: only <b>1</b>.",
         "Right dock &rarr; <b>Groups</b> tab (next to Inspector and Signals) &rarr; <b>+</b> &rarr; name <code>player</code>, Global unticked &rarr; OK. A group icon appears next to Player in the Scene dock.",
         "Add child <code>AnimatedSprite2D</code>, name it <code>Sprite</code>, Position (0, -10).",
         "Add child <code>CollisionShape2D</code>, name it <code>Shape</code>, Shape: New <code>CircleShape2D</code>, radius 5.",
         "Add child <code>Camera2D</code>: Position Smoothing Enabled on, Speed 6.",
         "Save as <code>scenes/player.tscn</code>. The two lanterns are added in step 20."],
     extra=tree("Player (CharacterBody2D)  layer 2, mask 1, Floating, group \"player\"\n"
                "├── Sprite (AnimatedSprite2D)   position (0, -10)\n"
                "├── Shape (CollisionShape2D)    circle r = 5\n"
                "└── Camera2D                    smoothing on, speed 6"),
     how=["<b>Floating</b> motion mode is for top-down games: no floor and no gravity, so it slides along walls in any direction.",
          "The body's origin is at the feet; the sprite is moved up 10 px so its feet line up with the circle. That keeps collisions honest in a 3/4 view.",
          "<b>Layer 2, mask 1</b>: the player sits on layer 2 and bumps into layer 1 (walls, gate). Monsters' sight rays check only layer 1, so the player's own body never blocks them."],
     key="scenes/player.tscn")

step("Movement, footsteps and noise",
     goal="Walk silently, run fast and loudly, and animate.",
     do=["Select the Player root, click the script icon to attach a new script, save it as <code>scripts/player.gd</code>.",
         "Type the variables and the two functions below. The other functions come in later steps; leave them out for now, along with the "
         "<code>@onready</code> lines for <code>lantern</code> and <code>wall_light</code> and the two lines in <code>_ready</code> that use them."],
     codes=[code("scripts/player.gd (top)", header("scripts/player.gd")),
            code("scripts/player.gd", funcs("scripts/player.gd", "_ready", "_physics_process"))],
     how=["<code>get_vector</code> returns a direction already normalised, so diagonals aren't faster.",
          "<code>velocity = ...</code> then <code>move_and_slide()</code> is the standard CharacterBody2D pattern: you set the speed, Godot handles walls.",
          "Two countdown timers made from floats: <code>_step_t</code> for footstep sounds and <code>_noise_t</code> for noise pulses. Subtract <code>delta</code> each frame; when it hits zero, act and reset.",
          "Running emits <code>Events.noise_made</code> 4 times a second. Monsters (step 27) decide if they're close enough to hear it."],
     warn=["<code>@onready var sprite: AnimatedSprite2D = $Sprite</code> only works if the child is named exactly <code>Sprite</code>."],
     test="Drag <code>player.tscn</code> into a temporary empty scene and press F6. The knight walks, runs with Shift and flips left and right.",
     key="scripts/player.gd &rarr; _ready, _physics_process")

phase("The maze")

step("The tile atlas",
     goal="One 256&times;48 image holding every wall and floor tile the maze needs.",
     do=["Easiest: copy <code>tools/make_tiles.py</code> from the answer key, install Pillow (<code>pip3 install pillow</code>) and run "
         "<code>python3 tools/make_tiles.py</code> from your project folder. It writes <code>art/maze_tiles.png</code>.",
         "Or draw it yourself in Aseprite or LibreSprite, following the layout below exactly."],
     extra='<div class="tablewrap"><table><thead><tr><th>Row</th><th>Columns</th><th>What</th></tr></thead><tbody>'
           '<tr><th>0</th><td>0&ndash;15</td><td>Normal walls. Column = mask: +1 wall to the north, +2 wall to the east, +4 wall to the west, +8 floor to the south (show bricks).</td></tr>'
           '<tr><th>1</th><td>0&ndash;15</td><td>Shifting walls: same masks, tinted purple with a small rune.</td></tr>'
           '<tr><th>2</th><td>0&ndash;7</td><td>Floor variants (0 is plain).</td></tr>'
           '<tr><th>2</th><td>8, 9, 10</td><td>Safe-room floor (teal), exit stairs, shift-hint floor (purple corner dots).</td></tr>'
           '</tbody></table></div>',
     how=["The pack's own wall tiles draw thin ridges. This maze's walls are exactly one tile thick, so full-block tiles are composed from the pack's bricks and colours instead.",
          "Only north, east, west and \"floor below\" matter for the look, so 16 variants cover every case.",
          "Shifting walls look different on purpose. Observant players learn which walls to distrust."],
     key="tools/make_tiles.py, art/maze_tiles.png")

step("Build the TileSet in code",
     goal="Turn the atlas into a TileSet where walls block movement and light, and floors do neither.",
     do=["New script <code>scripts/maze_tiles.gd</code> (no <code>extends</code>), type the code."],
     codes=[code("scripts/maze_tiles.gd", whole("scripts/maze_tiles.gd"))],
     how=["A <b>physics layer</b> gives tiles collision. Each wall tile gets a 16&times;16 square, so the player can't walk through it.",
          "An <b>occlusion layer</b> gives tiles light occluders. Walls cast shadows from the lantern (step 20).",
          "Tile shapes are centred on the tile, so the square runs from (-8, -8) to (8, 8).",
          "Floor tiles are created with <code>create_tile</code> but get no collision or occluder."],
     warn=["The order matters: <code>ts.add_source(src, ...)</code> must happen before setting collision on tiles, because the tiles need to know which physics layers exist."],
     key="scripts/maze_tiles.gd")

step("Write a maze as text",
     goal="A tiny hand-made test maze, in the same format as the real ones.",
     do=["Create <code>levels/outer_ring.gd</code> and type a small maze like the one below. Every row must be the same length.",
         "Put the <code>X</code> on the outer edge, next to a floor tile."],
     codes=[code("levels/outer_ring.gd (tiny test version)",
                 'extends RefCounted\n\nconst MAP := """\n###########X#\n#.....#.....#\n#.###.#.#1#.#\n#.#sssss#...#\n#...ss@ss.h.#\n#.#sssss#.#.#\n#...5.....#.#\n#############\n"""\n')],
     extra='<div class="tablewrap"><table><thead><tr><th>Char</th><th>Meaning</th></tr></thead><tbody>'
           '<tr><th><code>#</code> / <code>.</code></th><td>wall / floor</td></tr>'
           '<tr><th><code>@</code></th><td>player start (inside a safe room)</td></tr>'
           '<tr><th><code>X</code></th><td>exit gate, on the edge</td></tr>'
           '<tr><th><code>s</code></th><td>safe-room floor</td></tr>'
           '<tr><th><code>h</code> <code>m</code> <code>o</code></th><td>monster spawn, map piece, lantern oil</td></tr>'
           '<tr><th><code>1</code>&ndash;<code>4</code></th><td>shifting wall of group 1&ndash;4, <b>closed</b> at the start</td></tr>'
           '<tr><th><code>5</code>&ndash;<code>8</code></th><td>shifting wall of group 1&ndash;4, <b>open</b> at the start</td></tr>'
           '</tbody></table></div>',
     how=["Storing the map as a <code>const</code> in a <code>.gd</code> file means it's exported with the game automatically. A <code>.txt</code> file would need an export filter.",
          "In code, <code>load(\"res://levels/outer_ring.gd\").MAP</code> reads the string.",
          "When the group flips, closed cells open and open cells close, like a sliding wall."],
     warn=["A shifting wall must never be able to cut part of the maze off. With a hand-made maze, check every on/off combination yourself. Step 39's tool does it automatically."],
     key="levels/outer_ring.gd")

step("One Level scene for all three rings", sub="scenes/level.tscn",
     goal="The scene every ring uses. It reads which ring to build from <code>Game.current_level</code>.",
     do=["New Scene &rarr; <b>2D Scene</b> (a Node2D). Rename it <code>Level</code>.",
         "Add the children in the order shown. Order is draw order: later nodes draw on top.",
         "Select <code>Walls</code> &rarr; Inspector &rarr; <b>CanvasItem &rarr; Visibility &rarr; Light Mask</b>: turn bit 1 off and bit 2 on.",
         "Gate: add a <code>CollisionShape2D</code> child named <code>Shape</code> with a 16&times;16 <code>RectangleShape2D</code>; set the Gate's Collision Mask to nothing.",
         "Player: drag <code>scenes/player.tscn</code> from the FileSystem dock onto <code>Level</code> to instance it.",
         "Glow: CanvasLayer, Layer 1, turn on <b>Follow Viewport &rarr; Enabled</b>.",
         "Save as <code>scenes/level.tscn</code>. The HUD gets added in step 39."],
     extra=tree("Level (Node2D)               script: scripts/level.gd\n"
                "├── Floor (TileMapLayer)\n"
                "├── Walls (TileMapLayer)        Light Mask = 2 only\n"
                "├── Gate (StaticBody2D)         layer 1, mask none\n"
                "│   └── Shape (CollisionShape2D)  16×16 rectangle\n"
                "├── Items (Node2D)\n"
                "├── Monsters (Node2D)\n"
                "├── Player (player.tscn instance)\n"
                "├── Darkness (CanvasModulate)\n"
                "├── Glow (CanvasLayer)           layer 1, Follow Viewport on\n"
                "└── HUD (hud.tscn instance)      ← added in step 39"),
     how=["You don't set a TileSet on the two TileMapLayers in the editor; <code>level.gd</code> assigns <code>MazeTiles.build()</code> at runtime.",
          "<code>Items</code> and <code>Monsters</code> are just folders so spawned things stay tidy in the Remote tree."],
     key="scenes/level.tscn")

step("Parse the map",
     goal="Turn the text map into dictionaries the rest of the code can ask questions about.",
     do=["Attach a new script <code>scripts/level.gd</code> to the <code>Level</code> root.",
         "Type the top of the file. For now, comment out the <code>MONSTER_SCENE</code> and <code>PICKUP_SCENE</code> lines (those scenes arrive in steps 26 and 34; <code>preload</code> fails if the file doesn't exist yet) and the <code>@onready</code> line for <code>hud</code> (step 39).",
         "Type <code>_parse</code> and <code>is_wall</code>."],
     codes=[code("scripts/level.gd (top)", header("scripts/level.gd")),
            code("scripts/level.gd", funcs("scripts/level.gd", "_parse", "is_wall"))],
     how=["Cells are <code>Vector2i(x, y)</code>, used as dictionary keys. <code>base[Vector2i(3, 5)]</code> tells you what never moves at column 3, row 5.",
          "<code>@</code> is stored as <code>\"s\"</code> because the start is inside a safe room; its position is remembered in <code>start_cell</code>.",
          "Digits are stored as floor in <code>base</code>, plus an entry in <code>shift_cells</code>.",
          "<code>is_wall</code> decides shifting cells with one comparison: closed at start, unless the group has flipped. <code>!=</code> works like XOR here.",
          "Anything outside the map counts as a wall, so neighbour checks at the edges are safe."],
     key="scripts/level.gd &rarr; _parse, is_wall")

step("Paint each tile with the right piece",
     goal="Put the correct atlas tile in every cell, based on its neighbours.",
     do=["Type <code>_paint</code>."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_paint"))],
     how=["<code>mask |= MazeTiles.N</code> sets one bit. The finished mask is the column number in the atlas.",
          "<code>set_cell(cell, source_id, atlas_coords)</code> places a tile; <code>erase_cell</code> removes one.",
          "Walls go on the <code>Walls</code> layer, floors on the <code>Floor</code> layer, never both on one cell.",
          "<code>absi(hash(c))</code> gives a stable \"random\" number per cell. The floor pattern is the same every time you play, but looks natural."],
     key="scripts/level.gd &rarr; _paint")

step("Spawn the player and limit the camera", milestone=True,
     goal="See and walk your maze for the first time.",
     do=["Type the helpers <code>cell_center</code> and <code>world_to_cell</code>.",
         "Type this <b>starter</b> <code>_ready</code>. It grows in later steps; the final version is in step 38."],
     codes=[code("scripts/level.gd (starter _ready)",
                 "func _ready() -> void:\n    cfg = Game.level()\n    var tiles := MazeTiles.build()\n    walls.tile_set = tiles\n    floor_layer.tile_set = tiles\n\n"
                 "    _parse(load(cfg.map).MAP)\n    for c in base:\n        _paint(c)\n    player.global_position = cell_center(start_cell)\n\n"
                 "    var cam: Camera2D = player.camera\n    cam.limit_left = 0\n    cam.limit_top = 0\n    cam.limit_right = map_size.x * T\n"
                 "    cam.limit_bottom = map_size.y * T\n    cam.reset_smoothing.call_deferred()\n"),
            code("scripts/level.gd", funcs("scripts/level.gd", "cell_center", "world_to_cell"))],
     how=["Tile (3, 5) covers pixels 48&ndash;63 across and 80&ndash;95 down. Its centre is <code>(3, 5) * 16 + (8, 8)</code>.",
          "<code>world_to_cell</code> is the reverse: divide by 16 and round down with <code>floori</code>.",
          "Camera limits stop the view at the maze edges. <code>reset_smoothing</code> snaps the camera so it doesn't glide in from (0, 0) at the start."],
     warn=["<code>Game.level()</code> uses <code>current_level</code>, which starts at 0, so you can test with F6 straight away without a title screen.",
           "If the map loads but nothing shows, check that <code>MazeTiles.build()</code> found <code>res://art/maze_tiles.png</code>."],
     test="Open <code>level.tscn</code> and press <b>F6</b>. You stand in a teal room and walls stop you. Turn on <b>Debug &rarr; Visible Collision Shapes</b> to see the wall squares.",
     key="scripts/level.gd &rarr; _ready, cell_center, world_to_cell")

phase("Lights out")

step("Darken the world on blackout",
     goal="The whole maze goes black when the Phase changes to Dark, and comes back in the Light.",
     do=["In <code>_ready</code>, add <code>darkness.color = Color.WHITE</code>, <code>Phase.changed.connect(_on_phase)</code> and "
         "<code>Phase.start(cfg.light, cfg.dark, cfg.warning)</code>.",
         "Type <code>_on_phase</code>. For now, comment out the lines calling <code>_update_gate()</code> and <code>_shift_walls()</code> (steps 33 and 22), and <code>player.set_dark</code> (step 20)."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_on_phase"))],
     how=["A <b>CanvasModulate</b> multiplies the colour of everything on its canvas layer. White means normal; near-black means blackout.",
          "<code>create_tween().tween_property(darkness, \"color\", ..., 0.25)</code> fades it over a quarter of a second.",
          "<code>_dark_tween.kill()</code> stops a fade still running from the previous phase, so two tweens never fight."],
     warn=["The dark colour is <code>Color(0.012, 0.012, 0.022)</code>. The first version used 0.035, and you could see the whole maze faintly through the blackout, which ruined the memory game."],
     test="F6: the screen goes black every few seconds and nothing is visible at all, including you. The lantern comes next.",
     key="scripts/level.gd &rarr; _on_phase")

step("The two-lantern trick",
     goal="A lantern that throws real shadows down corridors, while nearby walls stay readable.",
     do=["Open <code>player.tscn</code>. Add a <code>PointLight2D</code> named <code>Lantern</code> at (0, -4).",
         "Texture: <b>New GradientTexture2D</b>. Width/Height 256, Fill <b>Radial</b>, Fill From (0.5, 0.5), Fill To (1, 0.5). "
         "Gradient: warm white at 0, warm orange half-transparent at 0.5, fully transparent at 1.",
         "Lantern: Energy 0, Shadow Enabled on, Shadow Filter PCF5, Filter Smooth 1.5. Range Item Cull Mask: bit 1 only. Shadow Item Cull Mask: bit 1 only.",
         "Duplicate it (Ctrl/Cmd + D), name it <code>WallLight</code>: Shadow Enabled <b>off</b>, Range Item Cull Mask: bit 2 only, Texture Scale 0.6.",
         "Back in <code>player.gd</code>, add the <code>@onready</code> lines for both lights and the two lines in <code>_ready</code> that zero their energy, then type <code>set_dark</code>.",
         "Uncomment <code>player.set_dark(...)</code> in the level's <code>_on_phase</code>."],
     codes=[code("scripts/player.gd", funcs("scripts/player.gd", "set_dark"))],
     how=["<b>Lantern</b> lights things on light mask 1 (floor, player, monsters, items) and casts shadows from the wall occluders.",
          "But a wall tile sits inside its own occluder, so a shadow-casting light leaves the walls themselves black.",
          "<b>WallLight</b> has no shadows and only touches light mask 2, which is just the <code>Walls</code> layer. So walls near you stay visible, while the floor only shows what's in your line of sight.",
          "Energy is 0 in daylight. A light adds brightness, so leaving it on would make a glowing blob around you in the light."],
     test="F6: in the blackout you see a warm circle around you, and shadows stretch away from corners.",
     key="scenes/player.tscn, scripts/player.gd &rarr; set_dark")

step("Warning flicker", milestone=True,
     goal="Before the lights die, they flicker three times with a tick sound, so the dark never catches you off guard.",
     do=["You already typed the <code>WARNING</code> branch of <code>_on_phase</code> in step 19. Make sure it's there."],
     how=["The flicker fits inside <code>cfg.warning</code> seconds: 3 dips, each taking a sixth of the time to dim and three-sixths to recover.",
          "<code>tween_callback(Sfx.play.bind(\"tick\", -8.0))</code> runs a function at that point in the tween. <code>bind</code> pre-fills its arguments.",
          "Tween steps run one after another unless you call <code>set_parallel()</code>."],
     test="The lights flicker, tick, die, and come back. Your lantern shows real shadows. This is the moment it starts to feel like a game.",
     key="scripts/level.gd &rarr; _on_phase (WARNING)")

phase("Shifting walls")

step("Flip groups on schedule",
     goal="Each blackout, some groups of walls swap: closed parts open and open parts close.",
     do=["Type <code>_shift_walls</code>. Leave out the <code>_update_astar</code> line until step 25, and the dust and shake lines until step 24.",
         "Uncomment <code>_shift_walls()</code> in <code>_on_phase</code>."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_shift_walls"))],
     how=["<code>Phase.blackouts</code> is 0 during the first blackout. <code>(n + 1) % every</code> is 0 when it's this group's turn: every 1st, 2nd or 3rd blackout.",
          "Flipping is just <code>group_flipped[g] = not group_flipped[g]</code>. <code>is_wall</code> already reads that.",
          "<code>to_paint</code> collects each changed cell and its 8 neighbours in a dictionary (so none is painted twice). Neighbours need repainting because a wall's look depends on what's around it.",
          "Changing tiles with <code>set_cell</code> also updates their collision and occluders automatically."],
     test="Stand still near a purple wall. When the lights return, it has moved and the tile next to it changed too.",
     key="scripts/level.gd &rarr; _shift_walls")

step("Never close a wall on someone",
     goal="If a wall would appear where the player or a monster is standing, skip that group this time.",
     do=["Type <code>_flip_is_safe</code>. Until monsters exist (step 26), the monster loop just finds nothing."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_flip_is_safe"))],
     how=["The player's collision circle can overlap up to four tiles, so all four corners (&plusmn;6 px) are checked.",
          "Each monster reports its current tile and the tile it's walking into (<code>occupied_cells()</code>, step 26).",
          "Only cells that are open now and would close matter, hence <code>not is_wall(c)</code>.",
          "Skipping is safe because the maze generator checked every on/off combination (step 37)."],
     warn=["Without this, the player gets stuck inside a wall and <code>move_and_slide</code> can't push them out."],
     key="scripts/level.gd &rarr; _flip_is_safe")

step("Rumble, shake and dust", milestone=True,
     goal="Make the shift felt: sound, a camera shake and dust where walls moved.",
     do=["Add <code>shake</code> to <code>player.gd</code> and <code>_dust</code> to <code>level.gd</code>.",
         "Make sure <code>_shift_walls</code> ends by playing <code>rumble</code>, calling <code>player.shake(3.0, 0.6)</code>, and spawning dust within 200 px."],
     codes=[code("scripts/player.gd", funcs("scripts/player.gd", "shake")),
            code("scripts/level.gd", funcs("scripts/level.gd", "_dust"))],
     how=["The shake tweens <code>Camera2D.offset</code> through 8 random points that shrink each step, then back to zero.",
          "<code>CPUParticles2D</code> with <code>one_shot</code> and high <code>explosiveness</code> makes one puff. <code>finished.connect(queue_free)</code> cleans it up."],
     test="Memorise a route, wait for the dark, feel the rumble, and find the route changed when the lights come back.",
     key="scripts/player.gd &rarr; shake, scripts/level.gd &rarr; _dust")

phase("Monsters")

step("A pathfinding grid with AStarGrid2D",
     goal="A grid that answers \"what's the shortest walkable path from here to there?\" for monsters.",
     do=["Type <code>_setup_astar</code>, <code>_update_astar</code> and <code>random_open_cell_near</code>.",
         "Call <code>_setup_astar()</code> in <code>_ready</code> right after <code>_parse(...)</code>.",
         "Uncomment the <code>_update_astar(c)</code> call in <code>_shift_walls</code>."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_setup_astar", "_update_astar", "random_open_cell_near"))],
     how=["<code>region</code> is the map size, <code>cell_size</code> 16 px, and <code>DIAGONAL_MODE_NEVER</code> means no corner-cutting.",
          "A <b>solid</b> point can't be walked through. Walls, safe rooms and the exit are all solid for monsters, so they never enter safe rooms or leave the maze.",
          "When walls shift, only the changed cells need <code>set_point_solid</code> again. No re-baking needed, which is why this beats NavigationAgent2D for a tile maze."],
     key="scripts/level.gd &rarr; _setup_astar, _update_astar, random_open_cell_near")

step("Monster scene", sub="scenes/monster.tscn",
     goal="A monster that knows its level, its speed and how far it can hear.",
     do=["New Scene &rarr; <b>Other Node</b> &rarr; <code>Node2D</code>, named <code>Monster</code>, in group <code>monsters</code>.",
         "Child <code>AnimatedSprite2D</code> named <code>Sprite</code> at (0, -12).",
         "Attach <code>scripts/monster.gd</code>. Type the top of the file and the four functions below.",
         "In level.gd, uncomment <code>MONSTER_SCENE</code>, type <code>_spawn</code>, and in <code>_ready</code> replace the <code>player.global_position = ...</code> line with <code>_spawn()</code>. It places the player, sets the first respawn point, and spawns monsters and items."],
     codes=[code("scripts/monster.gd (top)", header("scripts/monster.gd")),
            code("scripts/monster.gd", funcs("scripts/monster.gd", "setup", "_exit_tree", "cell", "occupied_cells")),
            code("scripts/level.gd", funcs("scripts/level.gd", "_spawn"))],
     how=["No physics body. Monsters follow grid paths, so they can't hit walls, and catching is a distance check.",
          "<code>setup()</code> is called right after <code>add_child</code>, so <code>@onready</code> variables are ready. It connects to the global signals itself.",
          "The eyes object is made in step 31; until then, comment out the two <code>_eyes</code> lines in <code>setup</code>.",
          "Comment out the pickup half of <code>_spawn</code> until step 34."],
     test="F6: monsters stand frozen in the maze as statues.",
     key="scenes/monster.tscn, scripts/monster.gd &rarr; setup")

step("The monster brain",
     goal="Four states: frozen in the light, wandering in the dark, hunting a sound, chasing what it sees.",
     do=["Type <code>_on_phase</code>, <code>_on_noise</code>, <code>_on_walls_shifted</code> and <code>_go</code>."],
     codes=[code("scripts/monster.gd", funcs("scripts/monster.gd", "_on_phase", "_on_noise", "_on_walls_shifted", "_go"))],
     how=["This is a <b>state machine</b>: <code>state</code> holds one value from <code>enum S</code>, and each signal can move it to another.",
          "Hearing ignores walls on purpose. Sound travels through a maze, but the monster still has to walk the long way round.",
          "<code>astar.get_id_path(from, to, true)</code>: the <code>true</code> allows a partial path, so aiming at a safe-room tile still gets the monster as close as possible.",
          "The first cell of a path is where the monster already stands, so it's removed.",
          "After a shift, the monster re-plans to the same destination (<code>path.back()</code>)."],
     key="scripts/monster.gd &rarr; _on_phase, _on_noise, _go")

step("Walk tile to tile",
     goal="Move along the path, chase on sight, catch, and growl.",
     do=["Type the monster's <code>_physics_process</code>. Until step 31, comment out the <code>_update_eyes</code> call."],
     codes=[code("scripts/monster.gd", funcs("scripts/monster.gd", "_physics_process"))],
     how=["<code>move_toward(target, step)</code> moves at most <code>step</code> pixels, so the monster never overshoots the tile centre.",
          "When within 0.5 px of the target tile, that tile is removed and the next becomes the target.",
          "Frozen monsters set <code>sprite.speed_scale = 0</code>, which pauses the animation mid-frame. That's the statue effect.",
          "Speed = base speed &times; <code>monster_speed_mult</code> (grows when the gate shuts) &times; 1.25 while chasing.",
          "Giving up a chase at 1.6&times; sight range (176 px), not 110, stops monsters flickering between chasing and wandering at the edge."],
     test="Run in the dark near a monster. Its eyes aren't in yet, but it starts walking toward you.",
     key="scripts/monster.gd &rarr; _physics_process")

step("Sight",
     goal="A monster sees you only if no wall is in the way.",
     do=["Type <code>has_line_of_sight</code> in level.gd."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "has_line_of_sight"))],
     how=["<code>intersect_ray</code> casts an invisible line through the physics world and returns the first thing it hits, or an empty dictionary.",
          "The last argument, <code>1</code>, is the collision mask: only layer 1 (walls and gate) can block it. The player is on layer 2, so the ray doesn't stop at the player's own body.",
          "Physics queries must run during physics processing, which is why sight is checked in <code>_physics_process</code>."],
     key="scripts/level.gd &rarr; has_line_of_sight")

step("Getting caught", milestone=True,
     goal="Lose a life, flash red, and respawn in the last safe room with a moment of protection.",
     do=["In level.gd: connect <code>Events.player_caught</code> in <code>_ready</code> and type <code>_on_player_caught</code>. Comment out the two <code>hud.</code> lines until step 39.",
         "In player.gd: type <code>respawn</code>. The blinking while invulnerable is already in <code>_physics_process</code>."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_on_player_caught")),
            code("scripts/player.gd", funcs("scripts/player.gd", "respawn"))],
     how=["Several monsters can touch you in the same frame. The first call sets <code>player.frozen</code>, and the check at the top makes every other call return.",
          "<code>await get_tree().create_timer(1.0).timeout</code> pauses this function for a second without freezing the game.",
          "<code>Game.lose_life()</code> returns true when you're out of lives; then <code>Game.finish(\"caught\")</code> goes to the end screen."],
     test="In the dark, run into a monster's path. You flash, freeze, then reappear in a teal room and blink for 2 seconds.",
     key="scripts/level.gd &rarr; _on_player_caught, scripts/player.gd &rarr; respawn")

step("Glowing eyes",
     goal="Two red dots that stay visible in the dark, so you can track monsters.",
     do=["New script <code>scripts/monster_eyes.gd</code>, type it.",
         "In monster.gd, uncomment the <code>_eyes</code> lines in <code>setup</code>, type <code>_update_eyes</code>, and call it from <code>_physics_process</code>."],
     codes=[code("scripts/monster_eyes.gd", whole("scripts/monster_eyes.gd")),
            code("scripts/monster.gd", funcs("scripts/monster.gd", "_update_eyes"))],
     how=["The darkness is a CanvasModulate on the main canvas. It doesn't affect other <b>CanvasLayers</b>, so eyes drawn on <code>Glow</code> stay bright.",
          "<b>Follow Viewport</b> makes the Glow layer scroll with the camera, so world positions line up.",
          "The eyes aren't children of the monster (they live on another layer), so the monster frees them in <code>_exit_tree</code>.",
          "A setter on <code>facing_left</code> calls <code>queue_redraw()</code> only when the value changes."],
     test="In the dark, pairs of red eyes appear and freeze when the lights come back.",
     key="scripts/monster_eyes.gd, scripts/monster.gd &rarr; _update_eyes")

step("Growls, heartbeat and safe rooms",
     goal="Hear monsters before you see them, and know when you're safe.",
     do=["Type the level's <code>_physics_process</code>. Comment out the fuel and exit parts until steps 36 and 38."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_physics_process"))],
     how=["Growls come from each monster's <code>_physics_process</code> via <code>Sfx.play_at</code>, every 2.5&ndash;5 s.",
          "The heartbeat finds the nearest monster. Under 120 px it plays, louder and faster the closer it is: <code>lerpf(0.45, 1.0, nearest / 120.0)</code> seconds between beats.",
          "Safe rooms need no Area2D: if the player's tile is <code>\"s\"</code>, they're safe and that tile becomes the respawn point.",
          "<code>_was_safe</code> remembers last frame, so \"SAFE ROOM\" only shows when you walk in."],
     key="scripts/level.gd &rarr; _physics_process")

phase("Maze rules")

step("The exit gate",
     goal="An exit that shuts after a few blackouts, reopens later, and makes monsters faster each time it shuts.",
     do=["Attach <code>scripts/gate.gd</code> to the Gate node and type it.",
         "In level.gd, type <code>_update_gate</code> and <code>blackouts_until_gate_change</code>. In <code>_ready</code>, add "
         "<code>gate.position = cell_center(exit_cell)</code> and <code>gate.set_open(true, true)</code>. Uncomment <code>_update_gate()</code> in <code>_on_phase</code>."],
     codes=[code("scripts/gate.gd", whole("scripts/gate.gd")),
            code("scripts/level.gd", funcs("scripts/level.gd", "_update_gate", "blackouts_until_gate_change"))],
     how=["The gate cycle is <code>closes_after + reopens_after</code> blackouts long. Open while the position in the cycle is below <code>closes_after</code>.",
          "<code>shape.set_deferred(\"disabled\", open)</code> changes collision safely. Changing physics shapes directly during a physics callback can error.",
          "The bars are drawn with <code>_draw()</code>. <code>tween_method</code> animates <code>_bars_y</code>, and each change calls <code>queue_redraw()</code>.",
          "The gate is also on layer 1, so a shut gate blocks sight too."],
     key="scripts/gate.gd, scripts/level.gd &rarr; _update_gate")

step("Map pieces and oil", sub="scenes/pickup.tscn",
     goal="Collectibles: chests that reveal the map (Medium), flasks that refill the lantern (Hard).",
     do=["New Scene, root <code>Area2D</code> named <code>Pickup</code>. Collision Layer: none. Mask: only <b>2</b>.",
         "Children: <code>Sprite2D</code> named <code>Sprite</code>, and <code>CollisionShape2D</code> named <code>Shape</code> with a circle of radius 7.",
         "Attach <code>scripts/pickup.gd</code> and type it. Save as <code>scenes/pickup.tscn</code>.",
         "In level.gd, uncomment <code>PICKUP_SCENE</code> and the pickup half of <code>_spawn</code>, connect <code>Events.item_picked</code> in <code>_ready</code>, and type <code>_on_item_picked</code>."],
     codes=[code("scripts/pickup.gd", whole("scripts/pickup.gd")),
            code("scripts/level.gd", funcs("scripts/level.gd", "_on_item_picked"))],
     how=["<code>@export_enum(\"map\", \"oil\")</code> shows a dropdown in the Inspector. The level sets it in code before adding the pickup.",
          "Mask 2 means the area only notices bodies on layer 2, which is just the player.",
          "Each ring only spawns what it uses: map pieces when <code>map_mode == \"pieces\"</code>, oil when <code>lantern_fuel</code> is on."],
     key="scenes/pickup.tscn, scripts/pickup.gd")

step("The memory map",
     goal="A minimap that only updates where you've been, so after a shift it shows the old maze.",
     do=["Type <code>scripts/minimap.gd</code>. It's attached to a Control in the HUD (step 39)."],
     codes=[code("scripts/minimap.gd", whole("scripts/minimap.gd"))],
     how=["<code>memory</code> maps each remembered tile to a number: 0 floor, 1 wall, 2 safe, 3 exit.",
          "Every 0.2 s it copies the <b>real</b> tiles within 4 tiles of you. Tiles you haven't revisited keep their old value, so it shows the maze as it used to be.",
          "<code>_draw()</code> paints a 2&times;2 rectangle per tile; <code>queue_redraw()</code> every frame keeps the blinking player dot moving.",
          "Easy remembers everything at the start, Medium starts blank (map pieces reveal radius 10), Hard hides the map."],
     key="scripts/minimap.gd")

step("Lantern fuel", sub="Hard",
     goal="On the last ring, the lantern shrinks over time unless you find oil.",
     do=["Type <code>set_fuel</code> in player.gd, and add <code>player.set_fuel(1.0)</code> to the level's <code>_ready</code>.",
         "Uncomment the fuel line in the level's <code>_physics_process</code>."],
     codes=[code("scripts/player.gd", funcs("scripts/player.gd", "set_fuel"))],
     how=["Fuel drains by <code>delta / 50</code> each frame: full to empty in 50 seconds.",
          "<code>lerpf(0.42, 1.0, fuel)</code> maps fuel to light size: empty is 42% of full size, never fully dark.",
          "Oil adds 0.5, and <code>clampf</code> keeps fuel between 0 and 1."],
     key="scripts/player.gd &rarr; set_fuel")

phase("Three rings, one run")

step("Generate the three rings",
     goal="Three real mazes that get bigger and harder, and can never trap you.",
     do=["Copy <code>tools/make_mazes.py</code> from the answer key and run <code>python3 tools/make_mazes.py</code>. It overwrites your test maze and writes <code>inner_ring.gd</code> and <code>the_core.gd</code>.",
         "Open the files and look. You can hand-edit any of them."],
     extra='<div class="tablewrap"><table><thead><tr><th></th><th>Outer Ring</th><th>Inner Ring</th><th>The Core</th></tr></thead><tbody>'
           '<tr><th>Size</th><td>45&times;27</td><td>49&times;29</td><td>55&times;31</td></tr>'
           '<tr><th>Monsters</th><td>1</td><td>3</td><td>6</td></tr>'
           '<tr><th>Shift groups &times; cells</th><td>2 &times; 7</td><td>4 &times; 9</td><td>4 &times; 14</td></tr>'
           '<tr><th>Extra safe rooms</th><td>2</td><td>2</td><td>1</td></tr>'
           '<tr><th>Items</th><td>none</td><td>4 map pieces</td><td>5 oil</td></tr>'
           '</tbody></table></div>',
     how=["It carves a perfect maze with a depth-first \"recursive backtracker\", then knocks out some walls to make loops (alternative routes).",
          "It places a 5&times;5 safe room in the centre, extra 3&times;3 safe rooms far apart, and the exit at the edge tile farthest from the start.",
          "For each candidate shifting wall it tests <b>every</b> on/off combination of all groups (up to 16) with a flood fill, and keeps the wall only if all floor still connects to the exit."],
     key="levels/*.gd, tools/make_mazes.py")

step("Ring to ring", milestone=True,
     goal="Reach the exit, see \"CLEARED\", and continue straight into the next ring.",
     do=["Type <code>_complete</code>, and uncomment the exit check in <code>_physics_process</code>.",
         "Compare your <code>_ready</code> with the final version below and fill in anything missing (except <code>hud.setup</code>, which comes next)."],
     codes=[code("scripts/level.gd", funcs("scripts/level.gd", "_complete")),
            code("scripts/level.gd (final _ready)", funcs("scripts/level.gd", "_ready"))],
     how=["<code>Phase.stop()</code> halts the cycle so the lights don't die during the celebration.",
          "<code>Game.next_level()</code> bumps <code>current_level</code> and reloads the <b>same</b> <code>level.tscn</code>. Its <code>_ready</code> reads the next entry of <code>LEVELS</code>.",
          "Lives carry over because they live in the <code>Game</code> autoload, which isn't freed when scenes change.",
          "<code>finished = true</code> stops <code>_physics_process</code> and phase handling from doing anything during the 1.8 s wait."],
     test="Play the Outer Ring to the exit and land in the Inner Ring with the same number of lives.",
     key="scripts/level.gd &rarr; _complete, _ready")

phase("UI and menus")

step("HUD", sub="scenes/hud.tscn",
     goal="Lives, ring name, the blackout bar, gate status, items, safe-room notice, minimap, banner and red flash.",
     do=["New Scene, root <code>CanvasLayer</code> named <code>HUD</code>, Layer 10.",
         "Build the tree below. For each node marked <b>%</b>, right-click it &rarr; <b>Access as Unique Name</b>.",
         "Positioning: select a Control and use the <b>Anchor preset</b> button in the toolbar (top left, top right, bottom left, bottom right, full rect).",
         "Labels: Font Size 9&ndash;10, Outline Size 3, Outline Color black (Theme Overrides in the Inspector). Banner: size 16, outline 5.",
         "PhaseBar: Show Percentage off, minimum height 5, Theme Overrides &rarr; Styles: Background and Fill as <b>New StyleBoxFlat</b>.",
         "Attach <code>scripts/hud.gd</code>, type it, save as <code>scenes/hud.tscn</code>. Instance it into <code>level.tscn</code> as <code>HUD</code>.",
         "Uncomment <code>@onready var hud</code>, add <code>hud.setup(self)</code> to <code>_ready</code> (before <code>Phase.start</code>), and uncomment the <code>hud.</code> lines in <code>_on_player_caught</code> and <code>_on_item_picked</code>."],
     extra=tree("HUD (CanvasLayer)  layer 10, script hud.gd\n"
                "├── TopLeft (VBoxContainer)             anchor top-left, at (8, 6)\n"
                "│   ├── %Hearts (HBoxContainer)        5 × TextureRect, ui_heart_full\n"
                "│   └── %LevelLabel (Label)\n"
                "├── TopRight (VBoxContainer)            anchor top-right, 142 px wide\n"
                "│   ├── %PhaseLabel (Label)            align right\n"
                "│   └── %PhaseBar (ProgressBar)\n"
                "├── BottomLeft (VBoxContainer)          anchor bottom-left\n"
                "│   ├── %SafeLabel (Label)             teal text\n"
                "│   ├── %ItemsLabel (Label)\n"
                "│   └── %GateLabel (Label)\n"
                "├── %MiniMap (Control)                  anchor bottom-right, script minimap.gd, mouse ignore\n"
                "├── %Banner (Label)                     anchor top-wide at 28% height, centred\n"
                "├── %Flash (ColorRect)                  full rect, transparent red, mouse ignore\n"
                "└── %PauseMenu (Control)                full rect, hidden  → step 40"),
     codes=[code("scripts/hud.gd", whole("scripts/hud.gd"))],
     how=["<code>%Name</code> finds a node marked Unique Name anywhere in the scene, so you can move nodes around without breaking paths.",
          "The fill StyleBox is duplicated in <code>_ready</code> so changing its colour per phase doesn't change the shared resource on disk.",
          "<code>Events.message</code> feeds the banner from anywhere: the level, safe rooms, the gate.",
          "The banner tween fades in, waits 1.6 s with <code>tween_interval</code>, and fades out. A new message kills the old tween first."],
     test="F5 from the level: hearts, the bar draining toward the next blackout, and the gate countdown all update.",
     key="scenes/hud.tscn, scripts/hud.gd")

step("Pause menu",
     goal="P or Esc pauses everything except the menu itself.",
     do=["Under <code>%PauseMenu</code> (full rect, Visible off): a <code>ColorRect</code> dim (black, 60% alpha, full rect), then <code>CenterContainer</code> &rarr; <code>PanelContainer</code> &rarr; <code>VBoxContainer</code> with a \"PAUSED\" Label, "
         "<code>%ResumeButton</code>, <code>%QuitButton</code> and a small help Label.",
         "The pause functions are already in hud.gd from the previous step."],
     codes=[code("scripts/hud.gd", funcs("scripts/hud.gd", "_unhandled_input", "_toggle_pause", "_quit_to_title"))],
     how=["<code>get_tree().paused = true</code> stops every node whose process mode is <b>Inherit</b> (the default): the level, monsters, player, and the Phase timer.",
          "The HUD sets <code>process_mode = PROCESS_MODE_ALWAYS</code> in <code>_ready</code>, so it keeps receiving input and can unpause.",
          "<code>_unhandled_input</code> only gets keys that no button or other UI already used, and <code>set_input_as_handled()</code> stops them going further."],
     warn=["Unpause before changing scenes (<code>_quit_to_title</code> does), or the next scene starts frozen."],
     test="Press P in the dark: monsters, timer and footsteps all stop. P again resumes.",
     key="scripts/hud.gd &rarr; _toggle_pause")

step("Title screen", sub="scenes/title.tscn",
     goal="A first screen with the knight, the demon, the rules and a Start button.",
     do=["New Scene, root <code>Control</code> named <code>Title</code>, full-rect anchors. Build the tree below.",
         "Knight and Demon: <code>AnimatedSprite2D</code>s at (250, 130) and (390, 118), Scale (3, 3), Demon flipped horizontally, both Unique Name.",
         "Attach <code>scripts/title.gd</code>, type it, save.",
         "<b>Project Settings &rarr; Application &rarr; Run &rarr; Main Scene</b>: <code>res://scenes/title.tscn</code>."],
     extra=tree("Title (Control)  full rect, script title.gd\n"
                "├── Background (ColorRect)      full rect, very dark purple\n"
                "├── %Knight (AnimatedSprite2D)\n"
                "├── %Demon (AnimatedSprite2D)\n"
                "├── %Shade (ColorRect)          full rect, transparent, mouse ignore\n"
                "└── VBox (VBoxContainer)        anchor bottom-wide\n"
                "    ├── Name (Label)            \"BLACKOUT MAZE\", size 32\n"
                "    ├── Tagline (Label)         two lines of rules\n"
                "    ├── Rings (Label)\n"
                "    ├── Buttons (HBoxContainer)\n"
                "    │   ├── %StartButton (Button)  \"Enter the maze\"\n"
                "    │   └── %Quit (Button)\n"
                "    └── Controls (Label)"),
     codes=[code("scripts/title.gd", whole("scripts/title.gd"))],
     how=["<code>start_button.pressed.connect(Game.new_run)</code> connects a signal straight to an autoload function. No extra function needed.",
          "The title teaches the core rule without words: every 4 s the screen goes dark for a moment, and only then does the demon move."],
     key="scenes/title.tscn, scripts/title.gd")

step("End screen", sub="scenes/end_screen.tscn",
     goal="\"YOU ESCAPED\" or \"CAUGHT IN THE DARK\", your time, and buttons to go again.",
     do=["New Scene, root <code>Control</code> named <code>EndScreen</code>, full rect: a dark <code>ColorRect</code> background, then "
         "<code>CenterContainer</code> &rarr; <code>VBoxContainer</code> with <code>%Headline</code>, <code>%Stats</code> and an HBox holding <code>%AgainButton</code> and <code>%TitleButton</code>.",
         "Attach <code>scripts/end_screen.gd</code>, type it, save as <code>scenes/end_screen.tscn</code>."],
     codes=[code("scripts/end_screen.gd", whole("scripts/end_screen.gd"))],
     how=["It reads everything from <code>Game</code>: <code>result</code>, <code>run_time</code>, <code>times_caught</code>.",
          "<code>\"%d:%02d\" % [t / 60, t % 60]</code> formats seconds as minutes:seconds with a leading zero."],
     test="Lose all 5 lives: the end screen says CAUGHT, and Run again starts a fresh run from the Outer Ring.",
     key="scenes/end_screen.tscn, scripts/end_screen.gd")

phase("Test, tune, ship")

step("A headless smoke test",
     goal="A script that plays the whole game by itself in seconds and reports problems.",
     do=["Create <code>tests/smoke_test.gd</code> and type it.",
         "Run it from a terminal in the project folder (adjust the Godot path):"],
     codes=[code("terminal", "/Users/bt/Downloads/Godot.app/Contents/MacOS/Godot --headless --path . --script res://tests/smoke_test.gd\n"
                 "/Users/bt/Downloads/Godot.app/Contents/MacOS/Godot --headless --path . --script res://tests/smoke_test.gd -- die", lang="sh"),
            code("tests/smoke_test.gd", whole("tests/smoke_test.gd"))],
     how=["A script that <code>extends SceneTree</code> replaces Godot's main loop. <code>_process</code> returning true quits.",
          "It speeds up the blackout timer to 0.4 s, walks in a square, runs half the time, puts a monster next to the player now and then, and teleports to the exit when the gate is open.",
          "Every 30 frames it checks that neither the player nor any monster is inside a wall.",
          "With <code>-- die</code> it keeps getting caught to test the game-over path."],
     warn=["Autoloads aren't in the tree yet during <code>_initialize()</code>, so the run starts on the first <code>_process</code> frame. The first version of this test crashed for exactly that reason."],
     test="Expected: <code>END: result=escaped</code> with <code>problems: none</code>; with <code>-- die</code>, <code>result=caught lives=0</code>.",
     key="tests/smoke_test.gd")

step("Look at it",
     goal="Screenshots of every ring in light and dark, saved automatically.",
     do=["Copy or type <code>tests/capture.gd</code>, then run it <b>without</b> <code>--headless</code> (it needs a window to render):"],
     codes=[code("terminal", "/Users/bt/Downloads/Godot.app/Contents/MacOS/Godot --path . --script res://tests/capture.gd -- ~/Desktop/shots", lang="sh"),
            code("tests/capture.gd", whole("tests/capture.gd"))],
     how=["It's a list of [frames to wait, action] pairs, run one after another.",
          "<code>root.get_viewport().get_texture().get_image().save_png(...)</code> saves exactly what's on screen.",
          "This is how the blackout got made darker: the first screenshots showed the maze faintly through it."],
     key="tests/capture.gd")

step("Play it and tune it",
     goal="Make it feel right. This is the step that makes it your game.",
     do=["Play each ring at least twice. Write down one thing that felt too easy and one that felt unfair.",
         "Change only numbers in <code>LEVELS</code> first: phase times, monster speed, hearing, when the gate shuts.",
         "Then add a twist of your own: a new monster type, a lever that freezes walls, a sprint stamina bar, a different end-screen message."],
     how=["Small changes matter: monster speed 52 vs 58 is the difference between \"I can outwalk the ogre\" and \"I must run\", and running makes noise.",
          "Rerun the smoke test after every change to catch anything you broke."])

step("Export",
     goal="A real app you can send to a friend.",
     do=["<b>Project &rarr; Export &rarr; Add&hellip; &rarr; macOS</b> (or Web).",
         "If Godot asks for export templates, click <b>Manage Export Templates &rarr; Download and Install</b>.",
         "Click <b>Export Project</b>, choose a location, done."],
     how=["The maps are <code>.gd</code> files and the art and sounds are imported resources, so everything is included automatically.",
          "Rename the project (Project Settings &rarr; Application &rarr; Config &rarr; Name) before sharing publicly; \"Maze Runner\" is someone else's name."])


# ================================================================== page

MILESTONES = [s["n"] for s in STEPS if s["milestone"]]

with open(OUT) as f:
    page = f.read()
head = page[:page.index("</style>")]
head = head[:head.index("  .key {")] if "  .key {" in head else head

css = """  .key { font: 12.5px var(--mono); color: var(--dim); }
  .key b { color: var(--type); font-weight: 500; }
  .goal { font-size: 15px; color: var(--text); }
  .body h4 { margin: 6px 0 -2px; font: 500 11px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--dim); }
  ol.do, ul.how, ul.warn { margin: 0; padding-left: 22px; display: grid; gap: 5px; }
  ol.do li::marker { color: var(--lantern); font-family: var(--mono); font-size: 12px; }
  ul.warn li::marker { color: var(--monster); }
  ul.warn li { color: var(--text); }
  pre.tree { color: var(--dim); }
  pre.tree code { color: var(--text); }
  .changed { border-left: 3px solid var(--lantern); background: var(--lantern-soft); padding: 12px 14px; border-radius: 0 4px 4px 0; font-size: 14px; }
  .changed p { margin: 0; }
  .changed ul { margin: 6px 0 0; padding-left: 18px; }
  .note ul { margin: 6px 0 0; padding-left: 18px; }
  .body { max-width: 78ch; }
  .codehead { margin-bottom: -6px; }
  .codehead span { background: var(--stone); border: 1px solid var(--wall); border-bottom: 0; border-radius: 4px 4px 0 0; padding: 3px 10px; display: inline-block; }
</style>
"""

hero = """
<div class="shell">
  <section class="hero" aria-labelledby="title">
    <p class="eyebrow">Godot 4.7 &middot; top-down &middot; <span id="stepTotal">%(total)d</span> steps</p>
    <h1 id="title">Blackout <span>Maze</span></h1>
    <p class="lede">Escape three rings of a maze in one run. <strong>Every few seconds the lights die.</strong> In the dark, purple walls shift and monsters move toward any noise you make. Each step below says exactly what to click, gives the complete code, explains how it works, and tells you how to test it.</p>

    <div class="meter" aria-live="polite">
      <div class="meter-top">
        <div class="meter-count" id="count">0 / %(total)d<small>steps done</small></div>
        <div class="actions">
          <button type="button" class="primary" id="btnNext">Go to next step</button>
          <button type="button" id="btnHide" aria-pressed="false">Hide finished</button>
          <button type="button" id="btnReset">Reset progress</button>
        </div>
      </div>
      <div class="bar"><i id="fill" style="width:0%%"></i></div>
      <div class="ticks" id="ticks" aria-hidden="true"></div>
    </div>

    <div class="note">
      <p><strong>How to use this guide.</strong> The finished game is in <code>maze-runner--platform-edition</code>. Treat it as your answer key, not your workspace.</p>
      <ul>
        <li>Build in a <b>new, empty Godot project</b> (step 1).</li>
        <li>Code shown here is the exact code from the answer key. Some steps show a function that also contains lines from later steps; the <b>Do it</b> list says which lines to comment out for now.</li>
        <li><b>Type the code instead of pasting it.</b> Read the <b>How it works</b> notes as you go. If you can explain a step out loud without looking, it's yours.</li>
        <li>Godot indents with tabs; the code here shows them as 4 spaces. Press Tab in the editor.</li>
      </ul>
    </div>
  </section>

  <div class="layout">
    <nav class="rail" id="rail" aria-label="Phases"></nav>
    <main id="main">
""" % {"total": len(STEPS)}

body = []
for i, ph in enumerate(PHASES):
    body.append('<section class="phase" id="phase-%d">' % i)
    body.append('<header><span class="pn">Phase %d</span><h2>%s</h2><span class="pc"></span></header>' % (i, ph["title"]))
    if ph["intro"]:
        body.append('<p class="intro">%s</p>' % ph["intro"])
    body.append('<ol class="steps">')
    for s in ph["steps"]:
        body.append(render_step(s))
    body.append("</ol></section>")

footer = """
    </main>
  </div>

  <footer class="help">
    <div>
      <h3>When you get stuck</h3>
      <ul>
        <li>Compare with the answer-key file named under the step.</li>
        <li>Read the red error in the Debugger panel: it names the file and line.</li>
        <li>Turn on Debug &rarr; Visible Collision Shapes to see what the engine sees.</li>
        <li>Paste your script and the error to Claude and ask for an explanation, not a fix.</li>
      </ul>
    </div>
    <div>
      <h3>References</h3>
      <ul>
        <li><a href="https://docs.godotengine.org/en/stable/">Godot docs</a>, or press F1 on any node in the editor.</li>
        <li><a href="https://0x72.itch.io/dungeontileset-ii">16x16 DungeonTileset II</a> by 0x72 (CC0).</li>
      </ul>
    </div>
    <div>
      <h3>Before you publish</h3>
      <p style="margin:0">The game's text avoids the Maze Runner names. Rename the project from "Maze Runner: Platform Edition" before sharing it publicly.</p>
    </div>
  </footer>
</div>
"""

script = page[page.index("<script>"):]
script = re.sub(r"const KEY = '[^']*';", "const KEY = 'blackoutMazeChecklist.v3';", script)
script = re.sub(r"const MILESTONES = \[[^\]]*\];", "const MILESTONES = %s;" % MILESTONES, script)

with open(OUT, "w") as f:
    f.write(head + css + hero + "\n".join(body) + footer + "\n" + script)
print("wrote", OUT, "-", len(STEPS), "steps, milestones", MILESTONES)

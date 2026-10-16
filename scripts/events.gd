extends Node
## Signal bus (autoload "Events"). Nodes talk through these without needing
## references to each other.

## The player made a sound at `pos` (running footsteps).
signal noise_made(pos: Vector2)
## A monster reached the player.
signal player_caught
## Shifting walls changed. `cells` are the tile coordinates that changed.
signal walls_shifted(cells: Array)
## The exit gate opened or closed.
signal gate_changed(is_open: bool)
## Something was picked up ("map" or "oil").
signal item_picked(kind: String, pos: Vector2)
## Short message for the HUD banner.
signal message(text: String)

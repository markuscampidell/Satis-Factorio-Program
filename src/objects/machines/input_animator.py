# objects.machines.input_animator

class InputAnimator:
    """Tracks purely-visual animations of items taking one more step in the
    belt's direction, played after the item has already been added to a
    machine's input inventory (the transport itself already happened - this
    just shows it happening). Doesn't know or care where the machine
    actually is."""

    DEFAULT_TILES_PER_SEC = 2.0

    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.animations = []

    def start(self, item, source_grid_pos, direction, tiles_per_sec=None):
        """Starts a new item sliding one tile forward, in whichever
        direction it was already traveling, timed to match the speed of
        the belt it came from."""
        entry_x = source_grid_pos[0] * self.cell_size + self.cell_size // 2
        entry_y = source_grid_pos[1] * self.cell_size + self.cell_size // 2
        dx = direction.x if direction else 0
        dy = direction.y if direction else 0
        target_x = entry_x + dx * self.cell_size
        target_y = entry_y + dy * self.cell_size

        speed = tiles_per_sec if tiles_per_sec is not None else self.DEFAULT_TILES_PER_SEC
        duration = max(1.0 / speed, 0.001)

        self.animations.append({
            "item": item,
            "start": (entry_x, entry_y),
            "end": (target_x, target_y),
            "progress": 0.0,
            "duration": duration,
        })

    def update(self, dt):
        """Moves every animation forward a bit, then throws away the ones
        that have finished."""
        if not self.animations:
            return
        for anim in self.animations:
            anim["progress"] += dt / anim["duration"]
        self.animations = [a for a in self.animations if a["progress"] < 1.0]

# objects.machines.input_animator

class InputAnimator:
    """Tracks purely-visual animations of items traveling from a belt tile
    to a machine's center, played after the item has already been added to
    the machine's input inventory (the transport itself already happened -
    this just shows it happening)."""

    DEFAULT_TILES_PER_SEC = 2.0

    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.animations = []

    def start(self, item, source_grid_pos, target_grid_pos, target_width, target_height, tiles_per_sec=None):
        entry_x = source_grid_pos[0] * self.cell_size + self.cell_size // 2
        entry_y = source_grid_pos[1] * self.cell_size + self.cell_size // 2
        target_x = target_grid_pos[0] * self.cell_size + (target_width * self.cell_size) // 2
        target_y = target_grid_pos[1] * self.cell_size + (target_height * self.cell_size) // 2

        distance = ((target_x - entry_x) ** 2 + (target_y - entry_y) ** 2) ** 0.5
        speed = tiles_per_sec if tiles_per_sec is not None else self.DEFAULT_TILES_PER_SEC
        speed_pixels_per_sec = speed * self.cell_size
        duration = max(distance / speed_pixels_per_sec, 0.001)

        self.animations.append({
            "item": item,
            "start": (entry_x, entry_y),
            "end": (target_x, target_y),
            "progress": 0.0,
            "duration": duration,
        })

    def update(self, dt):
        if not self.animations:
            return
        for anim in self.animations:
            anim["progress"] += dt / anim["duration"]
        self.animations = [a for a in self.animations if a["progress"] < 1.0]

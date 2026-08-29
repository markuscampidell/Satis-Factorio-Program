# objects.machines.splitter
from pygame.transform import rotate

from constants.itemdata import get_item_by_id
from core.vector2 import Vector2
from objects.machines.machine import Machine
from objects.item_filter import ItemFilter
from objects.filter_badge import draw_filter_badge
from game.grid import Grid


def relative_dirs(direction):
    """Left/forward/right unit vectors relative to `direction`. A free
    function (not just a Splitter method) so ghost_machine_renderer's
    placement-preview stub can share this geometry without needing a real
    Splitter instance (which would load its sprite from disk just to
    preview a rotation).

    Screen space has y increasing downward, so the usual math rotation
    (-dy, dx) for "90 degrees counter-clockwise" actually lands on the
    player's *right* on screen, not their left - e.g. facing (1, 0) (east),
    (-dy, dx) = (0, 1) is south, which is your right hand when facing east,
    not your left. (dy, -dx) is the one that lands north/left. Swapped
    accordingly so index 0 is really left and index 2 is really right."""
    dx, dy = float(direction.x), float(direction.y)
    return [
        Vector2(dy, -dx),  # left
        Vector2(dx, dy),   # forward
        Vector2(-dy, dx),  # right
    ]


class Splitter(Machine):
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = "src/assets/sprites/machines/splitter.png"
    BUILD_COST = {"iron_ingot": 4}
    SAVE_TYPE = "splitter"

    DEFAULT_TILES_PER_SEC = 2.0

    def __init__(self, grid_pos=(0,0), direction=None, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)

        # Rotation / direction
        self.direction = direction or Vector2(1, 0)
        self.rotation_angle = 0
        self._relative_dirs = relative_dirs(self.direction)

        # Image
        self.image_original = self.image.copy()

        # Item handling
        self.current_item = None

        self.current_output_index = 0
        self.item_progress = 0.0
        self.current_item_speed = self.DEFAULT_TILES_PER_SEC

        # One filter per output side, index-aligned with _relative_dirs
        # (0=left, 1=forward, 2=right). relative_dirs() is always
        # recomputed relative to the splitter's *current* facing, so this
        # alignment survives rotate() without any extra bookkeeping - slot 0
        # always means "my current left", rotated or not.
        self.output_filters = [ItemFilter(), ItemFilter(), ItemFilter()]

    def update(self, dt, belt_map, machine_map=None):
        if not self.current_item:
            self.item_progress = 0.0
            return

        self.item_progress += self.current_item_speed * dt

        if self.item_progress >= 1.0:
            moved = self.push_item(belt_map, machine_map)
            if moved:
                self.item_progress = 0.0
            else:
                self.item_progress = 1.0

    def push_item(self, belt_map, machine_map=None):
        if not self.current_item:
            return False

        machine_map = machine_map or {}
        relative_dirs_list = self._get_relative_dirs()
        num_dirs = len(relative_dirs_list)
        item_id = self.current_item.item_id

        for _ in range(num_dirs):
            idx = self.current_output_index % num_dirs
            direction = relative_dirs_list[idx]
            side_filter = self.output_filters[idx]
            next_tile = (self.grid_pos[0] + int(direction.x), self.grid_pos[1] + int(direction.y))
            seg = belt_map.get(next_tile)

            if seg is not None:
                if (seg.item is None and direction != -seg.direction
                        and side_filter.accepts(item_id) and seg.accepts_item(item_id)):
                    seg.item = self.current_item
                    seg.item_progress = 0.0

                    # The item enters this belt from the splitter direction
                    seg.current_incoming_direction = direction

                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True
            else:
                machine = machine_map.get(next_tile)
                accepted = (machine.try_receive_item(self.current_item, self.grid_pos, direction=direction, source_speed=self.current_item_speed)
                            if machine and side_filter.accepts(item_id) else False)

                if accepted:
                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True

            self.current_output_index = (self.current_output_index + 1) % num_dirs

        return False

    def _get_relative_dirs(self):
        return self._relative_dirs

    def draw(self, screen, camera):
        if not self.image:
            return
        super().draw(screen, camera)

        center_x = self.grid_pos[0] * self.cell_size + self.cell_size / 2 - camera.x
        center_y = self.grid_pos[1] * self.cell_size + self.cell_size / 2 - camera.y

        for direction, output_filter in zip(self._get_relative_dirs(), self.output_filters):
            if not output_filter.enabled:
                continue
            edge_x = center_x + direction.x * (self.cell_size / 2 - 6)
            edge_y = center_y + direction.y * (self.cell_size / 2 - 6)
            draw_filter_badge(screen, (edge_x, edge_y), size=9)

    def try_receive_item(self, item, source_grid_pos, direction=None, source_speed=None):
        """Shared Machine.try_receive_item contract - unlike ProducingMachine
        /Storage, a splitter only accepts from directly behind its own
        facing direction, and only holds one item at a time."""
        if self.current_item is not None:
            return False

        if direction != self.direction:
            return False

        self.current_item = item
        self.current_incoming_direction = direction
        self.item_progress = 0.0
        self.current_item_speed = source_speed if source_speed is not None else self.DEFAULT_TILES_PER_SEC

        return True

    def get_refund_items(self):
        refund = super().get_refund_items()
        if self.current_item:
            item_id = self.current_item.item_id if hasattr(self.current_item, "item_id") else self.current_item
            refund[item_id] = refund.get(item_id, 0) + 1
        return refund

    def to_dict(self):
        data = super().to_dict()
        data["direction"] = [self.direction.x, self.direction.y]
        data["current_item"] = self.current_item.item_id if self.current_item else None
        data["output_filters"] = [f.to_dict() for f in self.output_filters]
        return data

    @classmethod
    def from_dict(cls, data):
        m = cls(grid_pos=tuple(data["grid_pos"]), direction=Vector2(*data["direction"]))
        m.current_item = get_item_by_id(data["current_item"]) if data["current_item"] else None
        # try_receive_item() only ever accepts direction == self.direction
        # and sets current_incoming_direction to it - it's otherwise never
        # initialized, so a loaded splitter holding an item needs it set
        # here too (world_renderer reads it unconditionally when drawing).
        m.current_incoming_direction = m.direction
        m.item_progress = 0.0
        m.current_output_index = 0
        m.current_item_speed = cls.DEFAULT_TILES_PER_SEC
        m.output_filters = [ItemFilter.from_dict(d) for d in data.get("output_filters", [{}, {}, {}])]
        return m

    def rotate(self):
        self.direction = Vector2(-self.direction.y, self.direction.x)
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.image = rotate(self.image_original, -self.rotation_angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect(center=old_center)
        self._relative_dirs = relative_dirs(self.direction)
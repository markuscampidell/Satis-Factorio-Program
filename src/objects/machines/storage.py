# objects.machines.storage
from entities.inventory import Inventory
from objects.machines.machine import Machine
from objects.machines.input_animator import InputAnimator
from objects.machines.machine_output_pusher import push_storage_output
from game.grid import Grid
from constants.itemdata import get_item_by_id


class Storage(Machine):
    """A 2x2 storage building: a single flat inventory that belts and
    splitters can both drop any item into and pull items back out of (any
    side is both a valid input and a valid output"""

    WIDTH = 2
    HEIGHT = 2
    SPRITE_PATH = "src/assets/sprites/machines/storage.png"
    BUILD_COST = {"iron_ingot": 10}
    SAVE_TYPE = "storage"

    INVENTORY_WIDTH = 8
    INVENTORY_HEIGHT = 6

    def __init__(self, grid_pos, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)
        self.inventory = Inventory(self.INVENTORY_WIDTH, self.INVENTORY_HEIGHT)
        self.input_animator = InputAnimator(cell_size)

    def update(self, dt, belt_map=None, machine_map=None):
        self.input_animator.update(dt)
        push_storage_output(self, belt_map or {})

    def try_receive_item(self, item, source_grid_pos, direction=None, source_speed=None):
        """Same shared Machine.try_receive_item signature as
        ProducingMachine - accepts from any side, though `direction` still
        steers which way the input animation slides. Unlike a recipe
        machine, any item is accepted as long as there's room for it."""
        if not self.inventory.try_add_items(item, 1):
            return False

        self.input_animator.start(item, source_grid_pos, direction, tiles_per_sec=source_speed)
        return True

    def draw(self, screen, camera):
        super().draw(screen, camera)
        self._draw_top_item(screen, camera)

    def _draw_top_item(self, screen, camera):
        """Draws an icon of whichever item this storage is currently
        holding the most of, centered on top of it - a quick at-a-glance
        hint of what's inside without opening it."""
        contents = self.inventory.contents_as_dict()
        if not contents:
            return

        top_item_id = max(contents, key=contents.get)
        item_obj = get_item_by_id(top_item_id)
        if not item_obj or not item_obj.sprite:
            return

        center_x = self.grid_pos[0] * self.cell_size + (self.WIDTH * self.cell_size) // 2 - camera.x
        center_y = self.grid_pos[1] * self.cell_size + (self.HEIGHT * self.cell_size) // 2 - camera.y
        img = item_obj.sprite
        screen.blit(img, (center_x - img.get_width() // 2, center_y - img.get_height() // 2))

    def get_refund_items(self):
        """Also refunds everything currently stored inside it."""
        refund = super().get_refund_items()
        for item_id, amount in self.inventory.contents_as_dict().items():
            refund[item_id] = refund.get(item_id, 0) + amount
        return refund

    def to_dict(self):
        data = super().to_dict()
        data["slots"] = self.inventory.slots
        return data

    @classmethod
    def from_dict(cls, data):
        m = cls(grid_pos=tuple(data["grid_pos"]))
        m.inventory.slots = data["slots"]
        return m

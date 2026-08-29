# objects.machines.storage
from entities.inventory import Inventory
from objects.machines.machine import Machine
from objects.machines.input_animator import InputAnimator
from objects.machines.machine_output_pusher import push_storage_output
from game.grid import Grid


class Storage(Machine):
    """A 1x1 storage building: a single flat inventory that belts and
    splitters can both drop any item into and pull items back out of (any
    side is both a valid input and a valid output, exactly like a
    producing machine) - no recipe, no processing, just holds items until
    something (a belt, or the player) takes them."""

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
        push_storage_output(self, belt_map or {}, machine_map or {})

    def try_receive_item(self, item, source_grid_pos, direction=None, source_speed=None):
        """Same shared Machine.try_receive_item signature as
        ProducingMachine - accepts from any side, so `direction` is
        unused. Unlike a recipe machine, any item is accepted as long as
        there's room for it."""
        if not self.inventory.try_add_items(item, 1):
            return False

        self.input_animator.start(item, source_grid_pos, self.grid_pos, self.WIDTH, self.HEIGHT, tiles_per_sec=source_speed)
        return True

    def get_refund_items(self):
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

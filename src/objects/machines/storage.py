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

    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = "src/assets/sprites/machines/storage.png"
    BUILD_COST = {"iron_ingot": 10}

    INVENTORY_WIDTH = 8
    INVENTORY_HEIGHT = 6

    def __init__(self, grid_pos, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)
        self.cell_size = cell_size
        self.inventory = Inventory(self.INVENTORY_WIDTH, self.INVENTORY_HEIGHT)
        self.input_animator = InputAnimator(cell_size)

    def update(self, dt, belt_map=None, machine_map=None):
        self.input_animator.update(dt)
        push_storage_output(self, belt_map or {}, machine_map or {})

    def try_receive_item(self, item, source_grid_pos, source_speed=None):
        """Same entry point/signature as ProducingMachine.try_receive_item -
        belts and splitters call this generically. Unlike a recipe machine,
        any item is accepted as long as there's room for it."""
        if not self.inventory.try_add_items(item, 1):
            return False

        self.input_animator.start(item, source_grid_pos, self.grid_pos, self.WIDTH, self.HEIGHT, tiles_per_sec=source_speed)
        return True

    def get_refund_items(self):
        refund = super().get_refund_items()
        for row in self.inventory.slots:
            for slot in row:
                if slot:
                    refund[slot["item"]] = refund.get(slot["item"], 0) + slot["amount"]
        return refund

    def draw(self, screen, camera):
        if not self.image:
            return
        pixel_x = self.grid_pos[0] * self.cell_size - camera.x
        pixel_y = self.grid_pos[1] * self.cell_size - camera.y
        screen.blit(self.image, (pixel_x, pixel_y))

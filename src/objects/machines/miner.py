# objects.machines.miner
from objects.machines.producing_machine import ProducingMachine
from constants.recipes import Recipe


class Miner(ProducingMachine):
    """A machine that must be placed directly on an ore tile and produces
    that tile's ore for free, forever - no recipe inputs, since the ore
    comes from the ground rather than a belt. Built on ProducingMachine
    rather than a new base class: a Recipe with empty inputs already
    behaves exactly like free production with no changes needed there
    (can_process()'s input check is a no-op over an empty dict, and
    try_receive_item() correctly always rejects since input_inventories
    ends up empty too)."""

    WIDTH = 2
    HEIGHT = 3
    SPRITE_PATH = "src/assets/sprites/machines/miner.png"
    BUILD_COST = {"iron_ingot": 5}
    SAVE_TYPE = "miner"

    MINE_TIME = 2.0  # seconds per ore produced

    def __init__(self, grid_pos, ore_item_id):
        self.ore_item_id = ore_item_id
        # Deliberately not registered in constants.recipes' global lists -
        # which ore a Miner produces depends on the tile it's standing on,
        # not a fixed catalog entry, so get_recipe_by_id() was never meant
        # to find this. to_dict()/from_dict() save/restore ore_item_id
        # directly instead of round-tripping through a recipe_id lookup.
        recipe = Recipe(f"mine_{ore_item_id}", f"Mine {ore_item_id}", {}, {ore_item_id: 1}, self.MINE_TIME)
        super().__init__(grid_pos, recipe)

    def to_dict(self):
        data = super().to_dict()
        data["ore_item_id"] = self.ore_item_id
        return data

    @classmethod
    def from_dict(cls, data):
        m = cls(tuple(data["grid_pos"]), data["ore_item_id"])
        for item_id, slots in data["output_inventories"].items():
            m.output_inventories[item_id].slots = slots
        return m

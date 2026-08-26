# objects.machines.smelter
from objects.machines.producing_machine import ProducingMachine
from constants.recipes import smelter_recipes

class Smelter(ProducingMachine):
    WIDTH = 3
    HEIGHT = 2
    SPRITE_PATH = "src/assets/sprites/machines/smelter.png"
    BUILD_COST = {"iron_ingot": 2, "copper_ingot": 1}
    SAVE_TYPE = "smelter"

    def __init__(self, grid_pos):
        self.recipes = smelter_recipes
        super().__init__(grid_pos, self.recipes[0])
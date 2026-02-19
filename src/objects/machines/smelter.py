from objects.machines.producing_machine import ProducingMachine
from constants.recipes import smelter_recipes

class Smelter(ProducingMachine):
    SPRITE_PATH = "src/assets/sprites/machines/smelter.png"
    BUILD_COST = {"iron_ingot": 2, "copper_ingot": 1}
    SIZE = 96
    
    def __init__(self, pos):
        self.recipes = smelter_recipes
        super().__init__(pos, self.recipes[0])
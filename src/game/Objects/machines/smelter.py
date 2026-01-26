from game.Objects.machines.machine import Machine
from game.Objects.machines.recipes import smelter_recipes

class Smelter(Machine):
    SPRITE_PATH = "assets/Sprites/smelter.png"
    BUILD_COST = {"iron_ingot": 2, "copper_ingot": 1}
    SIZE = 96
    
    def __init__(self, pos):
        self.recipes = smelter_recipes
        super().__init__(pos, self.recipes[0])
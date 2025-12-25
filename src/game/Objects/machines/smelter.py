from game.Objects.machines.machine import Machine
from game.Objects.machines.recipes import smelter_recipes

class Smelter(Machine):
    SPRITE_PATH = "assets/Sprites/smelter.png"

    def __init__(self, pos):
        self.recipes = smelter_recipes
        super().__init__(pos, self.recipes[0])
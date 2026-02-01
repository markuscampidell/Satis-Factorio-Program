from game.Objects.machines.producing_machine import ProducingMachine
from game.Objects.machines.recipes import foundry_recipes

class Foundry(ProducingMachine):
    SPRITE_PATH = "assets/Sprites/machines/foundry.png"
    BUILD_COST = {"iron_ingot": 3, "coal": 2}
    SIZE = 96

    def __init__(self, pos):
        self.recipes = foundry_recipes
        super().__init__(pos, foundry_recipes[0])
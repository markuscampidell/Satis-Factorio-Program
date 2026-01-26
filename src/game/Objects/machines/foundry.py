from game.Objects.machines.machine import Machine
from game.Objects.machines.recipes import foundry_recipes
from entities.inventory import Inventory

class Foundry(Machine):
    SPRITE_PATH = "assets/Sprites/foundry.png"
    BUILD_COST = {"iron_ingot": 3, "coal": 2}
    SIZE = 96

    def __init__(self, pos):
        self.recipes = foundry_recipes
        super().__init__(pos, foundry_recipes[0])
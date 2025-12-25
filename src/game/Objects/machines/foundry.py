from game.Objects.machines.machine import Machine
from game.Objects.machines.recipes import foundry_recipes

class Foundry(Machine):
    SPRITE_PATH = "assets/Sprites/foundry.png"

    def __init__(self, pos):
        self.recipes = foundry_recipes
        super().__init__(pos, foundry_recipes[0])
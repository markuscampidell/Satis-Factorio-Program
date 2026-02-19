from objects.machines.producing_machine import ProducingMachine
from constants.recipes import assembler_recipes

class Assembler(ProducingMachine):
    SPRITE_PATH = "src/assets/sprites/machines/assembler.png"
    BUILD_COST = {"iron_ingot": 3}
    SIZE = 96

    def __init__(self, pos):
        self.recipes = assembler_recipes
        super().__init__(pos, assembler_recipes[0])
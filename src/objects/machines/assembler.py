# objects.machines.assembler
from objects.machines.producing_machine import ProducingMachine
from constants.recipes import assembler_recipes

class Assembler(ProducingMachine):
    """A machine that turns simple parts into more complex ones, using
    whichever assembler recipe is currently selected."""

    SPRITE_PATH = "src/assets/sprites/machines/assembler.png"

    BUILD_COST = {"iron_ingot": 3}

    WIDTH = 3
    HEIGHT = 3
    SAVE_TYPE = "assembler"

    def __init__(self, grid_pos):
        self.recipes = assembler_recipes
        super().__init__(grid_pos, assembler_recipes[0])
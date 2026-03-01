# objects.machines.smelter
import pygame as py

from objects.machines.producing_machine import ProducingMachine
from constants.recipes import smelter_recipes
from game.grid import Grid

class Smelter(ProducingMachine):
    WIDTH = 3
    HEIGHT = 3
    SPRITE_PATH = "src/assets/sprites/machines/smelter.png"
    BUILD_COST = {"iron_ingot": 2, "copper_ingot": 1}

    def __init__(self, grid_pos):
        self.recipes = smelter_recipes
        super().__init__(grid_pos, self.recipes[0])
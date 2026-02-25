import pygame as py
from sys import exit

from core.camera import Camera
from game.grid import Grid

from entities.player import Player

from constants.itemdata import ITEMS


from ui.producing_machine_ui import ProducingMachineUI
from ui.player_inventory_ui import PlayerInventoryUI

from objects.machines.smelter import Smelter
from objects.machines.splitter import Splitter
from objects.machines.producing_machine import ProducingMachine

from systems.machines.machine_system import MachineSystem
from systems.machine_interaction_system import MachineInteractionSystem

from systems.input_system import InputSystem
from systems.build_system import BuildSystem
from systems.render_system import RenderSystem

from systems.conveyors.beltsystem import BeltSystem
from systems.conveyors.beltspritemanager import BeltSpriteManager
from systems.conveyors.ghost_belt_renderer import GhostBeltRenderer
from systems.conveyors.ghost_belt_placer import GhostBeltPlacer

from ui.hand_crafting_ui import HandCraftingUI
from constants.recipes import smelter_recipes, assembler_recipes


from game.world import World


class Game:
    def __init__(self):
        py.init()

        self._init_window()
        self._init_graphics()
        self._init_build_state()
        self._init_overlays()

        self.create_starting_objects()

    def _init_window(self):
        self.start_screen_width, self.start_screen_height = 1920, 1080
        self.screen = py.display.set_mode((self.start_screen_width, self.start_screen_height), py.RESIZABLE)
        self.clock = py.time.Clock()

    def _init_graphics(self):
        for item in ITEMS: item.load_sprite()

        self.font = py.font.SysFont("Arial", 32)
        self.title_font_surface = self.font.render("Satis Factorio Program", True, "#000000")

        self.belt_sprite_manager = BeltSpriteManager()
        self.belt_sprite_manager.load_images()

        self.ghost_belt_renderer = GhostBeltRenderer(self.belt_sprite_manager)

        self.image_cache = {}

    def _init_build_state(self):
        # Placement state
        self.just_placed_machine = False
        self.selected_machine_class = Smelter
        self.selected_belt_type = "basic"
        self.splitter_rotation_steps = 0
        self.build_mode = None
        self.placing_belt = False

        # Options
        self.draw_grid = True
        self.show_items_player_inventory = False
        self.explain_recipe_machine = False
        self.explain_recipe_hand_crafting = True

        self.hovered_delete_target = None

    def _init_overlays(self):
        self.overlay_none = py.Surface((self.start_screen_width, self.start_screen_height), py.SRCALPHA)

        self.overlay_build_place = py.Surface((self.start_screen_width, self.start_screen_height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))

        self.overlay_delete = py.Surface((self.start_screen_width, self.start_screen_height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))

    def create_starting_objects(self):
        self._init_world()
        self._init_ui()
        self._init_systems()
        self._init_recipes()
        self._init_debug_items()

    def _init_world(self):
        self.camera = Camera(self.start_screen_width, self.start_screen_height)
        self.grid = Grid()

        self.player = Player(self.grid.CELL_SIZE)
        self.world = World(self.player, self.grid.CELL_SIZE)

        self.camera.x = self.player.rect.centerx - self.camera.screen_width // 2
        self.camera.y = self.player.rect.centery - self.camera.screen_height // 2

    def _init_ui(self):
        self.player_inventory_ui = PlayerInventoryUI(
            self.player, 
            get_screen_size=lambda: (self.camera.screen_width, self.camera.screen_height))

        self.machine_ui = ProducingMachineUI(
            self.camera.screen_width,
            self.camera.screen_height,
            self.world,
            self.camera,
            self.player,
            self.player_inventory_ui,
            self.screen)

        self.crafting_ui = HandCraftingUI(
            self.player,
            get_screen_size=lambda: (self.camera.screen_width, self.camera.screen_height))

    def _init_systems(self):
        self.build_system = BuildSystem(self)
        self.input_system = InputSystem(self)
        self.render_system = RenderSystem(self)

        self.belts = BeltSystem(
            self.world,
            self.grid,
            self.player,
            self.ghost_belt_renderer)

        self.ghost_placer = GhostBeltPlacer(
            self.world,
            self.player,
            self.grid,
            self.belts,
            self.ghost_belt_renderer,
            self.camera,
            self.screen)

        self.machine_placer = MachineSystem(
            self.world,
            self.player,
            self.grid,
            self.camera,
            self.screen,
            self.machine_ui,
            self)

        self.machine_interaction_system = MachineInteractionSystem(self)

    def _init_recipes(self):
        self.player.handcrafting.recipes = (smelter_recipes + assembler_recipes)

    def _init_debug_items(self):
        self._cheat_add_items("iron_ingot", 1000)
        self._cheat_add_items("coal", 100)
        self._cheat_add_items("copper_ore", 2)
        self._cheat_add_items("copper_ingot", 1000)
    
    def run(self):
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    exit()

                if event.type == py.VIDEORESIZE:
                    self.screen = py.display.set_mode((event.w, event.h), py.RESIZABLE)
                    self._update_screen_size(event.w, event.h)

                if event.type == py.MOUSEBUTTONUP and event.button == 1: 
                    self.just_placed_machine = False
                
                self._handle_event(event)

            self.update()

            self.render_system.draw(self.screen)

            py.display.flip()

    def _handle_event(self, event):
        self.input_system.handle_keys(event)
        self.input_system.handle_mouse(event)

        self.build_system.handle_placement(event)

        self.machine_ui.handle_event(event, self.just_placed_machine, self.build_mode == "building",)

        self.machine_interaction_system.handle_click(event, self.just_placed_machine)

    def update(self):
        delta_time = self.clock.tick(60) / 1000
        self.player.update(self.world.machines, delta_time)
        self.camera.update(self.player)

        if self.crafting_ui.open:
            self.crafting_ui.update(delta_time)

        cell = self.grid.CELL_SIZE
        for segment in self.world.belt_segments:
            segment.update(self.world.belt_map, self.world.machines, cell, delta_time)

        for machine in self.world.machines:
            if isinstance(machine, ProducingMachine):
                machine.update(delta_time)
            elif isinstance(machine, Splitter):
                machine.update(delta_time, self.grid.CELL_SIZE, self.world.belt_map)

        self.build_system.update_hovered_delete_target()
    
    def _update_screen_size(self, width, height):
        self.camera.screen_width = width
        self.camera.screen_height = height
        self.grid.update_screen_size(width, height)

        # Update overlay surfaces
        self.overlay_none = py.Surface((width, height), py.SRCALPHA)
        self.overlay_build_place = py.Surface((width, height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))
        self.overlay_delete = py.Surface((width, height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))


    def _cheat_add_items(self, item_id, amount):
        self.player.inventory.try_add_items(item_id, amount)
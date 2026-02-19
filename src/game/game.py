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

from systems.machines.machine_placer import MachinePlacer

from systems.machine_interaction_system import MachineInteractionSystem
from systems.input_system import InputSystem
from systems.build_system import BuildSystem
from systems.render_system import RenderSystem

from systems.conveyors.beltsystem import BeltSystem
from systems.conveyors.beltspritemanager import BeltSpriteManager
from systems.conveyors.ghost_belt_renderer import GhostBeltRenderer


from game.world import World


class Game:
    def __init__(self):
        # Initialize Pygame and create the window
        py.init()
        self.screen_width, self.screen_height = 1920, 1080
        self.screen = py.display.set_mode((self.screen_width, self.screen_height))
        self.clock = py.time.Clock()

        # Fonts
        self.font = py.font.SysFont("Arial", 32)
        self.title_font_surface = self.font.render("Satis Factorio Program", True, "#000000")

        # Game objects
        self.belt_sprite_manager = BeltSpriteManager()
        self.belt_sprite_manager.load_images()
        self.ghost_belt_renderer = GhostBeltRenderer(self.belt_sprite_manager)
        
        # Cache for scaled belt segment images to improve performance
        self.image_cache = {}

        # Build/placement state
        self.just_placed_machine = False
        self.selected_machine_class = Smelter
        self.selected_belt_type = "basic"
        self.splitter_rotation_steps = 0
        self.build_mode = None

        # For handling temporary pause of build mode when opening inventory
        self.paused_mode = None

        # For detecting hovered object in delete mode
        self.hovered_delete_target = None

        # Overlays for build/delete modes
        self.overlay_none = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_build_place = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))
        self.overlay_delete = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))

        self.create_starting_objects()
    
    def create_starting_objects(self):
        self.camera = Camera(self.screen_width, self.screen_height)
        self.grid = Grid(self.screen_width, self.screen_height)

        self.player = Player(self.grid.CELL_SIZE)

        # World
        self.world = World(self.player)

        # Center camera on player
        self.camera.x = self.player.rect.centerx - self.screen_width // 2
        self.camera.y = self.player.rect.centery - self.screen_height // 2

        # UIs
        self.player_inventory_ui = PlayerInventoryUI(self.player)
        self.machine_ui = ProducingMachineUI(self.screen_width, self.screen_height, self.world, self.camera, self.player, self.player_inventory_ui, self.screen)
        

        # Systems
        self.machine_interaction_system = MachineInteractionSystem(self)
        self.build_system = BuildSystem(self)
        self.input_system = InputSystem(self)
        self.render_system = RenderSystem(self)
        self.belts = BeltSystem(self.world, self.grid, self.player, self.screen, self.camera, self.screen_width, self.screen_height, self.ghost_belt_renderer)
        self.machine_placer = MachinePlacer(self.world, self.player, self.grid, self.camera, self.screen_width, self.screen_height, self.screen, self.machine_ui, self)

        # This is just for testing
        self._cheat_add_items("iron_ingot", 1000)
        self._cheat_add_items("coal", 100)
        self._cheat_add_items("copper_ingot", 1000)
    
    def run(self):
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    exit()

                if event.type == py.MOUSEBUTTONUP and event.button == 1: 
                    self.just_placed_machine = False
                
                self.input_system.handle_keys(event)
                self.input_system.handle_mouse(event)

                self.build_system.handle_placement(event)

                self.machine_ui.handle_event(event, self.just_placed_machine, self.build_mode == "building",)

            self.machine_interaction_system.handle_click(event)

            self.update()
            
            self.screen.fill("#987171")

            if self.build_mode is not None: self.grid.draw(self.screen, self.camera)

            if self.build_mode == "building" and self.selected_machine_class is not None:
                self.machine_placer.ghost_machine(self.selected_machine_class, self.build_mode, self.splitter_rotation_steps)
                self.belts.ghost_conveyor_belt(self.selected_machine_class, self.placing_belt, self.selected_belt_type)

            self.render_system.draw(self.screen)

            py.display.flip()

    def update(self):
        delta_time = self.clock.tick(60) / 1000
        self.player.update(self.world.machines)
        self.camera.update(self.player, self.screen_width, self.screen_height)

        cell = self.grid.CELL_SIZE
        for segment in self.world.belt_segments:
            segment.update(self.world.belt_map, self.world.machines, cell, delta_time)

        for machine in self.world.machines:
            if isinstance(machine, ProducingMachine):
                machine.update(delta_time)
            elif isinstance(machine, Splitter):
                machine.update(delta_time, self.grid.CELL_SIZE, self.world.belt_map)

        self.build_system.update_hovered_delete_target()


    def _cheat_add_items(self, item_id, amount):
        self.player.inventory.try_add_items(item_id, amount)

game = Game()
for item in ITEMS: item.load_sprite()
game.run()
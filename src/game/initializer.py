# game.initializer
import pygame as py

from game.game_context import GameContext

from game.grid import Grid
from core.camera import Camera
from entities.player import Player
from game.world import World

from constants.itemdata import ITEMS
from constants.recipes import smelter_recipes, assembler_recipes

# UI
from ui.producing_machine_ui import ProducingMachineUI
from ui.player_inventory_ui import PlayerInventoryUI
from ui.hand_crafting_ui import HandCraftingUI
from ui.ui_manager import UIManager

# Graphics
from systems.conveyors.belt_segment_sprite_manager import BeltSegmentSpriteManager
from systems.conveyors.ghost_belt_renderer import GhostBeltRenderer

# Systems
from systems.machines.machine_system import MachineSystem
from systems.machine_interaction_system import MachineInteractionSystem
from systems.input_system import InputSystem
from systems.build_system import BuildSystem
from systems.render_system import RenderSystem
from systems.conveyors.belt_system import BeltSystem
from systems.conveyors.belt_ghost_preview_controller import BeltGhostPreviewController

class Initializer:
    @staticmethod
    def init_game(window_size=(1280, 720)):
        screen = py.display.set_mode(window_size, py.RESIZABLE)
        clock = py.time.Clock()
        screen_width, screen_height = window_size

        grid = Grid()
        camera = Camera(screen_width, screen_height)
        player = Player(grid.CELL_SIZE)
        world = World(player, grid.CELL_SIZE)

        camera.x = player.rect.centerx - camera.screen_width // 2
        camera.y = player.rect.centery - camera.screen_height // 2

        font = py.font.SysFont("Arial", 20)
        title_font_surface = font.render("Satis Factorio Program", True, "#000000")

        belt_sprite_manager = BeltSegmentSpriteManager()
        belt_sprite_manager.load_images()

        ghost_belt_renderer = GhostBeltRenderer(belt_sprite_manager, grid.CELL_SIZE)

        for item in ITEMS: item.load_sprite()

        player_inventory_ui = PlayerInventoryUI(player, get_screen_size=lambda: (camera.screen_width, camera.screen_height))
        machine_ui = ProducingMachineUI(camera, world, player, player_inventory_ui, screen)
        hand_crafting_ui = HandCraftingUI(player, get_screen_size=lambda: (camera.screen_width, camera.screen_height))

        ui_manager = UIManager({"player_inventory": player_inventory_ui,
                                "machine": machine_ui,
                                "hand_crafting": hand_crafting_ui})

        machine_system = MachineSystem(world, player, camera, grid, screen)
        belt_system = BeltSystem(world, grid, player, ghost_belt_renderer)

        build_system = BuildSystem(world, player, camera, grid, belt_system, machine_system, machine_ui, player_inventory_ui)
        input_system = InputSystem(build_system, ui_manager, hand_crafting_ui, machine_ui, player_inventory_ui, belt_system, machine_system)
        belt_ghost_preview_controller = BeltGhostPreviewController(world, player, grid, belt_system, ghost_belt_renderer, camera, screen)
        render_system = RenderSystem(world, player, camera, grid, build_system, belt_sprite_manager, machine_ui, player_inventory_ui, hand_crafting_ui, machine_system, belt_ghost_preview_controller, belt_system)
        machine_interaction_system = MachineInteractionSystem(world, build_system, machine_ui, camera)

        player.handcrafting.recipes = smelter_recipes + assembler_recipes

        return GameContext(screen=screen,
                           clock=clock,

                           grid=grid,
                           camera=camera,
                           world=world,

                           player=player,
                           player_inventory_ui=player_inventory_ui,
                           hand_crafting_ui=hand_crafting_ui,

                           font=font,
                           title_font_surface=title_font_surface,

                           belt_sprite_manager=belt_sprite_manager,
                           ghost_belt_renderer=ghost_belt_renderer,
                           belt_system=belt_system,
                           belt_ghost_preview_controller=belt_ghost_preview_controller,

                           ui_manager=ui_manager,

                           build_system=build_system,
                           input_system=input_system,
                           render_system=render_system,

                           machine_system=machine_system,
                           machine_ui=machine_ui,
                           machine_interaction_system=machine_interaction_system)
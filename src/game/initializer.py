# game.initializer
import pygame as py

from game.game_context import GameContext

from game.grid import Grid
from core.camera import Camera
from entities.player import Player
from game.world import World

from constants.itemdata import ITEMS

# UI
from ui.producing_machine_ui import ProducingMachineUI
from ui.machine_ui_renderer import MachineUIRenderer
from ui.player_inventory_ui import PlayerInventoryUI
from ui.hand_crafting_ui import HandCraftingUI
from ui.hand_crafting_renderer import HandCraftingRenderer
from ui.game_menu_bar import GameMenuBar, GameMenuBarRenderer
from ui.storage_ui import StorageUI
from ui.storage_ui_renderer import StorageUIRenderer
from ui.belt_filter_ui import BeltFilterUI
from ui.belt_filter_ui_renderer import BeltFilterUIRenderer
from ui.splitter_filter_ui import SplitterFilterUI
from ui.splitter_filter_ui_renderer import SplitterFilterUIRenderer
from ui.ui_manager import UIManager

# Graphics
from systems.conveyors.belt_segment_sprite_manager import BeltSegmentSpriteManager
from systems.conveyors.ghost_belt_renderer import GhostBeltRenderer

# Systems
from systems.machines.machine_system import MachineSystem
from systems.machine_interaction_system import MachineInteractionSystem
from systems.input_system import InputSystem
from systems.build_system import BuildSystem

from systems.rendering.render_system import RenderSystem
from systems.rendering.world_renderer import WorldRenderer
from systems.rendering.item_renderer import ItemRenderer
from systems.rendering.ui_renderer import UiRenderer
from systems.rendering.build_mode_renderer import BuildModeRenderer
from systems.rendering.cursor_renderer import CursorRenderer
from systems.rendering.ghost_machine_renderer import GhostMachineRenderer

from systems.conveyors.belt_system import BeltSystem
from systems.conveyors.belt_ghost_preview_controller import BeltGhostPreviewController

MIN_SCREEN_SIZE = (1100, 700)

class Initializer:
    @staticmethod
    def init_game(window_size=(1280, 720), screen=None):
        window_size = (
            max(window_size[0], MIN_SCREEN_SIZE[0]),
            max(window_size[1], MIN_SCREEN_SIZE[1])
        )
        if screen is None:
            screen = py.display.set_mode(window_size, py.RESIZABLE)
        clock = py.time.Clock()
        # If an existing screen was passed in, its actual live size (which
        # may differ from the window_size default if it was resized before
        # this call) is authoritative, not the requested window_size.
        screen_width, screen_height = screen.get_size()

        grid = Grid()
        camera = Camera(screen_width, screen_height)
        player = Player(grid.CELL_SIZE)
        world = World(player, grid.CELL_SIZE)

        camera.center_on(player.rect)

        font = py.font.SysFont("Arial", 20)
        title_font_surface = font.render("Satis Factorio Program", True, "#000000")

        belt_sprite_manager = BeltSegmentSpriteManager()
        belt_sprite_manager.load_images()

        ghost_belt_renderer = GhostBeltRenderer(belt_sprite_manager, grid.CELL_SIZE)

        for item in ITEMS: item.load_sprite()

        player_inventory_ui = PlayerInventoryUI(player, get_screen_size=lambda: (camera.screen_width, camera.screen_height))
        machine_ui = ProducingMachineUI(camera, world, player, player_inventory_ui, screen)
        machine_ui_renderer = MachineUIRenderer(machine_ui)
        hand_crafting_ui = HandCraftingUI(player, get_screen_size=lambda: (camera.screen_width, camera.screen_height))
        hand_crafting_renderer = HandCraftingRenderer(hand_crafting_ui)
        storage_ui = StorageUI(camera, player, player_inventory_ui)
        storage_ui_renderer = StorageUIRenderer(storage_ui)
        belt_filter_ui = BeltFilterUI(camera, player_inventory_ui)
        belt_filter_ui_renderer = BeltFilterUIRenderer(belt_filter_ui)
        splitter_filter_ui = SplitterFilterUI(camera, player_inventory_ui)
        splitter_filter_ui_renderer = SplitterFilterUIRenderer(splitter_filter_ui)

        ui_manager = UIManager({"player_inventory": player_inventory_ui,
                                "machine": machine_ui,
                                "hand_crafting": hand_crafting_ui,
                                "storage": storage_ui,
                                "belt_filter": belt_filter_ui,
                                "splitter_filter": splitter_filter_ui})

        machine_system = MachineSystem(world, player, camera, grid)
        belt_system = BeltSystem(world, grid, player, ghost_belt_renderer)
        belt_ghost_preview_controller = BeltGhostPreviewController(world, player, grid, belt_system, ghost_belt_renderer, camera, screen)
        ghost_machine_renderer = GhostMachineRenderer(world, player, camera, grid, screen, belt_ghost_preview_controller)

        build_system = BuildSystem(world, player, camera, grid, belt_system, machine_system, machine_ui, player_inventory_ui, storage_ui, belt_filter_ui, splitter_filter_ui)
        input_system = InputSystem(build_system, ui_manager, hand_crafting_ui, machine_ui, player_inventory_ui, belt_system, machine_system, storage_ui, belt_filter_ui, splitter_filter_ui)

        item_renderer = ItemRenderer()
        world_renderer = WorldRenderer(world, camera, player, belt_sprite_manager, item_renderer, build_system, grid)
        ui_renderer = UiRenderer(machine_ui_renderer, player_inventory_ui, hand_crafting_renderer, storage_ui_renderer, belt_filter_ui_renderer, splitter_filter_ui_renderer)
        build_mode_renderer = BuildModeRenderer(build_system, machine_system, ghost_machine_renderer, belt_ghost_preview_controller, belt_system, camera, grid)
        cursor_renderer = CursorRenderer(build_system)
        game_menu_bar = GameMenuBar(world, player, camera, ui_manager, get_screen_size=lambda: (camera.screen_width, camera.screen_height))
        game_menu_bar_renderer = GameMenuBarRenderer(game_menu_bar)
        render_system = RenderSystem(
            world_renderer=world_renderer,
            build_renderer=build_mode_renderer,
            ui_renderer=ui_renderer,
            cursor_renderer=cursor_renderer,
            game_menu_bar_renderer=game_menu_bar_renderer
        )
        machine_interaction_system = MachineInteractionSystem(world, build_system, machine_ui, camera, hand_crafting_ui, storage_ui, player_inventory_ui, belt_filter_ui, splitter_filter_ui)

        return GameContext(screen=screen,
                           clock=clock,

                           grid=grid,
                           camera=camera,
                           world=world,

                           player=player,
                           player_inventory_ui=player_inventory_ui,
                           hand_crafting_ui=hand_crafting_ui,
                           storage_ui=storage_ui,
                           belt_filter_ui=belt_filter_ui,
                           splitter_filter_ui=splitter_filter_ui,

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

                           world_renderer=world_renderer,
                           ui_renderer=ui_renderer,
                           build_mode_renderer=build_mode_renderer,
                           cursor_renderer=cursor_renderer,
                           ghost_machine_renderer=ghost_machine_renderer,

                           machine_system=machine_system,
                           machine_ui=machine_ui,
                           machine_ui_renderer=machine_ui_renderer,
                           hand_crafting_renderer=hand_crafting_renderer,
                           machine_interaction_system=machine_interaction_system,

                           game_menu_bar=game_menu_bar)
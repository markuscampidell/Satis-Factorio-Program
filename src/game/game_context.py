# game.game_context
from dataclasses import dataclass

@dataclass
class GameContext:
    screen: any
    clock: any

    grid: any
    camera: any
    world: any

    player: any
    player_inventory_ui: any
    hand_crafting_ui: any
    storage_ui: any
    belt_filter_ui: any
    splitter_filter_ui: any

    font: any
    title_font_surface: any

    belt_sprite_manager: any
    ghost_belt_renderer: any
    belt_system: any
    belt_ghost_preview_controller: any

    ui_manager: any

    build_system: any
    input_system: any

    render_system: any

    world_renderer: any
    ui_renderer: any
    build_mode_renderer: any
    cursor_renderer: any
    ghost_machine_renderer: any

    machine_system: any
    machine_ui: any
    machine_ui_renderer: any
    hand_crafting_renderer: any
    machine_interaction_system: any
    build_hotbar: any
    hover_highlight_renderer: any

    game_menu_bar: any
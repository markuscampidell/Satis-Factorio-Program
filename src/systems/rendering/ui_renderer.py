# systems.rendering.ui_renderer
class UiRenderer:
    def __init__(self, machine_ui_renderer, player_inventory_ui, hand_crafting_renderer, screen_edge_hints_renderer):
        self.machine_ui_renderer = machine_ui_renderer
        self.player_inventory_ui = player_inventory_ui
        self.hand_crafting_renderer = hand_crafting_renderer
        self.screen_edge_hints_renderer = screen_edge_hints_renderer

    def draw(self, screen):
        self.machine_ui_renderer.draw(screen)
        self.player_inventory_ui.draw(screen)
        self.hand_crafting_renderer.draw(screen)
        self.screen_edge_hints_renderer.draw(screen)
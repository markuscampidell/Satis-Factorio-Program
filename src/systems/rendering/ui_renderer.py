# systems.rendering.ui_renderer
class UiRenderer:
    def __init__(self, machine_ui_renderer, player_inventory_ui, hand_crafting_renderer, storage_ui_renderer):
        self.machine_ui_renderer = machine_ui_renderer
        self.player_inventory_ui = player_inventory_ui
        self.hand_crafting_renderer = hand_crafting_renderer
        self.storage_ui_renderer = storage_ui_renderer

    def draw(self, screen):
        self.machine_ui_renderer.draw(screen)
        self.player_inventory_ui.draw(screen)
        self.hand_crafting_renderer.draw(screen)
        self.storage_ui_renderer.draw(screen)
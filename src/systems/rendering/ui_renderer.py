# systems.rendering.ui_renderer
class UiRenderer:
    def __init__(self, machine_ui_renderer, player_inventory_ui, hand_crafting_renderer, storage_ui_renderer, belt_filter_ui_renderer, splitter_filter_ui_renderer):
        self.machine_ui_renderer = machine_ui_renderer
        self.player_inventory_ui = player_inventory_ui
        self.hand_crafting_renderer = hand_crafting_renderer
        self.storage_ui_renderer = storage_ui_renderer
        self.belt_filter_ui_renderer = belt_filter_ui_renderer
        self.splitter_filter_ui_renderer = splitter_filter_ui_renderer

    def draw(self, screen):
        self.machine_ui_renderer.draw(screen)
        self.player_inventory_ui.draw(screen)
        self.hand_crafting_renderer.draw(screen)
        self.storage_ui_renderer.draw(screen)
        self.belt_filter_ui_renderer.draw(screen)
        self.splitter_filter_ui_renderer.draw(screen)
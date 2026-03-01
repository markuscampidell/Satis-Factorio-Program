# systems.rendering.ui_renderer
class UiRenderer:
    def __init__(self, machine_ui, player_inventory_ui, hand_crafting_ui):
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui
        self.hand_crafting_ui = hand_crafting_ui

    def draw(self, screen):
        self.machine_ui.draw(screen)
        self.player_inventory_ui.draw(screen)
        self.hand_crafting_ui.draw(screen)
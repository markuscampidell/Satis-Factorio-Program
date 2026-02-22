class UIManager:
    def __init__(self, game):
        self.game = game

    def toggle_ui(self, ui_name: str):
        ui = getattr(self.game, f"{ui_name}_ui")
        ui.open = not ui.open

    def close_ui(self, ui_name: str):
        getattr(self.game, f"{ui_name}_ui").open = False

    def close_all_uis(self):
        for ui_name in ("player_inventory", "machine", "crafting"):
            getattr(self.game, f"{ui_name}_ui").open = False
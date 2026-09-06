# ui.ui_manager
class UIManager:
    """Keeps track of every togglable UI panel by name, so things like
    "ESC closes everything" don't need to know about each panel one by
    one."""

    def __init__(self, uis: dict[str, object]):
        self.uis = uis

    def toggle_ui(self, ui_name: str):
        if ui_name in self.uis:
            self.uis[ui_name].open = not self.uis[ui_name].open

    def close_ui(self, ui_name: str):
        if ui_name in self.uis:
            self.uis[ui_name].open = False

    def close_all_uis(self):
        for ui in self.uis.values():
            ui.open = False
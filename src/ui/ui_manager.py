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

    def close_uis_clicked_outside(self, mx, my):
        """If (mx, my) doesn't land inside any currently-open UI's rect,
        closes every UI panel at once - so clicking away from whatever's
        open (a machine panel, storage, a filter panel, the player
        inventory, handcrafting, any combination of them being open
        together) dismisses all of it in one click, rather than each panel
        only knowing how to close itself."""
        open_uis = [ui for ui in self.uis.values() if ui.open]
        if not open_uis:
            return
        if any(ui.rect.collidepoint(mx, my) for ui in open_uis):
            return
        self.close_all_uis()
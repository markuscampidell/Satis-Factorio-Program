# ui.game_menu_bar
import pygame as py

from ui.text_input import TextInput
from ui.confirm_dialog import ConfirmDialog
from ui.message_dialog import MessageDialog
from game import save_system

INVALID_NAME_MESSAGE = "Save names can only contain letters, numbers, spaces, - and _."


class GameMenuBar:
    """State for the top-right in-game Game Menu: a toggle button that
    opens/closes a small overlay with "Save and exit" (saves under the
    current name, returns to the main menu), "Save As" (writes the current
    world under a new name, branching off the active save without leaving
    it) and "Exit" (asks whether to save first, then returns to the main
    menu either way). Opening/closing is also driven by ESC and an X button
    inside the overlay itself - see handle_event()."""

    def __init__(self, world, player, camera, ui_manager, get_screen_size):
        self.world = world
        self.player = player
        self.camera = camera
        self.ui_manager = ui_manager
        self.get_screen_size = get_screen_size

        self.current_save_name = None

        self.game_menu_open = False
        self.exit_confirm_dialog = None  # ConfirmDialog | None

        self.save_as_open = False
        self.save_as_input = None  # TextInput | None
        self.save_as_confirm_dialog = None  # ConfirmDialog | None
        self.save_as_message_dialog = None  # MessageDialog | None
        self._pending_save_as_name = None

        # Polled once per frame by Game._run_game_frame, then acted on.
        self.return_to_menu_requested = False
        self.save_before_return = False

        self.menu_button_rect = None
        self.save_and_exit_rect = None
        self.save_as_rect = None
        self.exit_rect = None
        self.close_x_rect = None
        self.save_as_confirm_button_rect = None
        self.save_as_cancel_button_rect = None
        self.panel_rect = None
        self.save_as_panel_rect = None

    def handle_event(self, event) -> bool:
        """Returns True if this event was consumed and shouldn't propagate
        to any other system."""
        if self.exit_confirm_dialog is not None:
            result = self.exit_confirm_dialog.handle_event(event)
            if result == "yes":
                self.save_before_return = True
                self.return_to_menu_requested = True
                self.exit_confirm_dialog = None
                self.game_menu_open = False
            elif result == "no":
                self.save_before_return = False
                self.return_to_menu_requested = True
                self.exit_confirm_dialog = None
                self.game_menu_open = False
            elif result == "cancel":
                # Unlike "no" (exit without saving), an outside click must
                # not trigger an exit - it just dismisses the dialog and
                # falls back to the game menu panel behind it.
                self.exit_confirm_dialog = None
            return True

        if self.save_as_message_dialog is not None:
            if self.save_as_message_dialog.handle_event(event):
                self.save_as_message_dialog = None
            return True

        if self.save_as_confirm_dialog is not None:
            result = self.save_as_confirm_dialog.handle_event(event)
            if result == "yes":
                self._do_save_as(self._pending_save_as_name)
                self.save_as_confirm_dialog = None
                self._pending_save_as_name = None
                self.save_as_open = False
                self.save_as_input = None
                self.game_menu_open = False
            elif result in ("no", "cancel"):
                # Let them adjust the name rather than discarding it.
                name = self._pending_save_as_name
                self.save_as_confirm_dialog = None
                self._pending_save_as_name = None
                self._open_save_as(initial_text=name)
            return True

        if self.save_as_open:
            if (event.type == py.MOUSEBUTTONDOWN and event.button == 1
                    and self.save_as_panel_rect and not self.save_as_panel_rect.collidepoint(event.pos)):
                self.save_as_open = False
                self.save_as_input = None
                return True

            self.save_as_input.handle_event(event)

            if self.save_as_input.submitted:
                name = self.save_as_input.text.strip()
                self.save_as_input.submitted = False
                if name:
                    self._submit_save_as(name)
            elif self.save_as_input.cancelled:
                self.save_as_open = False
                self.save_as_input = None
            elif event.type == py.MOUSEBUTTONDOWN and event.button == 1:
                if self.save_as_confirm_button_rect and self.save_as_confirm_button_rect.collidepoint(event.pos):
                    name = self.save_as_input.text.strip()
                    if name:
                        self._submit_save_as(name)
                elif self.save_as_cancel_button_rect and self.save_as_cancel_button_rect.collidepoint(event.pos):
                    self.save_as_open = False
                    self.save_as_input = None

            return True  # modal - swallow everything else while open

        if self.game_menu_open:
            if event.type == py.KEYDOWN and event.key == py.K_ESCAPE:
                self.game_menu_open = False
                return True

            if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
                if self.panel_rect and not self.panel_rect.collidepoint(event.pos):
                    self.game_menu_open = False
                elif self.close_x_rect and self.close_x_rect.collidepoint(event.pos):
                    self.game_menu_open = False
                elif self.menu_button_rect and self.menu_button_rect.collidepoint(event.pos):
                    self.game_menu_open = False
                elif self.save_and_exit_rect and self.save_and_exit_rect.collidepoint(event.pos):
                    save_system.save_game(self.world, self.player, self.camera, self.current_save_name)
                    self.save_before_return = False
                    self.return_to_menu_requested = True
                    self.game_menu_open = False
                elif self.save_as_rect and self.save_as_rect.collidepoint(event.pos):
                    self._open_save_as(initial_text=self.current_save_name or "")
                elif self.exit_rect and self.exit_rect.collidepoint(event.pos):
                    self.exit_confirm_dialog = ConfirmDialog("Save before exiting?")

            return True  # the game menu is modal - swallow everything else while open

        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_button_rect and self.menu_button_rect.collidepoint(event.pos):
                self.ui_manager.close_all_uis()
                self.game_menu_open = True
                return True

        return False

    def _open_save_as(self, initial_text):
        w, h = self.get_screen_size()
        rect = py.Rect(0, 0, 320, 44)
        rect.center = (w // 2, h // 2 - 10)
        self.save_as_input = TextInput(rect, initial_text=initial_text)
        self.save_as_open = True

    def _submit_save_as(self, name):
        if not save_system.is_valid_save_name(name):
            self.save_as_message_dialog = MessageDialog(INVALID_NAME_MESSAGE)
            return

        if save_system.save_exists(name) and name != self.current_save_name:
            self._pending_save_as_name = name
            self.save_as_confirm_dialog = ConfirmDialog(f"Overwrite save '{name}'?")
            self.save_as_input = None
            return

        self._do_save_as(name)
        self.save_as_open = False
        self.save_as_input = None
        self.game_menu_open = False

    def _do_save_as(self, name):
        save_system.save_game(self.world, self.player, self.camera, name)
        self.current_save_name = name


class GameMenuBarRenderer:
    def __init__(self, game_menu_bar):
        self.bar = game_menu_bar
        self.font = py.font.SysFont("Arial", 18)
        self.title_font = py.font.SysFont("Arial", 24)

    def draw(self, screen):
        bar = self.bar

        bar.menu_button_rect = self._draw_menu_button(screen)

        if bar.save_as_open:
            self._draw_save_as_dialog(screen)
        elif bar.game_menu_open:
            self._draw_panel(screen)

        if bar.exit_confirm_dialog:
            bar.exit_confirm_dialog.draw(screen)

        if bar.save_as_confirm_dialog:
            bar.save_as_confirm_dialog.draw(screen)

        if bar.save_as_message_dialog:
            bar.save_as_message_dialog.draw(screen)

    def _draw_menu_button(self, screen):
        w, _ = screen.get_size()
        rect = py.Rect(w - 110, 10, 100, 32)
        py.draw.rect(screen, (70, 70, 140), rect, border_radius=6)
        text = self.font.render("Menu", True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=rect.center))
        return rect

    def _draw_panel(self, screen):
        bar = self.bar
        w, h = screen.get_size()

        panel = py.Rect(0, 0, 320, 280)
        panel.center = (w // 2, h // 2)
        bar.panel_rect = panel
        py.draw.rect(screen, (240, 240, 240), panel, border_radius=10)
        py.draw.rect(screen, (60, 60, 60), panel, width=2, border_radius=10)

        title = self.title_font.render("Game Menu", True, (0, 0, 0))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 30)))

        bar.save_and_exit_rect = py.Rect(0, 0, 240, 44)
        bar.save_and_exit_rect.center = (panel.centerx, panel.y + 90)
        py.draw.rect(screen, (0, 150, 0), bar.save_and_exit_rect, border_radius=8)
        save_text = self.font.render("Save and exit", True, "#FFFFFF")
        screen.blit(save_text, save_text.get_rect(center=bar.save_and_exit_rect.center))

        bar.save_as_rect = py.Rect(0, 0, 240, 44)
        bar.save_as_rect.center = (panel.centerx, panel.y + 150)
        py.draw.rect(screen, (70, 70, 140), bar.save_as_rect, border_radius=8)
        save_as_text = self.font.render("Save As", True, "#FFFFFF")
        screen.blit(save_as_text, save_as_text.get_rect(center=bar.save_as_rect.center))

        bar.exit_rect = py.Rect(0, 0, 240, 44)
        bar.exit_rect.center = (panel.centerx, panel.y + 210)
        py.draw.rect(screen, (150, 0, 0), bar.exit_rect, border_radius=8)
        exit_text = self.font.render("Exit", True, "#FFFFFF")
        screen.blit(exit_text, exit_text.get_rect(center=bar.exit_rect.center))

        bar.close_x_rect = py.Rect(0, 0, 26, 26)
        bar.close_x_rect.topright = (panel.right - 8, panel.y + 8)
        py.draw.rect(screen, (150, 0, 0), bar.close_x_rect, border_radius=6)
        x_text = self.font.render("X", True, "#FFFFFF")
        screen.blit(x_text, x_text.get_rect(center=bar.close_x_rect.center))

    def _draw_save_as_dialog(self, screen):
        bar = self.bar
        w, h = screen.get_size()

        panel = py.Rect(0, 0, 360, 160)
        panel.center = (w // 2, h // 2)
        bar.save_as_panel_rect = panel
        py.draw.rect(screen, (240, 240, 240), panel, border_radius=10)
        py.draw.rect(screen, (60, 60, 60), panel, width=2, border_radius=10)

        title = self.title_font.render("Save As", True, (0, 0, 0))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 28)))

        if bar.save_as_input:
            bar.save_as_input.update(1 / 60)
            bar.save_as_input.draw(screen)

        bar.save_as_confirm_button_rect = py.Rect(0, 0, 120, 40)
        bar.save_as_confirm_button_rect.center = (panel.centerx - 70, panel.bottom - 34)
        py.draw.rect(screen, (0, 150, 0), bar.save_as_confirm_button_rect, border_radius=8)
        confirm_text = self.font.render("Save", True, "#FFFFFF")
        screen.blit(confirm_text, confirm_text.get_rect(center=bar.save_as_confirm_button_rect.center))

        bar.save_as_cancel_button_rect = py.Rect(0, 0, 120, 40)
        bar.save_as_cancel_button_rect.center = (panel.centerx + 70, panel.bottom - 34)
        py.draw.rect(screen, (150, 0, 0), bar.save_as_cancel_button_rect, border_radius=8)
        cancel_text = self.font.render("Cancel", True, "#FFFFFF")
        screen.blit(cancel_text, cancel_text.get_rect(center=bar.save_as_cancel_button_rect.center))

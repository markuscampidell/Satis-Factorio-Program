# game.main_menu
import pygame as py

from ui.text_input import TextInput
from ui.confirm_dialog import ConfirmDialog
from ui.message_dialog import MessageDialog
from game import save_system

INVALID_NAME_MESSAGE = "Save names can only contain letters, numbers, spaces, - and _."


class MainMenu:
    """The pre-game menu: New Game (name it, writes the save immediately),
    Load Game (pick or delete an existing save), Quit."""

    def __init__(self, get_screen_size):
        self.get_screen_size = get_screen_size
        self.screen_state = "root"  # "root" | "new_game" | "load_game"

        self.font = py.font.SysFont("Arial", 32)
        self.button_font = py.font.SysFont("Arial", 24)
        self.small_font = py.font.SysFont("Arial", 20)

        self.name_input = None
        self.message_dialog = None
        self.confirm_dialog = None
        self.confirm_action = None  # "delete" | "rename" | "new_game"
        self.delete_target = None

        self.rename_input = None
        self.rename_target = None      # the save currently being renamed
        self.rename_new_name = None    # pending name, once an overwrite confirm is needed

        self.pending_new_game_name = None  # name awaiting a New Game overwrite confirm

        self.saves = []
        self.last_opened = None
        self._root_button_rects = {}
        self._new_game_button_rects = {}
        self._load_game_row_rects = []  # list of (name_rect, name, edit_rect, delete_rect)
        self._load_game_back_rect = None

        self.refresh_save_list()

    def refresh_save_list(self):
        self.saves = save_system.list_saves()
        self.last_opened = save_system.get_last_opened()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        """Returns an action tuple for Game to act on, or None.
        Possible returns: ("start_new_game", name), ("load_game", name), ("quit",)"""
        if self.message_dialog is not None:
            if self.message_dialog.handle_event(event):
                self.message_dialog = None
            return None

        if self.confirm_dialog is not None:
            result = self.confirm_dialog.handle_event(event)
            if result == "yes":
                if self.confirm_action == "delete":
                    save_system.delete_save(self.delete_target)
                    self.refresh_save_list()
                    self._clear_modal_state()
                elif self.confirm_action == "rename":
                    save_system.rename_save(self.rename_target, self.rename_new_name)
                    self.refresh_save_list()
                    self._clear_modal_state()
                elif self.confirm_action == "new_game":
                    name = self.pending_new_game_name
                    self._clear_modal_state()
                    self.screen_state = "root"
                    return ("start_new_game", name)
            elif result in ("no", "cancel"):
                if self.confirm_action == "new_game":
                    # Let them adjust the name rather than starting over blank.
                    name = self.pending_new_game_name
                    self._clear_modal_state()
                    self._open_new_game_screen(initial_text=name)
                else:
                    self._clear_modal_state()
            return None

        if self.rename_input is not None:
            return self._handle_rename_input_event(event)

        if self.screen_state == "root":
            return self._handle_root_event(event)
        elif self.screen_state == "new_game":
            return self._handle_new_game_event(event)
        elif self.screen_state == "load_game":
            return self._handle_load_game_event(event)

        return None

    def _clear_modal_state(self):
        self.confirm_dialog = None
        self.confirm_action = None
        self.delete_target = None
        self.rename_target = None
        self.rename_new_name = None
        self.pending_new_game_name = None

    def _handle_root_event(self, event):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self._root_button_rects.get("continue") and self._root_button_rects["continue"].collidepoint(event.pos):
            return ("load_game", self.last_opened)
        elif self._root_button_rects.get("new_game") and self._root_button_rects["new_game"].collidepoint(event.pos):
            self._open_new_game_screen()
        elif self._root_button_rects.get("load_game") and self._root_button_rects["load_game"].collidepoint(event.pos):
            self.screen_state = "load_game"
            self.refresh_save_list()
        elif self._root_button_rects.get("quit") and self._root_button_rects["quit"].collidepoint(event.pos):
            return ("quit",)

        return None

    def _open_new_game_screen(self, initial_text=""):
        self.screen_state = "new_game"
        w, h = self.get_screen_size()
        rect = py.Rect(0, 0, 320, 44)
        rect.center = (w // 2, h // 2 - 20)
        self.name_input = TextInput(rect, initial_text=initial_text)

    def _handle_new_game_event(self, event):
        if self.name_input is not None:
            self.name_input.handle_event(event)

            if self.name_input.submitted:
                name = self.name_input.text.strip()
                self.name_input.submitted = False
                if name:
                    return self._submit_new_game_name(name)

            if self.name_input.cancelled:
                self.name_input = None
                self.screen_state = "root"
                return None

        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self._new_game_button_rects.get("start") and self._new_game_button_rects["start"].collidepoint(event.pos):
                name = self.name_input.text.strip() if self.name_input else ""
                if name:
                    return self._submit_new_game_name(name)
            elif self._new_game_button_rects.get("back") and self._new_game_button_rects["back"].collidepoint(event.pos):
                self.name_input = None
                self.screen_state = "root"

        return None

    def _submit_new_game_name(self, name):
        if not save_system.is_valid_save_name(name):
            self.message_dialog = MessageDialog(INVALID_NAME_MESSAGE)
            return None

        if save_system.save_exists(name):
            self.pending_new_game_name = name
            self.confirm_action = "new_game"
            self.confirm_dialog = ConfirmDialog(f"Overwrite save '{name}'?")
            self.name_input = None
            return None

        self.name_input = None
        self.screen_state = "root"
        return ("start_new_game", name)

    def _handle_load_game_event(self, event):
        # message_dialog/confirm_dialog/rename_input are all checked before
        # dispatching here (see handle_event), so reaching this point already
        # means no other panel is open over the load game screen.
        if event.type == py.KEYDOWN and event.key == py.K_ESCAPE:
            self.screen_state = "root"
            return None

        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self._load_game_back_rect and self._load_game_back_rect.collidepoint(event.pos):
            self.screen_state = "root"
            return None

        for name_rect, name, edit_rect, delete_rect in self._load_game_row_rects:
            if delete_rect.collidepoint(event.pos):
                self.delete_target = name
                self.confirm_action = "delete"
                self.confirm_dialog = ConfirmDialog(f"Delete save '{name}'?")
                return None
            if edit_rect.collidepoint(event.pos):
                self._open_rename(name)
                return None
            if name_rect.collidepoint(event.pos):
                return ("load_game", name)

        return None

    def _open_rename(self, name):
        self.rename_target = name
        w, h = self.get_screen_size()
        rect = py.Rect(0, 0, 320, 44)
        rect.center = (w // 2, h // 2)
        self.rename_input = TextInput(rect, initial_text=name)

    def _handle_rename_input_event(self, event):
        if (event.type == py.MOUSEBUTTONDOWN and event.button == 1
                and not self.rename_input.rect.collidepoint(event.pos)):
            self.rename_input = None
            self.rename_target = None
            return None

        self.rename_input.handle_event(event)

        if self.rename_input.submitted:
            new_name = self.rename_input.text.strip()
            old_name = self.rename_target
            self.rename_input.submitted = False

            if not new_name or new_name == old_name:
                self.rename_input = None
                self.rename_target = None
                return None

            if not save_system.is_valid_save_name(new_name):
                self.message_dialog = MessageDialog(INVALID_NAME_MESSAGE)
                return None  # keep rename_input open so they can fix it

            self.rename_input = None
            if save_system.save_exists(new_name):
                self.rename_new_name = new_name
                self.confirm_action = "rename"
                self.confirm_dialog = ConfirmDialog(f"Overwrite save '{new_name}'?")
                # rename_target stays set - the confirm branch needs it
            else:
                save_system.rename_save(old_name, new_name)
                self.refresh_save_list()
                self.rename_target = None
            return None

        if self.rename_input.cancelled:
            self.rename_input = None
            self.rename_target = None
            return None

        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, screen):
        w, h = self.get_screen_size()
        screen.fill("#987171")

        if self.screen_state == "root":
            self._draw_root(screen, w, h)
        elif self.screen_state == "new_game":
            self._draw_new_game(screen, w, h)
        elif self.screen_state == "load_game":
            self._draw_load_game(screen, w, h)

        if self.rename_input:
            self.rename_input.update(1 / 60)
            self.rename_input.draw(screen)

        if self.confirm_dialog:
            self.confirm_dialog.draw(screen)

        if self.message_dialog:
            self.message_dialog.draw(screen)

    def _draw_button(self, screen, rect, label, color=(90, 90, 90)):
        py.draw.rect(screen, color, rect, border_radius=8)
        fitted = self._fit_text(label, rect.width - 20, self.button_font)
        text = self.button_font.render(fitted, True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=rect.center))

    def _fit_text(self, text, max_width, font):
        """Shrinks text to fit max_width, adding an ellipsis if it had to
        cut anything - used for the Continue button, whose label includes
        the (variable-length) save name."""
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        truncated = text
        while truncated and font.size(truncated + ellipsis)[0] > max_width:
            truncated = truncated[:-1]

        return (truncated + ellipsis) if truncated else ellipsis

    def _draw_root(self, screen, w, h):
        title = self.font.render("Satis Factorio Program", True, "#000000")
        title_rect = title.get_rect(center=(w // 2, h // 2 - 140))
        screen.blit(title, title_rect)

        button_w, button_h, spacing = 260, 50, 20
        labels = []
        if self.last_opened:
            labels.append(("continue", f"Continue ({self.last_opened})"))
        labels += [("new_game", "New Game"), ("load_game", "Load Game"), ("quit", "Quit")]

        # Anchored to the title's bottom edge, not screen-center - otherwise
        # adding more buttons (like Continue) grows the stack upward and
        # overlaps the title instead of just extending further down.
        top = title_rect.bottom + 60

        self._root_button_rects = {}
        for i, (key, label) in enumerate(labels):
            rect = py.Rect(0, 0, button_w, button_h)
            rect.center = (w // 2, top + i * (button_h + spacing) + button_h // 2)
            self._root_button_rects[key] = rect
            self._draw_button(screen, rect, label)

    def _draw_new_game(self, screen, w, h):
        title = self.font.render("New Game", True, "#000000")
        screen.blit(title, title.get_rect(center=(w // 2, h // 2 - 100)))

        if self.name_input is not None:
            self.name_input.update(1 / 60)
            self.name_input.draw(screen)

        start_rect = py.Rect(0, 0, 120, 44)
        start_rect.center = (w // 2 - 70, h // 2 + 50)
        back_rect = py.Rect(0, 0, 120, 44)
        back_rect.center = (w // 2 + 70, h // 2 + 50)

        self._new_game_button_rects = {"start": start_rect, "back": back_rect}
        self._draw_button(screen, start_rect, "Start", color=(0, 150, 0))
        self._draw_button(screen, back_rect, "Back", color=(150, 0, 0))

    def _draw_load_game(self, screen, w, h):
        title = self.font.render("Load Game", True, "#000000")
        screen.blit(title, title.get_rect(center=(w // 2, 60)))

        self._load_game_row_rects = []

        if not self.saves:
            empty = self.small_font.render("No saves yet", True, "#000000")
            screen.blit(empty, empty.get_rect(center=(w // 2, h // 2)))
        else:
            row_w, row_h, spacing = 420, 44, 10
            top = 120
            name_area_width = row_w - 12 - 74  # left padding + reserved space for edit/delete buttons
            for i, name in enumerate(self.saves):
                row_rect = py.Rect(0, 0, row_w, row_h)
                row_rect.center = (w // 2, top + i * (row_h + spacing) + row_h // 2)

                py.draw.rect(screen, (90, 90, 90), row_rect, border_radius=8)
                fitted_name = self._fit_text(name, name_area_width, self.button_font)
                text = self.button_font.render(fitted_name, True, "#FFFFFF")
                screen.blit(text, text.get_rect(midleft=(row_rect.x + 12, row_rect.centery)))

                delete_rect = py.Rect(0, 0, 32, 32)
                delete_rect.center = (row_rect.right - 22, row_rect.centery)
                py.draw.rect(screen, (150, 0, 0), delete_rect, border_radius=6)
                x_text = self.small_font.render("X", True, "#FFFFFF")
                screen.blit(x_text, x_text.get_rect(center=delete_rect.center))

                edit_rect = py.Rect(0, 0, 32, 32)
                edit_rect.center = (delete_rect.centerx - 40, row_rect.centery)
                py.draw.rect(screen, (70, 70, 140), edit_rect, border_radius=6)
                edit_text = self.small_font.render("E", True, "#FFFFFF")
                screen.blit(edit_text, edit_text.get_rect(center=edit_rect.center))

                self._load_game_row_rects.append((row_rect, name, edit_rect, delete_rect))

        back_rect = py.Rect(0, 0, 120, 44)
        back_rect.center = (w // 2, h - 50)
        self._load_game_back_rect = back_rect
        self._draw_button(screen, back_rect, "Back", color=(150, 0, 0))

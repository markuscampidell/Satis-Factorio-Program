# ui.text_input
import pygame as py


class TextInput:
    """Single-line text entry box with a movable cursor. Feed it every
    pygame event via handle_event(); it consumes py.MOUSEBUTTONDOWN
    (click-to-position-cursor / focus), py.TEXTINPUT (character entry at
    the cursor) and py.KEYDOWN (backspace/delete/left/right/enter/escape -
    Ctrl+Left/Right jumps the cursor to the start/end, Ctrl+Backspace erases
    everything left of the cursor). Global text-input mode
    (py.key.start_text_input()) is the caller's responsibility to enable
    once at startup - nothing to start/stop per widget instance."""

    MAX_LENGTH = 32

    def __init__(self, rect: py.Rect, initial_text: str = ""):
        self.rect = rect
        self.text = initial_text
        self.cursor_pos = len(initial_text)
        self.active = True
        self.submitted = False   # one-shot: set True the frame Enter is pressed
        self.cancelled = False   # one-shot: set True the frame Escape is pressed
        self.font = py.font.SysFont("Arial", 22)
        self._cursor_visible = True
        self._cursor_timer = 0.0

    def handle_event(self, event):
        if event.type == py.MOUSEBUTTONDOWN:
            # Always re-evaluate active state on click, even if currently
            # inactive - otherwise clicking back into the box after
            # clicking away from it could never reactivate it.
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                self.cursor_pos = self._index_at_x(event.pos[0])
                self._show_cursor()
            return

        if not self.active:
            return

        if event.type == py.TEXTINPUT:
            if len(self.text) < self.MAX_LENGTH:
                self.text = self.text[:self.cursor_pos] + event.text + self.text[self.cursor_pos:]
                self.cursor_pos += len(event.text)
                self._show_cursor()
        elif event.type == py.KEYDOWN:
            ctrl_held = event.mod & py.KMOD_CTRL

            if event.key == py.K_BACKSPACE:
                if ctrl_held:
                    if self.cursor_pos > 0:
                        self.text = self.text[self.cursor_pos:]
                        self.cursor_pos = 0
                        self._show_cursor()
                elif self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self._show_cursor()
            elif event.key == py.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
                    self._show_cursor()
            elif event.key == py.K_LEFT:
                self.cursor_pos = 0 if ctrl_held else max(0, self.cursor_pos - 1)
                self._show_cursor()
            elif event.key == py.K_RIGHT:
                self.cursor_pos = len(self.text) if ctrl_held else min(len(self.text), self.cursor_pos + 1)
                self._show_cursor()
            elif event.key == py.K_RETURN:
                self.submitted = True
            elif event.key == py.K_ESCAPE:
                self.cancelled = True

    def _index_at_x(self, screen_x):
        """Nearest character boundary to a click's x coordinate."""
        click_x = screen_x - (self.rect.x + 8)
        best_index = 0
        best_dist = abs(click_x)
        for i in range(1, len(self.text) + 1):
            width = self.font.size(self.text[:i])[0]
            dist = abs(width - click_x)
            if dist < best_dist:
                best_dist = dist
                best_index = i
        return best_index

    def _show_cursor(self):
        self._cursor_visible = True
        self._cursor_timer = 0.0

    def update(self, dt):
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

    def draw(self, screen):
        py.draw.rect(screen, (255, 255, 255), self.rect, border_radius=6)
        py.draw.rect(screen, (60, 60, 60), self.rect, width=2, border_radius=6)

        text_surf = self.font.render(self.text, True, (0, 0, 0))
        screen.blit(text_surf, (self.rect.x + 8, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))

        if self.active and self._cursor_visible:
            prefix_width = self.font.size(self.text[:self.cursor_pos])[0]
            cursor_x = self.rect.x + 8 + prefix_width
            cy = self.rect.y + 6
            py.draw.line(screen, (0, 0, 0), (cursor_x, cy), (cursor_x, self.rect.bottom - 6), 2)

    def reset(self, text=""):
        self.text = text
        self.cursor_pos = len(text)
        self.submitted = False
        self.cancelled = False

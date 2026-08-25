# ui.message_dialog
import pygame as py


class MessageDialog:
    """Small modal info box with a single OK button, drawn centered on
    screen. handle_event() returns True once acknowledged (click OK, or
    press Enter/Escape). Used for simple notices - e.g. rejecting an
    invalid save name - that don't need a yes/no choice."""

    def __init__(self, message: str):
        self.message = message
        self.font = py.font.SysFont("Arial", 22)
        self.ok_rect = None

    def handle_event(self, event) -> bool:
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_rect and self.ok_rect.collidepoint(event.pos):
                return True
        elif event.type == py.KEYDOWN:
            if event.key in (py.K_RETURN, py.K_ESCAPE):
                return True
        return False

    def draw(self, screen):
        w, h = screen.get_size()

        box = py.Rect(0, 0, 550, 165)
        box.center = (w // 2, h // 2)
        py.draw.rect(screen, (240, 240, 240), box, border_radius=10)
        py.draw.rect(screen, (60, 60, 60), box, width=2, border_radius=10)

        text = self.font.render(self.message, True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=(box.centerx, box.y + 45)))

        self.ok_rect = py.Rect(0, 0, 100, 36)
        self.ok_rect.center = (box.centerx, box.bottom - 40)
        py.draw.rect(screen, (70, 70, 140), self.ok_rect, border_radius=6)
        ok_text = self.font.render("OK", True, "#FFFFFF")
        screen.blit(ok_text, ok_text.get_rect(center=self.ok_rect.center))

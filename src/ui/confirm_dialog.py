# ui.confirm_dialog
import pygame as py


class ConfirmDialog:
    """Small modal yes/no confirmation box drawn centered on screen.
    handle_event() returns "yes", "no", or None. Reused for both the
    Save As overwrite confirm and the Load Game delete confirm."""

    def __init__(self, message: str):
        self.message = message
        self.font = py.font.SysFont("Arial", 22)
        self.yes_rect = None
        self.no_rect = None

    def handle_event(self, event):
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.yes_rect and self.yes_rect.collidepoint(event.pos):
                return "yes"
            if self.no_rect and self.no_rect.collidepoint(event.pos):
                return "no"
        elif event.type == py.KEYDOWN:
            if event.key == py.K_RETURN:
                return "yes"
            if event.key == py.K_ESCAPE:
                return "no"
        return None

    def draw(self, screen):
        w, h = screen.get_size()

        box = py.Rect(0, 0, 380, 140)
        box.center = (w // 2, h // 2)
        py.draw.rect(screen, (240, 240, 240), box, border_radius=10)
        py.draw.rect(screen, (60, 60, 60), box, width=2, border_radius=10)

        text = self.font.render(self.message, True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=(box.centerx, box.y + 40)))

        self.yes_rect = py.Rect(box.centerx - 90, box.bottom - 50, 80, 34)
        self.no_rect = py.Rect(box.centerx + 10, box.bottom - 50, 80, 34)

        py.draw.rect(screen, (0, 180, 0), self.yes_rect, border_radius=6)
        py.draw.rect(screen, (180, 0, 0), self.no_rect, border_radius=6)

        yes_text = self.font.render("Yes", True, "#FFFFFF")
        no_text = self.font.render("No", True, "#FFFFFF")
        screen.blit(yes_text, yes_text.get_rect(center=self.yes_rect.center))
        screen.blit(no_text, no_text.get_rect(center=self.no_rect.center))

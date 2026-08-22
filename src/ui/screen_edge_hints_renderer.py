# ui.screen_edge_hints_renderer
import pygame as py


class ScreenEdgeHintsRenderer:
    """Small always-on hints at the left/right screen edges showing which
    key opens the panel docked to that side (inventory on the left,
    handcrafting on the right). Text sits right at the edge, with a small
    arrow past it pointing back in toward the center of the screen.
    Hidden once the corresponding panel is open, since the panel itself
    covers that edge at that point."""

    ARROW_W = 10
    ARROW_H = 14
    MARGIN = 6
    COLOR = (30, 30, 30)

    def __init__(self, player_inventory_ui, hand_crafting_ui):
        self.player_inventory_ui = player_inventory_ui
        self.hand_crafting_ui = hand_crafting_ui
        self.font = py.font.SysFont("Arial", 13)

    def draw(self, screen):
        w, h = screen.get_size()
        cy = h // 2

        if not self.player_inventory_ui.open:
            self._draw_hint(screen, "Tab: Inventory", side="left", w=w, cy=cy)

        if not self.hand_crafting_ui.open:
            self._draw_hint(screen, "F: Handcrafting", side="right", w=w, cy=cy)

    def _draw_hint(self, screen, label, side, w, cy):
        text = self.font.render(label, True, self.COLOR)
        gap = 4

        if side == "left":
            text_rect = text.get_rect(midleft=(self.MARGIN, cy))
            # Arrow sits past the text (further from the edge), pointing
            # back in toward the center of the screen.
            base_x = text_rect.right + gap
            tip_x = base_x + self.ARROW_W
            arrow_points = [
                (tip_x, cy),
                (base_x, cy - self.ARROW_H // 2),
                (base_x, cy + self.ARROW_H // 2),
            ]
        else:
            text_rect = text.get_rect(midright=(w - self.MARGIN, cy))
            base_x = text_rect.left - gap
            tip_x = base_x - self.ARROW_W
            arrow_points = [
                (tip_x, cy),
                (base_x, cy - self.ARROW_H // 2),
                (base_x, cy + self.ARROW_H // 2),
            ]

        screen.blit(text, text_rect)
        py.draw.polygon(screen, self.COLOR, arrow_points)

# ui.belt_filter_ui_renderer
import pygame as py


class BeltFilterUIRenderer:
    """Draws a BeltFilterUI's panel: background, title, the single
    ItemFilterPanel bound to the selected belt's filter, and - in its own
    reserved area to the right, never on top of the slots - the shared
    item picker when it's open."""

    def __init__(self, belt_filter_ui):
        self.ui = belt_filter_ui
        self.title_font = py.font.SysFont("Arial", 22)

    def draw(self, screen):
        ui = self.ui
        if not ui.open or not ui.selected_belt:
            return

        ui.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        screen.blit(ui.sprite, ui.rect)

        title = self.title_font.render("Belt Filter", True, "#000000")
        screen.blit(title, title.get_rect(midtop=(ui.rect.centerx, ui.rect.y + 8)))

        content_top_left = (ui.rect.x + ui.PADDING, ui.rect.y + ui.TITLE_HEIGHT)
        ui.panel.draw(screen, content_top_left, ui.selected_belt.filter)

        picker_top_left = (content_top_left[0] + ui.slot_area_width + ui.PICKER_GAP, content_top_left[1])
        ui.picker.draw(screen, picker_top_left)

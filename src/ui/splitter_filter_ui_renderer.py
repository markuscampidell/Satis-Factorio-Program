# ui.splitter_filter_ui_renderer
import pygame as py

from ui.splitter_filter_ui import SIDE_LABELS


class SplitterFilterUIRenderer:
    """Draws a SplitterFilterUI's panel: background, title, its three
    Left/Forward/Right ItemFilterPanels side by side, and - in its own
    reserved area to the right of all three columns, never on top of any
    of them - the shared item picker when it's open."""

    def __init__(self, splitter_filter_ui):
        self.ui = splitter_filter_ui
        self.title_font = py.font.SysFont("Arial", 22)

    def draw(self, screen):
        ui = self.ui
        if not ui.open or not ui.selected_splitter:
            return

        ui.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        screen.blit(ui.sprite, ui.rect)

        title = self.title_font.render("Splitter Output Filters", True, "#000000")
        screen.blit(title, title.get_rect(midtop=(ui.rect.centerx, ui.rect.y + 8)))

        content_top = ui.rect.y + ui.TITLE_HEIGHT
        for i, (panel, output_filter) in enumerate(zip(ui.panels, ui.selected_splitter.output_filters)):
            x = ui.rect.x + ui.PADDING + i * (ui.column_width + ui.COLUMN_GAP)
            panel.draw(screen, (x, content_top), output_filter, SIDE_LABELS[i])

        picker_top_left = (ui.rect.x + ui.PADDING + ui.slot_area_width + ui.PICKER_GAP, content_top)
        ui.picker.draw(screen, picker_top_left)

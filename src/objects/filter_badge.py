# objects.filter_badge
import pygame as py

_FILL = "#FFD23F"
_OUTLINE = "#402A00"


def draw_filter_badge(screen, center_pos, size=10):
    """Small funnel glyph marking a tile (or a splitter's output edge) as
    having an active item filter - shared by world_renderer (belt tiles)
    and Splitter.draw() (per-output-side badges) so both use the same
    visual language."""
    cx, cy = center_pos
    half = size / 2
    points = [
        (cx - half, cy - half),
        (cx + half, cy - half),
        (cx + half * 0.3, cy + half * 0.2),
        (cx + half * 0.3, cy + half),
        (cx - half * 0.3, cy + half),
        (cx - half * 0.3, cy + half * 0.2),
    ]
    py.draw.polygon(screen, _FILL, points)
    py.draw.polygon(screen, _OUTLINE, points, width=1)

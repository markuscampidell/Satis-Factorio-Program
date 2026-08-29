# ui.scroll
import pygame as py


def clamp_scroll(offset, content_height, viewport_height):
    """Keeps a scroll offset within [0, content_height - viewport_height]
    so a panel can't be scrolled past either end of its content."""
    max_offset = max(0, content_height - viewport_height)
    return max(0, min(offset, max_offset))


def apply_wheel_scroll(offset, event, content_height, viewport_height, speed=40):
    """Returns the scroll offset after applying one MOUSEWHEEL event -
    event.y is positive when scrolling up, so it subtracts to move the
    content up (revealing what's below)."""
    return clamp_scroll(offset - event.y * speed, content_height, viewport_height)


def draw_scrollbar(screen, track_rect, offset, content_height, viewport_height,
                    color=(140, 140, 140), track_color=(210, 210, 210)):
    """Thin vertical scrollbar thumb inside track_rect, positioned to match
    offset/content_height/viewport_height. Only call when content actually
    overflows (content_height > viewport_height)."""
    py.draw.rect(screen, track_color, track_rect, border_radius=track_rect.width // 2)

    max_offset = max(1, content_height - viewport_height)
    thumb_h = max(24, int(track_rect.height * viewport_height / content_height))
    thumb_y = track_rect.y + int((track_rect.height - thumb_h) * (offset / max_offset))
    thumb = py.Rect(track_rect.x, thumb_y, track_rect.width, thumb_h)
    py.draw.rect(screen, color, thumb, border_radius=track_rect.width // 2)

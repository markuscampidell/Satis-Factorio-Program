import pygame as py
from game.grid import Grid


class ItemRenderer:

    def draw_item(self, screen, camera, item, grid_pos, progress, incoming_direction):
        if not item or not item.sprite:
            return

        incoming = incoming_direction

        start = (
            grid_pos[0] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2 - incoming.x * Grid.CELL_SIZE,
            grid_pos[1] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2 - incoming.y * Grid.CELL_SIZE,
        )

        end = (
            grid_pos[0] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2,
            grid_pos[1] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2,
        )

        self.draw_item_lerp(screen, camera, item, start, end, progress)

    def draw_item_lerp(self, screen, camera, item, start, end, progress):
        """Draw `item` interpolated between pixel points `start` and `end`,
        using the same sizing/scaling as the normal belt-item animation."""
        if not item or not item.sprite:
            return

        x = start[0] + (end[0] - start[0]) * progress
        y = start[1] + (end[1] - start[1]) * progress

        size = int(Grid.CELL_SIZE * 0.5)

        sprite = (
            item.get_scaled_sprite(size)
            if hasattr(item, "get_scaled_sprite")
            else py.transform.scale(item.sprite, (size, size))
        )

        screen.blit(
            sprite,
            (
                x - camera.x - size // 2,
                y - camera.y - size // 2
            )
        )
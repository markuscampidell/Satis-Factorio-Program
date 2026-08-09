import pygame as py
from game.grid import Grid


class ItemRenderer:

    def draw_item(self, screen, camera, item, grid_pos, progress, incoming_direction):
        if not item or not item.sprite:
            return

        incoming = incoming_direction

        start_x = (
            grid_pos[0] * Grid.CELL_SIZE
            + Grid.CELL_SIZE // 2
            - incoming.x * Grid.CELL_SIZE
        )

        start_y = (
            grid_pos[1] * Grid.CELL_SIZE
            + Grid.CELL_SIZE // 2
            - incoming.y * Grid.CELL_SIZE
        )

        end_x = (
            grid_pos[0] * Grid.CELL_SIZE
            + Grid.CELL_SIZE // 2
        )

        end_y = (
            grid_pos[1] * Grid.CELL_SIZE
            + Grid.CELL_SIZE // 2
        )

        x = start_x + (end_x - start_x) * progress
        y = start_y + (end_y - start_y) * progress

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
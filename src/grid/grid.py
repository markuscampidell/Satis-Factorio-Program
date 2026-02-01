import pygame as py

class Grid:
    CELL_SIZE = 32
    def __init__(self, screen_width, screen_height, color=(204, 204, 204)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.color = color

    def draw(self, screen, camera, alpha=150):
        # Create a temporary surface for the grid lines
        grid_surf = py.Surface((self.screen_width, self.screen_height), py.SRCALPHA)
        
        start_x = int(-camera.x % self.CELL_SIZE)
        start_y = int(-camera.y % self.CELL_SIZE)

        # Draw vertical lines
        for x in range(start_x, self.screen_width, self.CELL_SIZE):
            py.draw.line(grid_surf, (*self.color, alpha), (x, 0), (x, self.screen_height))
        # Draw horizontal lines
        for y in range(start_y, self.screen_height, self.CELL_SIZE):
            py.draw.line(grid_surf, (*self.color, alpha), (0, y), (self.screen_width, y))

        # Blit the grid surface onto the main screen
        screen.blit(grid_surf, (0, 0))

# core.camera
class Camera:
    """Decides what part of the world is shown on screen. Everything gets
    drawn shifted by camera.x/camera.y, so moving the camera makes the
    whole world appear to scroll."""

    def __init__(self, screen_width: float, screen_height: float, margin=350, smooth=0.05):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0
        self.y = 0
        self.margin = margin # distance from edge before camera moves
        self.smooth = smooth # 0.05 → 5% of distance per frame

    def center_on(self, rect):
        """Snaps the camera to be centered exactly on 'rect' """
        self.x = rect.centerx - self.screen_width // 2
        self.y = rect.centery - self.screen_height // 2

    def update(self, player):
        """Follows the player, but only a little bit at a time and only
        once they get close to the edge of the screen - like a soft leash
        instead of the camera being glued to them."""
        playerx = player.rect.centerx - self.x
        playery = player.rect.centery - self.y

        # Horizontal movement
        if playerx < self.margin:
            self.x -= (self.margin - playerx) * self.smooth
        elif playerx > self.screen_width - self.margin:
            self.x += (playerx - (self.screen_width - self.margin)) * self.smooth

        # Vertical movement
        if playery < self.margin:
            self.y -= (self.margin - playery) * self.smooth
        elif playery > self.screen_height - self.margin:
            self.y += (playery - (self.screen_height - self.margin)) * self.smooth

    def visible_tile_rect(self, cell_size):
        """(left, top, right, bottom) tile bounds of what's currently on
        screen, right/bottom exclusive - centralizes the camera-bounds math
        world_renderer.py used to duplicate ad hoc in two places. Cast to
        int since camera.x/y drift to floats (the soft-follow smoothing in
        update() adds fractional amounts each frame), but a tile coordinate
        used as a chunk-range bound needs to be an actual int."""
        left = int(self.x // cell_size)
        top = int(self.y // cell_size)
        right = int((self.x + self.screen_width) // cell_size) + 1
        bottom = int((self.y + self.screen_height) // cell_size) + 1
        return left, top, right, bottom
# core.camera
class Camera:
    def __init__(self, screen_width: float, screen_height: float, margin=350, smooth=0.05):
        self.screen_width = screen_width      # total width of the window
        self.screen_height = screen_height    # total height of the window
        self.x = 0
        self.y = 0
        self.margin = margin                  # distance from edge before camera moves
        self.smooth = smooth                  # 0.05 → 5% of distance per frame

    def center_on(self, rect):
        """Snaps the camera to be centered exactly on `rect` - unlike
        update(), which smoothly follows the player with a margin, this
        jumps straight there (e.g. a fresh/loaded game with no saved
        camera position yet)."""
        self.x = rect.centerx - self.screen_width // 2
        self.y = rect.centery - self.screen_height // 2

    def update(self, player):
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
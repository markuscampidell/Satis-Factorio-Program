class Camera:
    def __init__(self, width, height, margin=400, smooth=0.05):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.margin = margin
        self.smooth = smooth

    def update(self, player, screen_width, screen_height):
        playerx = player.rect.x - self.x
        playery = player.rect.y - self.y

        # Horizontal camera movement
        if playerx < self.margin:
            self.x -= (self.margin - playerx) * self.smooth
        elif playerx > screen_width - self.margin:
            self.x += (playerx - (screen_width - self.margin)) * self.smooth

        # Vertical camera movement
        if playery < self.margin:
            self.y -= (self.margin - playery) * self.smooth
        elif playery > screen_height - self.margin:
            self.y += (playery - (screen_height - self.margin)) * self.smooth
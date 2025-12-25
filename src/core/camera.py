class Camera:
    def __init__(self, width, height, margin=400):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.margin = margin

    def update(self, player, screen_width, screen_height):
        # Player position on screen
        px = player.rect.x - self.x
        py = player.rect.y - self.y

        # Horizontal camera movement
        if px < self.margin:
            self.x -= self.margin - px
        elif px > screen_width - self.margin:
            self.x += px - (screen_width - self.margin)

        # Vertical camera movement
        if py < self.margin:
            self.y -= self.margin - py
        elif py > screen_height - self.margin:
            self.y += py - (screen_height - self.margin)
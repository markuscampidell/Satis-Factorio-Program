import pygame as py
from constants.itemdata import get_item_by_id

class PlayerInventoryUI:
    SLOT_SIZE = 64
    PADDING = 10

    def __init__(self, player):
        self.player = player
        self.open = False
        width = self.player.inventory.width * self.SLOT_SIZE + self.PADDING * 2
        height = self.player.inventory.height * self.SLOT_SIZE + self.PADDING * 2
        self.image = py.Surface((width, height))
        self.image.fill("#CAC8E4")
        self.rect = self.image.get_rect(x=0,centery=540)
        self.font = py.font.SysFont("Arial", 10)

        self.dragging = False
        self.drag_offset = (0, 0)
        self.image.set_alpha(200)

    def draw(self, screen):
        if not self.open:
            return

        # Background
        screen.blit(self.image, self.rect.topleft)

        # Draw grid slots
        for y in range(self.player.inventory.height):
            for x in range(self.player.inventory.width):
                slot_rect = py.Rect(
                    self.rect.x + self.PADDING + x * self.SLOT_SIZE,
                    self.rect.y + self.PADDING + y * self.SLOT_SIZE,
                    self.SLOT_SIZE,
                    self.SLOT_SIZE
                )
                py.draw.rect(screen, "#AAAAAA", slot_rect, 2)  # draw slot border

                slot = self.player.inventory.slots[y][x]
                if slot:
                    item_id = slot["item"]
                    amount = slot["amount"]

                    # Get the Item object
                    item = get_item_by_id(item_id)
                    if item and item.image:
                        # Scale sprite to fit slot
                        img = py.transform.scale(item.image, (self.SLOT_SIZE - 10, self.SLOT_SIZE - 10))
                        screen.blit(img, (slot_rect.x + 5, slot_rect.y + 5))

                    # Draw stack amount
                    text = self.font.render(str(amount), True, "#000000")
                    # Put it in the bottom-right corner
                    text_rect = text.get_rect(bottomright=(slot_rect.right - 5, slot_rect.bottom - 5))
                    screen.blit(text, text_rect)
    
    def close(self):
        self.open = False
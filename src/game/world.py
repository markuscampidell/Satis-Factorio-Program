class World:
    def __init__(self, player):
        self.player = player
        self.machines = []
        self.belt_segments = []
        self.belt_map = {}

    def is_rect_blocked(self, rect):
        if self.player.rect.colliderect(rect):
            return True

        for machine in self.machines:
            if machine.rect.colliderect(rect):
                return True

        for seg in self.belt_segments:
            if seg.rect.colliderect(rect):
                return True

        return False
    
    def get_machine_at_screen_pos(self, mx, my, camera):
        world_x = mx + camera.x
        world_y = my + camera.y

        for machine in self.machines:
            if machine.rect.collidepoint(world_x, world_y):
                return machine

        return None

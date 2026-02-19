import pygame as py

class BeltSpriteManager:
    def __init__(self):
        self.straights = {}
        self.curves = {}

        self.straight_paths = {(1, 0): "src/assets/sprites/conveyors/straight/belt_straight_right.png", # right
                               (-1, 0): "src/assets/sprites/conveyors/straight/belt_straight_left.png", # left
                               (0, -1): "src/assets/sprites/conveyors/straight/belt_straight_up.png", # up
                               (0, 1): "src/assets/sprites/conveyors/straight/belt_straight_down.png",} # down
        
        """The straight sprite names are based off the outgoing direction of the belt segment"""

        self.curve_paths = {(1, 0, 0, -1): "src/assets/sprites/conveyors/curve/belt_curve_right_up.png",  # right→up
                            (1, 0, 0, 1): "src/assets/sprites/conveyors/curve/belt_curve_right_down.png", # right→down
                            (-1,0,0,-1): "src/assets/sprites/conveyors/curve/belt_curve_left_up.png",   # left→up
                            (-1,0,0,1): "src/assets/sprites/conveyors/curve/belt_curve_left_down.png", # left→down
                            (0,-1,1,0): "src/assets/sprites/conveyors/curve/belt_curve_up_right.png",    # up→right
                            (0,-1,-1,0): "src/assets/sprites/conveyors/curve/belt_curve_up_left.png",    # up→left
                            (0,1,1,0): "src/assets/sprites/conveyors/curve/belt_curve_down_right.png",  # down→right
                            (0,1,-1,0): "src/assets/sprites/conveyors/curve/belt_curve_down_left.png",} # down→left
        
        """The curve sprite names are based off the incoming direction and outgoing direction of the belt segment in that order"""

    def load_images(self):
        self.straights = {k: py.image.load(v).convert_alpha() for k, v in self.straight_paths.items()}
        self.curves = {k: py.image.load(v).convert_alpha() for k, v in self.curve_paths.items()}

    def get_straight(self, direction) -> py.Surface:
        key = (direction.x, direction.y)
        return self.straights.get(key)

    def get_curve(self, incoming, outgoing) -> py.Surface:
        key = (incoming.x, incoming.y, outgoing.x, outgoing.y)
        return self.curves.get(key)
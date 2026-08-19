# systems.conveyors.belt_sprite_manager
import pygame as py

from game.grid import Grid

class BeltSegmentSpriteManager:
    def __init__(self):
        self.straights = {}
        self.curves = {}
        self.intersections = {}
        self.crosssections = {}
        self.opposites = {}

        self.straight_paths = {(1, 0): "src/assets/sprites/conveyors/straight/belt_straight_right.png", # right
                               (-1, 0): "src/assets/sprites/conveyors/straight/belt_straight_left.png", # left
                               (0, -1): "src/assets/sprites/conveyors/straight/belt_straight_up.png", # up
                               (0, 1): "src/assets/sprites/conveyors/straight/belt_straight_down.png",} # down

        """The straight sprite names are based off the outgoing direction of the belt segment"""

        self.curve_paths = {(1, 0, 0, -1): "src/assets/sprites/conveyors/curve/belt_curve_right_to_up.png", # right --> up
                            (1, 0, 0, 1): "src/assets/sprites/conveyors/curve/belt_curve_right_to_down.png", # right --> down
                            (-1,0,0,-1): "src/assets/sprites/conveyors/curve/belt_curve_left_to_up.png", # left --> up
                            (-1,0,0,1): "src/assets/sprites/conveyors/curve/belt_curve_left_to_down.png", # left --> down
                            (0,-1,1,0): "src/assets/sprites/conveyors/curve/belt_curve_up_to_right.png", # up --> right
                            (0,-1,-1,0): "src/assets/sprites/conveyors/curve/belt_curve_up_to_left.png", # up --> left
                            (0,1,1,0): "src/assets/sprites/conveyors/curve/belt_curve_down_to_right.png", # down --> right
                            (0,1,-1,0): "src/assets/sprites/conveyors/curve/belt_curve_down_to_left.png",} # down --> left

        """The curve sprite names are based off the incoming direction and outgoing direction of the belt segment in that order, seperated by _to_"""

        self.intersection_paths = {(0, -1, 1, 0): "src/assets/sprites/conveyors/intersection/right_up_to_right.png",   # right, up --> right
                                   (0, 1, 1, 0): "src/assets/sprites/conveyors/intersection/down_right_to_right.png",  # down, right --> right
                                   (0, -1, -1, 0): "src/assets/sprites/conveyors/intersection/left_up_to_left.png",    # left, up --> left
                                   (0, 1, -1, 0): "src/assets/sprites/conveyors/intersection/down_left_to_left.png",   # down, left --> left
                                   (1, 0, 0, -1): "src/assets/sprites/conveyors/intersection/right_up_to_up.png",      # right, up --> up
                                   (-1, 0, 0, -1): "src/assets/sprites/conveyors/intersection/left_up_to_up.png",      # left, up --> up
                                   (1, 0, 0, 1): "src/assets/sprites/conveyors/intersection/down_right_to_down.png",    # right, down --> down
                                   (-1, 0, 0, 1): "src/assets/sprites/conveyors/intersection/down_left_to_down.png",}  # left, down --> down

        """The intersection sprite names are based off the incoming directions and outgoing direction of the belt segment in that order, seperated by _to_"""

        self.opposite_paths = {(1, 0): "src/assets/sprites/conveyors/opposite/down_up_to_right.png", # down, up --> right
                               (-1, 0): "src/assets/sprites/conveyors/opposite/down_up_to_left.png", # down, up --> left
                               (0, -1): "src/assets/sprites/conveyors/opposite/right_left_to_up.png", # right, left --> up
                               (0, 1): "src/assets/sprites/conveyors/opposite/right_left_to_down.png",} # right, left --> down

        """The opposite sprite names are based off the incoming directions and outgoing direction of the belt segment in that order, seperated by _to_"""

        self.crosssection_paths = {(1, 0): "src/assets/sprites/conveyors/crosssection/down_right_up_to_right.png", # down, right, up --> right
                                   (-1, 0): "src/assets/sprites/conveyors/crosssection/down_left_up_to_left.png", # down, left, up --> left
                                   (0, -1): "src/assets/sprites/conveyors/crosssection/right_left_up_to_up.png", # right, left, up --> up
                                   (0, 1): "src/assets/sprites/conveyors/crosssection/down_right_left_to_down.png",} # down, right, left --> down

        """The crosssection sprite names are based off the incoming directions and outgoing direction of the belt segment in that order, seperated by _to_"""

    def load_images(self, cell_size=None):
        cell_size = cell_size or Grid.CELL_SIZE

        self.straights = {k: py.image.load(v).convert_alpha() for k, v in self.straight_paths.items()}
        self.curves = {k: py.image.load(v).convert_alpha() for k, v in self.curve_paths.items()}
        self.intersections = {k: py.image.load(v).convert_alpha() for k, v in self.intersection_paths.items()}
        self.opposites = {k: py.image.load(v).convert_alpha() for k, v in self.opposite_paths.items()}
        self.crosssections = {k: py.image.load(v).convert_alpha() for k, v in self.crosssection_paths.items()}

    def get_sprite(self, incoming_directions, outgoing) -> py.Surface:
        """Picks which belt image to show for this segment"""

        dirs = {(d.x, d.y) for d in incoming_directions}
        out = (outgoing.x, outgoing.y)

        perpendiculars = {
            (1, 0): ((0, -1), (0, 1)),
            (-1, 0): ((0, -1), (0, 1)),
            (0, -1): ((1, 0), (-1, 0)),
            (0, 1): ((1, 0), (-1, 0)),
        }

        first, second = perpendiculars[out]

        has_straight = out in dirs
        has_first = first in dirs
        has_second = second in dirs

        if has_straight and has_first and has_second:
            return self.crosssections[out]

        if has_straight and has_first:
            return self.intersections[first + out]

        if has_straight and has_second:
            return self.intersections[second + out]

        if has_first and has_second:
            return self.opposites[out]

        if has_first:
            return self.curves[first + out]

        if has_second:
            return self.curves[second + out]

        return self.straights[out]
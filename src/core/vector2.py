# core.vector2
class Vector2():
    """A point or a direction, made of an x and a y. Used all over the
    game for positions, movement, and which way something is facing."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @classmethod
    def up(cls):
        return cls(0, -1)
    
    @classmethod
    def down(cls):
        return cls(0, 1)
    
    @classmethod
    def left(cls):
        return cls(-1, 0)
    
    @classmethod
    def right(cls):
        return cls(1, 0)
    
    def normalize(self):
        """Makes this vector exactly 1 long, but keeps it pointing the
        same way. If it has no length at all, just gives back (0, 0)
        instead of crashing."""
        length = self.length()
        if length == 0: return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)
    
    def length(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    @classmethod
    def dot(cls, vector1: "Vector2", vector2: "Vector2"):
        """A number that says how much two vectors point the same way.
        Bigger means more "in the same direction", negative means they
        point more away from each other."""
        return vector1.x * vector2.x + vector1.y * vector2.y

    @classmethod
    def from_points(cls, point1: tuple, point2: tuple):
        """Makes a vector that points from point1 straight to point2."""
        return cls(point2[0] - point1[0], point2[1] - point1[1])
    
    def __add__(self, other: "Vector2"):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: "Vector2"):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __str__(self):
        return f"Vector2({self.x}, {self.y})"
    
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)

    def __eq__(self, other):
        if not isinstance(other, Vector2):
            return False
        return self.x == other.x and self.y == other.y

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __truediv__(self, scalar: float):
        return Vector2(self.x / scalar, self.y / scalar)

    def __itruediv__(self, scalar: float):
        self.x /= scalar
        self.y /= scalar
        return self
    
    def snapped(self, threshold=0.1):
        """Rounds each axis down to -1, 0 or 1. Used so tiny math mistakes
        (like 0.999992 instead of 1) don't mess up direction checks."""
        x = 0 if abs(self.x) < threshold else (1 if self.x > 0 else -1)
        y = 0 if abs(self.y) < threshold else (1 if self.y > 0 else -1)
        return Vector2(x, y)
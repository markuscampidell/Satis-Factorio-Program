class Vector2():
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
        length = self.length()  # nutzt die neue length()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)
    
    def magnitude(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    # NEU: alias length() für kompatibilität
    def length(self):
        return self.magnitude()
    
    @classmethod
    def dot(cls, vector1: "Vector2", vector2: "Vector2"):
        return vector1.x * vector2.x + vector1.y * vector2.y
    
    @classmethod
    def from_points(cls, point1: tuple, point2: tuple):
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

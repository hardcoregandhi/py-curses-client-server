from typing import NamedTuple
class Position2D(NamedTuple):
    x : int
    y : int

    def __str__(self):
        return f"{self.x}, {self.y}"
    
    def to_dict(self):
        return {'x': self.x, 'y': self.y}
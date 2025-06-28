from typing import NamedTuple, List
class Position2D(NamedTuple):
    x : int
    y : int

    def __str__(self):
        return f"{self.x}, {self.y}"
    
    def to_dict(self):
        return {'x': self.x, 'y': self.y}
    
    @staticmethod
    def from_list(position: List[int]) -> 'Position2D':
        """Create a Position2D instance from a list of two integers."""
        if len(position) != 2:
            raise ValueError("Position list must contain exactly two elements.")
        return Position2D(position[0], position[1])
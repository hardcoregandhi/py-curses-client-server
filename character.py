from collections import namedtuple

Position2D = namedtuple('Position2D', ['x', 'y'])

class Character:
    def __init__(self, name = "Unnamed"):
        # Get the height and width of the window and round to even
        self.name = name
        self.health = 5
        self.stamina = 5
        self.mana = 5
        self.strength = 5
        self.defence = 5
        self.speed = 5
        self.position = Position2D(5,5)

    def moveTo(self, new_x, new_y, game_map):
        """Move the character to a new position if valid."""
        tile = game_map.get_tile(new_x, new_y)
        if tile and tile.tile_type != 'unknown' and game_map.is_walkable(new_x, new_y):  # Check if the tile is valid
            self.position = Position2D(new_x, new_y)  # Update position if valid
            return True
        return False  # Move was not valid
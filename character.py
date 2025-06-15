from collections import namedtuple
from position import Position2D



class Character:
    def __init__(self, name = "Unnamed"):
        # Get the height and width of the window and round to even
        self.name = name
        self.level = 1
        self.xp = 0
        self.health = self.max_health = 5
        self.stamina = self.max_stamina = 5
        self.mana = self.max_mana = 5
        self.strength = 5
        self.defence = 5
        self.speed = 5
        self.position = Position2D(5,5)
    
    def __iter__(self):
        yield {
            "name" : self.name, 
            "level" : self.level, 
            "xp" : self.xp, 
            "health" : self.health, 
            "stamina" : self.stamina, 
            "mana" : self.mana, 
            "strength" : self.strength, 
            "defence" : self.defence, 
            "speed" : self.speed, 
            "position" : self.position
        }

    def moveTo(self, new_x, new_y, game_map):
        """Move the character to a new position if valid."""
        tile = game_map.get_tile(new_x, new_y)
        if tile and tile.tile_type != 'unknown' and game_map.is_walkable(new_x, new_y):  # Check if the tile is valid
            self.position = Position2D(new_x, new_y)  # Update position if valid
            return True
        return False  # Move was not valid
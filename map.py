import random

# class Tile:
#     def __init__(self, tile_type, additional_data=None):
#         self.tile_type = tile_type
#         self.active_timer = None
#         self.ready = False
#         self.additional_data = additional_data or {}

#     def __repr__(self):
#         return f"Tile(type={self.tile_type}, data={self.additional_data})"
    
import threading
import uuid
import json
from position import Position2D
import logging
import math

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Tile:
    def __init__(self, event_manager, tile_type, position, additional_data=None):
        self.event_manager = event_manager
        self.tile_type = tile_type
        self.position = position 
        self.work_time = 5  # Time before the tile can be activated
        self.cooldown_time = 5      # Time before the tile can be activated again
        self.is_ready_to_work = True        # Indicates if the tile can be worked
        self.is_finished_work = False        # Indicates if the tile has finished work
        self.is_cooling_down = False
        self.additional_data = additional_data or {}
        self.id = str(uuid.uuid4())  # Generate a unique ID

    def __repr__(self):
        return (f"Tile(tile_type={self.tile_type!r}, position={self.position!r}, "
                f"work_time={self.work_time!r}, cooldown_time={self.cooldown_time!r}, "
                f"is_ready_to_work={self.is_ready_to_work!r}, "
                f"is_finished_work={self.is_finished_work!r}, "
                f"is_cooling_down={self.is_cooling_down!r}, "
                f"additional_data={self.additional_data!r}, id={self.id!r})")

    def work_complete(self):
        """Called when the activation timer completes."""
        logging.info(f"Tile {self.id} is ready to activate.")
        self.is_ready_to_work = False
        self.is_finished_work = True
        # Notify players that the tile can be activated
        self.event_manager.publish('tile_worked', None, self.position, True)

    def work(self, player_id):
        """Player works the tile, starting the work timer."""
        logging.info(self.position)
        if self.is_ready_to_work:
            logging.info(f"Player works tile {self.id}.")
            self.is_ready_to_work = False
            self.is_finished_work = False
            # Start the activation timer
            threading.Timer(self.work_time, self.work_complete).start()
            self.event_manager.publish('tile_working', player_id, self.position, True)
        else:
            logging.info(f"Tile {self.id} is not ready to work.")
            self.event_manager.publish('tile_working', player_id, self.position, False)

    def cooldown(self, player_id):
        """Player activates the tile, starting the cooldown timer."""
        if self.is_finished_work:
            logging.info(f"Player activates tile {self.id}.")
            self.is_finished_work = False
            self.is_cooling_down = True
            # Start the cooldown timer
            threading.Timer(self.cooldown_time, self.cooldown_complete).start()
            self.event_manager.publish('tile_activated', player_id, self.position, True)
        else:
            logging.info(f"Tile {self.id} is not finished working.")
            self.event_manager.publish('tile_activated', player_id, self.position, False)

    def cooldown_complete(self):
        """Called when the cooldown timer completes."""
        logging.info(f"Tile {self.id} is ready to be worked again.")
        self.is_ready_to_work = True
        self.is_cooling_down = False
        # Notify players that the tile can be worked again
        self.event_manager.publish('tile_ready', None, self.position, True)

    def notify_players(self):
        """Notify players about the tile's status."""
        # Implement your notification logic here
        logging.info(f"Notify players: Tile {self.id} status updated.")

    def to_dict(self):
        return {
            'tile_type' : self.tile_type,
            'position' : self.position,
            'work_time' : self.work_time,
            'cooldown_time' : self.cooldown_time,
            'is_ready_to_work' : self.is_ready_to_work,
            'is_finished_work' : self.is_finished_work,
            'is_cooling_down'  : self.is_cooling_down,
            'additional_data' : self.additional_data,
            'id' : self.id,
        }


class GameMap:
    def __init__(self, event_manager, width, height, map_string):
        self.event_manager = event_manager
        self.width = width
        self.height = height
        self.map = []
        self.grid = None # Pathfinding
        self.additional_data = {}
        self.create_map(event_manager, map_string)

    def create_map(self, event_manager, map_string):
        tile_mapping = {
            'x': 'plain',
            'o': 'dungeon',
            'w': 'woods',
            'r': 'river',
            'm': 'mountain',
            'f': 'farmland',
            'c': 'castle',
            'g': 'grassland',
            's': 'swamp',
            'd': 'desert',
            't': 'town',
            'l': 'lake',
            'p': 'path',
            'h': 'hill',
            'b': 'bridge',
        }

        for y in range(self.height):
            map_row = []
            for x in range(self.width):
                index = y * self.width + x  # Calculate the index in the string
                char = map_string[index]
                tile_type = tile_mapping.get(char, 'unknown')  # Default to 'unknown' if not found
                if tile_type != 'unknown':
                    map_row.append(Tile(event_manager, tile_type, Position2D(x,y)))
                else:
                    raise Exception()
            self.map.append(map_row)

    def display_map(self):
        for row in self.map:
            line = ''.join(tile.tile_type[0] for tile in row)  # Display first letter of tile type
            logging.info(line)

    def set_additional_data(self, x, y, data):
        self.additional_data[(y, x)] = data
        self.map[y][x].additional_data = data

    def get_cell_data(self, x, y):
        return self.additional_data.get((y, x), None)
    
    def get_tile(self, x, y):
        """Retrieve the tile at the specified coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.map[y][x]
        return None  # Return None if the coordinates are out of bounds
    
    def is_walkable(self, x, y):
        """Check if the tile at (x, y) is walkable."""
        tile = self.get_tile(x, y)
        return tile and tile.tile_type not in ['unknown', 'mountain', 'river']  # Add more non-walkable types as needed

    def to_dict(self):
        return {
            'width': self.width,
            'height': self.height,
            'map': [[tile.to_dict() for tile in row] for row in self.map],
            'additional_data': self.additional_data
        }

    def find_closest_player_to_player(self, player_id, player_pos, player_positions):
        """Find the closest player to the given player_id."""
        # if player_id not in player_positions:
        #     logging.warning("Couldn't find initiating player in player_positions")
        #     return None, None  # Player not found
        if not player_positions:
            return None, None
        player_position = Position2D.from_list(player_pos)
        closest_player_id = None
        closest_distance = float('inf')

        for other_player_id, other_data in player_positions.items():
            other_position = Position2D.from_list(other_data['position'])
            logging.info(f"other_player_id {other_player_id} other_position {other_position}")
            if other_player_id == player_id:
                continue  # Skip the same player

            # Calculate the distance
            # distance = self.calculate_distance(player_position, other_position)

            # Check if the path is walkable
            path = self.find_walkable_path(player_position, other_position)
            if (path):
                if len(path) < closest_distance:
                    closest_distance = len(path)
                    closest_position = other_position
                    closest_player_id = other_player_id

        return closest_player_id, closest_position

    def calculate_distance(self, pos1, pos2):
        """Calculate the Euclidean distance between two positions."""
        return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)

    # def is_path_walkable(self, start, end):
    #     """Check if the path between start and end positions is walkable."""
    #     # You can implement a simple line-of-sight check or a pathfinding algorithm here.
    #     # For simplicity, we'll check all tiles between the two positions.
    #     x1, y1 = start.x, start.y
    #     x2, y2 = end.x, end.y

    #     # Use Bresenham's line algorithm to get the points between the two positions
    #     points = self.bresenham(x1, y1, x2, y2)

    #     for x, y in points:
    #         if not self.is_walkable(x, y):
    #             return False  # Found a non-walkable tile

    #     return True

    def bresenham(self, x1, y1, x2, y2):
        """Bresenham's line algorithm to get the points between two coordinates."""
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            err2 = err * 2
            if err2 > -dy:
                err -= dy
                x1 += sx
            if err2 < dx:
                err += dx
                y1 += sy

        return points
    

    def find_walkable_path(self, start, end):
        # Create a grid representation for pathfinding
        if not self.grid:
            grid_data = [[1 if self.is_walkable(x, y) else 0 for x in range(self.width)] for y in range(self.height)]
            self.grid = grid = Grid(matrix=grid_data)

        # Define start and end nodes
        start_node = self.grid.node(start.x, start.y)
        end_node = self.grid.node(end.x, end.y)

        # Create an A* finder
        finder = AStarFinder()

        # Find the path
        path, _ = finder.find_path(start_node, end_node, self.grid)
        return path

    def is_path_walkable(self, start, end):
        """Check if the path between start and end positions is walkable using A*."""
        path = self.find_walkable_path(start, end)
        return path is not None  # Return True if a path exists, False otherwise

test_map_string = \
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\
"xxxxxxxxxx"\

default_map_string = \
"wwwwwwwwwwwwwwwwwwwwwwwwwmrmwwwwwwwwwwwwrwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwbwwwwwwwwwwwwwrwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwmwwwwwwwwwwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwmwwwwwwwwwwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwwwwwwwwwwwwwwwwwwww"\
"rrrbrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrbrrr"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwwwwwwwwwwwwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwrmmwwwwwrwwwwwwwwwwwwwwwwwwwwwww"\
"wwwwwwwwwwwwwwwwrrrwwwwwwwrwwwwwwwwwmmwcwwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwbwwwwwwwwwmmwwwwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwrrrmrmwwwwwwwwwwwwwwwwwwwwww"\


default_map_string2 = """
xffpppddxxxxxxdddxxpppffxmrmssspppwwwwoxrffftttwww
xffphhhdxxxxxgdddxxppppfxdbdssspppwwsssxrffftttwww
xffphhhdpppxxgdddfwwpppllwrwdssmssswsssxgggllltxxx
wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwwwwwwwwwwwwwwwwwwww
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
wwwwwwwwwwwwwwwwwwwwwwwwwwrwwwwwwwwwwwwwwwwwwwwwww
ffxxwwwwwwwwwwwwwwrmmgggfwrwbxxfffxxwwwwwwwwwwgxxx
fffxxxgggfxxxxxxrrrxxgggffrbbxxfffxxmmgcbbtpppxxxx
fffwoogggfxxxwwwxxxpppggffbxxxhhhwxxmmhbbbtttxxxhh
fffwoogggfxxxwwwxxxppprrrmrmxxhhhwxxxxhbbbtttxxxhh
"""

class MapGenerator:
    def __init__(self, game_map):
        self.width = game_map.width
        self.height = game_map.height
        self.tile_types = ['x', 'o', 'w', 'r', 'm', 'f', 'c', 'g', 's', 'd', 't', 'l', 'p', 'h', 'b']

    def generate_map_string(self):
        # Create an empty map
        map_grid = [['x' for _ in range(self.width)] for _ in range(self.height)]

        # Define clusters of different terrain types
        clusters = {
            'o': 5,  # Dungeon
            'w': 10, # Woods
            'r': 5,  # River
            'm': 5,  # Mountain
            'f': 15, # Farmland
            'c': 1,  # Castle
            'g': 10, # Grassland
            's': 5,  # Swamp
            'd': 5,  # Desert
            't': 3,  # Town
            'l': 2,  # Lake
            'p': 10, # Path
            'h': 5,  # Hill
            'b': 2,  # Bridge
        }

        # Place clusters of tiles
        for tile_type, count in clusters.items():
            for _ in range(count):
                # Randomly choose a starting point for the cluster
                start_x = random.randint(0, self.width - 1)
                start_y = random.randint(0, self.height - 1)

                # Create a small cluster around the starting point
                for dx in range(-1, 2):  # -1, 0, 1
                    for dy in range(-1, 2):  # -1, 0, 1
                        x = start_x + dx
                        y = start_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            map_grid[y][x] = tile_type

        # Flatten the map grid into a string
        map_string = ''.join(''.join(row) for row in map_grid)
        
        # Format the map string for easy copy-pasting
        formatted_map_string = 'map_string = """\n'
        for i in range(self.height):
            formatted_map_string += map_string[i * self.width:(i + 1) * self.width] + '\n'
        formatted_map_string += '"""'
        
        logging.info(formatted_map_string)  # Print the formatted string for copy-pasting
        return map_string

from event_manager import EventManager

class GameMapEncoderDecoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GameMap):
            return obj.to_dict()
        return super().default(obj)

    @staticmethod
    def from_dict(data):
        width = data['width']
        height = data['height']
        map_string = ''.join([''.join([tile['tile_type'][0] for tile in row]) for row in data['map']])
        game_map = GameMap(EventManager(), width, height, map_string)
        map = data['map']
        for tiles in map:
            for tile in tiles:
                new_tile = Tile(
                    game_map.event_manager,
                    tile_type=tile['tile_type'],
                    position=Position2D(tile['position'][0], tile['position'][1])
                )
                # import pdb; pdb.set_trace()
                new_tile.work_time = tile['work_time']
                new_tile.cooldown_time = tile['cooldown_time']
                new_tile.is_ready_to_work = tile['is_ready_to_work']
                new_tile.is_finished_work = tile['is_finished_work']
                new_tile.is_cooling_down = tile['is_cooling_down']
                new_tile.additional_data = tile['additional_data']
                new_tile.id = 0
                
                x, y = tile['position']
                game_map.map[y][x] = new_tile  # Place the tile in the correct position
        return game_map

# Example usage
if __name__ == "__main__":
    width = 50
    height = 10

    # Create a GameMap instance with a placeholder map string
    placeholder_map_string = "x" * (width * height)  # Placeholder for the initial map
    game_map = GameMap(width, height, placeholder_map_string)

    # Create an instance of MapGenerator using the GameMap instance
    map_generator = MapGenerator(game_map)

    # Generate the map string
    generated_map_string = map_generator.generate_map_string()

    # Create a new GameMap instance using the generated map string
    game_map = GameMap(width, height, generated_map_string)

    # Display the map
    game_map.display_map()

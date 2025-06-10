import random

class Tile:
    def __init__(self, tile_type, additional_data=None):
        self.tile_type = tile_type
        self.additional_data = additional_data or {}

    def __repr__(self):
        return f"Tile(type={self.tile_type}, data={self.additional_data})"


class GameMap:
    def __init__(self, width, height, map_string):
        self.width = width
        self.height = height
        self.map = []
        self.additional_data = {}
        self.create_map(map_string)

    def create_map(self, map_string):
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
                    map_row.append(Tile(tile_type))
                else:
                    raise Exception()
            self.map.append(map_row)

    def display_map(self):
        for row in self.map:
            line = ''.join(tile.tile_type[0] for tile in row)  # Display first letter of tile type
            print(line)

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

    
default_map_string = \
"wwwwwwwwwwwwwwwwwwwwwwwwwmrmwwwwwwwwwwwwrwwwwwwwww"\
"wwwwwwwwwwwwwwwwwwwwwwwwwwbwwwwwwwwwwwwwrwwwwwwwww"\
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
        
        print(formatted_map_string)  # Print the formatted string for copy-pasting
        return map_string


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

import curses

class ScreenMeasurements:
    def __init__(self, stdscr):
        # Get the height and width of the window and round to even
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self.height = self.round_to_even(self.height)
        self.width = self.round_to_even(self.width)

        # Calculate the height for the bottom panel
        self.half_height = self.height // 2
        self.top_panel_height = self.height - self.half_height  # Remaining height for the top panels

        # Calculate the width for the top panels
        half_width = self.width // 2  # Each top panel will take half of the width

        self.top_panel1 = curses.newwin(self.top_panel_height, half_width, 0, 0)
        self.top_panel2 = curses.newwin(self.top_panel_height, half_width, 0, half_width)
        self.bottom_panel = curses.newwin(self.half_height, self.width, self.top_panel_height, 0)
    def round_to_even(self, n):
        return n if n % 2 == 0 else n - 1
    

def create_health_bar(current_health, max_health, bar_length=30):
    # Calculate the proportion of health
    health_ratio = current_health / max_health
    filled_length = int(bar_length * health_ratio)  # Calculate filled length of the bar
    bar = '█' * filled_length + '-' * (bar_length - filled_length)  # Create the bar

    # Print the health bar
    return (f"|{bar}| {current_health}/{max_health} ({health_ratio:.0%})")

def draw_map(window, screen, game_map, character, player_positions):
    # Calculate the starting position to draw the map
    window_height, window_width = window.getmaxyx()
    start_x = max(0, character.position.x - window_width // 2) -2
    start_y = max(0, character.position.y - window_height // 2) -2

    # Draw the map within the window
    for y in range(window_height):
        for x in range(window_width):
            map_x = start_x + x
            map_y = start_y + y
            tile = game_map.get_tile(map_x, map_y)
            if tile:
                # Get the first character of the tile type for display
                tile_char = tile.tile_type[0]  # Get the first character of the tile type
                window.addch(y, x, tile_char)

            # Check if the current position matches the character's position
            if (map_x, map_y) == (character.position.x, character.position.y):
                window.addch(y, x, '@')  # Draw the character at its position
            for player_id, position in player_positions.items():
                print(f"{player_id}: {position}\n")
                if (map_x, map_y) == (position[0], position[1]):
                    window.addch(y, x, '%')  # Draw the character at its position

    screen.top_panel2.box()
    screen.top_panel2.refresh()

def draw(screen, output, input_buffer, game_map, character, player_positions):
    # Clear the screen
    draw_top_left(screen, character)
    # draw_top_right(screen)
    draw_map(screen.top_panel2, screen, game_map, character, player_positions)
    draw_bottom(screen, output, input_buffer)

def draw_top_left(screen, character):
    # Create the first top panel (window)
    screen.top_panel1.box()
    screen.top_panel1.addstr(0, 1, "Character Sheet", curses.A_BOLD)
    (panel_height, panel_width) = screen.top_panel1.getmaxyx()
    # Initialize variables
    max_entries_per_column = (panel_height-4)  # Maximum number of entries that can fit in one column
    current_column = 0
    current_row = 1

    # Iterate through the character's attributes
    for i, (entry, value) in enumerate(character.__dict__.items()):
        if "max_" in entry:
            continue
        text = f"{entry.capitalize():<{10}} : {value}"[:panel_width]
        # Check if we need to move to the next column
        if current_row >= max_entries_per_column:
            current_column += 1
            current_row = 1

        # Calculate the position to draw the entry
        x = screen.round_to_even(3 + current_column * (panel_width / 2))  # Add some space between columns
        y = current_row

        # Draw the entry in the specified position
        screen.top_panel1.addstr(y, int(x), text)

        # Move to the next row
        current_row += 1
    screen.top_panel1.addstr(panel_height -4, 2, f"{'Health':<{11}}: " + create_health_bar(character.health, character.max_health))
    screen.top_panel1.addstr(panel_height -3, 2, f"{'Stamina':<{11}}: " + create_health_bar(character.stamina, character.max_stamina))
    screen.top_panel1.addstr(panel_height -2, 2, f"{'Mana':<{11}}: " + create_health_bar(character.mana, character.max_mana))
    screen.top_panel1.refresh()

def draw_top_right(screen):
    # Create the second top panel (window)
    # screen.top_panel2.addstr(0, 1, "Top Panel 2", curses.A_BOLD)
    # screen.top_panel2.addstr(1, 1, "This is the second top panel.")
    # screen.top_panel2.addstr(2, 1, f"height {screen.height} width {screen.width}")
    screen.top_panel2.box()
    screen.top_panel2.refresh()

def draw_bottom(screen, output, input_buffer):
    # Create the bottom panel (window)
    print(input_buffer)
    screen.bottom_panel.clear()
    screen.bottom_panel.addstr(0, 1, "Bottom Panel", curses.A_BOLD)
    screen.bottom_panel.addstr(1, 1, "This is the bottom panel spanning the full width.")
    # Display the output in the bottom panel
    screen.bottom_panel.addstr(3, 1, output)  # Adjust the row as needed

    # Display the input buffer
    screen.bottom_panel.addstr(5, 1, "Input: " + input_buffer)  # Adjust the row as needed
    screen.bottom_panel.box()
    screen.bottom_panel.refresh()

    # Wait for user input to exit
    # stdscr.getch()
    # pdb.set_trace()
    # time.sleep(1)
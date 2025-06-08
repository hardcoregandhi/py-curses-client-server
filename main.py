import curses
from server import add_upnp_port_mapping
import map
from character import Character, Position2D
from draw import draw, ScreenMeasurements
from client import create_connection, send_update, positions_lock, player_positions


def handle_input(key, input_buffer, output, character, game_map):
    """Handle user input and update the input buffer and character position."""
    if key in (curses.KEY_BACKSPACE, 8):  # Handle backspace
        input_buffer = input_buffer[:-1]  # Remove the last character
    elif key == curses.KEY_ENTER or key == 10:  # Handle enter
        # Process the command
        if input_buffer.strip() == "quit":
            output = "Quitting..."  # Placeholder for future functionality
        elif input_buffer.strip() == "run":
            output = "Running command..."  # Placeholder for future functionality
        else:
            output = f"Unknown command: {input_buffer.strip()}"
        input_buffer = ""  # Clear the input buffer after processing
    elif key == curses.KEY_UP:  # Move up
        character.moveTo(character.position.x, character.position.y - 1, game_map)
    elif key == curses.KEY_DOWN:  # Move down
        character.moveTo(character.position.x, character.position.y + 1, game_map)
    elif key == curses.KEY_LEFT:  # Move left
        character.moveTo(character.position.x - 1, character.position.y, game_map)
    elif key == curses.KEY_RIGHT:  # Move right
        character.moveTo(character.position.x + 1, character.position.y, game_map)
    elif 32 <= key <= 126:  # Handle printable characters
        input_buffer += chr(key)  # Add character to input buffer

    return input_buffer, output

def init_game():
    game_map = map.GameMap(50, 10, map.default_map_string)  # Example map size
    character = Character("Player")  # Start in the middle of the map
    return game_map, character

def main(stdscr):
    # Hide the cursor
    curses.curs_set(0)
    curses.cbreak()

    screen = ScreenMeasurements(stdscr)

    add_upnp_port_mapping()

    output = input_buffer = ""  # Initialize the input buffer
    stdscr.nodelay(True)  # Make getch non-blocking

    game_map, character = init_game()

    # Create connection to the server
    username='Player1'
    host='127.0.0.1'
    client_socket = create_connection(host, 43210, username)

    while True:
        with positions_lock:
            draw(screen, output, input_buffer, game_map, character, player_positions)  # Call draw to update the display
        key = stdscr.getch()  # Get user input

        input_buffer, output = handle_input(key, input_buffer, output, character, game_map)
        send_update(client_socket, username, character)
    # Close the socket when done (this part may not be reached in a typical game loop)
    client_socket.close()

# Initialize the curses application
curses.wrapper(main)

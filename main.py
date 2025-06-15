import curses
import argparse
from server import add_upnp_port_mapping
import map
from character import Character
from position import Position2D
from draw import draw, ScreenMeasurements
from client import positions_lock, player_positions, Connection

import logging
import sys

# Configure the logger
logging.basicConfig(
    filename='client.log',  # Specify the log file name
    filemode='w',        # Append mode; use 'w' to overwrite the file
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s',
    level=logging.DEBUG   # Set the logging level
)

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.exit(1)
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set the exception hook to log uncaught exceptions
sys.excepthook = log_exception

def try_move_player(connection, character, x, y):
    if character.moveTo(x, y, connection.map):
        connection.send_position_update(character)

def handle_input(key, input_buffer, output, character, connection):
    """Handle user input and update the input buffer and character position."""
    if key in (curses.KEY_BACKSPACE, 8):  # Handle backspace
        input_buffer = input_buffer[:-1]  # Remove the last character
    elif key == curses.KEY_ENTER or key == 10:  # Handle enter
        # Process the command
        if input_buffer.strip() == "quit":
            output = "Quitting..."  # Placeholder for future functionality
        elif input_buffer.strip() in ["w", "work"]:
            output = "Working tile..."
            connection.send_update(character, "work")
        elif input_buffer.strip() in ["a", "activate"]:
            output = "Activating tile..."
            connection.send_update(character, "activate")
        elif input_buffer.strip() == "run":
            output = "Running command..."  # Placeholder for future functionality
        else:
            output = f"Unknown command: {input_buffer.strip()}"
        input_buffer = ""  # Clear the input buffer after processing
    elif key == curses.KEY_UP:  # Move up
        try_move_player(connection, character, character.position.x, character.position.y - 1)
    elif key == curses.KEY_DOWN:  # Move down
        try_move_player(connection, character, character.position.x, character.position.y + 1)
    elif key == curses.KEY_LEFT:  # Move left
        try_move_player(connection, character, character.position.x - 1, character.position.y)
    elif key == curses.KEY_RIGHT:  # Move right
        try_move_player(connection, character, character.position.x + 1, character.position.y)
    elif 32 <= key <= 126:  # Handle printable characters
        input_buffer += chr(key)  # Add character to input buffer

    return input_buffer, output

def init_game(username):
    character = Character(username)  # Start in the middle of the map
    return character

def main(stdscr, host, username):
    # Hide the cursor
    curses.curs_set(0)
    curses.cbreak()

    screen = ScreenMeasurements(stdscr)

    add_upnp_port_mapping()

    output = input_buffer = ""  # Initialize the input buffer
    stdscr.nodelay(True)  # Make getch non-blocking

    character = init_game(username)

    # Create connection to the server with host and username
    connection = Connection(host, username=username)
    connection.send_position_update(character)

    while True:
        with positions_lock:
            draw(screen, output, input_buffer, connection, character, player_positions)  # Call draw to update the display
        key = stdscr.getch()  # Get user input

        input_buffer, output = handle_input(key, input_buffer, output, character, connection)

if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Game Client")
    parser.add_argument("-host", type=str, help="Host IP address of the server", default="127.0.0.1")
    parser.add_argument("-username", type=str, help="Username for the game", default="Player1")
    args = parser.parse_args()

    # Initialize the curses application
    curses.wrapper(lambda stdscr: main(stdscr, args.host, args.username))


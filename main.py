import curses
import argparse
from server import add_upnp_port_mapping
import map
from character import Character
from position import Position2D
from draw import draw, ScreenMeasurements
from client import positions_lock, player_positions, Connection
from views import View, Views

class GameState:
    def __init__(self, event_manager):
        self.current_view = View.WORLD
        self.event_manager = event_manager
        self.event_manager.subscribe("fight_initiated", self.fight_initiated)
        self.event_manager.subscribe("fight_concluded", self.fight_concluded)
        
    def fight_initiated(self, _,__,___):
        self.current_view = View.BATTLE

    def fight_concluded(self, _,__,___):
        self.current_view = View.WORLD

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


def handle_input(key, input_buffer, output, character, connection, game_state):
    """Handle user input and update the input buffer and character position."""
    if key in (curses.KEY_BACKSPACE, 8):  # Handle backspace
        input_buffer = input_buffer[:-1]  # Remove the last character
    elif key == curses.KEY_ENTER or key == 10:  # Handle enter
        # Process the command
        command = input_buffer.strip()
        # Handle the view change here, otherwise pass the handling to the view's handle_input()
        if command in ["l", "level", "levelup"]:
            game_state.current_view = View.LEVEL_UP
            return "", "Switching View"
        elif command in ["f", "fight"]:
            # game_state.current_view = View.BATTLE
            connection.send_action(character, "fight")
            return "", "Switching View"
        elif command in ["b", "back"]:
            game_state.current_view = View.WORLD
            return "", "Switching View"
        output = Views[game_state.current_view].handle_input(command, character, connection)
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

def init_game(connection, username):
    character = Character(connection, username)  # Start in the middle of the map
    return character

def main(stdscr, host, username):
    # Hide the cursor
    curses.curs_set(0)
    curses.cbreak()

    screen = ScreenMeasurements(stdscr)

    add_upnp_port_mapping()

    output = input_buffer = ""  # Initialize the input buffer
    stdscr.nodelay(True)  # Make getch non-blocking

    # Create connection to the server with host and username
    connection = Connection(host, username=username)
    character = init_game(connection, username)
    connection.send_position_update(character)

    game_state = GameState(connection.map.event_manager)

    while True:
        with positions_lock:
            Views[game_state.current_view].draw(screen, output, input_buffer, connection, character, player_positions)
        key = stdscr.getch()  # Get user input

        input_buffer, output = handle_input(key, input_buffer, output, character, connection, game_state)

if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Game Client")
    parser.add_argument("-host", type=str, help="Host IP address of the server", default="127.0.0.1")
    parser.add_argument("-username", type=str, help="Username for the game", default="Player1")
    args = parser.parse_args()

    # Initialize the curses application
    curses.wrapper(lambda stdscr: main(stdscr, args.host, args.username))


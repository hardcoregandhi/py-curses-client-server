from enum import Enum
import curses
from draw import draw, ScreenMeasurements


class View(Enum):
    WORLD = "world"
    LEVEL_UP = "levelup"

class BaseView:
    def draw(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def handle_input(self):
        raise NotImplementedError("Subclasses should implement this method.")

class WorldView(BaseView):
    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        draw(screen, output, input_buffer, connection, character, player_positions)

    def handle_input(self, command, character, connection):
        """Basic character actions."""
        output = ""
        
        if command in ["q", "quit"]:
            output = "Quitting..."  # Placeholder for future functionality
        elif command in ["w", "work"]:
            if character.stats.stamina:
                output = "Working tile..."
                connection.send_update(character, "work")
            else:
                output = "Not enough stamina to work."
        elif command in ["a", "activate"]:
            if character.stats.stamina:
                output = "Activating tile..."
                connection.send_update(character, "activate")
            else:
                output = "Not enough stamina to activate."
        elif command in ["r", "run"]:
            output = "Running command..."  # Placeholder for future functionality
        else:
            output = f"Unknown command: {command}"

        return output

class LevelUpView(BaseView):
    def __init__(self):
        self.level_up_win = None

    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        self.draw_top(screen, output, input_buffer, connection, character, player_positions)
        self.draw_bottom(screen, output, input_buffer, connection, character, player_positions)


    def handle_input(self, command, character, connection):
        try:
            # Attempt to cast the command to an integer
            command = int(command)
        except ValueError:
            # Handle the case where the input is not a valid integer
            print("Invalid input: Please enter a valid integer.")
            return "Invalid input: Please enter a valid integer."
        if character.stats.xp >= character.stats.level_cost:
            input_map = dict()
            for idx, (stat_name, stat_value) in enumerate(character.stats.levels.__dict__.items(), start=1):
                input_map[idx] = stat_name

            if not command in input_map:
                return "Invalid input: Please enter a valid integer."
            stat_name = input_map[command]
            stat_value = getattr(character.stats.levels, stat_name)
            setattr(character.stats.levels, stat_name, stat_value + 1)
            if "max_" in stat_name:
                stat_name = stat_name.replace("max_", "")
                stat_value = getattr(character.stats, stat_name)
                setattr(character.stats, stat_name, stat_value + 1)
            character.spend_xp(character.stats.level_cost)
            message = f"{stat_name} increased by 1."
            print(message)  # Print to console for debugging
            return message
        else:
            print("Not enough XP to increase the stat.")  # Print to console for debugging
            return "Not enough XP to increase the stat."

    def draw_top(self, screen, output, input_buffer, connection, character, player_positions):
            # screen.stdscr.clear()

        # Create a new window for the level-up menu
        if not self.level_up_win:
            height, width = screen.half_height, screen.width  # Height and width of the level-up menu
            start_y = 0  # Start at the top of the screen
            start_x = 0  # Start at the left of the screen
            self.level_up_win = curses.newwin(height, width, start_y, start_x)

        # Draw the level-up menu
        self.level_up_win.box()  # Draw a box around the window
        self.level_up_win.addstr(1, 1, "Select a stat to increase:")

        # List stats dynamically
        stats_list = vars(character.stats.levels)  # Get all attributes of the Stats class
        for idx, (stat_name, stat_value) in enumerate(stats_list.items(), start=1):
            stat_name = stat_name.replace('max_', '')
            stat_name = stat_name.capitalize()
            self.level_up_win.addstr(idx + 2, 1, f"{idx}. {stat_name} ({stat_value})")

        self.level_up_win.addstr(len(stats_list) + 4, 1, "b. Back")

        self.level_up_win.refresh()

    def draw_bottom(self, screen, output, input_buffer, connection, character, player_positions):

        (panel_height, panel_width) = screen.bottom_panel.getmaxyx()

        # Create the bottom panel (window)
        screen.bottom_panel.clear()
        screen.bottom_panel.box()
        screen.bottom_panel.addstr(0, 1, "Bottom Panel", curses.A_BOLD)
        # Display the output in the bottom panel
        if output is None:
            output = ""
        screen.bottom_panel.addstr(1, 1, output)  # Adjust the row as needed

        # Display the input buffer
        screen.bottom_panel.addstr(2, 1, "Input: " + input_buffer)  # Adjust the row as needed

        message_history_height = panel_height - 6
        last_messages = connection.message_history.get_last_messages(message_history_height)
        screen.bottom_panel.addstr(4, 1, "Last messages:")
        current_row = 5
        for msg in last_messages:
            # import pdb; pdb.set_trace()
            screen.bottom_panel.addstr(current_row, 1, msg)
            current_row += 1

        screen.bottom_panel.refresh()
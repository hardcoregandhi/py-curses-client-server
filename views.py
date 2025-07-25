from enum import Enum
import curses
import logging
from draw import draw, ScreenMeasurements, create_health_bar, draw_bottom, draw_top_left, draw_bottom_right
from fight import FightAction
import sys

class View(Enum):
    WORLD = "world"
    LEVEL_UP = "levelup"
    BATTLE = "battle"
    DEAD = "dead"

class BaseView:
    def draw(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def handle_input(self):
        raise NotImplementedError("Subclasses should implement this method.")

class WorldView(BaseView):
    def __init__(self):
        # Define available actions
        self.actions = {
            "w": ("Work on a tile", self.work_action),
            "a": ("Activate a tile", self.activate_action),
            # "r": ("Run a command", self.run_action),
            "l": ("Level up", self.level_up_action),
            "f": ("Fight", self.fight_action),
            "q": ("Quit the game", self.quit_action),
        }
    
    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        draw(screen, output, input_buffer, connection, character, player_positions)
        draw_bottom_right(screen, output, input_buffer, connection, character, player_positions, self.actions)

    def handle_input(self, command, character, connection):
        """Basic character actions."""
        output = ""

        if command in self.actions:
            action_description, action_function = self.actions[command]
            output = action_function(character, connection)
        else:
            output = f"Unknown command: {command}"
            # "Available actions:\n" + "\n".join(f"{key}: {desc[0]}" for key, desc in self.actions.items()

        return output

    def quit_action(self, character, connection):
        connection.send_action(character, "client_disconnecting")
        return "Quitting..."

    def work_action(self, character, connection):
        if character.stats.stamina:
            connection.send_action(character, "work")
            return "Working tile..."
        else:
            return "Not enough stamina to work."

    def activate_action(self, character, connection):
        if character.stats.stamina:
            connection.send_action(character, "activate")
            return "Activating tile..."
        else:
            return "Not enough stamina to activate."

    def run_action(self, character, connection):
        return "Running command..."  # Placeholder for future functionality

    def level_up_action(self, character, connection):
        connection.map.event_manager.publish("switch_view", new_view=View.LEVEL_UP)
        return "Switching View"

    def fight_action(self, character, connection):
        connection.send_action(character, "fight")
        return "Switching View"


class LevelUpView(BaseView):
    def __init__(self):
        self.level_up_win = None
        # Define available actions as an instance attribute
        self.actions = {
            "b": ("Back to world view", self.back_to_world_view),
            # You can add more actions here if needed
        }

    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        draw_top_left(screen, character)
        self.draw_top(screen, output, input_buffer, connection, character, player_positions)
        self.draw_bottom(screen, output, input_buffer, connection, character, player_positions)
        draw_bottom_right(screen, output, input_buffer, connection, character, player_positions, self.actions)

    def handle_input(self, command, character, connection):
        try:
            # Attempt to cast the command to an integer
            if command in self.actions:
                action_description, action_method = self.actions[command]
                return action_method(character, connection)  # Call the corresponding action method

            command = int(command)
        except ValueError:
            # Handle the case where the input is not a valid integer
            print("Invalid input: Please enter a valid integer.")
            return "Invalid input: Please enter a valid integer."

        if character.stats.xp >= character.stats.level_cost:
            input_map = dict()
            for idx, (stat_name, stat_value) in enumerate(character.stats.levels.__dict__.items(), start=1):
                input_map[idx] = stat_name

            if command not in input_map:
                return "Invalid input: Please enter a valid integer."
            stat_name = input_map[command]
            stat_value = getattr(character.stats.levels, stat_name)
            setattr(character.stats.levels, stat_name, stat_value + 1)
            if "max_" in stat_name:
                stat_name = stat_name.replace("max_", "")
                stat_value = getattr(character.stats, stat_name)
                setattr(character.stats, stat_name, stat_value + 1)
            character.spend_xp(character.stats.level_cost)
            character.stats.level_cost+=1
            character.stats.level+=1
            message = f"{stat_name} increased by 1."
            print(message)  # Print to console for debugging
            return message
        else:
            print("Not enough XP to increase the stat.")  # Print to console for debugging
            return "Not enough XP to increase the stat."

    def back_to_world_view(self, character, connection):
        connection.map.event_manager.publish("switch_view", new_view=View.WORLD)
        return "Switching View"

    def draw_top(self, screen, output, input_buffer, connection, character, player_positions):
            # screen.stdscr.clear()

        # Create a new window for the level-up menu
        if not self.level_up_win:
            height, width = screen.half_height, screen.width  # Height and width of the level-up menu
            start_y = 0  # Start at the top of the screen
            start_x = 0  # Start at the left of the screen
            self.level_up_win = screen.top_panel2 # HACK Im trying out using an existing panel instead

        self.level_up_win.clear()
        self.level_up_win.box()

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

class BattleView(BaseView):
    def __init__(self):
        self.battle_win = None
        self.actions = {
            "1": ("Stab", None),
            "2": ("Slash", None),
            "3": ("Parry", None),
        }

    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        # self.draw_battle_interface(screen, output, input_buffer, player_character, enemy_character)
        self.draw_battle_interface_in_map_area(screen.top_panel2, screen, output, input_buffer, character, character)
        draw_top_left(screen, character)
        draw_bottom(screen, output, input_buffer, connection)
        draw_bottom_right(screen, output, input_buffer, connection, character, player_positions, self.actions)

    def handle_input(self, command, character, connection):
        """Handle battle actions based on player input."""
        # Check if the input is a number
        if command.isdigit() or (command[0] == '-' and command[1:].isdigit()):
            # Convert to integer
            FightAction_value = int(command)
            # Check if the value corresponds to an enum member
            if FightAction_value in (FightAction.value for FightAction in FightAction):
                fight_action = FightAction(FightAction_value)
            else:
                return("Invalid FightAction! Please choose '1', '2', '3'.")
        else:
            # Attempt to convert the input to the corresponding enum member
            try:
                fight_action = FightAction[command.upper()]
            except KeyError:
                return("Invalid FightAction! Please choose '1', '2', '3'.")

        # Send the player's action to the server
        sent_value = int(fight_action.value)
        logging.info(character.name, sent_value)
        connection.send_fight_action(character, sent_value)
        return f"Sent {fight_action}"
    
    def draw_character(self, window, y, x):
        character_representation = \
"""\
         />_________________________________
[########[]________________________________/
         \>"""
        
        
        for i, line in enumerate(character_representation.splitlines()):
            window.addstr(y + i, x + 1, line)
    
    def draw_battle_interface_in_map_area(self, window, screen, output, input_buffer, player_character, enemy_character):
        """Draw the battle interface in the area where the map is displayed."""
        window.clear()
        window.box()

        (panel_height, panel_width) = screen.top_panel1.getmaxyx()

        self.draw_character(window, 1, 1)
        # Draw enemy character on the right
        window.addstr(panel_height-8, 1, f"Enemy: {enemy_character.name} (HP: {enemy_character.stats.health})")
        window.addstr(panel_height-7, 1, f"{'Health':<{11}}: " + create_health_bar(enemy_character.stats.health, enemy_character.stats.levels.max_health))
        window.addstr(panel_height-5, 1, "Choose your action:")
        window.addstr(panel_height-4, 1, "1. Stab")
        window.addstr(panel_height-3, 1, "2. Slash")
        window.addstr(panel_height-2, 1, "3. Parry")


        window.refresh()



    def draw_battle_interface(self, screen, output, input_buffer, player_character, enemy_character):
        """Draw the battle interface showing both characters."""
        if not self.battle_win:
            height, width = screen.half_height, screen.width  # Adjust as needed
            start_y = 0
            start_x = 0
            self.battle_win = curses.newwin(height, width, start_y, start_x)

        self.battle_win.clear()
        self.battle_win.box()

        # Draw player character on the left
        # self.battle_win.addstr(1, 1, f"{'Health':<{11}}: " + create_health_bar(player_character.stats.health, player_character.stats.levels.max_health))
        # self.battle_win.addstr(1, 1, f"Player: {player_character.name} (HP: {player_character.health})")


        # Draw enemy character on the right
        self.battle_win.addstr(2, 1, f"{'Health':<{11}}: " + create_health_bar(enemy_character.stats.health, enemy_character.stats.levels.max_health))

        self.battle_win.addstr(1, width - 30, f"Enemy: {enemy_character.name} (HP: {enemy_character.health})")

        self.battle_win.addstr(3, 1, "Choose your action:")
        self.battle_win.addstr(4, 1, "1. Slash")
        self.battle_win.addstr(5, 1, "2. Stab")
        self.battle_win.addstr(6, 1, "3. Parry")

        self.battle_win.refresh()



class DeadView(BaseView):
    def __init__(self):
        self.level_up_win = None
        # Define available actions as an instance attribute
        self.actions = {
            "q": ("Quit game", self.back_to_world_view),
            # You can add more actions here if needed
        }

    def draw(self, screen, output, input_buffer, connection, character, player_positions):
        draw_top_left(screen, character)
        self.draw_top(screen, output, input_buffer, connection, character, player_positions)
        self.draw_bottom(screen, output, input_buffer, connection, character, player_positions)
        draw_bottom_right(screen, output, input_buffer, connection, character, player_positions, self.actions)

    def handle_input(self, command, character, connection):
        try:
            # Attempt to cast the command to an integer
            if command in self.actions:
                action_description, action_method = self.actions[command]
                return action_method(character, connection)  # Call the corresponding action method

            command = int(command)
        except ValueError:
            # Handle the case where the input is not a valid integer
            print("Invalid input: Please enter a valid integer.")
            return "Invalid input: Please enter a valid integer."

    def quit_action(self, character, connection):
        connection.send_action(character, "client_disconnecting")
        return "Quitting..."

    def back_to_world_view(self, character, connection):
        connection.map.event_manager.publish("switch_view", new_view=View.WORLD)
        return "Switching View"

    def draw_top(self, screen, output, input_buffer, connection, character, player_positions):

        screen.top_panel1.clear()
        screen.top_panel1.box()
        screen.bottom_panel.addstr(0, 1, "You died. Please restart the game")
        screen.bottom_panel.addstr(0, 2, "I couldn't be bothered to code restarting the game")
        screen.top_panel1.refresh()

    def draw_bottom(self, screen, output, input_buffer, connection, character, player_positions):

        (panel_height, panel_width) = screen.bottom_panel.getmaxyx()

        # Create the bottom panel (window)
        screen.bottom_panel.clear()
        screen.bottom_panel.box()
        screen.bottom_panel.refresh()




# Initialize views
Views = {
    View.WORLD: WorldView(),
    View.LEVEL_UP: LevelUpView(),
    View.BATTLE: BattleView(),
    View.DEAD: DeadView(),
}
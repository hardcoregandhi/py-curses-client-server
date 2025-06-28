import logging
from enum import Enum
from position import Position2D
import threading

# i am envisioning a rock paper scissors like battle system, but we will call it slash stab parry, 
# stab beats slash, parry beats stab, slash beats parry

class FightAction(Enum):
    NONE = -1
    STAB = 1  # rock
    SLASH = 2 # paper
    PARRY = 3 # scissors

class FightResolution(Enum):
    RIGHTWINS = 1
    LEFTWINS = 2
    DRAW = 3

class FightManager:
    def __init__(self, initiating_player_id, position, players, world):
        self.aggressor = initiating_player_id
        self.defender = None
        self.position = position
        self.world = world
        self.fight_radius = 3
        self.aggressor_action = FightAction.NONE
        self.defender_action = FightAction.NONE
        nearest_opponent = self.find_other_near_player(self.aggressor, self.position, players, world.game_map)
        if (nearest_opponent):
            self.defender = nearest_opponent
            self.start_next_round()
        else:
            logging.warning("failed to find close player")

    def find_other_near_player(self, aggressor, position, players, map):
        nearest_opponent, nearest_opponent_position = map.find_closest_player_to_player(aggressor, self.position, players)
        if not nearest_opponent or not nearest_opponent_position:
            logging.warning("no closest player")
            return None
        if map.calculate_distance(Position2D.from_list(position), nearest_opponent_position) < self.fight_radius:
            return nearest_opponent
        else:
            logging.warning("closest player too far away")
            return None
        
    def action_round(self):
        resolution = self.resolve_action(self.aggressor_action, self.defender_action)
        if (FightResolution.RIGHTWINS):
            self.world.event_manager.publish('damage_received', self.aggressor, self.position, True)
        if (FightResolution.LEFTWINS):
            self.world.event_manager.publish('damage_received', self.defender, self.position, True)
        self.start_next_round()
        return resolution

    def resolve_action(self, action_left, action_right):
        # Handle the NONE FightAction
        if action_left == FightAction.NONE and action_right == FightAction.NONE:
            return FightResolution.DRAW
        elif action_left == FightAction.NONE:
            return FightResolution.RIGHTWINS
        elif action_right == FightAction.NONE:
            return FightResolution.LEFTWINS
        

        if (action_left == action_right):
            return FightResolution.DRAW
        # % 3 causes the wrap around to 0 so rock beats scissors
        elif (action_left.value + 1) % 3 == action_right.value:
            return FightResolution.RIGHTWINS
        else:
            return FightResolution.LEFTWINS

        
    def start_next_round(self):
        self.aggressor_action = self.defender_action = FightAction.NONE
        threading.Timer(10, self.action_round).start()
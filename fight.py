import logging

from position import Position2D

class FightManager:
    def __init__(self, initiating_player_id, position, players, world):
        self.aggressor = initiating_player_id
        self.defender = None
        self.position = position
        self.fight_radius = 3
        nearest_opponent = self.find_other_near_player(self.aggressor, self.position, players, world.game_map)
        if (nearest_opponent):
            self.defender = nearest_opponent

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
from collections import namedtuple
from position import Position2D
import threading
import logging

from views import View

class LevelableStats:
    def __init__(self):
        self.max_health = 5
        self.max_stamina = 5
        self.max_mana = 5
        self.strength = 5
        self.defence = 5
        self.speed = 5

class Stats:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.level_cost = 1

        self.levels = LevelableStats()

        self.health = self.levels.max_health
        self.stamina = self.levels.max_stamina
        self.mana = self.levels.max_mana

class Character:
    def __init__(self, connection, name = "Unnamed"):
        # Get the height and width of the window and round to even
        self.name = name
        self.stats = Stats()
        self.position = Position2D(8,8)
        self.connection = connection 
        self.register_subscriptions(connection.map.event_manager)

    
    def add_xp(self, amount):
        self.stats.xp += int(amount)

    def spend_xp(self, cost):
        if self.stats.xp >= cost:
            self.stats.xp -= cost
            return True
        return False

    def register_subscriptions(self, event_manager):
        event_manager.subscribe('tile_working', self.character_working_tile)
        event_manager.subscribe('tile_worked', self.character_worked_tile)
        event_manager.subscribe('tile_activated', self.character_activated_tile)
        event_manager.subscribe('damage_received', self.damage_received)
        event_manager.subscribe('xp_received', self.character_add_xp)

    def character_working_tile(self, *args, **kwargs):
        if kwargs.get('player_id') == self.connection.player_id:
            # self.add_xp(1)
            self.stats.stamina -= 1
            threading.Timer(5, self.restore_stamina).start()
        return
    
    def character_worked_tile(self, *args, **kwargs):
        return
    
    def character_activated_tile(self, *args, **kwargs):
        if kwargs.get('player_id') == self.connection.player_id:
            # self.add_xp(1)
            self.stats.stamina -= 1
            threading.Timer(5, self.restore_stamina).start()
        return
    
    def character_add_xp(self, *args, **kwargs):
        if kwargs.get('player_id') == self.connection.player_id:
            self.add_xp(kwargs.get('amount'))
        return
    
    def restore_stamina(self):
        self.stats.stamina += 1

    def damage_received(self, *args, **kwargs):
        self.stats.health -= 1
        if(self.stats.health <= 0):
            logging.info(f"Player {self.name} died")
            self.connection.map.event_manager.publish('player_died', player_id=self.connection.player_id)
            self.connection.send_action(self, "player_died")
            self.connection.map.event_manager.publish('switch_view', new_view=View.DIED)


    
    def __iter__(self):
        yield {
            "name" : self.name, 
            "level" : self.level, 
            "xp" : self.xp, 
            "health" : self.health, 
            "stamina" : self.stamina, 
            "mana" : self.mana, 
            "strength" : self.strength, 
            "defence" : self.defence, 
            "speed" : self.speed, 
            "position" : self.position
        }

    def moveTo(self, new_x, new_y, game_map):
        """Move the character to a new position if valid."""
        tile = game_map.get_tile(new_x, new_y)
        if tile and tile.tile_type != 'unknown' and game_map.is_walkable(new_x, new_y):  # Check if the tile is valid
            self.position = Position2D(new_x, new_y)  # Update position if valid
            return True
        return False  # Move was not valid
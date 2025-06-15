import unittest
from unittest.mock import patch, MagicMock
import time
from map import GameMap, Tile, default_map_string  # Replace 'your_module' with the actual module name where Tile is defined
import json
from event_manager import EventManager
from position import Position2D

class TestTile(unittest.TestCase):

    @patch('threading.Timer')
    @patch('event_manager.EventManager.publish')
    def test_work_activation(self, mock_timer, mock_publish):
        evman = EventManager()
        tile = Tile(evman, 'farm', Position2D(1,1))
        tile.id = 1  # Set an ID for testing

        # Simulate working the tile
        tile.work()
        self.assertFalse(tile.is_ready_to_work)
        self.assertFalse(tile.is_finished_work)

        # Simulate the timer completing
        tile.work_complete()
        self.assertTrue(tile.is_finished_work)
        self.assertFalse(tile.is_ready_to_work)

    @patch('threading.Timer')
    @patch('event_manager.EventManager.publish')
    def test_cooldown(self, mock_timer, mock_publish):
        evman = EventManager()
        tile = Tile(evman, 'farm', Position2D(1,1))
        tile.id = 1  # Set an ID for testing

        # Simulate working the tile
        tile.work()
        tile.work_complete()  # Complete activation to allow cooldown

        # Simulate cooldown
        tile.cooldown()
        self.assertFalse(tile.is_finished_work)

        # Simulate the timer completing
        tile.cooldown_complete()
        self.assertTrue(tile.is_ready_to_work)

    @patch('threading.Timer')
    def test_notify_players(self, mock_timer):
        evman = EventManager()
        tile = Tile(evman, 'farm', Position2D(1,1))
        tile.id = 1  # Set an ID for testing

        # Mock the notify_players method
        tile.notify_players = MagicMock()

        evman.publish = MagicMock()

        # Simulate working the tile
        tile.work()
        tile.work_complete()
        tile.cooldown()
        tile.cooldown_complete()

        # Check if notify_players was called
        self.assertTrue(evman.publish.called)

class TestMap(unittest.TestCase):
    def test_map_json(self):
        evman = EventManager
        game_map = GameMap(evman, 50, 10, default_map_string)  # Example map size
        self.assertTrue(json.dumps(game_map.to_dict()).encode('utf-8'))

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import time
from client import Connection
from map import GameMap, Tile, default_map_string, GameMapEncoderDecoder, test_map_string
import json
from event_manager import EventManager
from position import Position2D
import itertools 

class TestTile(unittest.TestCase):
    
    @patch('threading.Timer')
    @patch('event_manager.EventManager.publish')
    def test_work_activation(self, mock_timer, mock_publish):
        evman = EventManager()
        tile = Tile(evman, 'farm', Position2D(1,1))
        tile.id = 1  # Set an ID for testing
        player_id = 1

        # Simulate working the tile
        tile.work(player_id)
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
        player_id = 1

        # Simulate working the tile
        tile.work(player_id)
        tile.work_complete()  # Complete activation to allow cooldown

        # Simulate cooldown
        tile.cooldown(player_id)
        self.assertFalse(tile.is_finished_work)

        # Simulate the timer completing
        tile.cooldown_complete()
        self.assertTrue(tile.is_ready_to_work)

    @patch('threading.Timer')
    def test_notify_players(self, mock_timer):
        evman = EventManager()
        tile = Tile(evman, 'farm', Position2D(1,1))
        tile.id = 1  # Set an ID for testing
        player_id = 1

        # Mock the notify_players method
        tile.notify_players = MagicMock()

        evman.publish = MagicMock()

        # Simulate working the tile
        tile.work(player_id)
        tile.work_complete()
        tile.cooldown(player_id)
        tile.cooldown_complete()

        # Check if notify_players was called
        self.assertTrue(evman.publish.called)

class TestMap(unittest.TestCase):
    def test_map_json(self):
        evman = EventManager
        game_map = GameMap(evman, 50, 10, default_map_string)  # Example map size
        self.assertTrue(json.dumps(game_map.to_dict()).encode('utf-8'))

    def assertEqual(self, first, second, msg=None):
        try:
            super().assertEqual(first, second, msg)
        except AssertionError:
            # import pdb; pdb.set_trace()
            raise  # Re-raise the exception after debugging
    def test_map_json(self):
        evman = EventManager
        game_map = GameMap(evman, 50, 10, default_map_string)
        data_packet = {
                'request': 'map',
                'map': game_map
            }
        data = json.dumps(data_packet, cls=GameMapEncoderDecoder).encode('utf-8')
        new_map = GameMapEncoderDecoder.from_dict(json.loads(data.decode())['map'])

        with open('downloaded_map1.json', 'w') as f:
                f.write(f"map_data {data}")

        with open('downloaded_map2.json', 'w') as f:
                f.write(f"map_data {json.loads(data.decode())}")


        # import pdb; pdb.set_trace()
        for (tiles1, tiles2) in zip(game_map.map, new_map.map):
            for (tile1, tile2) in zip(tiles1, tiles2):
                tile1.id = 0
                tile2.id = 0
                self.assertEqual(str(tile1), str(tile2))

    def assertTrue(self, first, msg=None):
        try:
            super().assertTrue(first, msg)
        except AssertionError:
            # import pdb; pdb.set_trace()
            raise  # Re-raise the exception after debugging
    # def test_map_download(self):
    #     connection = Connection()
    #     self.assertTrue(connection.map.get_tile(3,5).is_finished_work)

class TestPosition2D(unittest.TestCase):
    def test_position_creation(self):
        pos = Position2D(3, 4)
        self.assertEqual(pos.x, 3)
        self.assertEqual(pos.y, 4)

    def test_position_str(self):
        pos = Position2D(3, 4)
        self.assertEqual(str(pos), "3, 4")

    def test_position_to_dict(self):
        pos = Position2D(3, 4)
        self.assertEqual(pos.to_dict(), {'x': 3, 'y': 4})

    def test_from_list_valid(self):
        pos = Position2D.from_list([5, 6])
        self.assertEqual(pos.x, 5)
        self.assertEqual(pos.y, 6)

    def test_from_list_invalid_length(self):
        with self.assertRaises(ValueError):
            Position2D.from_list([5])  # Only one element
        with self.assertRaises(ValueError):
            Position2D.from_list([5, 6, 7])  # More than two elements

class TestGameMap(unittest.TestCase):
    def setUp(self):
        # Create a mock event manager and a simple map string
        self.event_manager = None  # Replace with actual event manager if needed
        self.map_string = "xxxxxxxxxx"  # Simple map for testing
        self.game_map = GameMap(self.event_manager, 10, 10, test_map_string)

        # Create mock players
        self.players = {}
        self.players[1] = {"position": Position2D(1, 2)}
        self.players[2] = {"position": Position2D(3, 4)}
        self.players[3] = {"position": Position2D(5, 6)}

    def test_find_closest_player(self):
        closest_player_id, closest_player_pos = self.game_map.find_closest_player_to_player(0, [0,0], self.players)
        self.assertEqual(closest_player_id, 1)
        closest_player_id, closest_player_pos = self.game_map.find_closest_player_to_player(0, [9,9], self.players)
        self.assertEqual(closest_player_id, 3)

    def test_find_closest_player_no_players(self):
        closest_player_id, closest_player_pos = self.game_map.find_closest_player_to_player(1, [0,0], [])
        self.assertIsNone(closest_player_id)  # No players should return None


if __name__ == '__main__':
    unittest.main()

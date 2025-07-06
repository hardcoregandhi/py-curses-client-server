import unittest
from unittest.mock import patch, MagicMock
import time
import threading
from map import GameMap, Tile, default_map_string
import json
import client
from server import GameServer
from unittest.mock import patch, MagicMock
from position import Position2D
from fight import FightManager

class TestFight(unittest.TestCase):

    def test_fight(self):
        # Will hang forever due to start() loop
        server = GameServer()
        # server.handle_client = MagicMock()
        server_thread = threading.Thread(target=server.start, args=(), daemon=True)
        server_thread.start()
        connection = client.Connection()
        self.assertIsNotNone(connection.map)

        player_id=1
        
        players = {}
        players[2] = {"position": Position2D(1, 2)}

        new_fight = FightManager(player_id, [0,0], players, server.world)
        self.assertIsNotNone(new_fight.defender)
        self.assertIs(new_fight.defender, 2)

        players[2] = {"position": Position2D(10, 10)}
        new_fight = FightManager(player_id, [0,0], players, server.world)
        self.assertIsNone(new_fight.defender)

        players[2] = {"position": Position2D(14, 8)}
        new_fight = FightManager(player_id, [3,8], players, server.world)
        self.assertIsNone(new_fight.defender)

        players[2] = {"position": Position2D(3, 8)}
        new_fight = FightManager(player_id, [14,8], players, server.world)
        self.assertIsNone(new_fight.defender)


if __name__ == '__main__':
    unittest.main()

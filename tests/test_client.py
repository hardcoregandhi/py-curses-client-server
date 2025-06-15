import unittest
from unittest.mock import patch, MagicMock
import time
from map import GameMap, Tile, default_map_string
import json
import client
from server import GameServer

class TestClient(unittest.TestCase):

    def test_connection(self):
        # Will hang forever due to start() loop
        server = GameServer()
        server.start()
        connection = client.Connection()
        self.assertIsNotNone(connection.map)


if __name__ == '__main__':
    unittest.main()

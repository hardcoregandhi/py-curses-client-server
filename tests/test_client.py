import unittest
from unittest.mock import patch, MagicMock
import time
from map import GameMap, Tile, default_map_string
import json
import client

class TestClient(unittest.TestCase):

    def test_connection(self):
        connection = client.Connection()
        self.assertIsNotNone(connection.map)


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import time
import threading
from map import GameMap, Tile, default_map_string
import json
import client
from server import GameServer
from unittest.mock import patch, MagicMock

class TestClient(unittest.TestCase):

    def test_connection(self):
        # Will hang forever due to start() loop
        server = GameServer()
        # server.handle_client = MagicMock()
        server_thread = threading.Thread(target=server.start, args=(), daemon=True)
        server_thread.start()
        connection = client.Connection()
        self.assertIsNotNone(connection.map)
        return True


if __name__ == '__main__':
    unittest.main()

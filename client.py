
import json
import socket
import threading
import traceback
from position import Position2D
from map import GameMapEncoderDecoder
import gzip 
from struct import unpack
import os 
import logging
from event_manager import EventManager

# Global variable to hold player positions
player_positions = {}
positions_lock = threading.Lock()  # Lock for thread-safe access to player_positions

map = {}
map_lock = threading.Lock()  # Lock for thread-safe access to player_positions

class MessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, message: str):
        """Add a new message to the history."""
        self.messages.append(message)

    def get_last_messages(self, count: int) -> list:
        """Retrieve the last X messages from the history."""
        if count <= 0:
            return []
        return self.messages[-count:]

    def __str__(self):
        """Return a string representation of the message history."""
        return "\n".join(self.messages)

class Connection:
    def __init__(self, host='127.0.0.1', port=43210, username='Player1'):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = self.create_connection(host, port, username)
        self.map = self.download_map()
        self.message_history = MessageHistory()
        # Start a thread to receive messages from the server
        threading.Thread(target=self.receive_messages, args=(), daemon=True).start()

    def download_map(self):
        data_packet = {
            'request': 'map',
        }
        self.client_socket.sendall(json.dumps(data_packet).encode('utf-8'))
        while True:
            bs = self.client_socket.recv(8)
            logging.info(f"Raw bytes received for length: {bs}")
            (length,) = unpack('>Q', bs)  # Unpack the length
            logging.info(f"Unpacked length: {length}")  # Print the unpacked length
            data = b''
            while len(data) < length:
                # doing it in batches is generally better than trying
                # to do it all in one go, so I believe.
                to_read = length - len(data)
                data += self.client_socket.recv(
                    4096 if to_read > 4096 else to_read)

            # send our 0 ack
            assert len(b'\00') == 1
            self.client_socket.sendall(b'\00')

            map_data = gzip.decompress(data)
            # logging.info(f"map_data {map_data}")
            # Step 2: Write the output to a file
            with open('downloaded_map.json', 'w') as f:
                f.write(f"map_data {map_data}")
            return GameMapEncoderDecoder.from_dict(json.loads(map_data.decode())['map'])


    def create_connection(self, host='127.0.0.1', port=43210, username='Player1'):
        """Create a socket connection to the game server."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        initial_state = {
            'player_id': username,
            'position': Position2D(0,0)
        }
        client_socket.sendall(json.dumps(initial_state).encode('utf-8'))
        
        return client_socket


    def send_update(self, character, action):
        initial_state = {
            'player_id': self.username,
            'position': character.position,
            'action': action
        }
        logging.info(initial_state)
        return self.client_socket.sendall(json.dumps(initial_state).encode('utf-8'))

    def send_tile_update(self, character):
        self.send_update(character, "farm")

    def send_position_update(self, character):
        self.send_update(character, "move")

    def receive_messages(self):
        """Thread to receive messages from the server and update player positions."""
        global player_positions
        logging.info("starting receive messages thread")
        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break  # Connection closed
                logging.info(data)
                # Process the received data
                messages = data.splitlines()  # Assuming each message is on a new line
                for message in messages:
                    if message:
                        try:
                            command = json.loads(message)
                            logging.info(command)
                            self.message_history.add_message(str(command))
                            if command.get('new_position'):
                                player_id = command['player_id']
                                position = command['new_position']
                                # Update the player position in a thread-safe manner
                                with positions_lock:
                                    player_positions[player_id] = position
                            elif command.get('origin') and command.get('origin') == "tile":
                                logging.info("tile action received")
                                action = command['action']
                                pos_array = command['tile_pos']
                                is_success = command['is_success']
                                if not is_success:
                                    continue
                                tile_pos = Position2D(pos_array[0], pos_array[1])
                                with map_lock:
                                    if command.get("player_id"):
                                        player_id = command['player_id']
                                    if action == "working":
                                        self.map.get_tile(tile_pos.x, tile_pos.y).work(player_id)
                                    if action == "worked":
                                        self.map.get_tile(tile_pos.x, tile_pos.y).work_complete()
                                    if action == "activated":
                                        self.map.get_tile(tile_pos.x, tile_pos.y).cooldown(player_id)
                                    if action == "ready":
                                        self.map.get_tile(tile_pos.x, tile_pos.y).cooldown_complete()
                        except json.JSONDecodeError:
                            logging.error("Received invalid JSON:", message)
            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                logging.error(repr(traceback.print_exc(e)))

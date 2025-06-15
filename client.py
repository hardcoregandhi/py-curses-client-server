
import json
import socket
import threading

from position import Position2D
from map import GameMapEncoderDecoder
import gzip 
from struct import unpack
import os 
# Global variable to hold player positions
player_positions = {}
positions_lock = threading.Lock()  # Lock for thread-safe access to player_positions

map = {}
map_lock = threading.Lock()  # Lock for thread-safe access to player_positions

class Connection:
    def __init__(self):
        self.username, self.client_socket = self.create_connection()
        self.map = self.download_map()

        # Start a thread to receive messages from the server
        threading.Thread(target=self.receive_messages, args=(self.client_socket,), daemon=True).start()

    def download_map(self):
        data_packet = {
            'request': 'map',
        }
        self.client_socket.sendall(json.dumps(data_packet).encode('utf-8'))
        while True:
            bs = self.client_socket.recv(8)
            print(f"Raw bytes received for length: {bs}")
            (length,) = unpack('>Q', bs)  # Unpack the length
            print(f"Unpacked length: {length}")  # Print the unpacked length
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
            # print(f"map_data {map_data}")
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
        
        return username, client_socket


    def send_update(self, character, action):
        initial_state = {
            'player_id': self.username,
            'position': character.position,
            'action': action
        }
        print(initial_state)
        return self.client_socket.sendall(json.dumps(initial_state).encode('utf-8'))

    def send_tile_update(self, character):
        self.send_update(character, "farm")

    def send_position_update(self, character):
        self.send_update(character, "move")

    def receive_messages(self):
        """Thread to receive messages from the server and update player positions."""
        global player_positions
        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break  # Connection closed
                # Process the received data
                messages = data.splitlines()  # Assuming each message is on a new line
                for message in messages:
                    if message:
                        try:
                            command = json.loads(message)
                            print(command)
                            if command.get('new_position'):
                                player_id = command['player_id']
                                position = command['new_position']
                                # Update the player position in a thread-safe manner
                                with positions_lock:
                                    player_positions[player_id] = position
                            elif command.get('origin') and command.get('origin') == "tile":
                                print("tile action received")
                                action = command['action']
                                tile_pos = Position2D(command['tile_pos'])
                                with map_lock:
                                    if action == "working":
                                        self.map.get_tile(tile_pos).work()
                                    if action == "worked":
                                        self.map.get_tile(tile_pos).work_complete()
                                    if action == "activated":
                                        self.map.get_tile(tile_pos).cooldown()
                                    if action == "ready":
                                        self.map.get_tile(tile_pos).cooldown_complete()
                        except json.JSONDecodeError:
                            print("Received invalid JSON:", message)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

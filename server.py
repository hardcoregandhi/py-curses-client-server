import map
from position import Position2D
import miniupnpc 
import gzip
import logging
import sys

# Configure the logger
logging.basicConfig(
    filename='server.log',  # Specify the log file name
    filemode='w',        # Append mode; use 'w' to overwrite the file
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s',
    level=logging.DEBUG   # Set the logging level
)


class GameWorld:
    def __init__(self, event_manager):
        self.players = []
        self.event_manager = event_manager
        self.game_map = map.GameMap(event_manager, 50, 10, map.default_map_string)  # Example map size


def add_upnp_port_mapping():
    upnp = miniupnpc.UPnP()

    upnp.discoverdelay = 10
    upnp.discover()

    upnp.selectigd()

    port = 43210

    # addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
    upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'testing', '')

    return f"UPnP initialized. Mapped port {port}."

import socket
import threading
import json
from collections import namedtuple
from map import GameMapEncoderDecoder
import struct
from struct import pack
from event_manager import EventManager

position_packet = {
    'player_id': "",
    'position': ""
}

class GameServer:
    def __init__(self, host='0.0.0.0', port=43210):
        self.host = host
        self.port = port
        self.event_manager = EventManager()
        self.world = GameWorld(self.event_manager)
        self.players = {}  # Dictionary to hold player data
        self.register_subscriptions()

    def start(self):
        """Start the server and listen for incoming connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            logging.info(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, addr = server_socket.accept()
                logging.info(f"Player connected from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    
    def send_data_in_chunks(self, sock, json_data, chunk_size=1024):
        logging.info(json_data)
        total_length = len(json_data)
        
        # Send the total length first
        sock.sendall(struct.pack('!I', total_length))
        
        # Send data in chunks
        for i in range(0, total_length, chunk_size):
            chunk = json_data[i:i + chunk_size]
            sock.sendall(chunk)

    def handle_client(self, client_socket):
        """Handle communication with a connected client."""
        player_id = len(self.players) + 1  # Simple player ID assignment
        self.players[player_id] = {
            'position': Position2D(0, 0),  # Start at position (0, 0)
            'socket': client_socket
        }
        # Send initial game state to the player
        # initial_state = {
        #     'player_id': player_id,
        #     'position': self.players[player_id]['position']
        # }
        # client_socket.sendall(json.dumps(initial_state).encode('utf-8'))
        buffer = ""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break  # Client disconnected

                buffer += data
        
                # Attempt to decode the JSON
                try:
                    # If the buffer contains multiple JSON objects, split them
                    while True:
                        # Find the end of the JSON object
                        end_index = buffer.find('}')  # Assuming JSON objects end with '}'
                        if end_index == -1:
                            break  # No complete JSON object found yet
                        
                        # Extract the complete JSON object
                        json_str = buffer[:end_index + 1]
                        buffer = buffer[end_index + 1:]  # Remove the processed JSON from the buffer
                        
                        # Decode the JSON
                        # json_data = json.loads(json_str)
                        # logging.info("Received JSON:", json_data)  # Process the JSON data as needed
                        command = json.loads(json_str)
                        self.process_command(player_id, command)

                except json.JSONDecodeError:
                    # If decoding fails, continue to receive more data
                    continue



        finally:
            client_socket.close()
            del self.players[player_id]  # Remove player from the list
            logging.info(f"Player {player_id} disconnected.")

    def send_map(self, sock, map_data):
        logging.info("sending map")
        # use struct to make sure we have a consistent endianness on the length
        logging.info(f"Length of map_data: {len(map_data)}")
        length = pack('>Q', len(map_data))

        # sendall to make sure it blocks if there's back-pressure on the socket
        logging.info(f"Packed length (bytes): {length}")  # Should show 8 bytes
        sock.sendall(length)
        sock.sendall(map_data)

        ack = sock.recv(1)

    def process_command(self, player_id, command):
        """Process movement commands from the player."""
        logging.info(command)
        if command.get("request") and command['request'] == 'map':
            data_packet = {
                'request': 'map',
                'map': self.world.game_map
            }
            data = json.dumps(data_packet, cls=GameMapEncoderDecoder).encode('utf-8')

            with open('server_map.json', 'w') as f:
                f.write(f"map_data {data}")

            compressed_data = gzip.compress(data)
            # data = json.dumps(data_packet).encode('utf-8')

            self.send_map(self.players[player_id]['socket'], compressed_data)

        if command.get('action') and command['action'] == 'move':
            position = command['position']
            self.move_player(player_id, position)
        if command.get('action') and command['action'] == 'work':
            position = command['position']
            self.work_tile(player_id, position)
        if command.get('action') and command['action'] == 'activate':
            position = command['position']
            self.activate_tile(player_id, position)

    def work_tile(self, player_id, position):
        tile = self.world.game_map.get_tile(position[0], position[1])
        tile.work()

    def activate_tile(self, player_id, position):
        tile = self.world.game_map.get_tile(position[0], position[1])
        tile.cooldown()

    def move_player(self, player_id, position):
        """Move the player based on the direction provided."""
        current_position = self.players[player_id]

        new_position = position

        # Update the player's position
        self.players[player_id]['position'] = new_position

        # Notify all players of the new position (optional)
        self.notify_players(player_id, new_position)

    def broadcast(self, data_packet):
        for pid, player in self.players.items():
            logging.info(f"Broadcasting {data_packet}")
            player['socket'].sendall(json.dumps(data_packet).encode('utf-8'))

    def notify_players(self, player_id, new_position):
        """Notify all players of the updated position."""
        message = {
            'player_id': player_id,
            'new_position': new_position
        }
        for pid, player in self.players.items():
            if pid != player_id:  # Don't send to the player who moved
                player['socket'].sendall(json.dumps(message).encode('utf-8'))

    def register_subscriptions(self):
        self.event_manager.subscribe('tile_working', self.notify_tile_working)
        self.event_manager.subscribe('tile_worked', self.notify_tile_worked)
        self.event_manager.subscribe('tile_activated', self.notify_tile_activated)
        self.event_manager.subscribe('tile_ready', self.notify_tile_ready)

    def notify_tile_working(self, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'working',
            'tile_pos': tile_position,
            'is_success': is_success
        }
        self.broadcast(data_packet)

    def notify_tile_worked(self, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'worked',
            'tile_pos': tile_position,
            'is_success': is_success

        }
        self.broadcast(data_packet)

    def notify_tile_activated(self, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'activated',
            'tile_pos': tile_position,
            'is_success': is_success
        }
        self.broadcast(data_packet)

    def notify_tile_ready(self, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'ready',
            'tile_pos': tile_position,
            'is_success': is_success
        }
        self.broadcast(data_packet)

if __name__ == "__main__":
    server = GameServer()
    server.start()

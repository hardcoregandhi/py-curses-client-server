import map
from position import Position2D
import miniupnpc 
import gzip
import logging
import sys
from fight import FightAction, FightManager


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
        self.game_map = map.GameMap(event_manager, 50, 11, map.default_map_string)  # Example map size


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

class GameServer:
    def __init__(self, host='0.0.0.0', port=43210):
        self.host = host
        self.port = port
        self.event_manager = EventManager()
        self.world = GameWorld(self.event_manager)
        self.players = {}  # Dictionary to hold player data
        self.client_threads = {}
        self.fights = []
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
                self.client_threads[f"{addr}"] = threading.Thread(target=self.handle_client, args=(client_socket,))
                self.client_threads[f"{addr}"].start()

    
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
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                except Exception as ex:
                    logging.error(f"Lost connection {client_socket}")
                    logging.error(ex)
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
        if command.get("request") and command['request'] == 'id':
            data_packet = {
                'request': 'id',
                'id': player_id
            }
            self.players[player_id]['socket'].sendall(json.dumps(data_packet).encode('utf-8'))
        if command.get("request") and command['request'] == 'map':
            data_packet = {
                'request': 'map',
                'map': self.world.game_map
            }
            data = json.dumps(data_packet, cls=GameMapEncoderDecoder).encode('utf-8')

            compressed_data = gzip.compress(data)
            # data = json.dumps(data_packet).encode('utf-8')

            self.send_map(self.players[player_id]['socket'], compressed_data)

        if command.get('action') and command['action'] == 'move':
            position = command['position']
            self.move_player(player_id, position)
        elif command.get('action') and command['action'] == 'work':
            position = command['position']
            player_name = command['player_id']
            self.work_tile(player_name, position)
        elif command.get('action') and command['action'] == 'activate':
            position = command['position']
            player_name = command['player_id']
            self.activate_tile(player_name, position)
        elif command.get('action') and command['action'] == 'fight':
            position = command['position']
            player_name = command['player_id']
            self.fight_requested(position, player_id)
        elif command.get('action') and command['action'] == 'player_died':
            position = command['position']
            player_name = command['player_id']
            self.event_manager.publish("player_died", command['player_id'], command['position'], True)
        elif command.get('action') and command['action'] == 'fight_action':
            position = command['position']
            player_id = command['player_id']
            # Set fight action in fight
            for fight in self.fights:
                if fight.aggressor == player_id:
                    fight.aggressor_action = FightAction(command['fight_action'])
                if fight.defender == player_id:
                    fight.defender_action = FightAction(command['fight_action'])

    def work_tile(self, player_id, position):
        tile = self.world.game_map.get_tile(position[0], position[1])
        tile.work(player_id)

    def activate_tile(self, player_id, position):
        tile = self.world.game_map.get_tile(position[0], position[1])
        tile.cooldown(player_id)

    def fight_requested(self, position, player_id):
        message = {
            'player_id': player_id,
            'message': "fight requested"
        }
        self.broadcast(message)
        new_fight = FightManager(player_id, position, self.players, self.world)
        if new_fight.defender == None:
            self.message_player(player_id, "No defender found")
        else:
            self.message_player(new_fight.defender, "fight_initiated")
            self.message_player(new_fight.aggressor, "fight_initiated")
            self.fights.append(new_fight)
            

    def move_player(self, player_id, position):
        """Move the player based on the direction provided."""
        current_position = self.players[player_id]

        new_position = position

        # Update the player's position
        self.players[player_id]['position'] = new_position

        # Notify all players of the new position (optional)
        self.notify_players(player_id, new_position)

    def message_player(self, player_id, message):
        message_packet = {
            'player_id': player_id,
            'message': message
        }
        self.send_to_player(player_id, message_packet)

    def send_to_player(self, player_id, packet):
        self.players[player_id]['socket'].sendall(json.dumps(packet).encode('utf-8'))

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
        self.event_manager.subscribe('damage_received', self.notify_damage_received)
        self.event_manager.subscribe('player_died', self.notify_player_died)


    def notify_tile_working(self, player_id, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'working',
            'tile_pos': tile_position,
            'is_success': is_success,
            'player_id': player_id

        }
        self.broadcast(data_packet)

    def notify_tile_worked(self, player_id, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'worked',
            'tile_pos': tile_position,
            'is_success': is_success

        }
        self.broadcast(data_packet)

    def notify_tile_activated(self, player_id, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'activated',
            'tile_pos': tile_position,
            'is_success': is_success,
            'player_id': player_id
        }
        self.broadcast(data_packet)

    def notify_tile_ready(self, player_id, tile_position, is_success):
        data_packet = {
            'origin': 'tile',
            'action': 'ready',
            'tile_pos': tile_position,
            'is_success': is_success
        }
        self.broadcast(data_packet)

    def notify_damage_received(self, player_id, position, is_success):
        self.message_player(player_id, "damage_received")

    def notify_player_died(self, player_id, position, is_success):
        self.message_player(player_id, "player_died")
        # Check for fights ending
        for fight in self.fights:
            if fight.aggressor == player_id or fight.defender == player_id:
                self.message_player(fight.aggressor, "fight_concluded")
                self.message_player(fight.defender, "fight_concluded")

if __name__ == "__main__":
    server = GameServer()
    server.start()


import json
import socket
import sys
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

global_exit_flag = False

# Custom exception for signaling exit
class ExitThread(Exception):
    pass

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
        self.player_id = self.get_id()
        self.message_history = MessageHistory()
        # Start a thread to receive messages from the server
        self.network_thread = threading.Thread(target=self.receive_messages, args=(), daemon=True)
        self.network_thread.start()
        self.exit_flag = False
        threading.Timer(1, self.get_players).start()
        self.get_players()

    def get_id(self):
        data_packet = {
            'request': 'id',
        }
        self.client_socket.sendall(json.dumps(data_packet).encode('utf-8'))
        data = self.client_socket.recv(1024).decode('utf-8')
        data = json.loads(data)
        # send our 0 ack
        assert len(b'\00') == 1
        self.client_socket.sendall(b'\00')
        return data['id']
    
    def get_players(self):
        data_packet = {
            'request': 'players',
        }
        self.client_socket.sendall(json.dumps(data_packet).encode('utf-8'))

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
    
    def close_connection(self):
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()

    def send_fight_action(self, character, fight_action):
        initial_state = {
            'player_id': self.player_id,
            'position': character.position,
            'action': 'fight_action',
            'fight_action' : fight_action
        }
        return self.client_socket.sendall(json.dumps(initial_state).encode('utf-8'))

    def send_action(self, character, action):
        initial_state = {
            'player_id': self.player_id,
            'position': character.position,
            'action': action
        }
        logging.info(initial_state)
        return self.client_socket.sendall(json.dumps(initial_state).encode('utf-8'))
    
    def send_message(self, message):
        initial_state = {
            'player_id': self.player_id,
            'message': message,
        }
        return self.client_socket.sendall(json.dumps(initial_state).encode('utf-8'))

    def send_tile_update(self, character):
        self.send_action(character, "farm")

    def send_position_update(self, character):
        self.send_action(character, "move")

    def receive_messages(self):
        """Thread to receive messages from the server and update player positions."""
        global player_positions
        global global_exit_flag
        logging.info("starting receive messages thread")
        while not (global_exit_flag or self.exit_flag):
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
                            self.handle_command(command)
                        except json.JSONDecodeError:
                            logging.error("Received invalid JSON:", message)
                        except ExitThread:
                            logging.info("Worker thread exiting due to ExitThread exception.")
                            return
            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                logging.error(repr(traceback.print_exc(e)))

    def handle_command(self, command):
        global global_exit_flag
        logging.info(f"received command : {command}")
        self.message_history.add_message(str(command))
        if command.get('new_position'):
            player_id = command['player_id']
            position = command['new_position']
            # Update the player position in a thread-safe manner
            with positions_lock:
                player_positions[player_id] = position
        elif command.get("gift"):
            player_id = command['player_id']
            if player_id == self.player_id and command["amount"]:
                self.map.event_manager.publish("xp_received", player_id=player_id, amount=command["amount"])
        elif command.get("message"):
            if command["message"] == "quit":
                global_exit_flag = True
                self.exit_flag = True
                raise ExitThread()
            if command["message"] == "damage_received":
                # hurt player
                self.map.event_manager.publish("damage_received")
            if command["message"] == "fight_initiated":
                self.map.event_manager.publish("fight_initiated")
            if command["message"] == "fight_concluded":
                self.map.event_manager.publish("fight_concluded")

        elif command.get('origin') and command.get('origin') == "tile":
            logging.info("tile action received")
            action = command['action']
            pos_array = command['tile_pos']
            is_success = command['is_success']
            if not is_success:
                return
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
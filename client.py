
import json
import socket
import threading

from character import Position2D

# Global variable to hold player positions
player_positions = {}
positions_lock = threading.Lock()  # Lock for thread-safe access to player_positions

def create_connection(host='127.0.0.1', port=43210, username='Player1'):
    """Create a socket connection to the game server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    initial_state = {
        'player_id': username,
        'position': Position2D(0,0)
    }
    client_socket.sendall(json.dumps(initial_state).encode('utf-8'))  # Send the username to the server

    # Start a thread to receive messages from the server
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    
    return client_socket

def send_update(connection, username, character):
    """Create a socket connection to the game server."""
    initial_state = {
        'player_id': username,
        'position': character.position,
        'action': 'move'
    }
    return connection.sendall(json.dumps(initial_state).encode('utf-8'))  # Send the username to the server

def receive_messages(client_socket):
    """Thread to receive messages from the server and update player positions."""
    global player_positions
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break  # Connection closed
            # Process the received data
            messages = data.splitlines()  # Assuming each message is on a new line
            for message in messages:
                if message:
                    try:
                        command = json.loads(message)
                        if command.get('new_position'):
                            player_id = command['player_id']
                            position = command['new_position']
                            # Update the player position in a thread-safe manner
                            with positions_lock:
                                player_positions[player_id] = position
                    except json.JSONDecodeError:
                        print("Received invalid JSON:", message)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

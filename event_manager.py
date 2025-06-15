import logging


class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, listener):
        logging.info(f"Subscribing to event: {event_type} with listener: {listener}")
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def publish(self, event_type, player_id, position, is_success):
        logging.info(f"Publishing event: {event_type} with data: {player_id} {position} {is_success}")
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(player_id, position, is_success)
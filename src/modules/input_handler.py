import logging
from typing import Dict, Any
import subprocess

class InputHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def process_event(self, event_data: Dict[str, Any]) -> None:
        """Process input events from the web client"""
        try:
            event_type = event_data.get('type')
            if not event_type:
                self.logger.error("Missing event type in input event")
                return

            if event_type == 'mouse':
                self._handle_mouse_event(event_data)
            elif event_type == 'keyboard':
                self._handle_keyboard_event(event_data)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
        except Exception as e:
            self.logger.error(f"Error processing input event: {e}")

    def _handle_mouse_event(self, event_data: Dict[str, Any]) -> None:
        """Handle mouse events using xdotool"""
        try:
            x = event_data.get('x', 0)
            y = event_data.get('y', 0)
            button = event_data.get('button')
            action = event_data.get('action')

            if action == 'move':
                subprocess.run(['xdotool', 'mousemove', str(x), str(y)])
            elif action == 'click':
                subprocess.run(['xdotool', 'click', str(button)])
            elif action == 'doubleclick':
                subprocess.run(['xdotool', 'click', '--repeat', '2', str(button)])
        except Exception as e:
            self.logger.error(f"Error handling mouse event: {e}")

    def _handle_keyboard_event(self, event_data: Dict[str, Any]) -> None:
        """Handle keyboard events using xdotool"""
        try:
            key = event_data.get('key')
            if not key:
                return

            if event_data.get('action') == 'keydown':
                subprocess.run(['xdotool', 'key', key])
        except Exception as e:
            self.logger.error(f"Error handling keyboard event: {e}") 
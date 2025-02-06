import pyautogui
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
import logging

logger = logging.getLogger(__name__)

class InputHandler:
    def __init__(self):
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.special_keys_map = {
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'shift': Key.shift,
            'enter': Key.enter,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'tab': Key.tab,
            'space': Key.space,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'esc': Key.esc,
            'command': Key.cmd,
        }
        
    def handle_mouse(self, data):
        try:
            event_type = data.get('type')
            x = data.get('x')
            y = data.get('y')
            
            if not all([event_type, x, y]):
                return
                
            # Move mouse to position
            self.mouse.position = (x, y)
            
            # Handle click events
            if event_type == 'click':
                self.mouse.click(Button.left)
            elif event_type == 'rightclick':
                self.mouse.click(Button.right)
            elif event_type == 'doubleclick':
                self.mouse.click(Button.left, 2)
                
        except Exception as e:
            logger.error(f"Error handling mouse event: {str(e)}")
            
    def handle_keyboard(self, data):
        try:
            key = data.get('key')
            event_type = data.get('type', 'keydown')
            
            if not key:
                return
                
            if len(key) == 1:  # Regular character
                if event_type == 'keydown':
                    self.keyboard.press(key)
                    self.keyboard.release(key)
            else:  # Special key
                special_key = self.special_keys_map.get(key.lower())
                if special_key:
                    if event_type == 'keydown':
                        self.keyboard.press(special_key)
                    else:
                        self.keyboard.release(special_key)
                        
        except Exception as e:
            logger.error(f"Error handling keyboard event: {str(e)}")
            
    def handle_special_keys(self, data):
        try:
            keys = data.get('keys', [])
            if not keys:
                return
                
            # Press all keys in sequence
            pressed_keys = []
            for key in keys:
                if key in self.special_keys_map:
                    self.keyboard.press(self.special_keys_map[key])
                    pressed_keys.append(self.special_keys_map[key])
                elif len(key) == 1:
                    self.keyboard.press(key)
                    pressed_keys.append(key)
                    
            # Release all keys in reverse order
            for key in reversed(pressed_keys):
                self.keyboard.release(key)
                
        except Exception as e:
            logger.error(f"Error handling special keys: {str(e)}") 
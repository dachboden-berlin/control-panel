from gui import WindowManager
from .lasergame import LaserGame


class TerminalGUI(WindowManager):
    def __init__(self):
        super().__init__('TerminalGUI')
        self.create_new_desktop("LaserGame", make_selected=True)
        self.desktop.add_element(LaserGame("LaserGame", self.desktop), True)
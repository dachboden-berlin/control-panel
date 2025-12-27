from gui import WindowManager, widgets


class TerminalGUI(WindowManager):
    def __init__(self):
        super().__init__('TerminalGUI')
        self.create_new_desktop("LaserGame", make_selected=True)
        self.desktop.add_element(widgets.LaserGame("LaserGame", self.desktop), True)
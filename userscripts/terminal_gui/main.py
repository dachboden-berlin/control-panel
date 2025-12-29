from gui import WindowManager, widgets


GUI_GAP = 8


class TerminalGUI(WindowManager):
    def __init__(self):
        super().__init__('TerminalGUI')
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.create_new_desktop("GUI", make_selected=True)
        self.desktop.add_element(widgets.Terminal("Terminal", self.desktop, x=GUI_GAP, y=GUI_GAP, w=width // 2 - GUI_GAP, h=height - 2 * GUI_GAP))
        self.desktop.add_element(stl:=widgets.STLRenderer("ControlPanelAnim", self.desktop, "controlpanel.stl", x=width // 2 + GUI_GAP//2, y=GUI_GAP, w=width//2 - GUI_GAP, h=height - 2 * GUI_GAP))
        stl.camera.rotate_up_down(30)
        stl.camera.zoom *= 0.75
        return
        # desktop.add_element(
        #     terminal :=
        # desktop.add_element(
        #     log := Log(desktop, x=RENDER_WIDTH // 2 + GUI_GAP, y=GUI_GAP, w=RENDER_WIDTH // 2 - 2 * GUI_GAP,
        #                h=RENDER_HEIGHT // 2 - 2 * GUI_GAP))
        # empty_widget = Widget(desktop, x=RENDER_WIDTH // 2 + GUI_GAP, y=RENDER_HEIGHT // 2 + GUI_GAP,
        #                       w=RENDER_WIDTH // 2 - 2 * GUI_GAP, h=RENDER_HEIGHT // 2 - 2 * GUI_GAP)
        # image = Image(desktop, x=RENDER_WIDTH // 2 + GUI_GAP, y=RENDER_HEIGHT // 2 + GUI_GAP,
        #               w=RENDER_WIDTH // 2 - 2 * GUI_GAP, h=RENDER_HEIGHT // 2 - 2 * GUI_GAP,
        #               image_path=os.path.join('media', 'robot36.png'))
        # text_field = TextField(desktop, x=RENDER_WIDTH // 2 + GUI_GAP, y=RENDER_HEIGHT // 2 + GUI_GAP,
        #                        w=RENDER_WIDTH // 2 - 2 * GUI_GAP, h=RENDER_HEIGHT // 2 - 2 * GUI_GAP,
        #                        text=os.path.join('media', 'roboter_ascii.txt'), load_ascii_file=True, transparent=False,
        #                        font=SMALL_FONT)
        # desktop.add_element(STLRenderer(desktop, "media/fox_centered.stl", x=RENDER_WIDTH // 2 + GUI_GAP,
        #                                 y=RENDER_HEIGHT // 2 + GUI_GAP,
        #                                 w=RENDER_WIDTH // 2 - 2 * GUI_GAP, h=RENDER_HEIGHT // 2 - 2 * GUI_GAP))
        # desktop.add_element(LoginWindow(desktop))
        # desktop.terminal = terminal
        # desktop.add_element(Taskbar(desktop, 20))
        # log.print_to_log("ROTER TEXT", (255, 0, 0))
        #
        # desktop2 = desktops[1]
        # desktop2.add_element(Radar(desktop2, png='media/red_dot_image.png'))
        #
        # desktop3 = desktops[2]
        # from laser_game import LaserGame
        # desktop3.add_element(LaserGame(desktop3))
        #
        # desktop4 = desktops[3]
        # from dmx_monitor import DMXMonitor
        # desktop4.add_element(DMXMonitor(None, 0, 0, RENDER_WIDTH, RENDER_HEIGHT))

from controlpanel import api
from .main import TerminalGUI
from datetime import datetime


terminal_gui = TerminalGUI()


@api.callback(source="TerminalInputBox", action="TextInput")
def console(event: api.Event[str]):
    split = event.value.split(" ")
    command, *args = split
    if not command.startswith("/"):
        time_str = datetime.now().strftime("%H:%M")
        terminal_gui.desktop.elements[0].elements[0].print_to_log(f"{time_str} {event.value}")
        return
    match command:
        case "/display":
            api.get_device("fourteensegment").text = " ".join(args)
        case _:
            terminal_gui.desktop.elements[0].elements[0].print_to_log(f"Unknown command: {command}", (255, 255, 0))



@api.call_with_frequency(4)
def rotate_controlpanel_model():
    terminal_gui.desktop.widget_manifest["ControlPanelAnim"].camera.rotate_left_right(5)
    terminal_gui.desktop.widget_manifest["ControlPanelAnim"].flag_as_needing_rerender()


api.add_game(terminal_gui, True)

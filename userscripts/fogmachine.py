import time

from controlpanel import api

last_fog = time.time()


def turn_on_fog_machine():
    global last_fog

    current_time = time.time()

    if current_time < last_fog + 310:
        api.get_device("FogMachine").turn_off()
        return

    api.get_device("FogMachine").turn_on()
    last_fog = current_time

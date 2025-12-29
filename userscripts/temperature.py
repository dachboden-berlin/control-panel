from fogmachine import turn_on_fog_machine

from controlpanel import api

temperature = 20


def update_temperature():
    api.get_device("Temperature").duty = temperature / 100


def increase_temperature():
    global temperature
    temperature += 1


@api.callback(source="WaterFlowSensor")
def on_cooling_water(event: api.Event):
    global temperature

    temperature -= event.value


def check_temperature():
    if temperature > 95:
        turn_on_fog_machine()


@api.call_with_frequency(1)
def loop():
    update_temperature()
    increase_temperature()
    check_temperature()

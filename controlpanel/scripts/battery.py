import time

from controlpanel import api

FLICKER_THRESHOLD_SECONDS = 60
POWER_OFF_THRESHOLD_SECONDS = 180

battery_capacity = 1  # between 0 and 1
is_battery_inserted = True
last_unplug_time = time.time()

BUTTON_TO_PORT_LIGHT = {
    "BatteryPortButtonPanel": "BatteryPortLightPanel",
    "BatteryPortButtonReactor": "BatteryPortLightReactor",
}


@api.callback(source="BatteryPortButtonPanel")
@api.callback(source="BatteryPortButtonReactor")
def on_battery_button_event(event: api.Event):
    global is_battery_inserted
    global last_unplug_time

    port_light_name = BUTTON_TO_PORT_LIGHT.get(event.source)

    if port_light_name is not None:
        device = api.get_device(port_light_name)  # type: ignore

        if event.action == "ButtonReleased":
            device.color = (255, 0, 0)
            last_unplug_time = time.time()
            is_battery_inserted = False

        elif event.action == "ButtonPressed":
            device.color = (0, 255, 0)
            is_battery_inserted = True


def update_voltmeter():
    if is_battery_inserted:
        api.get_device("Voltmeter1").duty = 0
        api.get_device("Voltmeter2").duty = 0
        api.get_device("Voltmeter3").duty = 0
        api.get_device("Voltmeter4").duty = 0
    else:
        api.get_device("Voltmeter1").duty = battery_capacity
        api.get_device("Voltmeter2").duty = battery_capacity
        api.get_device("Voltmeter3").duty = battery_capacity
        api.get_device("Voltmeter4").duty = battery_capacity


def update_led_ring():
    if is_battery_inserted and battery_capacity > 0.3:
        if int(time.time()) % 2 == 0:
            api.get_device("BatteryPortLightPanel").color = (0, 255, 255)
        else:
            api.get_device("BatteryPortLightPanel").color = (0, 0, 0)
            api.get_device("BatteryPortLightPanel").blackout()
            api.get_device("")


def update_cell():
    global is_battery_inserted, last_unplug_time

    if is_battery_inserted:
        api.get_device("BatteriePWM").duty = 0
        return

    elapsed_time = time.time() - last_unplug_time

    if elapsed_time >= POWER_OFF_THRESHOLD_SECONDS:
        api.get_device("BatteriePWM").duty = 0
    elif elapsed_time >= FLICKER_THRESHOLD_SECONDS:
        # TODO: Use random strobe
        api.get_device("BatteriePWM").duty = battery_capacity
    else:
        # Only run this if we are NOT flickering and NOT powered off
        api.get_device("BatteriePWM").duty = battery_capacity


@api.call_with_frequency(1)
def loop():
    update_voltmeter()
    update_led_ring()
    update_cell()

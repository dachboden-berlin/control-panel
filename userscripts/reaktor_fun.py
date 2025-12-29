from controlpanel import api
import colorsys
from controlpanel.api.logger import get_logger

logger = get_logger("ReaktorFun")

# --- State Management ---
# We track the desired state of our toggleable devices
# Default to False (Off)
device_states = {
    "fog": False,       # Controlled by Sw 0/1
    "plasma": False,    # Controlled by Sw 2/3
    "spot_left": False, # Controlled by Sw 4/5
    "spot_right": False # Controlled by Sw 6/7
}

# --- Mapping ---
# Switch Index -> (State Key, Target Value)
# Even index = Switch turned ON -> State True
# Odd index = Switch turned OFF -> State False
INPUT_MAP = {
    0: ("fog", True),
    1: ("fog", False),
    2: ("plasma", True),
    3: ("plasma", False),
    4: ("spot_left", True),
    5: ("spot_left", False),
    6: ("spot_right", True),
    7: ("spot_right", False),
}

# --- Input Callback ---

@api.callback(source="AnnieShiftRegister")
def on_switch_event(event):
    """
    Handles events from the 4-switch panel.
    event.value is expected to be a tuple of (index, pressed_bool).
    The shift register sends updates only on change.
    We only care when a position is ACTIVE (True).
    The 'released' state of a switch position (False) is just a transition,
    unless the switch is stateless, but description says:
    "Left position is index 0... right position 1..."
    "send ((0,True)) if turn left, but ((0,False)) if back to released"
    "We only want to turn off if it is going to ((1, True))"
    So we ONLY act on `pressed == True`.
    """
    changes = False
    
    # Iterate through all changes in this event
    # event.value is [(idx, bool), ...]
    for idx, pressed in event.value:
        if pressed:
            if idx in INPUT_MAP:
                key, state_val = INPUT_MAP[idx]
                
                if device_states[key] != state_val:
                    device_states[key] = state_val
                    logger.info(f"[Reaktor] {key} -> {state_val}")
                    
                    # Apply Digital States Immediately
                    if key == "fog":
                        set_digital("FogMachine", state_val)
                    elif key == "plasma":
                        set_digital("Plasmakugel", state_val)
                    # Spots are handled in loop for Color, 
                    # but we could force an update for responsiveness if we wanted.
                    
def set_digital(dev_name, value):
    dev = api.get_device(dev_name)
    if dev:
        dev.set_value(value)
    else:
        logger.warning(f"Device {dev_name} not found")

# --- Main Loop ---

def get_normalized_poti(name):
    dev = api.get_device(name)
    if not dev: return 0.0
    val = dev.value
    # Heuristic normalization if raw ADC is usually 4095
    if val > 1.0: val /= 4095.0
    return max(0.0, min(1.0, val))

@api.call_with_frequency(20)
def loop():
    # 1. Calculate Common Color from Potis
    hue = get_normalized_poti("PotiLeft")
    bri = get_normalized_poti("PotiRight")
    
    # Saturation fixed at 1.0 for vibrant color
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, bri)
    
    # RGBW tuple (R, G, B, W) - we leave W=0 for pure color
    # Scale to 0-255
    color_on = (int(r*255), int(g*255), int(b*255), 0)
    color_off = (0, 0, 0, 0)
    
    # 2. Update Spots based on State
    spot_l = api.get_device("EntranceSpotLeft")
    if spot_l:
        target = color_on if device_states["spot_left"] else color_off
        spot_l.set_color(target)

    spot_r = api.get_device("EntranceSpotRight")
    if spot_r:
        target = color_on if device_states["spot_right"] else color_off
        spot_r.set_color(target)
import math
from controlpanel import api
from controlpanel.dmx.devices import HydroBeamX12
from controlpanel.api.logger import get_logger
import pygame

# --- Configuration ---
MOVING_HEADS = ["MovingHeadRight", "MovingHeadLeft"]
AXIS_PAN = 0
AXIS_TILT = 1
BTN_TRIGGER = 0
BTN_SIDE = 1
JOYSTICK_ID = 0

# Pan/Tilt Ranges (in radians)
MAX_PHI = math.pi*8/6 
MAX_THETA = math.pi*12./24.

# Colors from Enum
COLORS = [
    HydroBeamX12.COLOR.WHITE,
    HydroBeamX12.COLOR.RED,
    HydroBeamX12.COLOR.ORANGE,
    HydroBeamX12.COLOR.AQUAMARINE,
    HydroBeamX12.COLOR.GREEN,
    HydroBeamX12.COLOR.LIGHT_GREEN,
    HydroBeamX12.COLOR.LAVENDER,
    HydroBeamX12.COLOR.PINK,
    HydroBeamX12.COLOR.LIGHT_YELLOW,
    HydroBeamX12.COLOR.MAGENTA,
    HydroBeamX12.COLOR.CYAN,
    HydroBeamX12.COLOR.YELLOW,
    HydroBeamX12.COLOR.WHITE_WARM,
    HydroBeamX12.COLOR.WHITE_COOL,
    HydroBeamX12.COLOR.UV
]

# --- State ---
trigger_held = False
color_idx = 0
color = COLORS[0]

# --- Setup ---
joystick = None
logger = get_logger("JoystickFun")

def get_joystick(index: int = 0) -> Joystick | None:
    """
    Get the Nth connected joystick, wrapped in a safe Joystick object.
    :param index: The index of the joystick (default 0 for the first one).
    :return: Joystick object or None if not found or GameManager not initialized.
    """
    if services.game_manager is None:
        return None
    
    # helper to access private _joysticks safely
    joysticks = getattr(services.game_manager, "_joysticks", {})
    if not joysticks:
        return None
        
    try:
        # Return the Nth joystick connected
        raw_joystick = list(joysticks.values())[index]
        return Joystick(raw_joystick)
    except IndexError:
        return None

def init_joystick():
    global joystick
    # Try indices 0 to 9 to find any joystick
    for i in range(10):
        try:
             if pygame.joystick.get_count() > i:
                 joystick = pygame.joystick.Joystick(i)
                 joystick.init()
                 logger.info(f"Initialized joystick {i}: {joystick.get_name()}")
                 break
        except Exception as e:
            logger.debug(f"Failed to check joystick {i}: {e}")

@api.call_with_frequency(10)
def loop():
    global joystick, color_idx, trigger_held, color
    
    # Retrieve Joystick via safe API
    joystick = get_joystick(0)
    if not joystick:
        if pygame.joystick.get_count() > 0:
             try:
                 j = pygame.joystick.Joystick(0)
                 j.init()
             except:
                 pass
        return

    # Process Events logic is handled by backend game loop usually.
    # We just poll state.

    try:
        # --- Axes (Pan/Tilt) ---
        x_val = joystick.get_axis(AXIS_PAN)
        y_val = joystick.get_axis(AXIS_TILT)
        
        # Deadzone & Exponential Curve
        x_v = x_val * x_val
        if x_val < 0: x_v = -x_v
        
        y_v = y_val * y_val
        if y_val < 0: y_v = -y_v
        
        phi = -x_v * MAX_PHI  # Inverted X
        theta = -y_v * MAX_THETA # Inverted Y

        # --- Buttons ---
        curr_trigger = joystick.get_button(BTN_TRIGGER)
        
        # Detect Rising Edge for Color Cycle
        if curr_trigger and not trigger_held:
            color_idx = (color_idx + 1) % len(COLORS)
            color = COLORS[color_idx]
            logger.debug(f"Color cycled to: {color}")
            
        trigger_held = curr_trigger
        
        # Apply to ALL moving heads
        for head_name in MOVING_HEADS:
            dev = api.get_device(head_name)
            if not dev: continue
            
            # Map API to Device
            if hasattr(dev, "set_color"):
                dev.set_color(color)
            
            if hasattr(dev, "set_phi"):
                dev.set_phi(phi)
            
            if hasattr(dev, "set_theta"):
                dev.set_theta(theta)

            if hasattr(dev, "set_intensity"):
                dev.set_intensity(1.0 if trigger_held else 0.0)

    except Exception as e:
        logger.error(f"Error in loop: {e}")
        pass

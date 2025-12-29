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
    0, # White
    4, # Read
    8, #Orange
    12, #Aqua
    16, #Green
    20, #Light Green
    24, #Lavender
    28, #Pink
    32, #Light Yellow
    36, #Magenta
    40, #Cyan
    44, #Yellow
    48, #White Warm
    52, #White Cool
    56, #UV
]

# --- State ---
trigger_held = False
color_idx = 0
color = COLORS[0]

# --- Setup ---
joystick = None
logger = get_logger("JoystickFun")



def init_joystick():
    global joystick
    if pygame.joystick.get_count() > JOYSTICK_ID:
        try:
            joystick = pygame.joystick.Joystick(JOYSTICK_ID)
            joystick.init()
            logger.info(f"[Joystick] Initialized: {joystick.get_name()}")
        except Exception as e:
            logger.error(f"[Joystick] Failed to init: {e}")
    else:
        logger.info("No joystick found.") 
        pass


@api.call_with_frequency(10)
def loop():
    global joystick, color_idx, trigger_held, color
    
    # Ensure Joystick is ready
    if not joystick:
        init_joystick()
        if not joystick:
            return


    # Process Events logic is handled by backend game loop usually.
    # We just poll state.

    try:
        # --- Axes (Pan/Tilt) ---
        x_val = joystick.get_axis(AXIS_PAN)
        y_val = joystick.get_axis(AXIS_TILT)
        logger.debug(f"[Joystick] Polling: {x_val} {y_val}")
        
        # Deadzone & Exponential Curve
        x_v = x_val **3
        y_v = y_val **3
        
        phi = x_v * MAX_PHI  # Inverted X
        theta = y_v * MAX_THETA # Inverted Y

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
            if not dev:
                logger.debug(f"Device not found: {head_name}")
                continue
            
            logger.debug(f"Found device: {head_name}")
            logger.debug(f"Color: {color}")
            logger.debug(f"Phi: {phi}")
            logger.debug(f"Theta: {theta}")
            logger.debug(f"Intensity: {trigger_held}")
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

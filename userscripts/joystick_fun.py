import pygame
import math
from controlpanel import api

# --- Configuration ---
JOYSTICK_ID = 0
MOVING_HEADS = ["MovingHeadRight", "MovingHeadLeft"]
AXIS_PAN = 0
AXIS_TILT = 1
BTN_TRIGGER = 0
BTN_SIDE = 1

# Pan/Tilt Ranges (in radians)
# Adjust these based on preference/safe limits
MAX_PHI = math.pi      # +/- 180 degrees
MAX_THETA = math.pi/2  # +/- 90 degrees

# Gobo Values (0-255)
# Assuming some standard slots.
GOBOS = [0, 10, 20, 30, 40, 50, 60, 70] 

# --- State ---
current_gobo_index = 0
is_trigger_held = False
last_btn_side_state = False

# --- Setup ---
joystick = None

def init_joystick():
    global joystick
    if pygame.joystick.get_count() > JOYSTICK_ID:
        try:
            joystick = pygame.joystick.Joystick(JOYSTICK_ID)
            joystick.init()
            print(f"[Joystick] Initialized: {joystick.get_name()}")
        except Exception as e:
            print(f"[Joystick] Failed to init: {e}")
    else:
        # print("No joystick found.") 
        pass

@api.call_with_frequency(30)
def loop():
    global joystick, current_gobo_index, is_trigger_held, last_btn_side_state
    
    # Ensure Joystick is ready
    if not joystick:
        init_joystick()
        if not joystick:
            return

    # Process Pygame Events (Pump)
    
    # --- Axes (Pan/Tilt) ---
    try:
        x_val = joystick.get_axis(AXIS_PAN)
        y_val = joystick.get_axis(AXIS_TILT)
        
        # Deadzone
        if abs(x_val) < 0.1: x_val = 0
        if abs(y_val) < 0.1: y_val = 0

        # Map to device
        # Phi: -PI to PI
        phi = x_val * MAX_PHI
        # Theta: -PI/2 to PI/2
        theta = y_val * MAX_THETA # Invert Y if needed? Usually Up is -1 on joysticks.
        
        # --- Buttons ---
        trigger_state = joystick.get_button(BTN_TRIGGER)
        if trigger_state != is_trigger_held:
            is_trigger_held = trigger_state
        
        # Side Button (Gobo Cycle) controls global state
        side_state = joystick.get_button(BTN_SIDE)
        gobo_changed = False
        if side_state and not last_btn_side_state:
            # Pressed
            current_gobo_index = (current_gobo_index + 1) % len(GOBOS)
            gobo_changed = True
            print(f"[Joystick] Gobo set to {GOBOS[current_gobo_index]}")
            
        last_btn_side_state = side_state

        # Apply to ALL moving heads
        for head_name in MOVING_HEADS:
            dev = api.get_device(head_name)
            if not dev:
                continue

            if hasattr(dev, "set_phi"):
                dev.set_phi(phi)
            
            if hasattr(dev, "set_theta"):
                dev.set_theta(theta)

            if hasattr(dev, "set_intensity"):
                dev.set_intensity(1.0 if is_trigger_held else 0.0)


    except Exception as e:
        print(f"[Joystick] Error: {e}")

import random
import time
from controlpanel import api

# --- Configuration ---

COLORS = {
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Cyan": (0, 255, 255),
    "Magenta": (255, 0, 255),
    "White": (255, 255, 255),
}
COLOR_LIST = list(COLORS.values())

STARBAR_TOP = "StarbarTop"
STARBARS_USER = ["StarbarLeft", "StarbarRight"]
ALL_STARBARS = [STARBAR_TOP] + STARBARS_USER

BUTTONS = ["ButtonRed", "ButtonGreen", "ButtonBlue"]

TIMEOUT_SECONDS = 60
MAX_SCORE = 12
BRIGHTNESS = 100

# --- State ---

target_color = (0, 0, 0)
last_activity_time = time.time()
game_active = True
current_score = 0  # 0 to 12

# --- Helpers ---

def set_starbar_color(starbar_name, color):
    dev = api.get_device(starbar_name)
    if not dev:
        return
    if hasattr(dev, "set_leds_to_color"):
        dev.set_leds_to_color(color)

def update_progress_lights():
    """
    Updates the white LEDs on all starbars to reflect current_score.
    First 'current_score' LEDs are ON (intensity 100), rest are OFF.
    """
    for name in ALL_STARBARS:
        dev = api.get_device(name)
        if not dev:
            continue
            
        # Access 'lights' list directly as per device definition
        if hasattr(dev, "lights"):
            # Create list of 12 ints
            new_lights = []
            for i in range(12): # Assuming 12 LEDs
                if i < current_score:
                    new_lights.append(BRIGHTNESS)
                else:
                    new_lights.append(0)
            dev.lights = new_lights

def start_new_round():
    global target_color, last_activity_time, game_active
    
    # Pick new random target color
    target_color = random.choice(COLOR_LIST)
    
    # Reset Timer
    last_activity_time = time.time()
    game_active = True
    
    # Update Top Bar Color
    set_starbar_color(STARBAR_TOP, target_color)
    
    # Update Progress Lights (Score is persisted across rounds unless timeout/win)
    update_progress_lights()
    
    # Reset User Bars Color (to current input)
    update_user_bars()
    
    print(f"[Starbars Riddle] New Round! Target: {target_color} | Score: {current_score}/{MAX_SCORE}")


def get_user_color():
    r = 255 if api.get_device("ButtonRed").pressed else 0
    g = 255 if api.get_device("ButtonGreen").pressed else 0
    b = 255 if api.get_device("ButtonBlue").pressed else 0
    return (r, g, b)

def update_user_bars():
    user_color = get_user_color()
    for name in STARBARS_USER:
        set_starbar_color(name, user_color)

def check_win_condition():
    global game_active
    
    if not game_active:
        return

    user_color = get_user_color()
    if user_color == target_color:
        handle_success()

def set_starbar_strobe(starbar_name, strobe_val):
    dev = api.get_device(starbar_name)
    if not dev:
        return
    if hasattr(dev, "strobe"):
        dev.strobe = strobe_val

def handle_success():
    global game_active, current_score, last_activity_time
    
    print("[Starbars Riddle] Riddle Solved!")
    
    # Increment Score
    current_score += 1
    
    # Update lights immediately to show progress
    update_progress_lights()
    
    if current_score >= MAX_SCORE:
        print("[Starbars Riddle] GAME CLEARED!")
        
        # Enable Strobe for Victory
        for name in ALL_STARBARS:
             set_starbar_strobe(name, 1.0) # Max strobe speed
             
        current_score = 0
        game_active = False
        last_activity_time = time.time()
        return

    # Start next round
    game_active = False 
    start_new_round()

def handle_timeout():
    global game_active, current_score
    print("[Starbars Riddle] Timeout! Resetting progress.")
    
    # Disable Strobe just in case
    for name in ALL_STARBARS:
         set_starbar_strobe(name, 0.0)

    current_score = 0
    update_progress_lights()
    start_new_round()


# --- Callbacks ---

@api.callback(source="ButtonRed")
@api.callback(source="ButtonGreen")
@api.callback(source="ButtonBlue")
def on_input(event: api.Event):
    if game_active:
        update_user_bars()
        check_win_condition()

# --- Loop ---

@api.call_with_frequency(1)
def game_loop():
    global last_activity_time, game_active, current_score
    
    now = time.time()
    
    # Victory Delay Logic with Strobe Cleanup
    if not game_active and current_score == 0: 
        if now - last_activity_time > 3: # 3 second victory party
             # Disable Strobe before starting new round
             for name in ALL_STARBARS:
                 set_starbar_strobe(name, 0.0)
                 
             start_new_round()
        return

    # Check Timeout
    if game_active and (now - last_activity_time > TIMEOUT_SECONDS):
        handle_timeout()


# --- Initialization ---
start_new_round()
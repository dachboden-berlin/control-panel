from keyboard import WIDTH, HEIGHT, button_pos, led_idx
from controlpanel import api
import random
import time
import colorsys
import logging
from controlpanel.api.logger import get_logger

# --- Logging Setup ---
logger = get_logger("GameOfLife")

logger.info("Initializing Game of Life Script")

# --- Logic & Optimization ---

SIZE = WIDTH * HEIGHT
logger.debug(f"Grid Size: {WIDTH}x{HEIGHT} = {SIZE} cells")

# Pre-calculate neighbors (flattened indices)
NEIGHBORS = [[] for _ in range(SIZE)]
# Pre-calculate Logical to Physical Mapping
LOGIC_TO_PHYS = [0] * SIZE

for x in range(WIDTH):
    for y in range(HEIGHT):
        idx = y * WIDTH + x
        LOGIC_TO_PHYS[idx] = led_idx(x, y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                nx, ny = (x + dx) % WIDTH, (y + dy) % HEIGHT
                n_idx = ny * WIDTH + nx
                NEIGHBORS[idx].append(n_idx)

# State: 0=Dead, 1=Alive
# Replaced bytearray with list for restricted env compatibility
BOARD = [0] * SIZE 
BOARD_NEXT = [0] * SIZE # Double buffer for simulation

# Parallel array for Mode 3 colors (r, g, b tuples)
BOARD_COLORS = [(120, 120, 120)] * SIZE 

# Global Pixel Buffer
PIXEL_DATA = [(0, 0, 0)] * SIZE

MIN_DELAY = 0.03
MAX_DELAY = 0.5 

# --- Modes ---
class Mode:
    CLASSIC = 1    # BW + Speed
    ADJUSTABLE = 2 # HSV Color + Speed
    RANDOM = 3     # Random Color + Speed
    FROZEN = 4     # No updates + Edit only

current_mode = Mode.CLASSIC
last_sim_time = 0.0

# --- Colors ---
COLOR_OFF = (0, 0, 0)
COLOR_CLASSIC_ALIVE = (50, 50, 80)

# --- Helpers ---

def clamp(val, min_v, max_v):
    if val < min_v: return min_v
    if val > max_v: return max_v
    return val

def get_poti_val(dev_name) -> float:
    """Returns 0.0 to 1.0 from ADC value property."""
    dev = api.get_device(dev_name)
    if not dev: 
        logger.warning(f"Device {dev_name} not found, returning 0.0")
        return 0.0
    val = dev.value
    # Safe check for raw int values without 'max' built-in
    if val > 1.0: val = val / 4095.0
    return clamp(val, 0.0, 1.0)

def spawn_color():
    # HSV: Random Hue, High Saturation, High Value
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 0.9, 1.0)
    return (int(r*120), int(g*120), int(b*120))

# --- Input Handlers ---

@api.callback(source="MultiButton01")
def set_mode_1(event):
    if event.value: set_mode(Mode.CLASSIC)

@api.callback(source="MultiButton02")
def set_mode_2(event):
    if event.value: set_mode(Mode.ADJUSTABLE)

@api.callback(source="MultiButton03")
def set_mode_3(event):
    if event.value: set_mode(Mode.RANDOM)

@api.callback(source="MultiButton04")
def set_mode_4(event):
    if event.value: set_mode(Mode.FROZEN)

def set_mode(mode):
    global current_mode
    if current_mode != mode:
        logger.info(f"[GoL] Mode changed from {current_mode} to {mode}")
        current_mode = mode
    else:
        logger.debug(f"[GoL] Mode set to {mode} (no change)")


@api.callback(source="MainframeKeys", action="ButtonsChanged")
def toggle_cells(event):
    global BOARD, BOARD_COLORS
    changes = False
    for button_id, pressed in event.value:
        if pressed:
            x, y = button_pos(button_id)
            idx = y * WIDTH + x
            # Toggle state
            if BOARD[idx] == 1:
                BOARD[idx] = 0
                logger.debug(f"Cell ({x}, {y}) toggled DEAD")
            else:
                BOARD[idx] = 1
                BOARD_COLORS[idx] = spawn_color()
                logger.debug(f"Cell ({x}, {y}) toggled ALIVE")
            changes = True
    
    # We do NOT force render here anymore.
    # The main loop runs at 30Hz and will pick up the change immediately.
    # This separates Input vs Render.

@api.callback(source="DialReset")
def reset():
    global BOARD
    logger.info("[GoL] Reset triggered")
    for i in range(SIZE):
        BOARD[i] = 0

# --- Loop ---

@api.call_with_frequency(30)
def loop():
    global BOARD, BOARD_NEXT, last_sim_time
    
    now = time.time()
    
    # 1. Read Inputs
    speed_val = get_poti_val("PotiRight")
    color_val = get_poti_val("PotiLeft")
    
    # 2. Simulation Step
    # Decoupled from Frame Rate. Only runs when time is right.
    # We use a custom update_delay based on poti.
    
    update_delay = MAX_DELAY - (speed_val * (MAX_DELAY - MIN_DELAY))
    
    if current_mode != Mode.FROZEN and (now - last_sim_time > update_delay):
        last_sim_time = now
        
        # Perform Simulation
        # Using two lists: BOARD (current) -> BOARD_NEXT (future)
        alive_count = 0
        for i in range(SIZE):
            cell_state = BOARD[i]
            n = 0
            for neighbor_idx in NEIGHBORS[i]:
                if BOARD[neighbor_idx] == 1:
                    n += 1
            
            if cell_state == 1:
                if n == 2 or n == 3:
                     BOARD_NEXT[i] = 1
                else:
                     BOARD_NEXT[i] = 0
            else:
                if n == 3:
                    BOARD_NEXT[i] = 1
                    BOARD_COLORS[i] = spawn_color() # Generate new color for birth
                else:
                    BOARD_NEXT[i] = 0
            
            if BOARD_NEXT[i] == 1:
                alive_count += 1
                
        # Swap buffers: Copy NEXT to CURRENT
        for i in range(SIZE):
            BOARD[i] = BOARD_NEXT[i]
            
        logger.debug(f"Sim Step: {alive_count} alive cells, Delay: {update_delay:.3f}s")
        
    # 3. Render Step (Always run at 30Hz)
    # Re-build PIXEL_DATA every frame based on authoritative BOARD state.
    # This ensures "button press visibility" is max 33ms latency.
    
    # Pre-calc Mode 2 color once per frame
    mode2_h = color_val # 0-1
    mode2_r, mode2_g, mode2_b = colorsys.hsv_to_rgb(mode2_h, 1.0, 1.0)
    mode2_color = (int(mode2_r*120), int(mode2_g*120), int(mode2_b*120))
    
    for i in range(SIZE):
        if BOARD[i] == 1:
            if current_mode == Mode.CLASSIC:
                color = COLOR_CLASSIC_ALIVE
            elif current_mode == Mode.ADJUSTABLE:
                color = mode2_color
            elif current_mode == Mode.RANDOM:
                color = BOARD_COLORS[i]
            elif current_mode == Mode.FROZEN:
                color = (100, 100, 100)
            else:
                 color = COLOR_OFF
        else:
            color = COLOR_OFF
            
        phys_idx = LOGIC_TO_PHYS[i]
        PIXEL_DATA[phys_idx] = color
        
    api.get_device("MainframeLEDs").set_pixels(PIXEL_DATA)

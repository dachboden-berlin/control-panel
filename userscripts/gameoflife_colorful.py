from keyboard import WIDTH, HEIGHT, button_pos, led_idx
from controlpanel import api
import random
import time
import colorsys

# --- Logic & Optimization ---

SIZE = WIDTH * HEIGHT

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
BOARD = bytearray(SIZE)
# Parallel array for Mode 3 colors (r, g, b tuples)
BOARD_COLORS = [(120, 120, 120)] * SIZE 

# Global Pixel Buffer to avoid re-allocation
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
last_update_time = 0.0
last_color_val = -1.0 # Force update on first run

# --- Colors ---
COLOR_OFF = (0, 0, 0)
COLOR_CLASSIC_ALIVE = (50, 50, 80)

# --- Helpers ---

def get_poti_val(dev_name) -> float:
    """Returns 0.0 to 1.0 from ADC value property."""
    dev = api.get_device(dev_name)
    if not dev: return 0.0
    val = dev.value
    if val > 1.0: val = val / 4095.0
    return max(0.0, min(1.0, val))

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
    global current_mode, last_color_val
    current_mode = mode
    last_color_val = -1.0 # Force redraw
    print(f"[GoL] Mode set to {mode}")


@api.callback(source="MainframeKeys", action="ButtonsChanged")
def toggle_cells(event):
    global BOARD, last_color_val
    for button_id, pressed in event.value:
        if pressed:
            x, y = button_pos(button_id)
            idx = y * WIDTH + x
            # Toggle state
            if BOARD[idx]:
                BOARD[idx] = 0
            else:
                BOARD[idx] = 1
                BOARD_COLORS[idx] = spawn_color()
    
    # Force redraw in next loop frame to update LEDs
    last_color_val = -1.0


@api.callback(source="DialReset")
def reset():
    global BOARD, PIXEL_DATA
    for i in range(SIZE):
        BOARD[i] = 0
        PIXEL_DATA[i] = COLOR_OFF # Reset physical buffer too? 
        # Note: PIXEL_DATA is indexed by Phys ID only if we fill it that way.
        # But wait, LOGIC_TO_PHYS maps logic->phys.
        # If we just clear PIXEL_DATA, it's fine since it covers all LEDs.
    api.get_device("MainframeLEDs").set_pixels(PIXEL_DATA)

# --- Loop ---

@api.call_with_frequency(30)
def loop():
    global BOARD, last_update_time, last_color_val
    
    now = time.time()
    
    # 1. Read Controls
    speed_val = get_poti_val("PotiRight")
    color_val = get_poti_val("PotiLeft")
    
    update_delay = MAX_DELAY - (speed_val * (MAX_DELAY - MIN_DELAY))
    
    should_game_update = (now - last_update_time > update_delay) and (current_mode != Mode.FROZEN)
    
    # Check if we need to redraw all (Mode change or Color Poti change in Mode 2)
    force_redraw = False
    
    # Check Color Poti change for Mode 2
    if current_mode == Mode.ADJUSTABLE:
        if abs(color_val - last_color_val) > 0.01:
            force_redraw = True
            last_color_val = color_val
    elif last_color_val != -1.0:
        # If we switched OUT of Mode 2 (or just init), we force redraw once
        force_redraw = True
        last_color_val = -1.0

    # Determine Base Color for Mode 2
    mode2_color = (120, 120, 120)
    if current_mode == Mode.ADJUSTABLE:
        r, g, b = colorsys.hsv_to_rgb(color_val, 1.0, 1.0)
        mode2_color = (int(r*120), int(g*120), int(b*120))

    # 2. Update & Render Layer
    if should_game_update or force_redraw:
        if should_game_update:
            last_update_time = now
            
        changes_made = False # For set_pixels optimization if we wanted, but we usually push every frame
                             # Actually `set_pixels` is cheap if data same?
                             # But here we only modify PIXEL_DATA if needed.

        # New board buffer (only needed if computing next generation)
        # If just Redrawing (force_redraw) but no game update, we use current BOARD.
        
        sim_board = BOARD if not should_game_update else bytearray(SIZE)
        
        for i in range(SIZE):
            cell_prev = BOARD[i]
            cell_new = cell_prev
            
            # Simulation Step
            if should_game_update:
                n = 0
                for neighbor_idx in NEIGHBORS[i]:
                    if BOARD[neighbor_idx]:
                        n += 1
                
                if cell_prev:
                    if n == 2 or n == 3: cell_new = 1
                    else: cell_new = 0
                else:
                    if n == 3: 
                        cell_new = 1
                        # Mode 3 Color Persistence logic:
                        # Should we generate new color? Yes.
                        BOARD_COLORS[i] = spawn_color()
                
                sim_board[i] = cell_new

            # Rendering Step (Merged)
            # Update Pixel Data if:
            # 1. State Changed (Dead <-> Alive)
            # 2. Force Redraw is active (Mode/Color changed)
            if (cell_new != cell_prev) or force_redraw:
                phys_idx = LOGIC_TO_PHYS[i]
                
                if cell_new:
                    if current_mode == Mode.CLASSIC:
                        PIXEL_DATA[phys_idx] = COLOR_CLASSIC_ALIVE
                    elif current_mode == Mode.ADJUSTABLE:
                        PIXEL_DATA[phys_idx] = mode2_color
                    elif current_mode == Mode.RANDOM:
                        PIXEL_DATA[phys_idx] = BOARD_COLORS[i]
                    elif current_mode == Mode.FROZEN:
                        PIXEL_DATA[phys_idx] = (100, 100, 100)
                else:
                    PIXEL_DATA[phys_idx] = COLOR_OFF

        if should_game_update:
            BOARD = sim_board
            
        api.get_device("MainframeLEDs").set_pixels(PIXEL_DATA)

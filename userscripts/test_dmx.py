from controlpanel import api
from controlpanel.dmx.devices import HydroBeamX12

# --- Configuration ---

BUTTONS = ["ButtonRed", "ButtonGreen", "ButtonBlue"]

# List of all DMX devices to control
DMX_DEVICES = [
    "PanelSpotLeft",
    "PanelSpotRight",
    "EntranceSpotRight",
    "StarbarRight",
    "MovingHeadRight",
    "StarbarTop",
    "MovingHeadLeft",
    "StarbarLeft",
    "EntranceSpotLeft",
]

# --- Helpers ---

def get_button_color():
    """Returns (r, g, b, is_active) based on button states."""
    r = 255 if api.get_device("ButtonRed").pressed else 0
    g = 255 if api.get_device("ButtonGreen").pressed else 0
    b = 255 if api.get_device("ButtonBlue").pressed else 0
    is_active = (r > 0 or g > 0 or b > 0)
    return (r, g, b), is_active

def rgb_to_moving_head_color(r, g, b):
    """Maps RGB combination to HydroBeamX12.COLOR enum."""
    if r and g and b: return HydroBeamX12.COLOR.WHITE
    if r and g:       return HydroBeamX12.COLOR.YELLOW
    if r and b:       return HydroBeamX12.COLOR.MAGENTA
    if g and b:       return HydroBeamX12.COLOR.CYAN
    if r:             return HydroBeamX12.COLOR.RED
    if g:             return HydroBeamX12.COLOR.GREEN
    if b:             return HydroBeamX12.COLOR.LIGHT_GREEN # Map says (0,0,255) is LIGHT_GREEN
    return HydroBeamX12.COLOR.WHITE # Default/Off state handling

# --- Callbacks ---

@api.callback(source="ButtonRed")
@api.callback(source="ButtonGreen")
@api.callback(source="ButtonBlue")
def on_button_event(event: api.Event):
    (r, g, b), is_active = get_button_color()
    
    # Calculate colors once
    rgb_color = (r, g, b)
    mh_color = rgb_to_moving_head_color(r, g, b)

    for dev_name in DMX_DEVICES:
        dev = api.get_device(dev_name)
        if not dev:
            continue
            
        # 1. Moving Heads (HydroBeamX12)
        if hasattr(dev, "set_color") and hasattr(dev, "set_intensity"):
            if is_active:
                dev.set_color(mh_color)
                dev.set_intensity(1.0)
            else:
                dev.set_intensity(0.0) # Turn off
        
        # 2. Starbars (VaritecColorsStarbar12)
        elif hasattr(dev, "set_leds_to_color") and hasattr(dev, "turn_off_lights"):
             # Set Color
             dev.set_leds_to_color(rgb_color)
             # Ensure 'white/effect' LEDs are off
             if hasattr(dev, "turn_off_lights"):
                 dev.turn_off_lights()
        
        # 3. RGBW Spots (RGBWLED)
        elif hasattr(dev, "color"): # RGBWLED has 'color' property
             # It accepts (r,g,b) or (r,g,b,w)
             try:
                 dev.color = rgb_color
             except:
                 pass
        
        # Fallback for generic RGB setters
        elif hasattr(dev, "r") and hasattr(dev, "g") and hasattr(dev, "b"):
             dev.r = r
             dev.g = g
             dev.b = b

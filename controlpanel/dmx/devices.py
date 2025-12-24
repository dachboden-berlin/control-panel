"""
This module describes the properties and behaviors of DMX Devices,
and are modeled after real-life devices.
"""
from .dmx import DMXDevice, DMXUniverse
import numpy as np
from enum import Enum
import math


TimeType = float


class MovingHead(DMXDevice):
    """
    Moving head.
    Modeled after the Shehds "LED Spot 100W Lighting" moving head
    CH1: Dimming        (0-255)
    CH2: Strobe Speed   (4-251)
         Open Light     (252-255)
    CH3: Pan            (0-255)
    CH4: Tilt           (0-255)
    CH5: Pan/Tilt Speed (0-255)
    CH6: Color          (0-255)
         White:         0-4
         Red:           5-9
         Green:         10-14
         Blue:          15-19
         Yellow:        20-24
         Purple:        25-29
         Cyan:          30-34
    CH7: Gobo 1
    CH8: Gobo 2
    CH9: Gobo 2 Rotation
    CH10: Prism Switch  (10-14)
          Prism Rot.    (15-255)
    CH11: Focus         (0-255)
    CH12: Pan fine      (0-255)
    CH13: Tilt fine     (0-255)
    CH14: Reset         (255)

    Pan:
    0.00 is pointing back
    0.15 is pointing left
    0.33 is pointing forward
    0.50 is pointing right

    Tilt:
    0.00 is pointing forward
    0.50 is fully up
    1.00 is pointing back
    """
    THETA_RANGE = (-95*np.pi/180, -5*np.pi/180)
    NUM_COLORS = 7
    NUM_GOBOS1 = 8
    NUM_GOBOS2 = 7
    BEAM_ANGLE = 16
    COLORS = {0: (255, 255, 255),
              1: (255, 0, 0),
              2: (0, 255, 0),
              3: (0, 0, 255),
              4: (255, 255, 0),
              5: (255, 0, 255),
              6: (0, 255, 255),
              }

    def __init__(self, name: str, chan_no: int, *, yaw_limit: tuple[float, float] | None = None, pitch_limit: tuple[float, float] | None = None):
        super().__init__(name, chan_no, num_chans=14)
        self._intensity: float = 1.0
        self._strobe: int = 255
        self._pan: float = 0.0
        self._tilt: float = 0.0
        self._speed: float = 1.0
        self._color: int = 0
        self._gobo1: int = 0
        self._gobo2: int = 0
        self._gobo2_rotation: int = 0
        self._prism: int = 0
        self._focus: float = 0.0
        self._pan_fine: float = 0.0
        self._tilt_fine: float = 0.0
        self._reset: float = 0.0
        
        self._yaw: float = 0.0
        self._pitch: float = -np.pi/4
        self.strobe_frequency: float = 1.0
        self.prism_speed: float = 0

        self._animation = None
        self.yaw_limit: tuple[float, float] | None = yaw_limit
        self.pitch_limit: tuple[float, float] | None = pitch_limit

    def get_rgb(self):
        return self.COLORS[self.color]
    
    def reset(self):
        self._reset = 1.0
    
    @property
    def intensity(self):
        return self._intensity
    
    @intensity.setter
    def intensity(self, value: float):
        self._intensity = min(1.0, max(0.0, value))
    
    @property
    def yaw(self) -> float:
        return self._yaw
    
    @yaw.setter
    def yaw(self, radians: float):
        self._pan = radians / (3*np.pi)  # 3pi = 540°
        if self._pan > 540/540:
            self._pan -= 360/540
        elif self._pan < 0/540:
            self._pan += 360/540
        unclamped_yaw = self._pan * 3*np.pi
        self._yaw = max(min(unclamped_yaw, self.yaw_limit[1]), self.yaw_limit[0]) if self.yaw_limit else unclamped_yaw

    @property
    def pitch(self) -> float:
        return self._pitch
    
    @pitch.setter
    def pitch(self, radians: float):
        angle = max(min(self.THETA_RANGE[1], radians), self.THETA_RANGE[0])
        self._pitch = angle
        self._tilt = angle/np.pi + 1/2

    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, value: float):
        self._speed = min(1.0, max(0.0, value))
        
    @property
    def prism(self):
        return True if self._prism >= 10 else False
    
    @prism.setter
    def prism(self, value: bool):
        if value is True:
            self._prism = 15 + int(240*self.prism_speed)
        elif value is False:
            self._prism = 0
    
    @property
    def strobe(self):
        return True if self._strobe <= 251 else False
    
    @strobe.setter
    def strobe(self, value: bool):
        if value is True:
            self._strobe = 4 + int(247*self.strobe_frequency)
        elif value is False:
            self._strobe = 255
    
    @property
    def color(self):
        return self._color // 5
    
    @color.setter
    def color(self, value: int):
        self._color = 5*(value % self.NUM_COLORS)
    
    @property
    def gobo1(self):
        return self._gobo1 // 10
    
    @gobo1.setter
    def gobo1(self, value: int):
        self._gobo1 = 10*(value % self.NUM_GOBOS1)
    
    @property
    def gobo2(self):
        return self._gobo2 // 10
    
    @gobo2.setter
    def gobo2(self, value: int):
        self._gobo2 = 10*(value % self.NUM_GOBOS2)
        
    @property
    def gobo2_rotation(self):
        return self._gobo2_rotation
    
    @gobo2_rotation.setter
    def gobo2_rotation(self, value: float):
        if value == 0:
            self._gobo2_rotation = 0
        elif value > 0:
            self._gobo2_rotation = 64 + int((127-64)*value)
        elif value < 0:
            self._gobo2_rotation = 255 - int(65 * (value+1))
    
    @property
    def focus(self):
        return self._focus
    
    @focus.setter
    def focus(self, value: float):
        self._focus = min(1.0, max(0.0, value))
    
    def next_color(self):
        if self.color < 30:
            self.color += 5
    
    def previous_color(self):
        if self.color >= 5:
            self.color -= 5

    def update(self, dmx: DMXUniverse):
        dmx.set_float(self.chan_no, 1, self._intensity)
        dmx.set_int(self.chan_no, 2, self._strobe)
        dmx.set_float(self.chan_no, 3, self._pan)
        dmx.set_float(self.chan_no, 4, self._tilt)
        dmx.set_float(self.chan_no, 5, 1 - self._speed)
        dmx.set_int(self.chan_no, 6, self._color)
        dmx.set_int(self.chan_no, 7, self._gobo1)
        dmx.set_int(self.chan_no, 8, self._gobo2)
        dmx.set_int(self.chan_no, 9, self._gobo2_rotation)
        dmx.set_int(self.chan_no, 10, self._prism)
        dmx.set_float(self.chan_no, 11, self._focus)
        dmx.set_float(self.chan_no, 12, self._pan_fine)
        dmx.set_float(self.chan_no, 13, self._tilt_fine)
        dmx.set_float(self.chan_no, 14, self._reset)


class HydroBeamX12(DMXDevice):
    """
    Moving head.
    Modeled after the Hydro Beam X12 moving head
    User manual: https://www.adj.com/cdn/shop/files/ADJ_HYDRO_BEAM_X12_-_USER_MANUAL.pdf?v=11308301875406801713

    Pan:
    0.0 is pointing right   | phi = 3pi/2
    0.166 is pointing back  | phi = pi
    0.333 is pointing left  | phi = pi/2
    0.5 is pointing forward | phi = 0
    0.666 is poing right    | phi = -pi/2
    0.833 is pointing back  | phi = -pi
    1.0 is pointling left   | phi = -3pi/2

    Tilt:
    0.166 is pointing forward
    0.50 is fully up
    0.833 is pointing back
    """

    class COLOR(Enum):
        WHITE = 0
        RED = 4
        ORANGE = 8
        AQUAMARINE = 12
        GREEN = 16
        LIGHT_GREEN = 20
        LAVENDER = 24
        PINK = 28
        LIGHT_YELLOW = 32
        MAGENTA = 36
        CYAN = 40
        YELLOW = 44
        WHITE_WARM = 48
        WHITE_COOL = 52
        UV = 56

    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, num_chans=18)
        self._pan: int = 255//2
        self._pan_fine: int = 255//2
        self._tilt: float = 255//2
        self._tilt_fine: float = 255//2
        self._color_wheel: int = 0
        self._static_gobo: int = 0
        self._prism1: int = 0
        self._prism1_rot: int = 0
        self._prism2: int = 0
        self._prism2_rot: int = 0
        self._strobe: int = 32
        self._dimmer: float = 1.0
        self._dimmer_fine: float = 0.0
        self._focus: float = 0.0
        self._focus_fine: float = 0.0
        self._frost: int = 0
        self._pan_tilt_speed: float = 0.0
        self._special_function: int = 0

    @staticmethod
    def _phi_to_pan(phi: float) -> float:
        return 1 / (3 * math.pi) * phi + 0.5  # (DeltaY-DeltaX)*x+b = mx+b

    @staticmethod
    def _theta_to_tilt(theta: float) -> float:
        return (-4/6) / math.pi * theta + 0.5  # (DeltaY-DeltaX)*x+b = mx+b

    @staticmethod
    def _encode_float_to_bytes(x) -> tuple[int, int]:
        assert 0.0 <= x <= 1.0
        n = int(round(x * 65535))
        return (n >> 8) & 0xFF, n & 0xFF

    def set_color(self, color: COLOR | int) -> None:
        self._color_wheel = color

    def set_intensity(self, intensity: float) -> None:
        intensity = min(1.0, max(0.0, intensity))
        self._dimmer, self._dimmer_fine = self._encode_float_to_bytes(intensity)

    def set_focus(self, focus: float) -> None:
        focus = min(1.0, max(0.0, focus))
        self._focus, self._focus_fine = self._encode_float_to_bytes(focus)

    def set_phi(self, phi: float) -> None:
        low_bound = -5 / 4 * math.pi
        high_bound = 5 / 4 * math.pi
        width = high_bound - low_bound

        phi = ((phi - low_bound) % width) + low_bound
        pan = self._phi_to_pan(phi)
        self._pan, self._pan_fine = self._encode_float_to_bytes(pan)

    def set_theta(self, theta: float) -> None:
        theta = min(2/3 * math.pi, max(-2/3 * math.pi, theta))
        tilt = self._theta_to_tilt(theta)
        self._tilt, self._tilt_fine = self._encode_float_to_bytes(tilt)

    def update(self, dmx: DMXUniverse):
        dmx.set_int(self.chan_no, 1, self._pan)
        dmx.set_int(self.chan_no, 2, self._pan_fine)
        dmx.set_int(self.chan_no, 3, self._tilt)
        dmx.set_int(self.chan_no, 4, self._tilt_fine)
        dmx.set_int(self.chan_no, 5, self._color_wheel)
        dmx.set_int(self.chan_no, 6, self._static_gobo)
        dmx.set_int(self.chan_no, 7, self._prism1)
        dmx.set_int(self.chan_no, 8, self._prism1_rot)
        dmx.set_int(self.chan_no, 9, self._prism2)
        dmx.set_int(self.chan_no, 10, self._prism2_rot)
        dmx.set_int(self.chan_no, 11, self._strobe)
        dmx.set_float(self.chan_no, 12, self._dimmer)
        dmx.set_float(self.chan_no, 13, self._dimmer_fine)
        dmx.set_float(self.chan_no, 14, self._focus)
        dmx.set_float(self.chan_no, 15, self._focus_fine)
        dmx.set_int(self.chan_no, 16, self._frost)
        dmx.set_float(self.chan_no, 17, self._pan_tilt_speed)
        dmx.set_int(self.chan_no, 18, self._special_function)


class VaritecColorsStarbar12(DMXDevice):
    LED_COUNT = 12
    FUNCTIONS = [int((255/64)*i)+7 for i in range(62)]

    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, num_chans=52)
        self.intensity: float = 1.0
        self.strobe: float = 0.0
        self.leds: list[tuple[int,int,int]] = [(0,0,0) for _ in range(self.LED_COUNT)]
        self.lights: list[int] = [0 for _ in range(self.LED_COUNT)]
        self._function: int = 7
        self.effect_speed: float = 0.5
        
    @property
    def function(self):
        return int(self._function / (255/64)) - 1
    
    @function.setter
    def function(self, value: int):
        self._function = int(self.FUNCTIONS[value]) if 0<=value<len(self.FUNCTIONS) else 7

    def turn_off_lights(self):
        self.lights = [0 for _ in range(self.LED_COUNT)]

    def turn_on_lights(self):
        self.lights = [255 for _ in range(self.LED_COUNT)]

    def set_leds_to_color(self, color: tuple[int, int, int]):
        self.leds = [color for _ in range(self.LED_COUNT)]

    def animate(self, dmx: DMXUniverse, t: float):
        *color, light = self._animation(t)
        self.leds = [color for _ in range(self.LED_COUNT)]
        self.lights = [light for _ in range(self.LED_COUNT)]
        self.update(dmx)
    
    def update(self, dmx: DMXUniverse):
        dmx.set_float(self.chan_no, 1, self.intensity)
        dmx.set_float(self.chan_no, 2, self.strobe)
        for i in range(self.LED_COUNT):
            dmx.set_int(self.chan_no, 3 + i*4 + 0, self.leds[i][0])
            dmx.set_int(self.chan_no, 3 + i*4 + 1, self.leds[i][1])
            dmx.set_int(self.chan_no, 3 + i*4 + 2, self.leds[i][2])
            dmx.set_int(self.chan_no, 3 + i*4 + 3, self.lights[i])
        dmx.set_int(self.chan_no, 51, self._function)
        dmx.set_float(self.chan_no, 52, self.effect_speed)


class RGBWLED(DMXDevice):
    NUM_CHANS = 4

    def __init__(self, name: str, chan_no: int):
        super().__init__(name, chan_no, self.NUM_CHANS)
        self._r = 0
        self._g = 0
        self._b = 0
        self._w = 0

    @property
    def color(self):
        return self._r, self._g, self._b, self._w

    @color.setter
    def color(self, value: tuple[int, int, int] | tuple[int, int, int, int]):
        self.r = value[0]
        self.g = value[1]
        self.b = value[2]
        if len(value) == 4:
            self.w = value[3]

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, value: int):
        self._r = value

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, value: int):
        self._g = value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value: int):
        self._b = value

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, value: int):
        self._w = value

    def animate(self, dmx: DMXUniverse, t: float):
        rgbw = self._animation(t)
        self.color = rgbw
        self.update(dmx)

    def update(self, dmx: DMXUniverse):
        dmx.set_int(self.chan_no, 1, self.r)
        dmx.set_int(self.chan_no, 2, self.g)
        dmx.set_int(self.chan_no, 3, self.b)
        dmx.set_int(self.chan_no, 4, self.w)


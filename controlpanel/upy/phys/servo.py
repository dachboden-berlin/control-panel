from machine import Pin, PWM
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
import machine
from micropython import const
import struct

_servo_pwm_freq = const(50)
_min_u10_duty = const(26 - 0)  # offset for correction
_max_u10_duty = const(123 - 0)  # offset for correction
_min_angle = const(0)
_max_angle = const(180)
_angle_conversion_factor = const((_max_u10_duty - _min_u10_duty) / (_max_angle - _min_angle))


class Servo(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pin: int,
            *,
            universe: int | None = None,
    ) -> None:
        super().__init__(_context[0], _name, update_rate_hz=0.0, universe=universe)
        self.current_angle = -0.001
        self._motor = PWM(Pin(pin))
        self._motor.freq(_servo_pwm_freq)

    def move(self, angle):
        # round to 2 decimal places, so we have a chance of reducing unwanted servo adjustments
        angle = round(angle, 2)
        # do we need to move?
        if angle == self.current_angle:
            return
        self.current_angle = angle
        # calculate the new duty cycle and move the motor
        duty_u10 = self._angle_to_u10_duty(angle)
        self._motor.duty(duty_u10)
        print(f"setting duty to {duty_u10}")

    def parse_dmx_data(self, data: bytes):
        assert len(data) == 4, f"Data is of unexpected length ({len(data)} bytes)"
        angle = struct.unpack('f', data)[0]
        self.move(angle)

    def _angle_to_u10_duty(self, angle):
        return int((angle - _min_angle) * _angle_conversion_factor) + _min_u10_duty

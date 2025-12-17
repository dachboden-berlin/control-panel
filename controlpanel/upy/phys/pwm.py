import machine
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
import struct


class PWM(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pin: int,
            *,
            universe: int | None = None,
            intensity: float = 0.5,
            freq: int = 512,
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz=0.0, universe=universe)
        self.pin = machine.Pin(pin)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(freq)
        self.pwm.duty_u16(int(intensity * (2**16 - 1)))

    def parse_dmx_data(self, data: bytes):
        assert len(data) == 2, f"Data is of unexpected length ({len(data)} bytes)"
        raw_duty = struct.unpack(">H", data)[0]
        self.pwm.duty_u16(raw_duty)

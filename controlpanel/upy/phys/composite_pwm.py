import machine
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet


class CompositePWM(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pins: list[int | None],
            *,
            # update_rate_hz: int = _DEFAULT_UPDATE_RATE_HZ,
            universe: int | None = None,
            color: tuple[int, int, int] = (50, 50, 50),
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz=0.0, universe=universe)
        self.pwms: list[machine.PWM | None] = [
            pin and machine.PWM(pin, duty_u16=self.u8_to_u16(color[i])) for i, pin in enumerate(pins)
        ]

    @staticmethod
    def u8_to_u16(u8: int) -> int:
        return (u8 << 8) | u8

    def parse_dmx_data(self, data: bytes):
        assert len(data) == 3, f"Data is of unexpected length ({len(data)} bytes)"
        for i, value in enumerate(data):
            self.pwms[i].duty_u16 = self.u8_to_u16(value)

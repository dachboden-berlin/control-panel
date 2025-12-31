import machine
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet


class DigitalPin(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pin: int,
            *,
            universe: int | None = None,
            state: bool = False,
            invert: bool = False,
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz=0.0, universe=universe)
        self._pin = machine.Pin(pin, machine.Pin.OUT)
        self._pin.value(state ^ invert)
        self._invert = invert

    def parse_dmx_data(self, data: bytes):
        assert len(data) == 1, f"Data is of unexpected length ({len(data)} bytes)"
        self._pin.value((data[0] >> 7) ^ self._invert)

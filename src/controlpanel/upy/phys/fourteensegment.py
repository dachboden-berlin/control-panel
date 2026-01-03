from machine import Pin, SoftSPI, I2C
import neopixel
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
from controlpanel.upy.c_modules import fourteensegment


class FourteenSegmentDisplay(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, SoftSPI, I2C],
            _name: str,
            pin: int,
            element_count: int,
            *,
            universe: int | None = None,
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz=0.0, universe=universe)
        self._element_count = element_count
        self._neopixels: neopixel.NeoPixel = neopixel.NeoPixel(Pin(pin, Pin.OUT), element_count * 188)

    def parse_dmx_data(self, data: bytes):
        assert len(data) == self._element_count*64, f"Data is of unexpected length ({len(data)} bytes)"
        fourteensegment.get_pixel_buffer(self._neopixels.buf, data)
        self._neopixels.write()

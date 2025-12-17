from .fixture import Fixture
from controlpanel.upy.libs.seven_segment import SevenSegment
from controlpanel.upy.artnet import ArtNet
from machine import SoftSPI, I2C
from micropython import const


_DEFAULT_UPDATE_RATE_HZ = const(1.0)


class SevenSegmentDisplay(Fixture):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 pin_chip_select: int,
                 digit_count: int,
                 *,
                 update_rate_hz: float = _DEFAULT_UPDATE_RATE_HZ,
                 universe: int | None = None
                 ) -> None:
        Fixture.__init__(self, _context[0], _name, update_rate_hz, universe=universe)
        self._display = SevenSegment(_context[1], digit_count, cs=pin_chip_select, reverse=True)

    def parse_dmx_data(self, data: bytes) -> None:
        brightness: int = data[0]
        self._display.text(data[1:].decode("ascii"))
        self._display.brightness(brightness)

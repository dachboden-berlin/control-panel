from machine import Pin, SoftSPI, I2C
from .sensor import Sensor
from .fixture import Fixture
from controlpanel.upy.artnet import ArtNet
from time import sleep_us
from micropython import const


_DEFAULT_POLLING_RATE_HZ = const(10.0)  # for PISO
_DEFAULT_UPDATE_RATE_HZ = const(2.0)  # for SIPO


class PisoShiftRegister(Sensor):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 latch: int,
                 count: int = 1,
                 *,
                 polling_rate_hz: float = _DEFAULT_POLLING_RATE_HZ,
                 ) -> None:
        super().__init__(_context[0], _name, polling_rate_hz)
        self._spi: SoftSPI = _context[1]
        self._latch_pin: Pin = Pin(latch, Pin.OUT)
        self._count = count
        self._buffers = [bytearray(self._count), bytearray(self._count)]  # Two alternating buffers
        self._active_index = 0

    def _read_states(self):
        buf = self._buffers[self._active_index]
        prev_buf = self._buffers[1 - self._active_index]

        # Latch inputs
        self._latch_pin.off()
        sleep_us(2)
        self._latch_pin.on()

        # Read new states into current buffer
        self._spi.readinto(buf, 0x42)

        # Compare with previous
        if buf != prev_buf:
            self._send_trigger_packet(buf)

        # Swap buffers (no copy, no new alloc)
        self._active_index = 1 - self._active_index



    async def update(self) -> None:
        self._read_states()


class SipoShiftRegister(Fixture):
    def __init__(
            self,
            _context: tuple[ArtNet, SoftSPI, I2C],
            _name: str,
            latch: int,
            count: int = 1,
            *,
            update_rate_hz: float = _DEFAULT_UPDATE_RATE_HZ,
            universe: int | None = None,
        ) -> None:
        super().__init__(_context[0], _name, update_rate_hz, universe=universe)
        self._spi: SoftSPI = _context[1]
        self._latch_pin: Pin = Pin(latch, Pin.OUT)
        self._number_of_bits = count * 8

    def _write_states(self, data: bytes) -> None:
        raise NotImplementedError  # TODO: Restore functionality!

    def parse_dmx_data(self, data: bytes):
        assert len(data) == self._number_of_bits
        self._write_states(data)

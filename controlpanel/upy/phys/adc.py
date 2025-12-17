import machine
from .sensor import Sensor
from controlpanel.upy.artnet import ArtNet
from controlpanel.shared.compatibility import Literal
import struct
from micropython import const


_DEFAULT_POLLING_RATE_HZ = const(2.0)


class ADC(Sensor):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            pin: int,
            *,
            polling_rate_hz: float = _DEFAULT_POLLING_RATE_HZ,
            attenuation: Literal[0, 1, 2, 3] = machine.ADC.ATTN_11DB,
    ) -> None:
        super().__init__(_context[0], _name, polling_rate_hz)
        self.adc = machine.ADC(machine.Pin(pin))
        self.adc.atten(attenuation)

    async def update(self) -> None:
        value = self.adc.read_u16()
        self._send_trigger_packet(struct.pack(">H", value))

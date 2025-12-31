import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .esp32 import ESP32
import struct


class PWM(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 *,
                 duty: float = 1.0,
                 universe: int | None = None,
                 ) -> None:
        super().__init__(_artnet, _loop, _esp, _name, universe=universe)
        self._duty: float = duty
        self._raw_duty: int = 0

    def send_dmx(self) -> None:
        self._send_dmx_packet(struct.pack(">H", self._raw_duty))

    @property
    def duty(self) -> float:
        return self._duty

    @duty.setter
    def duty(self, duty: float) -> None:
        self.set_duty(duty)

    @property
    def raw_duty(self) -> int:
        return self._raw_duty

    @raw_duty.setter
    def raw_duty(self, raw_duty: int) -> None:
        self._raw_duty = raw_duty
        self._duty = raw_duty / (2 ** 16 - 1)
        self.send_dmx()

    def set_duty(self, duty: float) -> None:
        duty = min(max(duty, 0.0), 1.0)
        self._duty = duty
        self._raw_duty = int(duty * (2 ** 16 - 1))
        self.send_dmx()

    def blackout(self) -> None:
        self.set_duty(0.0)

    def whiteout(self) -> None:
        self.set_duty(1.0)

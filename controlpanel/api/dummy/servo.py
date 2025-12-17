import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .esp32 import ESP32
import struct


class Servo(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 *,
                 universe: int | None = None,
                 ) -> None:
        super().__init__(_artnet, _loop, _esp, _name, universe=universe)
        self._current_angle: float = 0.001

    def move(self, angle: float) -> None:
        self._current_angle = angle
        self.send_dmx()

    def send_dmx(self) -> None:
        self._send_dmx_packet(struct.pack('f', self._current_angle))

    def blackout(self) -> None:
        pass

    def whiteout(self) -> None:
        pass

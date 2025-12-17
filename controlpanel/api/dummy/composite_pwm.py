import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .esp32 import ESP32


class CompositePWM(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 *,
                 color: tuple[int, int, int] = (50, 50, 50),
                 universe: int | None = None,
                 ) -> None:
        super().__init__(_artnet, _loop, _esp, _name, universe=universe)
        self._color = color

    def send_dmx(self) -> None:
        self._send_dmx_packet(bytes(self._color))

    @property
    def color(self) -> tuple[int, int, int]:
        return self._color

    @color.setter
    def color(self, color: tuple[int, int, int]) -> None:
        self._color = color
        self.send_dmx()

    def blackout(self) -> None:
        self.color = (0, 0, 0)

    def whiteout(self) -> None:
        self.color = (255, 255, 255)

import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .node import Node


class CompositePWM(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _node: Node,
                 _name: str,
                 /,
                 *,
                 color: tuple[int, int, int] = (50, 50, 50),
                 universe: int | None = None,
                 ) -> None:
        super().__init__(_artnet, _loop, _node, _name, universe=universe)
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

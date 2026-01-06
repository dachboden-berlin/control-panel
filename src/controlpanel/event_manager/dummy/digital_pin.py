import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .node import Node


class DigitalPin(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _node: Node,
                 _name: str,
                 /,
                 *,
                 universe: int | None = None,
                 invert: bool = False,
                 ) -> None:
        super().__init__(_artnet, _loop, _node, _name, universe=universe)
        self._state: bool = False

    def send_dmx(self) -> None:
        self._send_dmx_packet(b"\xff" if self._state else b"\x00")

    def turn_on(self) -> None:
        self.state = True

    def turn_off(self) -> None:
        self.state = False

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        if state == self._state:
            return
        self._state = state
        self.send_dmx()

    def toggle(self) -> None:
        self.state = not self.state

    def blackout(self) -> None:
        self.state = False

    def whiteout(self) -> None:
        self.state = True

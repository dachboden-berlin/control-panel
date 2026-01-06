import asyncio
from .fixture import Fixture
from artnet import ArtNet
from .node import Node


class SevenSegmentDisplay(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _node: Node,
                 _name: str,
                 /,
                 digit_count: int,
                 *,
                 universe: int | None = None):
        super().__init__(_artnet, _loop, _node, _name, universe=universe)
        self._text: str = ""
        self._digit_count = digit_count
        self._brightness: int = 7

    def display_text(self, text: str) -> None:
        self._text = text[:self._digit_count]
        self._send_dmx_packet(self._brightness.to_bytes() + self._text.encode('ASCII'))

    def set_brightness(self, brightness: float = 0.5) -> None:
        brightness = max(0.0, min(1.0, brightness))
        self._brightness = int(brightness * 15)
        self._send_dmx_packet(self._brightness.to_bytes() + self._text.encode('ASCII'))

    def whiteout(self) -> None:
        brightness: int = 15
        text: str = ("8" * self._digit_count)
        self._send_dmx_packet(brightness.to_bytes() + text.encode('ASCII'))

    def blackout(self) -> None:
        text: str = ""
        self._send_dmx_packet(self._brightness.to_bytes() + text.encode('ASCII'))

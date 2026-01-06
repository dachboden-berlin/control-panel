import asyncio
from abc import abstractmethod
from .node import Node
from controlpanel.shared.base import BaseFixture


_PACKET_RETRY_COUNT = 2 # number of "retries" (duplicate sends) of packets
_PACKET_RETRY_PAUSE_MS = 500  # time in milliseconds between "retries"


class Fixture(BaseFixture):
    def __init__(self, _artnet, _loop, _node, _name: str, /, universe: int | None) -> None:
        super().__init__(_artnet, _name, universe=universe)
        self._loop: asyncio.AbstractEventLoop = _loop
        self._current_task: asyncio.Future | None = None
        self._node: Node = _node
        self._deafened: bool = False

    @property
    def deafened(self) -> bool:
        return self._deafened

    def _send_dmx_packet(self, data: bytes | bytearray) -> None:
        if self._deafened:
            return

        self._increment_seq()

        self._artnet.send_dmx(self.universe, self._seq, data, ip_override=self._node.ip)
        
        if not _PACKET_RETRY_COUNT:
            return
        
        # Start a new packet send task
        self._current_task = asyncio.run_coroutine_threadsafe(
            self._send_packets(self._seq, data),
            self._loop
        )

    async def _send_packets(self, seq: int, data: bytes | bytearray) -> None:
        for _ in range(_PACKET_RETRY_COUNT):
            await asyncio.sleep(_PACKET_RETRY_PAUSE_MS/1000)
            if (seq != self._seq) and self.should_ignore_seq(seq):  # don't bother sending outdated packets
                return
            self._artnet.send_dmx(self.universe, seq, data, ip_override=self._node.ip)

    @abstractmethod
    def send_dmx(self) -> None:
        pass

    @abstractmethod
    def blackout(self) -> None:
        pass

    @abstractmethod
    def whiteout(self) -> None:
        pass

import asyncio
from abc import abstractmethod
from controlpanel.api.dummy.esp32 import ESP32
from controlpanel.shared.base import BaseFixture


class Fixture(BaseFixture):
    def __init__(self, _artnet, _loop, _esp, _name: str, /, universe: int | None) -> None:
        super().__init__(_artnet, _name, universe=universe)
        self._loop: asyncio.AbstractEventLoop = _loop
        self._current_task: asyncio.Future | None = None
        self._esp: ESP32 = _esp
        self._deafened: bool = False

    @property
    def deafened(self) -> bool:
        return self._deafened

    def _send_dmx_packet(self, data: bytes | bytearray) -> None:
        if self._deafened:
            return

        self._increment_seq()

        # Cancel any ongoing packet send task
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        # Start a new packet send task
        self._current_task = asyncio.run_coroutine_threadsafe(
            self._send_packets(self._seq, data),
            self._loop
        )

    async def _send_packets(self, seq: int, data: bytes | bytearray) -> None:
        for _ in range(3):
            self._artnet.send_dmx(self.universe, seq, data, ip_override=self._esp.ip)
            await asyncio.sleep(0.5)

    @abstractmethod
    def send_dmx(self) -> None:
        pass

    @abstractmethod
    def blackout(self) -> None:
        pass

    @abstractmethod
    def whiteout(self) -> None:
        pass

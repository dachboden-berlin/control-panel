import asyncio
from controlpanel.shared.base import BaseSensor
from controlpanel.shared.compatibility import abstractmethod
from controlpanel.upy.artnet import ArtNet


class Sensor(BaseSensor):
    def __init__(self, _artnet: ArtNet, _name: str, polling_rate_hz: float = 1.0):
        super().__init__(_artnet, _name)
        self.update_rate_ms: int = int(1000 / polling_rate_hz) if polling_rate_hz > 0.0 else 0
        self._current_task: asyncio.Task | None = None

    @abstractmethod
    async def update(self) -> None:
        pass

    def _send_trigger_packet(self, payload: bytes | bytearray) -> None:
        data: bytes = self.name.encode('ascii') + b'\x00' + payload

        self._increment_seq()

        self._artnet.send_trigger(76, self._seq, data)

        # Cancel any ongoing packet send task
        current_task = asyncio.current_task()
        if self._current_task is not None and self._current_task != current_task:
            self._current_task.cancel()

        # Start a new packet send task
        self._current_task = asyncio.create_task(
            self._send_packets(self._seq, data)
        )

    async def _send_packets(self, seq: int, data: bytes | bytearray) -> None:
        for _ in range(3):
            await asyncio.sleep(0.5)
            self._artnet.send_trigger(key=76, subkey=seq, data=data)

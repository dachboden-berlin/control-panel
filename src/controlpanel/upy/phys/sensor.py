import asyncio
from controlpanel.shared.base import BaseSensor
from controlpanel.shared.compatibility import abstractmethod
from controlpanel.upy.artnet import ArtNet
from micropython import const


_CONTROL_PANEL_KEY = const(76)
_PACKET_RETRY_COUNT = const(2) # number of "retries" (duplicate sends) of packets
_PACKET_RETRY_PAUSE_MS = const(500)  # time in milliseconds between "retries"


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

        self._artnet.send_trigger(_CONTROL_PANEL_KEY, self._seq, data)
        
        if not _PACKET_RETRY_COUNT:
            return

        # Start a new packet send task
        self._current_task = asyncio.create_task(
            self._send_retry_packets(self._seq, data)
        )

    async def _send_retry_packets(self, seq: int, data: bytes | bytearray) -> None:
        for _ in range(_PACKET_RETRY_COUNT):
            await asyncio.sleep_ms(_PACKET_RETRY_PAUSE_MS)
            if (seq != self._seq) and self.should_ignore_seq(seq):  # don't bother sending outdated packets
                return
            self._artnet.send_trigger(key=_CONTROL_PANEL_KEY, subkey=seq, data=data)

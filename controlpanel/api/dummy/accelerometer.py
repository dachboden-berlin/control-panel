from artnet import ArtNet
from .sensor import Sensor
import struct


class Accelerometer(Sensor):
    EVENT_TYPES = {
        "ValueRead": float,
    }

    def __init__(
            self,
            _artnet: ArtNet,
            _name: str,
    ) -> None:
        super().__init__(_artnet, _name)
        self._gyro: tuple[float | None, float | None, float | None] = (None, None, None)
        self._real_gyro: tuple[float | None, float | None, float | None] = (None, None, None)

    @property
    def desynced(self) -> bool:
        return self._gyro != self._real_gyro

    @property
    def gyro(self) -> tuple[float, float, float]:
        return self._gyro

    @gyro.setter
    def gyro(self, value: tuple[float, float, float]) -> None:
        if self._gyro == value:
            return
        self._gyro = value
        self._fire_event("GyroRead", value)

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        assert len(data) == 6, f"Data is of unexpected length ({len(data)} bytes)"
        self._gyro = self._real_gyro = struct.unpack('<3e', data)
        self._fire_event("GyroRead", self._gyro)

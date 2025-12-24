from .adc import ADC
from artnet import ArtNet
from collections import deque
import struct


class HallSensor(ADC):
    def __init__(
            self,
            _artnet: ArtNet,
            _name: str,
            bounds: tuple[float, float],
            rolling_average_size: int,
    ) -> None:
        super().__init__(_artnet, _name)
        self._rolling_average_deque = deque(maxlen=rolling_average_size)
        self._normalized_value: float = 0.0
        self._bounds = bounds

    @property
    def normalized_value(self) -> float:
        return self._normalized_value

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        assert len(data) == 2, f"Data is of unexpected length ({len(data)} bytes)"
        real_raw_value = struct.unpack(">H", data)[0]
        self._value = self._real_value = real_raw_value/(2**16-1)
        self._raw_value = self._real_raw_value = real_raw_value

        self._rolling_average_deque.append(self._value)
        average_value = sum(self._rolling_average_deque) / len(self._rolling_average_deque)
        normalized_value = (average_value -self._bounds[0]) / (self._bounds[1]-self._bounds[0])
        self._normalized_value = min(1.0, max(0.0, normalized_value))
        self._fire_event("ValueRead", self._normalized_value)





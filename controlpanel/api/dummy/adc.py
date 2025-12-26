from artnet import ArtNet
from .sensor import Sensor
import struct
from collections import deque


class ADC(Sensor):
    EVENT_TYPES = {
        "ValueRead": float,
    }

    def __init__(
            self,
            _artnet: ArtNet,
            _name: str,
            map_range: tuple[float, float] | None = None,  # normalize incoming values to a range a..b
            clamp: bool = True,
            rolling_average_size: int | None = None,
    ) -> None:
        super().__init__(_artnet, _name)
        self._value: float = 0.0
        self._real_value: float | None = None
        self._raw_value: int = 0
        self._real_raw_value: int | None = None

        self.map_range: tuple[float, float] | None = map_range
        self._clamp: bool = clamp
        self._rolling_average_deque: deque[float] | None = deque(maxlen=rolling_average_size) if (rolling_average_size and rolling_average_size > 1) else None

    @property
    def desynced(self) -> bool:
        return self._value != self._real_value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        value = min(1.0, max(0.0, value))
        self._value = value
        self._raw_value = int(value * (2 ** 16 - 1))
        self._fire_event("ValueRead", value)

    @property
    def raw_value(self) -> int:
        return self._raw_value

    @raw_value.setter
    def raw_value(self, value: int) -> None:
        assert 0 <= value < 2 ** 16, f"{value} is outside the range of u16 integer"
        self._raw_value = value
        self._value = value/(2**16-1)
        self._fire_event("ValueRead", self._value)

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        assert len(data) == 2, f"Data is of unexpected length ({len(data)} bytes)"
        real_raw_value = struct.unpack(">H", data)[0]
        self._raw_value = self._real_raw_value = real_raw_value

        decoded = real_raw_value/(2**16-1)  # range 0..1

        if self.map_range is not None:
            mapped = (decoded - self.map_range[0]) / (self.map_range[1]-self.map_range[0])
            if self._clamp:
                mapped = max(0.0, min(1.0, mapped))
        else:
            mapped = decoded

        if self._rolling_average_deque is not None:
            self._rolling_average_deque.append(mapped)
            average = sum(self._rolling_average_deque) / len(self._rolling_average_deque)
        else:
            average = mapped

        self._value = self._real_value = average
        self._fire_event("ValueRead", self._value)

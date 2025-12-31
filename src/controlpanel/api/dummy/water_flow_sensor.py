import struct
from .sensor import Sensor
from artnet import ArtNet


class WaterFlowSensor(Sensor):
    EVENT_TYPES = {
        "WaterFlow": int,
        "WaterFlowPerSecond": float,
    }

    def __init__(
            self,
            _artnet: ArtNet,
            _name: str,
            /,
            polling_rate_hz: float,
        ) -> None:
        super().__init__(_artnet, _name)
        self._polling_rate_hz = polling_rate_hz
        self._lifetime_water_flow: int = 0
        self._last_flow_time: float = 0.0

    @property
    def desynced(self) -> False:
        return False

    def flow(self, amount: int) -> None:
        self._fire_event("WaterFlow", amount)
        self._lifetime_water_flow += amount

    @property
    def lifetime_water_flow(self) -> int:
        return self._lifetime_water_flow

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        water_flow: int = struct.unpack("<I", data)[0]
        self._lifetime_water_flow += water_flow
        self._fire_event("WaterFlow", water_flow)
        self._fire_event("WaterFlowPerSecond", water_flow / (timestamp - self._last_flow_time))
        self._last_flow_time = timestamp

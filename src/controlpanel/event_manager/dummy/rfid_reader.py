from .sensor import Sensor
import time


class RFIDReader(Sensor):
    EVENT_TYPES = {
        "TagScanned": bytes,
        "TagRemoved": bytes,
    }

    def __init__(self, _artnet, _name: str, /, *, forget_time: float | None = None):
        super().__init__(_artnet, _name)
        self._current_uid: bytes | None = None
        self._real_current_uid: bytes | None = None
        self._last_update_time: float = 0.0
        self._forget_time: float | None = forget_time

    @property
    def desynced(self):
        return self._current_uid != self._real_current_uid

    @property
    def current_uid(self) -> bytes | None:
        return self._current_uid

    def scan_uid(self, uid: bytes | None, *, timestamp: float | None = None) -> None:
        if timestamp is None:
            timestamp = time.time()
        if self._current_uid == uid and (self._forget_time is None or timestamp - self._last_update_time < self._forget_time):
            return
        self._last_update_time = timestamp
        previous_uid = self._current_uid
        self._current_uid = uid
        if previous_uid:
            self._fire_event("TagRemoved", previous_uid)
        if uid:
            self._fire_event("TagScanned", uid)

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        new_uid = data if data else None
        self._real_current_uid = data
        self.scan_uid(new_uid, timestamp=timestamp)

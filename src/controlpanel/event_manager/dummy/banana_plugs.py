from controlpanel.shared.base.banana_plugs import NO_CONNECTION
from .sensor import Sensor
from typing import Iterable


class BananaPlugs(Sensor):
    EVENT_TYPES = {
        "PlugDisconnected": tuple[int, int],
        "PlugConnected": tuple[int, int],
        "ConnectionsChanged": tuple[int | None, ...]
    }

    def __init__(
            self,
            _artnet,
            _name: str,
            /,
            plug_pins: Iterable[int],
    ) -> None:
        super().__init__(_artnet, _name)
        self._connections: list[int | None] = [None for _ in plug_pins]
        self._real_connections: list[int | None] = [None for _ in plug_pins]

    @property
    def desynced(self):
        return self._connections != self._real_connections

    @property
    def connections(self) -> tuple[int | None, ...]:
        return tuple(self._connections)

    def connect(self, plug_idx: int, socket_idx: int | None) -> None:
        if self._connections[plug_idx] == socket_idx:
            return
        for p, s in enumerate(self._connections):
            if s == socket_idx and s is not None:
                self._connections[p] = None
                print(f"Disconnecting plug {p} that was in socket {s}")
                self._fire_event("PlugDisconnected", (p, s))
                break

        old_socket_idx = self._connections[plug_idx]
        if old_socket_idx is not None:
            self._fire_event("PlugDisconnected", (plug_idx, old_socket_idx))

        self._connections[plug_idx] = socket_idx

        if socket_idx is not None:
            self._fire_event("PlugConnected", (plug_idx, socket_idx))

        self._fire_event("ConnectionsChanged", tuple(self._connections))

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        assert len(data) == 2, "Data is of unexpected length"
        plug_idx, socket_idx = data
        self._real_connections[plug_idx] = socket_idx if socket_idx != NO_CONNECTION else None
        self.connect(plug_idx, socket_idx)

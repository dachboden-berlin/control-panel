from controlpanel.shared.base import BaseSensor
from typing import Hashable
from abc import abstractmethod
from controlpanel import api
from artnet import ArtNet


class Sensor(BaseSensor):
    EVENT_TYPES: dict[str, Hashable] = dict()

    def __init__(self, _artnet: ArtNet, name: str, **kwargs):
        super().__init__(_artnet, name)
        self._muted: bool = False

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    @abstractmethod
    def desynced(self) -> bool:
        pass

    def _fire_event(self, action_name: str, value: Hashable) -> None:
        api.fire_event(self._name, action_name, value)

    @abstractmethod
    def parse_trigger_payload(self, payload: bytes, timestamp: float) -> None:
        pass

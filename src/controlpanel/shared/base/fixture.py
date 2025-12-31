from .device import Device
from controlpanel.shared.compatibility import abstractmethod


class BaseFixture(Device):
    def __init__(self, _artnet, _name: str, *, universe: int | None) -> None:
        super().__init__(_artnet, _name)
        self._universe = self._universe_from_string(_name) if universe is None else universe

    @property
    def universe(self) -> int:
        return self._universe

    @staticmethod
    def _universe_from_string(string: str) -> int:
        import hashlib
        hash_object = hashlib.sha1(string.encode())
        return int.from_bytes(hash_object.digest(), "big") & 0x7FFF  # max 32767 universes (15bit)

    @abstractmethod
    async def update(self) -> None:
        pass

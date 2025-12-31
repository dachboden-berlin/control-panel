from controlpanel.shared.base import Device, BaseFixture
from controlpanel.shared.compatibility import abstractmethod
from controlpanel.upy.artnet import ArtNet


class Fixture(BaseFixture):
    def __init__(self, _artnet: ArtNet, _name: str, update_rate_hz, *, universe: int | None) -> None:
        super().__init__(_artnet, _name, universe=universe)
        self.update_rate_ms: int = int(1000 / update_rate_hz) if update_rate_hz > 0.0 else 0

    @abstractmethod
    async def update(self) -> None:
        pass

    @abstractmethod
    def parse_dmx_data(self: Device, data: bytes) -> None:
        """Decode and apply DMX data"""
        pass

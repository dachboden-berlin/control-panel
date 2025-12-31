from .device import Device
from controlpanel.shared.compatibility import ArtNet


class BaseSensor(Device):
    def __init__(self, _artnet: ArtNet, name: str):
        super().__init__(_artnet, name)

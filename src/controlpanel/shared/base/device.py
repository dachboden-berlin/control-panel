try:
    from artnet import ArtNet
except ImportError:
    from controlpanel.upy.artnet import ArtNet


class Device:

    def __init__(self, _artnet: ArtNet, name: str):
        self._artnet: ArtNet = _artnet
        self._name: str = name
        self._seq: int = 1

    def _increment_seq(self) -> None:
        self._seq = self._seq % 255 + 1

    def _decrement_seq(self) -> None:
        self._seq = (self._seq - 2) % 255 + 1

    def should_ignore_seq(self, seq: int) -> bool:
        """Returns whether the given sequence integer should be considered as outdated. Seq 0 is never ignored."""
        if seq == 0 or self._seq == 0:
            return False  # never ignore seq=0
        return seq <= self._seq and not (seq < 16 and self._seq > 255-16)

    @property
    def name(self) -> str:
        return self._name

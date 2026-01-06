from artnet import ArtNet
from .sensor import Sensor


class Button(Sensor):
    EVENT_TYPES = {
        "ButtonPressed": bool,
        "ButtonReleased": bool,
    }

    def __init__(self, _artnet: ArtNet, _name: str) -> None:
        super().__init__(_artnet, _name)
        self._state: bool = False
        self._real_state: bool | None = None

    def __bool__(self) -> bool:
        return self._state

    def press(self) -> None:
        if self._state:
            return
        self._state = True
        self._fire_event("ButtonPressed", True)

    def release(self) -> None:
        if not self._state:
            return
        self._state = False
        self._fire_event("ButtonReleased", False)

    @property
    def desynced(self) -> bool:
        return self._state != self._real_state

    @property
    def pressed(self) -> bool:
        return self._state

    @pressed.setter
    def pressed(self, value: bool) -> None:
        if value:
            self.press()
        else:
            self.release()

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        assert len(data) == 1, "Data is of unexpected length"
        is_pressed: bool = bool(data[0])
        self._real_state = is_pressed
        if is_pressed:
            self.press()
        else:
            self.release()

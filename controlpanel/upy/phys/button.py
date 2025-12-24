from machine import Pin, SoftSPI, I2C
from .sensor import Sensor
from micropython import const
from time import ticks_ms, ticks_diff
from controlpanel.upy.artnet import ArtNet


_DEFAULT_SOFTWARE_DEBOUNCE: int = const(20)
_DEFAULT_POLLING_RATE_HZ: float = const(0.0)


class Button(Sensor):
    def __init__(
            self,
            _context: tuple[ArtNet, SoftSPI, I2C],
            _name: str,
            pin: int,
            *,
            invert: bool = False,
            polling_rate_hz: float = _DEFAULT_POLLING_RATE_HZ,
            software_debounce_ms: int | None = _DEFAULT_SOFTWARE_DEBOUNCE,
    ) -> None:
        super().__init__(_context[0], _name, polling_rate_hz=polling_rate_hz)
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_interrupt)
        self._invert = invert
        self._previous_state: bool = self.get_pressed()
        self._software_debounce_ms = software_debounce_ms
        if software_debounce_ms:
            self._last_press_time: int = 0
            self._last_release_time: int = 0

    def _handle_interrupt(self, pin: Pin) -> None:
        current_time = ticks_ms()
        value = pin.value() ^ self._invert
        if not self._software_debounce_ms:
            pass
        elif value == 1 and ticks_diff(current_time, self._last_release_time) > self._software_debounce_ms:
            self._last_release_time = current_time
        elif value == 0 and ticks_diff(current_time, self._last_press_time) > self._software_debounce_ms:
            self._last_press_time = current_time
        else:
            return
        self._previous_state = value
        self._send_trigger_packet(value.to_bytes(1, "big"))

    def get_pressed(self) -> bool:
        return self.pin.value() ^ self._invert

    async def update(self) -> None:
        state = self.get_pressed()
        if state != self._previous_state:
            self._previous_state = state
            self._send_trigger_packet(state.to_bytes(1, "big"))

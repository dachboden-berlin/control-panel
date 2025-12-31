from machine import Pin, SoftSPI, I2C
import time
from .sensor import Sensor
from micropython import const
from controlpanel.upy.artnet import ArtNet
try:
    from typing import Callable
except ImportError:
    Callable = object()


_DEFAULT_DEBOUNCE: int = const(50)


class RotaryDial(Sensor):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 pin_counter: int,
                 pin_reset: int,
                 *,
                 software_debounce_ms: int | None = _DEFAULT_DEBOUNCE,
                 ) -> None:
        super().__init__(_context[0], _name)
        self._count: int = 0
        self._counter_switch = _Switch(pin_counter,
                                       trigger=self._increment_counter,
                                       software_debounce_ms=software_debounce_ms or 0
                                       )
        self._reset_switch = _Switch(pin_reset,
                                     trigger=self._confirm_count,
                                     software_debounce_ms=software_debounce_ms or 0
                                     )

    def _confirm_count(self) -> None:
        if self._count == 0:
            return
        self._count %= 10
        self._send_trigger_packet(self._count.to_bytes(1, "big"))
        self._count = 0

    def _increment_counter(self) -> None:
        self._count = (self._count + 1) % 255

    async def update(self) -> None:
        pass


class _Switch:
    def __init__(self, gpio: int, trigger: Callable[[], None], software_debounce_ms: int) -> None:
        self._trigger: Callable[[], None] = trigger
        self._last_interrupt_time_ms: int = 0
        self._debounce_ms: int = software_debounce_ms
        self._pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_FALLING, handler=self._interrupt_handler)

    def _interrupt_handler(self, pin: Pin) -> None:
        current_time: int = time.ticks_ms()
        if time.ticks_diff(current_time, self._last_interrupt_time_ms) > self._debounce_ms:
            self._trigger()
            self._last_interrupt_time_ms = current_time

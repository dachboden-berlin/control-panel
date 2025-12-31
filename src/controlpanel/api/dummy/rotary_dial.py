from artnet import ArtNet
from .sensor import Sensor
from controlpanel import api
from typing import Literal
import time
import asyncio


DigitType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 0]


class RotaryDial(Sensor):
    EVENT_TYPES = {
        "DigitEntered": Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
        "SequenceEntered": tuple[int, ...],
    }

    def __init__(self, _artnet: ArtNet, _name: str, /, *, confirmation_time_seconds: float = 3.0, max_digits: int = 8):
        super().__init__(_artnet, _name)
        self._last_digit: DigitType | None = None
        self._last_digit_time: float = 0.0
        self._confirmation_time_seconds: float = confirmation_time_seconds
        self._max_digits: int = max_digits
        self._entered_sequence: list[DigitType] = []
        api.subscribe(self._wait_for_confirmation, self._name, "DigitEntered", None, allow_parallelism=True)

    @property
    def desynced(self) -> bool:
        return False

    @property
    def entered_sequence(self) -> tuple[int, ...]:
        return tuple(self._entered_sequence)

    def enter_digit(self, digit: DigitType, *, timestamp: float | None = None) -> None:
        if timestamp is None:
            timestamp = time.time()
        self._last_digit = digit
        self._entered_sequence.append(digit)
        self._last_digit_time = timestamp
        self._fire_event("DigitEntered", digit)
        if len(self._entered_sequence) >= self._max_digits:
            self._confirm_sequence()

    def parse_trigger_payload(self, data: bytes, timestamp: float) -> None:
        digit: DigitType = (data[0]) % 10  # type: ignore
        self.enter_digit(digit)

    def _confirm_sequence(self) -> None:
        self._fire_event("SequenceEntered", tuple(self._entered_sequence))
        self._entered_sequence.clear()

    async def _wait_for_confirmation(self):
        if not self._entered_sequence:
            return
        await asyncio.sleep(self._confirmation_time_seconds)
        if time.time() - self._last_digit_time < self._confirmation_time_seconds:
            return
        self._confirm_sequence()

    def get_last_entered_digit(self) -> int | None:
        return self._last_digit

from dataclasses import dataclass
from typing import Callable, Optional, Coroutine, Any
import asyncio
import pygame as pg
from collections.abc import Hashable
from typing import Generic, TypeVar, TypedDict, Required, NotRequired

# Atomic numbers: iron = 26, oxygen = 8
# Iron(II) oxide (FeO): 32 protons
# Iron(III) oxide (Fe22O3): 76 protons
KEY_CONTROL_PANEL_PROTOCOL = 76
CONTROL_PANEL_EVENT = pg.event.custom_type()


EventSourceType = str
EventActionType = str
EventValueType = Hashable | None


T = TypeVar("T")


@dataclass(frozen=True)
class Event(Generic[T]):
    source: EventSourceType
    action: EventActionType
    value: T
    sender: tuple[str, int] | None
    timestamp: float


@dataclass(frozen=True)
class Condition:
    source: EventSourceType
    action: EventActionType
    value: EventValueType


CallbackType = (Callable[[Event], Coroutine[Any, Any, None]] |
                Callable[[Event], None] |
                Callable[[], Coroutine[Any, Any, None]] |
                Callable[[], None]
                )


@dataclass
class Subscriber:
    callback: CallbackType
    fire_once: bool
    allow_parallelism: bool
    requires_event_arg: bool
    task: Optional[asyncio.Task] = None


class SPIConfig(TypedDict):
    clock: Required[int]
    miso: NotRequired[int]
    mosi: NotRequired[int]


class I2CConfig(TypedDict, total=True):
    scl: int
    sda: int


class NodeConfig(TypedDict):
    SPI: SPIConfig
    I2C: I2CConfig
    devices: dict[str, tuple[str, dict[str, float | int | str], dict[str, float | int | str]]]

from .commons import (
    KEY_CONTROL_PANEL_PROTOCOL,
    CONTROL_PANEL_EVENT,
    Event,
    EventSourceType,
    EventActionType,
    EventValueType,
    Condition,
    CallbackType,
    Subscriber,
    )
from typing import Literal, TYPE_CHECKING, Callable, TypeVar
from .services import services
from .load_scripts import load_scripts
from .api import call_with_frequency, fire_event, subscribe, send_dmx
from controlpanel.game_manager.sound import play_sound
from .callback import callback
from .get_device import get_device
from .event_manager import EventManager
from . import logger



if TYPE_CHECKING:
    from artnet import ArtNet
    from controlpanel.game_manager import GameManager, BaseGame
    from controlpanel.dmx import DMXUniverse
    from types import ModuleType
    artnet: ArtNet
    event_manager: EventManager
    game_manager: GameManager
    dmx: DMXUniverse
    loaded_scripts: dict[str, ModuleType]
    T = TypeVar("T", bound=BaseGame)
    add_game: Callable[[T, bool], T]
    get_game: Callable[[str | None], BaseGame | None]


def __getattr__(name: Literal["artnet", "event_manager", "game_manager", "dmx"]):
    if name == "artnet":
        return services.artnet
    elif name == "event_manager":
        return services.event_manager
    elif name == "game_manager":
        return services.game_manager
    elif name == "dmx":
        return services.dmx
    elif name == "loaded_scripts":
        return services.loaded_scripts
    elif name == "add_game":
        return services.game_manager.add_game
    elif name == "get_game":
        return services.game_manager.get_game
    raise AttributeError(f"cannot import attribute '{name}' from '{__package__}'")

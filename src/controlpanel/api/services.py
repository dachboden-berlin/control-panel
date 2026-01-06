from typing import TYPE_CHECKING, Optional
from controlpanel.dmx import DMXUniverse
from artnet import ArtNet
from controlpanel.event_manager.event_manager import EventManager
if TYPE_CHECKING:
    from controlpanel.game_manager import GameManager


class Services:
    """Hacky workaround to allow global access to these singletons"""
    def __init__(self):
        self.artnet: Optional[ArtNet] = None
        self.event_manager: Optional[EventManager] = None
        self.game_manager: Optional["GameManager"] = None
        self.dmx: Optional[DMXUniverse] = None


services = Services()

from os import environ as _environ
_environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from controlpanel.game_manager.games import BaseGame
from anaconsole import console_command, Autocomplete

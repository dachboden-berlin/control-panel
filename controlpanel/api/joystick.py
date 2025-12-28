from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pygame

class Joystick:
    def __init__(self, pygame_joystick: "pygame.joystick.Joystick"):
        self._joystick = pygame_joystick
    
    def get_name(self) -> str:
        return self._joystick.get_name()
    
    def get_numaxes(self) -> int:
        return self._joystick.get_numaxes()
    
    def get_axis(self, axis: int) -> float:
        return self._joystick.get_axis(axis)
    
    def get_numbuttons(self) -> int:
        return self._joystick.get_numbuttons()
    
    def get_button(self, button: int) -> bool:
        return bool(self._joystick.get_button(button))
    
    def get_instance_id(self) -> int:
        return self._joystick.get_instance_id()

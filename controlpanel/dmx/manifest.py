"""
This module contains a list of all DMX devices that are PHYSICALLY connected to the USB to DMX adapter.
"""

from .devices import VaritecColorsStarbar12, RGBWLED, HydroBeamX12


device_list = [
    RGBWLED("PanelSpotLeft", 1),
    RGBWLED("PanelSpotRight", 5),
    RGBWLED("EntranceSpotRight", 9),
    VaritecColorsStarbar12("StarbarRight", 13),
    HydroBeamX12("MovingHeadRight", 65),
    VaritecColorsStarbar12("StarbarTop", 83),
    HydroBeamX12("MovingHeadLeft", 135),
    VaritecColorsStarbar12("StarbarLeft", 153),
    RGBWLED("EntranceSpotLeft", 205),
]

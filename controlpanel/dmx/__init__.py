"""
This package is designed to be used with a Serial to DMX adapter, such as the Enttec Open DMX USB Interface.
The DMX devices used in the DMX universe are defined in the manifest.py file,
including their user-defined names, addresses, and optionally their initial animations.

Example usage (assuming the manifest.py file includes a device named "Laser" of type MovingHead):
    from dmx import dmx_universe
    laser = dmx_universe.devices.get("Laser")
    laser.strobe = True
"""


from .dmx import DMXUniverse, DMXDevice, get_device_url
from .devices import VaritecColorsStarbar12, MovingHead, RGBWLED, HydroBeamX12
from .animations import *

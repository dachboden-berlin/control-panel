"""
This package is responsible for handling the shaders (the CRT effect)
Shaders require OpenGL 3.00 (ES for RaspberryPi)
Should the shaders cause any trouble they can be disabled using the --no-shaders launch parameter
"""

from .shaders import Shaders

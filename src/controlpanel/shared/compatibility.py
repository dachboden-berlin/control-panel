"""This is where we define functions that are recognized on one platform but not the other,
for maximum cross-platform compatibility
"""


try:
    from micropython import const
except ImportError:
    from typing import TypeVar
    T = TypeVar("T")
    def const(x: T) -> T:
        return x


try:
    from abc import abstractmethod
except ImportError:
    def abstractmethod(func):
        return func


try:
    from time import ticks_ms, ticks_diff, ticks_add
except ImportError:
    from time import time
    ticks_ms = lambda: int(time() * 1000)
    ticks_diff = lambda x, y: x - y
    ticks_add = lambda x, y: x + y


try:
    from artnet import ArtNet
except ImportError:
    from controlpanel.upy.artnet import ArtNet


try:
    from typing import Generator, Callable, Literal, Optional, Any
except ImportError:
    Generator = object()
    Callable = object()
    Literal = object()
    Optional = object()
    Any = object()

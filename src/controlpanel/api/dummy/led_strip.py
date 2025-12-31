import asyncio
from controlpanel.shared.base.led_strip import BaseLEDStrip
from .fixture import Fixture
from typing import SupportsIndex, Literal, Callable, Generator
from artnet import ArtNet
import struct
from .esp32 import ESP32


class _Pixels:
    """A proxy class for the pixel list.
    Automatically calls the update_callback function when a value in the list is changed."""
    def __init__(self, pixels: list[tuple[int, int, int]], update_callback: Callable[[], None]):
        self._pixels: list[tuple[int, int, int]] = pixels
        self._update_callback: Callable[[], None] = update_callback

    def __getitem__(self, key):
        return self._pixels[key]

    def __setitem__(self, key, value):
        self._pixels[key] = value
        self._update_callback()

    def __len__(self):
        return len(self._pixels)

    def __iter__(self):
        return iter(self._pixels)

    def __repr__(self):
        return repr(self._pixels)

    def __getslice__(self, i, j):
        return self._pixels[i:j]

    def __setslice__(self, i, j, sequence):
        self._pixels[i:j] = sequence
        self._update_callback()

    def __eq__(self, other):
        return self._pixels == other


class LEDStrip(BaseLEDStrip, Fixture):
    ANIMATIONS: dict[str, Callable[[float, bytearray, tuple[int, int, int]], Generator[None, None, None]]] = {
        animation.__name__: animation for animation in BaseLEDStrip.ANIMATIONS if animation is not None
    }

    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 length: int,
                 *,
                 universe: int | None =None,
                 rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB",
                 use_compression: bool = False,
                 refresh_rate_hz: float = 30.0,
                 ) -> None:
        BaseLEDStrip.__init__(self, rgb_order)
        Fixture.__init__(self, _artnet, _loop, _esp, _name, universe=universe)
        self._pixel_proxy: _Pixels = _Pixels([(0, 0, 0) for _ in range(length)], self._send_pixel_data)
        self._use_compression: bool = use_compression

        self._animation_index: int | None = None
        self._animation_speed: float = 1.0
        self._primary_animation_color: tuple[int, int, int] = (50, 0, 0)
        self._secondary_animation_color: tuple[int, int, int] = (0, 50, 0)
        self._refresh_rate_hz: float = refresh_rate_hz

    def send_dmx(self) -> None:
        if self._animation_index is None:
            self._send_pixel_data()
        else:
            self._send_animation_data()

    def _parse_animation_name_or_index(self, animation_name_or_index: str | int | None) -> int | None:
        if isinstance(animation_name_or_index, str):
            animation = self.ANIMATIONS.get(animation_name_or_index)
            if not animation:
                print("Invalid animation name")
                return None
            return BaseLEDStrip.ANIMATIONS.index(animation)
        elif isinstance(animation_name_or_index, int):
            if not 0 <= animation_name_or_index <= len(BaseLEDStrip.ANIMATIONS):
                print("Invalid animation index")
                return None
            return animation_name_or_index
        else:
            return None

    def _pack_animation_bytes(self) -> bytes:
        return struct.pack(
            'BBB' + 'BBB' + 'BBB',  # format: 3 single-byte ints + 2 RGB tuples
            self._animation_index + 1 if self._animation_index is not None else 0,
            self.encode_update_rate(self._refresh_rate_hz),
            self.encode_update_rate(self._animation_speed),
            *self._primary_animation_color,
            *self._secondary_animation_color
        )

    def set_animation(self,
                      animation_name_or_index: str | int | None,
                      refresh_rate_hz: float,
                      animation_speed: float,
                      primary_color: tuple[int, int, int],
                      secondary_color: tuple[int, int, int],
                      ) -> None:
        self._animation_index = self._parse_animation_name_or_index(animation_name_or_index)
        self._refresh_rate_hz = refresh_rate_hz
        self._animation_speed = animation_speed
        self._primary_animation_color = primary_color
        self._secondary_animation_color = secondary_color
        self._send_dmx_packet(self._pack_animation_bytes())

    @staticmethod
    def _compress_rgb(rgb: tuple[int, int, int]) -> int:
        """
        Convert an RGB tuple (R, G, B) with values in the range 0..255
        into a single RGB byte in the format RRRGGGBB.
        """
        r, g, b = rgb
        r = (r >> 5) & 0x07  # Take the top 3 bits of R
        g = (g >> 5) & 0x07  # Take the top 3 bits of G
        b = (b >> 6) & 0x03  # Take the top 2 bits of B
        return (r << 5) | (g << 2) | b

    def _send_pixel_data(self):
        self._animation_index = None
        self._send_dmx_packet(self._pack_pixel_bytes())

    def _send_animation_data(self):
        self._send_dmx_packet(self._pack_animation_bytes())

    def _reorder_rgb(self, rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        return rgb[self._rgb_mapping[0]], rgb[self._rgb_mapping[1]], rgb[self._rgb_mapping[2]]

    def _pack_pixel_bytes(self) -> bytes:
        if not self._use_compression:
            return b"\x00" + bytes(value for rgb in self._pixel_proxy for value in self._reorder_rgb(rgb))
        else:
            return b"\x00" + bytes(self._compress_rgb(self._reorder_rgb(rgb)) for rgb in self._pixel_proxy)

    def __len__(self):
        return len(self._pixel_proxy)

    def __getitem__(self, item) -> tuple[int, int, int]:
        return self._pixel_proxy[item]

    def __setitem__(self, pixel: SupportsIndex, rgb: tuple[int, int, int]) -> None:
        self.set_pixel(pixel, rgb)

    def __iter__(self):
        return iter(self._pixel_proxy)

    @property
    def pixels(self) -> _Pixels:
        return self._pixel_proxy

    @pixels.setter
    def pixels(self, new_pixels: list[tuple[int, int, int]]):
        if not isinstance(new_pixels, list):
            raise TypeError("Pixels must be assigned a list of (R, G, B) tuples.")
        if len(new_pixels) != len(self):
            raise ValueError(f"Pixel list must be exactly {len(self)} items long.")
        if not all(
                isinstance(rgb, tuple) and len(rgb) == 3 and all(0 <= val <= 255 for val in rgb) for rgb in new_pixels):
            raise ValueError("Each pixel must be a tuple of three integers between 0 and 255.")
        self._pixel_proxy[:] = new_pixels  # Update the existing Pixels proxy in-place so references don't break

    def set_pixel(self, pixel: SupportsIndex, rgb: tuple[int, int, int]):
        assert isinstance(rgb, tuple) and len(rgb) == 3 and all(0 <= val <= 255 for val in rgb), "Invalid rgb tuple"
        self._pixel_proxy[pixel] = rgb
        self._send_pixel_data()

    def set_pixels(self, pixels: list[tuple[int, int, int]]):
        self.pixels = pixels

    def fill(self, color: tuple[int, int, int]):
        self._pixel_proxy[:] = [color] * len(self)

    def blackout(self) -> None:
        self.fill((0, 0, 0))

    def whiteout(self) -> None:
        self.fill((255, 255, 255))

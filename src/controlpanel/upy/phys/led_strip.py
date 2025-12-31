import neopixel
from machine import Pin, SoftSPI, I2C
from controlpanel.shared.base.led_strip import BaseLEDStrip, Generator, Literal, Animation
from .fixture import Fixture
from micropython import const
from controlpanel.upy.artnet import ArtNet
from controlpanel.upy import rgb_decompression


_BITMASK_RED = const(0b11100000)
_BITMASK_GREEN = const(0b00011100)
_BITMASK_BLUE = const(0b00000011)


_ANIM_INDEX_OFFSET = const(0)
_ANIM_INDEX_BYTES = const(1)
_UPDATE_RATE_OFFSET = const(_ANIM_INDEX_OFFSET + _ANIM_INDEX_BYTES)
_UPDATE_RATE_BYTES = const(1)
_ANIM_SPEED_OFFSET = const(_UPDATE_RATE_OFFSET + _UPDATE_RATE_BYTES)
_ANIM_SPEED_BYTES = const(1)
_PRIMARY_COLOR_OFFSET = const(_ANIM_SPEED_OFFSET + _ANIM_SPEED_BYTES)
_PRIMARY_COLOR_BYTES = const(3)
_SECONDARY_COLOR_OFFSET = const(_PRIMARY_COLOR_OFFSET + _PRIMARY_COLOR_BYTES)
_SECONDARY_COLOR_BYTES = const(3)
_TOTAL_ANIM_BYTES = const(_SECONDARY_COLOR_OFFSET + _SECONDARY_COLOR_BYTES)


class LEDStrip(BaseLEDStrip, Fixture):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 pin: int,
                 length: int,
                 *,
                 universe: int | None = None,
                 use_compression: bool = False,
                 update_rate_hz: float = 1.0,
                 rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB",  # used for animations
                 primary_animation_color: list[int] | None = None,
                 secondary_animation_color: list[int] | None = None,
                 ) -> None:
        BaseLEDStrip.__init__(self, rgb_order)
        Fixture.__init__(self, _context[0], _name, update_rate_hz, universe=universe)
        self._neopixels: neopixel.NeoPixel = neopixel.NeoPixel(Pin(pin, Pin.OUT), length)
        self._use_compression = use_compression
        self._animation: Generator[bytearray, None, None] | None = None
        self._primary_animation_color: list[int] = primary_animation_color or [100, 0, 0]
        self._secondary_animation_color: list[int] = secondary_animation_color or [0, 100, 0]

    def __len__(self):
        return len(self._neopixels)

    @staticmethod
    def _uncompress_rgb_into(buffer: bytearray, compressed: bytes | memoryview) -> None:
        """
        Convert a bytes object containing compressed RGB values (RRRGGGBB)
        into a bytearray where each byte is a separate color channel.
        """
        for i, byte in enumerate(compressed):
            # Extract R, G, B values
            r = (byte & _BITMASK_RED) >> 5  # Top 3 bits for R
            g = (byte & _BITMASK_GREEN) >> 2  # Middle 3 bits for G
            b = byte & _BITMASK_BLUE  # Bottom 2 bits for B

            # Scale them back to the 0-255 range
            r = (r << 5) | (r << 2) | (r >> 1)  # Scale 3-bit to 8-bit
            g = (g << 5) | (g << 2) | (g >> 1)  # Scale 3-bit to 8-bit
            b = (b << 6) | (b << 4) | (b << 2) | b  # Scale 2-bit to 8-bit

            # Append the expanded channels
            buffer[3 * i] = r
            buffer[3 * i + 1] = g
            buffer[3 * i + 2] = b

    def parse_dmx_data(self, data: bytes):
        animation_byte = data[0]
        if animation_byte == 0:
            self._animation = None
            if len(data) == 1:
                return
            else:
                self._parse_pixel_data(memoryview(data)[1:])
        else:
            self._parse_animation_data(data)

    def _parse_animation_data(self, animation_data: bytes | memoryview):
        assert len(animation_data) == _TOTAL_ANIM_BYTES, f"Total number of bytes must be {_TOTAL_ANIM_BYTES}"
        animation_index: int = animation_data[_ANIM_INDEX_OFFSET] - 1
        assert animation_index < len(self.ANIMATIONS), f"Animation index {animation_index} outside range of animations"
        animation: Animation = self.ANIMATIONS[animation_index]
        self.update_rate_ms: int = int(1000/self.decode_update_rate(animation_data[_UPDATE_RATE_OFFSET]))
        animation_speed: float = self.decode_update_rate(animation_data[_ANIM_SPEED_OFFSET])
        primary_color: tuple[int, int, int] = (animation_data[_PRIMARY_COLOR_OFFSET],
                                               animation_data[_PRIMARY_COLOR_OFFSET + 1],
                                               animation_data[_PRIMARY_COLOR_OFFSET + 2])
        secondary_color: tuple[int, int, int] = (animation_data[_SECONDARY_COLOR_OFFSET],
                                                 animation_data[_SECONDARY_COLOR_OFFSET + 1],
                                                 animation_data[_SECONDARY_COLOR_OFFSET + 2])
        self._animation = animation(self.update_rate_ms,
                                    self._neopixels.buf,
                                    animation_speed,
                                    primary_color,
                                    secondary_color,
                                    )
        # TODO: mutable data structure to store animation speed and colors?
        # TODO: remove rgb ordering argument from phys class? (dummy can fix rgb order for animations too?)

    def _parse_pixel_data(self, pixel_data: bytes | memoryview):
        if not self._use_compression:
            assert len(pixel_data) == 3 * len(self._neopixels), "length of pixel data must be 3 times the number of pixels"
            self._neopixels.buf = bytearray(pixel_data)
        else:
            assert len(pixel_data) == len(self._neopixels), "length of pixel data must be equal to the number of pixels"
            rgb_decompression.uncompress_rgb_into(self._neopixels.buf, pixel_data)
        self._neopixels.write()

    async def update(self):
        if not self._animation:
            return
        try:
            next(self._animation)
            self._neopixels.write()
        except StopIteration:
            self._animation = None

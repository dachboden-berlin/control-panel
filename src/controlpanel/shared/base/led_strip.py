from controlpanel.shared.compatibility import Generator, Callable, Literal, const
try:
    Animation = Callable[[int, bytearray, float, tuple[int, int, int], tuple[int, int, int]], Generator[None, None, None]]
except TypeError:
    Animation = object()


_MIN_UPDATE_RATE: float = const(0.1)
_MAX_UPDATE_RATE: float = const(30.0)


def interpolate_color(color1: tuple[int, int, int], color2: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (int(color1[0] + (color2[0] - color1[0]) * factor),
            int(color1[1] + (color2[1] - color1[1]) * factor),
            int(color1[2] + (color2[2] - color1[2]) * factor))


def looping_line(_update_rate_ms: int,
                 _buf: bytearray,
                 speed: float,
                 color1: tuple[int, int, int],
                 color2: tuple[int, int, int],
                 ) -> Generator[None, None, None]:
    offset_per_update = speed * (_update_rate_ms / 1000)
    led_count = len(_buf) // 3
    # buf = bytearray(led_count * 3)
    position: float = 0.0

    while True:
        for i in range(led_count):
            dist = abs((i - position) % led_count)
            fade = max(0.0, 1.0 - dist / 3.0)
            color = interpolate_color(color2, color1, fade)

            offset = i * 3
            _buf[offset + 0] = color[0]
            _buf[offset + 1] = color[1]
            _buf[offset + 2] = color[2]

        yield None
        position = (position + offset_per_update) % led_count


def strobe(_update_rate_ms: int,
           _buf: bytearray,
           speed: None = None,
           color1: tuple[int, int, int] = (255, 255, 255),
           color2: tuple[int, int, int] = (0, 0, 0),
           ) -> Generator[None, None, None]:
    led_count = len(_buf) // 3
    while True:
        for color in (color1, color2):
            for i in range(led_count):
                offset = i * 3
                _buf[offset + 0] = color[0]
                _buf[offset + 1] = color[1]
                _buf[offset + 2] = color[2]
            yield None


class BaseLEDStrip:
    ANIMATIONS: list[Animation] = [
        looping_line,
        strobe,
    ]

    def __init__(self, rgb_order: Literal["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"] = "RGB"):
        index_map: dict[Literal["R", "G", "B"], int] = {'R': 0, 'G': 1, 'B': 2}
        self._rgb_mapping: tuple[int, int, int] = (index_map[rgb_order[0]],
                                                   index_map[rgb_order[1]],
                                                   index_map[rgb_order[2]])

    @staticmethod
    def encode_update_rate(rate: float):
        from math import log
        rate = max(min(rate, _MAX_UPDATE_RATE), _MIN_UPDATE_RATE)
        scale = log(_MAX_UPDATE_RATE / _MIN_UPDATE_RATE)
        return int(round(255 * log(rate / _MIN_UPDATE_RATE) / scale))

    @staticmethod
    def decode_update_rate(byte_value: int):
        scale = _MAX_UPDATE_RATE / _MIN_UPDATE_RATE
        return _MIN_UPDATE_RATE * (scale ** (byte_value / 255))

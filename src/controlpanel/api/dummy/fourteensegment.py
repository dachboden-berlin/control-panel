import asyncio
from .fixture import Fixture
from artnet import ArtNet
import colorsys
from .esp32 import ESP32


character_dict = {
    " ": 0b00000000000000,
    "!": 0b00000000000110,
    '"': 0b00001000000010,
    "#": 0b01001011001110,
    "$": 0b01001011101101,
    "%": 0b11111111100100,
    "&": 0b10001101011001,
    "'": 0b00001000000000,
    "(": 0b10010000000000,
    ")": 0b00100100000000,
    "*": 0b11111111000000,
    "+": 0b01001011000000,
    ",": 0b00100000000000,
    "-": 0b00000011000000,
    ".": 0b00000000000000,
    "/": 0b00110000000000,
    "0": 0b00110000111111,
    "1": 0b00010000000110,
    "2": 0b00000011011011,
    "3": 0b00000010001111,
    "4": 0b00000011100110,
    "5": 0b10000001101001,
    "6": 0b00000011111101,
    "7": 0b00000000000111,
    "8": 0b00000011111111,
    "9": 0b00000011101111,
    ":": 0b01001000000000,
    ";": 0b00101000000000,
    "<": 0b10010001000000,
    "=": 0b00000011001000,
    ">": 0b00100110000000,
    "?": 0b01000010000011,
    "@": 0b00001010111011,
    "A": 0b00000011110111,
    "B": 0b01001010001111,
    "C": 0b00000000111001,
    "D": 0b01001000001111,
    "E": 0b00000001111001,
    "F": 0b00000001110001,
    "G": 0b00000010111101,
    "H": 0b00000011110110,
    "I": 0b01001000001001,
    "J": 0b00000000011110,
    "K": 0b10010001110000,
    "L": 0b00000000111000,
    "M": 0b00010100110110,
    "N": 0b10000100110110,
    "O": 0b00000000111111,
    "P": 0b00000011110011,
    "Q": 0b10000000111111,
    "R": 0b10000011110011,
    "S": 0b00000011101101,
    "T": 0b01001000000001,
    "U": 0b00000000111110,
    "V": 0b00110000110000,
    "W": 0b10100000110110,
    "X": 0b10110100000000,
    "Y": 0b00000011101110,
    "Z": 0b00110000001001,
    "[": 0b00000000111001,
    "]": 0b00000000001111,
    "^": 0b10100000000000,
    "_": 0b00000000001000,
    "`": 0b00000100000000,
    "a": 0b01000001011000,
    "b": 0b10000001111000,
    "c": 0b00000011011000,
    "d": 0b00100010001110,
    "e": 0b00100001011000,
    "f": 0b01010011000000,
    "g": 0b00010010001110,
    "h": 0b01000001110000,
    "i": 0b01000000000000,
    "j": 0b00101000010000,
    "k": 0b11011000000000,
    "l": 0b00000000110000,
    "m": 0b01000011010100,
    "n": 0b01000001010000,
    "o": 0b00000011011100,
    "p": 0b00000101110000,
    "q": 0b00010010000110,
    "r": 0b00000001010000,
    "s": 0b10000010001000,
    "t": 0b00000001111000,
    "u": 0b00000000011100,
    "v": 0b00100000010000,
    "w": 0b10100000010100,
    "x": 0b10110100000000,
    "y": 0b00001010001110,
    "z": 0b00100001001000,
    "{": 0b00100101001001,
    "|": 0b01001000000000,
    "}": 0b10010010001001,
    "~": 0b00110011000000,
}


class FourteenSegmentDisplay(Fixture):
    def __init__(self,
                 _artnet: ArtNet,
                 _loop: asyncio.AbstractEventLoop,
                 _esp: ESP32,
                 _name: str,
                 /,
                 element_count: int,
                 *,
                 universe: int | None =None,
                 ) -> None:
        super().__init__(_artnet, _loop, _esp, _name, universe=universe)

        self._text: str = ""
        self._element_count: int = element_count
        self._digit_count: int = element_count * 2

        self._segments: list[tuple[int, int, int]] = [(0, 0, 0) for _ in range(element_count*32)]

    def draw(self, color: tuple[int, int, int]) -> None:
        for i, char in enumerate(self._text):
            is_left = (i % 2 == 0)
            bitmap = character_dict.get(char, character_dict[" "])
            for b in range(14 - 1, -1, -1):
                segment_on = (bitmap >> b) & 1
                segment_idx = b if is_left else 17 + b
                self._segments[(i//2) * 32 + segment_idx] = color if segment_on else (0, 0, 0)
        self.send_dmx()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text[:self._digit_count].ljust(self._digit_count, " ")
        self.draw((255,0,0))

    def send_dmx(self) -> None:
        data = bytes(value for rgb in self._segments for value in self._compress_rgb_to_hl(rgb))
        print(data)
        self._send_dmx_packet(data)

    @staticmethod
    def _compress_rgb_to_hl(rgb: tuple[int, int, int]) -> tuple[int, int]:
        h, l, s = colorsys.rgb_to_hls(*rgb)
        h = int(h*255)
        l = int(l)
        return h, l

    def blackout(self) -> None:
        self._segments = [(0, 0, 0) for _ in range(self._element_count*32)]
        self.send_dmx()

    def whiteout(self) -> None:
        self._segments = [(255, 0, 0) for _ in range(self._element_count*32)]
        self.send_dmx()

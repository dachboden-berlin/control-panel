from controlpanel.upy.libs.rfid_reader.mfrc522 import MFRC522
from machine import SoftSPI, I2C
from .sensor import Sensor
from controlpanel.upy.artnet import ArtNet
from micropython import const


_DEFAULT_POLLING_RATE_HZ = const(1.0)


class RFIDReader(Sensor):
    def __init__(self,
                 _context: tuple[ArtNet, SoftSPI, I2C],
                 _name: str,
                 pin_reset: int,
                 pin_chip_select: int,
                 *,
                 polling_rate_hz: float = _DEFAULT_POLLING_RATE_HZ,
                 ) -> None:
        super().__init__(_context[0], _name, polling_rate_hz)
        self._mfrc522 = MFRC522(_context[1], pin_reset, pin_chip_select)
        self._current_uid: bytes | None = None

    def get_uid(self) -> None | bytes:
        (stat, tag_type) = self._mfrc522.request(self._mfrc522.REQIDL)
        if not stat == self._mfrc522.OK:
            return None
        
        (stat, raw_uid) = self._mfrc522.anticoll()
        if not stat == self._mfrc522.OK:
            return None
        
        # print("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
        return raw_uid

    async def update(self) -> None:
        uid: bytes | None = self.get_uid()
        if uid != self._current_uid:
            self._send_trigger_packet(uid or b"\x00\x00\x00\x00")

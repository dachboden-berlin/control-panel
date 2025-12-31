import machine
from .sensor import Sensor
from controlpanel.upy.artnet import ArtNet
from controlpanel.upy.libs.MPU6050 import MPU6050
import struct
from micropython import const


_DEFAULT_POLLING_RATE_HZ = const(5)


class Accelerometer(Sensor):
    def __init__(
            self,
            _context: tuple[ArtNet, machine.SoftSPI, machine.I2C],
            _name: str,
            *,
            polling_rate_hz: float = _DEFAULT_POLLING_RATE_HZ,
    ) -> None:
        super().__init__(_context[0], _name, polling_rate_hz)
        self.mpu6050 = MPU6050(_context[2])

    async def update(self) -> None:
        self._send_trigger_packet(struct.pack("<3e", *self.mpu6050.read_gyro_data()))

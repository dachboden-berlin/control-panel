from machine import Pin, SoftSPI, I2C
import struct
from controlpanel.upy.phys import Sensor
from controlpanel.upy.artnet import ArtNet


class WaterFlowSensor(Sensor):
    def __init__(
            self,
            _context: tuple[ArtNet, SoftSPI, I2C],
            name: str,
            pin: int,
            polling_rate_hz: float,
        ) -> None:
        Sensor.__init__(self, _context[0], name, polling_rate_hz)
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_RISING, handler=self.water_flow_irq_handler)  # correct edge?
        self._flow_counter: int = 0

    def water_flow_irq_handler(self, pin: Pin):
        self._flow_counter += 1

    async def update(self) -> None:
        if not self._flow_counter:
            return
        self._send_trigger_packet(struct.pack("<I", self._flow_counter))
        self._flow_counter = 0

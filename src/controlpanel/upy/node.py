import utils
from machine import reset, SoftSPI, I2C
from controlpanel.upy import phys
from controlpanel.upy.artnet import ArtNet
from controlpanel.shared.base import Device
from controlpanel.upy.phys import Fixture, Sensor
from controlpanel.shared.compatibility import Callable
from micropython import const
import uasyncio as asyncio
import webrepl


_OP_ARTPOLL = const(0x2000)
_OP_ARTCMD = const(0x2400)
_OP_ARTDMX = const(0x5000)


class Node:
    def __init__(self):
        self._name = utils.get_hostname()
        self._artnet = ArtNet()
        self._artnet.subscribe(_OP_ARTDMX, self.artdmx_callback)
        self._artnet.subscribe(_OP_ARTCMD, self.artcmd_callback)
        self._artnet.subscribe(_OP_ARTPOLL, self.artpoll_callback)
        self.commands: dict[bytes, Callable] = {
            b"RESET": reset,
            b"STOP": self._stop_updating_devices,
            b"PING": lambda: self._artnet.send_command(b"RETURN_PING"),
        }
        manifest = self._parse_manifest()
        self._spi: SoftSPI | None = self._instantiate_spi(manifest)
        self._i2c: I2C | None = self._instantiate_i2c(manifest)
        self.devices: dict[str, Device] = self._instantiate_devices(manifest)
        self.universes: dict[int, Fixture] = {
            device.universe: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.fixtures: dict[str, Fixture] = {
            device.name: device for device in self.devices.values() if isinstance(device, Fixture)
        }
        self.sensors: dict[str, Sensor] = {
            device.name: device for device in self.devices.values() if isinstance(device, Sensor)
        }

        self._update_devices: bool = True

    def _parse_manifest(self) -> dict[str, dict]:
        manifest = utils.load_json('controlpanel/shared/device_manifest.json')
        if not manifest:
            return {}
        return manifest.get(self._name, {})

    @staticmethod
    def _instantiate_spi(config: dict[str, dict]) -> SoftSPI | None:
        spi_config = config.get("spi")
        if not spi_config:
            return None
        return SoftSPI(
            sck=spi_config["sck"],
            mosi=spi_config["mosi"],
            miso=spi_config["miso"],
            phase=spi_config.get("phase") or 0,
            polarity=spi_config.get("polarity") or 0,
        )

    @staticmethod
    def _instantiate_i2c(config: dict[str, dict]) -> I2C | None:
        i2c_config = config.get("i2c")
        if not i2c_config:
            return
        scl = i2c_config.get("scl")
        sda = i2c_config.get("sda")
        return I2C(scl=scl, sda=sda)

    def _instantiate_devices(self, config: dict[str, dict]) -> dict[str, Device]:
        device_config = config.get("devices")
        if not device_config:
            return {}
        devices: dict[str, Device] = {}
        for device_name, (class_name, kwargs, _) in device_config.items():
            cls: type = getattr(phys, class_name)
            try:
                device: Device = cls((self._artnet, self._spi, self._i2c), device_name, **kwargs)
                devices[device.name] = device
            except Exception as e:
                print(f"Failed to instantiate device '{device_name}', logging...")
                utils.log_error(e)
        return devices

    def _stop_updating_devices(self):
        print("Stopping device updates...")
        self._update_devices = False

    async def _update_device(self, device: Sensor | Fixture):
        while self._update_devices:
            await device.update()
            await asyncio.sleep_ms(device.update_rate_ms)

    async def update_all_devices(self):
        tasks = [
            self._update_device(device)
            for device in self.devices.values()
            if device.update_rate_ms > 0
        ]
        tasks.append(self.connection_watchdog())
        tasks.append(self.artnet_task())
        await asyncio.gather(*tasks)

    async def connection_watchdog(self, sleep_ms: int = 10_000, retries: int = 5):
        attempt = 0
        while True:
            if utils.INTERFACE.isconnected():
                # print("Connection is still live!")
                attempt = 0
                pass
            else:
                attempt += 1
                utils.INTERFACE.disconnect()
                if attempt >= retries:
                    print("Max number of retries reached! Creating AP and stopping watchdog.")
                    utils.INTERFACE = utils.create_ap()
                    webrepl.start()
                    break
                print(f"We are not connected! Trying to reconnect, attempt #{attempt}")
                utils.INTERFACE.connect()
            await asyncio.sleep_ms(sleep_ms)

    def artcmd_callback(self, op_code: int, ip: str, port: int, payload: tuple[int, int, int, memoryview]):
        prot_ver, esta, length, cmd_buf = payload
    
        cmd = bytes(cmd_buf)
        func = self.commands.get(cmd)
        if func:
            print(f"Received command {cmd}")
            func()
        else:
            print(f"Received unknown command {cmd}")

    def artdmx_callback(self, op_code: int, ip: str, port: int, payload):
        seq, universe, data = payload
        fixture = self.universes.get(universe)
        if not fixture or fixture.should_ignore_seq(seq):
            return
        fixture._seq = seq
        fixture.parse_dmx_data(data)

    def artpoll_callback(self, op_code: int, ip: str, port: int, payload):
        # prot_ver, flags, diag_prio, tp_bot, tp_top, esta, oem = payload
        self._artnet.address = (ip, self._artnet.address[1])  # Update target address to sender
        asyncio.create_task(self.delayed_reply_to_artpoll(ip, port))

    async def artnet_task(self):
        while True:
            self._artnet.poll()
            await asyncio.sleep_ms(2)

    async def delayed_reply_to_artpoll(self, ip: str, port: int):
        from random import randint
        await asyncio.sleep_ms(randint(0, 1000))  # ArtNet 4 standard specifies a random delay of up to 1s
        self._artnet.send_poll_reply(ip=utils.get_local_ip(),
                                     port=self._artnet.address[1],
                                     address=(ip, port),
                                     short_name=self._name,
                                     long_name="Control Panel ESP32 Node: " + self._name,
                                     mac=utils.get_mac_address(),
                                     )
